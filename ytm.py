#*requirements*
'''
sudo apt update
sudo apt install mpv python
pip install -U ytmusicapi rich requests
'''


import time
import subprocess
import os
import json
import re
import requests
import socket
from dataclasses import dataclass
from typing import Optional, List

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.live import Live
from rich.align import Align
from ytmusicapi import YTMusic

console = Console()



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



# Lyrics Sync
@dataclass
class LrcLine:
    time: float
    text: str


class LyricsSync:
    def __init__(self):
        self.lines: List[LrcLine] = []

    def fetch_lyrics(self, track_name: str, artist_name: str, album_name: str = "") -> bool:
        
        try:
            url = "https://api.lyrics.boidu.dev/lyrics"
            params = {
                "track_name": track_name,
                "artist_name": artist_name,
                "album_name": album_name,
            }
            console.print("[cyan]Fetching lyrics [/cyan]")
            r = requests.get(url, params=params, timeout=10)
            if r.status_code == 200:
                data = r.json()
                synced = data.get("syncedLyrics")
                if synced:
                    console.print("[green]✓ Found [/green]")
                    self.lines = self._parse_lrc(synced)
                    return len(self.lines) > 0
        except Exception as e:
            console.print(f"[yellow]Failed: {e}[/yellow]")

      
        try:
            console.print("[cyan]Trying fallback...[/cyan]")
            url = "https://lrclib.net/api/get"
            params = {
                "track_name": track_name,
                "artist_name": artist_name,
                "album_name": album_name,
            }
            r = requests.get(url, params=params, timeout=10)
            if r.status_code == 200:
                data = r.json()
                synced = data.get("syncedLyrics")
                if synced:
                    console.print("[green]✓ Found [/green]")
                    self.lines = self._parse_lrc(synced)
                    return len(self.lines) > 0
        except Exception as e:
            console.print(f"[red]fallback failed: {e}[/red]")

        return False

    def _parse_lrc(self, synced_lyrics: str) -> List[LrcLine]:
        out: List[LrcLine] = []
        for line in synced_lyrics.strip().split("\n"):
            line = line.strip()
            if not line.startswith("[") or "]" not in line:
                continue

            try:
                time_str = line[1:line.index("]")]
                text = line[line.index("]") + 1 :].strip()

                
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
            return "No lyrics"

        
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



# Main
class YouTubeMusicPlayer:
    def __init__(self):
        self.ytmusic = YTMusic()
        self.lyrics = LyricsSync()
        self.mpv = MPVPlayer()

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

    def play_track(self, track: dict):
        title = track.get("title", "Unknown")
        artist = track["artists"][0]["name"] if track.get("artists") else "Unknown"
        album = track.get("album", {}).get("name", "") if track.get("album") else ""
        video_id = track.get("videoId")

        if not video_id:
            console.print("[red]No videoId found for this track.[/red]")
            return

        url = f"https://www.youtube.com/watch?v={video_id}"

        console.clear()
        console.print(f"[bold green]Now Playing:[/bold green] {title} - {artist}\n")

        ok = self.lyrics.fetch_lyrics(title, artist, album)
        if ok:
            console.print(f"[green]Loaded {len(self.lyrics.lines)} lyric lines[/green]\n")
        else:
            console.print("[yellow]No synced lyrics found[/yellow]\n")

        self.mpv.play(url)
        console.print("[dim]Press Ctrl+C to stop[/dim]\n")

        try:
            with Live(console=console, refresh_per_second=20, screen=True) as live:
                while self.mpv.is_playing():
                    t = self.mpv.time_pos()
                    line = self.lyrics.current_line(t) if ok else "No lyrics"
                    panel = Panel(
                        Align.center(Text(line, style="bold white"), vertical="middle"),
                        title=f"{title} - {artist}",
                        border_style="cyan",
                        height=9,
                    )
                    live.update(panel)
                    time.sleep(0.05)
        except KeyboardInterrupt:
            pass
        finally:
            self.mpv.stop()
            console.print("\n[yellow]Stopped[/yellow]")


def main():
    console.print(
        Panel.fit(
            "[bold cyan]Player[/bold cyan]\n[dim]by deb[/dim]",
            border_style="green",
        )
    )

    player = YouTubeMusicPlayer()

    while True:
        try:
            q = input("\n🎵 Search (or 'q' quit): ").strip()
            if q.lower() == "q":
                break
            if not q:
                continue

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
