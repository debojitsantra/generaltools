###  Playlist Support
- Paste YouTube Music playlist URLs to play entire playlists
- Automatic track progression
- Background lyrics prefetching for seamless transitions
- Track counter (e.g., "Track 3/15")

###  Keyboard Controls
- **Ctrl+C** - Stop playback and return to search
- **Ctrl+W** - Cycle through visualizations (when no lyrics)

##  Installation

### Step 1: Install System Dependencies

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install mpv python3-pip
```

**macOS:**
```bash
brew install mpv python3
```

**Arch Linux:**
```bash
sudo pacman -S mpv python
```

### Step 2: Install Python Dependencies

```bash
pip install ytmusicapi rich requests
```

### Step 3: Download the Player

```bash
wget https://raw.githubusercontent.com/debojitsantra/generaltools/refs/heads/main/ytm.py
chmod +x yt.py
```

##  Usage

### Basic Usage

Run the player:
```bash
python3 yt.py
```






### Controls During Playback

| Key | Action |
|-----|--------|
| `Ctrl+C` | Stop current song/playlist and return to search |
| `Ctrl+W` | Switch visualization (only without lyrics) |
| `q` | Quit application (at search prompt) |













### Authentication (Optional)



```bash

ytmusicapi oauth


```

This creates `oauth.json` in your current directory.




##  API Credits

- **YouTube Music**: [ytmusicapi](https://github.com/sigma67/ytmusicapi)
- **Lyrics**: [lrclib.net](https://lrclib.net)
- **Media Player**: [MPV](https://mpv.io)
- **UI**: [Rich](https://github.com/Textualize/rich)

