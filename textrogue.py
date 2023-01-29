# simple text-based roguelike
# tdwsl 2023

import random
import math

mapw = 50
maph = 30
map = []
explored = []
player = 0
level = 1
turn = 0

dirs = [[0,-1], [1,0], [0,1], [-1,0]]
dirLetters = ["N", "E", "S", "W"]
dirNames = ["north", "east", "south", "west", "somewhere"]

sightDist = 5

tl_rock = 0
tl_wall = 1
tl_room = 2
tl_door = 3
tl_path = 4
tl_temp = 5
tl_up = 6
tl_down = 7
tl_oob = 20
tl_blocked = 20
tl_tdoor = 20

tileChars = [" ", "#", ".", "+", "-", "T", "<", ">"]
tileNames = ["r", "w", "rm", "a door", "p", "t", "the entrance", "the exit"]

def inBounds(x, y):
    return x >= 0 and y >= 0 and x < mapw and y < maph

def getTile(x, y):
    if inBounds(x, y):
        return map[y*mapw+x]
    return tl_oob

def setTile(x, y, t):
    if inBounds(x, y):
        map[y*mapw+x] = t

def pathMap(allowed, x2, y2):
    pmap = []
    for i in range(mapw*maph):
        pmap.append(0 if map[i] in allowed else -1)
    pmap[y2*mapw+x2] = 1
    g = 0
    while True:
        g += 1
        nutin = True
        for i in range(mapw*maph):
            if pmap[i] == g:
                nutin = False
                for d in dirs:
                    x = i%mapw + d[0]
                    y = i//mapw + d[1]
                    if inBounds(x, y):
                       if pmap[y*mapw+x] == 0:
                           pmap[y*mapw+x] = g+1
        if nutin:
            break
    return pmap

def findPath(allowed, x1, y1, x2, y2):
    if not map[y1*mapw+x1] in allowed or not map[y2*mapw+x2] in allowed:
        return []
    pmap = pathMap(allowed, x2, y2)
    if pmap[y1*mapw+x1] == 0:
        return []
    x = x1
    y = y1
    path = []
    while x != x2 or y != y2:
        for d in dirs:
            dx = x+d[0]
            dy = y+d[1]
            if inBounds(dx, dy):
                if pmap[dy*mapw+dx] == pmap[y*mapw+x]-1:
                    x = dx
                    y = dy
                    break
        path.append([x, y])
    return path

def sees(x1, y1, x2, y2):
    if x1 == x2 and y1 == y2:
        return True
    xd = x2-x1
    yd = y2-y1
    if xd*xd+yd*yd > sightDist*sightDist:
        return False
    m = 0
    if abs(xd) > abs(yd):
        m = abs(xd)
    else:
        m = abs(yd)
    for i in range(1, m+1):
        x = math.floor(x1+(xd*i)/m+0.5)
        y = math.floor(y1+(yd*i)/m+0.5)
        if x == x1 and y == y1:
            continue
        if not inBounds(x, y):
            return False
        if x == x2 and y == y2:
            return True
        if map[y*mapw+x] in [tl_door, tl_wall, tl_rock]:
            return False
    return False

def getFov(x, y):
    fov = []
    for i in range(mapw*maph):
        fov.append(sees(x, y, i%mapw, i//mapw))
    return fov

def updateExplored(fov):
    for i in range(mapw*maph):
        if fov[i]:
            explored[i] = True

class Actor:
    actors = []
    passable = [tl_door, tl_path, tl_room, tl_up, tl_down]

    def __init__(self, x=0, y=0, hp=5, mp=0, name="actor"):
        self.x = x
        self.y = y
        self.name = name
        self.hp = hp
        self.mhp = hp
        self.mp = mp
        self.mmp = mp
        self.lvl = 0
        self.xp = 0
        self.mxp = 0
        self.dead = False
        self.under = tl_room
        Actor.actors.append(self)

    def calcStr(self, a):
        return self.str - a.str//4

    def block(self):
        if not self.dead:
            self.under = map[self.y*mapw+self.x]
            map[self.y*mapw+self.x] = tl_blocked

    def unblock(self):
        if not self.dead:
            map[self.y*mapw+self.x] = self.under

    def meleeAttack(self, a):
        visible = sees(player.x, player.y, self.x, self.y)
        str = self.calcStr(a)
        a.hp -= str
        if visible:
            print("{} attacks {} for {} damage.".format \
                  (self.name, a.name, str))
        if a.hp <= 0:
            if visible:
                print("{} dies!".format(a.name))
            a.dead = True
            self.xp += a.lvl

    def actorAt(x, y):
        for a in Actor.actors:
            if a.x == x and a.y == y and not a.dead:
                return a
        return False

    def move(self, x, y):
        if self.dead:
            return 0
        if x == self.x and y == self.y:
            return 1
        if not getTile(x, y) in Actor.passable:
            return 0
        a = Actor.actorAt(x, y)
        if a != False:
            self.meleeAttack(a)
            return 2
        self.x = x
        self.y = y
        return 1

    def wander(self):
        mdirs = dirs.copy()
        random.shuffle(mdirs)
        for d in mdirs:
            if Actor.actorAt(self.x+d[0], self.y+d[1]) == False:
                if getTile(self.x+d[0], self.y+d[1]) in Actor.passable:
                    self.x += d[0]
                    self.y += d[1]
                    return

    def update(self):
        if turn % 8 == 0 and not self.dead and self.hp < self.mhp:
            self.hp += 1

    def enemyUpdate(self):
        if self.dead:
            return
        if sees(self.x, self.y, player.x, player.y):
            self.approach(player.x, player.y)
        else:
            self.wander()

    def approach(self, x, y):
        for a in Actor.actors:
            a.block()
        a = Actor.actorAt(x, y)
        if a != False:
            a.unblock()
        self.unblock()
        p = findPath(Actor.passable, self.x, self.y, x, y)
        if len(p) != 0:
            self.move(p[0][0], p[0][1])
        for a in Actor.actors:
            a.unblock()

    def moveAlert(self, x, y):
        d = [x-self.x, y-self.y]
        m = self.move(x, y)
        if m == 1:
            di = 4
            for i in range(4):
                if dirs[i][0] == d[0] and dirs[i][1] == d[1]:
                    di = i
                    break
            print("You move {}.".format(dirNames[di]))
        elif m == 0:
            print("You can't go that way.")
            return False
        return True

def connectRooms(rooms):
    for i in range(len(rooms)-1):
        r1 = rooms[i]
        r2 = rooms[i+1]
        path = findPath([tl_door, tl_tdoor, tl_room, tl_path, tl_rock], \
                        r1[0], r1[1], r2[0], r2[1])
        for p in path:
            t = map[p[1]*mapw+p[0]]
            if t == tl_rock:
                map[p[1]*mapw+p[0]] = tl_path
            elif t == tl_tdoor:
                map[p[1]*mapw+p[0]] = tl_door
        for i in range(len(path)):
            p = path[i]
            if i % 3 != 0:
                for d in dirs:
                    if getTile(p[0]+d[0], p[1]+d[1]) == tl_rock:
                        setTile(p[0]+d[0], p[1]+d[1], tl_temp)

def generateMap(up=False):
    global map
    global player
    global explored
    global turn
    t = tl_temp
    p = tl_path
    d = tl_tdoor
    D = tl_door
    w = tl_wall
    r = tl_room
    k = tl_rock
    prefabs = [
        [
            7,6, 3,2,
           [t,t,t,t,t,t,t,
            t,p,p,p,t,p,p,
            t,p,t,p,t,p,t,
            t,p,t,p,t,p,t,
            p,p,t,p,p,p,t,
            t,t,t,t,t,t,t]
        ],
        [
            7,5, 3,1,
           [t,t,t,t,t,p,t,
            t,p,p,p,p,p,t,
            t,p,t,t,t,t,t,
            t,p,p,p,p,p,t,
            t,t,t,t,t,p,t]
        ],
        [
            5,5, 2,1,
           [t,t,d,t,t,
            t,p,p,p,t,
            d,p,t,p,d,
            t,p,p,p,t,
            t,t,d,t,t]
        ],
        [
            9,6, 2,3,
           [w,d,w,w,k,w,w,d,w,
            w,r,r,w,p,D,r,r,w,
            d,r,r,w,p,w,r,r,w,
            w,r,r,w,p,w,r,r,w,
            w,r,r,D,p,w,r,r,d,
            w,w,w,w,k,w,d,w,w]
        ]
    ]
    map = []
    grid = []
    gridw = 4
    gridh = 4
    maxw = mapw // gridw
    maxh = maph // gridh
    minw = maxw - 5
    minh = 4
    for i in range(mapw*maph):
        map.append(tl_rock)
    for i in range(gridw*gridh):
        grid.append(False)
    rn = random.randrange(7, 10)
    rooms = []
    last = [0,0]
    for ri in range(rn):
        i = random.randrange(0, gridw*gridh)
        while grid[i]:
            i = (i+1)%(gridw*gridh)
        grid[i] = True
        cx = (i%gridw) * maxw + maxw//2
        cy = (i//gridw) * maxh + maxh//2
        if ri != 0 and random.randrange(0, 3) == 0:
            pf = random.choice(prefabs)
            for i in range(pf[0]*pf[1]):
                x = cx - pf[0]//2 + i % pf[0]
                y = cy - pf[1]//2 + i // pf[0]
                map[y*mapw+x] = pf[4][i]
            rooms.append([cx-pf[0]//2+pf[2], cy-pf[1]//2+pf[3]])
            continue
        w = random.randrange(minw, maxw)
        h = random.randrange(minh, maxh)
        if maxw-w > 1:
            cx += random.randrange((maxw-w)//-2+1, (maxw-w)//2)
        if maxh-h > 1:
            cy += random.randrange((maxh-h)//-2+1, (maxh-h)//2)
        for y in range(cy-h//2, cy+h//2):
            for x in range(cx-w//2, cx+w//2):
                map[y*mapw+x] = tl_wall
        for y in range(cy-h//2+1, cy+h//2-1):
            for x in range(cx-w//2+1, cx+w//2-1):
                map[y*mapw+x] = tl_room
        x = random.randrange(cx-w//2+1, cx+w//2-1)
        map[(cy-h//2)*mapw+x] = tl_tdoor
        x = random.randrange(cx-w//2+1, cx+w//2-1)
        map[(cy+h//2-1)*mapw+x] = tl_tdoor
        y = random.randrange(cy-h//2+1, cy+h//2-1)
        map[y*mapw+cx-w//2] = tl_tdoor
        y = random.randrange(cy-h//2+1, cy+h//2-1)
        map[y*mapw+cx+w//2-1] = tl_tdoor
        last = [cx, cy]
        rooms.append([cx, cy])
    if up:
        rg = range(0, len(rooms)-1)
    else:
        rg = range(1, len(rooms))
    Actor.actors = [player]
    if level >= 1:
        for i in rg:
            r = rooms[i]
            if random.randrange(0, 4) != 0:
                gob = Actor(x=r[0], y=r[1], name="Goblin", hp=5)
                gob.str = 2
                gob.lvl = 1
    first = rooms[0]
    connectRooms(rooms)
    random.shuffle(rooms)
    connectRooms(rooms)
    for i in range(mapw*maph):
        if map[i] == tl_temp:
            map[i] = tl_rock
        elif map[i] == tl_tdoor:
            map[i] = tl_rock
        elif map[i] == tl_wall:
            map[i] = tl_rock
    map[first[1]*mapw+first[0]] = tl_up
    map[last[1]*mapw+last[0]] = tl_down
    if up:
        player.x = last[0]
        player.y = last[1]
    else:
        player.x = first[0]
        player.y = first[1]
    explored = []
    for i in range(mapw*maph):
        explored.append(not map[i] in Actor.passable)
    updateExplored(getFov(player.x, player.y))
    turn = 0

def printMap():
    for i in range(mapw*maph):
        print(tileChars[map[i]], end="")
        if (i+1)%mapw == 0:
            print("")

def roomSize(x, y):
    rx = x
    ry = y
    nroom = [tl_door, tl_rock, tl_path]
    while not getTile(rx, y) in nroom:
        rx -= 1
    while not getTile(x, ry) in nroom:
        ry -= 1
    rx2 = x
    ry2 = y
    while not getTile(rx2, y) in nroom:
        rx2 += 1
    while not getTile(x, ry2) in nroom:
        ry2 += 1
    rx += 1
    ry += 1
    rx2 -= 1
    ry2 -= 1
    return [rx, ry, rx2-rx+1, ry2-ry+1]

def whereStr(x1, y1, x2, y2):
    if x1 == x2 and y1 == y2:
        return "here"
    str = "at"
    if x2 < x1:
        str += " {} W".format(x1-x2)
    elif x2 > x1:
        str += " {} E".format(x2-x1)
    if y2 < y1:
        str += " {} N".format(y1-y2)
    elif y2 > y1:
        str += " {} S".format(y2-y1)
    return str

listVars = []

def listStart(start1, start2):
    global listVars
    listVars = [start1, start2, True]

def listItem(str):
    global listVars
    start = listVars[1]
    if listVars[2]:
        listVars[2] = False
        start = listVars[0]
    print("{} {}".format(start, str))

def describe(x, y, status=True):
    print()
    if status:
        print("HP {}/{} MP {}/{}".format(player.hp, player.mhp, \
              player.mp, player.mmp))
    fov = getFov(x, y)
    if map[y*mapw+x] == tl_door:
        print("You are in a doorway")
        listStart("There is", "And")
        for i in range(len(dirs)):
            d = dirs[i]
            t = getTile(x+d[0], y+d[1])
            if t == tl_rock:
                continue
            if t == tl_path:
                listItem("a corridor {}".format(dirNames[i]))
            elif t != tl_door:
                sz = roomSize(x+d[0], y+d[1])
                listItem("a {}x{} room {}".format \
                      (sz[2], sz[3], dirNames[i]))
    elif map[y*mapw+x] == tl_path:
        ptype = ""
        for i in range(len(dirs)):
            d = dirs[i]
            if getTile(x+d[0], y+d[1]) == tl_path:
                ptype += " " + dirLetters[i]
        print("You are in a{} corridor".format(ptype))
        listStart("With", "And")
        for di in range(len(dirs)):
            d = dirs[di]
            if getTile(x+d[0], y+d[1]) != tl_path:
                continue
            xx = x
            yy = y
            while getTile(xx+d[0], yy+d[1]) == tl_path:
                xx += d[0]
                yy += d[1]
                if not sees(x, y, xx, yy):
                    break
                fork = []
                for i in range(len(dirs)):
                    dd = dirs[i]
                    if getTile(xx+dd[0], yy+dd[1]) == tl_path:
                        fork.append(i)
                if len(fork) == 1:
                    dd = dirs[fork[0]]
                    if getTile(xx+dd[0], yy+dd[1]) == tl_rock:
                        listItem("a dead end {}".format \
                              (whereStr(x, y, xx+dd[0], yy+dd[1])))
                elif len(fork) == 2 and not di in fork:
                    ttype = ""
                    for fd in fork:
                        if fd != (di+2)%4:
                            ttype = dirLetters[fd]
                    listItem("a {} turn {}".format \
                             (ttype, whereStr(x, y, xx, yy)))
                elif len(fork) > 2:
                    ftype = ""
                    for fd in fork:
                        if fd != (di+2)%4:
                            ftype += " " + dirLetters[fd]
                    listItem("a{} fork {}".format \
                             (ftype, whereStr(x, y, xx, yy)))
    else:
        sz = roomSize(x, y)
        print("You are in a {}x{} room at {} {}".format \
              (sz[2], sz[3], x-sz[0], y-sz[1]))
    mapObjects = []
    listStart("There is", "And")
    for i in range(mapw*maph):
        if fov[i]:
            if map[i] in [tl_door, tl_up, tl_down]:
                xd = i%mapw-x
                yd = i//mapw-y
                listItem("{} {}".format \
                      (tileNames[map[i]], \
                       whereStr(x, y, i%mapw, i//mapw)))
    listStart("There is", "And")
    for a in Actor.actors:
        if a != player:
            if sees(x, y, a.x, a.y):
                if a.dead:
                    listItem("a dead {} {}".format \
                             (a.name, whereStr(x, y, a.x, a.y)))
                else:
                    listItem("a {} {}".format \
                             (a.name, whereStr(x, y, a.x, a.y)))

def gameOver():
    print("GAME OVER")

def leaveDungeon():
    print("You leave the dungeon.")

def update():
    global turn
    for a in Actor.actors:
        a.update()
        if a != player:
            a.enemyUpdate()
    turn += 1

def safe():
    for a in Actor.actors:
        if a != player and not a.dead:
            if sees(player.x, player.y, a.x, a.y):
                return False
    return True

def autoMove(x, y):
    old = map[player.y*mapw+player.x]
    player.moveAlert(x, y)
    update()
    updateExplored(getFov(player.x, player.y))
    if old == tl_door and map[player.y*mapw+player.x] == tl_room:
        describe(player.x, player.y, status=False)

def explore():
    all = True
    for x in explored:
        if not x:
            all = False
            break
    if all:
        print("Map explored.")
        return False
    if not safe():
        print("Monsters nearby.")
        describe(player.x, player.y)
        return False
    pmap = pathMap(Actor.passable, player.x, player.y)
    closest = player.y*mapw+player.x
    for i in range(mapw*maph):
        if explored[i] == False:
            if explored[closest] or pmap[i] < pmap[closest]:
                closest = i
    p = findPath(Actor.passable, player.x, player.y, \
                 closest%mapw, closest//mapw)
    if len(p) == 0:
        print("Explored all accessible areas.")
        return False
    autoMove(p[0][0], p[0][1])
    return True

def rest():
    hp = player.hp != player.mhp
    mp = player.mp != player.mmp
    if not mp and not hp:
        print("No need.")
        return
    while True:
        if safe():
            update()
            if player.hp == player.mhp and hp:
                print("HP restored")
            if player.mp == player.mmp and mp:
                print("MP restored")
                break
            if player.hp == player.mhp and hp:
                break
        else:
            print("Monsters nearby.")
            break
    describe(player.x, player.y)

def findTile(t):
    pmap = pathMap(Actor.passable, player.x, player.y)
    closest = -1
    for i in range(mapw*maph):
        if map[i] == t and explored[i] and pmap[i] > 1:
            if closest == -1:
                closest = i
            elif pmap[i] < pmap[closest]:
                closest = i
    return closest

def target(x2, y2, str):
    path = findPath(Actor.passable, player.x, player.y, x2, y2)
    if len(path) == 0:
        print("No path.")
        return
    for p in path:
        if not safe():
            print("Monsters nearby.")
            describe(player.x, player.y)
            return
        autoMove(p[0], p[1])
    print("Arrived at {}.".format(str))
    describe(player.x, player.y)

def yes(prompt):
    yn = input("{} y/N ".format(prompt)).strip().lower()
    return yn in ["y", "ye", "yes", "yeah"]

player = Actor(name="Player", hp=10)
player.lvl = 1
player.mxp = 10
player.str = 3

helpList = [
    ["help", "Show this list"],
    ["north/east/south/west", "Move/attack in a direction"],
    ["up/down", "Ascend/descend stairs"],
    ["look", "Repeat description of surroundings"],
    ["quit", "Quit the game"],
    ["go <location>", "Go to a known location on the map"],
    ["rest", "Rest until HP/MP are restored"],
    ["explore", "Explore the map"],
]

helpExtra = [
    "Commands are auto-complete (e.g. \"ex\" instead of \"explore\")",
    "\"go\" will accept door, entrance or exit",
]

print("textrogue - tdwsl 2022")
print("Type \"help\" for a list of game commands")

generateMap()
#printMap()

upd = False
describe(player.x, player.y)
while True:
    if upd:
        update()
        if player.hp <= 0:
            gameOver()
            break
        describe(player.x, player.y)
        updateExplored(getFov(player.x, player.y))
    upd = False
    line = input(">").strip().lower().split(" ")
    if line[0] == "":
        print("Enter a command.")
    elif "north".startswith(line[0]):
        upd = player.moveAlert(player.x, player.y-1)
    elif "east".startswith(line[0]):
        upd = player.moveAlert(player.x+1, player.y)
    elif "south".startswith(line[0]):
        upd = player.moveAlert(player.x, player.y+1)
    elif "west".startswith(line[0]):
        upd = player.moveAlert(player.x-1, player.y)
    elif "up".startswith(line[0]):
        if map[player.y*mapw+player.x] == tl_up:
            if level == 1:
                if yes("Leave the dungeon?"):
                    leaveDungeon()
                    break
            else:
                print("You ascend up a maze of stairs...")
                level -= 1
                generateMap(up=True)
                describe(player.x, player.y)
        else:
            print("There is no way up here.")
    elif "down".startswith(line[0]):
        if map[player.y*mapw+player.x] == tl_down:
            print("You descend down a maze of stairs...")
            level += 1
            generateMap()
            describe(player.x, player.y)
        else:
            print("There is no way down here.")
    elif "wait".startswith(line[0]):
        print("You wait.")
        upd = True
    elif "quit".startswith(line[0]):
        #if yes("Really quit?"):
            #break
        break
    elif "help".startswith(line[0]):
        print()
        for h in helpList:
            print("{}{}{}".format(h[0], "\t"*(3 - len(h[0])//8), h[1]))
        print()
        for h in helpExtra:
            print(h)
    elif "look".startswith(line[0]):
        describe(player.x, player.y)
    elif "explore".startswith(line[0]):
        while explore():
            continue
    elif "rest".startswith(line[0]):
        rest()
    elif "go".startswith(line[0]):
        if not safe():
            print("Monsters nearby.")
            continue
        if len(line) > 1:
            if line[1] == "to":
                del line[1]
        else:
            line.append("####")
        options = ["entrance", "exit", "door"]
        for o in options:
            if o.startswith(line[1]):
                line[1] = o
                break
        xy = 0
        if line[1] == "entrance":
            xy = findTile(tl_up)
        elif line[1] == "exit":
            xy = findTile(tl_down)
        elif line[1] == "door":
            xy = findTile(tl_door)
        else:
            print("Invalid location.")
            continue
        if xy == -1:
            print("Couldn't find location - try exploring first.")
            continue
        print("Targeting {} {}".format \
              (line[1], whereStr(player.x, player.y, xy%mapw, xy//mapw)))
        target(xy%mapw, xy//mapw, line[1])
    else:
        print("You can't do that.")
