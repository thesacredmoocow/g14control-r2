from winusbpy import *
import time
import keyboard
import random
class MatrixController(object):
    vid = "0b05"
    pid = "193b"
    connected = False
    initPacket = [0x5e]
    for char in "ASUS Tech.Inc.":
        initPacket.append(ord(char))
    initPacket += [0]*625
    
    firstPane = [0x5e, 0xc0, 0x02, 0x01, 0x00, 0x73, 0x02]
    firstPane += [0x00]*633
    
    secondPane = [0x5e, 0xc0, 0x02, 0x74, 0x02, 0x73, 0x02]
    secondPane += [0x00]*633
    
    flushPacket = [0x5e, 0xc0, 0x03]
    flushPacket += [0x00]*637
    
    api = WinUsbPy()
    setupPacket = UsbSetupPacket(0x21, 0x09, 0x035e, 0x00, 0x280)
    
    rowWidths = [33,33,33,33,33,33,33,32,32,31,31,30,30,29,29,28,28,27,27,26,26,25,25,24,24,23,23,22,22,21,21,20,20,19,19,18,18,17,17,16,16,15,15,14,14,13,13,12,12,11,11,10,10,9,9]
    rowIndex = [[7, 39],
                [41, 73],
                [76, 108],
                [109,141],
                [144,176],
                [177,209],
                [211,243],
                [244,275],
                [277,308],
                [309,339],
                [341,371],
                [372,401],
                [403,432],
                [433,461],
                [463,491],
                [492,519],
                [521,548],
                [549,575],
                [577,603],
                [604,629],
                [631,656],
                [30,54],
                [56,80],
                [81,104],
                [106,129],
                [130,152],
                [154,176],
                [177,198],
                [200,221],
                [222,242],
                [244,264],
                [265,284],
                [286,305],
                [306,324],
                [326,344],
                [345,362],
                [364,381],
                [382,398],
                [400,416],
                [417,432],
                [434,449],
                [450,464],
                [466,480],
                [481,494],
                [496,509],
                [510,522],
                [524,536],
                [537,548],
                [550,561],
                [562,572],
                [574,584],
                [585,594],
                [596,605],
                [606,614],
                [616,624]]
    def __init__(self):
        result = self.api.list_usb_devices(deviceinterface=True, present=True)
        if result:
            if self.api.init_winusb_device("AniMe Matrix", self.vid, self.pid):
                self.api.control_transfer(self.setupPacket, self.initPacket)
                self.connected = True

    def sendTest(self):
        if self.connected:
            firstPane = [0x5e, 0xc0, 0x02, 0x01, 0x00, 0x73, 0x02]
            firstPane += [0xff]*633
            secondPane = [0x5e, 0xc0, 0x02, 0x74, 0x02, 0x73, 0x02]
            secondPane += [0xff]*633
            self.api.control_transfer(self.setupPacket, firstPane)
            self.api.control_transfer(self.setupPacket, secondPane)
            self.api.control_transfer(self.setupPacket, self.flushPacket)

    def clearMatrix(self):
        if self.connected:
            firstPane = [0x5e, 0xc0, 0x02, 0x01, 0x00, 0x73, 0x02]
            firstPane += [0x00]*633
            secondPane = [0x5e, 0xc0, 0x02, 0x74, 0x02, 0x73, 0x02]
            secondPane += [0x00]*633
            self.api.control_transfer(self.setupPacket, firstPane)
            self.api.control_transfer(self.setupPacket, secondPane)
            self.api.control_transfer(self.setupPacket, self.flushPacket)

    def closeDevice(self):
        if self.connected:
            self.api.close_winusb_device()

    def drawMatrix(self, inputMatrix):
        if len(inputMatrix) != 55:
            return False
        for i in range(len(inputMatrix)):
            if len(inputMatrix[i]) != self.rowWidths[i]:
                return False
            else:
                if i < 20:
                    if i == 0:
                        for j in range(self.rowWidths[i]-1):
                            self.firstPane[self.rowIndex[i][1] - j] = inputMatrix[i][j+1]
                    else:
                        for j in range(self.rowWidths[i]):
                            self.firstPane[self.rowIndex[i][1] - j] = inputMatrix[i][j]
                elif i == 20:
                    for j in range(23):
                        self.secondPane[29-j] = inputMatrix[i][j]
                    for j in range(23, 26):
                        self.firstPane[self.rowIndex[i][1]-j] = inputMatrix[i][j]
                else:
                    for j in range(self.rowWidths[i]):
                        self.secondPane[self.rowIndex[i][1] - j] = inputMatrix[i][j]
        self.api.control_transfer(self.setupPacket, self.firstPane)
        self.api.control_transfer(self.setupPacket, self.secondPane)
        self.api.control_transfer(self.setupPacket, self.flushPacket)
        return True

    def playSnake(self):
        inverseSpeed = 8
        snake = [[0, 3], [0, 2], [0, 1]]
        snakeDir = 1
        alive = True
        movementCounter = 0
        changed = False
        goal = []
        goal.append(random.randint(0, 24)*2)
        goal.append(random.randint(1, self.rowWidths[goal[0]]-1))
        inputMatrix = []
        for i in range(len(self.rowWidths)):
            inputMatrix.append([0x00]*self.rowWidths[i])
        for i in snake:
            inputMatrix[i[0]][i[1]] = 0xff;
        inputMatrix[goal[0]][goal[1]] = 0xff
        self.drawMatrix(inputMatrix)
        keyboard.wait('d')
        while alive:
            time.sleep(0.01)
            try:
                if keyboard.is_pressed('esc'):
                    break
            except:
                pass
            try:  # used try so that if user pressed other than the given key error will not be shown
                if keyboard.is_pressed('w') and (snakeDir == 3 or snakeDir == 1) and changed == False:
                    snakeDir = 0
                    changed = True
            except:
                pass
            try:  # used try so that if user pressed other than the given key error will not be shown
                if keyboard.is_pressed('a') and (snakeDir == 0 or snakeDir == 2) and changed == False:
                    snakeDir = 3
                    changed = True
            except:
                pass
            try:  # used try so that if user pressed other than the given key error will not be shown
                if keyboard.is_pressed('s') and (snakeDir == 3 or snakeDir == 1) and changed == False:
                    snakeDir = 2
                    changed = True
            except:
                pass
            try:  # used try so that if user pressed other than the given key error will not be shown
                if keyboard.is_pressed('d') and (snakeDir == 0 or snakeDir == 2) and changed == False:
                    snakeDir = 1
                    changed = True
            except:
                pass
            movementCounter += 1
            if movementCounter >= inverseSpeed:
                changed = False
                if snakeDir == 0:
                    snake.insert(0, [snake[0][0]+2, snake[0][1]])
                elif snakeDir == 1:
                    snake.insert(0, [snake[0][0], snake[0][1]+1])
                elif snakeDir == 2:
                    snake.insert(0, [snake[0][0]-2, snake[0][1]])
                elif snakeDir == 3:
                    snake.insert(0, [snake[0][0], snake[0][1]-1])
                if(snake[0] == goal):
                    goal[0] = random.randint(0, 24)*2
                    goal[1] = random.randint(1, self.rowWidths[goal[0]]-1)
                else:
                    del snake[len(snake)-1]
                for i in range(1, len(snake)):
                    if(snake[0] == snake[i]):
                        alive = False
                        break
                if snake[0][0] < 0 or snake[0][0] >= 55 or snake[0][1] < 0 or snake[0][1] >= self.rowWidths[snake[0][0]]:
                    alive = False
                if alive == False:
                    break
                inputMatrix = []
                for i in range(len(self.rowWidths)):
                    inputMatrix.append([0x00]*self.rowWidths[i])
                for i in snake:
                    inputMatrix[i[0]][i[1]] = 0xff;
                inputMatrix[goal[0]][goal[1]] = 0xff
                movementCounter = 0
                self.drawMatrix(inputMatrix)
        if alive == False:
            inputMatrix = []
            for i in range(len(self.rowWidths)):
                inputMatrix.append([0xff]*self.rowWidths[i])
            self.drawMatrix(inputMatrix)
            time.sleep(1.5)
        self.clearMatrix()
        
    
