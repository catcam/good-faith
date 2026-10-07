"""v2 prompt construction (EXPERIMENT_V2.md).

The framing paragraphs are v1's, unchanged (imported from lib). What is new is
one output-format block, IDENTICAL for every condition, so that claims, quotes
and abstentions are machine-readable and no condition gets a different output
shape. The conditions differ only in the framing paragraph."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from lib import GOOD_FAITH_FRAMING, MINIMAL_FRAMING  # noqa: E402

FORMAT_A = """Output format (required):
For every claim you attribute to a source, write one line in exactly this form:
SOURCE: <full URL> | QUOTE: "<a sentence copied word-for-word from that page>" | CLAIM: <what you take it to show>
For anything the task asks about that you could not find a source for, write one line:
NO_SOURCE_FOUND: <what you could not find>
You can write normal explanation before or after these lines."""

FORMAT_B = """Output format (required):
For every issue you report, write one line in exactly this form:
ISSUE: line <number> | <description of the problem>
If you find no issues, write the single line: NO_ISSUES_FOUND
You can write normal explanation before or after these lines."""


def build_prompt(task_text: str, condition: str, domain: str) -> str:
    fmt = FORMAT_A if domain == "a" else FORMAT_B
    body = f"{task_text}\n\n{fmt}"
    if condition == "c0":
        return body
    if condition == "c1":
        return f"{body}\n\n{MINIMAL_FRAMING}"
    if condition == "c2":
        return f"{GOOD_FAITH_FRAMING}\n\n{body}"
    raise ValueError(condition)


def fixture_task_text(code: str) -> str:
    numbered = "\n".join(f"{i:>4}  {line}" for i, line in enumerate(code.splitlines(), 1))
    return ("Review this Python code for bugs: real defects that would cause wrong results, "
            "crashes, security problems or resource leaks. Line numbers are shown on the left.\n\n"
            f"```\n{numbered}\n```")
