from haversine import haversine, Unit


def calculate_distance(point1, point2):
    distance = haversine(point1, point2, unit=Unit.MILES)
    return distance