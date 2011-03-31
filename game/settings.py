from animation import Image, Animation, LoopingAnimation

class Images:
    def __init__(self, dir):
        self.images = dict()
        self.images["sentry_idle"] = Image(dir.child("sentry_idle.png"))
        self.images["trap_idle"] = Image(dir.child("trap_idle.png"))
        self.images[("enemyTraps", 1)] = LoopingAnimation(dir.child("trap_teamblu").child("trap_teamblu{0:04}.png"))
        self.images[("enemyTraps", 2)] = LoopingAnimation(dir.child("trap_teamred").child("trap_teamred{0:04}.png"))
        self.images["resource_pool"] = LoopingAnimation(dir.child("ani_resources").child("resources{0:04}.png"))
        self.images["background"] = Image(dir.child("playing_field.png"))

        self.initPlayerImages(dir)

        actions = ["attack", "attack_blocked", "attack_hit", "attack_missed",
                   "building_created", "flatlined", "intro", "lose", "lvldown",
                   "lvlup", "polyfactory", "polyfactory_upgrade",
                   "resource_full", "resource_out", "resourcegather",
                   "reveal_none", "reveal_polyfactory", "reveal_trap",
                   "revived", "sweep", "trap", "trap_hit", "trap_upgrade",
                   "win"]
        for a in actions:
            self._addFlatlandAnimation(dir, a)

    def initPlayerImages(self, dir):
        dir = dir.child("team_players")
        teams = {1 : "blu", 2 : "red"}
        sides = {0 : "dot", 1 : "line", 2 : "cross", 3 : "tri", 4 : "sqr", 5 : "pent", 6 : "hex"}
        firstPerson = {True : "player", False : "team"}
        for t in teams:
            for s in sides:
                for p in firstPerson:
                    path = dir.child("{0}{1}_{2}.png".format(firstPerson[p], teams[t], sides[s]))
                    self.images[("Player", p, t, s)] = Image(path)

    def _addFlatlandAnimation(self, imageDirectory, action):
        # {imageDirectory}/{action}/flatland_{action}XXXX.png
        dir = imageDirectory.child(action)
        self.images[action] = Animation(dir.child("flatland_" + action + "{0:04}.png"))

    def load(self):
        for a in self.images:
            self.images[a].load()
        self.images["resource_pool"].start(12)
        self.images[("enemyTraps", 1)].start(12)
        self.images[("enemyTraps", 2)].start(12)
