from dataclasses import dataclass

from app.core.domains import VALID_DOMAINS


@dataclass
class DomainClassification:
    primary_domain: str
    domains: list[str]
    scores: dict[str, int]
    

DOMAIN_KEYWORDS: dict[str, list[str]] = {
    "cloud_computing": [
        "aws", "azure", "gcp", "cloud", "iam", "s3", "ec2", "lambda",
        "vpc", "cloudfront", "cloud run", "cloudformation", "terraform",
        "serverless", "availability zone", "region", "autoscaling",
    ],
    "data_engineering": [
        "etl", "elt", "pipeline", "airflow", "spark", "kafka", "flink",
        "warehouse", "lakehouse", "data lake", "batch", "streaming",
        "parquet", "delta lake", "dbt", "bigquery", "snowflake",
    ],
    "ai_ml": [
        "machine learning", "deep learning", "model", "training", "inference",
        "embedding", "vector", "rag", "llm", "transformer", "neural",
        "pytorch", "tensorflow", "scikit", "classification", "regression",
    ],
    "cybersecurity": [
        "security", "threat", "soc", "siem", "soar", "xsoar", "xsiam",
        "malware", "phishing", "incident", "vulnerability", "exploit",
        "zero trust", "mitre", "attack", "ioc", "detection", "edr",
        "authentication", "authorization", "encryption", "risk",
    ],
    "devops": [
        "devops", "ci/cd", "pipeline", "docker", "kubernetes", "helm",
        "deployment", "monitoring", "observability", "prometheus",
        "grafana", "logging", "sre", "release", "rollback", "container",
    ],
    "backend_development": [
        "api", "rest", "graphql", "fastapi", "django", "flask", "backend",
        "endpoint", "middleware", "authentication", "authorization",
        "session", "request", "response", "orm", "sqlalchemy", "service",
    ],
    "system_architecture": [
        "architecture", "design", "scalability", "reliability", "availability",
        "fault tolerance", "load balancing", "rate limiting", "circuit breaker",
        "queue", "event driven", "microservices", "monolith", "modular",
        "high availability", "resilience",
    ],
    "linux_systems": [
        "linux", "kernel", "process", "thread", "syscall", "cgroup",
        "namespace", "file descriptor", "socket", "systemd", "bash",
        "shell", "procfs", "auditd", "permissions", "capabilities",
    ],
    "databases": [
        "database", "sql", "postgres", "mysql", "mongodb", "redis",
        "index", "transaction", "acid", "isolation", "replication",
        "sharding", "partition", "query", "schema", "normalization",
    ],
    "networking": [
        "tcp", "udp", "dns", "http", "tls", "ssl", "ip", "subnet",
        "routing", "firewall", "proxy", "load balancer", "nat",
        "packet", "port", "osi", "network",
    ],
    "distributed_systems": [
        "distributed", "consensus", "raft", "paxos", "replication",
        "partition tolerance", "cap theorem", "eventual consistency",
        "leader election", "quorum", "gossip", "cluster", "node",
    ],
}


def classify_domains(text: str, max_domains: int = 3) -> DomainClassification:
    lowered = text.lower()
    scores: dict[str, int] = {}

    for domain, keywords in DOMAIN_KEYWORDS.items():
        score = 0

        for keyword in keywords:
            if keyword in lowered:
                score += 1

        scores[domain] = score

    ranked = sorted(
        scores.items(),
        key=lambda item: item[1],
        reverse=True,
    )

    matched = [domain for domain, score in ranked if score > 0]

    if not matched:
        return DomainClassification(
            primary_domain="general",
            domains=["general"],
            scores=scores,
        )

    selected = matched[:max_domains]
    primary = selected[0]

    cleaned_selected = [
        domain for domain in selected
        if domain in VALID_DOMAINS
    ]

    return DomainClassification(
        primary_domain=primary,
        domains=cleaned_selected or ["general"],
        scores=scores,
    )