# from fractions import Fraction
# from math import gcd
# from functools import reduce

# def lcm(a, b):
#     #""Compute the Least Common Multiple of two numbers.""
#     return abs(a * b) // gcd(a, b)

# def lcm_of_floats(arr):
#     #""Compute the LCM of an array of floating-point numbers.""
#     fractions = [Fraction(f).limit_denominator() for f in arr]
    
#     numerators = [frac.numerator for frac in fractions]
#     denominators = [frac.denominator for frac in fractions]

#     lcm_den = reduce(lcm, denominators)
#     gcd_num = reduce(gcd, numerators)
    
#     result = Fraction(gcd_num, 1) * Fraction(lcm_den, 1)
#     return float(result)

# # Example usage
# numbers = [1, 2, 3]
# cycle_times = [360/x for x in numbers] #cycle_times = [360, 180, 120]
# lcm = lcm_of_floats(cycle_times) #lcm = 360

# rotations_to_repeat = [lcm/x for x in cycle_times] #[1, 2, 3]
# for i in range(len(rotations_to_repeat)):
#     print(f"Arm {i}: {rotations_to_repeat[i]}")
#print("LCM of the array:", lcm_of_floats(cycle_times))


"""
from math import gcd
from functools import reduce

def lcm(a, b):
    return abs(a * b) // gcd(a, b)

def lcm_of_set(numbers):
    numbers = [abs(n) for n in numbers]
    return reduce(lcm, numbers)

# Example usage
numbers = [1, 2]
cycle_times = [360/x for x in numbers] #cycle times = [360,180]
result = lcm_of_set(numbers) #result = 2
repeat_numbers = [result / x for x in cycle_times] #[]
for i in range(len(repeat_numbers)):
    print(f"Arm {i}: {repeat_numbers[i]}")
#print(f"LCM of {numbers} is {result}")"""

"""
from math import gcd
from functools import reduce

def lcm(a, b):
    # Compute the Least Common Multiple of two numbers.
    return abs(a * b) // gcd(a, b)

def lcm_of_integers(arr):
    # Compute the LCM of an array of integers.
    return reduce(lcm, arr)

# Example usage
numbers = [3, 7, 9]  # These are the speeds at which the arms rotate
ticks_per_rotation = [360 // x for x in numbers]  # This gives the number of ticks per rotation for each arm

# Calculate the LCM of ticks per rotation
lcm_value = lcm_of_integers(ticks_per_rotation)

# Calculate the rotations for each arm to reset
rotations_to_repeat = [lcm_value // x for x in ticks_per_rotation]

# Print out the result
for i in range(len(rotations_to_repeat)):
    print(f"Arm {i}: {rotations_to_repeat[i]}")
"""

import math
from functools import reduce

def find_gcd_of_set(nums):
    return reduce(math.gcd, nums)

# Example usage
numbers = [60, 75, 15]
gcd_value = find_gcd_of_set(numbers)
repeat_numbers = [x/gcd_value for x in numbers]
#print(f"GCD of {numbers} is {gcd_value}")
for i in range(len(repeat_numbers)):
    print(f"Arm {i}: {repeat_numbers[i]}")