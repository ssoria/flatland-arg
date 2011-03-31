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

    def draw(self, image, position):
        """
        Render an image at a position.
        """
        viewCoord = self.viewport.modelToView(position)
        self.screen.blit(image, (viewCoord.x, viewCoord.y - image.get_size()[1]))

    def drawPlayer(self, position, sides, resources):
        """
        Render a player at a position
        """
        x, y = self.viewport.modelToView(position).tuple()
        pygame.draw.circle(self.screen, (255, 255, 255), (x, y), 50)

        while resources > 0:
            pygame.draw.line(self.screen, (0, 255, 0), (x, y), (x, y+10), 7)
            x += 10
            resources -= 1
            sides -= 1
        while sides > 0:
            pygame.draw.line(self.screen, (255, 0, 0), (x, y), (x, y+10), 7)
            x += 10
            sides -= 1


    def drawResourcePool(self):
        x, y = self.resourcePool.position.tuple()
        pygame.gfxdraw.filled_circle(self.screen, x, y, self.resourcePool.size, pygame.Color(0, 0, 255, 150))


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
