import subprocess


def get_today_events() -> list[dict]:
    script = """
tell application "Calendar"
    set todayStart to (current date)
    set hours of todayStart to 0
    set minutes of todayStart to 0
    set seconds of todayStart to 0
    set todayEnd to todayStart + (24 * 60 * 60)
    set output to ""
    repeat with cal in calendars
        set calName to name of cal
        try
            set evts to (every event of cal whose start date >= todayStart and start date < todayEnd)
            repeat with evt in evts
                set evtTitle to summary of evt
                set evtStart to start date of evt
                set evtEnd to end date of evt
                set startStr to (time string of evtStart)
                set endStr to (time string of evtEnd)
                set output to output & calName & "|" & evtTitle & "|" & startStr & "|" & endStr & linefeed
            end repeat
        end try
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
        events = []
        for line in raw.splitlines():
            parts = line.split("|")
            if len(parts) == 4:
                events.append({
                    "calendar": parts[0].strip(),
                    "title": parts[1].strip(),
                    "start": parts[2].strip(),
                    "end": parts[3].strip(),
                })
        return sorted(events, key=lambda e: e["start"])
    except Exception:
        return []


def get_upcoming_events(days: int = 7) -> list[dict]:
    script = f"""
tell application "Calendar"
    set todayStart to (current date)
    set hours of todayStart to 0
    set minutes of todayStart to 0
    set seconds of todayStart to 0
    set rangeEnd to todayStart + ({days} * 24 * 60 * 60)
    set output to ""
    repeat with cal in calendars
        set calName to name of cal
        try
            set evts to (every event of cal whose start date >= todayStart and start date < rangeEnd)
            repeat with evt in evts
                set evtTitle to summary of evt
                set evtStart to start date of evt
                set evtEnd to end date of evt
                set dateStr to (date string of evtStart)
                set startStr to (time string of evtStart)
                set endStr to (time string of evtEnd)
                set output to output & calName & "|" & evtTitle & "|" & dateStr & "|" & startStr & "|" & endStr & linefeed
            end repeat
        end try
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
        events = []
        for line in raw.splitlines():
            parts = line.split("|")
            if len(parts) == 5:
                events.append({
                    "calendar": parts[0].strip(),
                    "title": parts[1].strip(),
                    "date": parts[2].strip(),
                    "start": parts[3].strip(),
                    "end": parts[4].strip(),
                })
        return events
    except Exception:
        return []


def format_for_context(events: list[dict]) -> str:
    if not events:
        return "No events found."
    lines = []
    for e in events:
        date_str = e.get("date", "Today")
        lines.append(f"- {e['title']} ({date_str} {e['start']}–{e['end']}) [{e['calendar']}]")
    return "\n".join(lines)
