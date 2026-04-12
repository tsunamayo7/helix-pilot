# First comment (post immediately after submission)

Author here. Thanks for checking it out. Three concerns I'd expect upfront, so let me address them honestly.

## Q1: "Isn't giving an LLM raw keyboard/mouse control a security nightmare?"

Fair. The answer is not "trust the model" but "put the model inside a default-deny policy contract." The policy layer lives in `src/tools/pilot_action_contract.py` and is enforced by `SafetyGuard` in `scripts/helix_pilot.py` (~line 500); every action goes through both before PyAutoGUI fires.

Concretely:

- **Four execution modes**: `observe_only` (no mutating actions at all), `draft_only` (default — plan + execute reversible actions, but `submit` / `publish` / `final-submit` are blocked), `apply_with_approval` (mutating actions require an approval callback), and `publish_human_final` (human has to push the final button themselves).
- **Site policies** you pick per target: `helix_internal`, `browser_general_observe`, `github_release_draft`, `x_draft_only`, `reddit_draft_only`, `hn_draft_only`. Each one is an allowlist/denylist of actions plus "require approval" hooks on sensitive ones like `browse` and `type`.
- **Window denylist** out of the box: Windows Security, Task Manager, anything starting with `Administrator:`, Password/Credential dialogs, Windows Defender. Plus an optional `allowed_windows` allowlist — if you set it, anything not matching is refused.
- **Secret scrubbing on typed text**: input through `type_text` is regex-checked against `sk-[A-Za-z0-9]{20,}`, `ghp_[A-Za-z0-9]{20,}`, `AIza[0-9A-Za-z\-_]{20,}` plus substrings `password`, `credential`, `secret`, `api_key`, `token`. Paths containing `.env` or `secrets/` are refused. This is the `immutable_policy` — site configs can't override it.
- **Emergency stop**: fling the mouse into a screen corner (default top-left, 5px) and the next action raises `PilotEmergencyStop`. User activity detection via `pynput` also pauses execution when you start typing.

None of this replaces running sensitive stuff in a VM. It does mean the LLM operates against a narrow, allow-listed surface, not your whole desktop.

## Q2: "Local vision on screenshots must be slow and brittle — what about DPI changes or UI state?"

Yes to the first half, and the design tries to work with that. A `find` call (screenshot -> encode -> Ollama Vision -> parse JSON) takes on the order of a couple of seconds on an RTX 5070 Ti with `mistral-small3.2`; bigger models are slower. I haven't published formal benchmarks — it's model- and GPU-dependent.

The mitigations are:

- **Coordinate-free targeting**. `find("the Save button in the toolbar")` returns the element center from the Vision LLM, then `click_screenshot` fires and grabs the post-click screenshot in one call. Raw `click(x, y)` exists but isn't how the autonomous loops drive things.
- **verify as a primitive**. After every mutating step, the `auto` loop can call `verify("the save dialog is gone")` and get a JSON yes/no with explanation. If the model disagrees with the expectation, the step fails instead of plowing forward.
- **wait_stable** polls until pixels stop changing, better than a fixed sleep for animating menus.
- **DPI / resolution**. The `find` prompt is parameterized on the actual screenshot dimensions ("this screen is 3840x2160, taskbar at the bottom"). Not magic — if the model is wrong, the click misses. That's why `verify` exists.
- **explorer role**. `agent_type="explorer"` runs in `dry_run` — pure observation and planning, no clicks. Good for scoping a new workflow before you trust it.

It's slower than a Playwright selector. It also works on native Windows apps whose source you don't own.

## Q3: "Why use this over Playwright / UIAutomation / AutoHotkey / a VM?"

The honest answer is: most of the time, use one of those. helix-pilot is for a narrow slot:

- **Playwright**: if your target is a web page, use Playwright. Faster, more reliable, real selectors. helix-pilot is for when there is no browser surface.
- **Windows UIAutomation / accessibility APIs**: strictly better when they work — real introspectable element trees. They fall apart on apps that render their own UI (Electron inconsistencies, custom DirectX/OpenGL canvases, older Win32 apps without accessibility metadata). Visual-only is a fallback for those cases.
- **AutoHotkey**: great for static scripted macros. helix-pilot is the opposite — workflow isn't known ahead of time and an LLM has to decide based on what's on screen.
- **VM-based agents (Cua, etc.)**: isolate the whole OS, which is safer but also means they can't touch your real Premiere project or Excel workbook. helix-pilot drives the host you're working on.

Concrete uses: walking an LLM through Windows Settings panels that have no API, kicking off a Premiere Pro sequence for clip intake, and a "clean this messy spreadsheet" loop in Excel where the model observes, decides, clicks, verifies. All MCP-driven, all local.

So: Windows-only, Ollama-only, slower than selectors, firmly in the "last resort when the app has no real API" category. Happy to answer anything else.

---

Repo: https://github.com/tsunamayo7/helix-pilot
Safety layer source: https://github.com/tsunamayo7/helix-pilot/blob/main/src/tools/pilot_action_contract.py
SafetyGuard + emergency stop: https://github.com/tsunamayo7/helix-pilot/blob/main/scripts/helix_pilot.py
