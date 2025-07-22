import customtkinter as ctk
from tkinter import filedialog
import pygame
from mutagen.easyid3 import EasyID3
import os
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC
from PIL import Image, ImageTk
import io
import time
import keyboard
from PIL import ImageOps
from PIL import Image, ImageTk, ImageDraw, ImageOps
import sys


pygame.mixer.init()

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.geometry("470x220")  # Increased height to fit sliders
app.title("Vixl0's Way Too Simple Music Player")
app.resizable(False, False)

# Configure columns and rows
app.grid_columnconfigure(0, weight=0)  # cover art column
app.grid_columnconfigure(1, weight=1)  # title/artist column
app.grid_columnconfigure(2, weight=0)  # buttons columns
app.grid_columnconfigure(3, weight=0)
app.grid_rowconfigure(3, weight=1)  # For sliders

# Globals
current_file = None
playing = False
play_button_text = "Play"
song_length = 0
current_pos = 0  # position in seconds where playback started or was last seeked
last_update_time = 0  # time when playback started or was last seeked
is_muted = False
previous_volume = 0.5  # default volume
current_folder = None
folder_playlist = []
current_folder_index = 0
pause_start_time = 0
total_paused_time = 0


cover_label = ctk.CTkLabel(app, text="")
cover_label.grid(row=1, column=0, rowspan=2, padx=(10, 5), pady=(10, 2), sticky="nw")


def add_rounded_corners(im, radius):
    # Create a rounded rectangle mask
    rounded_mask = Image.new('L', im.size, 0)
    draw = ImageDraw.Draw(rounded_mask)
    draw.rounded_rectangle((0, 0) + im.size, radius=radius, fill=255)
    
    # Apply mask to the image, preserving alpha
    im_rounded = im.copy()
    im_rounded.putalpha(rounded_mask)
    
    return im_rounded


def update_metadata_ui(file_path):
    global song_length
    try:
        audio = EasyID3(file_path)
        title = audio.get("title", ["Unknown Title"])[0]
        artist = audio.get("artist", ["Unknown Artist"])[0]
        album = audio.get("album", ["Unknown Album"])[0]
        song_title.configure(text=title)
        song_artist.configure(text=artist)
        song_album.configure(text=album)
    except Exception as e:
        print("Error reading metadata:", e)
        song_title.configure(text=os.path.basename(file_path))
        song_artist.configure(text="Unknown Artist")
        song_artist.configure(text="Unknown Album")

    # Update cover art
    try:
        audio = MP3(file_path, ID3=ID3)
        for tag in audio.tags.values():
            if isinstance(tag, APIC):
                image_data = tag.data
                # Example usage in your cover art loading:
                image = Image.open(io.BytesIO(image_data)).resize((120, 120))

                # Add bezel: expand border with black color
                image_with_border = ImageOps.expand(image, fill='blue')

                # Add rounded corners with radius 15
                image_rounded = add_rounded_corners(image_with_border, radius=15)

                cover_image = ImageTk.PhotoImage(image_rounded)
                cover_label.configure(image=cover_image, text="")
                cover_label.image = cover_image
                break
        else:
            cover_label.configure(image=None, text="🎵")
    except Exception as e:
        print("No album art found:", e)
        cover_label.configure(image=None, text="🎵")

    # Update duration label and playback slider max value
    try:
        audio_info = MP3(file_path)
        song_length = audio_info.info.length
        song_duration.configure(text=format_time(song_length))
        playback_slider.configure(to=song_length)
        current_song_pos.configure(text="00:00")
    except Exception as e:
        print("Error reading duration:", e)
        song_duration.configure(text="--:--")
        playback_slider.configure(to=0)
        current_song_pos.configure(text="00:00")

def load_file():
    global current_file, playing, current_folder, folder_playlist, current_folder_index
    global song_length, current_pos, last_update_time

    file_path = filedialog.askopenfilename(
        filetypes=[("MP3 files", "*.mp3")],
        title="Choose an MP3 file"
    )
    if file_path:
        current_file = file_path
        pygame.mixer.music.load(current_file)
        pygame.mixer.music.play()
        playing = True

        # Reset playback info
        current_pos = 0
        last_update_time = time.time()

        update_metadata_ui(current_file)


        # Setup playlist for folder
        current_folder = os.path.dirname(current_file)
        folder_playlist = sorted([
            f for f in os.listdir(current_folder)
            if f.lower().endswith(".mp3")
        ])
        current_folder_index = folder_playlist.index(os.path.basename(current_file))

        play_button.configure(text="Pause")

        update_playback_slider()  # Start slider updates
        

        print("Playing:", current_file)
    else:
        print("No file selected")

def get_playback_position():
    if not playing:
        return current_pos  # Don't advance if paused
    return current_pos + (time.time() - last_update_time)




def skip_song():
    global current_folder_index, folder_playlist, current_folder, playing
    global song_length, current_pos, last_update_time

    if not folder_playlist or current_folder is None:
        print("No folder playlist available")
        return

    current_folder_index = (current_folder_index + 1) % len(folder_playlist)
    next_song_path = os.path.join(current_folder, folder_playlist[current_folder_index])
    pygame.mixer.music.load(next_song_path)
    pygame.mixer.music.play()
    playing = True

    # Reset playback info
    current_pos = 0
    last_update_time = time.time()

    update_metadata_ui(next_song_path)

    play_button.configure(text="Pause")

    update_playback_slider()

    print("Skipped to:", next_song_path)

def unskip_song():
    global current_folder_index, folder_playlist, current_folder, playing
    global song_length, current_pos, last_update_time

    if not folder_playlist or current_folder is None:
        print("No folder playlist available")
        return

    current_folder_index = (current_folder_index - 1) % len(folder_playlist)
    previous_song_path = os.path.join(current_folder, folder_playlist[current_folder_index])
    pygame.mixer.music.load(previous_song_path)
    pygame.mixer.music.play()
    playing = True

    # Reset playback info
    current_pos = 0
    last_update_time = time.time()

    update_metadata_ui(previous_song_path)

    play_button.configure(text="Pause")

    update_playback_slider()

    print("UnSkipped to:", previous_song_path)

pause_start_time = 0
total_paused_time = 0

def play_music():
    global playing, pause_start_time, total_paused_time, last_update_time, current_pos
    if playing:
        pygame.mixer.music.pause()
        playing = False
        current_pos += time.time() - last_update_time  # Save how long we played
        play_button.configure(text="Resume")
    else:
        pygame.mixer.music.unpause()
        last_update_time = time.time()  # Reset the play clock
        playing = True
        play_button.configure(text="Pause")



def change_volume(value):
    volume = float(value) / 100
    pygame.mixer.music.set_volume(volume)
    volume_percent.configure(text=f"{int(value)}%")

def volume_up():
    current = volume_slider.get()
    new = min(100, current + 5)  # increase by 5%, max 100%
    volume_slider.set(new)
    change_volume(new)

def volume_down():
    current = volume_slider.get()
    new = max(0, current - 5)  # decrease by 5%, min 0%
    volume_slider.set(new)
    change_volume(new)

def toggle_mute():
    global is_muted, previous_volume
    if is_muted:
        pygame.mixer.music.set_volume(previous_volume)
        volume_slider.set(previous_volume * 100)
        volume_percent.configure(text=f"{int(previous_volume * 100)}%")
        mute_button.configure(text="Mute")
        is_muted = False
    else:
        previous_volume = pygame.mixer.music.get_volume()
        pygame.mixer.music.set_volume(0)
        volume_slider.set(0)
        volume_percent.configure(text="0%")
        mute_button.configure(text="Unmute")
        is_muted = True

def seek_song(value):
    global playing, current_pos, last_update_time
    if current_file:
        seek_time = float(value)
        pygame.mixer.music.play(start=seek_time)
        current_pos = seek_time
        last_update_time = time.time()
        if not playing:
            pygame.mixer.music.pause()
        playback_slider.set(current_pos)


def update_playback_slider():
    if current_file and playing:
        pos = get_playback_position()
        if pos > song_length:
            pos = song_length
        playback_slider.set(pos)
        current_song_pos.configure(text=format_time(pos))
    app.after(500, update_playback_slider)


def format_time(seconds):
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins:02}:{secs:02}"

def focus_app_window():
    app.deiconify()        # Restore window if minimized
    app.lift()             # Bring window to the front
    app.focus_force()      # Focus the window


# Buttons
play_button = ctk.CTkButton(
    app,
    text=play_button_text,
    font=("Arial", 18, "bold"),
    width=30,
    height=30,
    command=play_music
)

load_button = ctk.CTkButton(
    app,
    text="Load File",
    width=70,
    height=30,
    command=load_file
)

skip_button = ctk.CTkButton(
    app,
    text="Skip",
    width=60,
    height=30,
    font=("Arial",16,"bold"),
    command=skip_song
)

unskip_button = ctk.CTkButton(
    app,
    text="UnSkip",
    width=60,
    height=30,
    font=("Arial",16,"bold"),
    command=unskip_song
)

# Labels
song_title = ctk.CTkLabel(
    app,
    text="--No song loaded--",
    font=("Arial", 24, "bold"),
)

song_artist = ctk.CTkLabel(
    app,
    text="--",
    font=("Arial", 18),
)

song_album = ctk.CTkLabel(
    app,
    text="--",
    font=("Arial", 18),
)

volume_percent = ctk.CTkLabel(
    app,
    text="50%",
    font=("Arial", 18),
)

current_song_pos = ctk.CTkLabel(
    app,
    text="00:00",
    font=("Arial", 18),
)

song_duration = ctk.CTkLabel(
    app,
    text="00:00",
    font=("Arial", 18),
)

# Volume slider
volume_slider = ctk.CTkSlider(
    app,
    from_=0,
    to=100,
    number_of_steps=100,
    command=change_volume
)
volume_slider.set(50)  # default volume 50%
pygame.mixer.music.set_volume(0.5)

mute_button = ctk.CTkButton(
    app,
    text="Mute",
    width=32,
    height=18,
    command=toggle_mute
)

# Playback slider
playback_slider = ctk.CTkSlider(
    app,
    from_=0,
    to=100,
    number_of_steps=100,
    command=seek_song
)

# Get the directory where the script is running (even when compiled)
base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
placeholder_path = os.path.join(base_path, "cover_art_placeholder.png")

# Load the placeholder image
placeholder_image = Image.open(placeholder_path)
placeholder_image = placeholder_image.resize((120, 120))  # Adjust size as needed
cover_art_image = ImageTk.PhotoImage(placeholder_image)

# Apply it to your label or image widget
cover_label.configure(image=cover_art_image)
cover_label.image = cover_art_image  # Prevent garbage collection

# Layout
play_button.grid(row=0, column=2, padx=5, pady=10, sticky="nw")
load_button.grid(row=0, column=3, padx=10, pady=10, sticky="nw")
skip_button.grid(row=0, column=1, padx=2, pady=(10,0), sticky="nw")
unskip_button.grid(row=0, column=0, padx=2, pady=(10,0), sticky="ne")

song_title.grid(row=1, column=1, columnspan=2, sticky="nw", pady=(5, 0), padx=(0, 10))
song_artist.grid(row=2, column=1, columnspan=2, sticky="nw", pady=(0, 0), padx=(0, 10))
song_album.grid(row=3, column=1, columnspan=2, sticky="nw", pady=(0, 0), padx=(0, 10))

cover_label.grid(row=1, column=0, rowspan=3, padx=(10, 5), pady=(2, 2), sticky="nw")

volume_slider.grid(row=4, column=1, columnspan=2, sticky="ew", padx=(0, 10), pady=3)
playback_slider.grid(row=5, column=1, columnspan=2, sticky="ew", padx=(0, 10), pady=(0, 5))

current_song_pos.grid(row=5, column=0, sticky="ne", pady=(0, 0), padx=(10, 5))
song_duration.grid(row=5, column=3, sticky="nw", pady=(0, 0), padx=(0, 5))
volume_percent.grid(row=4, column=3, sticky="w", pady=(0, 0), padx=(0, 5))
mute_button.grid(row=4, column=0, sticky="e", pady=(0, 0), padx=(10, 5))

# Register global hotkeys Ctrl+Space for play/pause and Ctrl+Right for skip
keyboard.add_hotkey('ctrl+space', play_music)
keyboard.add_hotkey('ctrl+right', skip_song)
keyboard.add_hotkey('ctrl+left', unskip_song)

# Register global hotkeys for volume control
keyboard.add_hotkey('ctrl+up', volume_up)
keyboard.add_hotkey('ctrl+down', volume_down)

# Focus the app window
keyboard.add_hotkey('ctrl+f', focus_app_window)



app.mainloop()
