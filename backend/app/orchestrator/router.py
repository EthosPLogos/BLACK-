import re

# Domain detection — score by keyword hits, pick highest
DOMAIN_KEYWORDS: dict[str, list[str]] = {
    "finance": [
        "stock", "market", "invest", "portfolio", "trade", "equity", "bond",
        "dividend", "return", "risk", "rate", "yield", "fund", "asset",
        "financial", "price", "valuation", "crypto", "forex", "earnings",
        "revenue", "profit", "loss", "balance sheet", "etf", "index",
        "interest", "inflation", "treasury", "capital", "shares", "holdings",
        "rebalance", "allocation", "brokerage", "sector", "commodity",
    ],
    "business": [
        "business", "commerce", "product", "customer", "sale", "marketing",
        "strategy", "competitor", "market share", "operation", "ecommerce",
        "shop", "brand", "startup", "venture", "client", "service", "pricing",
        "launch", "campaign", "conversion", "funnel", "acquisition", "churn",
        "retention", "partnership", "contract", "vendor", "supply chain",
    ],
    "build": [
        "code", "build", "deploy", "app", "software", "function", "class",
        "api", "database", "server", "frontend", "backend", "script",
        "debug", "test", "implement", "develop", "program", "engineer",
        "python", "javascript", "react", "fastapi", "sql", "git",
        "feature", "bug", "refactor", "architecture", "endpoint", "model",
    ],
}

# Intent keywords — checked with word boundaries to reduce false positives
INTENT_MAP: list[tuple[str, str, list[str]]] = [
    # (task_type, agent, keywords)
    ("action-plan", "builder", [
        "execute", "deploy", "delete", "send", "buy", "sell", "publish",
        "submit", "remove", "cancel", "transfer",
    ]),
    ("draft", "builder", [
        "draft", "write", "plan", "outline", "create", "design", "structure",
        "propose", "make", "build", "generate", "produce",
    ]),
    ("research", "researcher", [
        "research", "summarize", "explain", "analyze", "compare", "list",
        "what", "how", "why", "when", "who", "which", "tell", "describe",
        "show", "find", "understand", "review",
    ]),
]


def _word_in(text: str, word: str) -> bool:
    return bool(re.search(r"\b" + re.escape(word) + r"\b", text))


def _detect_domain(text: str) -> str:
    scores = {
        domain: sum(1 for kw in keywords if kw in text)
        for domain, keywords in DOMAIN_KEYWORDS.items()
    }
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "general"


def classify_intent(user_input: str) -> dict:
    text = user_input.lower()
    domain = _detect_domain(text)

    for task_type, agent, keywords in INTENT_MAP:
        if any(_word_in(text, kw) for kw in keywords):
            return {"agent": agent, "task_type": task_type, "domain": domain}

    return {"agent": "researcher", "task_type": "general", "domain": domain}
