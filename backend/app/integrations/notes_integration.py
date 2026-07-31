import subprocess


def get_all_notes(limit: int = 100) -> list[dict]:
    """Fetch recent notes from macOS Notes app."""
    script = f"""
tell application "Notes"
    set output to ""
    set cnt to 0
    set allNotes to every note
    repeat with n in allNotes
        if cnt >= {limit} then exit repeat
        set noteTitle to name of n
        set noteBody to plaintext of n
        if length of noteBody > 300 then
            set noteBody to text 1 thru 300 of noteBody
        end if
        set safeBody to ""
        repeat with ch in characters of noteBody
            if ch is not "|" then
                set safeBody to safeBody & ch
            end if
        end repeat
        set output to output & noteTitle & "|" & safeBody & linefeed
        set cnt to cnt + 1
    end repeat
    return output
end tell
"""
    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True, text=True, timeout=15,
        )
        raw = result.stdout.strip()
        if not raw:
            return []
        notes = []
        for line in raw.splitlines():
            parts = line.split("|", 1)
            if parts and parts[0].strip():
                notes.append({
                    "title": parts[0].strip(),
                    "body": parts[1].strip() if len(parts) > 1 else "",
                })
        return notes
    except Exception:
        return []


def search_notes(query: str, limit: int = 10) -> list[dict]:
    """Search notes by keyword in title or body."""
    all_notes = get_all_notes(limit=200)
    query_lower = query.lower()
    matches = []
    for note in all_notes:
        if query_lower in note["title"].lower() or query_lower in note["body"].lower():
            matches.append(note)
        if len(matches) >= limit:
            break
    return matches


def format_for_context(notes: list[dict]) -> str:
    if not notes:
        return "No matching notes found."
    lines = []
    for n in notes:
        preview = n["body"][:200].replace("\n", " ")
        lines.append(f"- [{n['title']}] {preview}")
    return "\n".join(lines)
