import unittest
from unittest.mock import patch

from src.pilot import HelixPilot, PilotConfig
from helix_pilot import ActionValidator


class _DummyWindow:
    def __init__(self, title, left, top, width, height):
        self.title = title
        self.left = left
        self.top = top
        self.width = width
        self.height = height


class _Formatter:
    @staticmethod
    def format(payload):
        return payload


class TestPilotRuntimeHelpers(unittest.TestCase):
    def test_collect_visible_windows_supports_geometry(self):
        pilot = HelixPilot.__new__(HelixPilot)
        wins = [
            _DummyWindow("App One", 10, 20, 300, 400),
            _DummyWindow("", 0, 0, 500, 500),
            _DummyWindow("Too Small", 1, 2, 50, 60),
        ]
        with patch("helix_pilot.gw.getAllWindows", return_value=wins):
            titles = pilot._collect_visible_windows()
            detailed = pilot._collect_visible_windows(detailed=True)

        self.assertEqual(titles, ["App One"])
        self.assertEqual(detailed, [{
            "title": "App One",
            "left": 10,
            "top": 20,
            "width": 300,
            "height": 400,
        }])

    def test_cmd_list_windows_returns_titles_and_windows(self):
        pilot = HelixPilot.__new__(HelixPilot)
        pilot.formatter = _Formatter()
        pilot._now = lambda: "2026-03-24T00:00:00.000"

        with patch.object(HelixPilot, "_collect_visible_windows",
                          side_effect=[["App One"], [{
                              "title": "App One",
                              "left": 10,
                              "top": 20,
                              "width": 300,
                              "height": 400,
                          }]]):
            result = pilot.cmd_list_windows()

        self.assertEqual(result["visible_windows"], ["App One"])
        self.assertEqual(result["windows"][0]["width"], 300)

    def test_action_validator_allows_internal_screenshot_action(self):
        validator = ActionValidator(PilotConfig())
        ok, reason = validator.validate({"action": "screenshot", "name": "auto_capture"})
        self.assertTrue(ok)
        self.assertEqual(reason, "ok")


if __name__ == "__main__":
    unittest.main()
