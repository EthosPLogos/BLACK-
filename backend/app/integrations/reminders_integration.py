import subprocess


def get_pending_reminders(list_name: str = "") -> list[dict]:
    target = f'list named "{list_name}"' if list_name else "default list"
    script = f"""
tell application "Reminders"
    set output to ""
    try
        set rems to (every reminder of {target} whose completed is false)
        repeat with rem in rems
            set remName to name of rem
            set dueStr to ""
            try
                set dueDate to due date of rem
                set dueStr to date string of dueDate
            end try
            set output to output & remName & "|" & dueStr & linefeed
        end repeat
    end try
    return output
end tell
"""
    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True, text=True, timeout=10,
        )
        raw = result.stdout.strip()
        if not raw:
            return []
        reminders = []
        for line in raw.splitlines():
            parts = line.split("|")
            if parts and parts[0].strip():
                reminders.append({
                    "title": parts[0].strip(),
                    "due": parts[1].strip() if len(parts) > 1 else "",
                })
        return reminders
    except Exception:
        return []


def create_reminder(title: str, due_date: str = "", list_name: str = "") -> bool:
    target = f'list named "{list_name}"' if list_name else "default list"
    safe_title = title.replace('"', "'")
    if due_date:
        safe_date = due_date.replace('"', "'")
        props = f'{{name: "{safe_title}", due date: date "{safe_date}"}}'
    else:
        props = f'{{name: "{safe_title}"}}'
    script = f"""
tell application "Reminders"
    make new reminder at end of reminders of {target} with properties {props}
end tell
"""
    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True, text=True, timeout=10,
        )
        return result.returncode == 0
    except Exception:
        return False


def format_for_context(reminders: list[dict]) -> str:
    if not reminders:
        return "No pending reminders."
    lines = []
    for r in reminders:
        due = f" (due {r['due']})" if r.get("due") else ""
        lines.append(f"- {r['title']}{due}")
    return "\n".join(lines)
