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
        self.images = Images(FilePath("data").child("img2"))
        self.images.load()
        self.actions = deque()
        self.action = None
        self.center = Vector2D((0,0))

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
        bg = self.images.images["background"]
        bgWidth = bg.width
        bgHeight = bg.height
        x = -(self.center * 20).x
        y = -(self.center * 20).y
        while x > 0:
            x -= bgWidth;
        while y > 0:
            y -= bgHeight
        while x < 480:
            j = y
            while j < 800:
                self.screen.blit(bg._image, pygame.Rect(x, j, bgWidth, bgHeight))
                j += bgHeight
            x += bgWidth
        self.environment.paint(self)
        if self.action:
         #   self.action.draw(self.screen, Vector2D((240, 400)))
            pass
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
        return Vector2D((((p.x - self.center[0]) / (self.environment.width / 2)) * width) + cx,
                        (((p.y - self.center[1]) / (self.environment.height / 2)) * height) + cy)

    def start(self, title):
        self.screen = pygame.display.get_surface()
        pygame.display.set_caption(title)
        self._renderCall = LoopingCall(self.paint)
        self._renderCall.start(0.03)

    def stop(self):
        self._renderCall.stop()
