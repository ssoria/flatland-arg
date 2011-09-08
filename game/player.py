import math
import pygame
from twisted.internet import defer
from twisted.spread import pb
from vector import Vector2D
from twisted.internet import reactor

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
        return (math.log1p(min(1, (dt / 10000.0) / (math.e - 1))) * .65) + 0.35

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
        self.resources = 0
        self.observers = []
        self.scanning = PlayerScan()
        self.size = 1
        self.action = None
        self.upgradingAt = None
        self.self = False
        self.events = set()
        self.topEvents = set()
        self.armor = dict()
        self.building = None
        self._buildingReset = None
        self.tooltip = None

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
            for i in range(self.resources, 0, -1):
                self.breakArmor(self.sides, i)
            self.resources = 0
        else:
            self.sides = 0
    def trapped(self):
        self.observe_trapped()
        for o in self.observers: o.callRemote('trapped')

    def setAction(self, remote, local):
        self.action = local
        for o in self.observers: o.callRemote('setAction', remote)
    def observe_setAction(self, action):
        # TODO Tooltips no longer used?
        self.tooltip = None

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
            self.breakArmor(self.sides, self.resources)
            self.resources -= 1
    def loseResource(self):
        self._loseResource()
        for o in self.observers: o.callRemote('loseResource')
    observe_loseResource = _loseResource

    def _attack(self):
        animation = self.images["Attack"].copy()
        animation.start(12).addCallback(lambda ign: self.events.remove(animation))
        self.events.add(animation)
    def attack(self):
        self._attack()
        for o in self.observers: o.callRemote('attack')
    observe_attack = _attack

    def _updatePosition(self, position, building):
        self.position = position
        # TODO only need this for self.self
        def buildingReset():
            self.building = None
            self._buildingReset = None
        if building:
            self.building = building
            if self._buildingReset:
                self._buildingReset.cancel()
            self._buildingReset = reactor.callLater(1, buildingReset)
    def updatePosition(self, position, building):
        self._updatePosition(position, building)
        for o in self.observers: o.callRemote('updatePosition', position, building)
    observe_updatePosition = _updatePosition

    def breakArmor(self, sides, resources):
        # TODO nothing to do here?
        pass

    def _hit(self):
        if self.resources:
            self.breakArmor(self.sides, self.resources)
            self.resources -= 1
        else:
            animation = self.images["LevelUp"].copy()
            animation.startReversed(12).addCallback(lambda ign: self.topEvents.remove(animation))
            self.topEvents.add(animation)
            self.sides -= 1
    def hit(self):
        self._hit()
        for o in self.observers: o.callRemote('hit')
    observe_hit = _hit

    def _levelUp(self):
        self.armor.clear()
        self.resources = 0
        self.sides += 1

        animation = self.images["LevelUp"].copy()
        animation.start(12).addCallback(lambda ign: self.topEvents.remove(animation))
        self.topEvents.add(animation)
    def levelUp(self):
        self._levelUp()
        for o in self.observers: o.callRemote('levelUp')
    observe_levelUp = _levelUp

    def paint(self, view, position, isTeammate, isVisible):
        # TODO player image deviates from center of screen occasionally
        # likely caused by view.center being updated but not player.position
        # which must wait for the server to update its
        if self.self:
            position = Vector2D(240, 400)
        # TODO HACK save the view to get images
        self.images = view.images.images

        if isVisible and self.scanning:
            view.images.images["PlayerScan"].drawScaled(view.screen, position, self.getScanRadius())

        for image in self.events:
            image.draw(view.screen, position)

        if isVisible:
            image = view.images.images["Player", (self.self, isTeammate), self.sides]
            image.draw(view.screen, position)
            for image in self.topEvents:
                image.draw(view.screen, position)
            if self.tooltip:
                self.tooltip.draw(view.screen, position + Vector2D(0, -100))
        else:
            image = view.images.images["Enemy"]
            image.draw(view.screen, position)
            return

        for a in self.armor:
            # XXX Must start all clients at the same time or armor is Unpersistable
            self.armor[a].draw(view.screen, position)

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
        self.explosion = None

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
        else:
            player.loseResource()
            self.gainResource()
        for o in player.observers: o.callRemote('setAction', "Building")

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

    def drawToolTip(self, view, tip, team = None):
        # TODO No more tool tips?
        pass

    def paint(self, view, position, isTeammate):
        if self.explosion:
           self.explosion.draw(view.screen, position)
           return

        if self.sides == 0 and self.resources == 0:
            return

        if self.sides:
            view.images.images["Building", self.sides, isTeammate].draw(view.screen, position)
            view.images.images["BuildingHealth", isTeammate, self.sides, self.resources].draw(view.screen, position)
        else:
            image = view.images.images["Building", self.resources, isTeammate].draw(view.screen, position)

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

    def _explode(self):
        self.explosion = self.images["TrapExplosion"].copy()
        return self.explosion.start(24)
    def explode(self):
        self._explode().addCallback(lambda ign: self.onDestroyed.callback(self))
        for o in self.observers: o.callRemote('explode')
    observe_explode = _explode

    def isTrap(self):
        if self.sides == 3 and not self.explosion:
            return True
        return False

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
        for o in player.observers: o.callRemote('setAction', "Mining")

    def addBuilder(self, player):
        pass

    def removeBuilder(self, player):
        pass

    def drawToolTip(self, view, tip, team):
        # TODO No more tool tips?
        pass

    def paint(self, view, position):
        view.images.images["resource_pool"].draw(view.screen, position)

pb.setUnjellyableForClass(ResourcePool, ResourcePool)
