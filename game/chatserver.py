import pygame.event

from game.environment import Environment
from game.view import Window

from zope.interface import implements

from twisted.cred import checkers, portal
from twisted.internet.task import LoopingCall
from twisted.internet import reactor
from twisted.spread import pb
from twisted.internet.protocol import DatagramProtocol

class GameRealm:
    implements(portal.IRealm)

    def __init__(self):
        self._team = 1

    def _getTeam(self):
        if self._team == 1:
            self._team = 2
        elif self._team == 2:
            self._team = 1
        return self._team

    def requestAvatar(self, avatarId, mind, *interfaces):
        assert pb.IPerspective in interfaces
        assert avatarId is checkers.ANONYMOUS
        avatar = GameAvatar(self.environment, self._getTeam())
        return pb.IPerspective, avatar, avatar.disconnect

class GameAvatar(pb.Avatar):
    def __init__(self, environment, team):
        self.environment = environment
        self.player = self.environment.createPlayer(team)
    def disconnect(self):
        self.environment.removePlayer(self.player)
    def perspective_startAttacking(self):
        self.environment.startAttacking(self.player)
    def perspective_finishAttacking(self):
        self.environment.finishAction(self.player)
    def perspective_startBuilding(self):
        self.environment.startBuilding(self.player)
    def perspective_finishBuilding(self):
        self.environment.finishAction(self.player)
    def perspective_startScanning(self):
        self.player.startScanning()
    def perspective_finishScanning(self):
        self.player.finishScanning()
    def perspective_startUpgrading(self):
        self.environment.startUpgrading(self.player)
    def perspective_finishUpgrading(self):
        self.environment.finishUpgrading(self.player)
    def perspective_updatePosition(self, position):
        self.environment.updatePlayerPosition(self.player, position)
    def perspective_getEnvironment(self):
        return self.environment
    def perspective_getTeam(self):
        return self.player.team
    #TODO could we add a perspective_getPosition and perspective_getIRTargetStatus here
    #TODO otherwise, how do we do remote call on a client?


pygame.init()
pygame.display.set_mode((480, 800), pygame.DOUBLEBUF)
realm = GameRealm()
env = Environment()
view = Window(env)
realm.environment = env
view.start('Server')
LoopingCall(lambda: pygame.event.pump()).start(0.03)

portal = portal.Portal(realm, [checkers.AllowAnonymousAccess()])

reactor.listenTCP(8800, pb.PBServerFactory(portal))

from twisted.protocols.basic import LineReceiver
from twisted.internet import protocol
import cPickle

class PlayerBlob:
    def __init__(self, id):
        self.id = id
        self.lights = []

    def hasLight(self):
        return len(self.lights) > 0

    def addLight(self, light):
        self.lights.append(light)
        self.updatePosition()

    def removeLight(self, light):
        self.lights.remove(light)

        if self.hasLight():
            self.updatePosition()

    def updatePosition(self):
        x = 0
        y = 0

        for light in self.lights:
            x += light.x
            y += light.y

        self.x = x / len(self.lights)
        self.y = y / len(self.lights)

        print (self.id, self.x, self.y)


class Light:
    def __init__(self, point, player):
        self.id = point['id']
        self.x = point['pos'][0]
        self.y = point['pos'][1]

        self.player = player
        player.addLight(self)

    def move(self, pos):
        self.x = pos[0]
        self.y = pos[1]

        self.player.updatePosition()

    def dispose(self):
        self.player.removeLight(self)

class TrackRecv(LineReceiver):
    def __init__(self):
        self.numPlayers = 2;

        self.players = []
        for i in range(self.numPlayers):
            self.players.append(PlayerBlob(i))

        self.lights = {}

    def getEmptyPlayer(self):
        for player in self.players:
            if not player.hasLight():
                return player

    def process(self, point):
        if point['type'] == 'new':
            player = self.getEmptyPlayer()
            self.lights[point['id']] = Light(point, player)
        elif point['type'] == 'mov':
            light = self.lights[point['id']]
            light.move(point['pos'])
        elif point['type'] == 'del':
            light = self.lights[point['id']]
            light.dispose()
        else:
            # unkown, do not process
            return

    def lineReceived(self, line):
        self.process(cPickle.loads(line))

tracker_factory = protocol.ClientFactory()
tracker_factory.protocol = TrackRecv
reactor.connectTCP("127.0.0.1", 1025, tracker_factory)


p = reactor.listenUDP(0, DatagramProtocol())
LoopingCall(lambda: p.write("FlatlandARG!!!", ("224.0.0.1", 8000))).start(1)
reactor.run()
