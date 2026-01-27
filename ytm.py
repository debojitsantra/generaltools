import time
import subprocess
import os
import json
import re
import requests
import socket
import random
import threading
import sys
import termios
import tty
import select
from dataclasses import dataclass
from typing import Optional, List

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.live import Live
from rich.align import Align
from ytmusicapi import YTMusic

console = Console()



class KeyboardListener:
    def __init__(self):
        self.key_pressed = None
        self.running = False
        self.thread = None
    
    def start(self):
        
        self.running = True
        self.thread = threading.Thread(target=self._listen, daemon=True)
        self.thread.start()
    
    def stop(self):
        
        self.running = False
    
    def _listen(self):
      
        try:
            
            old_settings = termios.tcgetattr(sys.stdin)
            try:
                tty.setcbreak(sys.stdin.fileno())
                while self.running:
                    if sys.stdin in select.select([sys.stdin], [], [], 0.1)[0]:
                        ch = sys.stdin.read(1)
                        
                        if ord(ch) == 23:
                            self.key_pressed = 'ctrl_w'
            finally:
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
        except:
            pass
    
    def get_key(self):
        
        key = self.key_pressed
        self.key_pressed = None
        return key



# MPV IPC Player 
class MPVPlayer:
    def __init__(self):
        self.proc: Optional[subprocess.Popen] = None
        self.sock_path: Optional[str] = None

    def play(self, url: str):
        self.stop()

        cache_dir = os.path.join(os.path.expanduser("~"), ".cache")
        os.makedirs(cache_dir, exist_ok=True)
        self.sock_path = os.path.join(cache_dir, f"mpv-sock-{os.getpid()}")

        try:
            os.remove(self.sock_path)
        except Exception:
            pass

        cmd = [
            "mpv",
            "--no-video",
            "--quiet",
            "--ytdl=yes",
            "--ytdl-format=bestaudio[ext=m4a]/bestaudio/best",
            f"--input-ipc-server={self.sock_path}",
            url,
        ]

        self.proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # wait socket
        for _ in range(60):
            if os.path.exists(self.sock_path):
                break
            time.sleep(0.05)

    def stop(self):
        if self.proc and self.proc.poll() is None:
            try:
                self.proc.terminate()
            except Exception:
                pass
        self.proc = None

        if self.sock_path:
            try:
                os.remove(self.sock_path)
            except Exception:
                pass
        self.sock_path = None

    def is_playing(self) -> bool:
        return self.proc is not None and self.proc.poll() is None

    def _send(self, payload: dict) -> Optional[dict]:
        if not self.sock_path or not os.path.exists(self.sock_path):
            return None
        try:
            s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            s.settimeout(0.5)
            s.connect(self.sock_path)
            s.sendall((json.dumps(payload) + "\n").encode("utf-8"))

            data = b""
            while True:
                chunk = s.recv(4096)
                if not chunk:
                    break
                data += chunk
                if b"\n" in data:
                    break

            s.close()
            line = data.split(b"\n", 1)[0].decode("utf-8", errors="ignore")
            return json.loads(line)
        except Exception:
            return None

    def time_pos(self) -> float:
        resp = self._send({"command": ["get_property", "time-pos"]})
        if not resp or resp.get("error") != "success":
            return 0.0
        try:
            return float(resp.get("data") or 0.0)
        except Exception:
            return 0.0

    def duration(self) -> float:
        resp = self._send({"command": ["get_property", "duration"]})
        if not resp or resp.get("error") != "success":
            return 0.0
        try:
            return float(resp.get("data") or 0.0)
        except Exception:
            return 0.0



# Lyrics Sync
@dataclass
class LrcLine:
    time: float
    text: str


class LyricsSync:
    def __init__(self):
        self.lines: List[LrcLine] = []

    def fetch_lyrics(self, track_name: str, artist_name: str, album_name: str = "") -> bool:
        # lrclib.net exact match
        try:
            console.print("[cyan]Fetching lyrics from lrclib...[/cyan]")
            url = "https://lrclib.net/api/get"
            params = {
                "track_name": track_name,
                "artist_name": artist_name,
            }
            if album_name:
                params["album_name"] = album_name
            
            r = requests.get(url, params=params, timeout=10)
            if r.status_code == 200:
                data = r.json()
                synced = data.get("syncedLyrics")
                if synced:
                    console.print("[green]✓ Found synced lyrics[/green]")
                    self.lines = self._parse_lrc(synced)
                    return len(self.lines) > 0
        except Exception as e:
            console.print(f"[yellow]lrclib failed: {e}[/yellow]")

        # Fallback: lrclib search
        try:
            console.print("[cyan]Trying lrclib search...[/cyan]")
            url = "https://lrclib.net/api/search"
            params = {
                "q": f"{artist_name} {track_name}",
            }
            
            r = requests.get(url, params=params, timeout=10)
            if r.status_code == 200:
                results = r.json()
                if results and len(results) > 0:
                    synced = results[0].get("syncedLyrics")
                    if synced:
                        console.print("[green]✓ Found via search[/green]")
                        self.lines = self._parse_lrc(synced)
                        return len(self.lines) > 0
        except Exception as e:
            console.print(f"[yellow]Search failed: {e}[/yellow]")

        console.print("[red]✗ No synced lyrics found[/red]")
        return False

    def _parse_lrc(self, synced_lyrics: str) -> List[LrcLine]:
        """Parse standard LRC format"""
        out: List[LrcLine] = []
        for line in synced_lyrics.strip().split("\n"):
            line = line.strip()
            if not line.startswith("[") or "]" not in line:
                continue

            try:
                time_str = line[1:line.index("]")]
                text = line[line.index("]") + 1 :].strip()

                # skip metadata like [ar:], [ti:]
                if not re.match(r"^\d+:\d+(\.\d+)?$", time_str):
                    continue
                if not text:
                    continue

                mm, ss = time_str.split(":", 1)
                t = int(mm) * 60 + float(ss)
                out.append(LrcLine(time=t, text=text))
            except Exception:
                continue

        out.sort(key=lambda x: x.time)
        return out

    def current_line(self, t: float) -> str:
        
        if not self.lines:
            return ""

        if t < self.lines[0].time:
            return "…"

        
        lo, hi = 0, len(self.lines) - 1
        ans = 0
        while lo <= hi:
            mid = (lo + hi) // 2
            if self.lines[mid].time <= t:
                ans = mid
                lo = mid + 1
            else:
                hi = mid - 1

        return self.lines[ans].text


# ASCII Animations
class ASCIIAnimator:
    def __init__(self):
        self.frame = 0
        self.last_time = 0
        self.beat_history = []
        self.animation_names = ['equalizer', 'wave', 'pulse', 'spectrum', 'circles', 'vortex']
        self.animations = {
            'equalizer': self._equalizer,
            'wave': self._wave,
            'pulse': self._pulse,
            'spectrum': self._spectrum,
            'circles': self._circles,
            'vortex': self._vortex,
        }
        self.current_anim_index = random.randint(0, len(self.animation_names) - 1)
        self.current_anim = self.animation_names[self.current_anim_index]
    
    def switch_animation(self):
        """Switch to next animation style"""
        self.current_anim_index = (self.current_anim_index + 1) % len(self.animation_names)
        self.current_anim = self.animation_names[self.current_anim_index]
        self.frame = 0
        return self.current_anim  
        
    def get_frame(self, time_pos: float = 0) -> str:
        
        self.frame += 1
        
        # Detect tempo changes and create dynamic beat
        time_delta = time_pos - self.last_time if self.last_time > 0 else 0
        self.last_time = time_pos
        
        # Create multiple beat frequencies for variety
        import math
        beat1 = abs(math.sin(time_pos * 2.0))  # 120 BPM
        beat2 = abs(math.sin(time_pos * 2.8))  # 168 BPM
        beat3 = abs(math.sin(time_pos * 1.5))  # 90 BPM
        
        # Combine beats 
        intensity = (beat1 * 0.5 + beat2 * 0.3 + beat3 * 0.2)
        
        # Add frame-based randomness 
        random_factor = (self.frame % 7) / 10.0
        final_intensity = min(1.0, intensity + random_factor * 0.2)
        
        return self.animations[self.current_anim](final_intensity, time_pos)
    
    def _equalizer(self, intensity: float, time_pos: float) -> str:
        """Equalizer bar """
        import math
        bars = []
        
        for i in range(16):

            freq_offset = i * 0.7
            bar_beat = abs(math.sin((time_pos * 2.5) + freq_offset))
            
           
            noise = abs(math.sin(self.frame * 0.1 + i)) * 0.3
            
            height = int(1 + 6 * (bar_beat * 0.7 + intensity * 0.3 + noise))
            bar_char = "█"
            bars.append((bar_char * height).ljust(7))
        
        lines = []
        for row in range(7, 0, -1):
            line = ""
            for bar in bars:
                if len(bar.strip()) >= row:
                    line += "█"
                else:
                    line += " "
            lines.append(line)
        return "\n".join(lines)
    
    def _wave(self, intensity: float, time_pos: float) -> str:
        """Wave pattern """
        import math
        lines = []
        
        for y in range(8):
            line = ""
            for x in range(40):
                # Create wave effect based on time and position
                wave = math.sin((x * 0.3) + (time_pos * 3) + (y * 0.5))
                wave2 = math.sin((x * 0.2) - (time_pos * 2) + (y * 0.3))
                combined = (wave + wave2) / 2
                
                # Map to characters based on intensity
                if combined > 0.6 * (1 - intensity * 0.5):
                    char = "█"
                elif combined > 0.3 * (1 - intensity * 0.5):
                    char = "▓"
                elif combined > 0:
                    char = "▒"
                elif combined > -0.3:
                    char = "░"
                else:
                    char = " "
                
                line += char
            lines.append(line)
        return "\n".join(lines)
    
    def _pulse(self, intensity: float, time_pos: float) -> str:
        """Pulsing circles"""
        import math
        
     
        pulse1 = abs(math.sin(time_pos * 2.0))
        pulse2 = abs(math.sin(time_pos * 3.0))
        
        lines = []
        center_y, center_x = 4, 20
        
        for y in range(8):
            line = ""
            for x in range(40):
                dist = math.sqrt((x - center_x) ** 2 + (y - center_y) ** 2 * 2)
                
                #  rings
                ring1 = abs(dist - (pulse1 * 15)) < 2
                ring2 = abs(dist - (pulse2 * 10)) < 1.5
                
                if ring1 or ring2:
                    if intensity > 0.7:
                        char = "●"
                    elif intensity > 0.4:
                        char = "○"
                    else:
                        char = "∘"
                else:
                    char = " "
                
                line += char
            lines.append(line)
        return "\n".join(lines)
    
    def _spectrum(self, intensity: float, time_pos: float) -> str:
        """Audio spectrum """
        import math
        spectrum = []
        
        for i in range(20):
            # Each bar represents a frequency band
            freq_response = abs(math.sin((time_pos * 2.5) + (i * 0.4)))
            noise = abs(math.sin(self.frame * 0.15 + i * 0.3)) * 0.3
            
            height = freq_response * 0.6 + intensity * 0.4 + noise
            
            if height > 0.8:
                char = "█"
            elif height > 0.6:
                char = "▓"
            elif height > 0.4:
                char = "▒"
            elif height > 0.2:
                char = "░"
            else:
                char = "·"
            
            spectrum.append(char * 2)
        
        return "\n".join([
            " ".join(spectrum[0:5]),
            " ".join(spectrum[5:10]),
            " ".join(spectrum[10:15]),
            " ".join(spectrum[15:20]),
        ])
    
    def _circles(self, intensity: float, time_pos: float) -> str:
        """Concentric circles pulsing outward"""
        import math
        
        lines = []
        center_y, center_x = 4, 20
        
        for y in range(8):
            line = ""
            for x in range(40):
                dist = math.sqrt((x - center_x) ** 2 + (y - center_y) ** 2 * 2)
                
                #  expanding circles
                circle_phase = (dist - time_pos * 5) % 8
                
                if circle_phase < 1.5 * (1 + intensity):
                    if intensity > 0.7:
                        char = "●"
                    elif intensity > 0.5:
                        char = "◉"
                    elif intensity > 0.3:
                        char = "○"
                    else:
                        char = "∘"
                else:
                    char = " "
                
                line += char
            lines.append(line)
        return "\n".join(lines)
    
    def _vortex(self, intensity: float, time_pos: float) -> str:
        """Spinning vortex effect"""
        import math
        
        lines = []
        center_y, center_x = 4, 20
        
        for y in range(8):
            line = ""
            for x in range(40):
                dx = x - center_x
                dy = (y - center_y) * 2
                
                dist = math.sqrt(dx ** 2 + dy ** 2)
                angle = math.atan2(dy, dx)
                
                # spiral pattern
                spiral = (angle + time_pos * 2 + dist * 0.3) % (math.pi * 2)
                spiral_intensity = abs(math.sin(spiral * 3))
                
                combined = spiral_intensity * (1 - dist / 30)
                
                if combined > 0.7 * (1 + intensity * 0.5):
                    char = "█"
                elif combined > 0.5:
                    char = "▓"
                elif combined > 0.3:
                    char = "▒"
                elif combined > 0.1:
                    char = "░"
                else:
                    char = " "
                
                line += char
            lines.append(line)
        return "\n".join(lines)


# Main
class YouTubeMusicPlayer:
    def __init__(self):
        try:
            
            self.ytmusic = YTMusic()
        except Exception as e:
            console.print(f"[yellow]Note: Running without authentication[/yellow]")
            console.print(f"[dim]Some playlists may not be accessible[/dim]")
          
            self.ytmusic = YTMusic()
        
        self.lyrics = LyricsSync()
        self.mpv = MPVPlayer()
        self.next_lyrics = LyricsSync()
        self.prefetch_thread = None

    def extract_playlist_id(self, url: str) -> Optional[str]:
        
        patterns = [
            r'list=([a-zA-Z0-9_-]+)',
            r'youtube\.com/playlist\?list=([a-zA-Z0-9_-]+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    def get_playlist_tracks(self, playlist_id: str) -> List[dict]:
        """Get all tracks from a playlist"""
        try:
            console.print(f"[cyan]Loading playlist...[/cyan]")
            
            
            for attempt_id in [playlist_id, playlist_id.replace('VL', ''), f"VL{playlist_id}"]:
                try:
                    playlist = self.ytmusic.get_playlist(attempt_id, limit=200)
                    tracks = playlist.get('tracks', [])
                    if tracks:
                        break
                except:
                    continue
            
            if not tracks:
                console.print("[red]Unable to load playlist directly[/red]")
                console.print("[yellow]This playlist might be private or unavailable[/yellow]")
                console.print("[cyan]Tip: Try making the playlist public or use a different playlist[/cyan]")
                return []
            
            console.print(f"[green]Found {len(tracks)} tracks in playlist[/green]")
            
            #filter
            valid_tracks = []
            for track in tracks:
                if track.get('videoId'):
                    valid_tracks.append(track)
            
            if valid_tracks:
                console.print(f"[green]{len(valid_tracks)} valid tracks ready to play[/green]")
            
            return valid_tracks
            
        except Exception as e:
            console.print(f"[red]Error: {str(e)[:100]}[/red]")
            console.print("[yellow]This playlist may be private or require authentication[/yellow]")
            console.print("[cyan]Try: 1) Search songs manually, or 2) Use a public playlist[/cyan]")
            return []

    def search_track(self, query: str):
        console.print(f"[cyan]Searching for: {query}[/cyan]")
        results = self.ytmusic.search(query, filter="songs", limit=8)
        if not results:
            console.print("[red]No results found[/red]")
            return None

        console.print("\n[green]Search Results:[/green]")
        for i, r in enumerate(results, 1):
            artist = r["artists"][0]["name"] if r.get("artists") else "Unknown"
            console.print(f"{i}. {r['title']} - {artist}")

        choice = input("\nSelect track number: ").strip()
        if not choice.isdigit():
            return None

        idx = int(choice) - 1
        if 0 <= idx < len(results):
            return results[idx]
        return None

    def prefetch_next_lyrics(self, track: dict):

        def fetch():
            title = track.get("title", "Unknown")
            artist = track["artists"][0]["name"] if track.get("artists") else "Unknown"
            album = track.get("album", {}).get("name", "") if track.get("album") else ""
            self.next_lyrics.fetch_lyrics(title, artist, album)
        
        self.prefetch_thread = threading.Thread(target=fetch, daemon=True)
        self.prefetch_thread.start()

    def play_track(self, track: dict, playlist_mode: bool = False, track_num: int = 0, total_tracks: int = 0, next_track: Optional[dict] = None):
        title = track.get("title", "Unknown")
        artist = track["artists"][0]["name"] if track.get("artists") else "Unknown"
        album = track.get("album", {}).get("name", "") if track.get("album") else ""
        video_id = track.get("videoId")

        if not video_id:
            console.print("[red]No videoId found for this track.[/red]")
            return False

        url = f"https://www.youtube.com/watch?v={video_id}"

        console.clear()
        if playlist_mode:
            console.print(f"[bold green]Now Playing ({track_num}/{total_tracks}):[/bold green] {title} - {artist}\n")
        else:
            console.print(f"[bold green]Now Playing:[/bold green] {title} - {artist}\n")

        has_lyrics = self.lyrics.fetch_lyrics(title, artist, album)
        
        if has_lyrics:
            console.print(f"[green]Loaded {len(self.lyrics.lines)} lyric lines[/green]\n")
        else:
            console.print("[yellow]Playing without lyrics - showing animation[/yellow]\n")


        if next_track:
            console.print("[dim]Prefetching next track's lyrics...[/dim]\n")
            self.prefetch_next_lyrics(next_track)

        self.mpv.play(url)
        console.print("[dim]Press Ctrl+C to stop | Ctrl+W to change animation[/dim]\n")

        animator = ASCIIAnimator() if not has_lyrics else None
        keyboard = KeyboardListener()
        keyboard.start()
        user_stopped = False

        try:
            with Live(console=console, refresh_per_second=20, screen=True) as live:
                while self.mpv.is_playing():
                    t = self.mpv.time_pos()
                    

                    if not has_lyrics and animator:
                        key = keyboard.get_key()
                        if key == 'ctrl_w':
                            new_anim = animator.switch_animation()

                            console.print(f"[cyan]Switched to: {new_anim}[/cyan]")
                    
                    if has_lyrics:
                        current = self.lyrics.current_line(t)
                        content = Text(current, style="bold white")
                    else:

                        anim_text = animator.get_frame(t)
                        content = Text(anim_text, style="cyan")
                    
                    title_text = f"{title} - {artist}"
                    if playlist_mode:
                        title_text += f" ({track_num}/{total_tracks})"
                    
                    panel = Panel(
                        Align.center(content, vertical="middle"),
                        title=title_text,
                        border_style="cyan",
                        height=12,
                    )
                    live.update(panel)
                    time.sleep(0.05)
        except KeyboardInterrupt:
            user_stopped = True
            console.print("\n[yellow]Stopped by user[/yellow]")
        finally:
            keyboard.stop()
            self.mpv.stop()
        
        return user_stopped  

    def play_playlist(self, tracks: List[dict]):
        """Play all tracks in a playlist"""
        total = len(tracks)
        for i, track in enumerate(tracks, 1):

            next_track = tracks[i] if i < total else None
            
            console.print(f"\n[bold cyan]Track {i}/{total}[/bold cyan]")
            user_stopped = self.play_track(track, playlist_mode=True, track_num=i, total_tracks=total, next_track=next_track)
            

            if user_stopped:
                console.print("[yellow]Playlist stopped. Returning to search...[/yellow]")
                return
            
            
            if next_track:
                self.lyrics = self.next_lyrics
                self.next_lyrics = LyricsSync()
          
            if i < total:
                time.sleep(1)  
        
        console.print("\n[green]✓ Playlist finished![/green]")


def main():
    console.print(
        Panel.fit(
            "[bold cyan]YouTube Music Player[/bold cyan]\n[dim]by deb[/dim]",
            border_style="green",
        )
    )

    player = YouTubeMusicPlayer()

    while True:
        try:
            q = input("\n🎵 Search or paste playlist URL (or 'q' to quit): ").strip()
            if q.lower() == "q":
                break
            if not q:
                continue

            # Check if it's a playlist URL
            playlist_id = player.extract_playlist_id(q)
            if playlist_id:
                tracks = player.get_playlist_tracks(playlist_id)
                if tracks:
                    player.play_playlist(tracks)
            else:
                # Regular search
                track = player.search_track(q)
                if track:
                    player.play_track(track)

        except KeyboardInterrupt:
            console.print("\n[yellow]Goodbye![/yellow]")
            break
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")


if __name__ == "__main__":
    main()
