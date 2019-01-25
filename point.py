import math


class Point(object):
    '''Creates a point on a coordinate plane with values x and y.'''

    def __init__(self, tuple, app):
        '''Defines x and y variables'''
        self.app = app
        self.X, self.Y = tuple

    def __str__(self):
        return "(%s,%s)"%(self.X, self.Y)

    def __repr__(self):
        return "".join(["(", str(self.x), ",", str(self.y), ")"])

    def __add__(self, new):
        x = self.x + new.x
        y = self.y + new.y
        return Point(x,y)

    def __sub__(self, new):
        x = self.x - new.x
        y = self.y - new.y
        return Point(x,y)

    def move(self, dx, dy):
        '''Determines where x and y move'''
        self.X += dx
        self.Y += dy

    def getX(self):
        return self.X

    def getY(self):
        return self.Y

    def getXY(self):
        return (self.X, self.Y)

    def is_origin(self):
        return self.X <= 0 and self.Y <= 0

    def distance(self, other):
        dx = self.X - other.X
        dy = self.Y - other.Y
        return math.sqrt(dx ** 2 + dy ** 2)

    def heading_away(self, point_2, point_3, max_angle):

        if point_2 == point_3:
            angle_2_3 = 0
        else:
            dist_self_to_2 = self.distance(point_2)
            dist_self_to_3 = self.distance(point_3)
            dist_2_to_3 = point_2.distance(point_3)
            if dist_self_to_2 > 0 and dist_2_to_3 > 0:
                try:
                    radians = math.acos(((dist_self_to_2 ** 2) + (dist_2_to_3 ** 2) - (dist_self_to_3 ** 2)) / (2 * dist_self_to_2 * dist_2_to_3))
                    angle_2_3 = math.degrees(radians)
                except Exception as e:
                    self.app.logger.warning("heading_away(): maths error, probably divide by zero, using degree 0")
                    angle_2_3 = 0
            else:
                angle_2_3 = 0

        return angle_2_3 >= max_angle