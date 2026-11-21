"""Run from backend: python -m app.evaluation.run --dataset smoke --version v1"""
import argparse
from app.db.session import SessionLocal
from app.evaluation.service import execute_run


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", required=True)
    ap.add_argument("--version", required=True)
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--max-cases", type=int, default=20)
    ap.add_argument("--base-url", default="http://127.0.0.1:8000")
    args = ap.parse_args()
    if not 1 <= args.k <= 20 or not 1 <= args.max_cases <= 50:
        ap.error("k must be 1-20 and max-cases 1-50")
    db = SessionLocal()
    try:
        run = execute_run(db, dataset_name=args.dataset, dataset_version=args.version,
                          system_config={"invoker": "cli"}, k=args.k,
                          max_cases=args.max_cases, base_url=args.base_url)
        print("run_id:", run.evaluation_run_id, "status:", run.status)
        print("summary:", run.summary_metrics)
    finally:
        db.close()


if __name__ == "__main__":
    main()