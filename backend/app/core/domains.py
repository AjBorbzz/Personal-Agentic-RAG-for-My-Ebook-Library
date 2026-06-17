VALID_DOMAINS = {
    "cloud_computing",
    "data_engineering",
    "ai_ml",
    "cybersecurity",
    "devops",
    "backend_development",
    "system_architecture",
    "linux_systems",
    "databases",
    "networking",
    "distributed_systems",
    "general",
}


DOMAIN_LABELS = {
    "cloud_computing": "Cloud Computing",
    "data_engineering": "Data Engineering",
    "ai_ml": "AI/ML",
    "cybersecurity": "Cybersecurity",
    "devops": "DevOps",
    "backend_development": "Backend Development",
    "system_architecture": "System Architecture",
    "linux_systems": "Linux / Systems",
    "databases": "Databases",
    "networking": "Networking",
    "distributed_systems": "Distributed Systems",
    "general": "General",
}


def normalize_domain(domain: str) -> str:
    normalized = (
        domain.strip()
        .lower()
        .replace(" ", "_")
        .replace("-", "_")
        .replace("/", "_")
    )

    aliases = {
        "cloud": "cloud_computing",
        "aws": "cloud_computing",
        "azure": "cloud_computing",
        "gcp": "cloud_computing",
        "ai": "ai_ml",
        "ml": "ai_ml",
        "machine_learning": "ai_ml",
        "artificial_intelligence": "ai_ml",
        "security": "cybersecurity",
        "cyber": "cybersecurity",
        "backend": "backend_development",
        "api": "backend_development",
        "architecture": "system_architecture",
        "systems": "linux_systems",
        "linux": "linux_systems",
        "db": "databases",
        "database": "databases",
        "distributed": "distributed_systems",
        "distributed_system": "distributed_systems",
    }

    normalized = aliases.get(normalized, normalized)

    if normalized not in VALID_DOMAINS:
        return "general"

    return normalized