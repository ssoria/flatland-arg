import pygame.event

from game.environment import Environment
from game.view import Window

from zope.interface import implements

from twisted.cred import checkers, portal
from twisted.internet.task import LoopingCall
from twisted.internet import reactor
from twisted.spread import pb
from twisted.internet.protocol import DatagramProtocol
from vector import Vector2D

MAX_DISTANCE2 = 100
MAX_SPEED = 10

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
        tm.addPlayer(self.player)
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
    def __init__(self, player):
        self.player = player
        self.lights = []
        self.x = -1
        self.y = -1

        LoopingCall(self._updatePlayer).start(0.03)

    def hasLight(self):
        return len(self.lights) > 0

    def addLight(self, light):
        self.lights.append(light)
        self.updatePosition()

    def removeLight(self, light):
        self.lights.remove(light)

        if self.hasLight():
            self.updatePosition()

    def _updatePlayer(self):
        startX = self.player.position.x
        startY = self.player.position.y

        dx = self.x - startX
        dy = self.y - startY

        env.updatePlayerPosition(self.player, Vector2D(startX + dx / 2, startY + dy / 2))

        print (startX, startY)

    def updatePosition(self):
        x = 0
        y = 0

        for light in self.lights:
            x += light.x
            y += light.y

        self.x = x / len(self.lights)
        self.y = y / len(self.lights)

        print (self.x, self.y)

    def blink(self):
        for light in self.lights:
            light.player = None

        self.lights = []
        # TODO
        #self.player.blink()


class Light:
    def __init__(self, point):
        self.id = point['id']
        self.x = point['pos'][0]
        self.y = point['pos'][1]

        self.player = None

    def move(self, pos):
        if self.player == None:
            return

        self.x = pos[0]
        self.y = pos[1]

        self.player.updatePosition()

    def setPlayer(self, player):
        if self.player:
            self.player.removeLight(self)

        self.player = player
        player.addLight(self)

    def dispose(self):
        if self.player == None:
            return
        self.player.removeLight(self)

import random

class TrackMaster:
    def __init__(self):
        self.numPlayers = 2;

        self.players = []

        self.lights = {}
        print "init"

    def findNearestPlayer(self, light):
        min = None
        minPlayer = None
        for player in self.players:
            if not player.hasLight():
                minPlayer = player

            dx = player.x - light.x
            dy = player.y - light.y
            distanceSquared = dx*dx + dy*dy
            if distanceSquared < MAX_DISTANCE2:
                if min == None or distanceSquared < min:
                    minPlayer = player
                    min = distanceSquared

        return minPlayer

    def blinkNextPlayer(self):
        self.blinkingPlayer = None

        for p in self.players:
            if not p.hasLight():
                self.blinkingPlayer = p
                break

        if self.blinkingPlayer == None:
            self.blinkingPlayer = random.choice(self.players)

        self.blinkingPlayer.blink()

    def process(self, point):
        if point['type'] == 'new':
            light = Light(point)
            self.lights[point['id']] = light

            # Other
            player = self.findNearestPlayer(light)
            if player:
                light.setPlayer(player)
            #light.setPlayer(self.blinkingPlayer)
            #self.blinkNextPlayer()

        elif point['type'] == 'mov':
            light = self.lights[point['id']]
            light.move(point['pos'])
        elif point['type'] == 'del':
            light = self.lights[point['id']]
            light.dispose()
        else:
            # unkown, do not process
            return

    def addPlayer(self, player):
        self.players.append(PlayerBlob(player))

        self.blinkingPlayer = player


class TrackRecv(LineReceiver):
    def lineReceived(self, line):
        point = cPickle.loads(line)
        # TODO: Uniquify
        point['id'] = str(point['id']) + '1'
        tm.process(point)

tm = TrackMaster()
tracker_factory = protocol.ServerFactory()
tracker_factory.protocol = TrackRecv
reactor.listenTCP(1025, tracker_factory)


p = reactor.listenUDP(0, DatagramProtocol())
LoopingCall(lambda: p.write("FlatlandARG!!!", ("224.0.0.1", 8000))).start(1)
reactor.run()
