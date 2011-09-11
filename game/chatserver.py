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


class TrackerPort(pb.Root):
    def remote_echo(self, st):
        print 'echoing: ', st
        return st

    def remote_lost_target(self, touch):
        print 'this target was lost: ', touch

    def remote_new_target(self, touch):
        print 'this is a new target: ', touch

    def remote_moved_target(self, touch):
        print 'this is a moved target: ', touch




pygame.init()
pygame.display.set_mode((480, 800), pygame.DOUBLEBUF)
realm = GameRealm()
env = Environment()
view = Window(env)
realm.environment = env
view.start('Server')
LoopingCall(lambda: pygame.event.pump()).start(0.03)

tracker = TrackerPort()

portal = portal.Portal(realm, [checkers.AllowAnonymousAccess()])

reactor.listenTCP(8800, pb.PBServerFactory(portal))


reactor.listenTCP(8789, pb.PBServerFactory(tracker))

p = reactor.listenUDP(0, DatagramProtocol())
LoopingCall(lambda: p.write("FlatlandARG!!!", ("224.0.0.1", 8000))).start(1)
reactor.run()
