"""Tests for the MCP server tool registration."""

import asyncio
import unittest


class TestServerToolRegistration(unittest.TestCase):
    def test_mcp_server_loads(self):
        from server import mcp
        self.assertEqual(mcp.name, "helix-pilot")

    def test_expected_tools_registered(self):
        from server import mcp
        tools = asyncio.run(mcp.list_tools())
        tool_names = {t.name for t in tools}
        expected = {
            "screenshot",
            "click",
            "type_text",
            "hotkey",
            "scroll",
            "describe",
            "find",
            "verify",
            "status",
            "list_windows",
            "wait_stable",
            "auto",
            "browse",
            "click_screenshot",
            "resize_image",
        }
        self.assertTrue(
            expected.issubset(tool_names),
            f"Missing tools: {expected - tool_names}",
        )

    def test_pilot_module_importable(self):
        from src.pilot import create_pilot, PilotConfig
        self.assertTrue(callable(create_pilot))


if __name__ == "__main__":
    unittest.main()
