\# Music Player 🎵



A lightweight (and very simple) local MP3 player built with Python and customtkinter.



\## Features



\- Play, pause, skip MP3 songs

\- Volume control

\- Cover art support (with default placeholder)

\- Playlist (Creation and Deletion) support

\- Custom Themes

(Credits to themes provided by a13xe's CTkThemesPack)


\- Global hotkeys:

&nbsp; - `Ctrl + Shift + Space`: Play/Pause

&nbsp; - `Ctrl + Shift + →`: Skip to next song

&nbsp; - `Ctrl + Shift + ←`: UnSkip to previous song

&nbsp; - `Ctrl + Shift + ↑ / ↓`: Volume up/down

&nbsp; - `Ctrl + Shift + M`: Mute song

&nbsp; - `Ctrl + Shift + L`: Load an Mp3


\## How to use:

\* Load a song either by clicking on `Load File` or `Playlist` and creating a new playlist

\* Play the song by using the buttons at the top and the sliders on the bottom

\* The `UnSkip`, `Skip`, and `Pause/Play` buttons are pretty obvious

\* The first slider is a volume slider to control the sound

\* The second slider is a progress bar to move throughout the song or see where the song currently is

\## To use playlists:

\* First, create a playlist by clicking on the `Playlist` button and then entering a name at the bottom
\* Then, click on `Add` to select what MP3 files you would like to add to the playlist
\* Secondly, to play a playlist, click on its title in the window above
\* To delete a playlist, Right-Click on its title and confirm

\## To change the app theme:

\* First, open the settings by clicking on the gear icon in the corner
\* Secondly, select a theme in the dropdown menu
\* To apply and save, click on `Save Settings`
\* Lastly, Restart the app and your changes should be applied

\## Requirements


\- Python 3.10+

\- `pygame`

\- `customtkinter`

\- `keyboard`

\- `mutagen`



\## Setup



Install dependencies:



```bash

pip install pygame customtkinter keyboard mutagen