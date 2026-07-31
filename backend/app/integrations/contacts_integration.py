import subprocess


def search_contacts(query: str, limit: int = 10) -> list[dict]:
    """Search macOS Contacts by name."""
    safe_query = query.replace('"', "'").strip()
    script = f"""
tell application "Contacts"
    set output to ""
    set cnt to 0
    set matchingPeople to (every person whose name contains "{safe_query}")
    repeat with p in matchingPeople
        if cnt >= {limit} then exit repeat
        set pName to name of p
        set pEmail to ""
        try
            set pEmail to value of first email of p
        end try
        set pPhone to ""
        try
            set pPhone to value of first phone of p
        end try
        set pOrg to ""
        try
            set pOrg to organization of p
        end try
        set output to output & pName & "|" & pEmail & "|" & pPhone & "|" & pOrg & linefeed
        set cnt to cnt + 1
    end repeat
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
        contacts = []
        for line in raw.splitlines():
            parts = line.split("|")
            if parts and parts[0].strip():
                contacts.append({
                    "name": parts[0].strip(),
                    "email": parts[1].strip() if len(parts) > 1 else "",
                    "phone": parts[2].strip() if len(parts) > 2 else "",
                    "org": parts[3].strip() if len(parts) > 3 else "",
                })
        return contacts
    except Exception:
        return []


def format_for_context(contacts: list[dict]) -> str:
    if not contacts:
        return "No matching contacts found."
    lines = []
    for c in contacts:
        details = []
        if c.get("email"):
            details.append(c["email"])
        if c.get("phone"):
            details.append(c["phone"])
        if c.get("org"):
            details.append(c["org"])
        suffix = f" — {', '.join(details)}" if details else ""
        lines.append(f"- {c['name']}{suffix}")
    return "\n".join(lines)
