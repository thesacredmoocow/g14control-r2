import math


class Animatrix:
    mc = None

    def __init__(self, matrix_controller):
        self.mc = matrix_controller

    def drawMatrix(self, matrix, raw_brightness=False):
        finalMatrix = []
        for index, subList in enumerate(matrix):
            modifiedBrightness = [self.getBrightness(entry) if not raw_brightness else entry for entry in subList]
            modifiedBrightness.reverse()
            finalMatrix.append(modifiedBrightness)
        self.mc.drawMatrix(finalMatrix)

    def clear(self):
        self.mc.clearMatrix()

    def getBrightness(self, brightness):
        return min(math.floor((brightness / 9) * 255), 255)

    def updateFrame(self):
        raise NotImplemented
