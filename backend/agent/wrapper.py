
import os
import io
import pyautogui
from dotenv import load_dotenv

# Try importing from gui_agents, handle if not installed
try:
    from gui_agents.s3.agents.agent_s import AgentS3
    from gui_agents.s3.agents.grounding import OSWorldACI
    from gui_agents.s3.utils.local_env import LocalEnv
except ImportError:
    print("WARNING: gui_agents not installed. Agent functionality will be mocked.")
    AgentS3 = None
    OSWorldACI = None
    LocalEnv = None

class AgentWrapper:
    def __init__(self):
        load_dotenv()
        
        self.platform = "linux" # Assuming running on Linux as requested
        self.provider = "openai"
        self.model = "gpt-5-2025-08-07"
        
        # Grounding Config (UI-TARS)
        self.ground_provider = "huggingface" 
        self.ground_url = os.getenv("VISION_SERVICE_URL", "http://localhost:8000")
        self.ground_model = "ui-tars-1.5-7b"
        self.ground_width = 1920
        self.ground_height = 1080

        if AgentS3:
            self._init_agent()
        else:
            self.agent = None

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
            "grounding_width": self.ground_width,
            "grounding_height": self.ground_height,
        }

        # Enable local env for coding tasks
        self.local_env = LocalEnv()
        
        self.grounding_agent = OSWorldACI(
            env=self.local_env,
            platform=self.platform,
            engine_params_for_generation=engine_params,
            engine_params_for_grounding=engine_params_for_grounding,
            width=self.ground_width,
            height=self.ground_height
        )

        self.agent = AgentS3(
            engine_params,
            self.grounding_agent,
            platform=self.platform,
            max_trajectory_length=8,
            enable_reflection=True
        )
        print("Agent S3 Initialized!")

    def step(self, instruction: str):
        if not self.agent:
            return {"status": "error", "message": "Agent not initialized"}

        # Capture screenshot
        screenshot = pyautogui.screenshot()
        buffered = io.BytesIO()
        screenshot.save(buffered, format="PNG")
        screenshot_bytes = buffered.getvalue()

        obs = {
            "screenshot": screenshot_bytes
        }

        # Predict
        try:
            info, action = self.agent.predict(instruction=instruction, observation=obs)
            
            # Action is a list of python code strings to execute
            # e.g., ["pyautogui.click(100, 200)"]
            
            result_logs = []
            for act in action:
                print(f"Executing: {act}")
                # Execute the code - DANGEROUS but required for Agent-S3
                # In a real deployment, this should be sandboxed
                try:
                    # We might need to inject dependencies into exec scope
                    exec_globals = {"pyautogui": pyautogui}
                    exec(act, exec_globals)
                    result_logs.append(f"Executed: {act}")
                except Exception as e:
                    result_logs.append(f"Error executing {act}: {e}")
            
            return {
                "status": "success",
                "info": info,
                "actions": action,
                "logs": result_logs
            }

        except Exception as e:
            return {"status": "error", "message": str(e)}
