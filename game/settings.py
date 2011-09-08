from animation import Image, Animation, LoopingAnimation

class Images:
    def __init__(self, dir):
        self.images = dict()
        self.images["resource_pool"] = Image(dir.child("resource").child("resource_pool.png"))
        self.images["background"] = Image(dir.child("other").child("bg_tile.png"))
        self.images["Attack"] = Animation(dir.child("players").child("attack").child("attack%04d.png"))
        self.images["LevelUp"] = Animation(dir.child("effects").child("player_lvlup").child("player_lvlup%04d.png"))

        self._initPlayerImages(dir)
        self._initBuildingImages(dir)
        self._initArmorImages(dir)

    def _initPlayerImages(self, dir):
        self.images["PlayerScan"] = Image(dir.child("players").child("scan").child("player_scan.png"))
        teamDir = dir.child("players").child("polygons")
        sides = {0 : "dot", 1 : "line", 2 : "cross", 3 : "tri", 4 : "sqr", 5 : "pent", 6 : "hex"}
        firstPerson = {(True, True) : "player", (False, True) : "team", (False, False): "enemy"}
        for p in firstPerson:
            for s in sides:
                path = teamDir.child(sides[s]).child("%s_%s.png" % (sides[s], firstPerson[p]))
                self.images["Player", p, s] = Image(path)
        self.images["Enemy"] = LoopingAnimation(teamDir.child("enemy_unidentified").child("enemy_unidentified%04d.png"))

    def _initBuildingImages(self, dir):
        buildingsDir = dir.child("buildings")

        resource1 = Image(dir.child("resource").child("resource01.png"))
        resource2 = Image(dir.child("resource").child("resource01.png"))

        teammate = {True : "", False : "_enemy"}
        sides = {3 : "trap", 4 : "sentry", 5 : "polyfactory"}
        offsets = {3 : (0, 30), 4 : (0, 55), 5 : (0, 80)}
        for t in teammate:
            self.images["Building", 1, t] = resource1
            self.images["Building", 2, t] = resource2

            for s in sides:
                pathBuilder = buildingsDir
                pathBuilder = pathBuilder.child(sides[s])
                pathBuilder = pathBuilder.child("%s_buildings" % (sides[s]))
                pathBuilder = pathBuilder.child("%s%s.png" % (sides[s], teammate[t]))
                self.images["Building", s, t] = Image(pathBuilder)

                pathBuilder = buildingsDir
                pathBuilder = pathBuilder.child(sides[s])
                pathBuilder = pathBuilder.child("%s_armor%s" % (sides[s], teammate[t]))
                for resources in range(0, s + 1):
                    armorPath = pathBuilder.child("%s_armor%s%02d.png" % (sides[s], teammate[t], resources))
                    self.images["BuildingHealth", t, s, resources] = Image(armorPath, offsets[s])

        self.images["TrapExplosion"] = Animation(dir.child("effects").child("explosion").child("explosion%04d.png"))

    def _initArmorImages(self, dir):
        armorDir = dir.child("players").child("armor")
        sides = {3 : "tri", 4 : "sqr", 5 : "pent", 6 : "hex"}
        for i in sides:
            for j in range(1, i + 1):
                armorPath = armorDir.child("%s_armor" % (sides[i])).child("%s_armor%02d.png" % (sides[i], j))
                self.images["Armor", i, j] = Image(armorPath)

    def _addFlatlandAnimation(self, imageDirectory, action):
        # {imageDirectory}/{action}/flatland_{action}XXXX.png
        dir = imageDirectory.child(action)
        self.images[action] = Animation(dir.child("flatland_" + action + "%04d.png"))

    def load(self):
        for a in self.images:
            self.images[a].load()
        self.images["Enemy"].start(12);
