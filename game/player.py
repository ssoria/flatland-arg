import math
import pygame
import pygame.gfxdraw
from twisted.internet import defer
from twisted.spread import pb
from vector import Vector2D
from twisted.internet import reactor

def drawArmor(screen, sides, resources, position):
    i = 0
    while i < resources:
        endPosition = (position[0], position[1] + 10)
        pygame.draw.line(screen, (0, 255, 0), position, endPosition, 7)
        position = (position[0] + 10, position[1])
        i += 1
    while i < sides:
        endPosition = (position[0], position[1] + 10)
        pygame.draw.line(screen, (255, 0, 0), position, endPosition, 7)
        position = (position[0] + 10, position[1])
        i += 1


class Player(pb.Cacheable, pb.RemoteCache):
    def __init__(self):
        #pb.Cacheable.__init__(self)
        #pb.RemoteCache.__init__(self)
        self.position = Vector2D(0, 0)
        self.sides = 3
        self.resources = 1
        self.observers = []
        self.scanning = 0
        self.size = 1
        self.action = None
        self.upgradingAt = None

    def _startScanning(self):
        self.scanning = pygame.time.get_ticks()
    def startScanning(self):
        self._startScanning()
        for o in self.observers: o.callRemote('startScanning')
    observe_startScanning = _startScanning

    def observe_trapped(self):
        if self.resources:
            self.resources = 0
        else:
            self.sides = 0
    def trapped(self):
        self.observe_trapped()
        for o in self.observers: o.callRemote('trapped')

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
        if not self.scanning:
            return 0
        if (self.scanning < 0):
            dt = -self.scanning / 2000.0
        else:
            dt = (pygame.time.get_ticks() - self.scanning) / 2000.0
        return math.sqrt(dt) * self.size

    def _gainResource(self):
        if self.sides < 3:
            self.sides += 1
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
            self.resources -= 1
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

    def _teamColor(self):
        if self.team == 1:
            return (255, 0, 255)
        else:
            return (0, 255, 255)
    def paint(self, screen, position, isTeammate):
        pygame.draw.circle(screen, self._teamColor(), position, 10)

        if not isTeammate:
            return

        if self.scanning:
            pygame.gfxdraw.filled_circle(screen, position.x, position.y, self.getScanRadius() * 10, pygame.Color(255, 0, 255, 150))

        drawArmor(screen, self.sides, self.resources, position)

    def getStateToCacheAndObserveFor(self, perspective, observer):
        self.observers.append(observer)
        state = pb.Cacheable.getStateToCopyFor(self, perspective).copy()
        del state['observers']
        return state

    def stoppedObserving(self, perspective, observer):
        self.observers.remove(observer)

pb.setUnjellyableForClass(Player, Player)

class Building(pb.Cacheable, pb.RemoteCache):
    def __init__(self):
        self.sides = 0
        self.resources = 0
        self.observers = []
        self.size = 1
        self.onDestroyed = defer.Deferred()
        self.upgrading = None

    def build(self, player):
        if not player.resources:
            return
        if self.sides == 5 and self.resources == 5:
            if self.upgrading and self.upgrading.sides > 2:
                player.loseResource()
                if self.upgrading.sides == self.upgrading.resources:
                    self.upgrading.levelUp()
                else:
                    self.upgrading.gainResource()
            return
        player.loseResource()
        self.gainResource()

    def _gainResource(self):
        # Not a full polyfactory
        # if rubble
        if not self.sides:
            if self.resources == 2:
                self.sides = 3
                self.resources = 0
            else:
                self.resources += 1
        else:
            # if armor is full
            if self.sides == self.resources:
                self.sides += 1
                self.resources = 0
            else:
                self.resources += 1
    def gainResource(self):
        self._gainResource()
        for o in self.observers: o.callRemote('gainResource')
    observe_gainResource = _gainResource

    def observe_setResources(self, r):
        self.resources = r

    # TODO!!!
    def _teamColor(self):
        if self.team == 1:
            return pygame.Color(255, 0, 255, 150)
        else:
            return pygame.Color(0, 255, 255, 150)

    def paintTrap(self, screen, position):
        size = 10
        pygame.gfxdraw.filled_circle(screen, position.x, position.y, size, self._teamColor())
    def paintSentry(self, screen, position):
        size = 20
        pygame.gfxdraw.filled_circle(screen, position.x, position.y, size, self._teamColor())
    def paintPolyFactory(self, screen, position):
        size = 20
        pygame.gfxdraw.filled_circle(screen, position.x, position.y, size, self._teamColor())
    def paint(self, screen, position):
        if self.sides == 3:
            self.paintTrap(screen, position)
        elif self.sides == 4:
            self.paintSentry(screen, position)
        elif self.sides == 5:
            self.paintPolyFactory(screen, position)
        drawArmor(screen, self.sides, self.resources, position)

    def getStateToCacheAndObserveFor(self, perspective, observer):
        self.observers.append(observer)
        state = pb.Cacheable.getStateToCopyFor(self, perspective).copy()
        del state['observers']
        return state

    def stoppedObserving(self, perspective, observer):
        self.observers.remove(observer)

    def hit(self):
        if not (self.sides and self.resources):
            self.onDestroyed.callback(self)
        elif self.resources:
            self.resources -= 1
            for o in self.observers: o.callRemote('setResources', self.resources)

    def isTrap(self):
        return self.sides == 3

    def isSentry(self):
        return self.sides == 4

    def isPolyFactory(self):
        return self.sides == 5

pb.setUnjellyableForClass(Building, Building)

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
