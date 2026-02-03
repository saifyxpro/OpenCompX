
import os
import io
import time
from dotenv import load_dotenv
from e2b_desktop import Sandbox

# Import adapter
from backend.agent.adapter import E2BAdapter

# Try importing from gui_agents
try:
    from gui_agents.s3.agents.agent_s import AgentS3
    from gui_agents.s3.agents.grounding import OSWorldACI
except ImportError as e:
    import traceback
    print(f"CRITICAL WARNING: gui_agents failed to import: {e}")
    traceback.print_exc()
    AgentS3 = None
    OSWorldACI = None

class AgentWrapper:
    def __init__(self):
        load_dotenv()
        
        self.provider = "openai"
        self.model = "gpt-5-2025-08-07"
        
        # Grounding Config (UI-TARS local)
        self.ground_provider = "openai" # Using OpenAI-compatible vLLM API
        self.ground_url = os.getenv("VISION_SERVICE_URL", "http://localhost:8080/v1")
        # Default to the full HuggingFace ID as vLLM usually requires it
        self.ground_model = os.getenv("VISION_MODEL", "ByteDance-Seed/UI-TARS-1.5-7B")
        self.ground_width = 1920
        self.ground_height = 1080

        self.agent = None
        self.sandbox = None
        self.adapter = None
        self.vnc_url = None

    def initialize_sandbox(self):
        if not self.sandbox:
            api_key = os.getenv("E2B_API_KEY")
            if not api_key or "placeholder" in api_key:
                raise ValueError("E2B_API_KEY is missing or invalid in backend/.env")

            print("Initializing E2B Sandbox...")
            # Use the robust template from CUA2 (Ubuntu + XFCE + Desktop Tools)
            # This ensures xfce4-popup-whiskermenu and other tools are available
            self.sandbox = Sandbox(template="k0wmnzir0zuzye6dndlw")
            
            # Start stream to get URL
            self.sandbox.stream.start()
            
            # Run CUA2 Cleanup/Setup Command for Firefox (prevents first-run wizards)
            # Run CUA2 Cleanup/Setup Command for Firefox (prevents first-run wizards)
            print("Configuring Sandbox Environment...")
            setup_cmd = """sudo mkdir -p /usr/lib/firefox-esr/distribution && echo '{"policies":{"OverrideFirstRunPage":"","OverridePostUpdatePage":"","DisableProfileImport":true,"DontCheckDefaultBrowser":true}}' | sudo tee /usr/lib/firefox-esr/distribution/policies.json > /dev/null"""
            self.sandbox.commands.run(setup_cmd)
            
            # Wait for desktop to be actually ready (prevent black screen issues)
            self._wait_for_desktop_ready()
            
            self.vnc_url = self.sandbox.stream.get_url()
            print(f"Sandbox created! VNC: {self.vnc_url}")
            
            # Create Adapter
            self.adapter = E2BAdapter(self.sandbox)
            
            # Init Agent
            if AgentS3:
                self._init_agent()
                
        return {"sandbox_id": self.sandbox.sandbox_id, "vnc_url": self.vnc_url}

    def _wait_for_desktop_ready(self):
        print("Waiting for desktop to initialize...")
        # Simple wait first
        time.sleep(5)
        
        # Poll for non-black screenshot
        # A completely black 1080p screen is small in PNG, but not zero.
        # We just assume if we can take a screenshot without error, we are somewhat ready.
        # But E2B sometimes takes time to start X server.
        for i in range(10):
            try:
                s = self.sandbox.screenshot()
                if s and len(s) > 10000: # Arbitrary threshold, empty black PNG is ~800 bytes sometimes
                    print("Desktop ready (screenshot captured).")
                    return
                print(f"Waiting for desktop... ({i}/10)")
                time.sleep(2)
            except Exception as e:
                print(f"Desktop not ready yet: {e}")
                time.sleep(2)
        print("Warning: Desktop might not be fully ready, proceeding anyway.")

    def _init_agent(self):
        engine_params = {
            "engine_type": self.provider,
            "model": self.model,
            "api_key": os.getenv("OPENAI_API_KEY"),
            "temperature": 1.0
        }

        # For UI-TARS via vLLM (OpenAI compatible)
        engine_params_for_grounding = {
            "engine_type": self.ground_provider,
            "model": self.ground_model,
            "base_url": self.ground_url,
            "api_key": "empty",
            "grounding_width": self.ground_width,
            "grounding_height": self.ground_height,
        }

        # We need to mock LocalEnv or provide a way for OSWorldACI to use our adapter
        # But Agent-S3 executes code. We need to inject our adapter as 'pyautogui' module.
        
        # Custom Grounding Agent that uses our Adapter if needed, 
        # or we just rely on the step() function to execute the code using the adapter.
        self.grounding_agent = OSWorldACI(
            env=None, # We handle execution manually
            platform="linux",
            engine_params_for_generation=engine_params,
            engine_params_for_grounding=engine_params_for_grounding,
            width=self.ground_width,
            height=self.ground_height
        )

        self.agent = AgentS3(
            engine_params,
            self.grounding_agent,
            platform="linux",
            max_trajectory_length=15,
            enable_reflection=True
        )
        print("Agent S3 Initialized!")

    def step(self, instruction: str):
        if not self.sandbox:
            self.initialize_sandbox()

        # Capture screenshot from E2B
        try:
            # Use native E2B SDK screenshot method (v1.5.0+)
            # Returns bytearray
            screenshot_bytes = self.sandbox.screenshot(format="bytes")
            
            if screenshot_bytes:
                obs = {
                    "screenshot": bytes(screenshot_bytes)
                }
            else:
                print("Screenshot captured but empty.")
                obs = {"screenshot": b""}
                
        except Exception as e:
            print(f"Screenshot exception: {e}")
            import traceback
            traceback.print_exc()
            obs = {"screenshot": b""}

        if not self.agent:
             return {"status": "error", "message": "Agent not loaded"}

        # Predict
        try:
            # We mock the observation for now or implementing screenshot retrieval is next step
            # Agent-S3 expects 'screenshot' in obs.
            
            # INJECT SYSTEM INSTRUCTION (CUA2 Style)
            # We force the agent to use our new robust tools instead of flaky clicking.
            augmented_instruction = (
                f"{instruction}\n\n"
                "IMPORTANT: To open applications or websites, do NOT click icons. "
                "Use the provided python functions directly:\n"
                "- pyautogui.launch('app_name')  (e.g. 'firefox', 'xfce4-terminal')\n"
                "- pyautogui.open_url('url')     (e.g. 'google.com')\n"
                "Use these functions immediately if the task requires opening something."
            )

            info, action = self.agent.predict(instruction=augmented_instruction, observation=obs)
            
            result_logs = []
            # Track what we actually executed to return the truth
            executed_actions = []
            
            for act in action:
                # HEURISTIC REPAIR: Detect "Start Menu -> Type -> Enter" pattern
                # If agent tries to key-press its way to an app, force-upgrade to launch()
                # Use regex to handle 'win', "win", 'super', etc.
                import re
                legacy_pattern = r"(hotkey|press)\s*\(\s*[\[\(]?\s*(['\"](win|super|windows)['\"])"
                if re.search(legacy_pattern, act, re.IGNORECASE) and "write" in act:
                    # extract app name from write('Name')
                    match = re.search(r"write\s*\(\s*['\"](.+?)['\"]\s*\)", act, re.IGNORECASE)
                    if match:
                        app_name = match.group(1).lower()
                        print(f"Intercepting legacy open pattern: converting to launch('{app_name}')")
                        act = f"import pyautogui; pyautogui.launch('{app_name}')"
                
                print(f"Executing Agent Action: {act}")
                executed_actions.append(act) # Add the REAL code we are about to run
                
                try:
                    # Sanitize: Handle single-line code blocks like "import pyautogui; pyautogui.click()"
                    # We must NOT delete the line, but rather neutralize the import so our injected 'pyautogui' global persists.
                    sanitized_act = act.replace("import pyautogui", "pass")
                    # Handle "from pyautogui import ..." if it appears (less common in AgentS3 but possible)
                    if "from pyautogui" in sanitized_act:
                         sanitized_act = sanitized_act.replace("from pyautogui", "# from pyautogui")

                    # THE MAGIC: Execute code but inject our adapter as 'pyautogui'
                    # We also expose launch/open_url directly on pyautogui object (adapter)
                    exec_globals = {"pyautogui": self.adapter, "time": time}
                    exec(sanitized_act, exec_globals)
                    
                    # HUMAN-LIKE LOGGING
                    # User wants to know "what I am doing" like a human worker
                    log_msg = f"Executed: {act}" # fallback
                    try:
                        if "launch" in act:
                             import re
                             m = re.search(r"launch\(['\"](.+?)['\"]\)", act)
                             app = m.group(1) if m else "application"
                             log_msg = f"I am opening {app} for you..."
                        elif "open_url" in act:
                             import re
                             m = re.search(r"open_url\(['\"](.+?)['\"]\)", act)
                             url = m.group(1) if m else "URL"
                             log_msg = f"I am navigating to {url}..."
                        elif "write" in act:
                             log_msg = "I am typing text..."
                        elif "click" in act:
                             log_msg = "I am interacting with the UI..."
                        elif "hotkey" in act:
                             log_msg = "I am pressing keys..."
                    except:
                        pass
                        
                    result_logs.append(log_msg)
                except Exception as e:
                    result_logs.append(f"I ran into an issue: {e}")
            
            return {
                "status": "success", 
                "info": info,
                "actions": executed_actions,  # Return what we actually ran!
                "logs": result_logs
            }

        except Exception as e:
            return {"status": "error", "message": str(e)}
