import pygame
import numpy as np
import time


# Initialize Pygame mixer
pygame.mixer.init(frequency=44100, size=-16, channels= 2, buffer= 1024)

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

def generate_sound(frequency, duration, volume):

    sample_rate = 44100  # Samples per second
    t = np.linspace(0, duration, int(sample_rate * duration), False) # Create a numpy array for the waveform

    waveform = volume * np.sin(2 * np.pi * frequency * t) 
    waveform_integers = np.int16(waveform * 32767) # Convert waveform to 16-bit signed integers
    waveform_stereo = np.column_stack((waveform_integers, waveform_integers)) # Make the mono waveform into stereo by duplicating it

    return pygame.sndarray.make_sound(waveform_stereo) # Convert numpy array to Pygame sound

freq_high = 480  # Frequency in Hz (A4)
freq_low = 80
duration = 1.0   # Duration in seconds
volume = 0.1     # Volume (0.0 to 1.0)
num_arms = 5
frequencies = calculate_frequencies(num_arms, freq_high, freq_low)

pygame.mixer.set_num_channels(num_arms)
sounds = [generate_sound(freq, duration, volume) for freq in frequencies]
channels = [pygame.mixer.Channel(i) for i in range(num_arms)]

currently_playing_arms = {0:10, 1:20, 2:30, 3:40, 4:50}


while (True):
    time.sleep(0.1)
    for arm in list(currently_playing_arms.keys()):
        if currently_playing_arms[arm] > 0:
            if not channels[arm].get_busy():
                channels[arm].play(sounds[arm])
            currently_playing_arms[arm] -= 1

"""           
def generate_sound_0(frequency, duration, volume):

    sample_rate = 44100  # Samples per second
    t = np.linspace(0, duration, int(sample_rate * duration), False) # Create a numpy array for the waveform

    waveform = volume * np.sin(2 * np.pi * frequency * t) 
    waveform_integers = np.int16(waveform * 32767) # Convert waveform to 16-bit signed integers
    waveform_stereo = np.column_stack((waveform_integers, waveform_integers)) # Make the mono waveform into stereo by duplicating it

    return pygame.sndarray.make_sound(waveform_stereo) # Convert numpy array to Pygame sound
"""

