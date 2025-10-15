import math

angle_to_steer = 0
distance = 0

def angle_between_points(p1, p2):
    """
    Returns the angle in degrees from point p1 to point p2.
    Points are tuples in the form (x, y).
    """
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    angle_rad = math.atan2(dy, dx)
    angle_deg = math.degrees(angle_rad)
    return int(angle_deg)


def angle_difference(current_angle, target_angle):
    """
    Returns the smallest difference between two angles in degrees.
    Positive = turn right, Negative = turn left.
    """
    diff = target_angle - current_angle + 90 # compensate to car thinking 0 is up
    diff_adjusted = (diff + 180) % 360 - 180
    return int(diff_adjusted)


def calculate_distance_to_target(my_pos, target_pos):
    """
    Calculates the Euclidean distance between two points in 2D space.

    Parameters:
    - my_pos: tuple of (x, y)
    - target_pos: tuple of (x, y)

    Returns:
    - float: distance between the two points
    """
    dx = my_pos[0] - target_pos[0]
    dy = my_pos[1] - target_pos[1]
    return math.sqrt(dx**2 + dy**2)

def calculate_car_action(angle, my_pos , target_pos):

    global distance, angle_to_steer

    action = {"up": False, "down": False, "left": False, "right": False}

    angle_to_target_degrees =  angle_between_points(my_pos, target_pos)
    angle_to_steer = angle_difference(angle, angle_to_target_degrees)

    if (angle_to_steer > 0):
        action["right"] = True
    else:
        action["left"] = True

    distance = calculate_distance_to_target(my_pos, target_pos)
    if distance > 150:
        action["up"] = True
    else:
        action["down"] = True

    return action
