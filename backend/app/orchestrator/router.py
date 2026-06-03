def classify_intent(user_input: str) -> dict:
    text = user_input.lower()

    action_keywords = ["execute", "run", "delete", "send", "post", "deploy", "buy"]
    draft_keywords = ["draft", "write", "plan", "outline", "create"]
    research_keywords = ["research", "summarize", "explain", "what", "how", "why"]

    if any(word in text for word in action_keywords):
        return {
            "agent": "builder",
            "task_type": "action-plan",
        }

    if any(word in text for word in draft_keywords):
        return {
            "agent": "builder",
            "task_type": "draft",
        }

    if any(word in text for word in research_keywords):
        return {
            "agent": "researcher",
            "task_type": "research",
        }

    return {
        "agent": "researcher",
        "task_type": "general",
    }