import pygame

from twisted.python.filepath import FilePath
from twisted.internet.task import LoopingCall


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
        self.environment.paint(self.screen)
        pygame.display.flip()


    def start(self, title):
        pygame.init()
        self.screen = pygame.display.set_mode((800, 480), pygame.DOUBLEBUF)
        pygame.display.set_caption(title)
        self._renderCall = LoopingCall(self.paint)
        self._renderCall.start(0.03)

    def stop(self):
        self._renderCall.stop()
