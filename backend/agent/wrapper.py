
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
except ImportError:
    print("WARNING: gui_agents not installed.")
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
        self.ground_model = "ui-tars-1.5-7b"
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
            self.sandbox = Sandbox()
            # Start stream to get URL
            self.sandbox.stream.start()
            time.sleep(2) # Wait for stream
            self.vnc_url = self.sandbox.stream.get_url()
            print(f"Sandbox created! VNC: {self.vnc_url}")
            
            # Create Adapter
            self.adapter = E2BAdapter(self.sandbox)
            
            # Init Agent
            if AgentS3:
                self._init_agent()
                
        return {"sandbox_id": self.sandbox.sandbox_id, "vnc_url": self.vnc_url}

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
            # Execute python script inside sandbox to take screenshot and return base64
            # This avoids dependency on 'scrot' tool availability
            cmd = "python3 -c \"import pyautogui, base64, io; b = io.BytesIO(); pyautogui.screenshot().save(b, format='PNG'); print(base64.b64encode(b.getvalue()).decode())\""
            
            # Run command in sandbox
            result = self.sandbox.commands.run(cmd)
            
            if result.stdout:
                import base64
                obs = {
                    "screenshot": base64.b64decode(result.stdout.strip())
                }
            else:
                print(f"Screenshot capture failed. stderr: {result.stderr}")
                obs = {"screenshot": b""}
                
        except Exception as e:
            print(f"Screenshot exception: {e}")
            obs = {"screenshot": b""}

        if not self.agent:
             return {"status": "error", "message": "Agent not loaded"}

        # Predict
        try:
            # We mock the observation for now or implementing screenshot retrieval is next step
            # Agent-S3 expects 'screenshot' in obs.
            
            info, action = self.agent.predict(instruction=instruction, observation=obs)
            
            result_logs = []
            for act in action:
                print(f"Executing Agent Action: {act}")
                try:
                    # THE MAGIC: Execute code but inject our adapter as 'pyautogui'
                    exec_globals = {"pyautogui": self.adapter, "time": time}
                    exec(act, exec_globals)
                    result_logs.append(f"Executed: {act}")
                except Exception as e:
                    result_logs.append(f"Error: {e}")
            
            return {
                "status": "success", 
                "info": info,
                "actions": action, 
                "logs": result_logs
            }

        except Exception as e:
            return {"status": "error", "message": str(e)}
