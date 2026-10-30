"""Tools available to the agent within the example workspace."""

from pathlib import Path
import subprocess
import sys

WORKSPACE_DIR = Path(__file__).resolve().parent / "examples" / "buggy_calculator"


def read_file(path: str) -> dict:
    """Read a text file within the example workspace."""
    file_path = (WORKSPACE_DIR / path).resolve()
    if not file_path.is_relative_to(WORKSPACE_DIR.resolve()):
        return {"ok": False, "error": "Path must be inside the workspace."}
    try:
        content = file_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return {"ok": False, "error": f"Could not read file: {exc}"}
    return {"ok": True, "path": path, "content": content}


def run_tests() -> dict:
    """Run the example's tests and return their output."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "test_calculator.py"],
            cwd=WORKSPACE_DIR,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "Test run timed out after 10 seconds."}
    except OSError as exc:
        return {"ok": False, "error": f"Could not start tests: {exc}"}
    return {
        "ok": result.returncode == 0,
        "exit_code": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


TOOL_DEFINITIONS = [
    {
        "name": "read_file",
        "description": "Read a text file in the example workspace.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path relative to the example workspace, e.g. calculator.py.",
                }
            },
            "required": ["path"],
            "additionalProperties": False,
        },
    },
    {
        "name": "run_tests",
        "description": "Run the example's pytest tests and return their output and exit code.",
        "parameters": {"type": "object", "properties": {}, "required": [], "additionalProperties": False},
    },
]

TOOL_FUNCTIONS = {"read_file": read_file, "run_tests": run_tests}
