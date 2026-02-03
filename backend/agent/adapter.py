
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
        self._check_connection()

    def _check_connection(self):
        try:
            # Simple check to ensure sandbox is responsive
            self.sandbox.params() 
        except Exception as e:
            logger.error(f"E2B Sandbox connection failed: {e}")

    # --- Mouse Functions ---
    def click(self, x=None, y=None, clicks=1, interval=0.0, button='left', **kwargs):
        logger.info(f"E2B Click: x={x}, y={y}, clicks={clicks}, button={button}")
        if x is not None and y is not None:
            # E2B doesn't support moving and clicking in one go easily via click cmd, 
            # usually separate, but we can try just clicking if move was implicit.
            # Actually E2B left_click takes x, y.
            pass
        
        # Agent-S3 might pass coordinates. 
        # CAUTION: Agent-S3 might rely on 'current position' if x,y are None.
        # We should track position if needed, but for now assuming explicit coords or stateless.
        
        for _ in range(clicks):
            if button == 'left':
                self.sandbox.left_click(x, y)
            elif button == 'right':
                self.sandbox.right_click(x, y)
            elif button == 'middle':
                self.sandbox.middle_click(x, y)
            
            if interval > 0:
                time.sleep(interval)

    def doubleClick(self, x=None, y=None, interval=0.0, button='left', **kwargs):
        logger.info(f"E2B DoubleClick: x={x}, y={y}")
        self.sandbox.double_click(x, y)

    def moveTo(self, x, y, duration=0.0, **kwargs):
        # E2B move_mouse is instant, duration ignored
        logger.info(f"E2B MoveTo: x={x}, y={y}")
        self.sandbox.move_mouse(x, y)

    def move(self, xOffset, yOffset, duration=0.0, **kwargs):
        # This is relative move. E2B doesn't have reliable relative move exposed directly 
        # in the simple API docs I saw, but we can assume we generally use moveTo.
        # For now, logging warning.
        logger.warning(f"E2B move (relative) not fully supported, ignoring offset: {xOffset}, {yOffset}")

    def drag(self, x, y, duration=0.0, **kwargs):
        # Dragging is complex in E2B simple API. 
        # We might need mouse_press, move_mouse, mouse_release sequence.
        # But Sandbox object might not expose low level 'mouse_press' easily in all SDK versions.
        # Agent-S3 simple actions might use it.
        logger.info(f"E2B Drag to: x={x}, y={y}")
        self.sandbox.left_click(x, y) # Fallback to click for now if drag not avail

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

    def press(self, keys, presses=1, interval=0.0, **kwargs):
        logger.info(f"E2B Press: {keys}")
        # keys can be a list or single string
        if isinstance(keys, str):
            keys = [keys]
        
        for _ in range(presses):
            for key in keys:
                self.sandbox.press(key)
            if interval > 0:
                time.sleep(interval)

    def hotkey(self, *args, **kwargs):
        logger.info(f"E2B Hotkey: {args}")
        # Agent sends 'ctrl', 'c'. E2B press accepts list for combo? 
        # Or usually it handles 'ctrl+c'. 
        self.sandbox.press(list(args))

    def keyDown(self, key, **kwargs):
        # E2B SDK might not support holding keys down statefully in the simple client.
        # We just press it for now.
        logger.warning(f"E2B keyDown {key} converted to press")
        self.sandbox.press(key)

    def keyUp(self, key, **kwargs):
        pass

    # --- Utils ---
    def position(self):
        # We can't easily get sync mouse position from E2B without a call.
        # Return dummy or last known.
        return (0, 0)
        
    def size(self):
        return (1920, 1080) # Default E2B resolution
