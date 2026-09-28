import asyncio
import sys
import unittest
from tests.test_nlp import test_nlp_rule_parser
from tests.test_policy_tools import test_policy_high_risk_gate
from tests.test_planner_execution import test_full_state_machine_flow
from voice.wake_word import WakeWordListener
from nlp.inference.engine import InferenceEngine
from nlp.agents.multi_agent_engine import MultiAgentNetwork
from core.planner.planner import TaskPlanner
from storage.models import Task

def run_all_tests():
    print("========================================")
    print(" RUNNING MAGNAS AI INTEGRATION TESTS")
    print("========================================")

    # 1. Test NLP Parser
    print("[1/6] Testing NLP Rule Parser...")
    test_nlp_rule_parser()
    print("  [OK] NLP Parser tests passed.")

    # 2. Test Policy Gate
    print("[2/6] Testing Policy Engine & Approvals...")
    test_policy_high_risk_gate()
    print("  [OK] Policy Engine tests passed.")

    # 3. Test Full State Machine Flow
    print("[3/6] Testing Task State Machine Flow...")
    asyncio.run(test_full_state_machine_flow())
    print("  [OK] Task State Machine flow passed.")

    # 4. Test Wake Word Listener
    print("[4/6] Testing Wake Word Engine Parsing...")
    listener = WakeWordListener()
    cmd1 = listener.process_text_for_wake_word("hey magnas open chrome")
    assert cmd1 == "open chrome", f"Expected 'open chrome', got '{cmd1}'"
    cmd2 = listener.process_text_for_wake_word("magnas search youtube")
    assert cmd2 == "search youtube", f"Expected 'search youtube', got '{cmd2}'"
    print("  [OK] Wake Word Engine tests passed.")

    # 5. Test Conversational Voice Chat, Antigravity IDE & Multi-Step Planner
    print("[5/6] Testing Conversational Chat, Progress Query & Antigravity IDE Multi-Step Planning...")
    nlp = InferenceEngine()
    parsed_greet = nlp.parse("hi magnas")
    assert parsed_greet["intent"] == "GREETING", f"Expected GREETING, got {parsed_greet['intent']}"

    parsed_prog = nlp.parse("tell me progress")
    assert parsed_prog["intent"] == "GET_PROGRESS", f"Expected GET_PROGRESS, got {parsed_prog['intent']}"

    parsed_ag = nlp.parse("develop a react task app using antigravity ide")
    assert parsed_ag["intent"] == "DEVELOP_PROJECT_ANTIGRAVITY", f"Expected DEVELOP_PROJECT_ANTIGRAVITY, got {parsed_ag['intent']}"
    
    planner = TaskPlanner()
    task_greet = Task(task_id="t_g", raw_prompt="hi magnas", intent=parsed_greet["intent"], entities=parsed_greet["entities"])
    greet_steps = planner.plan_task(task_greet)
    assert len(greet_steps) == 1 and greet_steps[0].tool_name == "speak_response"

    task_prog = Task(task_id="t_p", raw_prompt="tell me progress", intent=parsed_prog["intent"], entities=parsed_prog["entities"])
    prog_steps = planner.plan_task(task_prog)
    assert len(prog_steps) == 1 and prog_steps[0].tool_name == "get_task_progress"

    task_ag = Task(task_id="t_ag", raw_prompt="develop a react task app using antigravity ide", intent=parsed_ag["intent"], entities=parsed_ag["entities"])
    steps = planner.plan_task(task_ag)
    assert len(steps) == 4, f"Expected 4 plan steps, got {len(steps)}"
    assert steps[2].tool_name == "develop_project_in_antigravity"
    print("  [OK] Conversational Voice Chat, Progress Query & 4-Step Planner tests passed.")


    # 6. Test 11-Micro-Agent Classifier Network
    print("[6/6] Testing 11-Micro-Agent Network Classifiers...")
    multi_net = MultiAgentNetwork()
    res_os = multi_net.predict("launch notepad")
    assert res_os["intent"] == "OPEN_APP", f"Expected OPEN_APP, got {res_os['intent']}"

    res_sql = multi_net.predict("query database select from tasks")
    assert res_sql["intent"] == "QUERY_DATABASE", f"Expected QUERY_DATABASE, got {res_sql['intent']}"

    res_media = multi_net.predict("read screen text ocr screenshot")
    assert res_media["intent"] == "READ_SCREEN_TEXT", f"Expected READ_SCREEN_TEXT, got {res_media['intent']}"

    res_timer = multi_net.predict("set timer reminder for meeting in 60 seconds")
    assert res_timer["intent"] == "SET_TIMER_REMINDER", f"Expected SET_TIMER_REMINDER, got {res_timer['intent']}"
    print("  [OK] 11-Micro-Agent Network predictions verified successfully.")

    print("\n========================================")
    print(" ALL MAGNAS AI TESTS PASSED SUCCESSFULLY!")
    print("========================================")

if __name__ == "__main__":
    run_all_tests()
