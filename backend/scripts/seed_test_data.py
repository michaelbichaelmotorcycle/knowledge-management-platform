"""
Seeds the test database with a small fixed dataset so retrieval/e2e tests
are deterministic.

Usage:
    DATABASE_URL=postgresql://test:test@localhost:5432/kma_test python scripts/seed_test_data.py
"""
import os
import sys

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    print("DATABASE_URL not set", file=sys.stderr)
    sys.exit(1)

# TODO(track 3/5): replace with real SQLAlchemy inserts once
# backend/app/models/document.py and chunk.py exist.
SEED_DOCUMENTS = [
    {"title": "Employee Handbook", "content": "Employees get 15 days PTO per year."},
    {"title": "IT Security Policy", "content": "Passwords rotate every 90 days, 12+ chars."},
]


def main():
    print(f"[seed] would seed {len(SEED_DOCUMENTS)} documents into {DATABASE_URL}")


if __name__ == "__main__":
    main()