import math
import pygame
import pygame.gfxdraw
from twisted.internet import defer
from twisted.spread import pb
from vector import Vector2D
from twisted.internet import reactor

class Player(pb.Cacheable, pb.RemoteCache):
    def __init__(self):
        #pb.Cacheable.__init__(self)
        #pb.RemoteCache.__init__(self)
        self.position = Vector2D(0, 0)
        self.sides = 3
        self.resources = 0
        self.observers = []
        self.scanning = 0
        self.size = 1
        self.action = None

    def _startScanning(self):
        self.scanning = pygame.time.get_ticks()
    def startScanning(self):
        self._startScanning()
        for o in self.observers: o.callRemote('startScanning')
    observe_startScanning = _startScanning

    def _finishScanning(self):
        # scanning turns negative while effect lingers
        self.scanning -= pygame.time.get_ticks()
        def resetScanTime():
            self.scanning = 0
        reactor.callLater(5, resetScanTime)
    def finishScanning(self):
        self._finishScanning()
        for o in self.observers: o.callRemote('finishScanning')
    observe_finishScanning = _finishScanning

    def getScanRadius(self):
        if (self.scanning < 0):
            dt = -self.scanning / 2000.0
        else:
            dt = (pygame.time.get_ticks() - self.scanning) / 2000.0
        return math.sqrt(dt) * self.size

    def _gainResource(self):
        if self.resources < self.sides:
            self.resources += 1
    def gainResource(self):
        self._gainResource()
        for o in self.observers: o.callRemote('gainResource')
    observe_gainResource = _gainResource
    
    def _loseResource(self):
        if self.resources:
            self.resources -= 1
    def loseResource(self):
        self._loseResource()
        for o in self.observers: o.callRemote('loseResource')
    observe_loseResource = _loseResource

    def _hit(self):
        if self.resources:
            self.resources = 0
        else:
            self.sides -= 1
    def hit(self):
        self._hit()
        for o in self.observers: o.callRemote('hit')
    observe_hit = _hit

    def _levelUp(self):
        self.resources = 0
        self.sides += 1
    def levelUp(self):
        self._levelUp()
        for o in self.observers: o.callRemote('levelUp')
    observe_levelUp = _levelUp

    def paint(self, screen, position, isTeammate):
        pygame.draw.circle(screen, (255, 255, 255), position, self.size * 10)

        if not isTeammate:
            return

        if self.scanning:
            pygame.gfxdraw.filled_circle(screen, position.x, position.y, self.getScanRadius() * 10, pygame.Color(255, 0, 255, 150))

        i = 0
        while i < self.resources:
            endPosition = (position[0], position[1] + 10)
            pygame.draw.line(screen, (0, 255, 0), position, endPosition, 7)
            position = (position[0] + 10, position[1])
            i += 1
        while i < self.sides:
            endPosition = (position[0], position[1] + 10)
            pygame.draw.line(screen, (255, 0, 0), position, endPosition, 7)
            position = (position[0] + 10, position[1])
            i += 1

    def getStateToCacheAndObserveFor(self, perspective, observer):
        self.observers.append(observer)
        state = pb.Cacheable.getStateToCopyFor(self, perspective).copy()
        del state['observers']
        return state

    def stoppedObserving(self, perspective, observer):
        self.observers.remove(observer)

pb.setUnjellyableForClass(Player, Player)

def buildingFactory(sides):
    if sides < 3:
        return None
    elif sides == 3:
        return Trap()
    elif sides == 4:
        return Sentry()
    else:
        return PolyFactory()

class Building(pb.Cacheable, pb.RemoteCache):
    def __init__(self):
        self.sides = 0
        self.resources = 0
        self.observers = []
        self.builders = []
        self.deferred = defer.Deferred()
        self.size = 1

    def build(self, player):
        if not player.resources:
            return
        player.loseResource()
        self.resources += 1
        for o in self.observers: o.callRemote('setResources', self.resources)

    def observe_setResources(self, r):
        self.resources = r

    def paint(self, screen, position):
        pygame.gfxdraw.filled_circle(screen, position.x, position.y, self.size * 10, pygame.Color(255, 0, 0, (255 * (self.resources + 1)) / 7))

    def getStateToCacheAndObserveFor(self, perspective, observer):
        self.observers.append(observer)
        state = pb.Cacheable.getStateToCopyFor(self, perspective).copy()
        del state['observers']
        return state

    def stoppedObserving(self, perspective, observer):
        self.observers.remove(observer)

    def addBuilder(self, player):
        self.builders.append(player)

    def removeBuilder(self, player):
        self.builders.remove(player)
        if not self.builders:
            self.deferred.callback(buildingFactory(self.resources))

    def hit(self):
        if self.sides:
            return buildingFactory(self.sides - 1)

pb.setUnjellyableForClass(Building, Building)

class Trap(Building):
    def __init__(self):
        Building.__init__(self)
        self.sides = 3
        self.size = 1

    def paint(self, screen, position):
        pygame.gfxdraw.filled_circle(screen, position.x, position.y, self.size * 10, pygame.Color(0, 255, 255, 150))

    def build(self, player):
        pass

    def addBuilder(self, player):
        pass

    def removeBuilder(self, player):
        pass

    def trigger(self, player):
        player.hit()

pb.setUnjellyableForClass(Trap, Trap)

class Sentry(Building):
    def __init__(self):
        Building.__init__(self)
        self.sides = 4
        self.size = 2

    def paint(self, screen, position):
        pygame.gfxdraw.filled_circle(screen, position.x, position.y, self.size * 10, pygame.Color(255, 255, 0, 150))

    def build(self, player):
        pass

    def addBuilder(self, player):
        pass

    def removeBuilder(self, player):
        pass

pb.setUnjellyableForClass(Sentry, Sentry)

class PolyFactory(Building):
    def __init__(self):
        Building.__init__(self)
        self.sides = 5
        self.size = 2

    def paint(self, screen, position):
        pygame.gfxdraw.filled_circle(screen, position.x, position.y, self.size * 10, pygame.Color(255, 0, 255, 150))

    def removeBuilder(self, player):
        self.builders.remove(player)
        if not self.builders and self.resources >= player.sides:
            self.resources = 0
            for o in self.observers: o.callRemote('setResources', self.resources)
            player.levelUp()

pb.setUnjellyableForClass(PolyFactory, PolyFactory)

class ResourcePool(pb.Copyable, pb.RemoteCopy):
    def __init__(self, size):
        self.size = 3

    def build(self, player):
        player.gainResource()

    def addBuilder(self, player):
        pass

    def removeBuilder(self, player):
        pass

    def paint(self, screen, position):
        pygame.gfxdraw.filled_circle(screen, position.x, position.y, self.size * 10, pygame.Color(0, 0, 255, 150))

pb.setUnjellyableForClass(ResourcePool, ResourcePool)
