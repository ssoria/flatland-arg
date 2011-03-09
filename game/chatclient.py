#!/usr/bin/env python
# Copyright (c) 2009-2010 Twisted Matrix Laboratories.
# See LICENSE for details.

import environment
import player
import vector
from game.view import Window
from game.controller import PlayerController
from twisted.spread import pb
from twisted.internet import defer
from twisted.internet import reactor
from twisted.cred import credentials

class Client():
    def connect(self):
        factory = pb.PBClientFactory()
        reactor.connectTCP("localhost", 8800, factory)
        d = factory.login(credentials.Anonymous())
        d.addCallback(self.connected)
        reactor.run()

    @defer.inlineCallbacks
    def connected(self, perspective):
        self.perspective = perspective
        self.environment = yield perspective.callRemote('getEnvironment')
        self.environment.team = yield perspective.callRemote('getTeam')
        self.view = Window(self.environment)
        self.view.start("Client - %d" % (self.environment.team, ))
        self.controller = PlayerController(self.perspective, self.view)
        self.controller.go()

    def shutdown(self, result):
        reactor.stop()


Client().connect()

