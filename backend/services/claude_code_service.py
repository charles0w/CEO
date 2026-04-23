import subprocess


class ClaudeCodeService:
    def run(self, prompt: str, working_directory: str = "") -> str:
        """Run Claude Code CLI in non-interactive mode and return the output."""
        cwd = working_directory or None
        try:
            result = subprocess.run(
                ["claude", "--print", prompt],
                capture_output=True, text=True, timeout=120, cwd=cwd
            )
            out = result.stdout.strip()
            if result.returncode != 0 and result.stderr:
                out += f"\n[stderr]: {result.stderr.strip()}"
            return out or "No output."
        except FileNotFoundError:
            return "Claude Code CLI not found. Make sure 'claude' is in PATH."
        except subprocess.TimeoutExpired:
            return "Claude Code timed out after 120 seconds."
        except Exception as e:
            return f"Error: {e}"

    def get_status_and_diff(self, working_directory: str = "") -> str:
        cwd = working_directory or None
        try:
            status = subprocess.run(
                ["git", "status", "--short"], capture_output=True, text=True, cwd=cwd
            ).stdout.strip()
            stat = subprocess.run(
                ["git", "diff", "--stat"], capture_output=True, text=True, cwd=cwd
            ).stdout.strip()
            diff = subprocess.run(
                ["git", "diff"], capture_output=True, text=True, cwd=cwd
            ).stdout.strip()
            staged = subprocess.run(
                ["git", "diff", "--cached"], capture_output=True, text=True, cwd=cwd
            ).stdout.strip()
            full_diff = staged or diff
            return (
                f"=== Git Status ===\n{status}\n\n"
                f"=== Changed Files ===\n{stat}\n\n"
                f"=== Diff (first 4000 chars) ===\n{full_diff[:4000]}"
            )
        except Exception as e:
            return f"Error getting git status: {e}"

    def git_commit(self, commit_message: str, working_directory: str = "") -> str:
        """Stage all changes and commit. Only call after user confirmation."""
        cwd = working_directory or None
        try:
            subprocess.run(["git", "add", "-A"], capture_output=True, cwd=cwd, check=True)
            result = subprocess.run(
                ["git", "commit", "-m", commit_message],
                capture_output=True, text=True, cwd=cwd
            )
            return result.stdout.strip() or result.stderr.strip()
        except subprocess.CalledProcessError as e:
            return f"Commit failed: {e.stderr}"
        except Exception as e:
            return f"Error: {e}"

    def git_push(self, working_directory: str = "") -> str:
        """Push to remote. Only call after user confirmation."""
        cwd = working_directory or None
        try:
            result = subprocess.run(
                ["git", "push"], capture_output=True, text=True, cwd=cwd
            )
            return result.stdout.strip() or result.stderr.strip()
        except Exception as e:
            return f"Error: {e}"
