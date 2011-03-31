# Python
from collections import deque

# pyGame
import pygame

# twisted
from twisted.python.filepath import FilePath
from twisted.internet.task import LoopingCall

# local
from vector import Vector2D
from settings import Images


def loadImage(path):
    """
    Load an image from the L{FilePath} into a L{pygame.Surface}.

    @type path: L{FilePath}

    @rtype: L{pygame.Surface}
    """
    return pygame.image.load(path.path)



class Window(object):
    def __init__(self, environment):
        self.environment = environment
        self.images = Images(FilePath("data").child("images"))
        self.images.load()
        self.actions = deque()
        self.action = None
        self.center = Vector2D(0,0)

    def addAction(self, action):
        self.actions.append(self.images.images[action])
        self.startAction()

    def startAction(self):
        if self.action == None:
            try:
                self.action = self.actions.popleft()
                self.action.start(5).addCallback(self.stopAction)
            except:
                pass

    def stopAction(self, ign):
        self.action = None
        self.startAction()

    def paint(self):
        """
        Call C{paint} on all views which have been directly added to
        this Window.
        """
        self.screen.fill((0, 0, 0))
        self.environment.paint(self)
        if self.action:
            self.action.draw(self.screen, (240, 400))
        pygame.display.flip()

    def setCenter(self, position):
        self.center = position

    def worldCoord(self, p):
        width = self.screen.get_width()
        height = self.screen.get_height()
        (cx, cy) = self.screen.get_rect().center
        return Vector2D(((p.x - cx) * self.environment.width) / width,
                        ((p.y - cy) * self.environment.height) / height)

    def screenCoord(self, p):
        width = self.screen.get_width()
        height = self.screen.get_height()
        (cx, cy) = self.screen.get_rect().center
        return Vector2D((((p.x - self.center.x) / (self.environment.width / 2)) * width) + cx,
                        (((p.y - self.center.y) / (self.environment.height / 2)) * height) + cy)

    def start(self, title):
        self.screen = pygame.display.get_surface()
        pygame.display.set_caption(title)
        self._renderCall = LoopingCall(self.paint)
        self._renderCall.start(0.03)

    def stop(self):
        self._renderCall.stop()
