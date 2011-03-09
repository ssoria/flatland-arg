# -*- test-case-name: game.test.test_controller -*-

"""
Input handling.
"""

from twisted.internet.task import LoopingCall
import math

import pygame.event
import pygame.mouse
import pygame.time

# TODO: Can we have a keymap file?
from pygame import (K_a as ATTACK,
                    K_s as SCAN,
                    K_d as BUILD)

from game.vector import Vector2D

class PlayerController(object):
    """
    Input handler for L{game.player.Player} objects.

    @ivar player: The player being controlled.
    @ivar downDirections: List of currently held arrow keys.
    """
    _actions = set([ATTACK, SCAN, BUILD])
    
    def __init__(self, perspective, view):
        self.perspective = perspective
        self.position = Vector2D(0, 0)
        self.speed = 5
        self.view = view
        self._actionQueue = []
        self._currentAction = None

 
    def go(self):
        self.previousTime = pygame.time.get_ticks()
        self._inputCall = LoopingCall(self._handleInput)
        d = self._inputCall.start(0.03)
        return d


    def stop(self):
        self._inputCall.stop()


    def _updatePosition(self, dt):
        if not pygame.mouse.get_focused():
            return
        destination = self.view.worldCoord(Vector2D(pygame.mouse.get_pos()))
        direction = destination - self.position
        if direction < (self.speed * dt):
            self.position = destination
        else:
            self.position += (dt * self.speed) * direction.norm()
        self.perspective.callRemote('updatePosition', self.position)


    def _startedAction(self, action):
        self._currentAction = action
        if self._currentAction == ATTACK:
            self._attackStart = self.previousTime
        elif self._currentAction == BUILD:
            self.perspective.callRemote('startBuilding')
        elif self._currentAction == SCAN:
            self.perspective.callRemote('startScanning')
        else:
            self._currentAction = None


    def _finishedAction(self):
        if self._currentAction == ATTACK:
            dt = self.previousTime - self._attackStart
            self.perspective.callRemote('attack', dt / 1000.0)
            del self._attackStart
        elif self._currentAction == BUILD:
            self.perspective.callRemote('finishBuilding')
        elif self._currentAction == SCAN:
            self.perspective.callRemote('finishScanning')
        self._currentAction = None
        return


    def _handleInput(self):
        """
        Handle currently available pygame input events.
        """
        time = pygame.time.get_ticks()
        self._updatePosition((time - self.previousTime) / 1000.0)
        self.previousTime = time

        for event in pygame.event.get():
            if (event.type == pygame.KEYDOWN) and (event.key in self._actions):
                self._actionQueue.append(event.key)
            elif (event.type == pygame.KEYUP) and (event.key in self._actions):
                if self._currentAction == event.key:
                    self._finishedAction()
                else:
                    self._actionQueue.remove(event.key)

        if (not self._currentAction) and self._actionQueue:
            self._startedAction(self._actionQueue.pop())




