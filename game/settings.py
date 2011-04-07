from animation import Image, Animation, LoopingAnimation

class Images:
    def __init__(self, dir):
        self.images = dict()
        self.images[("enemyTraps", 1)] = LoopingAnimation(dir.child("trap_teamblu").child("trap_teamblu{0:04}.png"))
        self.images[("enemyTraps", 2)] = LoopingAnimation(dir.child("trap_teamred").child("trap_teamred{0:04}.png"))
        self.images["resource_pool"] = LoopingAnimation(dir.child("ani_resources").child("resources{0:04}.png"))
        self.images["background"] = Image(dir.child("playing_field.png"))
        self.images["Attack"] = Animation(dir.child("attack").child("attack{0:04}.png"))
        self.images["LevelDown", 1, 6] = Animation(dir.child("lvl_down").child("teamblu").child("hex_lvldown").child("hex_lvldown{0:04}.png"))

        self._initPlayerImages(dir)
        self._initBuildingImages(dir)
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
        self.images["PlayerScan"] = Image(dir.child("player_scan.png"))
        teamDir = dir.child("team_players")
        teams = {1 : "blu", 2 : "red"}
        sides = {1 : "line", 2 : "cross", 3 : "tri", 4 : "sqr", 5 : "pent", 6 : "hex"}
        firstPerson = {True : "player", False : "team"}
        for t in teams:
            for p in firstPerson:
                imgName = "{0}{1}_death".format(firstPerson[p], teams[t])
                self.images["Player", p, t, 0] = LoopingAnimation(dir.child("death").child(imgName).child(imgName + "{0:04}.png"))
                for s in sides:
                    path = teamDir.child("{0}{1}_{2}.png".format(firstPerson[p], teams[t], sides[s]))
                    self.images[("Player", p, t, s)] = Image(path)
        self.images["Enemy"] = Image(teamDir.child("enemyid_hidden.png"))

    def _initBuildingImages(self, dir):
        buildingsDir = dir.child("buildings")
        self.images["Building", 1] = Image(buildingsDir.child("1_resource.png"))
        self.images["Building", 2] = Image(buildingsDir.child("2_resource.png"))
        self.images["Building", 3] = Image(buildingsDir.child("trap").child("bd_trap").child("bd_trap.png"))
        self.images["Building", 4] = LoopingAnimation(buildingsDir.child("sentry").child("bd_sentry").child("bd_sentry{0:04}.png"))
        self.images["SentryOverlay"] = LoopingAnimation(buildingsDir.child("sentry").child("sentry_sight").child("sentry_sight{0:04}.png"))
        self.images["Building", 5] = LoopingAnimation(buildingsDir.child("polyfactory").child("bd_polyfactory").child("bd_polyfactory{0:04}.png"))
        self.images["TrapExplosion"] = LoopingAnimation(buildingsDir.child("trap").child("trap_explosion").child("trap_explosion{0:04}.png"), (0, -150))

        teams = {1 : "blu", 2 : "red"}
        offsets = {3 : (0, 30), 4 : (0, 55), 5 : (0, 80)}
        healthDir = dir.child("building_health")
        for t in teams:
            self.images["Upgrade", t] = LoopingAnimation(dir.child("tooltip").child("team{0}".format(teams[t])).child("tt{0}_upgrade".format(teams[t])).child("tt{0}_upgrade".format(teams[t]) + "{0:04}.png"))
            self.images["Build", t] = LoopingAnimation(dir.child("tooltip").child("team{0}".format(teams[t])).child("tt{0}_build".format(teams[t])).child("tt{0}_build".format(teams[t]) + "{0:04}.png"))
            self.images["HarvestResources", t] = LoopingAnimation(dir.child("tooltip").child("team{0}".format(teams[t])).child("tt{0}_resource".format(teams[t])).child("tt{0}_resource".format(teams[t]) + "{0:04}.png"))
            self.images["EnemyBuilding", t] = LoopingAnimation(dir.child("tooltip").child("team{0}".format(teams[t])).child("tt{0}_enemy".format(teams[t])).child("tt{0}_enemy".format(teams[t]) + "{0:04}.png"))
            teamDir = healthDir.child("team{0}".format(teams[t]))
            for sides in range(3, 6):
                buildingDir = teamDir.child("health{0}".format(sides))
                offset = offsets[sides]
                for resources in range(0, sides + 1):
                    path = buildingDir.child("health{0}_{1}of{2}.png".format(teams[t], resources, sides))
                    self.images["BuildingHealth", t, sides, resources] = Image(path, offset)

    def _initArmorImages(self, dir):
        shapes = {3 : "tri",
                  4 : "sqr",
                  5 : "pent",
                  6 : "hex"}
        armorBreakDir = dir.child("armorbreak")
        for sides in shapes:
            shapeDir = armorBreakDir.child(shapes[sides])
            for resources in range(1, sides + 1):
                imgName = "{0}_armorbreak{1}".format(shapes[sides], resources)
                path = shapeDir.child(imgName).child(imgName + "{0:04}.png")
                self.images["ArmorBreak", sides, resources] = Animation(path)

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
        for t in [1, 2]:
            self.images["Upgrade", t].start(24)
            self.images["Build", t].start(24)
            self.images["HarvestResources", t].start(24)
            self.images["EnemyBuilding", t].start(24)
            self.images["Player", True, t, 0].start(24)
            self.images["Player", False, t, 0].start(24)
