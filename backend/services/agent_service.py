
import os
import io
import time
from dotenv import load_dotenv
from e2b_desktop import Sandbox

# Import adapter
from backend.services.e2b_adapter import E2BAdapter

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

class AgentService:
    def __init__(self):
        load_dotenv()
        
        self.provider = "openai"
        self.model = "gpt-5.2-2025-12-11"
        
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

    def initialize_sandbox(self, resolution=None):
        if not self.sandbox:
            api_key = os.getenv("E2B_API_KEY")
            if not api_key or "placeholder" in api_key:
                raise ValueError("E2B_API_KEY is missing or invalid in backend/.env")

            print("Initializing E2B Sandbox...")
            # Use the robust template from CUA2 (Ubuntu + XFCE + Desktop Tools)
            # This ensures xfce4-popup-whiskermenu and other tools are available
            self.sandbox = Sandbox(template="k0wmnzir0zuzye6dndlw")
            
            # Set Resolution if provided (Dynamic Resizing)
            if resolution:
                try:
                    w, h = resolution
                    print(f"Setting sandbox resolution to {w}x{h}")
                    # xrandr needs to run in the display context, usually handled by E2B or just works.
                    # We background it just in case, or run sync. Resizing is usually fast.
                    self.sandbox.commands.run(f"xrandr -s {w}x{h}")
                except Exception as e:
                    print(f"Failed to set resolution: {e}")

            # Start stream to get URL
            self.sandbox.stream.start()
            
            # Run CUA2 Cleanup/Setup Command for Firefox (prevents first-run wizards)
            print("Configuring Sandbox Environment...")
            setup_cmd = """sudo mkdir -p /usr/lib/firefox-esr/distribution && echo '{"policies":{"OverrideFirstRunPage":"","OverridePostUpdatePage":"","DisableProfileImport":true,"DontCheckDefaultBrowser":true}}' | sudo tee /usr/lib/firefox-esr/distribution/policies.json > /dev/null"""
            self.sandbox.commands.run(setup_cmd)
            
            # DEBUG: Check what browsers are available
            try:
                check_result = self.sandbox.commands.run("which firefox-esr firefox chromium google-chrome 2>/dev/null || echo 'No browsers found'")
                print(f"Available browsers: {check_result.stdout}")
            except Exception as e:
                print(f"Browser check failed: {e}")
            
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

    def _take_screenshot(self) -> bytes:
        """Robust screenshot with fallbacks for display issues."""
        # Try E2B SDK first (preferred)
        try:
            screenshot_bytes = self.sandbox.screenshot(format="bytes")
            if screenshot_bytes and len(screenshot_bytes) > 1000:
                return bytes(screenshot_bytes)
        except Exception as e:
            print(f"E2B screenshot failed: {e}")
        
        # Fallback 1: Reset DISPLAY and try scrot
        try:
            print("Trying scrot fallback with DISPLAY reset...")
            result = self.sandbox.commands.run(
                "export DISPLAY=:0 && scrot -o /tmp/screen.png && cat /tmp/screen.png",
                timeout=10
            )
            if result.stdout:
                return result.stdout.encode('latin-1') if isinstance(result.stdout, str) else result.stdout
        except Exception as e:
            print(f"Scrot fallback failed: {e}")
        
        # Fallback 2: Try import command (ImageMagick)
        try:
            print("Trying ImageMagick import fallback...")
            result = self.sandbox.commands.run(
                "export DISPLAY=:0 && import -window root png:- 2>/dev/null",
                timeout=15
            )
            if result.stdout:
                return result.stdout.encode('latin-1') if isinstance(result.stdout, str) else result.stdout
        except Exception as e:
            print(f"ImageMagick fallback failed: {e}")
        
        # Fallback 3: Restart display server
        try:
            print("WARNING: Display appears dead, attempting restart...")
            self.sandbox.commands.run("export DISPLAY=:0 && xdotool key Escape", timeout=5)
        except:
            pass
        
        # Return empty bytes as last resort
        print("All screenshot methods failed, returning empty screenshot")
        return b""


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
        """Run the agent in a loop until task is complete or max steps reached."""
        MAX_STEPS = 10  # Prevent infinite loops
        
        if not self.sandbox:
            self.initialize_sandbox()

        if not self.agent:
            return {"status": "error", "message": "Agent not loaded"}

        all_logs = []
        all_actions = []
        executed_actions_count = 0  # Track ACTUAL actions executed, not just steps
        
        # Augment instruction - CRITICAL: Must tell agent to do ONE step at a time
        augmented_instruction = (
            f"{instruction}\n\n"
            "CRITICAL INSTRUCTIONS:\n"
            "1. Execute ONLY ONE action at a time, then wait for the next screenshot.\n"
            "2. Do NOT plan multiple steps ahead - just do the NEXT single action.\n"
            "3. To open applications: use pyautogui.launch('app_name')\n"
            "4. To open URLs: use pyautogui.open_url('url')\n"
            "5. Do NOT output 'DONE' until you can SEE the task is complete in the screenshot.\n\n"
            "Your first action should be to launch Firefox."
        )
        
        for step_num in range(MAX_STEPS):
            print(f"\n{'='*60}")
            print(f"AGENT STEP {step_num + 1}/{MAX_STEPS}")
            print(f"{'='*60}")
            
            # 1. Capture screenshot using robust helper with fallbacks
            screenshot_bytes = self._take_screenshot()
            obs = {"screenshot": screenshot_bytes}
            
            # 2. Call agent predict
            try:
                info, action = self.agent.predict(instruction=augmented_instruction, observation=obs)
                
                print(f"  info: {info}")
                print(f"  action count: {len(action) if action else 0}")
                print(f"  actions: {action}")
                
                # Check if action is just "DONE" or "FAIL" - these are not real actions
                if action and len(action) == 1:
                    single_action = action[0].strip().upper()
                    if single_action == "DONE":
                        print(f"Agent returned DONE - checking if premature (executed_actions_count={executed_actions_count})...")
                        # If no actions have been EXECUTED yet, this is premature
                        if executed_actions_count == 0:
                            print("WARNING: Premature DONE! No actions executed yet. Forcing retry...")
                            all_logs.append("Agent tried to complete without doing anything, retrying...")
                            # Give it a stronger hint
                            augmented_instruction = (
                                f"{instruction}\n\n"
                                "YOU MUST EXECUTE AN ACTION NOW. Do not say DONE.\n"
                                "Your FIRST action should be: pyautogui.launch('firefox')\n"
                                "Execute this ONE action, then wait for the next screenshot."
                            )
                            continue
                        else:
                            all_logs.append("Task completed!")
                            print(f"Agent signaled DONE after {executed_actions_count} actions")
                            break
                    elif single_action == "FAIL":
                        print("Agent returned FAIL - skipping")
                        all_logs.append("Agent encountered difficulty, continuing...")
                        continue
                
                # Check if no actions (agent might be stuck)
                if not action or len(action) == 0:
                    print("No actions returned, agent may be done or stuck")
                    all_logs.append("I've completed what I can see to do.")
                    break
                
                # 3. Execute each action (filter out DONE/FAIL if mixed with real actions)
                for act in action:
                    act_upper = act.strip().upper()
                    if act_upper in ["DONE", "FAIL"]:
                        print(f"  Skipping meta-action: {act}")
                        continue
                    
                    # NOTE: We removed the aggressive "legacy pattern" interception
                    # because it was breaking valid hotkey sequences like Ctrl+L for address bar
                    
                    print(f"  Executing: {act}")
                    all_actions.append(act)
                    
                    try:
                        sanitized_act = act.replace("import pyautogui", "pass")
                        if "from pyautogui" in sanitized_act:
                            sanitized_act = sanitized_act.replace("from pyautogui", "# from pyautogui")
                        
                        # Also neutralize subprocess imports - we don't want agent installing stuff
                        sanitized_act = sanitized_act.replace("import subprocess", "pass")
                        sanitized_act = sanitized_act.replace("subprocess.run", "# subprocess.run")
                        sanitized_act = sanitized_act.replace("subprocess.check_call", "# subprocess.check_call")
                        
                        # THE MAGIC: Execute code but inject our adapter as 'pyautogui'
                        import subprocess as _subprocess
                        exec_globals = {"pyautogui": self.adapter, "time": time, "subprocess": _subprocess}
                        exec(sanitized_act, exec_globals)
                        
                        # Track successful execution
                        executed_actions_count += 1
                        print(f"  Action executed successfully (total: {executed_actions_count})")
                        
                        # Human-like logging
                        log_msg = self._get_human_log(act)
                        all_logs.append(log_msg)
                        
                    except Exception as e:
                        error_msg = f"Action failed: {e}"
                        print(f"  ERROR: {error_msg}")
                        all_logs.append(error_msg)
                
                # 4. Wait a bit for UI to update before next step
                time.sleep(1.5)
                
            except Exception as e:
                print(f"Predict error: {e}")
                import traceback
                traceback.print_exc()
                all_logs.append(f"Error during step: {e}")
                break
        
        return {
            "status": "success",
            "info": {"steps_taken": step_num + 1},
            "actions": all_actions,
            "logs": all_logs
        }
    
    def _get_human_log(self, act):
        """Convert code action to human-readable log message."""
        import re
        if "launch" in act:
            m = re.search(r"launch\(['\"](.+?)['\"]\)", act)
            return f"I am opening {m.group(1) if m else 'application'} for you..."
        elif "open_url" in act:
            m = re.search(r"open_url\(['\"](.+?)['\"]\)", act)
            return f"I am navigating to {m.group(1) if m else 'URL'}..."
        elif "write" in act:
            m = re.search(r"write\(['\"](.+?)['\"]\)", act)
            text = m.group(1)[:30] + "..." if m and len(m.group(1)) > 30 else (m.group(1) if m else "text")
            return f"I am typing: {text}"
        elif "click" in act:
            m = re.search(r"click\((\d+),\s*(\d+)\)", act)
            if m:
                return f"I am clicking at position ({m.group(1)}, {m.group(2)})..."
            return "I am clicking..."
        elif "hotkey" in act or "press" in act:
            return "I am pressing keys..."
        elif "scroll" in act:
            return "I am scrolling..."
        else:
            return f"Executed: {act[:50]}..."

