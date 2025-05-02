from fractions import Fraction
import math
from functools import reduce
denominators = []
speeds_start = []
speeds_adjusted = []
speeds_combined = []

normal_speed = 5
def normalize(array_start, array_new, array_combined, full_value):
    total = 0
    array_new.clear()
    for i in range (len(array_start)):
        total += abs(array_start[i])
    for i in range(len(array_start)):
        num_percent = array_start[i]/total
        array_new.append(num_percent*full_value)
        if i == 0:
            array_combined.append(array_new[i])
        else:
            array_combined.append(array_new[i] + array_new [i-1])

def find_lcm(arr):
    global denominators
    fractions_list = [Fraction(num).limit_denominator() for num in arr]
    #numerators = [frac.numerator for frac in fractions_list]
    #lcm_num = reduce(math.lcm, numerators)
    denominators = [frac.denominator for frac in fractions_list]
    gcd_den = reduce(math.lcm, denominators)
    return gcd_den

speeds_start = [2, 5, 3]
normalize(speeds_start, speeds_adjusted, speeds_combined, normal_speed)
cycle_times = [Fraction(1, Fraction(speed).limit_denominator()) for speed in speeds_combined]

lcm = find_lcm(cycle_times)
for i in range(len(denominators)):
    print (speeds_start[i])
    print (speeds_adjusted[i])
    print (speeds_combined[i])
    print (denominators[i])
    print ()
print (lcm)