from twisted.internet.task import LoopingCall
import pygame
import itertools
from vector import Vector2D

def _loadImage(path):
    image = pygame.image.load(path)
    # TODO Are all of our images alpha'd now?
    if True:
        image = image.convert_alpha()
    else:
        image = image.convert()
        image.set_colorkey(image.get_at((0,0)))
    return image

class Image(object):
    def __init__(self, path, offset = (0,0)):
        if path:
            self.path = path.path
        self.offset = Vector2D(offset)

    def load(self):
        self._image = _loadImage(self.path)
        self._setCenter()

    def _setCenter(self):
        self.center = Vector2D(self._image.get_rect().center)
        self.width, self.height = self._image.get_rect().size

    def draw(self, screen, position):
        imagePosition = position - self.center + self.offset
        screen.blit(self._image, imagePosition)

    def drawScaled(self, screen, position, scale):
        center = self.center * scale
        image = pygame.transform.smoothscale(self._image, center * 2)
        imagePosition = (position[0] - center[0], position[1] - center[1])
        screen.blit(image, imagePosition)

    def copy(self):
        return self

class Animation(Image):
    def load(self):
        i = 1
        self._images = []
        while True:
            try:
                self._images.append(_loadImage(self.path % (i, )))
                i += 1
            except Exception:
                break
        self._image = self._images[0]
        self._setCenter()

    def start(self, fps):
        self._loopingCall = LoopingCall(self._nextImage, iter(self._images))
        return self._loopingCall.start(1.0 / fps)

    def startReversed(self, fps):
        self._loopingCall = LoopingCall(self._nextImage, reversed(self._images))
        return self._loopingCall.start(1.0 / fps)

    def stop(self):
        self._loopingCall.stop()

    def _nextImage(self, iterator):
        try:
            self._image = iterator.next()
        except StopIteration:
            self.stop()

    def copy(self):
        animation = Animation(None)
        animation.center = self.center
        animation._images = self._images
        animation.offset = self.offset
        return animation

class LoopingAnimation(Animation):
    def start(self, fps):
        self._loopingCall = LoopingCall(self._nextImage, itertools.cycle(self._images))
        return self._loopingCall.start(1.0 / fps)
