import uuid
from typing import List, Dict, Any
from storage.models import Task, PlanStep, RiskLevel

class TaskPlanner:
    """Decomposes intent and parameters into ordered PlanStep sequences with explicit verification stages."""

    def plan_task(self, task: Task) -> List[PlanStep]:
        intent = task.intent
        entities = task.entities or {}
        steps: List[PlanStep] = []

        if intent == "COMPOUND_TASK":
            sub_tasks = entities.get("sub_tasks", [])
            for sub in sub_tasks:
                sub_intent = sub.get("intent")
                sub_entities = sub.get("entities", {})
                sub_steps = self._plan_single_intent(sub_intent, sub_entities, task.raw_prompt)
                steps.extend(sub_steps)

        else:
            steps = self._plan_single_intent(intent, entities, task.raw_prompt)

        task.steps = steps
        return steps

    def _plan_single_intent(self, intent: str, entities: dict, raw_prompt: str) -> List[PlanStep]:
        steps = []
        if intent == "GREETING":
            msg = entities.get("message", "Hello! I am Magnas, your AI assistant. How can I help you today?")
            steps.append(PlanStep(
                step_id=f"step_{uuid.uuid4().hex[:6]}",
                tool_name="speak_response",
                parameters={"message": msg},
                description="Step 1/1 (Voice Chat): Respond out loud to user greeting",
                risk_level=RiskLevel.LOW
            ))

        elif intent == "GET_PROGRESS":
            steps.append(PlanStep(
                step_id=f"step_{uuid.uuid4().hex[:6]}",
                tool_name="get_task_progress",
                parameters={},
                description="Step 1/1 (Status Report): Query active task & speak progress update",
                risk_level=RiskLevel.LOW
            ))

        elif intent == "OPEN_APP":

            app = entities.get("application", "notepad")
            steps.append(PlanStep(
                step_id=f"step_{uuid.uuid4().hex[:6]}",
                tool_name="open_application",
                parameters={"application": app},
                description=f"Step 1/1 (Execution): Open application '{app}'",
                risk_level=RiskLevel.LOW
            ))

        elif intent == "CLOSE_APP":
            app = entities.get("application", "")
            steps.append(PlanStep(
                step_id=f"step_{uuid.uuid4().hex[:6]}",
                tool_name="close_application",
                parameters={"application": app},
                description=f"Step 1/1 (Execution): Terminate process '{app}'",
                risk_level=RiskLevel.MEDIUM
            ))

        elif intent == "DEVELOP_PROJECT_ANTIGRAVITY":
            proj_name = entities.get("project_name", "new_antigravity_project")
            prompt_str = entities.get("prompt", raw_prompt)

            steps.append(PlanStep(
                step_id=f"step_{uuid.uuid4().hex[:6]}",
                tool_name="list_directory",
                parameters={"path": "."},
                description="Step 1/4 (Workspace Prep): Initialize project workspace & check local files",
                risk_level=RiskLevel.LOW
            ))
            steps.append(PlanStep(
                step_id=f"step_{uuid.uuid4().hex[:6]}",
                tool_name="open_application",
                parameters={"application": "antigravity ide"},
                description="Step 2/4 (IDE Activation): Launch & focus Antigravity IDE workstation",
                risk_level=RiskLevel.LOW
            ))
            steps.append(PlanStep(
                step_id=f"step_{uuid.uuid4().hex[:6]}",
                tool_name="develop_project_in_antigravity",
                parameters={"prompt": prompt_str, "project_name": proj_name, "slash_command": "/goal"},
                description=f"Step 3/4 (IDE Control): Instruct Antigravity IDE Chat via /goal to plan, code, build & test '{proj_name}'",
                risk_level=RiskLevel.MEDIUM
            ))
            steps.append(PlanStep(
                step_id=f"step_{uuid.uuid4().hex[:6]}",
                tool_name="verify_task_output",
                parameters={"path": "."},
                description="Step 4/4 (Verification): Verify Antigravity IDE project generation & build completion",
                risk_level=RiskLevel.LOW
            ))

        elif intent == "DESIGN_RESUME":
            name = entities.get("name", "Om Salunke")
            title = entities.get("title", "FULL STACK JAVA DEVELOPER")
            
            # Step 1: Search local system for existing resume files or profile documents
            steps.append(PlanStep(
                step_id=f"step_{uuid.uuid4().hex[:6]}",
                tool_name="search_files",
                parameters={"query": "resume"},
                description="Step 1/4 (Scan & Analyze): Search local disk for previous resume/CV files",
                risk_level=RiskLevel.LOW
            ))

            # Step 2: Search web / LinkedIn for candidate profile and skills context
            steps.append(PlanStep(
                step_id=f"step_{uuid.uuid4().hex[:6]}",
                tool_name="browser_search",
                parameters={"query": f"{name} LinkedIn full stack developer profile skills", "site": "google"},
                description=f"Step 2/4 (Gathering): Gather profile details, LinkedIn experience, and skills",
                risk_level=RiskLevel.LOW
            ))

            # Step 3: Design professional Word resume
            steps.append(PlanStep(
                step_id=f"step_{uuid.uuid4().hex[:6]}",
                tool_name="design_resume_in_word",
                parameters={"name": name, "title": title},
                description=f"Step 3/4 (Generation): Synthesize details & build formatted Word resume for '{title}'",
                risk_level=RiskLevel.MEDIUM
            ))

            # Step 4: Verification
            steps.append(PlanStep(
                step_id=f"step_{uuid.uuid4().hex[:6]}",
                tool_name="verify_task_output",
                parameters={"path": "latest_resume"},
                description="Step 4/4 (Verification): Verify resume document integrity & disk presence",
                risk_level=RiskLevel.LOW
            ))

        elif intent == "AUTOMATE_DAILY_TASKS" or "daily" in raw_prompt.lower() or "automation" in raw_prompt.lower():
            steps.append(PlanStep(
                step_id=f"step_{uuid.uuid4().hex[:6]}",
                tool_name="execute_command",
                parameters={"command": "systeminfo"},
                description="Step 1/4 (Diagnostic): Check system status & hardware resource metrics",
                risk_level=RiskLevel.HIGH
            ))
            steps.append(PlanStep(
                step_id=f"step_{uuid.uuid4().hex[:6]}",
                tool_name="list_directory",
                parameters={"path": "."},
                description="Step 2/4 (Scan): Scan active workspace directory contents",
                risk_level=RiskLevel.LOW
            ))
            steps.append(PlanStep(
                step_id=f"step_{uuid.uuid4().hex[:6]}",
                tool_name="take_screenshot",
                parameters={},
                description="Step 3/4 (Snapshot): Capture desktop workstation screenshot",
                risk_level=RiskLevel.LOW
            ))
            steps.append(PlanStep(
                step_id=f"step_{uuid.uuid4().hex[:6]}",
                tool_name="verify_task_output",
                parameters={"path": "."},
                description="Step 4/4 (Verification): Verify automated task completion & metrics",
                risk_level=RiskLevel.LOW
            ))

        elif intent == "SEARCH_WEB":
            query = entities.get("query", "")
            site = entities.get("site", "google")
            steps.append(PlanStep(
                step_id=f"step_{uuid.uuid4().hex[:6]}",
                tool_name="browser_search",
                parameters={"query": query, "site": site},
                description=f"Step 1/2 (Search): Search '{query}' on {site}",
                risk_level=RiskLevel.LOW
            ))
            steps.append(PlanStep(
                step_id=f"step_{uuid.uuid4().hex[:6]}",
                tool_name="verify_task_output",
                parameters={"path": "."},
                description=f"Step 2/2 (Verification): Verify search query results",
                risk_level=RiskLevel.LOW
            ))

        elif intent == "SEARCH_FILES":
            query = entities.get("query", "resume")
            steps.append(PlanStep(
                step_id=f"step_{uuid.uuid4().hex[:6]}",
                tool_name="search_files",
                parameters={"query": query},
                description=f"Step 1/1 (Search): Search local files matching '{query}'",
                risk_level=RiskLevel.LOW
            ))

        elif intent == "OPEN_WEBSITE":
            url = entities.get("url", "https://google.com")
            steps.append(PlanStep(
                step_id=f"step_{uuid.uuid4().hex[:6]}",
                tool_name="open_url",
                parameters={"url": url},
                description=f"Step 1/1 (Execution): Navigate browser to '{url}'",
                risk_level=RiskLevel.LOW
            ))

        elif intent == "READ_FILE":
            path = entities.get("path", "")
            if not path or path == ".":
                tool_n = "list_directory"
                params = {"path": "."}
                desc = "Step 1/1 (Execution): List current directory files"
            else:
                tool_n = "read_file"
                params = {"path": path}
                desc = f"Step 1/1 (Execution): Read file '{path}'"

            steps.append(PlanStep(
                step_id=f"step_{uuid.uuid4().hex[:6]}",
                tool_name=tool_n,
                parameters=params,
                description=desc,
                risk_level=RiskLevel.LOW
            ))

        elif intent == "CREATE_FILE":
            path = entities.get("path", "notes.txt")
            content = entities.get("content", "Sample content created by Magnas AI.")
            steps.append(PlanStep(
                step_id=f"step_{uuid.uuid4().hex[:6]}",
                tool_name="create_file",
                parameters={"path": path, "content": content},
                description=f"Step 1/2 (Generation): Write content to file '{path}'",
                risk_level=RiskLevel.MEDIUM
            ))
            steps.append(PlanStep(
                step_id=f"step_{uuid.uuid4().hex[:6]}",
                tool_name="verify_task_output",
                parameters={"path": path},
                description=f"Step 2/2 (Verification): Verify file '{path}' creation & size",
                risk_level=RiskLevel.LOW
            ))

        elif intent == "DELETE_FILE":
            path = entities.get("path", "")
            steps.append(PlanStep(
                step_id=f"step_{uuid.uuid4().hex[:6]}",
                tool_name="delete_file",
                parameters={"path": path},
                description=f"Step 1/1 (Execution): Delete file '{path}' permanently",
                risk_level=RiskLevel.HIGH
            ))

        elif intent == "CHANGE_VOLUME":
            amount = int(entities.get("amount", 10))
            direction = entities.get("direction", "increase")
            steps.append(PlanStep(
                step_id=f"step_{uuid.uuid4().hex[:6]}",
                tool_name="change_volume",
                parameters={"amount": amount, "direction": direction},
                description=f"Step 1/1 (Execution): Adjust volume ({direction} {amount}%)",
                risk_level=RiskLevel.LOW
            ))

        elif intent == "TAKE_SCREENSHOT":
            steps.append(PlanStep(
                step_id=f"step_{uuid.uuid4().hex[:6]}",
                tool_name="take_screenshot",
                parameters={},
                description="Step 1/2 (Snapshot): Capture monitor screenshot",
                risk_level=RiskLevel.LOW
            ))
            steps.append(PlanStep(
                step_id=f"step_{uuid.uuid4().hex[:6]}",
                tool_name="verify_task_output",
                parameters={"path": "."},
                description="Step 2/2 (Verification): Verify screenshot image creation",
                risk_level=RiskLevel.LOW
            ))

        elif intent == "TYPE_TEXT":
            text_str = entities.get("text", "")
            steps.append(PlanStep(
                step_id=f"step_{uuid.uuid4().hex[:6]}",
                tool_name="type_text",
                parameters={"text": text_str},
                description=f"Step 1/1 (Execution): Type text '{text_str}'",
                risk_level=RiskLevel.MEDIUM
            ))

        elif intent == "PRESS_KEY":
            key_str = entities.get("key", "enter")
            steps.append(PlanStep(
                step_id=f"step_{uuid.uuid4().hex[:6]}",
                tool_name="press_key",
                parameters={"key": key_str},
                description=f"Step 1/1 (Execution): Press key '{key_str}'",
                risk_level=RiskLevel.LOW
            ))

        elif intent == "EXECUTE_COMMAND":
            cmd = entities.get("command", "")
            steps.append(PlanStep(
                step_id=f"step_{uuid.uuid4().hex[:6]}",
                tool_name="execute_command",
                parameters={"command": cmd},
                description=f"Step 1/1 (Execution): Execute command '{cmd}'",
                risk_level=RiskLevel.HIGH
            ))

        else:
            steps.append(PlanStep(
                step_id=f"step_{uuid.uuid4().hex[:6]}",
                tool_name="type_text",
                parameters={"text": raw_prompt},
                description=f"Step 1/1 (Execution): Fallback input handling for prompt '{raw_prompt}'",
                risk_level=RiskLevel.LOW
            ))

        return steps
