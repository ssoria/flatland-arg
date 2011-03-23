from twisted.python.filepath import FilePath

class ImagePaths:
    _dir = FilePath(__file__).parent().sibling("data").child("images")
    sentry = _dir.child("sentry_idle.png").path
    trap = _dir.child("trap_idle.png").path
    enemyTraps = {1 : _dir.child("trap_teamblu").child("trap_teamblu{0:04}.png").path,
                 2 : _dir.child("trap_teamred").child("trap_teamred{0:04}.png").path}