import kivy
kivy.require('1.0.6')

from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.graphics import Color, Rectangle, Point, GraphicException
from random import random
from math import sqrt

from kivy.support import install_twisted_reactor
install_twisted_reactor()
from twisted.spread import pb
from twisted.internet import reactor



def calculate_points(x1, y1, x2, y2, steps=5):
    dx = x2 - x1
    dy = y2 - y1
    dist = sqrt(dx * dx + dy * dy)
    if dist < steps:
        return None
    o = []
    m = dist / steps
    for i in xrange(1, int(m)):
        mi = i / m
        lastx = x1 + dx * mi
        lasty = y1 + dy * mi
        o.extend([lastx, lasty])
    return o



class Tracker(FloatLayout):

    def connect(self):
        self._lost_targets = []
        self._new_targets = []
        self._moved_targets = []
        self._clientfactory = pb.PBClientFactory()
        reactor.connectTCP("localhost", 8789, self._clientfactory)
        d = self._clientfactory.getRootObject()
        d.addCallback(self.send_msg)

    def send_msg(self, result):
        result.callRemote("echo", "hello network")

    def send_lost_target(self, result):
        result.callRemote("lost_target", self._lost_targets.pop())

    def send_new_target(self, result):
        result.callRemote("new_target", self._new_targets.pop())

    def send_target_moved(self, result):
        result.callRemote("moved_target", self._moved_targets.pop())

    def get_msg(self, result):
        print "server echoed: ", result

    def on_touch_down(self, touch):
        win = self.get_parent_window()
        ud = touch.ud
        ud['group'] = g = str(touch.uid)
        with self.canvas:
            ud['color'] = Color(random(), 1, 1, mode='hsv', group=g)
            ud['lines'] = (
                Rectangle(pos=(touch.x, 0), size=(1, win.height), group=g),
                Rectangle(pos=(0, touch.y), size=(win.width, 1), group=g),
                Point(points=(touch.x, touch.y), source='particle.png',
                      pointsize=5, group=g))

        ud['label'] = Label(size_hint=(None, None))
        self.update_touch_label(ud['label'], touch)
        self.add_widget(ud['label'])
        self._new_targets.append({'id': touch.uid, 'position': {'x': touch.x, 'y': touch.y}})
        d = self._clientfactory.getRootObject()
        d.addCallback(self.send_new_target)

    def on_touch_move(self, touch):
        ud = touch.ud
        ud['lines'][0].pos = touch.x, 0
        ud['lines'][1].pos = 0, touch.y

        points = ud['lines'][2].points
        oldx, oldy = points[-2], points[-1]
        points = calculate_points(oldx, oldy, touch.x, touch.y)
        if points:
            try:
                lp = ud['lines'][2].add_point
                for idx in xrange(0, len(points), 2):
                    lp(points[idx], points[idx+1])
            except GraphicException:
                pass

        ud['label'].pos = touch.pos
        self.update_touch_label(ud['label'], touch)
        self._moved_targets.append({'id': touch.uid, 'position': {'x': touch.x, 'y': touch.y}})
        d = self._clientfactory.getRootObject()
        d.addCallback(self.send_target_moved)

    def on_touch_up(self, touch):
        ud = touch.ud
        self.canvas.remove_group(ud['group'])
        self.remove_widget(ud['label'])
        self._lost_targets.append({'id': touch.uid, 'position': {'x': touch.x, 'y': touch.y}})
        d = self._clientfactory.getRootObject()
        d.addCallback(self.send_lost_target)

    def update_touch_label(self, label, touch):
        label.text = 'ID: %s\nPos: (%d, %d)\nClass: %s' % (
            touch.id, touch.x, touch.y, touch.__class__.__name__)
        label.texture_update()
        label.pos = touch.pos
        label.size = label.texture_size[0] + 20, label.texture_size[1] + 20



class TrackerApp(App):
    title = 'Touchtracer'
    icon = 'icon.png'

    def build(self):
        return Tracker()

    def on_start(self):
        pass
        self.root.connect()
#        reactor.run()

if __name__ in ('__main__', '__android__'):
    TrackerApp().run()
