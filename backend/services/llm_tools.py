import json
from datetime import datetime
from typing import Any, Callable

from services.claude_code_service import ClaudeCodeService
from services.github_service import GitHubService
from services.obsidian_service import ObsidianService

CEO_SYSTEM_PROMPT = """You are CEO, Charles's personal AI executive assistant - Tony Stark's JARVIS, but called CEO.
You are highly capable, direct, and proactive. You may address Charles as "Boss" occasionally.
Today: {date}

You have tools for:
- Charles's Obsidian vault (obi-secondbrain): read, write, search notes
- GitHub: list repos, get repo info, list issues, read files
- Claude Code CLI: run development prompts (this uses Claude tokens, so use judiciously)
- Git: commit and push changes

GIT SAFETY PROTOCOL - non-negotiable:
1. Before ANY commit or push, call get_git_status_and_diff() first
2. Present to Charles: what files changed, what the changes do, any risks
3. Ask explicitly: "Shall I proceed with the commit/push?"
4. Only call git_commit() or git_push() after Charles confirms with "yes", "confirm", "do it", etc.
Never skip this protocol."""

_obsidian = ObsidianService()
_github = GitHubService()
_claude_code = ClaudeCodeService()


def build_system_prompt() -> str:
    return CEO_SYSTEM_PROMPT.format(date=datetime.now().strftime("%A, %B %d %Y"))


def list_obsidian_notes(path: str = "") -> str:
    """List notes in Charles's Obsidian vault. path is relative to vault root, empty for all."""
    return _obsidian.list_notes(path)


def read_obsidian_note(note_path: str) -> str:
    """Read the full content of an Obsidian note by its relative path (e.g. 'Projects/CEO.md')."""
    return _obsidian.read_note(note_path)


def write_obsidian_note(note_path: str, content: str) -> str:
    """Write or update an Obsidian note. Creates the file and any parent directories if needed."""
    return _obsidian.write_note(note_path, content)


def search_obsidian_vault(query: str) -> str:
    """Search Charles's Obsidian vault for notes containing the query text."""
    return _obsidian.search_notes(query)


def list_github_repos() -> str:
    """List all of Charles's GitHub repositories."""
    return _github.list_repos()


def get_github_repo_info(repo_name: str) -> str:
    """Get details about a specific GitHub repository."""
    return _github.get_repo_info(repo_name)


def list_github_issues(repo_name: str, state: str = "open") -> str:
    """List issues in a GitHub repo. state: 'open', 'closed', or 'all'."""
    return _github.list_issues(repo_name, state)


def get_github_file(repo_name: str, file_path: str) -> str:
    """Get the content of a file from a GitHub repository."""
    return _github.get_file_content(repo_name, file_path)


def run_claude_code(prompt: str, working_directory: str = "") -> str:
    """Run Claude Code CLI with a development prompt. Returns CLI output. Uses Claude tokens."""
    return _claude_code.run(prompt, working_directory)


def get_git_status_and_diff(working_directory: str = "") -> str:
    """Get the current git status and full diff. ALWAYS call this before any commit or push."""
    return _claude_code.get_status_and_diff(working_directory)


def git_commit(commit_message: str, working_directory: str = "") -> str:
    """Stage all changes and commit. ONLY call after presenting diff to Charles and receiving explicit confirmation."""
    return _claude_code.git_commit(commit_message, working_directory)


def git_push(working_directory: str = "") -> str:
    """Push to remote. ONLY call after receiving explicit confirmation from Charles."""
    return _claude_code.git_push(working_directory)


GEMINI_TOOLS = [
    list_obsidian_notes,
    read_obsidian_note,
    write_obsidian_note,
    search_obsidian_vault,
    list_github_repos,
    get_github_repo_info,
    list_github_issues,
    get_github_file,
    run_claude_code,
    get_git_status_and_diff,
    git_commit,
    git_push,
]

AVAILABLE_TOOL_FUNCTIONS: dict[str, Callable[..., str]] = {
    tool.__name__: tool for tool in GEMINI_TOOLS
}


def _schema(
    name: str,
    description: str,
    properties: dict[str, dict[str, Any]],
    required: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required or [],
            },
        },
    }


OLLAMA_TOOLS = [
    _schema(
        "list_obsidian_notes",
        "List notes in Charles's Obsidian vault. path is relative to vault root, empty for all.",
        {"path": {"type": "string", "description": "Path relative to the Obsidian vault root."}},
    ),
    _schema(
        "read_obsidian_note",
        "Read the full content of an Obsidian note by its relative path.",
        {"note_path": {"type": "string", "description": "Relative note path, e.g. Projects/CEO.md."}},
        ["note_path"],
    ),
    _schema(
        "write_obsidian_note",
        "Write or update an Obsidian note. Creates the file and any parent directories if needed.",
        {
            "note_path": {"type": "string", "description": "Relative note path to write."},
            "content": {"type": "string", "description": "Full note content."},
        },
        ["note_path", "content"],
    ),
    _schema(
        "search_obsidian_vault",
        "Search Charles's Obsidian vault for notes containing the query text.",
        {"query": {"type": "string", "description": "Text to search for in the vault."}},
        ["query"],
    ),
    _schema("list_github_repos", "List all of Charles's GitHub repositories.", {}),
    _schema(
        "get_github_repo_info",
        "Get details about a specific GitHub repository.",
        {"repo_name": {"type": "string", "description": "Repository name."}},
        ["repo_name"],
    ),
    _schema(
        "list_github_issues",
        "List issues in a GitHub repo.",
        {
            "repo_name": {"type": "string", "description": "Repository name."},
            "state": {"type": "string", "description": "Issue state: open, closed, or all."},
        },
        ["repo_name"],
    ),
    _schema(
        "get_github_file",
        "Get the content of a file from a GitHub repository.",
        {
            "repo_name": {"type": "string", "description": "Repository name."},
            "file_path": {"type": "string", "description": "Path to the file in the repository."},
        },
        ["repo_name", "file_path"],
    ),
    _schema(
        "run_claude_code",
        "Run Claude Code CLI with a development prompt. Returns CLI output. Uses Claude tokens.",
        {
            "prompt": {"type": "string", "description": "Development prompt to run via Claude Code."},
            "working_directory": {"type": "string", "description": "Optional working directory for the command."},
        },
        ["prompt"],
    ),
    _schema(
        "get_git_status_and_diff",
        "Get the current git status and full diff. ALWAYS call this before any commit or push.",
        {"working_directory": {"type": "string", "description": "Optional git working directory."}},
    ),
    _schema(
        "git_commit",
        "Stage all changes and commit. ONLY call after presenting diff to Charles and receiving explicit confirmation.",
        {
            "commit_message": {"type": "string", "description": "Commit message."},
            "working_directory": {"type": "string", "description": "Optional git working directory."},
        },
        ["commit_message"],
    ),
    _schema(
        "git_push",
        "Push to remote. ONLY call after receiving explicit confirmation from Charles.",
        {"working_directory": {"type": "string", "description": "Optional git working directory."}},
    ),
]


def invoke_tool(tool_name: str, arguments: Any) -> str:
    if tool_name not in AVAILABLE_TOOL_FUNCTIONS:
        return f"Unknown tool: {tool_name}"

    if arguments is None:
        parsed_arguments: dict[str, Any] = {}
    elif isinstance(arguments, dict):
        parsed_arguments = arguments
    elif isinstance(arguments, str):
        try:
            parsed_arguments = json.loads(arguments) if arguments.strip() else {}
        except json.JSONDecodeError as exc:
            return f"Invalid tool arguments for {tool_name}: {exc}"
    else:
        return f"Invalid tool arguments for {tool_name}: expected object, got {type(arguments).__name__}"

    try:
        return AVAILABLE_TOOL_FUNCTIONS[tool_name](**parsed_arguments)
    except TypeError as exc:
        return f"Tool call failed for {tool_name}: {exc}"
    except Exception as exc:  # pragma: no cover - defensive runtime guard
        return f"Tool call failed for {tool_name}: {exc}"
