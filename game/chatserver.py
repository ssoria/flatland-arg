import pygame.event

from game.environment import Environment
from game.view import Window

from zope.interface import implements

from twisted.cred import checkers, portal
from twisted.internet.task import LoopingCall
from twisted.internet import reactor
from twisted.spread import pb

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
    def perspective_attack(self, dt):
        self.environment.attack(self.player, dt)
    def perspective_startBuilding(self):
        self.environment.startBuilding(self.player)
    def perspective_finishBuilding(self):
        self.environment.finishBuilding(self.player)
    def perspective_scan(self):
        pass
    def perspective_updatePosition(self, position):
        self.environment.updatePlayerPosition(self.player, position)
    def perspective_getEnvironment(self):
        return self.environment
    def perspective_getTeam(self):
        return self.player.team

realm = GameRealm()
env = Environment()
view = Window(env)
realm.environment = env
view.start('Server')
LoopingCall(lambda: pygame.event.pump()).start(0.03)

portal = portal.Portal(realm, [checkers.AllowAnonymousAccess()])

reactor.listenTCP(8800, pb.PBServerFactory(portal))
reactor.run()
