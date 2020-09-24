import copy
import math
import random

from g14_animatrix.ani_frame import point
from g14_animatrix.base_animatrix import Animatrix


class Flash(Animatrix):
    frame = []
    newDotDelay = 80
    threshold = 30
    newDotCounter = 60
    dotLength = 120
    dot = point()
    dots = []
    inputMatrix = []

    def __init__(self, matrix_controller):
        super().__init__(matrix_controller)
        self.inputMatrix = []
        for i in range(len(self.mc.rowWidths)):
            self.inputMatrix.append([0xff] * self.mc.rowWidths[i])
        for i in range(len(self.mc.rowWidths)):
            y = 66 + i * 11
            temp = []
            for j in range(self.mc.rowWidths[i]):
                x = 1080 - (45 + j * 30 + (i % 2) * 15)
                t = point()
                t.x = x
                t.y = y
                t.val = 0
                temp.append(copy.deepcopy(t))
            self.frame.append(copy.deepcopy(temp))

    def getDist(self, a, b):
        return math.sqrt((a.y - b.y) * (a.y - b.y) + (a.x - b.x) * (a.x - b.x))

    def remap(self, source, ol, oh, nl, nh):
        orr = oh - ol
        nr = nh - nl
        rat = nr / orr
        return int((source - ol) * rat + nl)

    def updateFrame(self):
        for i in range(len(self.mc.rowWidths)):
            for j in range(self.mc.rowWidths[i]):
                self.frame[i][j].val = 0
        if self.newDotCounter >= self.newDotDelay:
            self.newDotCounter = 0
            newDot = point()
            newDot.y = random.randint(0, 54)
            newDot.x = random.randint(0, self.mc.rowWidths[newDot.y] - 1)
            newDot.val = 0
            newDot = self.frame[newDot.y][newDot.x]
            self.dots.append(copy.deepcopy(newDot))
        else:
            self.newDotCounter += 4
        for i in range(len(self.dots)):
            if self.dots[i].val >= self.dotLength:
                del self.dots[i]
                break
            else:
                self.dots[i].val += 4

        for i in range(len(self.mc.rowWidths)):
            for j in range(self.mc.rowWidths[i]):
                for k in range(len(self.dots)):
                    # print(dots[k].x, " ", dots[k].y)
                    if abs(self.getDist(self.dots[k], self.frame[i][j]) - self.dots[k].val * 1.5) < 20:
                        self.frame[i][j].val = self.remap(
                            20 - abs(self.getDist(self.dots[k], self.frame[i][j]) - self.dots[k].val * 1.5), 0, 20,
                            0, min(self.dots[k].val * 10, max(0, 255 - self.dots[k].val * 3.5)))
                    elif self.dots[k].val > 60 and abs(
                            self.getDist(self.dots[k], self.frame[i][j]) - (self.dots[k].val - 60) * 1.5) < 20:
                        self.frame[i][j].val = self.remap(
                            20 - abs(self.getDist(self.dots[k], self.frame[i][j]) - (self.dots[k].val - 60) * 1.5),
                            0, 20, 0,
                            min(self.dots[k].val * 10, max(0, 255 - (self.dots[k].val - 45) * 4)))
        for i in range(len(self.mc.rowWidths)):
            for j in range(self.mc.rowWidths[i]):
                self.inputMatrix[i][j] = int(self.frame[i][j].val)
        self.mc.drawMatrix(self.inputMatrix)
