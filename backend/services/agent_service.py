"""
Agent Service - Uses Local Docker Container for desktop automation.
No E2B dependency - runs entirely locally with Docker + VNC.
"""

import os
import time
from dotenv import load_dotenv

# Import local adapter
from backend.services.local_adapter import LocalDockerAdapter, is_container_running, start_container, get_novnc_url

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
        self.ground_provider = "openai"
        self.ground_url = os.getenv("VISION_SERVICE_URL", "http://localhost:8080/v1")
        self.ground_model = os.getenv("VISION_MODEL", "ByteDance-Seed/UI-TARS-1.5-7B")
        self.ground_width = 1920
        self.ground_height = 1080

        self.agent = None
        self.adapter = None
        self.vnc_url = None
        self.container_running = False

    def initialize_sandbox(self, resolution=None):
        """Initialize local Docker container for desktop automation."""
        if not self.container_running:
            print("Checking Local Docker Container...")
            
            if not is_container_running():
                print("Container not running, starting it...")
                if not start_container():
                    raise RuntimeError("Failed to start Docker container. Make sure Docker is running.")
                print("Container started!")
            else:
                print("Container already running!")
            
            self.container_running = True
            
            # Wait for VNC to be ready
            print("Waiting for VNC to initialize...")
            time.sleep(5)
            
            # Create adapter
            self.adapter = LocalDockerAdapter()
            
            # Get VNC URL
            self.vnc_url = get_novnc_url()
            print(f"Desktop ready! VNC: {self.vnc_url}")
            
            # Wait for desktop to be ready
            self._wait_for_desktop_ready()
            
            # Init Agent
            if AgentS3:
                self._init_agent()
                
        return {"sandbox_id": "local-docker", "vnc_url": self.vnc_url}

    def _wait_for_desktop_ready(self):
        """Wait for desktop to initialize by checking screenshots."""
        print("Waiting for desktop to initialize...")
        time.sleep(3)
        
        for i in range(10):
            try:
                screenshot = self.adapter.screenshot()
                if screenshot and len(screenshot) > 10000:
                    print("Desktop ready (screenshot captured).")
                    return
                print(f"Waiting for desktop... ({i}/10)")
                time.sleep(2)
            except Exception as e:
                print(f"Desktop not ready yet: {e}")
                time.sleep(2)
        print("Warning: Desktop might not be fully ready, proceeding anyway.")

    def _take_screenshot(self) -> bytes:
        """Take screenshot using local adapter."""
        try:
            return self.adapter.screenshot()
        except Exception as e:
            print(f"Screenshot failed: {e}")
            return b""

    def _init_agent(self):
        engine_params = {
            "engine_type": self.provider,
            "model": self.model,
            "api_key": os.getenv("OPENAI_API_KEY"),
            "temperature": 1.0
        }

        engine_params_for_grounding = {
            "engine_type": self.ground_provider,
            "model": self.ground_model,
            "base_url": self.ground_url,
            "api_key": "empty",
            "grounding_width": self.ground_width,
            "grounding_height": self.ground_height,
        }

        self.grounding_agent = OSWorldACI(
            env=None,
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
        MAX_STEPS = 10
        
        if not self.container_running:
            self.initialize_sandbox()

        if not self.agent:
            return {"status": "error", "message": "Agent not loaded"}

        all_logs = []
        all_actions = []
        executed_actions_count = 0
        
        augmented_instruction = (
            f"{instruction}\n\n"
            "CRITICAL INSTRUCTIONS:\n"
            "1. Execute ONLY ONE action at a time, then wait for the next screenshot.\n"
            "2. Do NOT plan multiple steps ahead - just do the NEXT single action.\n"
            "3. To open applications: YOU MUST use `pyautogui.launch('app_name')`. DO NOT use keyboard shortcuts (like win key or alt+f2) or menu clicks to launch apps. THEY WILL FAIL.\n"
            "4. To open URLs: use `pyautogui.open_url('url')`\n"
            "5. The system password for user 'agent' is 'agent'. If asked for a password, type 'agent'.\n"
            "6. Do NOT output 'DONE' until you can SEE the task is complete in the screenshot.\n\n"
            "Your first action should be to launch Firefox using `pyautogui.launch('firefox')`."
        )
        
        for step_num in range(MAX_STEPS):
            print(f"\n{'='*60}")
            print(f"AGENT STEP {step_num + 1}/{MAX_STEPS}")
            print(f"{'='*60}")
            
            # Wait 2 seconds before first screenshot
            if step_num == 0:
                print("Waiting 2 seconds for screen to settle...")
                time.sleep(2)
            
            # Capture screenshot
            screenshot_bytes = self._take_screenshot()
            obs = {"screenshot": screenshot_bytes}
            
            # Call agent predict
            try:
                info, action = self.agent.predict(instruction=augmented_instruction, observation=obs)
                
                print(f"  info: {info}")
                print(f"  action count: {len(action) if action else 0}")
                print(f"  actions: {action}")
                
                # Check for DONE/FAIL
                if action and len(action) == 1:
                    single_action = action[0].strip().upper()
                    if single_action == "DONE":
                        print(f"Agent returned DONE (executed_actions_count={executed_actions_count})...")
                        if executed_actions_count == 0:
                            print("WARNING: Premature DONE! Forcing retry...")
                            all_logs.append("Agent tried to exit early, retrying...")
                            augmented_instruction += "\n\nYOU MUST EXECUTE AN ACTION NOW."
                            continue
                        else:
                            all_logs.append("Task completed!")
                            break
                    elif single_action == "FAIL":
                        print("Agent signaled FAIL")
                        all_logs.append("Task failed.")
                        break
                
                if not action or len(action) == 0:
                    print("No actions returned")
                    all_logs.append("I've completed what I can see to do.")
                    break
                
                # Execute actions
                for act in action:
                    act_upper = act.strip().upper()
                    if act_upper in ["DONE", "FAIL", "WAIT", "SCROLL", "SCREENSHOT"]:
                        continue
                    
                    all_actions.append(act)
                    
                    try:
                        print(f"  Executing: {act}")
                        
                        # Sanitize action
                        sanitized_act = act
                        sanitized_act = sanitized_act.replace("import subprocess", "pass")
                        sanitized_act = sanitized_act.replace("subprocess.run", "# subprocess.run")
                        # CRITICAL: Remove 'import pyautogui' to prevent overwriting our adapter
                        sanitized_act = sanitized_act.replace("import pyautogui;", "pass;")
                        sanitized_act = sanitized_act.replace("import pyautogui", "pass")
                        
                        # Execute with adapter as pyautogui
                        import subprocess as _subprocess
                        exec_globals = {"pyautogui": self.adapter, "time": time, "subprocess": _subprocess}
                        exec(sanitized_act, exec_globals)
                        
                        executed_actions_count += 1
                        print(f"  Action executed successfully (total: {executed_actions_count})")
                        
                        log_msg = self._get_human_log(act)
                        all_logs.append(log_msg)
                        
                    except Exception as e:
                        print(f"  ERROR: Action failed: {e}")
                        all_logs.append(f"Action error: {str(e)[:100]}")
                    
                    time.sleep(1.5)
                    
            except Exception as e:
                print(f"Agent predict error: {e}")
                return {"status": "error", "message": str(e)}
        
        return {
            "status": "success",
            "actions": all_actions,
            "logs": all_logs,
            "info": info if 'info' in dir() else {}
        }

    def _get_human_log(self, action_code: str) -> str:
        """Convert pyautogui code to human-readable description."""
        if "launch(" in action_code:
            app = action_code.split("launch(")[1].split(")")[0].strip("'\"")
            return f"Opening {app}..."
        elif "open_url(" in action_code:
            url = action_code.split("open_url(")[1].split(")")[0].strip("'\"")
            return f"Navigating to {url}..."
        elif "click(" in action_code:
            return "Clicking on element..."
        elif "write(" in action_code or "typewrite(" in action_code:
            return "Typing text..."
        elif "hotkey(" in action_code:
            return "Pressing keyboard shortcut..."
        elif "scroll(" in action_code:
            return "Scrolling..."
        else:
            return "Performing action..."

    def stop(self):
        """Stop the container (optional - can leave running for reuse)."""
        print("Stop requested - container will continue running for reuse.")
        # Don't actually stop, just mark as available for next request
        pass
