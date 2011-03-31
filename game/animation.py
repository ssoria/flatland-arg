from twisted.internet.task import LoopingCall
import pygame

def _loadImage(path):
    image = pygame.image.load(path)
    if image.get_at((0, 0))[3] == 0:
        image = image.convert_alpha()
    else:
        image = image.convert()
        image.set_colorkey(image.get_at((0,0)))
    return image

class Image(object):
    def __init__(self, path):
        if path:
            self.path = path.path

    def load(self):
        self._image = _loadImage(self.path)
        self._setCenter()

    def _setCenter(self):
        self.center = self._image.get_rect().center

    def draw(self, screen, position):
        imagePosition = (position[0] - self.center[0], position[1] - self.center[1])
        screen.blit(self._image, imagePosition)

class Animation(Image):
    @property
    def _image(self):
        return self._images[self._imageIndex]

    def load(self):
        i = 0
        self._images = {}
        while True:
            try:
                self._images[i] = _loadImage(self.path.format(i + 1))
                i += 1
            except Exception as e:
                break
        self._imageIndex = 0
        self._setCenter()

    def start(self, fps):
        self._imageIndex = 0
        self._loopingCall = LoopingCall(self._incrementImageIndex, len(self._images))
        return self._loopingCall.start(1.0 / fps)

    def _incrementImageIndex(self, max):
        self._imageIndex += 1
        if self._imageIndex == max:
            self._loopingCall.stop()

    def copy(self):
        animation = Animation(None)
        animation.center = self.center
        animation._images = self._images
        return animation

class LoopingAnimation(Animation):
    def _incrementImageIndex(self, max):
        self._imageIndex = (self._imageIndex + 1) % max
