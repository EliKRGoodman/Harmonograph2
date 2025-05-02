import math
from functools import reduce

def lcm(a, b):
    return (a * b) // math.gcd(a, b)

def lcm_of_array(speeds):
    return reduce(lcm, speeds)

def rotations_until_repeat(speeds):
    cycle = lcm_of_array(speeds)
    return [cycle // speed for speed in speeds]

if __name__ == "__main__":
    speeds = [40, 90, 110]  # Example input
    rotations = rotations_until_repeat(speeds)
    
    print("Rotations until full pattern repeat:")
    for i, rotation in enumerate(rotations, start=1):
        print(f"Arm {i}: {rotation} rotations")