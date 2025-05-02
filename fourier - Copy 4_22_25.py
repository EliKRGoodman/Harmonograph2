#add musical notes
#bug: speed percentages/ratios not showing up sometimes
#optimize screen rendering (only draw new stuff)
#make zoom respect decay

#region setup
import pygame, random, colorsys, os, math, datetime
from functools import reduce
from collections import deque
from fractions import Fraction
import numpy as np
import time

# Initialize pygame
pygame.init()
font = pygame.font.SysFont(None, 22)
font_prompt = pygame.font.SysFont(None, 30)
font_explain = pygame.font.SysFont(None, 26)
font_title = pygame.font.SysFont(None, 45)
clock = pygame.time.Clock()
pygame.mixer.init(frequency=44100, size=-16, channels= 2, buffer= 1024)

# Constants
screen_width, screen_height = 1200, 620 #screen dimensions
# Create screen
screen = pygame.display.set_mode((screen_width, screen_height))
border = (screen_height/2) - 15
button_width, button_height = 150, 40
max_ghost_length = 10000
WHITE = (255, 255, 255)
GREY = (100, 100, 100)
DARK_GREY = (75, 75, 75)
BLACK = (0,0,0)
button_color = (10, 65, 50)
button_pressed = (29, 53, 92)

game_states = ({"hue": 0, "gcd_value": 0, "num_arms": 0, "decay": 0, "screenshot_timer": 0,
                "hue_step": .0002, "normal_speed": 5, "new_normal_speed": 5, "normal_length": border-5, "new_normal_length": border-5,

                "running": True, "show_info": True, "show_trail": True, "show_lines":True, "rainbow": True, 
                "show_arms": True, "show_buttons": True, "start": True, "title": True, 
                "add_speed": False, "repeated": False, "reset": False, "random_inputs": False, 
                "pause": False, "back": False, "sound_fx": False,
                "last_click":"left"})

freq_high = 480  # Frequency in Hz (A4)
freq_low = 160
duration = .2   # Duration in seconds
volume = 0.1

repeat_nums, combined_repeat_nums, arm_list, fractions, button_list, title_arms = [], [], [], [], [], [] #trail_list
length_list, adjusted_lengths, length_percents, length_ratios = [], [], [], []
speed_list,  adjusted_speeds, speed_percents, speed_ratios, combined_speeds, curr_speeds = [], [], [], [], [], []
back_button_container = []
text = ""
#endregion setup

#region setup
def get_number_input(prompt): #ChatGPT
    """ Function to get numerical input before the main loop. """
    input_text = ""
    prompt_surface = font_prompt.render(prompt, True, WHITE)
    prompt_rect = prompt_surface.get_rect(center=(screen_width // 2, screen_height // 4))

    while True:
        screen.fill(BLACK) #why does it error here when I exit early
        pygame.draw.rect(screen, WHITE, ((0,0), (screen_width, screen_height)), 3)
        screen.blit(prompt_surface, prompt_rect)

        input_surface = font_prompt.render(input_text, True, WHITE)
        input_rect = input_surface.get_rect(topleft=(screen_width // 2, (screen_height // 4) + 20))
        screen.blit(input_surface, input_rect)
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

def hsv_to_rgb(hue): #ChatGPT
    r, g, b = colorsys.hsv_to_rgb(hue, .75, .75)  # Full saturation and brightness
    return int(r * 255), int(g * 255), int(b * 255)  # Convert to 8-bit RGB

def normalize(array_start, array_new, array_ratios, full_value):
    #total = 0
    total = sum(abs(x) for x in array_start)
    length = len(array_start)
    temp_array = array_start[:]
    array_new.clear()

    for i in range(length):
        num_percent = temp_array[i]/total
        array_new.append(num_percent*full_value)
        array_ratios.append(num_percent*full_value/(full_value/100))

def calculate_repeat_nums(speeds, game_states):
    game_states["gcd_value"] = reduce(math.gcd, speeds)
    return [abs(x//game_states["gcd_value"]) if x != 0 else 0 for x in speeds]

def calculate_ratios(input_array, ratios, game_states):
    for i in range(len(input_array)):
        fraction = Fraction(input_array[i]/100).limit_denominator()
        ratios.append(fraction.numerator)
        ratios.append(fraction.denominator)

def calculate_frequencies(num_arms, freq_high, freq_low):
    if num_arms == 1:
        frequencies = [(freq_low + freq_high)/2]
    elif num_arms == 2:
        frequencies = [freq_low, freq_high]
    else:
        frequencies = [freq_low]
        increment = (freq_high - freq_low)/(num_arms - 1)
        for i in range(1,num_arms-1):
            frequencies.append(freq_low + i*increment)
        frequencies.append(freq_high)
    return frequencies

def generate_sound(frequency, duration, volume): #ChatGPT
    sample_rate = 44100  # Samples per second
    t = np.linspace(0, duration, int(sample_rate * duration), False)

    waveform = np.sin(2 * np.pi * frequency * t) # Basic sine wave    
    fade = np.linspace(1, 0, len(t)) # Apply fade-out envelope (linear fade)
    waveform *= fade * volume  # Apply volume and fade    
    waveform_integers = np.int16(waveform * 32767) # Convert to 16-bit signed integers
    waveform_stereo = np.column_stack((waveform_integers, waveform_integers)) # Stereo version

    return pygame.sndarray.make_sound(waveform_stereo)
#endregion setup

#region Buttons
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
        self.press, self.hover = False, False

    def display_button(self, mouse_pos):
        self.color = button_pressed if self.press or self.hover == True else button_color
        pygame.draw.rect(screen, self.color, ((self.top_left_x + 5, self.top_left_y), (self.width, self.height)), 0, 10)        
        pygame.draw.rect(screen, WHITE, ((self.top_left_x + 5, self.top_left_y), (self.width, self.height)), 2, 10)

        text_surface = font.render(self.button_name, True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

        self.hover = self.rect.collidepoint(mouse_pos)

    def check_click(self, event):
        """Checks if the button is clicked and executes its action."""
        if event.type == pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(event.pos):
            game_states["last_click"] = "left" if event.button == 1 else "right"
            self.function(self, game_states)

def create_buttons():
    global back_button_container
    #button_width = 150
    #button_height = 40
    button_space = 10
    curr_height = screen_height - button_space - button_height - 10
    left_space = button_space+5
    right_space = screen_width - button_space - button_width - 15

    for i in range(7):
        button_left = Button(left_space, curr_height, button_width, button_height, button_color, i)
        button_list.append(button_left)

        button_right = Button(right_space, curr_height, button_width, button_height, button_color, -i-7)
        button_list.append(button_right)
        curr_height = curr_height - button_height - button_space
        
    curr_height = screen_height - button_space - button_height - 10    
    for i in range(1,4):
        button_left = Button(2 * left_space + button_width, curr_height, button_width, button_height, button_color, i+13)
        button_list.append(button_left)
        button_right = Button(screen_width - 2*button_space - 2*button_width - 20, curr_height, button_width, button_height, button_color, -i)
        button_list.append(button_right)
        curr_height = curr_height - button_height - button_space

    button_back = Button(screen_width/2 - (button_width/2), ((screen_height/4)*3), button_width, button_height, button_color, 0)
    button_back.button_name = "Back"
    button_back.function = back_button
    back_button_container.append(button_back)

#region finished buttons
def reset_pattern_state(game_states): #used both for reseting pattern and new pattern
    game_states["hue"] = game_states["decay"] = 0
    game_states["hue_step"] = .0002
    game_states["show_trail"] = game_states["rainbow"] = game_states["show_lines"] = game_states["reset"] = True
    game_states["new_normal_speed"] = game_states["normal_speed"] 
    game_states["new_normal_length"] = game_states["normal_length"]
    game_states["pause"] = game_states["sound_fx"] = False #?
    game_states["start"] = True

    for list in [adjusted_lengths, length_percents, adjusted_speeds, speed_percents]:
        list.clear()
    for button in button_list:
        if button.button_name not in ("Toggle Info", "Toggle Arms", "Toggle Friction"):
            button.press = False

def reset_pattern(button, game_states): #used just for a new pattern
    reset_pattern_state(game_states)
    arm_list[-1].ghost_queue.clear()
    normalize(length_list, adjusted_lengths, length_percents, game_states["normal_length"])
    normalize(speed_list, adjusted_speeds, speed_percents, game_states["normal_speed"])
    for i, arm in enumerate(arm_list):
        arm.curr_speed = arm.speed = adjusted_speeds[i]
        arm.length = adjusted_lengths[i]
        arm.main_angle = 0

def change_pattern(game_states):
    for list in [arm_list, speed_list, length_list, speed_ratios, length_ratios, combined_speeds]:
        list.clear()

    game_states["title"] = False
    reset_pattern_state(game_states)
    get_inputs(game_states)
    build_arms()
    next_frame(game_states)
    
def new_pattern(button, game_states):
    game_states["random_inputs"] = False
    change_pattern(game_states)

def random_pattern(button, game_states):
    game_states["random_inputs"] = True
    change_pattern(game_states)

def add_decay(button, game_states):
    game_states["decay"] = (game_states["decay"] + .0001) if game_states["last_click"] == "left" else (game_states["decay"] - .0001)

def add_rainbow(button, game_states):
    game_states["hue_step"] = (game_states["hue_step"] + .0002) if game_states["last_click"] == "left" else (game_states["hue_step"] - .0002)

def reset_trail(button, game_states):
    arm_list[-1].ghost_queue.clear()
    
def toggle_button(button, game_states, string, not_default_state):
    game_states[string] = not game_states[string]
    button.press = not_default_state if game_states[string] else not not_default_state

def show_buttons(button, game_state):
    toggle_button(button, game_states, "show_buttons", False)

def toggle_color (button, game_states):
    toggle_button(button, game_states, "rainbow", False)

def toggle_trail (button, game_states):
    toggle_button(button, game_states, "show_trail", False)

def toggle_info (button, game_states):
    toggle_button(button, game_states, "show_info", False)

def toggle_lines(button, game_states):
    toggle_button(button, game_states, "show_lines", False)

def toggle_arms(button, game_state):
    toggle_button(button, game_states, "show_arms", False)

def add_speeds(button, game_states):
    toggle_button(button, game_states, "add_speed", True)

def pause_game(button, game_states):
    toggle_button(button, game_states, "pause", True)

def zoom(button, game_states):
    adjusted_lengths.clear()
    length_percents.clear()

    game_states["new_normal_length"] = (game_states["new_normal_length"] * 1.1 if game_states["last_click"] == "left" 
                                        else game_states["new_normal_length"] / 1.1)
    normalize(length_list, adjusted_lengths, length_percents, game_states["new_normal_length"])
    for arm, length in zip(arm_list, adjusted_lengths):
        arm.length = length

def change_speed(button, game_states):
    adjusted_speeds.clear()
    speed_percents.clear()

    game_states["new_normal_speed"] = (game_states["new_normal_speed"] * 1.15 if game_states["last_click"] == "left" 
                                        else game_states["new_normal_speed"] / 1.15)
    normalize(speed_list, adjusted_speeds, speed_percents, game_states["new_normal_speed"])
    for i, arm in enumerate(arm_list):
        arm.curr_speed = arm.speed = adjusted_speeds[i]

def screenshot(button, game_states):
    current_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    file_name = f"{current_time}.png"
    pygame.image.save(screen, file_name)
    game_states["screenshot_timer"] = 180

def exit_button(button, game_states):
    pygame.quit()
    exit()
#endregion finished buttons

def toggle_sound(button,game_states):
    toggle_button(button, game_states, "sound_fx", True)

def back_button(button, game_states):
    game_states["back"] = True

def show_explanation(button, game_states):
    global back_button #    
    game_states["back"] = False
    toggle_string_2 = "\"Toggle Friction\" partially simulates friction by adding the rotation of arm n to arm n+1."
    toggle_string = "\"Toggle Sounds\" gives each arm a unique note that plays when it completes a rotation with a visual indicator to match."
    toggle_string_3 = "The rest of the toggle buttons turn visual elements on or off."
    button_string = "When you're ready to try a new pattern use \"New Pattern\" for manual input and \"Random Pattern\" for random input."
    variable_string_2 = "Use \"Speed +/-\" and \"Length +/-\" to change the speeds and lengths of the arms, respectively."
    variable_string = "\"Decay +/-\" gradually alters the arm lengths and \"Rainbow +/-\" changes the rate at which the color of the trail changes."
    variable_string_3 = "Use left-click to increase values and right-click to decrease them."
    reset_string = "\"Reset Trail\" erases any existing trail and \"Reset Pattern\" resets the pattern to the initial starting conditions."
    save_string = "If you like a pattern, save it with the Screenshot button. Make sure the info is showing if you want to recreate it!"

    string_list = [toggle_string, toggle_string_2, toggle_string_3, variable_string, variable_string_2, variable_string_3, reset_string, save_string, button_string]
    y_pos_list = [60, 85, 110, 170, 195, 220, 280, 305, 330]

    while (True):
        screen.fill(BLACK)
        draw_gradient()
        back_button_container[0].display_button(pygame.mouse.get_pos())
        for i in range(len(string_list)):
            line_surface = font_explain.render(string_list[i], True, WHITE)
            line_rect = line_surface.get_rect(center=(screen_width // 2, y_pos_list[i]))
            screen.blit(line_surface, line_rect)
        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()  # Handle quit event
                exit()
            back_button_container[0].check_click(event)
        if game_states["back"]:
            return

button_names = (["Toggle Buttons", "Toggle Sound", "Toggle Arms", "Toggle Trail", "Toggle Color", "Toggle Lines", "Toggle Info", #left outer, ascending
                 "Speed +/-", "Zoom +/-", "Decay +/-", "Rainbow +/-", "New Pattern", "Random Pattern", "Exit", #right outer, descending

                  "Toggle Friction", "Reset Pattern", "Reset Trail", #left inner, ascending
                  "Screenshot", "Pause", "~Explanation"]) #right outer, descending

button_functions = ([show_buttons, toggle_sound, toggle_arms, toggle_trail, toggle_color, toggle_lines, toggle_info, #left outer, ascending
                    change_speed, zoom, add_decay, add_rainbow, new_pattern, random_pattern, exit_button, #right outer
                    
                    add_speeds, reset_pattern, reset_trail, #left inner, ascending
                    screenshot, pause_game, show_explanation]) #right inner
#endregion Buttons

class Arm:
    def __init__ (self, speed, length, width, circle_radius, arm_num, parent = None): #add parent here
        self.length = length
        if parent != None:
            self.x_end = self.x_start = parent.x_end
            self.y_start = parent.y_end
        else: 
            self.x_end = self.x_start = screen_width/2
            self.y_start = screen_height/2
        self.y_end = self.y_start - self.length
        self.main_angle = 0
        self.speed = self.curr_speed = speed
        self.width = width
        self.circle_radius = circle_radius
        self.arm_num = arm_num
        self.ghost_queue = deque([])
        self.reset = False
        self.color = WHITE

    def update_pos(self, game_states, parent = None): #use self.parent instead
        self.reset = False
        self.curr_speed = self.speed + parent.speed if game_states["add_speed"] and parent is not None else self.speed
        self.main_angle += self.curr_speed
        self.length = self.length * (1-game_states["decay"])

        if parent != None:
            self.x_start = parent.x_end
            self.y_start = parent.y_end
        
        if game_states["sound_fx"] and not (0 < self.main_angle < 360):
            self.reset = True
            self.main_angle = self.main_angle % 360
            self.color = button_color
        
        rad_angle = math.radians(self.main_angle - 90)
        self.x_end = self.x_start + self.length * math.cos(rad_angle)
        self.y_end = self.y_start + self.length * math.sin(rad_angle)

    def update_sound_timer(self, currently_playing_arms):
        if game_states["sound_fx"] and self.reset:
            currently_playing_arms[self.arm_num] = 1

    def display_arms(self):
        if self.color != WHITE:
            self.color = tuple(min(c + 4, 255) for c in self.color)
        pygame.draw.circle(screen, DARK_GREY, (self.x_start, self.y_start), self.length, 1)
        pygame.draw.line(screen, self.color, (self.x_start, self.y_start), (self.x_end, self.y_end), self.width)
        pygame.draw.circle(screen, button_color, (self.x_start, self.y_start), self.circle_radius)

    def display_trail(self, max_ghost_length, game_states):
        ghost_array = [self.x_end, self.y_end, hsv_to_rgb(game_states["hue"])]
        if not game_states["reset"]:
            if not game_states["pause"]:
                self.ghost_queue.append(ghost_array)
        else:
            game_states["reset"] = False

        if len(self.ghost_queue) >= max_ghost_length:
            self.ghost_queue.popleft()
            
        for i, a in enumerate(self.ghost_queue):
            if i != len(self.ghost_queue) - 1 and game_states["show_trail"] == True:
                color = a[2] if game_states["rainbow"] == True else WHITE

                if game_states["show_lines"] == True:
                    pygame.draw.line(screen, color, (a[0], a[1]), (self.ghost_queue[i+1][0], self.ghost_queue[i+1][1]), 1)
                else:
                    pygame.draw.circle(screen, color, (a[0], a[1]), 1)    

#region title screen
def render_text(text, font_size=36, color=(255, 255, 255)):
    font = pygame.font.Font(None, font_size)
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect(center=(screen_width // 2, screen_height // 5))  # Centered position

    # Create multiple outlines with different offsets
    outline_surface = font.render(text, True, (65, 65, 65))  # Dark gray outline
    outline_surface2 = font.render(text, True, (30, 30, 30))
    outline_surface3 = font.render(text, True, (15, 15, 15))   # Even darker outline

    # Draw outlines slightly offset from center
    screen.blit(outline_surface3, (text_rect.x - 10, text_rect.y - 10))  
    screen.blit(outline_surface2, (text_rect.x - 8, text_rect.y - 8))  
    screen.blit(outline_surface, (text_rect.x - 4, text_rect.y - 4))  

    # Draw main text
    screen.blit(text_surface, text_rect)

def draw_gradient():
    for i in range(screen_height):
        gradient_step = i*(30/screen_height)
        curr_color = (gradient_step, gradient_step, gradient_step)
        pygame.draw.line(screen, curr_color, (0, i), (screen_width, i))
    pygame.draw.rect(screen, WHITE, ((0,0), (screen_width, screen_height)), 2)

def title_screen(): 
    build_title_arms()
    button_y = screen_height*3/4
    x_space = (screen_width - (4 * button_width))/5
    title_explanation_button = Button(x_space, button_y, button_width, button_height, button_color, 19)
    title_new_button = Button((2 * x_space) + button_width, button_y, button_width, button_height, button_color, 11)
    title_random_button = Button((3 * x_space) + (2*button_width), button_y, button_width, button_height, button_color, 12)
    title_exit_button = Button((4 * x_space) + (3*button_width), button_y, button_width, button_height, button_color, 13)
    title_buttons = [title_explanation_button, title_new_button, title_random_button, title_exit_button]
    
    while(game_states["title"]):
        draw_gradient()
        render_text("Fourier Harmonograph", 85)
        check_events(title_buttons)
        #[arm.update_pos(game_states) for arm in title_arms]
        for i in range(len(title_arms)):
            title_arms[i].update_pos(game_states, title_arms[i-1]) if i > 0 else title_arms[i].update_pos(game_states)
        [arm.display_arms() for arm in title_arms]
        [button.display_button(pygame.mouse.get_pos()) for button in title_buttons]
        clock.tick(60)
        pygame.display.flip()
    screen.fill(BLACK)
    pygame.display.flip()

def build_title_arms():
    global title_arms
    arm_speed_1 = random.uniform(0.75,1) * random.choice([1,-1])
    arm_length_1 = random.uniform(50,75)
    arm_speed_2 = random.uniform(1.5,2) * random.choice([1,-1])
    arm_length_2 = random.uniform(15,40)
    arm_speed_3 = (4 - abs(arm_speed_1) - abs(arm_speed_2)) * random.choice([1,-1])
    arm_length_3 = 150 - arm_length_1 - arm_length_2
    title_arm1 = Arm(arm_speed_1, arm_length_1, 1, 5, 0)
    title_arm2 = Arm(arm_speed_2, arm_length_2, 1, 4, 1, title_arm1)
    title_arm3 = Arm(arm_speed_3, arm_length_3, 1, 3, 2, title_arm2)
    title_arms = [title_arm1, title_arm2, title_arm3]
#endregion title screen

#region GameLoop
def get_inputs(game_states):
    global speed_ratios, length_ratios, fractions
    game_states["num_arms"] = 0
    while game_states["num_arms"] < 1:
        game_states["num_arms"] = int(get_number_input("Enter a whole number of arms >1: "))
    for i in range(1, game_states["num_arms"]+1):
        if game_states["random_inputs"]:
            speed_list.append(random.randint(0, 200) *  random.choice([1, -1]))
        else:
            speed_list.append(int(get_number_input(f"Enter the speed for arm {i} (any positive or negative number): ")))
    
    for i in range (1, game_states["num_arms"]+1):
        if game_states["random_inputs"]:
            length_list.append(random.randint(1,10000)*random.choice([1]))
        else:
            length_list.append(int(get_number_input(f"Enter the length for arm {i} (any positive or negative number): ")))

def build_arms():
    global repeat_nums, combined_speeds, combined_repeat_nums
    normalize(length_list, adjusted_lengths, length_percents, game_states["normal_length"]) #remove combined_length here
    normalize(speed_list, adjusted_speeds, speed_percents, game_states["normal_speed"])

    arm1 = (Arm(adjusted_speeds[0], adjusted_lengths[0], 2, 4, 0))
    arm_list.append(arm1)
    combined_speeds.append(speed_list[0])

    for i in range (1, game_states["num_arms"]):
        arm = (Arm(adjusted_speeds[i], adjusted_lengths[i], 2, 2, i, arm_list[i-1]))
        arm_list.append(arm)
        combined_speeds.append(speed_list[i] + speed_list[i-1])


    repeat_nums = calculate_repeat_nums(speed_list, game_states)
    combined_repeat_nums = calculate_repeat_nums(combined_speeds, game_states)
    calculate_ratios(speed_percents, speed_ratios, game_states)
    calculate_ratios(length_percents, length_ratios, game_states)

def next_frame(game_states):
    screen.fill(BLACK)
    pygame.draw.circle(screen, GREY, (screen_width/2, screen_height/2), border, 1)
    pygame.draw.rect(screen, WHITE, ((0,0), (screen_width, screen_height)), 3)
    clock.tick(60) # Limit FPS
    
    if not game_states["pause"]:
        game_states["hue"] = (game_states["hue"] + game_states["hue_step"])%1

    if game_states["show_buttons"]:    
        [button.display_button(pygame.mouse.get_pos()) for button in button_list]
    else:
        button_list[0].display_button(pygame.mouse.get_pos())

    if game_states["screenshot_timer"] is not 0:
        game_states["screenshot_timer"] -= 1
        text = font.render("Screenshot Saved", True, (255, 255, 255))
        screen.blit(text, (screen_width - 325, (screen_height - 190)))

def update_length(arm_list, adjusted_lengths, adjusted_speeds):
    if game_states["decay"] != 0:
        adjusted_lengths[:] = [arm.length for arm in arm_list]
    #if adjusted_speeds[1] != arm_list[1].curr_speed:
    adjusted_speeds[:] = [arm.curr_speed for arm in arm_list]
        
def print_info(game_states):
    speed_old_output =     "Speeds:              " + ",  ".join(map(str, speed_list)) 
    speed_new_output =     "Adjusted:            " + ",  ".join(map(lambda x: f"{x:.2f}", adjusted_speeds)) 
    
    speed_percent_output = "Percentages:     " + "%,  ".join(map(lambda x: f"{x:.2f}", speed_percents)) + "%"
    speed_fractions = [Fraction(speed_ratios[i], speed_ratios[i + 1]) for i in range(0, len(speed_ratios), 2)]
    speed_fraction_strings = [f"{frac.numerator}/{frac.denominator}" for frac in speed_fractions]
    speed_ratios_output = "Ratios:               " + ", ".join(speed_fraction_strings)

    length_old_output =     "Lengths:             " + ",  ".join(map(str, length_list)) 
    length_new_output =     "Adjusted:            " + ",  ".join(map(lambda x: f"{x:.2f}", adjusted_lengths)) 
    
    length_percent_output = "Percentages:     " + "%,  ".join(map(lambda x: f"{x:.2f}", length_percents)) + "%"
    length_fractions = [Fraction(length_ratios[i], length_ratios[i + 1]) for i in range(0, len(length_ratios), 2)]
    length_fraction_strings = [f"{frac.numerator}/{frac.denominator}" for frac in length_fractions]
    length_ratios_output = "Ratios:               " + ", ".join(length_fraction_strings)
    
    if game_states["add_speed"] == False:
        repeat_nums_output = "Rotations until pattern repeates:   " + ",  ".join(map(str, repeat_nums))
    else:
        repeat_nums_output = "Rotations until pattern repeates:   " + ",  ".join(map(str, combined_repeat_nums))
    rainbow_output = f"Rainbow Speed:   {1000* game_states["hue_step"]:.1f}" if  game_states["hue_step"] != 0 else "Rainbow Speed:   0"
    decay_output = f"   -   Decay:   {1000* game_states['decay']:.1f}" if game_states['decay'] != 0 else "   -   Decay:   0"
    extra_stats_output = rainbow_output + decay_output

    output_dict = ({speed_old_output: 20, speed_new_output: 40, speed_percent_output: 60, speed_ratios_output: 80, length_old_output: 115, 
                    length_new_output: 135, length_percent_output: 155, length_ratios_output: 175, repeat_nums_output: 210, extra_stats_output: 230})
    
    for key, value in output_dict.items():
        text = font.render(key, True, (255, 255, 255))
        screen.blit(text, (20, value))

def display_arms(currently_playing_arms):
    for i in range(game_states["num_arms"]):
        if game_states["show_arms"]:
            if not game_states["start"]:
                arm_list[i].display_arms()
            else:
                game_states["start"] = False

        if not game_states["pause"]:
            arm_list[i].update_pos(game_states, arm_list[i-1]) if i > 0 else arm_list[i].update_pos(game_states)
            arm_list[i].update_sound_timer(currently_playing_arms)

def check_events(button_list):
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            game_states["Running"] = False
        for button in button_list:
            button.check_click(event)

def play_sounds(game_states, currently_playing_arms, sounds, channels):
    if game_states["sound_fx"]:
        for arm in list(currently_playing_arms.keys()):
            if currently_playing_arms[arm] > 0:
                if not channels[arm].get_busy():
                    channels[arm].play(sounds[arm])
                currently_playing_arms[arm] -= 1

def initialize_sound_stuff():
    frequencies = calculate_frequencies(game_states["num_arms"], freq_high, freq_low)
    pygame.mixer.set_num_channels(game_states["num_arms"])
    sounds = [generate_sound(freq, duration, volume) for freq in frequencies]
    channels = [pygame.mixer.Channel(i) for i in range(game_states["num_arms"])]
    currently_playing_arms = {}
    for i in range(game_states["num_arms"]):
        currently_playing_arms[i] = 0

    return sounds, channels, currently_playing_arms

def game_loop(arm_list, adjusted_lengths, game_states):
    create_buttons()
    title_screen()
    #get_inputs(game_states)
    #build_arms()
    #next_frame(game_states)

    while game_states["running"]:
        if game_states["start"]:
            sounds, channels, currently_playing_arms = initialize_sound_stuff()
        
        next_frame(game_states)
        arm_list[-1].display_trail(max_ghost_length, game_states)
        display_arms(currently_playing_arms)    
        play_sounds(game_states, currently_playing_arms, sounds, channels)     
        check_events(button_list)
        update_length(arm_list, adjusted_lengths, adjusted_speeds)
        if game_states["show_info"] == True:
            print_info(game_states)
        pygame.display.flip()  # Update display

    pygame.quit()

game_loop(arm_list, adjusted_lengths, game_states)
#endregion GameLoop



"""
        if game_states["add_speed"] and parent is not None:
            self.curr_speed = self.speed + parent.speed
        else:
            self.curr_speed = self.speed

        
        self.main_angle += self.curr_speed
"""