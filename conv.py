import os
import subprocess
import re
import sys
import time

AUDIO_EXT = [".mp3", ".flac", ".wav", ".m4a"]
VIDEO_EXT = [".mp4", ".mkv", ".webm"]

def choose_aspect_ratio():
    print("Choose Aspect Ratio:")
    print("1 = 16:9 (1920x1080)")
    print("2 = 9:16 (1080x1920)")
    choice = input("Enter choice (1 or 2): ").strip()
    if choice == "1":
        return "1920x1080"
    elif choice == "2":
        return "1080x1920"
    else:
        raise ValueError("Invalid choice (must be 1 or 2).")

def choose_visualization(resolution, inpu, out, ab):
    print("\nChoose Visualization Style:")
    print("1 = Line Waveform")
    print("2 = Continuous Line")
    print("3 = Point-to-Point")
    print("4 = Bar")
    print("5 = Spectrogram")
    print("6 = Spectrum + Waveform Overlay")
    choice = input("Enter choice (1-6): ").strip()

    color = input("Enter wave/spectrum color (def=white): ").strip() or "white"

    if choice == "1":
        return f'ffmpeg -i "{inpu}" -filter_complex "[0:a]showwaves=s={resolution}:mode=line:rate=25:colors={color}[vid]" -map "[vid]" -map 0:a -c:v libx264 -c:a aac -b:a {ab} -shortest "{out}"'
    elif choice == "2":
        return f'ffmpeg -i "{inpu}" -filter_complex "[0:a]showwaves=s={resolution}:mode=cline:rate=25:colors={color}[vid]" -map "[vid]" -map 0:a -c:v libx264 -c:a aac -b:a {ab} -shortest "{out}"'
    elif choice == "3":
        return f'ffmpeg -i "{inpu}" -filter_complex "[0:a]showwaves=s={resolution}:mode=p2p:rate=25:colors={color}[vid]" -map "[vid]" -map 0:a -c:v libx264 -c:a aac -b:a {ab} -shortest "{out}"'
    elif choice == "4":
        return f'ffmpeg -i "{inpu}" -filter_complex "[0:a]showwaves=s={resolution}:mode=bar:rate=25:colors={color}[vid]" -map "[vid]" -map 0:a -c:v libx264 -c:a aac -b:a {ab} -shortest "{out}"'
    elif choice == "5":
        return f'ffmpeg -i "{inpu}" -filter_complex "[0:a]showspectrum=s={resolution}:mode=combined:color=fire:scale=log[vid]" -map "[vid]" -map 0:a -c:v libx264 -c:a aac -b:a {ab} -shortest "{out}"'
    elif choice == "6":
        return f'ffmpeg -i "{inpu}" -filter_complex "[0:a]showspectrum=s={resolution}:mode=combined:color=fire:scale=log[spec];[0:a]showwaves=s={resolution}:mode=cline:rate=25:colors={color}[waves];[spec][waves]overlay=0:0[vid]" -map "[vid]" -map 0:a -c:v libx264 -c:a aac -b:a {ab} -shortest "{out}"'
    else:
        raise ValueError("Invalid choice (must be 1-6).")

def get_duration(input_file):
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", 
         "-of", "default=noprint_wrappers=1:nokey=1", input_file],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    try:
        return float(result.stdout.strip())
    except:
        return None

def run_with_progress(command, input_file):
    total_duration = get_duration(input_file)
    if not total_duration:
        print("Could not determine duration. Running without progress bar...")
        subprocess.run(command, shell=True)
        return

    process = subprocess.Popen(command, shell=True, stderr=subprocess.PIPE, text=True, bufsize=1)
    time_pattern = re.compile(r"time=(\d+:\d+:\d+\.\d+)")

    def hms_to_sec(hms):
        h, m, s = hms.split(":")
        return int(h) * 3600 + int(m) * 60 + float(s)

    for line in process.stderr:
        match = time_pattern.search(line)
        if match:
            current_time = hms_to_sec(match.group(1))
            progress = min(current_time / total_duration, 1.0)
            bar_len = 40
            filled = int(bar_len * progress)
            bar = "█" * filled + "-" * (bar_len - filled)
            sys.stdout.write(f"\r[{bar}] {progress*100:5.1f}%")
            sys.stdout.flush()

    process.wait()
    print("\n ✓ Done!")

def main():
    inpu = input("Enter input file path: ").strip()

    if not os.path.exists(inpu):
        raise FileNotFoundError("Input file does not exist.")
   
    name, ext = os.path.splitext(inpu)  
    ab = input("Enter Bitrate (def: 320k): ").strip() or "320k"
    exta = input("Enter Output Extension (e.g. mp4/mp3): ").strip().lower() or "mp4"
    out = name + "." + exta

    # AUDIO INPUT
    if ext.lower() in AUDIO_EXT:
        if_video = input("Convert to Video? (y/n): ").strip().lower()
        if if_video == "y":
            resolution = choose_aspect_ratio()
            if exta not in VIDEO_EXT:
                exta = "mp4"
                out = name + "." + exta

            wave = input("Add Waveform/Spectrum? (y/n): ").strip().lower()
            if wave == "y":
                comm = choose_visualization(resolution, inpu, out, ab)
            else:
                bg_choice = input("Use background image? (y/n): ").strip().lower()
                if bg_choice == "y":
                    bg = input("Enter background image path: ").strip()
                    comm = f'ffmpeg -loop 1 -i "{bg}" -i "{inpu}" -c:v libx264 -c:a aac -b:a {ab} -shortest -s {resolution} "{out}"'
                else:
                    comm = f'ffmpeg -f lavfi -i color=c=black:s={resolution} -i "{inpu}" -c:v libx264 -c:a aac -b:a {ab} -shortest "{out}"'
        else:
            comm = f'ffmpeg -i "{inpu}" -vn -ab {ab} "{out}"'

    # VIDEO INPUT
    elif ext.lower() in VIDEO_EXT:
        action = input("Choose action: \n1 = Extract Audio \n2 = Re-encode Video \nEnter choice: ").strip()
        if action == "1":
            comm = f'ffmpeg -i "{inpu}" -vn -ab {ab} "{out}"'
        elif action == "2":
            resolution = choose_aspect_ratio()
            comm = f'ffmpeg -i "{inpu}" -vf scale={resolution} -c:v libx264 -c:a aac -b:a {ab} "{out}"'
        else:
            raise ValueError("Invalid choice (must be 1 or 2).")

    else:
        raise ValueError("Unsupported input file type.")

    print("\nRunning command with progress bar...\n")
    run_with_progress(comm, inpu)

if __name__ == "__main__":
    main()
