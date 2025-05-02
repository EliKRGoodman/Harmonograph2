#add musical notes
#bug: speed percentages/ratios not showing up sometimes
#optimize screen rendering (only draw new stuff)
#make zoom respect decay

#region setup
import pygame, random, colorsys, os, math, datetime
from functools import reduce
from collections import deque
from fractions import Fraction

# Initialize pygame
pygame.init()
font = pygame.font.SysFont(None, 22)
font_prompt = pygame.font.SysFont(None, 30)
font_explain = pygame.font.SysFont(None, 26)
font_title = pygame.font.SysFont(None, 45)
clock = pygame.time.Clock()

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
button_color = (8, 65, 50)
button_pressed = (29, 53, 92)

game_states = ({"hue": 0, "gcd_value": 0, "num_arms": 0, "decay": 0, "screenshot_timer": 0,
                "hue_step": .0002, "normal_speed": 5, "new_normal_speed": 5, "normal_length": border-5, "new_normal_length": border-5,

                "running": True, "show_info": True, "show_trail": True, "show_lines":True, "rainbow": True, 
                "show_arms": True, "show_buttons": True, "start": True, "title": True, 
                "add_speed": False, "repeated": False, "reset": False, "random_inputs": False, 
                "pause": False, "back": False, "sound_fx": False,
                "last_click":"left"})

repeat_nums, combined_repeat_nums, arm_list, fractions, button_list, title_arms = [], [], [], [], [], [] #trail_list
length_list, adjusted_lengths, length_percents, length_ratios = [], [], [], []
speed_list,  adjusted_speeds, speed_percents, speed_ratios, combined_speeds, curr_speeds = [], [], [], [], [], []
back_button_container = []
text = ""
#endregion setup

#region setup
def get_number_input(prompt):
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

def hsv_to_rgb(hue):
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
        pygame.draw.rect(screen, self.color, ((self.top_left_x + 5, self.top_left_y), (self.width, self.height)))        
        pygame.draw.rect(screen, WHITE, ((self.top_left_x + 5, self.top_left_y), (self.width, self.height)), 2)

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
def reset_pattern_state(game_states):
    game_states["hue"] = game_states["decay"] = 0
    game_states["hue_step"] = .0002
    game_states["show_trail"] = game_states["rainbow"] = game_states["show_lines"] = game_states["reset"] = True
    game_states["new_normal_speed"] = game_states["normal_speed"] 
    game_states["new_normal_length"] = game_states["normal_length"]
    game_states["pause"] = False #?

    for list in [adjusted_lengths, length_percents, adjusted_speeds, speed_percents]:
        list.clear()
    for button in button_list:
        if button.button_name not in ("Toggle Info", "Toggle Arms", "Toggle Friction"):
            button.press = False

def reset_pattern(button, game_states):
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
    toggle_button(button, game_states, "sound_fx", False)

def back_button(button, game_states):
    game_states["back"] = True

def show_explanation(button, game_states):
    global back_button #    
    game_states["back"] = False
    toggle_string = "\"Toggle Info\", \"Toggle Lines\", \"Toggle Color\", \"Toggle Trail\", and \"Toggle Arms\" turn off visual elements."
    toggle_string_2 = "\"Toggle Lines\" shows the trail with points instead of lines."
    toggle_string_3 = "\"Toggle Friction\" partially simulates friction by adding the rotation of arm n to arm n+1."
    button_string = "\"New Pattern\" takes new starting conditions and \"Random Pattern\" just takes a number of arms and randomly generates their speeds and lengths."
    variable_string = "\"Speed +/-\" changes the speed of the pattern and \"Length +/-\" changes the arm lengths."
    variable_string_2 = "\"Decay +-\" gradually alters the arm lengths over time and \"Rainbow +-\" changes the rate at which the color of the trail changes."
    variable_string_3 = "Use left-click to increase values and right-click to decrease them."
    reset_string = "\"Reset Trail\" erases any existing trail and \"Reset Pattern\" resets the pattern to the initial starting conditions."
    save_string = "\"Save Pattern\" outputs the starting conditions to a text file and \"Pause\" suspends the animation."
    #add toggle sound, screenshot

    string_list = [toggle_string, toggle_string_2, toggle_string_3, button_string, variable_string, variable_string_2, variable_string_3, reset_string, save_string]
    y_pos_list = [20, 40, 60, 80, 120, 140, 160, 180, 220, 240]

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

button_names = (["Toggle Buttons", "!Toggle Sound", "Toggle Arms", "Toggle Trail", "Toggle Color", "Toggle Lines", "Toggle Info", #left outer, ascending
                 "Speed +/-", "Zoom +/-", "Decay +/-", "Rainbow +/-", "New Pattern", "Random Pattern", "Exit", #right outer, descending

                  "Toggle Friction", "Reset Pattern", "Reset Trail", #left inner, ascending
                  "Screenshot", "Pause", "~Explanation"]) #right outer, descending

button_functions = ([show_buttons, toggle_sound, toggle_arms, toggle_trail, toggle_color, toggle_lines, toggle_info, #left outer, ascending
                    change_speed, zoom, add_decay, add_rainbow, new_pattern, random_pattern, exit_button, #right outer
                    
                    add_speeds, reset_pattern, reset_trail, #left inner, ascending
                    screenshot, pause_game, show_explanation]) #right inner
#endregion Buttons

class Arm:
    def __init__ (self, speed, length, width, circle_radius, parent = None): #add parent here
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
        self.ghost_queue = deque([])
        self.reset = False

    def update_pos(self, game_states, parent = None): #use self.parent instead
        if game_states["add_speed"] and parent is not None:
            self.curr_speed = self.speed + parent.speed
        else:
            self.curr_speed = self.speed
        if not game_states["pause"]:
            global decay
            self.reset = False
            if parent != None:
                self.x_start = parent.x_end
                self.y_start = parent.y_end
            self.main_angle += self.curr_speed
            if self.main_angle > 360:
                self.reset = True
                self.main_angle = self.main_angle % 360
            self.length = self.length * (1-game_states["decay"])

            rad_angle = math.radians(self.main_angle - 90)
            self.x_end = self.x_start + self.length * math.cos(rad_angle)
            self.y_end = self.y_start + self.length * math.sin(rad_angle)

    def display_arms(self):
        pygame.draw.circle(screen, DARK_GREY, (self.x_start, self.y_start), self.length, 1)
        pygame.draw.line(screen, WHITE, (self.x_start, self.y_start), (self.x_end, self.y_end), self.width)
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

def title_screen(): #button dimension can be made constants above
    build_title_arms()
    #button_width = 150
    #button_height = 40
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
    title_arm1 = Arm(arm_speed_1, arm_length_1, 1, 5)
    title_arm2 = Arm(arm_speed_2, arm_length_2, 1, 4, title_arm1)
    title_arm3 = Arm(arm_speed_3, arm_length_3, 1, 3, title_arm2)
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

    arm1 = (Arm(adjusted_speeds[0], adjusted_lengths[0], 2, 4))
    arm_list.append(arm1)
    combined_speeds.append(speed_list[0])

    for i in range (1, game_states["num_arms"]):
        arm = (Arm(adjusted_speeds[i], adjusted_lengths[i], 1, 2, arm_list[i-1]))
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

def display_arms():
    for i in range(game_states["num_arms"]):
        if game_states["show_arms"]:
            if not game_states["start"]:
                arm_list[i].display_arms()
            else:
                game_states["start"] = False

        arm_list[i].update_pos(game_states, arm_list[i-1]) if i > 0 else arm_list[i].update_pos(game_states)

def check_events(button_list):
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            game_states["Running"] = False
        for button in button_list:
            button.check_click(event)

def game_loop(arm_list, adjusted_lengths, game_states):
    create_buttons()
    title_screen()
    #get_inputs(game_states)
    #build_arms()
    #next_frame(game_states)

    while game_states["running"]:
        next_frame(game_states)
        arm_list[-1].display_trail(max_ghost_length, game_states)
        display_arms()         
        check_events(button_list)
        update_length(arm_list, adjusted_lengths, adjusted_speeds)
        if game_states["show_info"] == True:
            print_info(game_states)
        pygame.display.flip()  # Update display

    pygame.quit()


game_loop(arm_list, adjusted_lengths, game_states)
#endregion GameLoop




































#region Trash
"""
        #if game_states["start"]: #can be combined with the restart pop
        #    arm_list[-1].ghost_queue.popleft()
        #    game_states["start"] = False

#def save_pattern(button, game_states):
#    return True

    ##adjusted_lengths.clear()
    #length_percents.clear()
    #speed_percents.clear()
    #adjusted_speeds.clear()


    #arm_list.clear()
    #speed_list.clear()
    #length_list.clear()
    #speed_ratios.clear()
    #length_ratios.clear()
    #combined_speeds.clear()

    button = Button(2 *(button_space + 5) + button_width, screen_height - button_space - button_height - 10, button_width, button_height, button_color, 15)
    #button_list.append(button)
    button = Button(2 *(button_space + 5) + button_width, screen_height - 2*button_space - 2*button_height - 10, button_width, button_height, button_color, 14)
    #button_list.append(button)
    button = Button(2 *(button_space + 5) + button_width, screen_height - 3*button_space - 3*button_height - 10, button_width, button_height, button_color, 16)
    #button_list.append(button)

    button = Button(screen_width - 2*button_space - 2*button_width - 15, screen_height - button_space - button_height - 10, button_width, button_height, button_color, 17)
    #button_list.append(button)
    button = Button(screen_width - 2*button_space - 2*button_width - 15, screen_height - 2*button_space - 2*button_height - 10, button_width, button_height, button_color, 19)
    #button_list.append(button)
    button = Button(screen_width - 2*button_space - 2*button_width - 15, screen_height - 3*button_space - 3*button_height - 10, button_width, button_height, button_color, 18)
    #button_list.append(button)
                    
"""
#num_arms, gcd_value, hue = 0, 0, 0   #rotations_to_restart, length_total, speed_total, lcm_result, num_rotations, #starting_pos = False
#normal_length = new_normal_length = border - 5
#normal_speed = new_normal_speed = 5
#running, show_info, show_trail, rainbow, show_lines = True, True, True, True, True
#add_speed, repeated, reset, rando = False, False, False, False
#game_states = {num_arms: 0, gcd_value: 0, hue: 0, }

    #array_combined.append(array_new[i] + array_new [i-1]) if i > 0 else array_combined.append(array_new[i])


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

"""
def first_frame(game_states):
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

"""
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
#endregion Trash