import re

# Domain detection — score by keyword hits, pick highest
DOMAIN_KEYWORDS: dict[str, list[str]] = {
    "igbo": [
        # Language identity
        "igbo", "ibo", "igbo language", "speak igbo", "learn igbo", "teach me igbo",
        "igbo word", "igbo words", "igbo phrase", "igbo phrases",
        "igbo translation", "translate to igbo", "what is igbo for",
        "igbo meaning", "what does igbo", "in igbo",
        # Vocabulary triggers
        "ndeewo", "kedu", "daalu", "biko", "nnoo", "ka odi", "jide ike",
        "o di mma", "ọ dị mma", "ka chi fo", "ka emechaa",
        # Lessons
        "igbo greetings", "igbo numbers", "igbo family", "igbo food",
        "igbo verbs", "igbo body", "igbo colors", "igbo animals",
        "igbo proverbs", "ilu igbo", "igbo culture",
        # People / places
        "igbo people", "igbo nation", "southeastern nigeria", "biafra",
        "enugu", "anambra", "imo", "abia", "ebonyi",
        # Cultural
        "kola nut", "oji", "ọjị", "palm wine", "mmanya", "obi", "chi",
        "naming ceremony", "igba nkwu", "iwa akwa",
        # Meta
        "what is igbo", "igbo for beginners", "igbo lesson", "practice igbo",
        "igbo vocabulary", "igbo dictionary",
    ],
    "update_intel": [
        # System health / update checks
        "update check", "system check", "check for updates", "run updates",
        "what's outdated", "outdated packages", "pip outdated", "npm outdated",
        "package updates", "dependency updates", "upgrade packages",
        "update mr black", "update yourself", "update black",
        # New AI models / capabilities
        "new models", "latest models", "new ollama models", "ollama update",
        "what models are available", "pull new model", "update model",
        "latest llm", "new ai models", "better model", "faster model",
        "upgrade model", "new claude", "new groq", "new llama",
        "what's new in ai", "latest ai", "ai updates", "ai news tools",
        "new capabilities", "new features for black", "improve mr black",
        "make black better", "make mr black better", "enhance black",
        # System improvement framing
        "what should we upgrade", "what needs updating", "system health",
        "health report", "performance check", "is black up to date",
        "are we up to date", "anything to update", "any updates",
        "update report", "upgrade report", "weekly update",
        "latest and greatest", "keep current", "stay current",
    ],
    "weather": [
        "weather", "temperature", "forecast", "rain", "sunny", "cloudy",
        "humidity", "wind", "hot", "cold", "outside today", "what's it like",
        "should i bring", "umbrella",
    ],
    "calendar": [
        "calendar", "event", "meeting", "appointment", "agenda", "schedule",
        "what do i have", "what's on", "my day", "today's events",
        "upcoming", "this week", "next week", "what time", "when is",
    ],
    "reminders": [
        "reminder", "remind me", "reminders", "todo", "to-do", "to do",
        "don't forget", "add reminder", "create reminder", "pending tasks",
    ],
    "files": [
        "file", "folder", "document", "pdf", "find file", "locate file",
        "search for file", "where is my", "show me the", "open file",
        "find that", "look for", "locate", "my documents", "my downloads",
    ],
    "notes": [
        "note", "notes", "my notes", "i wrote", "i noted", "note about",
        "find my note", "search notes", "what did i write",
    ],
    "contacts": [
        "contact", "contacts", "who is", "phone number", "email of",
        "address of", "reach", "call", "person named", "find contact",
    ],
    "web": [
        "search the web", "look up online", "google", "find online",
        "latest news", "current news", "what is happening", "search for",
        "web search", "browse", "internet", "online",
    ],
    "email": [
        "email", "inbox", "unread", "emails from", "message from",
        "check email", "new emails", "read email", "my email",
        "mail", "check my mail", "any emails", "did i get",
        "messages", "subject", "sender",
    ],
    "finance": [
        # Core finance
        "stock", "market", "invest", "portfolio", "trade", "equity", "bond",
        "dividend", "return", "risk", "rate", "yield", "fund", "asset",
        "financial", "price", "valuation", "crypto", "forex", "earnings",
        "revenue", "profit", "loss", "balance sheet", "etf", "index",
        "interest", "inflation", "treasury", "capital", "shares", "holdings",
        "rebalance", "allocation", "brokerage", "sector", "commodity",
        # Options trading
        "option", "options", "call", "put", "strike", "expiry", "expiration",
        "delta", "gamma", "theta", "vega", "rho", "greek", "greeks",
        "implied volatility", "iv", "historical volatility", "hv", "vix",
        "covered call", "cash secured put", "iron condor", "butterfly",
        "straddle", "strangle", "spread", "debit spread", "credit spread",
        "vertical spread", "calendar spread", "diagonal spread",
        "wheel strategy", "pmcc", "protective put", "collar",
        "open interest", "options chain", "atm", "itm", "otm", "dte",
        "assignment", "exercise", "rolling", "roll up", "roll out",
        # Quantitative / algo trading
        "quant", "quantitative", "algorithmic", "algo trading", "backtest",
        "backtesting", "walk forward", "out of sample", "sharpe", "sortino",
        "drawdown", "alpha", "beta", "factor model", "momentum", "mean reversion",
        "arbitrage", "market making", "high frequency", "signal", "feature",
        "reinforcement learning", "ml trading", "strategy validation",
        # Platforms & research
        "quantconnect", "openbb", "finrl", "ibkr", "interactive brokers",
        "thinkorswim", "tastyworks", "arxiv", "ssrn", "thetagang",
        "r/options", "r/algotrading", "r/quantfinance",
        # Risk management
        "position sizing", "kelly criterion", "max loss", "stop loss",
        "hedge", "hedging", "portfolio risk", "var", "cvar", "expected value",
        "win rate", "profit factor", "risk reward",
    ],
    "business": [
        "business", "commerce", "customer", "sale", "marketing",
        "strategy", "competitor", "market share", "operation",
        "brand", "startup", "venture", "client", "service",
        "launch", "acquisition", "churn", "retention",
        "partnership", "contract", "vendor", "supply chain",
    ],
    "ecommerce": [
        "shopify", "woocommerce", "bigcommerce", "etsy", "ebay", "amazon seller",
        "online store", "ecommerce", "e-commerce", "dropship", "dropshipping",
        "fulfillment", "product listing", "sku", "reorder", "abandoned cart",
        "storefront", "wholesale", "retail margin", "aov", "roas", "cac", "ltv",
        "ad spend", "conversion rate", "product research", "niche product",
        "print on demand", "fba", "merch", "store revenue", "store sales",
        "store", "my store", "our store", "the store", "my shop", "our shop",
        "supplier", "sourcing", "moq", "inventory level", "stock level",
        "campaign roas", "ad campaign", "product margin", "sell online",
    ],
    "world_intel": [
        "good news", "positive news", "breakthrough", "breakthroughs", "discovery",
        "discoveries", "innovation", "success story", "world news", "latest discovery",
        "scientific breakthrough", "medical breakthrough", "technology breakthrough",
        "advances in", "progress in", "achievement", "milestone", "first ever",
        "new discovery", "cure found", "solved", "record broken", "mission success",
        "world progress", "humanity", "hope", "inspiring", "remarkable", "incredible news",
        "what good is happening", "good things happening", "positive developments",
        "space discovery", "cancer cure", "clean energy record", "species saved",
        "poverty reduced", "scanned the internet", "scrub the web", "scan the web",
        "around the world", "happening in the world", "amazing things",
        "what is going right", "world today", "positive stories",
    ],
    "job_search": [
        "job", "jobs", "hiring", "position", "role", "career", "resume", "cv",
        "interview", "apply", "application", "salary", "compensation",
        "remote work", "work from home", "job posting", "job board",
        "linkedin", "indeed", "glassdoor", "recruiter", "headhunter",
        "employment", "job market", "opening", "vacancy", "cover letter",
        "offer letter", "job offer", "job search", "job listing", "job description",
        "total comp", "equity offer", "signing bonus", "annual salary",
        "get hired", "find a job", "looking for work", "job hunting",
    ],
    "job_apply": [
        "apply for jobs", "start applying", "apply to jobs", "auto apply",
        "job applications", "apply every day", "keep applying",
        "stop applying", "pause applying", "disable job apply",
        "what jobs have you applied", "how many jobs applied",
        "applications today", "application history", "applied to today",
        "job apply status", "upload my resume", "update my resume",
        "set job criteria", "job criteria", "jobs applied",
        "run job apply", "apply now", "job hunt", "job hunting automated",
    ],
    "forge": [
        # Website / site — unambiguous intent words
        "website", "web site", "webpage", "web page",
        "landing page", "homepage", "home page",
        "portfolio site", "portfolio website", "portfolio page", "portfolio",
        "product page", "sales page", "one-page site", "single page site",
        "author website", "business website", "company website",
        "personal website", "personal site", "blog site", "blog website",
        # Explicit build commands (multi-word to avoid colliding with general "build")
        "build a website", "build me a website", "create a website", "make a website",
        "build a site", "create a site", "make a site", "build me a site",
        "build a web", "create a web", "make a web",
        "build a landing", "create a landing",
        "build a portfolio", "create a portfolio",
        "scaffold a", "scaffold the", "generate a website", "generate a site",
        # Framework-specific site creation
        "html site", "html website", "react site", "react website",
        "next.js site", "nextjs site", "vite app", "tailwind site",
        # Black Forge explicit
        "black forge", "forge build", "web project", "web build",
        # Deployment
        "deploy a site", "deploy a website", "netlify", "vercel deploy", "github pages",
    ],
    "build": [
        "code", "build", "deploy", "app", "software", "function", "class",
        "api", "database", "server", "frontend", "backend", "script",
        "debug", "unit test", "implement", "develop", "program", "engineer",
        "python", "javascript", "react", "fastapi", "sql", "git",
        "feature", "bug", "refactor", "architecture", "endpoint", "codebase",
    ],
    "security": [
        # Threats & attacks
        "hack", "hacked", "hacking", "breach", "breached", "malware", "virus",
        "ransomware", "phishing", "phish", "spyware", "keylogger", "trojan",
        "rootkit", "backdoor", "exploit", "exploited", "zero-day", "zero day",
        "vulnerability", "vulnerabilities", "cve", "cvss", "attack", "attacker",
        "threat actor", "apt", "nation state", "cybercriminal",
        # Network security
        "firewall", "intrusion", "ddos", "denial of service", "man in the middle",
        "mitm", "packet sniff", "port scan", "nmap", "wireshark", "network security",
        "network traffic", "rogue access point", "evil twin", "wifi security",
        # Privacy & OPSEC
        "privacy", "opsec", "operational security", "anonymity", "anonymous",
        "data broker", "data brokers", "digital footprint", "remove myself",
        "metadata", "exif", "fingerprint", "browser fingerprint", "compartment",
        # Credentials & identity
        "password", "credential", "credentials", "two factor", "two-factor",
        "2fa", "mfa", "multi factor", "authentication", "authenticator",
        "yubikey", "hardware key", "identity theft", "account takeover",
        "sim swap", "sim swapping", "haveibeenpwned", "leaked password",
        # Encryption & VPN
        "encrypt", "encryption", "encrypted", "vpn", "wireguard", "openvpn",
        "tor browser", "dark web", "onion", "ssl", "tls", "certificate",
        "end to end", "e2e encryption",
        # Physical security
        "smart lock", "security camera", "surveillance", "rfid", "access card",
        "key fob", "physical security", "evil maid", "usb drop",
        # Fraud & social engineering
        "scam", "fraud", "social engineering", "vishing", "smishing",
        "pretexting", "spear phish", "wire fraud", "identity fraud",
        # Incident response
        "compromised", "am i hacked", "suspicious activity", "unauthorized access",
        "data leak", "data exposed", "incident response", "forensics",
        # Frameworks & tools
        "mitre", "owasp", "nist security", "cis benchmark", "pentest",
        "penetration test", "red team", "blue team", "soc", "siem",
        "endpoint protection", "edr", "threat intelligence", "ioc",
        # Crypto security
        "seed phrase", "hardware wallet", "cold storage", "ledger", "trezor",
        "crypto security", "wallet security",
        # Mr.Black self-security
        "api key exposed", "backend security", "secure my setup",
        "security audit", "am i secure", "how secure",
    ],
    "gre": [
        # Exam + test names
        "gre", "gre exam", "gre test", "gre general test", "gre subject test",
        "powerprep", "ets gre", "magoosh gre", "manhattan prep gre",
        # Sections
        "verbal reasoning", "quantitative reasoning", "analytical writing",
        "quant section", "verbal section", "aw section", "issue essay", "argument essay",
        # Score language
        "gre score", "gre scores", "gre percentile", "scaled score",
        "130 to 170", "0 to 6 scale", "target score", "score goal",
        # Prep activities
        "gre prep", "gre practice", "gre study", "gre drill", "gre quiz",
        "practice test gre", "mock gre", "diagnostic test", "gre flashcard",
        "gre vocabulary", "gre math", "gre reading", "gre writing",
        # Question types
        "text completion", "sentence equivalence", "reading comprehension gre",
        "quantitative comparison", "data interpretation", "numeric entry",
        # Graduate school context
        "grad school", "graduate school", "graduate program", "phd program",
        "master program", "mba gre", "grad admissions", "ets",
    ],
    "science": [
        # Explicit study/teach triggers
        "teach me", "explain to me", "help me understand", "study", "studying",
        "quiz me", "test me", "practice problems", "test prep", "exam prep",
        "homework", "assignment", "lecture", "textbook", "course", "lesson",
        "what is a", "how does a", "why does",
        "boss battle", "feynman", "mnemonics", "mnemonic",
        # Anatomy & Physiology
        "anatomy", "physiology", "a&p", "histology", "integumentary",
        "skeletal", "muscular", "nervous system", "action potential",
        "depolarization", "repolarization", "homeostasis", "cardiac cycle",
        "nephron", "alveoli", "synapse", "neurotransmitter", "hormone",
        "endocrine", "cardiovascular", "lymphatic", "immune system",
        "respiratory", "digestive", "urinary", "reproductive",
        "sliding filament", "sarcomere", "myosin", "actin",
        # Medical Terminology
        "medical terminology", "med term", "medical term", "pathology",
        "diagnosis", "surgical suffix", "prefix meaning", "root word",
        "suffix", "-itis", "-osis", "-emia", "-plasty", "-ectomy", "-ostomy",
        "anatomy term", "clinical term", "medical prefix",
        # Physics
        "physics", "quantum", "relativity", "mechanics", "thermodynamics",
        "entropy", "momentum", "force", "energy", "velocity", "acceleration",
        "newton", "einstein", "bohr", "schrodinger", "wave function", "photon",
        "electron", "proton", "neutron", "atom", "nuclear", "fission", "fusion",
        "electromagnetic", "electromagnetism", "magnetic field", "electric field",
        "gravity", "gravitational", "black hole", "dark matter", "dark energy",
        "higgs boson", "quark", "lepton", "standard model", "string theory",
        # Chemistry
        "chemistry", "chemical", "molecule", "compound", "element", "periodic table",
        "reaction", "bond", "covalent", "ionic", "hydrogen bond", "oxidation",
        "reduction", "acid", "base", "pH", "catalyst", "enzyme", "polymer",
        "organic chemistry", "biochemistry", "stoichiometry", "molar", "mole",
        "equilibrium", "enthalpy", "gibbs", "entropy chemistry", "spectroscopy",
        # Biology
        "biology", "biological", "cell", "dna", "rna", "protein", "gene", "genome",
        "evolution", "natural selection", "mutation", "chromosome", "mitosis",
        "meiosis", "photosynthesis", "respiration", "metabolism", "neuron",
        "synapse", "brain", "nervous system", "immune system", "virus", "bacteria",
        "ecology", "ecosystem", "species", "taxonomy", "crispr", "epigenetics",
        "neuroscience", "cognitive", "consciousness",
        # Math
        "calculus", "derivative", "integral", "differential equation", "linear algebra",
        "matrix", "vector", "eigenvalue", "eigenvector", "probability",
        "statistics", "standard deviation", "regression", "bayes", "theorem",
        "proof", "topology", "abstract algebra", "number theory", "set theory",
        "fourier", "laplace", "taylor series", "complex analysis",
        # Earth & Space
        "astronomy", "astrophysics", "cosmology", "universe", "galaxy", "star",
        "planet", "solar system", "nebula", "supernova", "neutron star",
        "geology", "tectonic", "earthquake", "volcano", "climate", "atmosphere",
        "oceanography", "hydrosphere", "carbon cycle", "greenhouse",
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


# Domains where a single keyword is highly specific — no minimum threshold needed
_SINGLE_KW_DOMAINS = frozenset({
    "weather", "calendar", "reminders", "files", "notes", "contacts", "email",
    "science",       # scientific vocabulary is precise — one match is enough
    "finance",       # options/trading vocabulary is unambiguous — iron condor, straddle, etc.
    "security",      # security vocabulary is unambiguous — CVE, phishing, ransomware, etc.
    "job_apply",     # multi-word phrases are unambiguous — "apply for jobs", "stop applying"
    "gre",           # GRE vocabulary is unambiguous — "gre", "powerprep", "quantitative reasoning"
    "forge",         # multi-word phrases are unambiguous — "build a website", "landing page"
    "update_intel",  # update/system-check phrases are unambiguous — "check for updates", "new models"
    "igbo",          # "igbo" is unambiguous — one keyword is enough
})

# Minimum keyword hits required to commit to a domain (for all other domains)
_CONFIDENCE_THRESHOLD = 2


def _word_in(text: str, word: str) -> bool:
    return bool(re.search(r"\b" + re.escape(word) + r"\b", text))


def _kw_match(text: str, kw: str) -> bool:
    """Word-boundary match for single words; substring match for multi-word phrases.
    text is pre-lowercased; kw is lowercased here so uppercase tickers ('SPY') still match."""
    kw = kw.lower()
    if " " in kw:
        return kw in text
    return bool(re.search(r"\b" + re.escape(kw) + r"\b", text))


def _detect_domain(text: str) -> tuple[str, int]:
    """
    Returns (domain, confidence_score).
    Uses word-boundary matching to prevent 'test' hitting inside 'latest', etc.
    """
    scores = {
        domain: sum(1 for kw in keywords if _kw_match(text, kw))
        for domain, keywords in DOMAIN_KEYWORDS.items()
    }
    best = max(scores, key=scores.get)
    score = scores[best]
    if score == 0:
        return "general", 0
    return best, score


def classify_intent(user_input: str) -> dict:
    text = user_input.lower()
    domain, confidence = _detect_domain(text)

    # Low-confidence domain match on a complex domain — route to researcher
    # to avoid misrouting e.g. "what strategy should I use?" → business
    if domain not in _SINGLE_KW_DOMAINS and confidence < _CONFIDENCE_THRESHOLD:
        domain = "general"

    for task_type, agent, keywords in INTENT_MAP:
        if any(_word_in(text, kw) for kw in keywords):
            return {
                "agent": agent,
                "task_type": task_type,
                "domain": domain,
                "confidence": confidence,
            }

    return {
        "agent": "researcher",
        "task_type": "general",
        "domain": domain,
        "confidence": confidence,
    }
