import customtkinter as ctk
from tkinter import filedialog
import pygame
from mutagen.easyid3 import EasyID3
import os
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC
from PIL import Image, ImageTk
import io
import json
import time
import keyboard
from PIL import ImageOps
from PIL import Image, ImageTk, ImageDraw, ImageOps
import sys
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import zipfile
import shutil

#Imports
#########################################################################

#########################################################################

#########################################################################


# Define a safe path for loading external files, whether running as .py or .exe
def resource_path(relative_path):
    """ Get the absolute path to a resource, works for dev and PyInstaller """
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


pygame.mixer.init()

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme(resource_path("themes/lavender.json"))

#App settings
app = ctk.CTk()
app.geometry("490x220")
app.title("Vixl0's Way Too Simple Music Player")
app.minsize(490, 220)    # minimum width 470, minimum height 220
app.resizable(True, False)  # Allow horizontal resizing, disallow vertical

icon_path = os.path.join(os.path.dirname(__file__), "icon.ico")
app.iconbitmap(icon_path)


# Define folder structure
APP_NAME = "Vixl0"
APP_FOLDER = "MusicPlayer"

APPDATA_PATH = os.path.join(os.getenv("LOCALAPPDATA"), APP_NAME, APP_FOLDER)
SETTINGS_PATH = os.path.join(APPDATA_PATH, "settings.json")

# Ensure folder exists
os.makedirs(APPDATA_PATH, exist_ok=True)


# default settings
default_settings = {
    "theme_color": "lavender",
    "theme": "dark",
    "Playlists": []
}

def load_settings():
    if not os.path.exists(SETTINGS_PATH):
        return {}
    with open(SETTINGS_PATH, "r") as f:
        return json.load(f)

def save_settings(new_data):
    os.makedirs(APPDATA_PATH, exist_ok=True)

    # Step 1: Load existing settings (if file exists)
    if os.path.exists(SETTINGS_PATH):
        with open(SETTINGS_PATH, "r") as f:
            existing_data = json.load(f)
    else:
        existing_data = {}

    # Step 2: Update only the theme-related keys
    existing_data.update(new_data)

    # Step 3: Save all settings back
    with open(SETTINGS_PATH, "w") as f:
        json.dump(existing_data, f, indent=4)




load_settings()


# Space things out
app.grid_columnconfigure(0, weight=0)  # cover art column
app.grid_columnconfigure(1, weight=1)  # title/artist column
app.grid_columnconfigure(2, weight=0)  # buttons columns
app.grid_columnconfigure(3, weight=0)
app.grid_rowconfigure(3, weight=1)  # For sliders

# Global variables
current_file = None #File currently playing
playing = False #Is song playing rn
play_button_text = "Play" #useless
song_length = 0 #length of the song
current_pos = 0  # number of seconds after the song started
last_update_time = 0  # time when playback started or was last seeked
is_muted = False #pretty obvious
previous_volume = 0.5  # default volume
current_folder = None #folder where the last mp3 was played
folder_playlist = [] #all mp3s in the folder
current_folder_index = 0 #what number song is the mp3 in the "playlist"
pause_start_time = 0 #pausing settings
total_paused_time = 0 #pausing settings
dark_mode = "on"
THEME_OPTIONS = ["breeze", "coffee", "orange", "midnight", "violet", "autumn", "metal", "cherry", "red", "patina", "yellow", "marsh", "rose", "pink", "lavender", "carrot", "rime", "sky"]  # Theme color options


# Playlist globals
current_playlist_songs = []
current_playlist_index = 0

manual_song_list = []
manual_song_index = 0
in_playlist_mode = False


#The Cover Label settings
cover_label = ctk.CTkLabel(app, text="")
cover_label.grid(row=1, column=0, rowspan=2, padx=(10, 5), pady=(10, 2), sticky="nw")

settings = load_settings()
theme_color = settings.get("theme_color", "lavender")
ctk.set_default_color_theme(resource_path(f"themes/{theme_color}.json"))


# Get the directory of the current script
current_dir = os.path.dirname(os.path.abspath(__file__))

# Build the full path to the theme file
theme_path = os.path.join(current_dir, "themes", f"{theme_color}.json")

# Apply the theme
ctk.set_default_color_theme(resource_path(theme_path))



#########################################################################

#########################################################################

APP_DIR = os.path.dirname(os.path.abspath(__file__))
IMPORTED_PLAYLISTS_DIR = os.path.join(APP_DIR, "Imported Playlists")
SETTINGS_PATH = os.path.join(APPDATA_PATH, "settings.json")

def export_playlist(playlist):
    from pathlib import Path

    confirm = messagebox.askyesno(f"Export Playlist: {playlist}", "This will take a little while")
    if confirm:
        playlist_name = playlist["name"]
        songs = playlist["songs"]

        # Path to Downloads folder
        downloads_path = os.path.join(Path.home(), "Downloads")
        export_folder = os.path.join(downloads_path, f"{playlist_name}_Export")
        os.makedirs(export_folder, exist_ok=True)

        # Copy all songs into the export folder
        for song_path in songs:
            try:
                shutil.copy(song_path, export_folder)
            except FileNotFoundError:
                print(f"Song not found and skipped: {song_path}")

        # Write playlist metadata file
        metadata = {
            "name": playlist_name,
            "songs": [os.path.basename(path) for path in songs]  # Only filenames
        }
        with open(os.path.join(export_folder, "playlist.json"), "w") as f:
            json.dump(metadata, f, indent=4)

        # Zip the folder
        zip_path = os.path.join(downloads_path, f"{playlist_name}.zip")
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(export_folder):
                for file in files:
                    abs_path = os.path.join(root, file)
                    rel_path = os.path.relpath(abs_path, export_folder)
                    zipf.write(abs_path, arcname=rel_path)

        # Clean up the folder after zipping
        shutil.rmtree(export_folder)

        print(f"Playlist exported to: {zip_path}")
        messagebox.showinfo("Export Complete", f"Exported playlist: {playlist['name']}")

        


def import_playlist():
    zip_path = filedialog.askopenfilename(filetypes=[("Playlist Zip Files", "*.zip")])
    if not zip_path:
        return

    # Create folder for imported playlists if it doesn't exist
    os.makedirs(IMPORTED_PLAYLISTS_DIR, exist_ok=True)

    with zipfile.ZipFile(zip_path, 'r') as zf:
        # Find the playlist.json file inside the zip
        playlist_json_name = next((name for name in zf.namelist() if name.endswith("playlist.json")), None)
        if not playlist_json_name:
            print("Invalid playlist zip (no playlist.json found).")
            return
        
        # Load the playlist metadata
        playlist_data = json.loads(zf.read(playlist_json_name).decode('utf-8'))
        playlist_name = playlist_data.get("name", "Imported Playlist")

        # Create folder for this specific playlist
        target_folder = os.path.join(IMPORTED_PLAYLISTS_DIR, playlist_name)
        os.makedirs(target_folder, exist_ok=True)

        # Extract everything into that folder
        zf.extractall(target_folder)

        # Load MP3 file paths
        song_paths = [
            os.path.join(target_folder, f)
            for f in os.listdir(target_folder)
            if f.lower().endswith(".mp3")
        ]

        add_imported_playlist_to_settings(playlist_name, song_paths)



def add_imported_playlist_to_settings(playlist_name, song_paths):
    # Check if settings dictionary exists
    if "Playlists" not in settings:
        settings["Playlists"] = []

    # Prevent duplicates
    existing_names = [p["name"] for p in settings["Playlists"]]
    if playlist_name in existing_names:
        print(f"Playlist '{playlist_name}' already exists in settings.")
        return

    # Create playlist entry
    playlist = {
        "name": playlist_name,
        "songs": song_paths
    }

    settings["Playlists"].append(playlist)
    save_settings(settings)
    print(f"Added imported playlist '{playlist_name}' to settings.")
    messagebox.showinfo("Import Complete", "You can now delete the zip folder from your downloads")






def open_settings_window():
    settings = load_settings()

    global settings_window
    settings_window = ctk.CTkToplevel(app)
    settings_window.title("Settings")
    settings_window.geometry("300x270")
    settings_window.resizable(False, False)

    settings_window.deiconify()
    settings_window.lift()
    settings_window.focus_force()

    # --- Theme Color ---
    theme_label = ctk.CTkLabel(settings_window, text="Choose Theme Color:")
    theme_label.pack(pady=(8, 0))

    current_theme = settings.get("theme_color", "lavender")
    theme_var = ctk.StringVar(value=current_theme)

    theme_option_menu = ctk.CTkOptionMenu(
        settings_window,
        values=THEME_OPTIONS,
        variable=theme_var,
        command=change_theme_color  # Live update
    )
    theme_option_menu.pack(pady=10)

    # --- Dark Mode ---
    dark_label = ctk.CTkLabel(settings_window, text="Enable Dark Mode:")
    dark_label.pack(pady=(18, 0))

    current_dark = settings.get("theme_mode", "light")
    dark_mode_var = ctk.StringVar(value="on" if current_dark == "dark" else "off")

    dark_mode_checkbox = ctk.CTkCheckBox(
        master=settings_window,
        text="",
        variable=dark_mode_var,
        onvalue="on",
        offvalue="off",
        command=lambda: toggle_dark_mode(dark_mode_var.get())  # Live update
    )
    dark_mode_checkbox.pack(pady=10)

    # --- Reset Preferences ---

    reset_preferences_button = ctk.CTkButton(settings_window, text="Reset Preferences", command=lambda: reset_preferences())
    reset_preferences_button.pack(pady=(22, 0))
    


    # --- Save Button (optional, for permanent save confirmation) ---
    save_button = ctk.CTkButton(settings_window, text="Save Settings", command=lambda: save_settings({
        "theme_color": theme_var.get(),
        "theme_mode": "dark" if dark_mode_var.get() == "on" else "light"
    }))
    save_button.pack(pady=10)


def reset_preferences():
    confirm = messagebox.askyesno("Reset Preferences", "This will reset all your saved options including Playlists and Themes to the default values")
    if confirm:
        save_settings(default_settings)

def change_theme_color(color):
    ctk.set_default_color_theme(resource_path(f"themes/{color}.json"))  # Change theme immediately
    save_settings({"theme_color": color})

def toggle_dark_mode(value):
    mode = "dark" if value == "on" else "light"
    ctk.set_appearance_mode(mode)  # Change mode immediately
    save_settings({"theme_mode": mode})




def open_playlist_window():
    settings = load_settings()  # Load current settings including playlists

    global playlist_window
    

    playlist_window = ctk.CTkToplevel(app)
    playlist_window.title("Playlists")
    playlist_window.geometry("220x400")
    playlist_window.resizable(True, False)
    playlist_window.minsize(400, 250)

    playlist_window.deiconify()  
    playlist_window.lift()  
    playlist_window.focus_force()


    list_frame = ctk.CTkFrame(playlist_window)
    list_frame.pack(fill="both", expand=True, padx=10, pady=(10, 5))
    
    canvas = ctk.CTkCanvas(list_frame)
    scrollbar = ctk.CTkScrollbar(list_frame, orientation="vertical", command=canvas.yview)
    scrollable_frame = ctk.CTkFrame(canvas)
    
    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(
            scrollregion=canvas.bbox("all")
        )
    )
    
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    def refresh_playlists():
        playlists = load_settings().get("Playlists", [])

        for widget in scrollable_frame.winfo_children():
            widget.destroy()

        for col_index, playlist in enumerate(playlists):
            playlist_name = playlist.get("name", f"Playlist {col_index+1}")

            def on_left_click(p=playlist):
                load_playlist(p)

            def on_right_click(event, p=playlist):
                    confirm = messagebox.askyesno("Delete Playlist", f"Delete playlist '{p['name']}'?")
                    if confirm:
                        settings = load_settings()
                        settings["Playlists"] = [pl for pl in settings.get("Playlists", []) if pl["name"] != p["name"]]
                        save_settings(settings)
                        refresh_playlists()

                        # --- Delete associated imported playlist folder if it exists ---
                        folder_path = os.path.join(IMPORTED_PLAYLISTS_DIR, p["name"])
                        if os.path.exists(folder_path) and os.path.isdir(folder_path):
                            try:
                                shutil.rmtree(folder_path)
                                print(f"Deleted folder: {folder_path}")
                            except Exception as e:
                                print(f"Failed to delete folder '{folder_path}': {e}")

            # Create button for the playlist
            playlist_btn = ctk.CTkButton(
                scrollable_frame,
                text=playlist_name,
                font=("Arial", 16, "bold"),
                command=on_left_click
            )
            playlist_btn.grid(row=0, column=col_index, padx=20, pady=(10, 0), sticky="n")

            # Bind right click to delete
            playlist_btn.bind("<Button-3>", on_right_click)

            for row_index, song_path in enumerate(playlist.get("songs", [])):
                try:
                    audio = EasyID3(song_path)
                    song_name = audio.get("title", ["Unknown Title"])[0]
                except:
                    song_name = os.path.basename(song_path)

                # Create a full-width frame per song row
                song_frame = ctk.CTkFrame(scrollable_frame, fg_color="transparent")
                song_frame.grid(row=row_index + 1, column=col_index, sticky="ew", padx=5, pady=2)

                # Make sure the frame expands horizontally
                song_frame.grid_columnconfigure(0, weight=1)

                song_label = ctk.CTkLabel(
                    song_frame,
                    text=f"{row_index+1}. {song_name}",
                    font=("Arial", 12)
                )
                song_label.grid(row=0, column=0, sticky="w")  # Align left

                song_play_button = ctk.CTkButton(
                    song_frame,
                    text=">",
                    font=("Arial", 12),
                    width=16,
                    height=16,
                    command=lambda index=row_index, pl=playlist: load_playlist(pl, index)
                )
                song_play_button.grid(row=0, column=1, sticky="e")




    refresh_playlists()

    entry_frame = ctk.CTkFrame(playlist_window)
    entry_frame.pack(fill="x", padx=10, pady=10)

    new_playlist_entry = ctk.CTkEntry(entry_frame, placeholder_text="New playlist name...", height=66)
    new_playlist_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))

    def add_playlist():
        name = new_playlist_entry.get().strip()
        if not name:
            messagebox.showwarning("Input Error", "Please enter a playlist name.")
            return

        existing_names = [p["name"] for p in settings.get("Playlists", [])]
        if name in existing_names:
            messagebox.showwarning("Duplicate Playlist", f"A playlist named '{name}' already exists.")
            return

        files = filedialog.askopenfilenames(
            title=f"Select songs for '{name}'",
            filetypes=[("MP3 files", "*.mp3")]
        )

        if not files:
            return

        playlist = {
            "name": name,
            "songs": list(files)
        }

        if "Playlists" not in settings:
            settings["Playlists"] = []
        settings["Playlists"].append(playlist)

        save_settings(settings)
        refresh_playlists()
        new_playlist_entry.delete(0, 'end')

    def find_playlist_by_name(name):
        for playlist in settings.get("Playlists", []):
            if playlist["name"] == name:
                return playlist
        return None


    add_button = ctk.CTkButton(entry_frame, text="Add", command=add_playlist, width=56, height=66)
    add_button.pack(side="left", padx=5, pady=5)


    import_button = ctk.CTkButton(entry_frame, text="Import", command=import_playlist, width=40, height=28)
    import_button.pack(side="bottom", padx=5, pady=5)

    export_button = ctk.CTkButton(
    entry_frame,
    text="Export",
    command=lambda: export_playlist(find_playlist_by_name(new_playlist_entry.get().strip())),
    width=40, 
    height=28
    )
    export_button.pack(side="right", padx=5, pady=5)
     
    
    refresh_playlists()


def load_playlist(playlist, start_index=0):
    global current_file, playing, current_playlist_songs, current_playlist_index
    global current_pos, last_update_time
    global current_folder, folder_playlist, current_folder_index

    if not playlist.get("songs"):
        messagebox.showwarning("Empty Playlist", "This playlist has no songs.")
        return

    current_playlist_songs = playlist["songs"]
    current_playlist_index = start_index
    current_file = current_playlist_songs[start_index]

    try:
        pygame.mixer.music.load(current_file)
        pygame.mixer.music.play()
        playing = True
    except Exception as e:
        print(f"Error loading song: {e}")
        return

    current_pos = 0
    last_update_time = time.time()

    update_metadata_ui(current_file)

    # Clear folder playlist mode (optional)
    current_folder = None
    folder_playlist = []
    current_folder_index = 0

    play_button.configure(text="Pause")
    update_playback_slider()

    print(f"Loaded playlist: {playlist.get('name')} from index {start_index}")





def add_rounded_corners(im, radius):
    # Create a rounded rectangle mask
    rounded_mask = Image.new('L', im.size, 0)
    draw = ImageDraw.Draw(rounded_mask)
    draw.rounded_rectangle((0, 0) + im.size, radius=radius, fill=255)
    
    # Apply mask to the image, preserving alpha
    im_rounded = im.copy()
    im_rounded.putalpha(rounded_mask)
    
    return im_rounded

#Update the metadata of the song
def update_metadata_ui(file_path):
    global song_length
    try:
        #Update the title, artist, and album
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
                # Example usage in cover art loading:
                image = Image.open(io.BytesIO(image_data)).resize((120, 120))

                # Add bezel
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

    # Update the song length and reset to 0 seconds
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

#Load an mp3 to play
def load_file():
    global current_file, playing, current_folder, folder_playlist, current_folder_index
    global current_pos, last_update_time
    global current_playlist_songs, current_playlist_index

    # Clear playlist mode on manual load
    current_playlist_songs = []
    current_playlist_index = 0

    file_path = filedialog.askopenfilename(
        filetypes=[("MP3 files", "*.mp3")],
        title="Choose an MP3 file"
    )
    if file_path:
        current_file = file_path
        pygame.mixer.music.load(current_file)
        pygame.mixer.music.play()
        playing = True

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

        update_playback_slider()

        print("Playing:", current_file)
    else:
        print("No file selected")

#obvious
def get_playback_position():
    if not playing:
        return current_pos  # Don't advance if paused
    return current_pos + (time.time() - last_update_time)


#Skip the song
def skip_song():
    global current_playlist_index, playing, current_file
    global current_folder_index
    global current_pos, last_update_time  # <- Add this

    if current_playlist_songs:
        current_playlist_index = (current_playlist_index + 1) % len(current_playlist_songs)
        next_song_path = current_playlist_songs[current_playlist_index]
    else:
        current_folder_index = (current_folder_index + 1) % len(folder_playlist)
        next_song_path = os.path.join(current_folder, folder_playlist[current_folder_index])

    pygame.mixer.music.load(next_song_path)
    pygame.mixer.music.play()
    playing = True
    current_file = next_song_path

    current_pos = 0  # Reset progress tracking
    last_update_time = time.time()

    update_metadata_ui(current_file)
    play_button.configure(text="Pause")
    update_playback_slider()



#UnSkip the song
def unskip_song():
    global current_folder_index
    global current_playlist_index, playing, current_file
    global current_pos, last_update_time  # <- Add this

    if current_playlist_songs:
        current_playlist_index = (current_playlist_index - 1) % len(current_playlist_songs)
        prev_song_path = current_playlist_songs[current_playlist_index]
    else:
        current_folder_index = (current_folder_index - 1) % len(folder_playlist)
        prev_song_path = os.path.join(current_folder, folder_playlist[current_folder_index])

    pygame.mixer.music.load(prev_song_path)
    pygame.mixer.music.play()
    playing = True
    current_file = prev_song_path

    # Reset playback info
    current_pos = 0
    last_update_time = time.time()

    # Always run these
    update_metadata_ui(current_file)
    play_button.configure(text="Pause")
    update_playback_slider()


pause_start_time = 0
total_paused_time = 0

#Pause and play song
def play_music():
    global playing, last_update_time, current_pos
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


#Obvious
def change_volume(value):
    volume = float(value) / 100
    pygame.mixer.music.set_volume(volume)
    volume_percent.configure(text=f"{int(value)}%")

#Obvious
def volume_up():
    current = volume_slider.get()
    new = min(100, current + 5)  # increase by 5%, max 100%
    volume_slider.set(new)
    change_volume(new)

#Obvious
def volume_down():
    current = volume_slider.get()
    new = max(0, current - 5)  # decrease by 5%, min 0%
    volume_slider.set(new)
    change_volume(new)

#Obvious
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

#i forgot
def seek_song(value):
    global current_pos, last_update_time
    if current_file:
        seek_time = float(value)
        pygame.mixer.music.play(start=seek_time)
        current_pos = seek_time
        last_update_time = time.time()
        if not playing:
            pygame.mixer.music.pause()
        playback_slider.set(current_pos)

#obvious
def update_playback_slider():
    if current_file and playing:
        pos = get_playback_position()
        if pos > song_length:
            pos = song_length
        playback_slider.set(pos)
        current_song_pos.configure(text=format_time(pos))
    app.after(500, update_playback_slider)

#obvious
def format_time(seconds):
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins:02}:{secs:02}"

def check_for_song_end():
    if current_file and not pygame.mixer.music.get_busy() and playing:
        skip_song()
    app.after(1000, check_for_song_end)  # Check every second



#########################################################################

#########################################################################


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

playlist_button = ctk.CTkButton(
    app,
    text="Playlists",
    width=70,
    height=30,
    command=open_playlist_window
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

mute_button = ctk.CTkButton(
    app,
    text="Mute",
    width=32,
    height=18,
    command=toggle_mute
)

settings_button = ctk.CTkButton(
    app,
    text="⚙️",
    width=18,
    height=30,
    command=open_settings_window
)



# Text
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


# Sliders
volume_slider = ctk.CTkSlider(
    app,
    from_=0,
    to=100,
    number_of_steps=100,
    command=change_volume
)
volume_slider.set(50)  # default volume 50%
pygame.mixer.music.set_volume(0.5)

playback_slider = ctk.CTkSlider(
    app,
    from_=0,
    to=100,
    number_of_steps=100,
    command=seek_song
)
#########################################################################

#########################################################################

# Find the placeholder cover art image and set it when app is opened
base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
placeholder_path = os.path.join(base_path, "cover_art_placeholder.png")

placeholder_image = Image.open(placeholder_path)
placeholder_image = placeholder_image.resize((120, 120))  # Adjust size as needed
cover_art_image = ImageTk.PhotoImage(placeholder_image)

cover_label.configure(image=cover_art_image)
cover_label.image = cover_art_image  # Prevent garbage collection

#########################################################################

# GUI Layout
play_button.grid(row=0, column=0, columnspan=4, padx=5, pady=(10,0), sticky="n")
load_button.grid(row=0, column=3, padx=10, pady=(10,0), sticky="nw")
skip_button.grid(row=0, column=1, padx=2, pady=(10,0), sticky="nw")
unskip_button.grid(row=0, column=0, padx=2, pady=(10,0), sticky="ne")
playlist_button.grid(row=0, column=2, padx=2, pady=(10,0), sticky="nw")
settings_button.grid(row=0, column=0, padx=2, pady=(10,0), sticky="nw")

song_title.grid(row=1, column=1, columnspan=3, sticky="nw", pady=(15, 0), padx=(0, 10))
song_artist.grid(row=2, column=1, columnspan=3, sticky="nw", pady=(0, 0), padx=(0, 10))
song_album.grid(row=3, column=1, columnspan=3, sticky="nw", pady=(0, 0), padx=(0, 10))

cover_label.grid(row=1, column=0, rowspan=3, padx=(10, 5), pady=(15, 2), sticky="nw")

volume_slider.grid(row=4, column=1, columnspan=2, sticky="ew", padx=(0, 10), pady=3)
playback_slider.grid(row=5, column=1, columnspan=2, sticky="ew", padx=(0, 10), pady=(0, 5))

current_song_pos.grid(row=5, column=0, sticky="ne", pady=(0, 0), padx=(10, 5))
song_duration.grid(row=5, column=3, sticky="nw", pady=(0, 0), padx=(0, 5))
volume_percent.grid(row=4, column=3, sticky="w", pady=(0, 0), padx=(0, 5))
mute_button.grid(row=4, column=0, sticky="e", pady=(0, 0), padx=(10, 5))

#########################################################################

#########################################################################

#Hotkeys

# Load, Play/Pause, Skip, and UnSkip songs
keyboard.add_hotkey('ctrl+shift+space', play_music)
keyboard.add_hotkey('ctrl+shift+right', skip_song)
keyboard.add_hotkey('ctrl+shift+left', unskip_song)
keyboard.add_hotkey('ctrl+shift+l', load_file)

# Control Volume
keyboard.add_hotkey('ctrl+shift+up', volume_up)
keyboard.add_hotkey('ctrl+shift+down', volume_down)
keyboard.add_hotkey('ctrl+shift+m', toggle_mute)

#########################################################################

check_for_song_end()

app.mainloop()