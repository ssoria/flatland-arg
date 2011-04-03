from animation import Image, Animation, LoopingAnimation

class Images:
    def __init__(self, dir):
        self.images = dict()
        self.images["Building", 1] = Image(dir.child("buildings").child("1_resource.png"))
        self.images["Building", 2] = Image(dir.child("buildings").child("2_resource.png"))
        self.images["Building", 3] = Image(dir.child("buildings").child("trap").child("bd_trap").child("bd_trap.png"))
        self.images["Building", 4] = LoopingAnimation(dir.child("buildings").child("sentry").child("bd_sentry").child("bd_sentry{0:04}.png"))
        self.images["SentryOverlay"] = LoopingAnimation(dir.child("buildings").child("sentry").child("sentry_sight").child("sentry_sight{0:04}.png"))
        self.images["Building", 5] = LoopingAnimation(dir.child("buildings").child("polyfactory").child("bd_polyfactory").child("bd_polyfactory{0:04}.png"))
        self.images[("enemyTraps", 1)] = LoopingAnimation(dir.child("trap_teamblu").child("trap_teamblu{0:04}.png"))
        self.images[("enemyTraps", 2)] = LoopingAnimation(dir.child("trap_teamred").child("trap_teamred{0:04}.png"))
        self.images["resource_pool"] = LoopingAnimation(dir.child("ani_resources").child("resources{0:04}.png"))
        self.images["background"] = Image(dir.child("playing_field.png"))
        self.images["Attack"] = Animation(dir.child("attack").child("attack{0:04}.png"))

        self._initPlayerImages(dir)
        self._initArmorImages(dir)

        actions = ["attack_blocked", "attack_hit", "attack_missed",
                   "building_created", "flatlined", "intro", "lose", "lvldown",
                   "lvlup", "polyfactory", "polyfactory_upgrade",
                   "resource_full", "resource_out", "resourcegather",
                   "reveal_none", "reveal_polyfactory", "reveal_trap",
                   "revived", "sweep", "trap", "trap_hit", "trap_upgrade",
                   "win"]
        for a in actions:
            self._addFlatlandAnimation(dir, a)

    def _initPlayerImages(self, dir):
        dir = dir.child("team_players")
        teams = {1 : "blu", 2 : "red"}
        sides = {0 : "dot", 1 : "line", 2 : "cross", 3 : "tri", 4 : "sqr", 5 : "pent", 6 : "hex"}
        firstPerson = {True : "player", False : "team"}
        for t in teams:
            for s in sides:
                for p in firstPerson:
                    path = dir.child("{0}{1}_{2}.png".format(firstPerson[p], teams[t], sides[s]))
                    self.images[("Player", p, t, s)] = Image(path)
        self.images["Enemy"] = Image(dir.child("enemyid_hidden.png"))

    def _initArmorImages(self, dir):
        self.images["ArmorBreak", 3, 1] = Animation(dir.child("tri_armorbreak").child("tri1_armorbreak{0:04}.png"))
        self.images["ArmorBreak", 3, 2] = Animation(dir.child("tri_armorbreak").child("tri2_armorbreak{0:04}.png"))
        self.images["ArmorBreak", 3, 3] = Animation(dir.child("tri_armorbreak").child("tri3_armorbreak{0:04}.png"))

        dir = dir.child("armor")
        self.images[("Armor", 3, 1)] = Image(dir.child("tri").child("armor1_tri.png"))
        self.images[("Armor", 3, 2)] = Image(dir.child("tri").child("armor2_tri.png"))
        self.images[("Armor", 3, 3)] = Image(dir.child("tri").child("armor3_tri.png"))
        sides = {4 : "sqr", 5 : "pent", 6 : "hex"}
        for i in sides:
            for j in range(1, i + 1):
                self.images["Armor", i, j] = Image(dir.child(sides[i]).child("FIXME_armor{0}.png".format(j)))

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
        self.images["Building", 4].start(24)
        self.images["Building", 5].start(24)
        self.images["SentryOverlay"].start(24)