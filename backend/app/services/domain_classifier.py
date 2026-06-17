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
        "load balancer", "object storage", "kubernetes", "eks", "aks", "gke",
    ],
    "data_engineering": [
        "etl", "elt", "pipeline", "airflow", "spark", "kafka", "flink",
        "warehouse", "lakehouse", "data lake", "batch", "streaming",
        "parquet", "delta lake", "dbt", "bigquery", "snowflake",
        "data warehouse", "orchestration",
    ],
    "ai_ml": [
        "machine learning", "deep learning", "model", "training", "inference",
        "embedding", "vector", "rag", "llm", "transformer", "neural",
        "pytorch", "tensorflow", "scikit", "classification", "regression",
        "fine tuning", "prompt", "token", "retrieval", "rerank", "agent",
    ],
    "cybersecurity": [
        "security", "threat", "soc", "siem", "soar", "xsoar", "xsiam",
        "malware", "phishing", "incident", "vulnerability", "exploit",
        "zero trust", "mitre", "attack", "ioc", "detection", "edr",
        "authentication", "authorization", "encryption", "risk",
        "firewall", "dns telemetry", "alert", "case", "containment",
        "playbook", "investigation", "forensics", "sentinel", "qradar"
    ],
    "devops": [
        "devops", "ci/cd", "pipeline", "docker", "kubernetes", "helm",
        "deployment", "monitoring", "observability", "prometheus",
        "grafana", "logging", "sre", "release", "rollback", "container",
        "infrastructure as code", "terraform", "ansible", "build", "deploy",
    ],
    "backend_development": [
        "api", "rest", "graphql", "fastapi", "django", "flask", "backend",
        "endpoint", "middleware", "authentication", "authorization",
        "session", "request", "response", "orm", "sqlalchemy", "service",
        "controller", "repository", "webhook", "pydantic", "route", "celery", "redis"
    ],
    "system_architecture": [
        "architecture", "design", "scalability", "reliability", "availability",
        "fault tolerance", "load balancing", "rate limiting", "circuit breaker",
        "queue", "event driven", "microservices", "monolith", "modular",
        "high availability", "resilience", "failure mode", "tradeoff",
        "system design", "bounded context",
    ],
    "linux_systems": [
        "linux", "kernel", "process", "thread", "syscall", "cgroup",
        "namespace", "file descriptor", "socket", "systemd", "bash",
        "shell", "procfs", "auditd", "permissions", "capabilities",
        "signals", "ptrace",
    ],
    "databases": [
        "database", "sql", "postgres", "postgresql", "mysql", "mongodb", "redis",
        "index", "transaction", "acid", "isolation", "replication",
        "sharding", "partition", "query", "schema", "normalization",
        "lock", "deadlock",
    ],
    "networking": [
        "tcp", "udp", "dns", "http", "https", "tls", "ssl", "ip", "subnet",
        "routing", "firewall", "proxy", "load balancer", "nat",
        "packet", "port", "osi", "network", "cidr", "bgp",
    ],
    "distributed_systems": [
        "distributed", "consensus", "raft", "paxos", "replication",
        "partition tolerance", "cap theorem", "eventual consistency",
        "leader election", "quorum", "gossip", "cluster", "node",
        "idempotency", "retry", "backoff",
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