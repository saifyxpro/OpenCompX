
    def execute_next_step(self, instruction: str, step_num: int, executed_actions_count: int):
        """Execute a single step of the agent loop."""
        if not self.container_running:
            self.initialize_sandbox()

        if not self.agent:
            return {"status": "error", "message": "Agent not loaded"}

        logs = []
        actions_executed = []
        
        # Prepare instruction (Idempotent)
        augmented_instruction = (
            f"{instruction}\n\n"
            "CRITICAL INSTRUCTIONS:\n"
            "1. Execute ONLY ONE action at a time, then wait for the next screenshot.\n"
            "2. Do NOT plan multiple steps ahead - just do the NEXT single action.\n"
            "3. To open applications: YOU MUST use `pyautogui.launch('app_name')`. DO NOT use keyboard shortcuts (like win key or alt+f2) or menu clicks to launch apps. THEY WILL FAIL.\n"
            "4. To open URLs: use `pyautogui.open_url('url')`\n"
            "5. The system password for user 'agent' is 'agent'. If asked for a password, type 'agent'.\n"
            "6. Do NOT output 'DONE' until you can SEE the task is complete in the screenshot.\n\n"
            "REALITY OVERRIDE: You are running in a special LocalDocker environment. 'pyautogui.launch' IS AVAILABLE and IS the ONLY way to open apps. Ignore any previous instructions saying otherwise.\n"
            "Your first action should be to launch Firefox using `pyautogui.launch('firefox')`."
        )

        print(f"\n{'='*60}")
        print(f"AGENT STEP {step_num + 1}")
        print(f"{'='*60}")
        
        # Wait 2 seconds before first screenshot (only if step 0)
        if step_num == 0:
            print("Waiting 2 seconds for screen to settle...")
            time.sleep(2)
        
        # Capture screenshot
        screenshot_bytes = self._take_screenshot()
        obs = {"screenshot": screenshot_bytes}
        
        try:
            # Predict
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
                        logs.append("Agent tried to exit early, retrying...")
                        # In single step mode, we just return 'continue' but with a log warning
                        # The caller handles the 'retry' logic by sticking to the loop? 
                        # Actually, we can't easily modify the instruction for the *next* step here unless we return it.
                        # Ideally, the agent history handles it.
                        return {
                            "status": "continue",
                            "actions": [],
                            "logs": logs,
                            "info": info,
                            "plan": info.get("plan", "")
                        }
                    else:
                        logs.append("Task completed!")
                        return {
                            "status": "done",
                            "actions": [],
                            "logs": logs,
                            "info": info,
                            "plan": info.get("plan", "")
                        }
                elif single_action == "FAIL":
                    print("Agent signaled FAIL")
                    logs.append("Task failed.")
                    return {
                        "status": "fail",
                        "actions": [],
                        "logs": logs,
                        "info": info,
                        "plan": info.get("plan", "")
                    }
            
            if not action or len(action) == 0:
                print("No actions returned")
                logs.append("I've completed what I can see to do.")
                # Treat as done or wait? Usually done if no actions.
                return {
                    "status": "done",
                    "actions": [],
                    "logs": logs,
                    "info": info,
                    "plan": info.get("plan", "")
                }
            
            # Execute actions
            for act in action:
                act_upper = act.strip().upper()
                if act_upper in ["DONE", "FAIL", "WAIT", "SCROLL", "SCREENSHOT"]:
                    continue
                
                actions_executed.append(act)
                
                try:
                    print(f"  Executing: {act}")
                    
                    # Sanitize
                    sanitized_act = act
                    sanitized_act = sanitized_act.replace("import subprocess", "pass")
                    sanitized_act = sanitized_act.replace("subprocess.run", "# subprocess.run")
                    sanitized_act = sanitized_act.replace("import pyautogui;", "pass;")
                    sanitized_act = sanitized_act.replace("import pyautogui", "pass")

                    # Interceptor
                    lower_act = sanitized_act.lower()
                    if "hotkey('win')" in lower_act and ("write('firefox')" in lower_act or "write('chrome')" in lower_act):
                            print("  >>> INTERCEPTING: Converting broken 'Start Menu' launch to direct launch() <<<")
                            app_name = "firefox" if "firefox" in lower_act else "google-chrome"
                            sanitized_act = f"pyautogui.launch('{app_name}')"
                    
                    # Execute
                    import subprocess as _subprocess
                    exec_globals = {"pyautogui": self.adapter, "time": time, "subprocess": _subprocess}
                    exec(sanitized_act, exec_globals)
                    
                    executed_actions_count += 1
                    print(f"  Action executed successfully (total: {executed_actions_count})")
                    
                    logs.append(self._get_human_log(act))
                    
                except Exception as e:
                    print(f"  ERROR: Action failed: {e}")
                    logs.append(f"Action error: {str(e)[:100]}")
                
                time.sleep(1.5)
            
            return {
                "status": "continue",
                "actions": actions_executed,
                "logs": logs,
                "info": info,
                "plan": info.get("plan", "")
            }
                
        except Exception as e:
             print(f"Agent predict error: {e}")
             return {"status": "error", "message": str(e)}
