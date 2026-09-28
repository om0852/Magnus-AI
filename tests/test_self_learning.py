import os
import sys
import unittest
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from core.memory.self_learning import self_learning_engine
from nlp.inference.engine import InferenceEngine
from core.planner.planner import TaskPlanner
from storage.models import Task

class TestSelfLearning(unittest.TestCase):
    def test_learn_and_match(self):
        engine = InferenceEngine()
        # Learn a custom pattern correction
        pattern = "open firefox go to apify console"
        intent = "OPEN_WEBSITE"
        tool = "open_url"
        params = {"url": "https://console.apify.com"}

        res = self_learning_engine.learn_correction(pattern, intent, tool, params)
        self.assertIn("Successfully saved", res)

        # Test matching in self_learning_engine
        match = self_learning_engine.match_prompt("open firefox go to apify console")
        self.assertIsNotNone(match)
        self.assertEqual(match["intent"], "OPEN_WEBSITE")
        self.assertEqual(match["confidence"], 1.0)
        self.assertEqual(match["entities"]["url"], "https://console.apify.com")

        # Test NLP Engine parsing with learned rule
        parsed = engine.parse("open firefox go to apify console")
        self.assertEqual(parsed["intent"], "OPEN_WEBSITE")

        # Clean up learned rule
        rule_id = match["learned_rule_id"]
        forget_res = self_learning_engine.forget_rule(rule_id)
        self.assertIn("Successfully deleted", forget_res)

        # Verify rule no longer matches
        match_after = self_learning_engine.match_prompt("open firefox go to apify console")
        self.assertIsNone(match_after)

if __name__ == "__main__":
    unittest.main()
