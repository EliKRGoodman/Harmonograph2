#buttons: random pattern, rainbow speed
#implement settings dictionary
#pass variables in functions instead of using global

#region setup
import pygame, random, colorsys, os, math
from functools import reduce
from collections import deque
from fractions import Fraction

# Initialize pygame
pygame.init()
font = pygame.font.SysFont(None, 22)
font_propmt = pygame.font.SysFont(None, 30)
clock = pygame.time.Clock()

# Constants
screen_width, screen_height = 1200, 620 #screen dimensions
# Create screen
screen = pygame.display.set_mode((screen_width, screen_height))
border = (screen_height/2) - 20
max_ghost_length = 5000
WHITE = (255, 255, 255)
GREY = (100, 100, 100)
DARK_GREY = (60, 60, 60)
BLACK = (0,0,0)
BLUE = (0, 0, 255)
button_color = (8, 65, 50)

game_states = {num_arms: 0, gcd_value: 0, hue: 0, }
repeat_nums, arm_list, fractions = [], [], [] #trail_list
length_list, adjusted_lengths, length_percents, length_ratios, combined_length = [], [], [], [], []
speed_list,  adjusted_speeds, speed_percents, speed_ratios, combined_speed = [], [], [], [], []
num_arms, gcd_value, hue = 0, 0, 0   #rotations_to_restart, length_total, speed_total, lcm_result, num_rotations, #starting_pos = False
normal_length = new_normal_length = border - 5
normal_speed = new_normal_speed = 5
running, show_info, show_trail, rainbow, show_lines = True, True, True, True, True
add_speed, repeated, reset, rando = False, False, False, False
text = ""
#endregion setup

#region setup
def get_number_input(prompt):
    """ Function to get numerical input before the main loop. """
    input_text = ""
    while True:
        screen.fill(BLACK) #why does it error here when I exit early
        pygame.draw.rect(screen, WHITE, ((0,0), (screen_width, screen_height)), 3)
        text_surface = font_propmt.render(prompt + input_text, True, WHITE)
        screen.blit(text_surface, (50, 150))
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    if input_text.lstrip('-').isdigit():  # Check if input is a valid number (with optional negative sign)
                        return int(input_text)
                elif event.key == pygame.K_BACKSPACE:
                    input_text = input_text[:-1]
                elif event.unicode.isdigit() or (event.unicode == '-' and input_text == ""):  # Allow negative sign at the beginning
                    input_text += event.unicode

def hsv_to_rgb(hue):
    r, g, b = colorsys.hsv_to_rgb(hue, .75, .75)  # Full saturation and brightness
    return int(r * 255), int(g * 255), int(b * 255)  # Convert to 8-bit RGB

def normalize(array_start, array_new, array_ratios, array_combined, full_value):
    total = 0
    array_new.clear()
    total = sum(abs(x) for x in array_start)

    for i in range(len(array_start)):
        num_percent = array_start[i]/total
        array_new.append(num_percent*full_value)
        array_ratios.append(num_percent*full_value/(full_value/100))
        array_combined.append(array_new[i] + array_new [i-1]) if i > 0 else array_combined.append(array_new[i])

def calculate_repeat_nums(speeds):
    global repeat_nums, gcd_value
    gcd_value = reduce(math.gcd, speeds)
    repeat_nums = [abs(x//gcd_value) if x != 0 else 0 for x in speeds]
#endregion setup

#region GameLoop
def get_inputs(): #split this function up
    global num_arms, speed_ratios, length_ratios, fractions, rando
    num_arms = int(get_number_input("Enter a whole number of arms >1: "))
 
    for i in range(1, num_arms+1):
        if rando:
            speed_list.append(random.randint(0, 2000) *  random.choice([1, -1]))
        else:
            speed_list.append(int(get_number_input(f"Enter the speed for arm {i} (any positive or negative number): ")))
    
    for i in range (1, num_arms+1):
        if rando:
            length_list.append(random.randint(1,10000)*random.choice([1]))
        else:
            length_list.append(int(get_number_input(f"Enter the length for arm {i} (any positive or negative number): ")))

def build_arms():
    normalize(length_list, adjusted_lengths, length_percents, combined_length, normal_length) #remove combined_length here
    normalize(speed_list, adjusted_speeds, speed_percents, combined_speed, normal_speed)

    arm1 = (Arm(screen_width/2, screen_height/2, (screen_width/2), (screen_height/2) + adjusted_lengths[0], 0, 
                adjusted_speeds[0], adjusted_lengths[0], WHITE, 2, 4, combined_speed[0]))
    arm_list.append(arm1)

    for i in range (1, num_arms):
        arm = (Arm(arm_list[i-1].x_end, arm_list[i-1].y_end, arm_list[i-1].x_end, arm_list[i-1].y_end + adjusted_lengths[i], 0, 
                   adjusted_speeds[i], adjusted_lengths[i], WHITE, 1, 2, combined_speed[i]))
        arm_list.append(arm)

    calculate_repeat_nums(speed_list)
    for i in range(len(speed_list)):
        arm_list[i].repeat_num = repeat_nums[i]

def next_frame():
    global hue
    screen.fill(BLACK)
    pygame.draw.circle(screen, GREY, (screen_width/2, screen_height/2), border, 1)
    pygame.draw.rect(screen, WHITE, ((0,0), (screen_width, screen_height)), 3)
    clock.tick(60) # Limit FPS

    for i in range(num_arms):
        arm_list[i].update_pos(arm_list[i-1]) if i > 0 else arm_list[i].update_pos()
    hue = (hue + .0001)%1

    [button.display_button() for button in button_list]
   
def print_info():
    repeat_nums_output = "Rotations until pattern repeates:   " + ",  ".join(map(str, repeat_nums))

    speed_old_output =     "Speeds:              " + ",  ".join(map(str, speed_list)) 
    speed_new_output =     "Adjusted:            " + ",  ".join(map(lambda x: f"{x:.2f}", adjusted_speeds)) 
    speed_percent_output = "Percentages:     " + "%,  ".join(map(lambda x: f"{x:.2f}", speed_percents)) + "%"

    length_old_output =     "Lengths:             " + ",  ".join(map(str, length_list)) 
    length_new_output =     "Adjusted:            " + ",  ".join(map(lambda x: f"{x:.2f}", adjusted_lengths)) 
    length_percent_output = "Percentages:     " + "%,  ".join(map(lambda x: f"{x:.2f}", length_percents)) + "%"

    output_dict = ({repeat_nums_output: 20, speed_old_output: 60, speed_new_output: 80, speed_percent_output: 100, length_old_output: 160, 
                    length_new_output: 180, length_percent_output: 200})
    
    for key, value in output_dict.items():
        text = font.render(key, True, (255, 255, 255))
        screen.blit(text, (20, value))

def game_loop():
    get_inputs()
    build_arms()
    next_frame()

    global running
    while running:
        next_frame()

        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            for button in button_list:
                button.check_click(event)

        arm_list[-1].display_trail()
        if show_info == True:
            print_info()
        pygame.display.flip()  # Update display
#endregion GameLoop

#region Buttons
button_list = []
class Button:
    def __init__ (self, top_left_x, top_left_y, width, height, color, button_number):
        self.rect = pygame.Rect(top_left_x, top_left_y, width, height)
        self.top_left_x = top_left_x
        self.top_left_y = top_left_y
        self.width = width
        self.height = height
        self.color = color
        self.button_number = button_number
        self.function = button_functions[button_number]
        self.button_name = button_names[button_number]

    def display_button(self):
        pygame.draw.rect(screen, self.color, ((self.top_left_x + 5, self.top_left_y), (self.width, self.height)))        
        pygame.draw.rect(screen, WHITE, ((self.top_left_x + 5, self.top_left_y), (self.width, self.height)), 2)

        text_left = font.render(self.button_name, True, (255, 255, 255))
        screen.blit(text_left, (self.top_left_x + 25, self.top_left_y + 13))

    def check_click(self, event):
        """Checks if the button is clicked and executes its action."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                if self.function:
                    self.function(self)

def create_buttons():
    button_width = 150
    button_height = 40
    button_space = 10
    curr_height = screen_height - button_space - button_height - 10

    for i in range(7):
        button_left = Button(button_space + 5, curr_height, button_width, button_height, button_color, i)
        button_list.append(button_left)

        button_right = Button(screen_width - button_space - button_width - 15, curr_height, button_width, button_height, button_color, -i-1)
        button_list.append(button_right)
        curr_height = curr_height - button_height - button_space
        
def reset_game_state():
    global show_info, show_trail, rainbow, reset, new_normal_length, new_normal_speed, hue, add_speed#
    hue = 0
    show_info, show_trail, rainbow, reset = True, True, True, True 
    new_normal_speed = normal_speed 
    new_normal_length = normal_length 
    add_speed = False #?
    adjusted_lengths.clear()
    length_percents.clear()
    speed_percents.clear()
    adjusted_speeds.clear()

def reset_pattern(button):
    reset_game_state()
    arm_list[-1].ghost_queue.clear()
    normalize(length_list, adjusted_lengths, length_percents, combined_length, normal_length)
    normalize(speed_list, adjusted_speeds, speed_percents, combined_speed, normal_speed)
    for i, arm in enumerate(arm_list):
        arm.speed = adjusted_speeds[i]
        arm.length = adjusted_lengths[i]
        arm.main_angle = 0

def new_pattern(button): #combine with reset()
    arm_list.clear()
    speed_list.clear()
    length_list.clear()
    arm_list.clear()

    reset_game_state()
    get_inputs()
    build_arms()
    next_frame()

def add_decay(button):
    for arm in arm_list:
        arm.decay = (arm.decay + .01)%1

def save_pattern(button):
    return True

def reset_trail(button):
    arm_list[-1].ghost_queue.clear()
    
def toggle_color (button):
    global rainbow 
    rainbow = not rainbow

def toggle_trail (button):
    global show_trail
    show_trail = not show_trail

def toggle_info (button):
    global show_info
    show_info = not show_info

def toggle_lines(button):
    global show_lines
    show_lines = not show_lines

def zoom(button):
    adjusted_lengths.clear()
    length_percents.clear()
    global new_normal_length
    new_normal_length = new_normal_length * 1.1 if button.button_name == "Zoom +" else new_normal_length / 1.1
    normalize(length_list, adjusted_lengths, length_percents, combined_length, new_normal_length)
    for arm, length in zip(arm_list, length_list):
        arm.length = length

def add_speeds(button):
    global add_speed
    add_speed = False if add_speed == True else True

def change_speed(button):
    adjusted_speeds.clear()
    speed_percents.clear()
    global new_normal_speed
    new_normal_speed = new_normal_speed * 1.15 if button.button_name == "Speed +" else new_normal_speed / 1.15
    normalize(speed_list, adjusted_speeds, speed_percents, combined_speed, new_normal_speed)
    for i, arm in enumerate(arm_list):
        arm.speed = adjusted_speeds[i]

def exit(button):
    global running
    running = False

button_names = ["New Pattern", "!Save Pattern", "Reset Trail", "Toggle Trail", "Toggle Color", "Toggle Lines", "Toggle Info", "Speed +", "Speed -", "Zoom +", "Zoom -", "Add Speeds", "Reset Pattern", "Exit"] 
button_functions = [new_pattern, save_pattern, reset_trail, toggle_trail, toggle_color, toggle_lines, toggle_info, change_speed, change_speed, zoom, zoom, add_speeds, reset_pattern, exit]
#endregion Buttons

class Arm:
    def __init__ (self, x_start, y_start, x_end, y_end, main_angle, speed, length, color, width, circle_radius, combined_speed): #add parent here
        self.x_start = x_start
        self.y_start = y_start
        self.x_end = x_end
        self.y_end = y_end
        self.main_angle = main_angle
        self.speed = speed
        self.length = length
        self.color = color
        self.width = width
        self.ghost_queue = deque([])
        self.circle_radius = circle_radius
        self.reset = False
        self.combined_speed = combined_speed
        self.repeat_num = 0
        self.decay = 0

    def update_pos(self, parent = None):
        self.reset = False
        if parent != None:
            self.x_start = parent.x_end
            self.y_start = parent.y_end
            if add_speed:
                self.main_angle += parent.speed
        self.main_angle += self.speed
        if self.main_angle > 360:
            self.reset = True
            self.main_angle = self.main_angle % 360
        self.speed = self.speed * (1-self.decay)
     
        rad_angle = math.radians(self.main_angle - 90)
        self.x_end = self.x_start + self.length * math.cos(rad_angle)
        self.y_end = self.y_start + self.length * math.sin(rad_angle)
        pygame.draw.circle(screen, DARK_GREY, (self.x_start, self.y_start), self.length, 1)
        pygame.draw.line(screen, self.color, (self.x_start, self.y_start), (self.x_end, self.y_end), self.width)
        pygame.draw.circle(screen, button_color, (self.x_start, self.y_start), self.circle_radius)

    def display_trail(self):
        global reset, max_ghost_length
        ghost_array = [self.x_end, self.y_end, hsv_to_rgb(hue)]
        if not reset:
            self.ghost_queue.append(ghost_array)
        else:
            reset = False

        if len(self.ghost_queue) >= max_ghost_length:
            self.ghost_queue.popleft()
            
        for i, a in enumerate(self.ghost_queue):
            if i != len(self.ghost_queue) - 1 and show_trail == True:
                color = a[2] if rainbow == True else WHITE

                if show_lines == True:
                    pygame.draw.line(screen, color, (a[0], a[1]), (self.ghost_queue[i+1][0], self.ghost_queue[i+1][1]), 1)
                elif show_lines == False:
                    pygame.draw.circle(screen, color, (a[0], a[1]), 1)    

#region Main
create_buttons()
game_loop()
pygame.quit()
#endregion Main












































#def zoom_out(button):
#    adjusted_lengths.clear()
#    length_percents.clear()
#    global new_normal_length
#    new_normal_length = new_normal_length / 1.1
#    normalize(length_list, adjusted_lengths, length_percents, combined_length, new_normal_length)
#    for i, arm in enumerate(arm_list):
#        arm.length = adjusted_lengths[i]


#def speed_down(button):
##    speed_percents.clear()
#    adjusted_speeds.clear()
#    global new_normal_speed
#    new_normal_speed = new_normal_speed / 1.15
#    normalize(speed_list, adjusted_speeds, speed_percents, combined_speed, new_normal_speed)
#    for i, arm in enumerate(arm_list):
#        arm.speed = adjusted_speeds[i]

#button_dict = ({new_pattern: "New Pattern", save_pattern: "!Save Pattern", reset_trail: "Reset Trail", toggle_trail: "Toggle Trail", 
#                toggle_color: "Toggle Color", toggle_lines: "Toggle Lines", toggle_info: "Toggle Info", speed_up: "Speed Up", speed_down: "Speed Down", 
#                zoom_in: "Zoom In", zoom_out: "Zoom Out", add_speeds: "Add Speeds", reset_pattern: "Reset Pattern", exit: "Exit"})


    #global show_info, show_trail, rainbow, reset, new_normal_length, new_normal_speed, add_speed
    #show_info, show_trail, rainbow, reset = True, True, True, True 
    #add_speed = False
    #new_normal_speed = normal_speed
    #new_normal_length = normal_length
    #length_percents.clear()
    #speed_percents.clear()
    #adjusted_speeds.clear()
    #adjusted_lengths.clear()

    #global slowest_arm, lcm_result
    #repeat_numbers = 
    #speeds_old = 
    #speeds_new = 
    #speeds_pers =
    #lengths_old = 
    #lengths_new = 
    #lengths_pers = 

"""
    text = font.render(repeat_nums_output, True, (255, 255, 255))
    screen.blit(text, (20, 20))

    text = font.render(speed_old_output, True, (255, 255, 255))
    screen.blit(text, (20, 60))
    text = font.render(speed_new_output, True, (255, 255, 255))
    screen.blit(text, (20, 80))
    text = font.render(speed_percent_output, True, (255, 255, 255))
    screen.blit(text, (20, 100))

    text = font.render(length_old_output, True, (255, 255, 255))
    screen.blit(text, (20, 160))
    text = font.render(length_new_output, True, (255, 255, 255))
    screen.blit(text, (20, 180))
    text = font.render(length_percent_output, True, (255, 255, 255))
    screen.blit(text, (20, 200))"""


def first_frame():
    global rotations_to_restart, num_rotations, hue, restart
    arm_list[0].update_pos()
    for i in range (1,num_arms):
        arm_list[i].update_pos(arm_list[i-1])
        #if arm_list[i].reset != True:
        #    restart = False
    #if arm_list[0].reset == True and rotations_to_restart == 0:
    #    num_rotations += 1
    #else:
    #    restart = False
    #if restart == True:
    #   rotations_to_restart = num_rotations
    #hue = (hue + .0001)%1


    #text = font.render(f"Total Speed: {speed_total}, Total Length: {length_total}", True, (255, 255, 255)) 
    #screen.blit(text, (20, 20))
    #for i in range (1, num_arms+1):
    #    text = font.render(f"#{i} Start Speed: {speed_list[i-1]}, #{i} Speed: {arm_list[i-1].speed:.2f}, Start Length: {length_list[i-1]}, Adjusted Length: {arm_list[i-1].length:.2f}", True, (255, 255, 255)) 
    #    screen.blit(text, (20, (20*i + 20)))
    #cycle_output = f"Cycles of slowest arm (blue arm #{slowest_arm}) until pattern repeats: {lcm_result}"
    
    #speed_rats = ",  1/".join(map(str, speed_ratios))
    #speed_ratios_output = "Ratios:   1/" + speed_rats
    #length_rats = ",  1/".join(map(str, length_ratios))
    #length_ratios_output = "Ratios:   1/" + length_rats
    #text = font.render(length_ratios_output, True, (255, 255, 255))
    #screen.blit(text, (20, 120))
    #text = font.render(speed_ratios_output, True, (255, 255, 255))
    #screen.blit(text, (20, 220))
    
    #cycles = ", ".join(map(str, cycle_list))
    #cycles_output = "Cycles: " + cycles
    #cycle_output = f"Slowest Arm: Arm {slowest_arm} ~ Full rotations until pattern repetition: {lcm_result}"
    #text = font.render(cycles_output, True, (255, 255, 255))
    #screen.blit(text, (20, 120))

"""
def find_lcm(arr):
    global denominators
    fractions_list = [Fraction(num).limit_denominator() for num in arr]
    denominators = [frac.denominator for frac in fractions_list]
    lcm_value = reduce(math.lcm, denominators)
    #numerators = [frac.numerator for frac in fractions_list]
    #lcm_num = reduce(math.lcm, numerators)
    return lcm_value

for i in range(6):
        pygame.draw.rect(screen, button_color, ((button_space,curr_height), (button_width, button_height)))        
        pygame.draw.rect(screen, WHITE, ((button_space,curr_height), (button_width, button_height)), 3)

        pygame.draw.rect(screen, button_color, ((screen_width - button_width - button_space, curr_height), (button_width, button_height)))        
        pygame.draw.rect(screen, WHITE, ((screen_width - button_width - button_space, curr_height), (button_width, button_height)), 3)

        text_left = font.render(buttons[i], True, (255, 255, 255))
        screen.blit(text_left, (button_space + 25, curr_height + 13))
        text_right = font.render(buttons[-i-1], True, (255, 255, 255))
        screen.blit(text_right, (screen_width - button_width - button_space + 25, curr_height + 13))
        curr_height = curr_height - button_height - button_space"""

#arm2 = Arm(arm1.x_end, arm1.y_end, arm1.x_end, arm1.y_end + 50, 0, 11, 50, WHITE, 3)
#arm3 = Arm(arm2.x_end, arm2.y_end, arm2.x_end, arm2.y_end + 50, 0, -3, 50, WHITE, 3)
#arm4 = Arm(arm3.x_end, arm3.y_end, arm3.x_end, arm3.y_end + 50, 0, -3, 50, WHITE, 3)
#arm5 = Arm(arm3.x_end, arm3.y_end, arm3.x_end, arm3.y_end + 50, 0, 7, 50, WHITE, 3)
#arm6 = Arm(arm3.x_end, arm3.y_end, arm3.x_end, arm3.y_end + 50, 0, -3.75, 50, WHITE, 3)
#arm_list.append(arm2)
#arm_list.append(arm3)
#arm_list.append(arm4)
#arm_list.append(arm5)
#arm_list.append(arm6)
#num_arms = 3


##{i} Main Angle: {arm_list[i-1].main_angle:.2f}, 

    #text2 = font.render(f"#2 Main Angle: {arm2.main_angle}, #2 Speed: {arm2.speed}", True, (255, 255, 255)) 
    #text3 = font.render(f"#3 Main Angle: {arm3.main_angle}, #3 Speed: {arm3.speed}", True, (255, 255, 255)) 
    #text4 = font.render(f"#4 Main Angle: {arm4.main_angle}, #4 Speed: {arm4.speed}", True, (255, 255, 255)) 
    #text5 = font.render(f"#5 Main Angle: {arm5.main_angle}, #5 Speed: {arm5.speed}", True, (255, 255, 255)) 
    #text6 = font.render(f"#6 Main Angle: {arm6.main_angle}, #6 Speed: {arm6.speed}", True, (255, 255, 255)) 
    #screen.blit(text2, (20, 40))
    #screen.blit(text3, (20, 60))
    #screen.blit(text4, (20, 80))
    #screen.blit(text5, (20, 100))
    #screen.blit(text6, (20, 120))

"""
       self.main_angle = (self.main_angle - self.speed) % 360
        if self.main_angle == 0:
            self.angle_y = 90
            self.angle_x = 0
        if self.main_angle == 90:
            self.angle_y = 0
            self.angle_x = 90
        if self.main_angle == 180:
            self.angle_y = -90
            self.angle_x = 0
        if self.main_angle == 270:
            self.angle_y = 0
            self.angle_x = -90

        if self.main_angle > 0 and self.main_angle < 90: #Q1 (acting as q2)
            self.angle_y = 90 - self.main_angle
            self.angle_x = 90 - self.angle_y

        if self.main_angle > 90 and self.main_angle < 180: #Q2
            self.angle_y = -(self.main_angle%90)
            self.angle_x = 90 - abs(self.angle_y)

        if self.main_angle > 180 and self.main_angle < 270: #Q3
            self.angle_y = - (90 - (self.main_angle%90))
            self.angle_x = -(90 - abs(self.angle_y))

        if self.main_angle > 270 and self.main_angle < 360: #Q4
            self.angle_y = self.main_angle % 90
            self.angle_x = -(90 - abs(self.angle_y))

        self.angle_y = -self.angle_y
        self.angle_x = -self.angle_x
        angle_y_rads = math.radians(self.angle_y)
        self.length_y = (self.length * math.sin(angle_y_rads))
        self.y_end = screen_height - self.y_start + self.length_y

        angle_x_rads = math.radians(self.angle_x)
        self.length_x = (self.length * math.sin(angle_x_rads))
        self.x_end = screen_width - self.x_start + self.length_x
"""