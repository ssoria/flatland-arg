import math
import pygame
import pygame.gfxdraw
from twisted.internet import defer
from twisted.spread import pb
from vector import Vector2D
from twisted.internet import reactor

def drawArmor(view, sides, resources, position):
    if not resources:
        return
    image = view.images.images["Armor", sides, resources]
    image.draw(view.screen, position)


class PlayerScan:
    def __init__(self):
        self.reset()

    def reset(self):
        self.startTime = 0
        self._radius = 0
        self.resetTimer = None

    def start(self):
        if self.resetTimer:
            self.resetTimer.cancel()
            self.reset()
        self.startTime = pygame.time.get_ticks()

    def stop(self):
        self._radius = self.radius()
        self.startTime = pygame.time.get_ticks()
        self.resetTimer = reactor.callLater(5, self.reset)

    def radius(self):
        if self.startTime == 0:
            return 0
        dt = (pygame.time.get_ticks() - self.startTime)
        if self._radius:
            return self._radius * (1 - (dt / 5000.0))
        return math.sqrt(dt / 200.0)

    def __nonzero__(self):
        if self.startTime == 0:
            return False
        return True


class Player(pb.Cacheable, pb.RemoteCache):
    def __init__(self):
        #pb.Cacheable.__init__(self)
        #pb.RemoteCache.__init__(self)
        self.position = Vector2D(0, 0)
        self.sides = 3
        self.resources = 1
        self.observers = []
        self.scanning = PlayerScan()
        self.size = 1
        self.action = None
        self.upgradingAt = None
        self.self = False

    def _startScanning(self):
        self.scanning.start()
    def startScanning(self):
        self._startScanning()
        for o in self.observers: o.callRemote('startScanning')
    observe_startScanning = _startScanning

    def _finishScanning(self):
        self.scanning.stop()
    def finishScanning(self):
        self._finishScanning()
        for o in self.observers: o.callRemote('finishScanning')
    observe_finishScanning = _finishScanning

    def getScanRadius(self):
        return self.scanning.radius()

    def observe_trapped(self):
        if self.resources:
            self.resources = 0
        else:
            self.sides = 0
    def trapped(self):
        self.observe_trapped()
        for o in self.observers: o.callRemote('trapped')

    def _gainResource(self):
        if self.sides < 3:
            self.sides += 1
        elif self.resources < self.sides:
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
            return (0, 50, 255)
        else:
            return (255, 50, 0)

    def paint(self, view, position, isTeammate):
        # HACK player image deviates from center of screen occasionally
        # likely caused by view.center being updated but not player.position
        # which must wait for the server to update its
        if self.self:
            position = Vector2D(240, 400)
        if isTeammate:
            image = view.images.images[("Player", self.self, self.team, self.sides)]
            image.draw(view.screen, position)
        else:
            image = view.images.images[("Enemy", self.team)]
            image.draw(view.screen, position)
            return

        if self.scanning:
            pygame.gfxdraw.filled_circle(view.screen, position.x, position.y, self.getScanRadius() * 10, pygame.Color(255, 0, 255, 150))

        drawArmor(view, self.sides, self.resources, position)

    def getStateToCacheAndObserveFor(self, perspective, observer):
        self.observers.append(observer)
        state = pb.Cacheable.getStateToCopyFor(self, perspective).copy()
        del state['observers']
        if self == perspective.player:
            state['self'] = True
        return state

    def setCopyableState(self, state):
        pb.RemoteCache.setCopyableState(self, state)
        self.scanning = PlayerScan()

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

    def paintEnemySentry(self, screen, position):
        size = 20
        pygame.gfxdraw.filled_circle(screen, position.x, position.y, size, self._teamColor())
    def paintPolyFactory(self, screen, position):
        size = 20
        pygame.gfxdraw.filled_circle(screen, position.x, position.y, size, self._teamColor())
    def paint(self, view, position, isTeammate):
        if self.sides == 3:
            if isTeammate:
                view.images.images["trap_idle"].draw(view.screen, position)
            else:
                view.images.images[("enemyTraps", self.team)].draw(view.screen, position)
        elif self.sides == 4:
            if isTeammate:
                view.images.images["sentry_idle"].draw(view.screen, position)
            else:
                self.paintEnemySentry(view.screen, position)
        elif self.sides == 5:
            self.paintPolyFactory(view.screen, position)
        drawArmor(view, self.sides, self.resources, position)

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

    def paint(self, view, position):
        view.images.images["resource_pool"].draw(view.screen, position)

pb.setUnjellyableForClass(ResourcePool, ResourcePool)
