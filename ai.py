# -*- coding: utf-8 -*-

# python imports
import random

# chillin imports
from chillin_client import RealtimeAI

# project imports
from ks.models import ECell, EDirection, Position
from ks.commands import ChangeDirection, ActivateWallBreaker

from collections import deque
from copy import deepcopy

class AI(RealtimeAI):

    def __init__(self, world):
        super(AI, self).__init__(world)

    def initialize(self):
        print('initialize')
        self.m = len(self.world.board[0])
        self.n = len(self.world.board)
        self.xDir = [0, 1, 0, -1]
        self.yDir = [-1, 0, 1, 0]
        self.attackState = False

    def convertDirToInd(self, curDir):
        #Up0 Right1 Down2 Left3
        if curDir == EDirection.Up:
            return 0
        if curDir == EDirection.Right:
            return 1
        if curDir == EDirection.Down:
            return 2
        if curDir == EDirection.Left:
            return 3

    def convertIndToDir(self, curDir):
        foo = [EDirection.Up, EDirection.Right, EDirection.Down, EDirection.Left]
        return foo[curDir]

    def distanceFromOpp(self, x, y):
        oppX = self.world.agents[self.other_side].position.x
        oppY = self.world.agents[self.other_side].position.y
        return abs(x - oppX) + abs(y - oppY)

    def isValidPos(self, x, y):
        return self.m > x >= 0 and self.n > y >= 0

    def getOppPos(self):
        return [self.world.agents[self.other_side].position.x, self.world.agents[self.other_side].position.y]

    def isEmpty(self, x, y):
        return self.world.board[y][x] == ECell.Empty and self.getOppPos() != [x, y]

    def isEnemyWall(self, x, y):
        if self.other_side == "Blue":
            return self.world.board[y][x] == ECell.BlueWall or self.getOppPos() == [x, y]
        else:
            return self.world.board[y][x] == ECell.YellowWall or self.getOppPos() == [x, y]

    def agentsPotentialCollision(self, curX, curY, curDir):
        myNextX = curX + self.xDir[curDir]
        myNextY = curY + self.yDir[curDir]
        oppLastDir = self.convertDirToInd(self.world.agents[self.other_side].direction)
        oppNextX = self.world.agents[self.other_side].position.x + self.xDir[oppLastDir]
        oppNextY = self.world.agents[self.other_side].position.y + self.yDir[oppLastDir]
        print("tie preventer decision", curDir, "oppLastDir", oppLastDir, "coordinates:", myNextX, oppNextX, myNextY, oppNextY)
        return myNextX == oppNextX and myNextY == oppNextY
    
    def numberOfEmptyNeighbors(self, x, y):
        ans = 0
        for i in range(4):
            newX = x + self.xDir[i]
            newY = y + self.yDir[i]
            if self.isValidPos(newX, newY) and self.isEmpty(newX, newY):
                ans += 1
        return ans

    def emptyNeighbors(self, x, y): #Return direction ind to empty neighbors
        ans = []
        xDir = [0, 1, 0, -1]
        yDir = [-1, 0, 1, 0]
        for i in range(4):
            newX = x + self.xDir[i]
            newY = y + self.yDir[i]
            if self.isValidPos(newX, newY) and self.isEmpty(newX, newY):
                ans.append(i)
        return ans

    def playerWallNeighbors(self, x, y): #Return direction ind to player-wall neighbors
        ans = []
        xDir = [0, 1, 0, -1]
        yDir = [-1, 0, 1, 0]
        for i in range(4):
            newX = x + self.xDir[i]
            newY = y + self.yDir[i]
            if self.isValidPos(newX, newY) and self.world.board[newY][newX] in [ECell.BlueWall, ECell.YellowWall]:
                ans.append(i)
        return ans

    def notAreaWallNeighbors(self, x, y): #Return direction ind to not-Area-wall neighbors
        ans = []
        xDir = [0, 1, 0, -1]
        yDir = [-1, 0, 1, 0]
        for i in range(4):
            newX = x + self.xDir[i]
            newY = y + self.yDir[i]
            if self.isValidPos(newX, newY) and self.world.board[newY][newX] != ECell.AreaWall:
                ans.append(i)
        return ans
                
    def opposite(self, curDir):
        #Up0 Right1 Down2 Left3
        if curDir == 0:
            return 2
        if curDir == 1:
            return 3
        if curDir == 2:
            return 0
        if curDir == 3:
            return 1

    def reachableSpace(self, x, y, curDir):
        originX = x
        originY = y
        x += self.xDir[curDir]
        y += self.yDir[curDir]
        queue = deque([[x, y]])
        mark = [[-1] * self.m for i in range(self.n)]
        mark[y][x] = 0
        ans = 1
        while len(queue) > 0:
            left = queue.popleft()
            for i in self.emptyNeighbors(left[0], left[1]):
                newX = left[0] + self.xDir[i]
                newY = left[1] + self.yDir[i]
                if mark[newY][newX] == -1 and (newX != originX or newY != originY):
                    queue.append([newX, newY])
                    ans += 1
                    mark[newY][newX] = mark[left[1]][left[0]] + 1
        print("Reachable space from [", x, y, "] is: ", ans)
        return ans

    def reachableEmptyWB(self, x, y, curDir): #Return escape path length (It is just a useless trash function)
        originX = x
        originY = y
        x += self.xDir[curDir]
        y += self.yDir[curDir] 
        queue = deque([[x, y, 1]])
        mark = [[-1] * self.m for i in range(self.n)]
        mark[y][x] = 0
        while len(queue) > 0:
            left = queue.popleft()            
            for i in self.notAreaWallNeighbors(left[0], left[1]):
                newX = left[0] + self.xDir[i]
                newY = left[1] + self.yDir[i]
                if self.isEmpty(newX, newY) and (newX != originX or newY != originY):
                    return left[2] + 1 
                if mark[newY][newX] == -1 and (newX != originX or newY != originY):
                    queue.append([newX, newY, left[2] + 1])
                    mark[newY][newX] = mark[left[1]][left[0]] + 1
        print("Not found any escape path")
        return float("inf")

    def mostOpenDecision(self, x, y):
        ma = -1
        moves = []

        optionsList = self.emptyNeighbors(x, y)
        random.shuffle(optionsList)
        
        for i in optionsList:
            res = self.reachableSpace(x, y, i)
            if res > ma:
                ma = res
                moves = [i]
            elif res == ma:
                moves.append(i)
        
        ma = -1
        ans = -1
        for i in moves:
            newX = x + self.xDir[i]
            newY = y + self.yDir[i]
            cnt = self.numberOfEmptyNeighbors(newX, newY)
            if ma < cnt:
                ma = cnt
                ans = i
        return ans

    def checkEscape(self, x, y, markPtr, rem = None): #Returns bool
        mark = deepcopy(markPtr)
        mark[y][x] = 1
        if rem == None:
            maxWallBreaker = self.world.constants.wall_breaker_duration - 1
        else:
            maxWallBreaker = rem - 1

        queue = deque([[x, y, 1]]) #Third number indicates height of cell in BFS tree
        while len(queue) > 0:
            left = queue.popleft()
            for i in self.notAreaWallNeighbors(left[0], left[1]):
                newX = left[0] + self.xDir[i]
                newY = left[1] + self.yDir[i]

                if self.isEmpty(newX, newY) and left[2] <= maxWallBreaker and mark[newY][newX] == -1 and self.reachableSpace(left[0], left[1], i) >= self.world.constants.wall_breaker_cooldown:
                    print("maxWB", maxWallBreaker, "left2", left[2], "x", x, "y", y)
                    return True

                if not self.isEmpty(newX, newY) and left[2] + 1 <= maxWallBreaker and mark[newY][newX] == -1:
                    queue.append([newX, newY, left[2] + 1])
        return False

    def prepareAttackDecision(self, x, y, rem = None): #Return good decision to prepare an attack to enemy's wall
        originX = x
        originY = y
        queue = deque([[x, y, -1]]) #Third number indicates that what was first direction made in the beginning
        mark = [[-1] * self.m for i in range(self.n)]
        mark[y][x] = 0
        
        #print("queue:")
        #print(queue)

        curDir = self.convertDirToInd(self.world.agents[self.my_side].direction) #Dir index stored

        #We use alternative when we can not find any escapable opponent wall
        alternative = -1
        alternativeFlg = False
        while len(queue) > 0:
            #print("len queue:", len(queue))
            left = queue.popleft()

            optionsList = self.notAreaWallNeighbors(left[0], left[1])
            random.shuffle(optionsList)
            for i in optionsList:
                if left[2] == -1 and i == self.opposite(curDir): #We can not break last created of our walls
                    continue
                
                newX = left[0] + self.xDir[i]
                newY = left[1] + self.yDir[i]

                """Debug
                if originX == 25 and originY == 2:
                    print("Debug", newX, newY, self.isEnemyWall(newX, newY), self.checkEscape(newX, newY, mark), mark[newY][newX], left[2])"""

                if self.isEmpty(newX, newY) and mark[newY][newX] == -1:
                    firstDir = left[2]
                    if firstDir == -1: #First time we make a direction
                        firstDir = i
                    queue.append([newX, newY, firstDir])
                    mark[newY][newX] = mark[left[1]][left[0]] + 1

                elif self.isEnemyWall(newX, newY) and self.checkEscape(newX, newY, mark, rem) and mark[newY][newX] == -1:
                    if left[2] != -1:
                        return left[2]
                    else: #First time we make a direction (destination enemy wall is one of neighbor cells)
                        self.send_command(ActivateWallBreaker())
                        print("WALLLLBBBBBBBBBBBBBBBBBBBBBBBRRRRRRRR1111111111111")
                        self.attackState = True
                        return i

                elif not self.isEmpty(newX, newY) and self.checkEscape(newX, newY, mark, rem) and mark[newY][newX] == -1:
                    if left[2] != -1:
                        if alternative == -1: #This condition assure us we chose first good wall we seen
                            alternative = left[2]
                    else: #First time we make a direction
                        alternativeFlg = True
                        alternative = i
                        print("alternative Onnnnn", alternative)
        if alternativeFlg:
            self.send_command(ActivateWallBreaker())
            print("WALLLLBBBBBBBBBBBBBBBBBBBBBBBRRRRRRRR2222222222222")
            self.attackState = True
            return alternative
        else:
            return -1

    def decide(self):
        print('decide', self.current_cycle, self.my_side)
        #every cycle
        #500ms
        curX = self.world.agents[self.my_side].position.x
        curY = self.world.agents[self.my_side].position.y
        curDir = self.convertDirToInd(self.world.agents[self.my_side].direction) #Dir index stored
        decision = -1 #Not made yet
        if self.attackState and self.world.agents[self.my_side].wall_breaker_rem_time == 1:
            self.attackState = False
            print("1st if")
            decision = self.mostOpenDecision(curX, curY)
        elif self.attackState and self.world.agents[self.my_side].wall_breaker_rem_time > 1:
            print("2nd if")
            decision = self.prepareAttackDecision(curX, curY, self.world.agents[self.my_side].wall_breaker_rem_time)
        elif not self.attackState and self.world.agents[self.my_side].wall_breaker_cooldown == 0:
            print("first if")
            decision = self.prepareAttackDecision(curX, curY)
            #What if there was not any opponent neighbor wall reachable from current cell?
        elif not self.attackState and self.world.agents[self.my_side].wall_breaker_cooldown != 0:
            print("second if")
            decision = self.mostOpenDecision(curX, curY)
            #What if there was not any empty neighbors in this case?

        if decision == -1:
            print("third if")
            decision = self.mostOpenDecision(curX, curY)
            #What is this case use for exactly??? turn 0 and ...?
        if self.agentsPotentialCollision(curX, curY, decision) and self.world.scores[self.my_side] <= self.world.scores[self.other_side]:
            print("fourth if")
            decision = self.mostOpenDecision(curX, curY)
        
        print("decision:", decision)
        
        self.send_command(ChangeDirection(self.convertIndToDir(decision)))
