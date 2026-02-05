
import os
import time
import logging
from typing import TypedDict, Annotated, List, Dict, Any, Union
import operator

from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

# Import existing services
from backend.services.local_adapter import LocalDockerAdapter
# We assume AgentS3 matches the interface expected by existing agent_service
try:
    from gui_agents.s3.agents.agent_s import AgentS3
except ImportError:
    AgentS3 = None

logger = logging.getLogger(__name__)

class AgentState(TypedDict):
    """The state of the agent in the LangGraph."""
    messages: Annotated[list[BaseMessage], operator.add]
    instruction: str
    user_image: Union[str, None] # Base64 image from user
    step_count: int
    executed_actions_count: int
    logs: Annotated[list[str], operator.add]
    status: str # "running", "done", "fail", "error"
    info: Dict[str, Any]
    latest_actions: List[str] # Actions to be executed by tool node

class LangGraphAgentService:
    def __init__(self, agent_instance: Any, adapter: LocalDockerAdapter):
        self.agent = agent_instance
        self.adapter = adapter
        self.workflow = self._build_graph()
        self.runner = self.workflow.compile()
        
    def _build_graph(self):
        workflow = StateGraph(AgentState)
        
        workflow.add_node("agent", self._agent_node)
        workflow.add_node("tools", self._tool_node)
        
        workflow.set_entry_point("agent")
        
        workflow.add_conditional_edges(
            "agent",
            self._should_continue,
            {
                "continue": "tools",
                "done": END,
                "fail": END
            }
        )
        
        workflow.add_edge("tools", "agent")
        
        return workflow

    def _agent_node(self, state: AgentState) -> Dict[str, Any]:
        """Node for the AI Agent to think and decide actions."""
        step_num = state["step_count"]
        instruction = state["instruction"]
        user_image = state.get("user_image")
        
        # 1. Prepare Environment & Observation
        # (Similar to agent_service logic)
        
        # Taking screenshot
        screenshot_bytes = self.adapter.screenshot(format="bytes")
        obs = {"screenshot": screenshot_bytes}
        
        # Augment instruction if needed
        current_instruction = instruction
        
        # 2. Predict
        logger.info(f"LangGraph Agent Step {step_num}")
        try:
            # Simple augmented instruction for V0.1
            if step_num == 0:
                 current_instruction = (
                    f"{instruction}\n\n"
                    "# MISSION & IDENTITY\n"
                    "You are an advanced autonomous AI agent capable of controlling a computer to accomplish complex tasks. "
                    "Your goal is to complete the user's request efficiently and accurately. \n"
                    "You are in a specialized LocalDocker container. `pyautogui.launch` is your primary method for opening applications.\n"
                    "Start by launching Firefox with `pyautogui.launch('firefox')` if a browser is needed."
                 )
                 
                 if user_image:
                     current_instruction = f"[USER PROVIDED AN IMAGE/SCREENSHOT AS CONTEXT]\n\n" + current_instruction
            
            info, action = self.agent.predict(instruction=current_instruction, observation=obs)
            
            # 3. Process Result
            logs = []
            status = "running"
            
            if not action or len(action) == 0:
                 logs.append("No actions returned.")
                 status = "done" # Or fail? defaulting to done for now
            
            single_action = action[0].strip().upper() if action and len(action) == 1 else ""
            
            if single_action == "DONE":
                status = "done"
                logs.append("Task completed!")
            elif single_action == "FAIL":
                status = "fail"
                logs.append("Task failed.")
            
            return {
                "step_count": step_num + 1,
                "latest_actions": action if status == "running" else [],
                "status": status,
                "info": info,
                "logs": logs
            }
            
        except Exception as e:
            logger.error(f"Agent prediction error: {e}")
            return {
                "step_count": step_num + 1,
                "status": "error",
                "logs": [f"Error: {e}"]
            }

    def _tool_node(self, state: AgentState) -> Dict[str, Any]:
        """Node to execute the actions decided by the agent."""
        actions = state["latest_actions"]
        logs = []
        executed_count = 0
        
        for act in actions:
            act_upper = act.strip().upper()
            if act_upper in ["DONE", "FAIL", "WAIT", "SCROLL", "SCREENSHOT"]:
                continue
                
            try:
                # Sanitize & Intercept (simplified from agent_service.py)
                sanitized_act = act.replace("import subprocess", "pass")
                sanitized_act = sanitized_act.replace("import pyautogui;", "pass;")
                sanitized_act = sanitized_act.replace("import pyautogui", "pass")
                
                # Execute
                import subprocess as _subprocess
                exec_globals = {"pyautogui": self.adapter, "time": time, "subprocess": _subprocess}
                
                logger.info(f"Executing: {sanitized_act}")
                exec(sanitized_act, exec_globals)
                
                executed_count += 1
                logs.append(self._get_human_log(act))
                
            except Exception as e:
                logger.error(f"Action failed: {e}")
                logs.append(f"Action error: {str(e)[:100]}")
            
            # Turbo Mode V2: Fast sleep
            time.sleep(0.1) 
            
        return {
            "executed_actions_count": state["executed_actions_count"] + executed_count,
            "logs": logs
        }

    def _should_continue(self, state: AgentState) -> str:
        """Decide next node based on status."""
        if state["status"] in ["done", "fail", "error"]:
            return state["status"] # Maps to END in the graph definition if done/fail
        
        if state["step_count"] >= 50:
            return "done" # Force stop
            
        return "continue"

    def _get_human_log(self, action_code: str) -> str:
        """Convert pyautogui code to human-readable description."""
        if "launch(" in action_code:
            app = action_code.split("launch(")[1].split(")")[0].strip("'\"")
            return f"Opening {app}..."
        elif "open_url(" in action_code:
            url = action_code.split("open_url(")[1].split(")")[0].strip("'\"")
            return f"Navigating to {url}..."
        return "Performing action..."

    def run(self, instruction: str, user_image: str | None = None):
        """Run the graph for the given instruction."""
        initial_state = {
            "messages": [],
            "instruction": instruction,
            "user_image": user_image,
            "step_count": 0,
            "executed_actions_count": 0,
            "logs": [],
            "status": "running",
            "info": {},
            "latest_actions": []
        }
        
        # Use stream=True to yield updates if we want, but for now blocking run is fine
        # Or better, we return the generator so chat.py can iterate it
        # config dictionary with recursion_limit to allow long tasks (default is usually 25)
        config = {"recursion_limit": 100} 
        return self.runner.stream(initial_state, config=config)
