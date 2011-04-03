from vector import Vector2D
from game.player import Player, ResourcePool, Building
from twisted.spread import pb
from twisted.internet.task import LoopingCall

class Environment(pb.Cacheable, pb.RemoteCache):
    def __init__(self):
        self.observers = []
        self.players = {}
        self.rp = ResourcePool(100)
        self.rp.position = Vector2D(0, 0)
        self.width = 48.0
        self.height = 80.0
        self.buildings = {}
        self.team = None

    def createPlayer(self, team):
        player = Player()
        player.team = team
        playerId = id(player)
        self.players[playerId] = player
        for o in self.observers: o.callRemote('createPlayer', playerId, player)
        return player
    def observe_createPlayer(self, playerId, player):
        self.players[playerId] = player

    def removePlayer(self, player):
        pid = id(player)
        del self.players[pid]
        for o in self.observers: o.callRemote('removePlayer', pid)
    def observe_removePlayer(self, pid):
        del self.players[pid]

    def createBuilding(self, team, position):
        if (self.rp.position - position) < 6:
            return None
        for b in self.buildings.itervalues():
            if (team == b.team) and (b.position - position) < 6:
                return None
        building = Building()
        building.team = team
        building.position = position
        bid = id(building)
        self.buildings[bid] = building
        building.onDestroyed.addCallback(self.destroyBuilding)
        for o in self.observers: o.callRemote('createBuilding', bid, building)
        return building
    def observe_createBuilding(self, bid, building):
        self.buildings[bid] = building

    def destroyBuilding(self, building):
        bid = id(building)
        del self.buildings[bid]
        for o in self.observers: o.callRemote('destroyBuilding', bid)
    def observe_destroyBuilding(self, bid):
        del self.buildings[bid]

    def attack(self, player):
        distance = 3
        player.attack()
        for p in self.players.itervalues():
            if (p.team != player.team) and (p.position - player.position) < distance:
                p.hit()
        for b in self.buildings.values():
            if (b.position - player.position) < distance:
                b.hit()

    def startAttacking(self, player):
        player.action = LoopingCall(self.attack, player)
        player.action.start(2, now=False)

    def startBuilding(self, player):
        building = None
        for b in self.buildings.itervalues():
            if (player.team == b.team) and (b.position - player.position) < 3:
                building = b
        if not building:
            if (self.rp.position - player.position) < 3:
                building = self.rp
            else:
                building = self.createBuilding(player.team, player.position)
                if not building:
                    return
        player.action = LoopingCall(building.build, player)
        player.action.start(2, now=False)
    
    def finishAction(self, player):
        if player.action:
            player.action.stop()
            player.action = None

    def startUpgrading(self, player):
        for b in self.buildings.itervalues():
            if b.isPolyFactory() and (b.team == player.team) and (b.position - player.position) < 3 and not b.upgrading:
                b.upgrading = player
                player.upgradingAt = b

    def finishUpgrading(self, player):
        if player.upgradingAt:
            player.upgradingAt.upgrading = None
            player.upgradingAt = None

    def updatePlayerPosition(self, player, position):
        player.position = position
        for o in self.observers: o.callRemote('updatePlayerPosition', id(player), position)

        for b in self.buildings.itervalues():
            if b.isTrap() and (b.team != player.team) and ((b.position - player.position) < 1):
                player.trapped()
                self.destroyBuilding(b)
                break
    def observe_updatePlayerPosition(self, playerId, position):
        self.players[playerId].position = position

    def isVisible(self, entity):
        # Spectators see all
        if not self.team:
            return True
        # See objects on your team
        if self.team == entity.team:
            return True
        # Object in range of my sentries
        for b in self.buildings.itervalues():
            if b.isSentry() and (b.team == self.team) and (entity.position - b.position) < 7:
                return True
        # object in range of a scanning player
        for p in self.players.itervalues():
            if (self.team == p.team):
                if (entity.position - p.position) < p.getScanRadius():
                    return True
        return False

    def paint(self, view):
        for b in self.buildings.itervalues():
            if self.isVisible(b):
                b.paint(view, view.screenCoord(b.position), b.team == self.team)
        self.rp.paint(view, view.screenCoord(self.rp.position))
        for p in self.players.itervalues():
            p.paint(view, view.screenCoord(p.position), self.isVisible(p))

    # pb.Cacheable stuff
    def getStateToCacheAndObserveFor(self, perspective, observer):
        self.observers.append(observer)
        state = pb.Cacheable.getStateToCopyFor(self, perspective).copy()
        del state['observers']
        return state

    def stoppedObserving(self, perspective, observer):
        self.observers.remove(observer)

pb.setUnjellyableForClass(Environment, Environment)