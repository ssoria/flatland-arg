from animation import Image, Animation, LoopingAnimation

class Images:
    def __init__(self, dir):
        self.images = dict()
        self.images["sentry_idle"] = Image(dir.child("sentry_idle.png").path)
        self.images["trap_idle"] = Image(dir.child("trap_idle.png").path)
        self.images[("enemyTraps", 1)] = LoopingAnimation(dir.child("trap_teamblu").child("trap_teamblu{0:04}.png").path)
        self.images[("enemyTraps", 2)] = LoopingAnimation(dir.child("trap_teamred").child("trap_teamred{0:04}.png").path)
        self.images["resource_pool"] = LoopingAnimation(dir.child("ani_resources").child("resources{0:04}.png").path)

        actions = ["attack", "attack_blocked", "attack_hit", "attack_missed",
                   "building_created", "flatlined", "intro", "lose", "lvldown",
                   "lvlup", "polyfactory", "polyfactory_upgrade",
                   "resource_full", "resource_out", "resourcegather",
                   "reveal_none", "reveal_polyfactory", "reveal_trap",
                   "revived", "sweep", "trap", "trap_hit", "trap_upgrade",
                   "win"]
        for a in actions:
            self._addFlatlandAnimation(dir, a)

    def _addFlatlandAnimation(self, imageDirectory, action):
        # {imageDirectory}/{action}/flatland_{action}XXXX.png
        dir = imageDirectory.child(action)
        self.images[action] = Animation(dir.child("flatland_" + action + "{0:04}.png").path)

    def load(self):
        for a in self.images:
            self.images[a].load()
        self.images["resource_pool"].start(12)
        self.images[("enemyTraps", 1)].start(12)
        self.images[("enemyTraps", 2)].start(12)
