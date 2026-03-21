# Demo Capture Scenarios v2

These scenarios map the demo plan to `scripts/helix_pilot.py run-scenario`.

Examples:

```powershell
python scripts/helix_pilot.py run-scenario scripts/scenarios/demo_capture_v2/hero_soloai.json
python scripts/helix_pilot.py run-scenario scripts/scenarios/demo_capture_v2/mixai_5phase.json
python scripts/helix_pilot.py run-scenario scripts/scenarios/demo_capture_v2/all_tabs_stills.json
python scripts/helix_pilot.py run-scenario scripts/scenarios/demo_capture_v2/virtual_desktop_sandbox.json
python scripts/helix_pilot.py run-scenario scripts/scenarios/demo_capture_v2/web_ui_browser.json

# JSON Action Schema path
python scripts/run_demo_capture_scenario.py scripts/scenarios/demo_capture_v2/hero_soloai.json --mode draft_only --site-policy helix_internal
```

Notes:

- `hero_soloai.json` demonstrates `find -> click -> type -> screenshot`.
- `mixai_5phase.json` captures the Phase 1 -> 3.5 -> complete flow for mixAI.
- `all_tabs_stills.json` captures the 8 top-level tabs using the `Ctrl+1..8` hotkeys.
- `virtual_desktop_sandbox.json` demonstrates sandbox start/stop flow with dynamic coordinates.
- `web_ui_browser.json` drives the Web UI opening flow through the `browse` action.
- `run-scenario` now supports argument references like `$find_input.x` and `$last.path`.
