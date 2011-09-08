from twisted.spread import pb
import math

class Vector2D(pb.Copyable, pb.RemoteCopy):
    def __init__(self, *a):
        try:
            self.x = a[0]
            self.y = a[1]
        except:
            self.x = a[0][0]
            self.y = a[0][1]

    @property
    def length(self):
        return math.sqrt(self._lengthSquared())

    def __getitem__(self, n):
        if n:
            return self.y
        return self.x

    def __len__(self):
        return 2

    def _lengthSquared(self):
        return (self.x * self.x) + (self.y * self.y)

    def __lt__(self, other):
        return self._lengthSquared() < (other * other)

    def __mul__(self, m):
        return Vector2D((self.x * m, self.y * m))

    __rmul__ = __mul__

    def __div__(self, d):
        return Vector2D((self.x / d, self.y / d))

    def __add__(self, a):
        return Vector2D((self.x + a.x, self.y + a.y))

    def __sub__(self, s):
        return Vector2D((self.x - s.x, self.y - s.y))

    def __nonzero__(self):
        return (self.length != 0)

    def __str__(self):
        return str((self.x, self.y))

    def __neg__(self):
        return Vector2D((-self.x, -self.y))

    def norm(self):
        return Vector2D(self.x / self.length, self.y / self.length)

pb.setUnjellyableForClass(Vector2D, Vector2D)
