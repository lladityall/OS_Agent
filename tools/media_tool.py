#!/usr/bin/env python3
"""
RAM Tool: Multimedia Capture
Take pictures, record video, create time-lapse sequences using webcam.
"""

import subprocess
import os
import time
from pathlib import Path
from datetime import datetime


CAPTURE_DIR = Path.home() / "RAM_media"
CAPTURE_DIR.mkdir(exist_ok=True)


def _timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def take_picture(
    output_path: Optional[str] = None,
    device: str = "/dev/video0",
    delay: int = 1,
) -> dict:
    """Capture a still image from the webcam"""
    if output_path is None:
        output_path = str(CAPTURE_DIR / f"photo_{_timestamp()}.jpg")

    try:
        # Try fswebcam first
        result = subprocess.run(
            ["fswebcam", "-d", device, "-r", "1280x720",
             "--no-banner", f"--delay={delay}", output_path],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode == 0 and Path(output_path).exists():
            return {"success": True, "path": output_path, "tool": "fswebcam"}

        # Fallback: ffmpeg
        result2 = subprocess.run(
            ["ffmpeg", "-y", "-f", "v4l2", "-i", device,
             "-vframes", "1", output_path],
            capture_output=True, text=True, timeout=15
        )
        if result2.returncode == 0:
            return {"success": True, "path": output_path, "tool": "ffmpeg"}

        return {"success": False, "error": result.stderr + "\n" + result2.stderr}
    except FileNotFoundError as e:
        return {"success": False, "error": f"Tool not found: {e}. Install: sudo apt install fswebcam ffmpeg"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def record_video(
    duration: int = 10,
    output_path: Optional[str] = None,
    device: str = "/dev/video0",
    audio: bool = True,
) -> dict:
    """Record video from webcam"""
    if output_path is None:
        output_path = str(CAPTURE_DIR / f"video_{_timestamp()}.mp4")

    try:
        cmd = ["ffmpeg", "-y", "-f", "v4l2", "-i", device]
        if audio:
            cmd += ["-f", "alsa", "-i", "default"]
        cmd += ["-t", str(duration), "-vcodec", "libx264", "-acodec", "aac", output_path]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=duration + 30)
        if result.returncode == 0:
            size = Path(output_path).stat().st_size // 1024
            return {"success": True, "path": output_path, "size_kb": size, "duration_s": duration}
        return {"success": False, "error": result.stderr[-500:]}
    except Exception as e:
        return {"success": False, "error": str(e)}


def create_timelapse(
    duration: int = 60,
    interval: int = 5,
    output_path: Optional[str] = None,
    device: str = "/dev/video0",
) -> dict:
    """Create a timelapse by capturing frames at intervals, then merging"""
    frames_dir = CAPTURE_DIR / f"timelapse_{_timestamp()}"
    frames_dir.mkdir(exist_ok=True)

    if output_path is None:
        output_path = str(CAPTURE_DIR / f"timelapse_{_timestamp()}.mp4")

    n_frames = duration // interval
    captured = []

    print(f"Capturing {n_frames} frames every {interval}s over {duration}s...")
    for i in range(n_frames):
        frame_path = str(frames_dir / f"frame_{i:04d}.jpg")
        result = take_picture(frame_path, device)
        if result["success"]:
            captured.append(frame_path)
        time.sleep(interval)

    if not captured:
        return {"success": False, "error": "No frames captured"}

    # Merge into video
    try:
        result = subprocess.run(
            ["ffmpeg", "-y", "-framerate", "10",
             "-i", str(frames_dir / "frame_%04d.jpg"),
             "-vcodec", "libx264", "-pix_fmt", "yuv420p", output_path],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode == 0:
            return {"success": True, "path": output_path, "frames_captured": len(captured)}
        return {"success": False, "error": result.stderr[-500:]}
    except Exception as e:
        return {"success": False, "error": str(e)}


def list_media() -> list:
    """List all captured media files"""
    files = []
    for ext in ("*.jpg", "*.png", "*.mp4", "*.avi"):
        for f in CAPTURE_DIR.glob(ext):
            files.append({
                "name": f.name,
                "path": str(f),
                "size_kb": f.stat().st_size // 1024,
                "created": datetime.fromtimestamp(f.stat().st_ctime).strftime("%Y-%m-%d %H:%M"),
            })
    files.sort(key=lambda x: x["created"], reverse=True)
    return files


from typing import Optional

if __name__ == "__main__":
    print("Media capture test...")
    result = take_picture()
    print(result)
