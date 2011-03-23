import math
import pygame
import pygame.gfxdraw
from twisted.internet import defer
from twisted.spread import pb
from vector import Vector2D
from twisted.internet import reactor
from twisted.python.filepath import FilePath
from animation import loadImage, Animation, Image
import settings

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
        self.self = False
        self.loadImages()

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

    def loadImages(self):
        teams = {1 : "blu", 2 : "red"}
        sides = {3 : "tri", 4 : "sqr", 5 : "pent", 6 : "hex"}
        firstPerson = {True : "player", False : "team"}
        from game import __file__ as gameFile
        dir = FilePath(gameFile).parent().sibling("data").child("images")
        self.images = {}
        for t in teams:
            for s in sides:
                for p in firstPerson:
                    path = dir.child("%s%s_%s.png" % (firstPerson[p], teams[t], sides[s]))
                    self.images[(p, t, s)] = loadImage(path.path)

    def _teamColor(self):
        if self.team == 1:
            return (0, 50, 255)
        else:
            return (255, 50, 0)

    def paint(self, screen, position, isTeammate):
        if isTeammate:
            try:
                image = self.images[(self.self, self.team, self.sides)]
                w, h = image.get_size()
                x = position.x - (w / 2)
                y = position.y - (h / 2)
                screen.blit(image, (x, y))
            except:
                pygame.draw.circle(screen, self._teamColor(), position, 10)
        else:
            pygame.draw.circle(screen, self._teamColor(), position, 10)
            return

        if self.scanning:
            pygame.gfxdraw.filled_circle(screen, position.x, position.y, self.getScanRadius() * 10, pygame.Color(255, 0, 255, 150))

        drawArmor(screen, self.sides, self.resources, position)

    def getStateToCacheAndObserveFor(self, perspective, observer):
        self.observers.append(observer)
        state = pb.Cacheable.getStateToCopyFor(self, perspective).copy()
        del state['observers']
        del state['images']
        if self == perspective.player:
            state['self'] = True
        return state

    def setCopyableState(self, state):
        pb.RemoteCache.setCopyableState(self, state)
        self.loadImages()

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
        self.loadImages()

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

    def loadImages(self):
        self.trapImage = Image(settings.ImagePaths.trap)
        self.sentryImage = Image(settings.ImagePaths.sentry)
        self.enemyTraps = {1 : Animation(settings.ImagePaths.enemyTraps[1]),
                           2 : Animation(settings.ImagePaths.enemyTraps[2])}
        self.enemyTraps[1].start(12)
        self.enemyTraps[2].start(12)

    def paintTrap(self, screen, position):
        self.trapImage.draw(screen, position)
    def paintEnemyTrap(self, screen, position):
        self.enemyTraps[self.team].draw(screen, position)
    def paintSentry(self, screen, position):
        self.sentryImage.draw(screen, position)
    def paintEnemySentry(self, screen, position):
        size = 20
        pygame.gfxdraw.filled_circle(screen, position.x, position.y, size, self._teamColor())
    def paintPolyFactory(self, screen, position):
        size = 20
        pygame.gfxdraw.filled_circle(screen, position.x, position.y, size, self._teamColor())
    def paint(self, screen, position, isTeammate):
        if self.sides == 3:
            if isTeammate:
                self.paintTrap(screen, position)
            else:
                self.paintEnemyTrap(screen, position)
        elif self.sides == 4:
            if isTeammate:
                self.paintSentry(screen, position)
            else:
                self.paintEnemyTrap(screen, position)
        elif self.sides == 5:
            self.paintPolyFactory(screen, position)
        drawArmor(screen, self.sides, self.resources, position)

    def getStateToCacheAndObserveFor(self, perspective, observer):
        self.observers.append(observer)
        state = pb.Cacheable.getStateToCopyFor(self, perspective).copy()
        del state['observers']
        return state

    def setCopyableState(self, state):
        pb.RemoteCache.setCopyableState(self, state)
        self.loadImages()

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
        self.loadImages()

    def loadImages(self):
        from game import __file__ as gameFile
        path = FilePath(gameFile).parent().sibling("data").child("images").child("resource_pool").child("resource_pool{0:04}.png")
        self.image = Animation(path.path)
        self.image.start(12)

    def build(self, player):
        player.gainResource()

    def addBuilder(self, player):
        pass

    def removeBuilder(self, player):
        pass

    def paint(self, screen, position):
        self.image.draw(screen, position)

    def setCopyableState(self, state):
        pb.RemoteCopy.setCopyableState(self, state)
        self.loadImages()

pb.setUnjellyableForClass(ResourcePool, ResourcePool)
