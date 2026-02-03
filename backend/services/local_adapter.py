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
    
    CONTAINER_NAME = "openmanus-desktop"
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
    
    def doubleClick(self, x=None, y=None, interval=0.0, button='left', **kwargs):
        logger.info(f"Local DoubleClick: x={x}, y={y}")
        if x is not None and y is not None:
            self._exec(f"xdotool mousemove {int(x)} {int(y)}")
        self._exec("xdotool click --repeat 2 --delay 100 1")
    
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
    
    def scroll(self, clicks, x=None, y=None, **kwargs):
        direction = 4 if clicks > 0 else 5  # 4=up, 5=down in X11
        amount = abs(clicks)
        logger.info(f"Local Scroll: {'up' if clicks > 0 else 'down'} {amount}")
        
        if x is not None and y is not None:
            self._exec(f"xdotool mousemove {int(x)} {int(y)}")
        
        for _ in range(amount):
            self._exec(f"xdotool click {direction}")
    
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
        time.sleep(2)  # Wait for app to start
    
    def open_url(self, url):
        """Open URL in browser."""
        logger.info(f"Local Open URL: {url}")
        if not url.startswith("http"):
            url = f"https://{url}"
        
        self._exec(f"nohup firefox '{url}' > /tmp/browser.log 2>&1 &")
        time.sleep(3)  # Wait for browser to open
    
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


def is_container_running(container_name: str = "openmanus-desktop") -> bool:
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
        time.sleep(10)  # Wait for VNC to start
        return True
    except Exception as e:
        logger.error(f"Failed to start container: {e}")
        return False


def get_novnc_url(port: int = 6080) -> str:
    """Get the noVNC URL for the local container."""
    return f"http://localhost:{port}/vnc.html?autoconnect=true&resize=scale&password=agent"
