import unittest

from src.tools.pilot_response_processor import (
    parse_json_action_calls,
    parse_pilot_calls,
)


class TestPilotResponseProcessor(unittest.TestCase):
    def test_parse_legacy_marker(self):
        txt = "hello <<PILOT:click:x=100:y=200:window=Helix AI Studio>> world"
        calls = parse_pilot_calls(txt)
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]["command"], "click")
        self.assertEqual(calls[0]["params"]["x"], "100")

    def test_parse_json_action_block(self):
        txt = """```json
{"action":"screenshot","args":{"window":"Helix AI Studio","name":"shot1"}}
```"""
        calls = parse_json_action_calls(txt)
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]["action"], "screenshot")
        self.assertEqual(calls[0]["request"]["args"]["name"], "shot1")


if __name__ == "__main__":
    unittest.main()

