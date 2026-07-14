"""
Single source of truth for everything personal in this profile README.

Every generator (portrait, info card, heatmap) imports from here, so changing
your bio/stack/handle is a one-file edit -- no hunting through SVG builders.

Regenerate after editing:
    python scripts/fetch_contributions.py
    python scripts/render_heatmap_svg.py
    python scripts/make_info_card.py
    python scripts/prep_photo.py source-photo.jpg && python scripts/make_ascii_svg.py
"""

# ---- identity -------------------------------------------------------------
GITHUB_USER = "Kartikk-26"
FULL_NAME = "Kartik Jain"
TAGLINE = "DevOps Engineer · GenAI Backend Builder"

# shell prompt shown in each terminal-style SVG titlebar ("<PROMPT_USER>@github")
PROMPT_USER = "kartik"

# First year with contributions. GitHub's public endpoint only serves a rolling
# 12-month window, so fetch_contributions.py walks year-by-year from here to get
# real all-time totals and true streaks (a 1-year window caps streaks at ~366).
ACCOUNT_START_YEAR = 2022

# ---- info card rows -------------------------------------------------------
# ("host",)          -> "<PROMPT_USER>@github" + rule
# ("kv", key, value) -> orange key + light value
# ("sec", title)     -> blue section header
# ("bul", text)      -> green bullet
# ("gap",)           -> vertical space
ROWS = [
    ("host",),
    ("kv", "Now", "DevOps Engineer"),
    ("kv", "Focus", "CI/CD, IaC, GenAI Backends"),
    ("kv", "Learning", "System Design, MLOps & AIOps"),
    ("kv", "Ask me", "DevOps, Cloud, Problem Solving"),
    ("gap",),
    ("sec", "Stack"),
    ("kv", "Cloud", "AWS, GCP, Docker, Kubernetes"),
    ("kv", "DevOps", "Terraform, Ansible, Jenkins, Linux"),
    ("kv", "AI / ML", "LangChain, OpenAI, Claude, HF"),
    ("kv", "Backend", "Node, Python, FastAPI, MongoDB"),
    ("kv", "Frontend", "React, TypeScript, Tailwind"),
    ("gap",),
    ("sec", "Highlights"),
    ("bul", "Building AI-powered DevOps tooling"),
    ("bul", "Open source contributor · Holopin badges"),
]
