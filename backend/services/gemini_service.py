import asyncio
from datetime import datetime
from google import genai
from google.genai import types
from config import settings
from services.obsidian_service import ObsidianService
from services.github_service import GitHubService
from services.claude_code_service import ClaudeCodeService

CEO_SYSTEM_PROMPT = """You are CEO, Charles's personal AI executive assistant — Tony Stark's JARVIS, but called CEO.
You are highly capable, direct, and proactive. You may address Charles as "Boss" occasionally.
Today: {date}

You have tools for:
- Charles's Obsidian vault (obi-secondbrain): read, write, search notes
- GitHub: list repos, get repo info, list issues, read files
- Claude Code CLI: run development prompts (this uses Claude tokens, so use judiciously)
- Git: commit and push changes

GIT SAFETY PROTOCOL — non-negotiable:
1. Before ANY commit or push, call get_git_status_and_diff() first
2. Present to Charles: what files changed, what the changes do, any risks
3. Ask explicitly: "Shall I proceed with the commit/push?"
4. Only call git_commit() or git_push() after Charles confirms with "yes", "confirm", "do it", etc.
Never skip this protocol."""

_obsidian = ObsidianService()
_github = GitHubService()
_claude_code = ClaudeCodeService()


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
    """Push commits to remote. ONLY call after receiving explicit confirmation from Charles."""
    return _claude_code.git_push(working_directory)


TOOLS = [
    list_obsidian_notes, read_obsidian_note, write_obsidian_note, search_obsidian_vault,
    list_github_repos, get_github_repo_info, list_github_issues, get_github_file,
    run_claude_code, get_git_status_and_diff, git_commit, git_push,
]


class GeminiService:
    def __init__(self):
        self.client = genai.Client(api_key=settings.gemini_api_key)
        self._new_chat()

    def _new_chat(self):
        self.chat = self.client.chats.create(
            model="gemini-2.0-flash",
            config=types.GenerateContentConfig(
                system_instruction=CEO_SYSTEM_PROMPT.format(
                    date=datetime.now().strftime("%A, %B %d %Y")
                ),
                tools=TOOLS,
            ),
        )

    async def send(self, message: str) -> str:
        loop = asyncio.get_event_loop()
        try:
            response = await loop.run_in_executor(None, self.chat.send_message, message)
            return response.text or "[No response]"
        except Exception as e:
            return f"CEO Error: {e}"

    def reset(self) -> str:
        self._new_chat()
        return "Conversation cleared. Ready for your next command, Boss."
