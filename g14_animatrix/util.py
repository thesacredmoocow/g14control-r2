import math


def getDist(a, b):
    return math.sqrt((a.y - b.y) * (a.y - b.y) + (a.x - b.x) * (a.x - b.x))


def remap(source, ol, oh, nl, nh):
    orr = oh - ol
    nr = nh - nl
    rat = nr / orr
    return int((source - ol) * rat + nl)
