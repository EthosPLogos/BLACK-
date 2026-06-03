from app.agents.builder import BUILDER_SYSTEM
from app.agents.researcher import RESEARCHER_SYSTEM
from app.memory.store import add_conversation, get_user_context
from app.orchestrator.router import classify_intent
from app.services.ollama_client import call_ollama


def run_black(user_input: str) -> dict:
    route = classify_intent(user_input)
    user_context = get_user_context()

    if route["agent"] == "builder":
        system = BUILDER_SYSTEM
    else:
        system = RESEARCHER_SYSTEM

    prompt = f"""User context:
{user_context}

User request:
{user_input}

Respond clearly and directly.
If helpful, give short next steps.
"""

    reply = call_ollama(prompt=prompt, system=system)
    add_conversation(user_input, reply)

    return {
        "reply": reply,
        "agent": route["agent"],
        "task_type": route["task_type"],
        "memory_used": user_context != "No stored user context yet.",
    }