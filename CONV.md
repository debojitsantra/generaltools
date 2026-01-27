
# Audio/Video Converter with Visualization: CONV

A powerful Python CLI tool that wraps FFmpeg to convert audio and video files with stunning visualizations and real-time progress tracking.

![Python Version](https://img.shields.io/badge/python-3.6+-blue.svg)
![FFmpeg Required](https://img.shields.io/badge/ffmpeg-required-red.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## ✨ Features

- 🎵 **Audio to Video** - Convert audio files to video with visualizations
- 🎬 **Video Processing** - Extract audio or re-encode videos
- 📊 **6 Visualization Styles** - Waveforms, spectrograms, and more
- 📈 **Real-time Progress Bar** - Track conversion progress
- 🎨 **Customizable Colors** - Choose your visualization colors
- 📐 **Multiple Aspect Ratios** - 16:9 and 9:16 support
- 🔊 **Adjustable Bitrate** - Control audio quality

## 🚀 Quick Start

```bash
# Get the file
wget https://raw.githubusercontent.com/debojitsantra/generaltools/refs/heads/main/conv.py

# Run the script
python conv.py
```

## 📋 Prerequisites

### Required Software

1. **Python 3.6 or higher**
   ```bash
   python --version
   ```

2. **FFmpeg** (with FFprobe)
   
   **Windows:**
   ```bash
   choco install ffmpeg
   ```
   
   **macOS:**
   ```bash
   brew install ffmpeg
   ```
   
   **Linux (Ubuntu/Debian):**
   ```bash
   sudo apt update
   sudo apt install ffmpeg
   ```

Verify installation:
```bash
ffmpeg -version
ffprobe -version
```

## 🎯 Usage Examples

### Convert Audio to Video with Waveform

```
$ python conv.py

Enter input file path: music.mp3
Enter Bitrate (def: 320k): 320k
Enter Output Extension (e.g. mp4/mp3): mp4
Convert to Video? (y/n): y

Choose Aspect Ratio:
1 = 16:9 (1920x1080)
2 = 9:16 (1080x1920)
Enter choice (1 or 2): 1

Add Waveform/Spectrum? (y/n): y

Choose Visualization Style:
1 = Line Waveform
2 = Continuous Line
3 = Point-to-Point
4 = Bar
5 = Spectrogram
6 = Spectrum + Waveform Overlay
Enter choice (1-6): 1

Enter wave/spectrum color (def=white): cyan

Running command with progress bar...
[████████████████████████████████████████] 100.0%
 ✓ Done!
```

### Extract Audio from Video

```
$ python conv.py

Enter input file path: video.mp4
Enter Bitrate (def: 320k): 192k
Enter Output Extension (e.g. mp4/mp3): mp3

Choose action:
1 = Extract Audio
2 = Re-encode Video
Enter choice: 1

Running command with progress bar...
[████████████████████████████████████████] 100.0%
 ✓ Done!
```

### Convert Audio with Custom Background

```
Enter input file path: song.wav
Enter Bitrate (def: 320k): 256k
Enter Output Extension (e.g. mp4/mp3): mp4
Convert to Video? (y/n): y

Choose Aspect Ratio:
1 = 16:9 (1920x1080)
2 = 9:16 (1080x1920)
Enter choice (1 or 2): 2

Add Waveform/Spectrum? (y/n): n
Use background image? (y/n): y
Enter background image path: background.jpg

Running command with progress bar...
[████████████████████████████████████████] 100.0%
 ✓ Done!
```

## 🎨 Visualization Styles

| Style | Description | Best For |
|-------|-------------|----------|
| **Line Waveform** | Classic oscilloscope view | General purpose, clear representation |
| **Continuous Line** | Smooth flowing waveform | Smooth, organic feel |
| **Point-to-Point** | Connected dots visualization | Modern, geometric aesthetic |
| **Bar** | Vertical bar graph | Bold, impactful visuals |
| **Spectrogram** | Frequency spectrum over time | Detailed frequency analysis |
| **Spectrum + Waveform** | Combined overlay | Maximum visual information |

### Color Options

Choose from any FFmpeg-supported color:
- `white` (default)
- `red`, `blue`, `green`, `cyan`, `magenta`, `yellow`
- `orange`, `purple`, `pink`, `lime`
- Hex codes: `0xFF5733`

## 📁 Supported Formats

### Input Formats

| Type | Extensions |
|------|-----------|
| **Audio** | `.mp3`, `.flac`, `.wav`, `.m4a` |
| **Video** | `.mp4`, `.mkv`, `.webm` |

### Output Formats

Any format supported by your FFmpeg installation, including:
- Video: `mp4`, `mkv`, `webm`, `avi`, `mov`
- Audio: `mp3`, `flac`, `wav`, `m4a`, `ogg`, `aac`

## ⚙️ Configuration

### Bitrate Settings

| Bitrate | Quality | Use Case |
|---------|---------|----------|
| `128k` | Standard | Voice, podcasts |
| `192k` | Good | Most music |
| `256k` | High | High-quality music |
| `320k` | Very High | Audiophile, archival |

### Aspect Ratios

- **16:9 (1920×1080)** - YouTube, standard video, widescreen
- **9:16 (1080×1920)** - TikTok, Instagram Stories, vertical video

## 🔧 Advanced Usage

### Using as a Module

```python
from conv import get_duration, run_with_progress

# Get media file duration
duration = get_duration("input.mp3")
print(f"Duration: {duration} seconds")

# Run FFmpeg with progress tracking
command = 'ffmpeg -i "input.mp3" -vn -ab 320k "output.mp3"'
run_with_progress(command, "input.mp3")
```

### Batch Processing

Create a batch script:

```python
from pathlib import Path
from conv import run_with_progress

audio_files = sorted(Path('.').glob('*.mp3'))

for audio in audio_files:
    output = audio.with_suffix('.mp4')

    cmd = [
        'ffmpeg',
        '-y',
        '-i', str(audio),
        '-filter_complex',
        'showwaves=s=1280x720:mode=line:rate=25:colors=white',
        '-map', '0:a',
        '-map', '0:v',
        '-c:v', 'libx264',
        '-pix_fmt', 'yuv420p',
        '-c:a', 'aac',
        '-b:a', '320k',
        '-shortest',
        str(output)
    ]

    run_with_progress(cmd, audio.name)
```

## 🐛 Troubleshooting

### FFmpeg Not Found

**Error:** `'ffmpeg' is not recognized as an internal or external command`

**Solution:**
1. Install FFmpeg (see Prerequisites)
2. Add FFmpeg to system PATH
3. Restart terminal/command prompt

### No Progress Bar Displayed

**Cause:** File lacks duration metadata

**Solution:** Conversion still proceeds, just without progress indication

### Slow Conversion Speed

**Causes:**
- Large file size
- High resolution output
- CPU-intensive encoding

**Solutions:**
- Use hardware acceleration: `-c:v h264_nvenc` (NVIDIA) or `-c:v h264_videotoolbox` (macOS)
- Reduce output resolution
- Use faster preset: `-preset ultrafast`

### Output File is Too Large

**Solutions:**
- Lower bitrate: use `128k` or `192k`
- Use more compression: `-crf 23` (lower = better quality, higher = smaller file)
- Change format: use `webm` instead of `mp4`

## 📊 Performance Tips

- **Faster encoding:** Use `-preset ultrafast` (lower quality)
- **Better quality:** Use `-preset slow` (slower encoding)
- **Smaller files:** Adjust CRF value (18-28 recommended)
- **Hardware acceleration:** Use GPU encoding if available

## 🤝 Contributing

Contributions are welcome! 

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [FFmpeg](https://ffmpeg.org/) - the leading multimedia framework
- Inspired by the need for easy audio visualization
- Thanks to all contributors and users

## 📞 Support

- **Issues:** [GitHub Issues](https://github.com/debojitsantra/generaltools/issues)

## 🗺️ Roadmap

- [ ] v1.1 - Add batch processing mode
- [ ] v1.2 - Implement GUI interface
- [ ] v1.3 - Hardware acceleration support
- [ ] v2.0 - Plugin system for custom visualizations

---


**Star ⭐ this repository if you find it helpful!**

- This documentation is created with the help of claude

