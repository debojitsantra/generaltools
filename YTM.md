# 🎵 YouTube Music Player with Synced Lyrics: YTM

A beautiful terminal-based music player for YouTube Music with real-time synced lyrics and mesmerizing ASCII visualizations.

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.8+-green)
![License](https://img.shields.io/badge/license-MIT-orange)

## ✨ Features

### 🎤 Lyrics Display
- **Real-time synced lyrics** from lrclib.net
- Clean, centered display showing current line
- Automatic fallback to search when exact match fails
- Shows "…" before lyrics start

### 🎨 Music Visualizations
When lyrics aren't available, enjoy 6 different music-reactive ASCII animations:
- **Equalizer** - Bouncing bars simulating frequency response
- **Wave** - Flowing 2D sine wave patterns
- **Pulse** - Expanding concentric circles
- **Spectrum** - Audio frequency spectrum visualization
- **Circles** - Radiating ripple effects
- **Vortex** - Spinning spiral patterns

All visualizations react to music playback time for synchronized motion!

### 📋 Playlist Support
- Paste YouTube Music playlist URLs to play entire playlists
- Automatic track progression
- Background lyrics prefetching for seamless transitions
- Track counter (e.g., "Track 3/15")

### ⌨️ Keyboard Controls
- **Ctrl+C** - Stop playback and return to search
- **Ctrl+W** - Cycle through visualizations (when no lyrics)

### 🔍 Smart Search
- Search by song name, artist, or both
- Shows up to 8 results with artist information
- Easy numeric selection

## 📦 Installation

### Requirements
- Python 3.8 or higher
- MPV media player
- Terminal with Unicode support

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

## 🚀 Usage

### Basic Usage

Run the player:
```bash
python3 yt.py
```

### Search for Songs

At the prompt, enter a search query:
```
🎵 Search or paste playlist URL (or 'q' to quit): shape of you ed sheeran
```

Select a track from the results:
```
Search Results:
1. Shape of You - Ed Sheeran
2. Shape of You (Acoustic) - Ed Sheeran
...

Select track number: 1
```

### Play Playlists

Paste a YouTube Music playlist URL:
```
🎵 Search or paste playlist URL (or 'q' to quit): https://music.youtube.com/playlist?list=PLxxxxxx
```

The player will:
1. Load all tracks from the playlist
2. Play them sequentially
3. Prefetch lyrics for the next track while current plays
4. Show progress (e.g., "Track 5/20")

### Controls During Playback

| Key | Action |
|-----|--------|
| `Ctrl+C` | Stop current song/playlist and return to search |
| `Ctrl+W` | Switch visualization (only without lyrics) |
| `q` | Quit application (at search prompt) |

## 🎨 Visualizations Explained

### Equalizer
```
████████████████
█ █ ██ █ ███ █ █
  █  █ █  ██ █  
```
16 vertical bars bouncing with different frequency responses, creating a classic audio equalizer effect.

### Wave
```
░▒▓█████▓▒░░▒▓█
▒▓█████▓▒░░▒▓██
▓█████▓▒░░▒▓███
```
2D sine wave patterns flowing across the screen, speed varies with music intensity.

### Pulse
```
     ○○○○○
   ○○     ○○
     ○○○○○
```
Multiple concentric rings expanding from the center at different rates.

### Spectrum
```
█ ▓ ░ ▒ █ ▓ ░
▓ ░ ▒ █ ▓ ░ ▒
```
Frequency band visualization with 20 channels using different block characters.

### Circles
```
  ∘ ○ ◉ ○ ∘
 ○ ◉ ● ◉ ○ 
  ∘ ○ ◉ ○ ∘
```
Expanding ripples radiating outward from center point.

### Vortex
```
░▒▓█  █▓▒░
▒▓█    █▓▒
▓█      █▓
```
Spinning spiral pattern rotating with music tempo.

## 🎯 How It Works

### Architecture

```
┌─────────────┐
│   Search    │
│   (YTMusic) │
└──────┬──────┘
       │
       ▼
┌─────────────┐     ┌──────────────┐
│  MPV Player │────▶│   Display    │
│  (Audio)    │     │  (Rich UI)   │
└──────┬──────┘     └──────────────┘
       │
       ▼
┌─────────────┐
│   Lyrics    │
│  (lrclib)   │
└─────────────┘
```

### Components

1. **YTMusic API**: Searches YouTube Music and retrieves track information
2. **MPV Player**: Handles audio playback via IPC socket communication
3. **Lyrics Sync**: Fetches synced lyrics from lrclib.net API
4. **ASCII Animator**: Generates music-reactive visualizations
5. **Rich UI**: Displays everything in a beautiful terminal interface
6. **Keyboard Listener**: Non-blocking background thread for key detection

### Music Synchronization

Animations sync to music using:
- **Multiple beat frequencies** (120 BPM, 168 BPM, 90 BPM combined)
- **Time-based trigonometry** using current playback position
- **Per-element variation** simulating real frequency response
- **Controlled randomness** for organic, lively motion

## 🔧 Configuration

### Lyrics API

The player uses lrclib.net for lyrics. No API key required!

**Lyrics search strategy:**
1. Exact match (track + artist + album)
2. Search query (track + artist)
3. Show animations if not found

### MPV Settings

MPV is configured for:
- No video output (`--no-video`)
- Best audio quality (`bestaudio[ext=m4a]/bestaudio/best`)
- IPC control via Unix socket

## 🐛 Troubleshooting

### "No results found"
- Check your internet connection
- Try different search terms
- Try searching with both song and artist name

### "Unable to load playlist"
- Playlist may be private - make it public
- Some playlists require authentication
- Try individual song searches instead

### MPV not found
```bash
# Check if mpv is installed
which mpv

# If not, install it
# Ubuntu/Debian:
sudo apt install mpv

# macOS:
brew install mpv
```

### Lyrics not syncing
- Some songs don't have synced lyrics available
- Enjoy the visualizations instead!
- Lyrics database updates regularly

### Terminal display issues
- Ensure your terminal supports Unicode
- Try a different terminal emulator (iTerm2, Alacritty, etc.)
- Increase terminal size for better visualization display

### Ctrl+W not working
- Some terminals intercept Ctrl+W (close tab)
- Try a different terminal
- Alternative: Use different visualization by restarting the song

## 🎓 Advanced Usage

### Authentication (Optional)

For better playlist access:

```bash
# Setup OAuth authentication
ytmusicapi oauth

# Follow the prompts to authenticate
```

This creates `oauth.json` in your current directory, allowing access to:
- Private playlists
- Your library
- Liked songs

### Custom Terminal Setup

For best experience:
- **Font**: Use a monospace font with good Unicode support
- **Size**: At least 80x30 characters
- **Colors**: 256-color or true color support recommended
- **Theme**: Dark backgrounds work best

### Batch Operations

Create a playlist file and auto-play:
```bash
# songs.txt
shape of you
perfect
photograph

# Play all songs
while IFS= read -r song; do
    echo "$song" | python3 yt.py
done < songs.txt
```

## 📊 Performance

- **Memory**: ~50-100MB typical usage
- **CPU**: Low (~5-10% on modern systems)
- **Network**: Streams audio + downloads lyrics (~3-5 MB/song)

## 🤝 Contributing

Contributions welcome! Areas for improvement:

- Additional visualization styles
- More lyrics sources
- Spotify integration
- Local file support
- EQ/audio processing
- Custom themes

## 📝 API Credits

- **YouTube Music**: [ytmusicapi](https://github.com/sigma67/ytmusicapi)
- **Lyrics**: [lrclib.net](https://lrclib.net)
- **Media Player**: [MPV](https://mpv.io)
- **UI**: [Rich](https://github.com/Textualize/rich)

## ⚖️ License

MIT License - See LICENSE file for details

## 🙏 Acknowledgments

- Inspired by terminal music players like cmus, ncmpcpp
- Visualization algorithms inspired by classic audio visualizers

## 📧 Support

Having issues? Try:
1. Check the troubleshooting section above
2. Make sure all dependencies are installed
3. Test MPV separately: `mpv https://www.youtube.com/watch?v=dQw4w9WgXcQ`
4. Check your Python version: `python3 --version`

---

**Enjoy your music! 🎵✨**

Made with ❤️ for music lovers who appreciate the terminal aesthetic.

- This Documentation is created with the help of Claude
