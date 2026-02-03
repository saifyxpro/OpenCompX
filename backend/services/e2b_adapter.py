
from e2b_desktop import Sandbox
import time
import logging

logger = logging.getLogger(__name__)

class E2BAdapter:
    """
    Adapts Agent-S3's local control calls (pseudo-pyautogui) to E2B Desktop Sandbox calls.
    Mocking the pyautogui interface used by Agent-S3.
    """
    def __init__(self, sandbox: Sandbox):
        self.sandbox = sandbox
        # self._check_connection() # .params() not available in 1.5.0

    # def _check_connection(self):
    #     try:
    #         # Simple check to ensure sandbox is responsive
    #         self.sandbox.params() 
    #     except Exception as e:
    #         logger.error(f"E2B Sandbox connection failed: {e}")

    # --- Mouse Functions ---
    def click(self, x=None, y=None, clicks=1, interval=0.0, button='left', **kwargs):
        logger.info(f"E2B Click: x={x}, y={y}, clicks={clicks}, button={button}")
        
        # E2B SDK requires move_mouse first, then click without coordinates
        if x is not None and y is not None:
            self.sandbox.move_mouse(int(x), int(y))
        
        for _ in range(clicks):
            if button == 'left':
                self.sandbox.left_click()
            elif button == 'right':
                self.sandbox.right_click()
            elif button == 'middle':
                self.sandbox.middle_click()
            
            if interval > 0:
                time.sleep(interval)

    def doubleClick(self, x=None, y=None, interval=0.0, button='left', **kwargs):
        logger.info(f"E2B DoubleClick: x={x}, y={y}")
        if x is not None and y is not None:
            self.sandbox.move_mouse(int(x), int(y))
        self.sandbox.double_click()

    def moveTo(self, x, y, duration=0.0, **kwargs):
        # E2B move_mouse is instant, duration ignored
        logger.info(f"E2B MoveTo: x={x}, y={y}")
        self.sandbox.move_mouse(int(x), int(y))

    def move(self, xOffset, yOffset, duration=0.0, **kwargs):
        # This is relative move. E2B doesn't have reliable relative move exposed directly 
        # in the simple API docs I saw, but we can assume we generally use moveTo.
        # For now, logging warning.
        logger.warning(f"E2B move (relative) not fully supported, ignoring offset: {xOffset}, {yOffset}")

    def drag(self, x, y, duration=0.0, **kwargs):
        # Dragging is complex in E2B simple API. 
        # Use mouse_press, move_mouse, mouse_release sequence
        logger.info(f"E2B Drag to: x={x}, y={y}")
        try:
            self.sandbox.mouse_press("left")
            self.sandbox.move_mouse(int(x), int(y))
            self.sandbox.mouse_release("left")
        except Exception as e:
            logger.error(f"Drag failed: {e}, falling back to click")
            self.sandbox.move_mouse(int(x), int(y))
            self.sandbox.left_click()

    def scroll(self, clicks, x=None, y=None, **kwargs):
        # Pyautogui scroll amount is clicks. E2B scroll takes 'direction' and 'amount'.
        direction = 'up' if clicks > 0 else 'down'
        amount = abs(clicks)
        logger.info(f"E2B Scroll: {direction} {amount}")
        self.sandbox.scroll(direction, amount)

    # --- Keyboard Functions ---
    def write(self, message, interval=0.0, **kwargs):
        logger.info(f"E2B Write: {message}")
        self.sandbox.write(message)
    
    def typewrite(self, message, interval=0.0, **kwargs):
        self.write(message, interval, **kwargs)

    # --- Helper ---
    def _map_key(self, key):
        key = key.lower()
        mapping = {
            'win': 'super',
            'windows': 'super',
            'altleft': 'alt',
            'altright': 'alt',
            'ctrlleft': 'ctrl',
            'ctrlright': 'ctrl',
            'shiftleft': 'shift',
            'shiftright': 'shift',
            'esc': 'escape',
             # Add other mappings as needed for Linux/E2B
        }
        return mapping.get(key, key)

    def press(self, keys, presses=1, interval=0.0, **kwargs):
        # normalize keys
        if isinstance(keys, str):
            keys = [keys]
        
        # map keys
        keys = [self._map_key(k) for k in keys]
        
        logger.info(f"E2B Press (mapped): {keys}")
        
        for _ in range(presses):
            for key in keys:
                try:
                    self.sandbox.press(key)
                except Exception as e:
                    # Fallback to xdotool with DISPLAY
                    logger.warning(f"sandbox.press failed: {e}, using xdotool fallback")
                    self._xdotool_key(key)
            if interval > 0:
                time.sleep(interval)
    
    def _xdotool_key(self, key):
        """Fallback key press using xdotool with DISPLAY set"""
        # Map key names to xdotool format
        key_map = {
            'enter': 'Return',
            'return': 'Return', 
            'backspace': 'BackSpace',
            'tab': 'Tab',
            'escape': 'Escape',
            'space': 'space',
            'ctrl': 'ctrl',
            'alt': 'alt',
            'shift': 'shift',
            'super': 'super',
        }
        xdo_key = key_map.get(key.lower(), key)
        cmd = f"export DISPLAY=:0; xdotool key {xdo_key}"
        try:
            self.sandbox.commands.run(cmd, timeout=5)
        except Exception as e:
            logger.error(f"xdotool key failed: {e}")
                
    def hotkey(self, *args, **kwargs):
        # map keys
        mapped_args = [self._map_key(k) for k in args]
        logger.info(f"E2B Hotkey (mapped): {mapped_args}")
        
        # SPECIAL HANDLER: Windows key usually means "Open Start Menu"
        # In XFCE (E2B default), keybindings can be flaky. 
        # We force it open via command if we see 'win'/'super'.
        if 'super' in mapped_args or 'win' in args:
            try:
                logger.info("Intercepted 'win' key: Executing xfce4-popup-whiskermenu")
                self.sandbox.commands.run("export DISPLAY=:0; xfce4-popup-whiskermenu", background=True)
                time.sleep(0.5) # Wait for menu
                return # Skip physical key press to avoid toggling it closed
            except Exception as e:
                logger.error(f"Failed to force open menu: {e}")

        # E2B press with control keys usually handles chords if passed as list
        try:
            self.sandbox.press(list(mapped_args))
        except Exception as e:
            # Fallback to xdotool
            logger.warning(f"sandbox.press hotkey failed: {e}, using xdotool")
            key_combo = "+".join(mapped_args)
            cmd = f"export DISPLAY=:0; xdotool key {key_combo}"
            try:
                self.sandbox.commands.run(cmd, timeout=5)
            except Exception as e2:
                logger.error(f"xdotool hotkey failed: {e2}")

    def keyDown(self, key, **kwargs):
        # E2B SDK might not support holding keys down statefully in the simple client.
        # We just press it for now.
        logger.warning(f"E2B keyDown {key} converted to press")
        self.press(key)

    def keyUp(self, key, **kwargs):
        pass

    # --- Application/URL Launchers (CUA2 Style) ---
    def launch(self, app):
        logger.info(f"E2B Launch: {app}")
        
        # Map common app names to their actual binary names on Debian/Ubuntu
        app_map = {
            "firefox": "firefox-esr",
            "libreoffice": "libreoffice",
            "libreoffice-calc": "libreoffice --calc",
            "libreoffice--calc": "libreoffice --calc",
            "calc": "libreoffice --calc",
            "terminal": "xfce4-terminal",
            "xterm": "xterm",
        }
        
        actual_app = app_map.get(app.lower(), app)
        
        # Use nohup with background=True to avoid timeout issues
        cmd = f"export DISPLAY=:0; nohup {actual_app} > /tmp/launch_{app}.log 2>&1 &"
        logger.info(f"E2B Launch Command: {cmd}")
        
        try:
            self.sandbox.commands.run(cmd, background=True)
            time.sleep(1.5)  # Give app time to start
        except Exception as e:
            logger.error(f"Launch failed: {e}")

    def open_url(self, url):
        logger.info(f"E2B Open URL: {url}")
        if not url.startswith("http"):
             url = f"https://{url}"
        
        # Try multiple browsers in order of preference
        browsers = ["firefox-esr", "firefox", "chromium", "google-chrome"]
        
        for browser in browsers:
            try:
                cmd = f"export DISPLAY=:0; nohup {browser} '{url}' > /tmp/browser.log 2>&1 &"
                logger.info(f"Trying browser: {cmd}")
                self.sandbox.commands.run(cmd, background=True)
                time.sleep(1.5)
                return  # Success, exit
            except Exception as e:
                logger.warning(f"{browser} failed: {e}")
                continue
        
        logger.error("All browsers failed to launch!")

    # --- Utils ---
    def position(self):
        # We can't easily get sync mouse position from E2B without a call.
        # Return dummy or last known.
        return (0, 0)
        
    def size(self):
        return (1920, 1080) # Default E2B resolution
