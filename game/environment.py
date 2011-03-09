from vector import Vector2D
from game.player import Player, ResourcePool, Building, Trap, Sentry
from twisted.spread import pb
from twisted.internet.task import LoopingCall

class Environment(pb.Cacheable, pb.RemoteCache):
    def __init__(self):
        self.observers = []
        self.players = {}
        self.rp = ResourcePool(100)
        self.rp.position = Vector2D(0, 0)
        self.width = 80.0
        self.height = 40.0
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
        building.deferred.addCallback(self.buildingComplete, building)
        for o in self.observers: o.callRemote('createBuilding', bid, building)
        return building
    def observe_createBuilding(self, bid, building):
        self.buildings[bid] = building

    def buildingComplete(self, newBuilding, oldBuilding):
        if newBuilding:
            newBuilding.team = oldBuilding.team
            newBuilding.position = oldBuilding.position
            newId = id(newBuilding)
            self.buildings[newId] = newBuilding
            for o in self.observers: o.callRemote('createBuilding', newId, newBuilding)
        oldId = id(oldBuilding)
        del self.buildings[oldId]
        for o in self.observers: o.callRemote('destroyBuilding', oldId)
    def observe_destroyBuilding(self, bid):
        del self.buildings[bid]

    def attack(self, player, dt):
        distance = min(player.sides, dt / 2) * 50
        print "Player ", id(player), " attacked with strength ", distance
        for p in self.players.itervalues():
            if (p.team != player.team) and (p.position - player.position) < distance:
                p.hit()
        for b in self.buildings.values():
            if (b.position - player.position) < distance:
                self.buildingComplete(b.hit(), b)

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
        building.addBuilder(player)
        player.action = LoopingCall(building.build, player)
        player.action.start(2, False).addCallback(lambda ign: building.removeBuilder(player))
    
    def finishBuilding(self, player):
        if player.action:
            player.action.stop()
            player.action = None

    def updatePlayerPosition(self, player, position):
        player.position = position
        for o in self.observers: o.callRemote('updatePlayerPosition', id(player), position)

        for b in self.buildings.itervalues():
            if isinstance(b, Trap) and (b.team != player.team) and ((b.position - player.position) < b.size):
                b.trigger(player)
                bid = id(b)
                del self.buildings[bid]
                for o in self.observers: o.callRemote('destroyBuilding', bid)
                break
    def observe_updatePlayerPosition(self, playerId, position):
        self.players[playerId].position = position

    def isVisible(self, entity):
        if not self.team:
            return True
        if self.team == entity.team:
            return True
        for b in self.buildings.itervalues():
            if isinstance(b, Sentry) and (b.team == self.team) and (entity.position - b.position) < b.size:
                return True
        for p in self.players.itervalues():
            if (self.team == p.team):
                if (entity.position - p.position) < p.getScanRadius():
                    return True
        return False

    def paint(self, view):
        for p in self.players.itervalues():
            p.paint(view.screen, view.screenCoord(p.position), self.isVisible(p))
        for b in self.buildings.itervalues():
            if self.isVisible(b):
                b.paint(view.screen, view.screenCoord(b.position))
        self.rp.paint(view.screen, view.screenCoord(self.rp.position))

    # pb.Cacheable stuff
    def getStateToCacheAndObserveFor(self, perspective, observer):
        self.observers.append(observer)
        state = pb.Cacheable.getStateToCopyFor(self, perspective).copy()
        del state['observers']
        return state

    def stoppedObserving(self, perspective, observer):
        self.observers.remove(observer)

pb.setUnjellyableForClass(Environment, Environment)