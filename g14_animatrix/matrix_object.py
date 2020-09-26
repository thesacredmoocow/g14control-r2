import math
import random
from datetime import datetime

from g14_animatrix.ani_frame import Frame


# full size = 60x120 -> cropped size = 33x54
# top left     x:14 y:33
# bottom right x:47 y:87
# middle       x:30 y:62
class MatrixObject():

    def __init__(self, xPos=0.0, yPos=34.0, zPos=0.0, xVelocity=0.0, yVelocity=0.0, yStep=1, xStep=1, feathering=0):
        self.feathering = feathering
        self.yVelocity = yVelocity
        self.xVelocity = xVelocity
        self.zPos = zPos
        self.yPos = yPos
        self.xPos = xPos
        self.yStep = yStep
        self.xStep = xStep

    def outOfBounds(self):
        return self.xPos > 60 or self.yPos > 120

    def getData(self):
        raise NotImplemented

    def getChildren(self):
        return []

    def moveFrame(self, weather_config):
        self.xPos += self.xVelocity
        self.yPos += self.yVelocity

    @staticmethod
    def generate():
        raise NotImplemented


class Cloud(MatrixObject):
    large_cloud = [
        [0, 0, 0, 0, 9, 9, 9, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 9, 9, 9, 9, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 9, 1, 1, 1, 9, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 9, 1, 1, 1, 1, 9, 9, 0, 0, 9, 9, 0, 0, 0],
        [0, 0, 9, 9, 1, 1, 1, 1, 9, 9, 0, 9, 9, 9, 0, 0],
        [0, 9, 1, 9, 9, 9, 9, 1, 9, 9, 9, 1, 9, 9, 0, 0],
        [0, 9, 1, 1, 9, 1, 9, 1, 1, 9, 9, 1, 1, 1, 9, 0],
        [9, 1, 1, 1, 1, 1, 1, 1, 1, 9, 1, 1, 1, 1, 9, 0],
        [2, 9, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 9],
        [9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 2],
    ]

    medium_cloud = [
        [0, 0, 0, 0, 9, 9, 9, 0, 0, 0],
        [0, 0, 0, 9, 9, 9, 9, 0, 0, 0],
        [0, 0, 0, 9, 9, 1, 1, 9, 0, 0],
        [0, 0, 9, 1, 1, 1, 9, 0, 0, 0],
        [0, 0, 9, 9, 1, 1, 1, 9, 0, 0],
        [0, 9, 1, 9, 9, 1, 9, 9, 0, 0],
        [0, 2, 9, 1, 1, 9, 1, 9, 9, 0],
        [9, 9, 1, 1, 1, 1, 1, 1, 9, 0],
        [0, 9, 1, 1, 1, 1, 1, 1, 1, 9],
        [9, 9, 9, 9, 9, 9, 9, 9, 9, 2],
    ]

    small_cloud = [
        [0, 0, 0, 0, 0],
        [0, 9, 9, 0, 0],
        [0, 9, 9, 9, 0],
        [9, 1, 1, 9, 0],
        [0, 9, 1, 1, 1],
        [9, 1, 1, 9, 0],
        [9, 0, 1, 1, 9],
        [9, 9, 9, 9, 9],
    ]

    data = []

    def __init__(self, xPos=0, yPos=random.randrange(35, 41, 2), z=0.0, xVelocity=0.0, yVelocity=0.0, yStep=2,
                 feathering=0,
                 allowed_sizes=3):
        super().__init__(xPos, yPos, z, xVelocity, yVelocity, yStep, feathering)
        self.rain_drops = []
        if allowed_sizes == 0:
            self.data = [[]]
        if allowed_sizes == 1:
            self.data = random.choice([self.medium_cloud, self.small_cloud])
        if allowed_sizes == 2:
            self.data = random.choice([self.large_cloud, self.medium_cloud])

    def getChildren(self):
        return self.rain_drops

    def getData(self):
        return self.data

    def moveFrame(self, weather_config):
        self.xVelocity = weather_config.get("wind_speed_mps", 0)/10
        for drop in self.rain_drops:
            if drop.outOfBounds():
                self.rain_drops.remove(drop)
        if self.shouldAddRaindrop(weather_config):
            if weather_config.get("snow_1h_mm", 0) > weather_config.get("rain_1h_mm", 0):
                self.add_particle(yVelocity=random.randrange(1, 5, 1) / 10, yStep=1)  # snowing

            else:
                self.add_particle(yVelocity=2.0, yStep=2)  # raining
        super().moveFrame(weather_config)

    def shouldAddRaindrop(self, weather_config):
        rain_intensity = max(weather_config.get("rain_1h_mm"), weather_config.get("snow_1h_mm", 0))*5
        if rain_intensity == 0 or len(self.data) == 0:
            return False
        rainDropsBelowDensity = len(self.rain_drops) < rain_intensity
        rainDropPositions = [drop.yPos for drop in self.rain_drops]
        rainDropPositions.append(Frame.fullHeight())
        lastDropSpacedOutEnough = min(rainDropPositions) > (
                len(self.data) + self.yPos + (Frame.fullHeight() / rain_intensity))
        return rainDropsBelowDensity and lastDropSpacedOutEnough

    def add_particle(self, yVelocity=2.0, yStep=2):
        rainX = random.randrange(math.floor(self.xPos), math.floor(self.xPos) + len(self.data[0])) - 1
        rainY = len(self.data) + self.yPos
        self.rain_drops.append(
            Raindrop.generate(yPos=rainY, xPos=rainX, xVelocity=0, yStep=yStep, yVelocity=yVelocity))

    @staticmethod
    def generate(xPos=None, xVelocity=None, weather_config=None):
        if weather_config is None:
            weather_config = {}
        # Cloud.generate(xVelocity=(random.randrange(5, 10, 1) / 100), rain_intensity=self.rain_intensity))

        # return Cloud(xPos=xPos, xVelocity=xVelocity, yPos=random.randrange(35, 41, 2), rain_intensity=rain_intensity)
        # return Cloud(xPos=xPos, xVelocity=xVelocity, yPos=35, rain_intensity=rain_intensity)
        allowed_sizes = 0
        cloudiness = weather_config.get("cloudiness_percent", 0)
        if 1 < cloudiness < 20:
            allowed_sizes = 1
        elif cloudiness < 50:
            allowed_sizes = 2
        else:
            allowed_sizes = 3
        if xPos is not None and xVelocity is not None:
            return Cloud(allowed_sizes=allowed_sizes, xPos=xPos, xVelocity=xVelocity)
        return Cloud(allowed_sizes=allowed_sizes)


class Raindrop(MatrixObject):
    data = [[9]]

    def getData(self):
        return self.data

    def moveFrame(self, weather_config):
        self.xVelocity = weather_config.get("wind_speed_mps", 0)/10
        super().moveFrame(weather_config)

    @staticmethod
    def generate(xVelocity=0.0, yVelocity=2.0, xPos=0.0, yPos=0.0, yStep=2):
        return Raindrop(yVelocity=yVelocity, xVelocity=xVelocity, xPos=xPos, yPos=yPos, yStep=yStep)


class Snowflake(Raindrop):

    @staticmethod
    def generate(xVelocity=0.0, yVelocity=2.0, xPos=0.0, yPos=0.0, yStep=1):
        return Snowflake(yVelocity=yVelocity, xVelocity=xVelocity, xPos=xPos, yPos=yPos, yStep=yStep)


class WindDebris(Raindrop):
    data = [[1]]

    def getData(self):
        return self.data

    @staticmethod
    def generate(xVelocity=0.0, xPos=0.0, yPos=random.randrange(30, 60), **kwargs):
        return WindDebris(yVelocity=0.01, xVelocity=xVelocity, xPos=xPos, yPos=yPos)


class Sun(MatrixObject):
    data = [
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 9, 1, 1, 1, 1, 1, 1, 1, 9, 0, 0],
        [0, 9, 1, 1, 1, 1, 1, 1, 1, 9, 0, 0],
        [9, 9, 1, 1, 1, 1, 1, 1, 1, 9, 9, 0],
        [0, 9, 9, 1, 1, 1, 1, 1, 1, 9, 0, 0],
        [0, 0, 9, 1, 1, 1, 1, 1, 9, 9, 0, 0],
        [0, 0, 9, 9, 1, 1, 1, 1, 9, 0, 9, 0],
        [0, 9, 0, 9, 1, 1, 1, 9, 9, 0, 0, 0],
        [0, 0, 0, 9, 9, 1, 1, 9, 0, 9, 0, 0],
        [0, 0, 9, 0, 9, 9, 9, 9, 0, 0, 0, 0],
        [0, 0, 0, 0, 9, 9, 9, 9, 0, 0, 0, 0],
    ]

    default_sunrise = datetime(1970, 1, 1, 6, 0, 0)
    default_sunset = datetime(1970, 1, 1, 18, 0, 0)

    isSunActive = False

    def getCurrentMinuteOfDay(self):
        return (datetime.now().hour * 60) + datetime.now().minute

    def getData(self):
        return self.data if self.isSunActive else []

    def isActive(self, sunrise, sunset):
        return (sunrise.hour * 60 + sunrise.minute) \
               < self.getCurrentMinuteOfDay() < \
               (sunset.hour * 60 + sunset.minute)

    def moveFrame(self, weather_config):
        sunrise = weather_config.get("sunrise", self.default_sunrise)
        sunset = weather_config.get("sunset", self.default_sunrise)
        sunlightDuration = (sunset - sunrise)
        sunlightDurationInMinutes = sunlightDuration.seconds / 60
        # move it between 6am and 6pm
        # currentHour = 11
        self.isSunActive = self.isActive(sunrise, sunset)
        if self.isSunActive:  # between 6am and 6pm
            # 6am = 14 - len(self.data[0])
            # 6pm = 47 + len(self.data[0])
            minX = max(14 - (len(self.data[0]) / 2), 0)
            maxX = 47
            currentStep = self.getCurrentMinuteOfDay() - (sunrise.hour * 60 + sunrise.minute)  # 0 to 12 if after 6am
            stepIncrement = (maxX - minX) / sunlightDurationInMinutes  # 13 hour block
            self.xPos = max(minX + (stepIncrement * currentStep), 0)

    @staticmethod
    def generate():
        return Sun(xPos=0.0, xStep=2)


class Moon(MatrixObject):
    data = [
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 9, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 9, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 9, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 9, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 0, 0],
        [0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 9, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 3, 9, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 9, 3, 9, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 9, 9, 0, 0, 0],
        [2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 9, 0, 0, 0],
    ]

    default_sunrise = datetime(1970, 1, 1, 6, 0, 0)
    default_sunset = datetime(1970, 1, 1, 18, 0, 0)

    isMoonActive = False

    def getData(self):
        return self.data if self.isMoonActive else []

    def getCurrentMinuteOfDay(self):
        return (datetime.now().hour * 60) + datetime.now().minute

    def isActive(self, sunrise, sunset):
        return (sunset.hour * 60 + sunset.minute) < self.getCurrentMinuteOfDay() \
               or self.getCurrentMinuteOfDay() < (sunrise.hour * 60 + sunrise.minute)

    def moveFrame(self, weather_config):
        sunrise = weather_config.get("sunrise", self.default_sunrise)
        sunset = weather_config.get("sunset", self.default_sunrise)
        sunlightDuration = (sunset - sunrise)
        sunlightDurationInMinutes = sunlightDuration.seconds / 60
        self.isMoonActive = self.isActive(sunrise, sunset)
        if self.isMoonActive:
            minX = 14 - max(len(self.data[0]), 0)
            maxX = 47
            sunsetMinutes = ((sunset.hour * 60) + sunset.minute)
            if sunsetMinutes < self.getCurrentMinuteOfDay():
                currentStep = self.getCurrentMinuteOfDay() - sunsetMinutes  # start of night (1700 - 2359)
            else:
                currentStep = self.getCurrentMinuteOfDay() + (
                        (sunrise.hour * 60) + sunrise.minute)  # end of night (0000 - 0600)
            stepIncrement = (maxX - minX) / sunlightDurationInMinutes  # 13 hour block
            self.xPos = max(minX + (stepIncrement * currentStep), 0)

    @staticmethod
    def generate():
        return Moon(xPos=0.0, xStep=2)


class CloudHaze(MatrixObject):
    data = []
    rain_drops = []
    snowflakes = []
    wind_debris = []
    lastHaze = -1

    def __init__(self, xPos=14.0, yPos=33.0, zPos=0.0, xVelocity=0.0, yVelocity=0.0, yStep=1, feathering=0,
                 intensity=0):
        super().__init__(xPos, yPos, zPos, xVelocity, yVelocity, yStep, feathering)
        self.intensity = intensity
        self.updateData(intensity)

    def updateData(self, haze_brightness):
        matrix = []
        for i in range(12):
            matrix.append([haze_brightness] * 40)
        cloudRow = []
        while len(cloudRow) < 40:
            should_highlight = random.choice([True, False])
            if should_highlight:
                cloudRow.append(9)
                cloudRow.append(9)
            else:
                cloudRow.append(haze_brightness)
        matrix.append(cloudRow)
        self.data = matrix

    def getData(self):
        return self.data

    def getChildren(self):
        return self.rain_drops + self.snowflakes + self.wind_debris

    def moveFrame(self, weather_config):
        newHaze = weather_config.get("cloudiness_percent", 0)

        if newHaze != self.lastHaze:
            self.lastHaze = newHaze
            if newHaze < 33:
                self.data = []
            elif newHaze < 66:
                self.updateData(1)
            else:
                self.updateData(2)

        for drop in self.rain_drops:
            if drop.outOfBounds():
                self.rain_drops.remove(drop)
        while self.shouldAddRaindrop(weather_config):
            self.add_particle(particle_type="rain")  # raining

        for snowflake in self.snowflakes:
            if snowflake.outOfBounds():
                self.snowflakes.remove(snowflake)
        while self.shouldAddSnowflake(weather_config):
            self.add_particle(particle_type="snow")  # snowing

        for debris in self.wind_debris:
            if debris.outOfBounds():
                self.wind_debris.remove(debris)
        while self.shouldAddWindDebris(weather_config):
            self.add_particle(particle_type="debris")  # nothing
        return  # do nothing

    def shouldAddSnowflake(self, weather_config):
        snow_intensity = weather_config.get("snow_1h_mm", 0)
        if snow_intensity == 0:
            return False
        snowflakesInRange = [snowflake.yPos for snowflake in self.snowflakes if
                             snowflake.yPos < (self.yPos + len(self.data) + 4)]
        snowflakesBelowDensity = len(snowflakesInRange) < snow_intensity
        return snowflakesBelowDensity

    def shouldAddWindDebris(self, weather_config):
        if weather_config.get("snow_1h_mm", 0) > 0 \
                or weather_config.get("rain_1h_mm", 0) > 0:
            return False
        debrisInRange = [debris.xPos for debris in self.wind_debris if debris.xPos < (self.xPos + 20)]
        debrisBelowIntensity = len(debrisInRange) < 3
        return debrisBelowIntensity

    def shouldAddRaindrop(self, weather_config):
        rain_intensity = weather_config.get("rain_1h_mm", 0)*5
        rainDropsInRange = [drop.yPos for drop in self.rain_drops if drop.yPos < (self.yPos + len(self.data) + 4)]
        rainDropsBelowDensity = len(rainDropsInRange) < rain_intensity
        return rainDropsBelowDensity

    def add_particle(self, particle_type="rain"):
        xPos = random.randrange(10, 50)
        yPos = self.yPos + len(self.data) - 1
        if particle_type == "debris":
            self.wind_debris.append(WindDebris.generate())
        elif particle_type == "snow":
            self.snowflakes.append(Snowflake.generate(yPos=yPos, xPos=xPos, xVelocity=0.0, yStep=1,
                                                      yVelocity=random.randrange(1, 5, 1) / 10))
        else:
            self.rain_drops.append(Raindrop.generate(yPos=yPos, xPos=xPos, xVelocity=0.0,
                                                     yVelocity=random.randrange(10, 20, 1) / 10))

    @staticmethod
    def generate(intensity=0):
        return CloudHaze(intensity=intensity)


class Mountains(MatrixObject):
    data = [
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 5, 5, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 0, 0, 0, 0, 5, 1, 1, 5, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 5, 0, 0, 0, 5, 1, 1, 1, 5, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 5, 5, 0, 0, 5, 1, 1, 1, 1, 5, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 0, 0, 5, 0, 5, 1, 1, 1, 1, 0, 5, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 0, 0, 0, 5, 5, 0, 1, 1, 1, 1, 0, 5, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 0, 0, 0, 0, 5, 0, 0, 0, 0, 0, 0, 0, 5, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 0, 0, 0, 0, 5, 0, 0, 0, 0, 0, 0, 0, 0, 5, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 5, 0, 0, 0, 0, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 5, 5, 0, 0, 0, 0, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 5, 5, 0, 0, 0, 0, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    ]

    def getData(self):
        return self.data

    @staticmethod
    def generate():
        return Mountains(xPos=16, yPos=67 - len(Mountains.data))


class Time(MatrixObject):
    odd_colon = [
        [0, 9, 0],
        [0, 0, 0],
        [9, 0, 0],
    ]

    even_colon = [
        [0, 0, 9],
        [0, 0, 0],
        [0, 9, 0],
    ]

    is12HourTime = False

    def __init__(self, xPos=33.0, yPos=74.0, zPos=0.0, xVelocity=0.0, yVelocity=0.0, yStep=1, xStep=1, feathering=0,
                 is12HourTime=False):
        super().__init__(feathering=feathering,
                         yVelocity=yVelocity,
                         xVelocity=xVelocity,
                         zPos=zPos,
                         yPos=yPos,
                         xPos=xPos,
                         yStep=yStep,
                         xStep=xStep)
        self.is12HourTime = is12HourTime

    def getData(self):
        return self.even_colon if self.yPos % 2 == 0 else self.odd_colon

    def moveFrame(self, weather_config):
        super().moveFrame(weather_config)

    @staticmethod
    def generate(is12HourTime=False):
        return Time(xPos=33, yPos=74, is12HourTime=is12HourTime)

    def getChildren(self):
        now = datetime.now()
        ret = []
        hour = now.hour
        if self.is12HourTime and hour > 12:
            hour = hour - 12
        if hour >= 10 and self.is12HourTime:
            ret.append(Number.generate(self.xPos - 4, self.yPos - 9, numValue=1))
        elif not self.is12HourTime:
            ret.append(Number.generate(self.xPos - 4, self.yPos - 9, numValue=math.floor(hour / 10)))
        ret.append(Number.generate(self.xPos - 2, self.yPos - 5, numValue=hour % 10))
        ret.append(Number.generate(self.xPos + 1, self.yPos + 1, numValue=math.floor(now.minute / 10)))
        ret.append(Number.generate(self.xPos + 3, self.yPos + 5, numValue=now.minute % 10))
        return ret


class Number(MatrixObject):
    odd_numbers = [
        [
            [0, 0, 9, 0],
            [0, 0, 9, 9],
            [0, 9, 0, 9],
            [0, 9, 0, 9],
            [9, 0, 9, 0],
            [0, 9, 9, 0],
            [0, 9, 0, 0],
        ],
        [
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 9],
            [0, 0, 0, 9],
            [0, 0, 9, 0],
            [0, 0, 9, 0],
            [0, 9, 0, 0],
        ],
        [
            [0, 0, 9, 0],
            [0, 0, 0, 9],
            [0, 9, 0, 9],
            [0, 9, 9, 9],
            [9, 0, 9, 0],
            [0, 9, 0, 0],
            [0, 9, 0, 0],
        ],
        [
            [0, 0, 9, 0],
            [0, 0, 0, 9],
            [0, 9, 0, 9],
            [0, 0, 9, 9],
            [9, 0, 9, 0],
            [0, 9, 9, 0],
            [0, 9, 0, 0],
        ],
        [
            [0, 0, 9, 0],
            [0, 0, 9, 0],
            [0, 9, 0, 9],
            [0, 0, 9, 9],
            [0, 0, 9, 0],
            [0, 0, 9, 0],
            [0, 9, 0, 0],
        ],
        [
            [0, 0, 9, 0],
            [0, 0, 9, 9],
            [0, 9, 0, 9],
            [0, 0, 9, 0],
            [9, 0, 9, 0],
            [0, 9, 9, 0],
            [0, 9, 0, 0],
        ],
        [
            [0, 0, 9, 0],
            [0, 0, 9, 9],
            [0, 9, 0, 9],
            [0, 9, 9, 0],
            [9, 0, 9, 0],
            [0, 9, 9, 0],
            [0, 9, 0, 0],
        ],
        [
            [0, 0, 9, 0],
            [0, 0, 0, 9],
            [0, 0, 0, 9],
            [0, 0, 0, 9],
            [0, 0, 9, 0],
            [0, 0, 9, 0],
            [0, 9, 0, 0],
        ],
        [
            [0, 0, 9, 0],
            [0, 0, 9, 9],
            [0, 9, 0, 9],
            [0, 9, 9, 9],
            [9, 0, 9, 0],
            [0, 9, 9, 0],
            [0, 9, 0, 0],
        ],
        [
            [0, 0, 9, 0],
            [0, 0, 9, 9],
            [0, 9, 0, 9],
            [0, 0, 9, 9],
            [0, 0, 9, 0],
            [0, 0, 9, 0],
            [0, 9, 0, 0],
        ],
    ]
    #    1  2  3  4  5       1  2  3  4  5
    # 1 [0, 0, 9, 0, 0] # 1 [0, 0, 0, 0, 0],
    # 2 [0, 0, 9, 9, 0] # 2 [0, 0, 0, 9, 0],
    # 3 [0, 9, 0, 9, 0] # 3 [0, 0, 9, 9, 0],
    # 4 [0, 9, 0, 9, 0] # 4 [0, 0, 9, 0, 9],
    # 5 [9, 0, 9, 0, 0] # 5 [0, 9, 0, 9, 0],
    # 6 [0, 9, 9, 0, 0] # 6 [0, 9, 0, 9, 0],
    # 7 [0, 9, 0, 0, 0] # 7 [0, 9, 9, 0, 0],
    # 8 [0, 0, 0, 0, 0] # 8 [0, 0, 9, 0, 0],

    even_numbers = [
        [
            [0, 0, 9, 0],
            [0, 9, 9, 0],
            [0, 9, 0, 9],
            [9, 0, 9, 0],
            [9, 0, 9, 0],
            [9, 9, 0, 0],
            [0, 9, 0, 0],
        ],
        [
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 9],
            [0, 0, 9, 0],
            [0, 0, 9, 0],
            [0, 9, 0, 0],
            [0, 9, 0, 0],
        ],
        [
            [0, 0, 9, 0],
            [0, 0, 9, 0],
            [0, 9, 0, 9],
            [9, 9, 9, 0],
            [9, 0, 9, 0],
            [9, 0, 0, 0],
            [0, 9, 0, 0],
        ],
        [
            [0, 0, 9, 0],
            [0, 0, 9, 0],
            [0, 9, 0, 9],
            [0, 9, 9, 0],
            [9, 0, 9, 0],
            [9, 9, 0, 0],
            [0, 9, 0, 0],
        ],
        [
            [0, 0, 9, 0],
            [0, 9, 0, 0],
            [0, 9, 0, 9],
            [0, 9, 9, 0],
            [0, 0, 9, 0],
            [0, 9, 0, 0],
            [0, 9, 0, 0],
        ],
        [
            [0, 0, 9, 0],
            [0, 9, 9, 0],
            [0, 9, 0, 9],
            [0, 9, 0, 0],
            [9, 0, 9, 0],
            [9, 9, 0, 0],
            [0, 9, 0, 0],
        ],
        [
            [0, 0, 9, 0],
            [0, 9, 9, 0],
            [0, 9, 0, 9],
            [9, 9, 0, 0],
            [9, 0, 9, 0],
            [9, 9, 0, 0],
            [0, 9, 0, 0],
        ],
        [
            [0, 0, 9, 0],
            [0, 0, 9, 0],
            [0, 0, 0, 9],
            [0, 0, 9, 0],
            [0, 0, 9, 0],
            [0, 9, 0, 0],
            [0, 9, 0, 0],
        ],
        [
            [0, 0, 9, 0],
            [0, 9, 9, 0],
            [0, 9, 0, 9],
            [9, 9, 9, 0],
            [9, 0, 9, 0],
            [9, 9, 0, 0],
            [0, 9, 0, 0],
        ],
        [
            [0, 0, 9, 0],
            [0, 9, 9, 0],
            [0, 9, 0, 9],
            [0, 9, 9, 0],
            [0, 0, 9, 0],
            [0, 9, 0, 0],
            [0, 9, 0, 0],
        ],
    ]

    data = []

    def __init__(self, xPos=0.0, yPos=34.0, zPos=0.0, xVelocity=0.0, yVelocity=0.0, yStep=1, numValue=0, feathering=0):
        super().__init__(xPos, yPos, zPos, xVelocity, yVelocity, yStep, feathering)
        self.data = self.even_numbers[numValue] if yPos % 2 == 0 else self.odd_numbers[numValue]

    def getData(self):
        return self.data

    @staticmethod
    def generate(xPos=30.0, yPos=60.0, numValue=0):
        return Number(xPos=xPos, yPos=yPos, numValue=numValue)
