import math


class Animatrix:
    mc = None

    last_matrix = []

    def __init__(self, matrix_controller):
        self.mc = matrix_controller

    def drawMatrix(self, matrix, raw_brightness=False):
        newMatrix = []
        finalMatrix = []
        shadow = True
        for index, subList in enumerate(matrix):
            modifiedBrightness = [self.getBrightness(entry) if not raw_brightness else entry for entry in subList]
            modifiedBrightness.reverse()
            newMatrix.append(modifiedBrightness)
        if self.last_matrix and shadow:
            for yIndex, subList in enumerate(newMatrix):
                newRow = []
                for xIndex, pixel in enumerate(subList):
                    lastPixel = self.last_matrix[yIndex][xIndex]
                    newRow.append(math.floor(lastPixel/10) if (lastPixel > 0 and pixel == 0) else pixel)
                finalMatrix.append(newRow)
        else:
            finalMatrix = newMatrix
        self.last_matrix = newMatrix
        self.mc.drawMatrix(finalMatrix)

    def clear(self):
        self.mc.clearMatrix()

    def getBrightness(self, brightness):
        return min(math.floor((brightness / 9) * 255), 255)

    def updateFrame(self):
        raise NotImplemented
