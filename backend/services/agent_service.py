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

class GroundingProxy:
    """
    Acts as a proxy for the OSWorldACI (UI-TARS) agent.
    
    Purpose: 
    - Allows the Planner (Agent-S) to run WITHOUT seeing the screenshot (saving tokens).
    - When the Planner calls the Grounder, this proxy re-injects the real screenshot 
      that was cached from the latest observation.
    """
    def __init__(self, real_grounder):
        self.real_grounder = real_grounder
        self.latest_screenshot = None
        
    def update_screenshot(self, screenshot: bytes):
        """Update the cached screenshot."""
        self.latest_screenshot = screenshot
        
    def predict(self, *args, **kwargs):
        """Intercept the grounding call and inject the real screenshot."""
        # If we have a cached screenshot, inject it into the observation
        if self.latest_screenshot:
            if "observation" in kwargs:
                kwargs["observation"]["screenshot"] = self.latest_screenshot
            elif len(args) > 1 and isinstance(args[1], dict):
                 # Handle positional args: (instruction, observation)
                 args[1]["screenshot"] = self.latest_screenshot
        
        # Determine strict mode based on observation (heuristics)
        # If Planner didn't see the screen, we need fairly strict grounding
        return self.real_grounder.predict(*args, **kwargs)

    def __getattr__(self, name):
        """Delegate all other calls to the real grounder."""
        return getattr(self.real_grounder, name)

class AgentService:
    def __init__(self):
        load_dotenv()
        
        self.provider = os.getenv("LLM_PROVIDER", "google")
        
        default_model = "gemini-3-flash-preview"
        if self.provider == "fireworks":
            default_model = "accounts/fireworks/models/kimi-k2p5"
            
        self.model = os.getenv("LLM_MODEL", default_model)
        
        # Grounding Config (UI-TARS local)
        self.ground_provider = "openai"
        self.ground_url = os.getenv("VISION_SERVICE_URL", "http://localhost:8080/v1")
        self.ground_model = os.getenv("VISION_MODEL", "ByteDance-Seed/UI-TARS-1.5-7B")
        self.ground_width = 1920
        self.ground_height = 1080

        self.agent = None
        self.adapter = None
        self.langgraph_agent = None
        self.vnc_url = None
        self.container_running = False
        self.container_name = "opencompx-desktop"

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
            
            # 1. Initialize Adapter
            if not self.adapter:
                self.adapter = LocalDockerAdapter(self.container_name)
                
            # 2. Initialize Agent (Dependency for LangGraph)
            if not self.agent and AgentS3:
                 self._init_agent()
                 
            # 3. Initialize LangGraph Agent
            if not self.langgraph_agent:
                try:
                    from backend.services.langgraph_agent import LangGraphAgentService
                    self.langgraph_agent = LangGraphAgentService(self.agent, self.adapter)
                    print("LangGraph Agent Service Initialized!")
                except Exception as e:
                    print(f"Failed to init LangGraph: {e}")
                    self.langgraph_agent = None
                
            # Wait for VNC to be ready (Polling)
            print("Waiting for VNC availability...")
            if not self.adapter.wait_for_vnc(timeout=20):
                 print("WARNING: VNC polling timed out. Desktop might not be viewable.")
            
            # Get VNC URL
            self.vnc_url = get_novnc_url()
            print(f"Desktop ready! VNC: {self.vnc_url}")
            
            # Wait for desktop to be ready
            self._wait_for_desktop_ready()
                
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
        if self.provider == "google":
             engine_params = {
                "engine_type": "google",
                "model": self.model, # gemini-3-flash-preview
                "api_key": os.getenv("GEMINI_API_KEY"), # New key
                "thinking_level": "HIGH", # For Gemini 3 Flash
                "temperature": 1.0
            }
        elif self.provider == "fireworks":
            engine_params = {
                "engine_type": "openai",
                "model": self.model, # accounts/fireworks/models/kimi-k2p5
                "api_key": os.getenv("FIREWORKS_API_KEY"),
                "base_url": "https://api.fireworks.ai/inference/v1",
                "temperature": 0.6,
                "max_tokens": 4096
            }
        else:
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

        print(f"Initializing OSWorldACI with Grounding URL: {self.ground_url} | Model: {self.ground_model}")
        self.grounding_agent = OSWorldACI(
            env=None,
            platform="linux",
            engine_params_for_generation=engine_params,
            engine_params_for_grounding=engine_params_for_grounding,
            width=self.ground_width,
            height=self.ground_height
        )
        
        # Wrap in Proxy to enable cost optimization (Text-Only Planner)
        self.grounding_agent_proxy = GroundingProxy(self.grounding_agent)

        self.agent = AgentS3(
            engine_params,
            self.grounding_agent_proxy, # Use proxy for AgentS3
            platform="linux",
            max_trajectory_length=50,
            enable_reflection=True
        )
        print("Agent S3 Initialized!")

    # Legacy step/execute_next_step methods removed in favor of LangGraphAgentService


    def cleanup_desktop(self):
        """Kill all running applications directly."""
        if not self.adapter:
             return
        print("Cleaning up desktop...")
        self.adapter._exec("pkill -9 -f firefox")
        self.adapter._exec("pkill -9 -f chrome")
        self.adapter._exec("pkill -9 -f chromium")
        self.adapter._exec("pkill -9 -f terminal")
        time.sleep(1)

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
        print("Stop requested - Cleaning up desktop...")
        self.cleanup_desktop()
        self.vnc_url = None
        # Don't stop container, just cleanup apps
