from twisted.internet.task import LoopingCall
import pygame

def loadImage(path):
    image = pygame.image.load(path)
    image = image.convert()
    image.set_colorkey(image.get_at((0,0)))
    return image

class Image(object):
    def __init__(self, path):
        self._image = loadImage(path)
        self.width, self.height = self._image.get_size()

    def draw(self, screen, position):
        position = (position[0] - (self.width / 2), position[1] - (self.height / 2))
        screen.blit(self._image, position)

class Animation(object):
    def __init__(self, path):
        i = 0
        self._images = {}
        while True:
            try:
                self._images[i] = loadImage(path.format(i + 1))
                i += 1
            except Exception as e:
                break
        self.width, self.height = self._images[0].get_size()

    def draw(self, screen, position):
        position = (position[0] - (self.width / 2), position[1] - (self.height / 2))
        screen.blit(self._images[self._imageIndex], position)

    def start(self, fps):
        self._imageIndex = 0
        self._loopingCall = LoopingCall(self._incrementImageIndex)
        self._loopingCall.start(1.0 / fps)

    def _incrementImageIndex(self):
        self._imageIndex = (self._imageIndex + 1) % len(self._images)