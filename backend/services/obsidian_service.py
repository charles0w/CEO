from pathlib import Path
from config import settings


class ObsidianService:
    def __init__(self):
        self.vault = Path(settings.obsidian_vault_path)

    def list_notes(self, path: str = "") -> str:
        target = self.vault / path if path else self.vault
        if not target.exists():
            return f"Path not found: {path}"
        notes = [str(f.relative_to(self.vault)) for f in sorted(target.rglob("*.md"))]
        return "\n".join(notes[:100]) if notes else "No notes found."

    def read_note(self, note_path: str) -> str:
        path = self.vault / note_path
        if not path.exists():
            return f"Note not found: {note_path}"
        try:
            return path.read_text(encoding="utf-8")
        except Exception as e:
            return f"Error reading note: {e}"

    def write_note(self, note_path: str, content: str) -> str:
        path = self.vault / note_path
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            return f"Written: {note_path}"
        except Exception as e:
            return f"Error writing note: {e}"

    def search_notes(self, query: str) -> str:
        results = []
        q = query.lower()
        for f in self.vault.rglob("*.md"):
            try:
                content = f.read_text(encoding="utf-8", errors="ignore")
                if q in content.lower() or q in f.name.lower():
                    rel = str(f.relative_to(self.vault))
                    match_line = next(
                        (ln.strip()[:100] for ln in content.splitlines() if q in ln.lower()),
                        ""
                    )
                    results.append(f"{rel}: {match_line}" if match_line else rel)
            except Exception:
                continue
        if not results:
            return f"No notes found containing '{query}'"
        return f"Found {len(results)} result(s):\n" + "\n".join(results[:25])
