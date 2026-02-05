"""
Local Docker Adapter - Controls a local Docker container with VNC desktop.
Implements the same interface as E2BAdapter but uses docker exec for commands.
"""

import subprocess
import time
import logging
import base64
import os

logger = logging.getLogger(__name__)

class LocalDockerAdapter:
    """
    Adapts Agent-S3's pyautogui calls to a local Docker container with VNC.
    Uses docker exec to run xdotool/scrot commands inside the container.
    """
    
    CONTAINER_NAME = "opencompx-desktop"
    DISPLAY = ":1"  # VNC display
    
    def __init__(self, container_name: str = None):
        self.container_name = container_name or self.CONTAINER_NAME
        self._check_container()
    
    def _check_container(self):
        """Verify container is running."""
        try:
            result = subprocess.run(
                ["docker", "inspect", "-f", "{{.State.Running}}", self.container_name],
                capture_output=True, text=True, timeout=10
            )
            if "true" not in result.stdout.lower():
                raise RuntimeError(f"Container {self.container_name} is not running")
            logger.info(f"Container {self.container_name} is running")
        except subprocess.TimeoutExpired:
            raise RuntimeError("Docker command timed out")
        except FileNotFoundError:
            raise RuntimeError("Docker is not installed or not in PATH")

    def get_resolution(self) -> tuple[int, int]:
        """Get the current screen resolution from the container."""
        try:
            # parsing xdpyinfo output: '  dimensions:    1920x1080 pixels (508x285 millimeters)'
            cmd = "xdpyinfo | grep dimensions | awk '{print $2}'"
            result = self._exec(cmd).stdout.strip()
            if "x" in result:
                width, height = map(int, result.split("x"))
                logger.info(f"Detected Container Resolution: {width}x{height}")
                return width, height
        except Exception as e:
            logger.error(f"Failed to detect resolution: {e}")
        
        logger.warning("Could not detect resolution, defaulting to 1920x1080")
        return 1920, 1080
    
    def _exec(self, cmd: str, timeout: int = 30) -> subprocess.CompletedProcess:
        """Execute command in container with DISPLAY set."""
        full_cmd = f"export DISPLAY={self.DISPLAY} && {cmd}"
        return subprocess.run(
            ["docker", "exec", self.container_name, "bash", "-c", full_cmd],
            capture_output=True, text=True, timeout=timeout
        )
    
    def _exec_bytes(self, cmd: str, timeout: int = 30) -> bytes:
        """Execute command and return raw bytes (for screenshots)."""
        full_cmd = f"export DISPLAY={self.DISPLAY} && {cmd}"
        result = subprocess.run(
            ["docker", "exec", self.container_name, "bash", "-c", full_cmd],
            capture_output=True, timeout=timeout
        )
        return result.stdout
    
    # --- Screenshot ---
    def screenshot(self, format: str = "bytes") -> bytes:
        """Capture screenshot from container."""
        try:
            # Use scrot to capture, output to stdout as PNG
            result = self._exec_bytes("scrot -o /tmp/screen.png && cat /tmp/screen.png", timeout=10)
            if result and len(result) > 1000:
                return result
        except Exception as e:
            logger.error(f"Screenshot failed: {e}")
        
        # Fallback to import (ImageMagick)
        try:
            result = self._exec_bytes("import -window root png:-", timeout=15)
            if result and len(result) > 1000:
                return result
        except Exception as e:
            logger.error(f"ImageMagick screenshot failed: {e}")
        
        return b""
    
    # --- Mouse Functions ---
    def click(self, x=None, y=None, clicks=1, interval=0.0, button='left', **kwargs):
        logger.info(f"Local Click: x={x}, y={y}, clicks={clicks}, button={button}")
        
        if x is not None and y is not None:
            self._exec(f"xdotool mousemove {int(x)} {int(y)}")
        
        button_map = {'left': '1', 'middle': '2', 'right': '3'}
        btn = button_map.get(button, '1')
        
        for _ in range(clicks):
            self._exec(f"xdotool click {btn}")
            if interval > 0:
                time.sleep(interval)
    
        if x is not None and y is not None:
            self._exec(f"xdotool mousemove {int(x)} {int(y)}")
        self._exec("xdotool click --repeat 2 --delay 100 1")

    def rightClick(self, x=None, y=None, interval=0.0, **kwargs):
        logger.info(f"Local RightClick: x={x}, y={y}")
        if x is not None and y is not None:
            self._exec(f"xdotool mousemove {int(x)} {int(y)}")
        self._exec("xdotool click 3")
        
    def scroll(self, x=None, y=None, clicks=1, **kwargs):
        """Scroll usage: clicks > 0 is UP (4), clicks < 0 is DOWN (5)"""
        logger.info(f"Local Scroll: {clicks}")
        if x is not None and y is not None:
            self._exec(f"xdotool mousemove {int(x)} {int(y)}")
            
        direction = "4" if clicks > 0 else "5"
        count = abs(int(clicks))
        for _ in range(count):
            self._exec(f"xdotool click {direction}")
            time.sleep(0.05)

    # --- Keyboard / Text ---
    def hotkey(self, *args, **kwargs):
        """Execute hotkey combination e.g. 'ctrl', 'c' -> 'ctrl+c'."""
        keys = "+".join(args)
        logger.info(f"Local Hotkey: {keys}")
        self._exec(f"xdotool key {keys}")
        
    def typewrite(self, text, interval=0.0, **kwargs):
        """Type text using xdotool."""
        logger.info(f"Local Typewrite: {text}")
        # Escape single quotes for bash
        safe_text = text.replace("'", "'\\''")
        self._exec(f"xdotool type --delay {int(interval*1000)} '{safe_text}'")

    def write(self, text, interval=0.0, **kwargs):
        """Alias for typewrite."""
        self.typewrite(text, interval, **kwargs)

    # --- System / App Control ---
    def sleep(self, seconds):
        """Sleep (blocking)."""
        logger.info(f"Local Sleep: {seconds}s")
        time.sleep(float(seconds))

    def launch(self, app_name):
        """Launch an application in the background."""
        logger.info(f"Local Launch: {app_name}")
        # Try gtk-launch first, then direct execution
        # We use nohup and disown to prevent blocking
        cmd = f"nohup {app_name} > /dev/null 2>&1 &"
        self._exec(cmd)
    
    def moveTo(self, x, y, duration=0.0, **kwargs):
        logger.info(f"Local MoveTo: x={x}, y={y}")
        self._exec(f"xdotool mousemove {int(x)} {int(y)}")
    
    def move(self, xOffset, yOffset, duration=0.0, **kwargs):
        logger.warning(f"Local move (relative): {xOffset}, {yOffset}")
        self._exec(f"xdotool mousemove_relative {int(xOffset)} {int(yOffset)}")
    
    def drag(self, x, y, duration=0.0, **kwargs):
        logger.info(f"Local Drag to: x={x}, y={y}")
        self._exec("xdotool mousedown 1")
        self._exec(f"xdotool mousemove {int(x)} {int(y)}")
        self._exec("xdotool mouseup 1")
    
    def dragTo(self, x, y, duration=0.0, **kwargs):
        """Alias for drag (pyautogui compatibility)."""
        self.drag(x, y, duration, **kwargs)
    
    def scroll(self, clicks, x=None, y=None, **kwargs):
        """Vertical scroll (positive=up, negative=down)."""
        direction = 4 if clicks > 0 else 5  # 4=up, 5=down in X11
        amount = abs(int(clicks))
        logger.info(f"Local Scroll: {'up' if clicks > 0 else 'down'} {amount}")
        
        if x is not None and y is not None:
            self._exec(f"xdotool mousemove {int(x)} {int(y)}")
        
        for _ in range(amount):
            self._exec(f"xdotool click {direction}")
            time.sleep(0.05) # Small delay for reliability

    def vscroll(self, clicks, x=None, y=None, **kwargs):
        """Vertical scroll alias."""
        self.scroll(clicks, x, y, **kwargs)

    def hscroll(self, clicks, x=None, y=None, **kwargs):
        """Horizontal scroll (positive=right, negative=left)."""
        direction = 7 if clicks > 0 else 6  # 6=left, 7=right
        amount = abs(int(clicks))
        logger.info(f"Local HScroll: {'right' if clicks > 0 else 'left'} {amount}")
        
        if x is not None and y is not None:
            self._exec(f"xdotool mousemove {int(x)} {int(y)}")
        
        for _ in range(amount):
            self._exec(f"xdotool click {direction}")
            time.sleep(0.05)
    
    # --- App Management ---
    def launch(self, app_name: str, **kwargs):
        """Launch an application in the container background."""
        logger.info(f"Local Launch: {app_name}")
        # Use nohup and set DISPLAY to ensure it runs in background
        cmd = f"nohup {app_name} > /dev/null 2>&1 &"
        self._exec(cmd)
        time.sleep(2) # Wait for app to appear

    # --- Keyboard Functions ---
    def write(self, message, interval=0.0, **kwargs):
        logger.info(f"Local Write: {message[:50]}...")
        # Escape special characters for shell
        escaped = message.replace("'", "'\\''")
        self._exec(f"xdotool type --clearmodifiers '{escaped}'")
    
    def typewrite(self, message, interval=0.0, **kwargs):
        self.write(message, interval, **kwargs)
    
    def _map_key(self, key):
        """Map pyautogui key names to xdotool key names."""
        key = key.lower()
        mapping = {
            'win': 'super',
            'windows': 'super',
            'enter': 'Return',
            'return': 'Return',
            'backspace': 'BackSpace',
            'tab': 'Tab',
            'escape': 'Escape',
            'esc': 'Escape',
            'space': 'space',
            'ctrl': 'ctrl',
            'alt': 'alt',
            'shift': 'shift',
            'up': 'Up',
            'down': 'Down',
            'left': 'Left',
            'right': 'Right',
            'home': 'Home',
            'end': 'End',
            'pageup': 'Page_Up',
            'pagedown': 'Page_Down',
            'delete': 'Delete',
            'insert': 'Insert',
        }
        return mapping.get(key, key)
    
    def press(self, keys, presses=1, interval=0.0, **kwargs):
        if isinstance(keys, str):
            keys = [keys]
        
        keys = [self._map_key(k) for k in keys]
        logger.info(f"Local Press: {keys}")
        
        for _ in range(presses):
            for key in keys:
                self._exec(f"xdotool key {key}")
            if interval > 0:
                time.sleep(interval)
    
    def hotkey(self, *args, **kwargs):
        mapped_args = [self._map_key(k) for k in args]
        logger.info(f"Local Hotkey: {mapped_args}")
        
        # xdotool hotkey format: key1+key2+key3
        key_combo = "+".join(mapped_args)
        self._exec(f"xdotool key {key_combo}")
    
    def keyDown(self, key, **kwargs):
        mapped = self._map_key(key)
        self._exec(f"xdotool keydown {mapped}")
    
    def keyUp(self, key, **kwargs):
        mapped = self._map_key(key)
        self._exec(f"xdotool keyup {mapped}")
    
    # --- Application Launchers ---
    def launch(self, app):
        """Launch an application."""
        logger.info(f"Local Launch: {app}")
        
        app_map = {
            "firefox": "firefox",
            "terminal": "xfce4-terminal",
            "files": "thunar",
        }
        
        actual_app = app_map.get(app.lower(), app)
        self._exec(f"nohup {actual_app} > /tmp/launch.log 2>&1 &")
        time.sleep(1)  # Faster launch wait
    
    def open_url(self, url):
        """Open URL in browser."""
        logger.info(f"Local Open URL: {url}")
        if not url.startswith("http"):
            url = f"https://{url}"
        
        self._exec(f"nohup firefox '{url}' > /tmp/browser.log 2>&1 &")
        time.sleep(1.5)  # Faster browser wait
    
    # --- Utils ---
    def position(self):
        """Get current mouse position."""
        result = self._exec("xdotool getmouselocation --shell")
        # Parse X=123\nY=456
        pos = {"X": 0, "Y": 0}
        for line in result.stdout.split("\n"):
            if "=" in line:
                k, v = line.split("=")
                pos[k] = int(v)
        return (pos.get("X", 0), pos.get("Y", 0))
    
    def size(self):
        """Get screen resolution."""
        result = self._exec("xdpyinfo | grep dimensions")
        # Parse: dimensions:    1920x1080 pixels
        try:
            dims = result.stdout.split()[1].split("x")
            return (int(dims[0]), int(dims[1]))
        except:
            return (1920, 1080)

    def drag_rel(self, x_offset, y_offset, duration=0.0, **kwargs):
        """Drag relative to current position (Good for sliders)."""
        logger.info(f"Local Drag Rel: x={x_offset}, y={y_offset}")
        self._exec("xdotool mousedown 1")
        self._exec(f"xdotool mousemove_relative -- {int(x_offset)} {int(y_offset)}")
        self._exec("xdotool mouseup 1")

    def run_terminal(self, cmd: str):
        """Run a shell command in the container background."""
        logger.info(f"Local Terminal Run: {cmd}")
        return self._exec(cmd, timeout=10).stdout

    def set_clipboard(self, text: str):
        """Set clipboard content using xclip."""
        safe_text = text.replace("'", "'\\''")
        self._exec(f"echo -n '{safe_text}' | xclip -selection clipboard")

    def get_clipboard(self) -> str:
        """Get clipboard content."""
        return self._exec("xclip -selection clipboard -o", timeout=5).stdout

    def wait_for_vnc(self, timeout: int = 15) -> bool:
        """Poll container to check if VNC port (6080) is listening."""
        logger.info(f"Waiting for VNC to be ready (timeout={timeout}s)...")
        start = time.time()
        while time.time() - start < timeout:
            try:
                res = self._exec("pgrep -f websockify", timeout=2)
                if res.returncode == 0:
                    return True
            except:
                pass
            time.sleep(0.5)
        return False


def is_container_running(container_name: str = "opencompx-desktop") -> bool:
    """Check if the desktop container is running."""
    try:
        result = subprocess.run(
            ["docker", "inspect", "-f", "{{.State.Running}}", container_name],
            capture_output=True, text=True, timeout=5
        )
        return "true" in result.stdout.lower()
    except:
        return False


def start_container():
    """Start the desktop container using docker compose."""
    try:
        subprocess.run(
            ["docker", "compose", "-f", "docker-compose.desktop.yml", "up", "-d", "--build"],
            check=True, timeout=300
        )
        time.sleep(2)
        return True
    except Exception as e:
        logger.error(f"Failed to start container: {e}")
        return False


def get_novnc_url(port: int = 6080) -> str:
    """Get the noVNC URL for the local container."""
    return f"/vnc/vnc.html?autoconnect=true&resize=scale&password=agent&path=vnc/websockify"
