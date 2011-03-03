import pygame
import pygame.gfxdraw
from twisted.internet import defer
from twisted.spread import pb
from vector import Vector2D

class Player(pb.Cacheable, pb.RemoteCache):
    def __init__(self):
        #pb.Cacheable.__init__(self)
        #pb.RemoteCache.__init__(self)
        self.position = Vector2D(0, 0)
        self.sides = 3
        self.resources = 0
        self.observers = []

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

    def paint(self, screen, position, isTeammate):
        pygame.draw.circle(screen, (255, 255, 255), position, 50)

        if not isTeammate:
            return

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
    else:
        return Sentry()
#    else:
#        return PolyFactor()

class Building(pb.Cacheable, pb.RemoteCache):
    def __init__(self):
        self.sides = 0
        self.resources = 0
        self.observers = []
        self.builders = []
        self.deferred = defer.Deferred()
        self.size = 50

    def build(self, player):
        if not player.resources:
            return
        player.loseResource()
        self.resources += 1
        if self.resources < 5:
            for o in self.observers: o.callRemote('gainResource')
        else:
            for p in self.builders:
                self.removeBuilder(p)

    def observe_gainResource(self):
        self.resources += 1

    def paint(self, screen, position):
        pygame.gfxdraw.filled_circle(screen, position.x, position.y, self.size, pygame.Color(255, 0, 0, (255 * (self.resources + 1)) / 7))

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

pb.setUnjellyableForClass(Building, Building)

class Trap(Building):
    def __init__(self):
        Building.__init__(self)
        self.sides = 3
        self.size = 100

    def paint(self, screen, position):
        pygame.gfxdraw.filled_circle(screen, position.x, position.y, self.size, pygame.Color(0, 255, 255, 150))

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
        self.size = 150

    def paint(self, screen, position):
        pygame.gfxdraw.filled_circle(screen, position.x, position.y, self.size, pygame.Color(255, 255, 0, 150))

    def build(self, player):
        pass

    def addBuilder(self, player):
        pass

    def removeBuilder(self, player):
        pass

pb.setUnjellyableForClass(Sentry, Sentry)


class ResourcePool(pb.Copyable, pb.RemoteCopy):
    def __init__(self, size):
        self.size = size

    def build(self, player):
        player.gainResource()

    def addBuilder(self, player):
        pass

    def removeBuilder(self, player):
        pass

    def paint(self, screen, position):
        pygame.gfxdraw.filled_circle(screen, position.x, position.y, self.size, pygame.Color(0, 0, 255, 150))

pb.setUnjellyableForClass(ResourcePool, ResourcePool)
