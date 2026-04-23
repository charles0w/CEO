from config import settings


class GitHubService:
    def __init__(self):
        self._gh = None
        self._user = None

    def _client(self):
        if self._gh is None:
            if not settings.github_token:
                return None
            from github import Github
            self._gh = Github(settings.github_token)
            self._user = self._gh.get_user()
        return self._gh

    def list_repos(self) -> str:
        if not self._client():
            return "GitHub token not set — add GITHUB_TOKEN to backend/.env"
        repos = list(self._user.get_repos())[:30]
        return "\n".join(
            f"{r.name} ({'private' if r.private else 'public'}) — {r.description or 'no description'}"
            for r in repos
        )

    def get_repo_info(self, repo_name: str) -> str:
        if not self._client():
            return "GitHub token not set."
        try:
            r = self._user.get_repo(repo_name)
            return (
                f"Repo: {r.full_name}\nStars: {r.stargazers_count}\n"
                f"Language: {r.language}\nBranch: {r.default_branch}\n"
                f"Open issues: {r.open_issues_count}\nURL: {r.html_url}"
            )
        except Exception as e:
            return f"Error: {e}"

    def list_issues(self, repo_name: str, state: str = "open") -> str:
        if not self._client():
            return "GitHub token not set."
        try:
            repo = self._user.get_repo(repo_name)
            issues = list(repo.get_issues(state=state))[:20]
            if not issues:
                return f"No {state} issues in {repo_name}"
            return "\n".join(f"#{i.number}: {i.title}" for i in issues)
        except Exception as e:
            return f"Error: {e}"

    def get_file_content(self, repo_name: str, file_path: str) -> str:
        if not self._client():
            return "GitHub token not set."
        try:
            repo = self._user.get_repo(repo_name)
            return repo.get_contents(file_path).decoded_content.decode("utf-8")
        except Exception as e:
            return f"Error: {e}"
