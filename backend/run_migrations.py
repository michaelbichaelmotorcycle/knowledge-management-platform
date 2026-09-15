"""Run Alembic migrations programmatically."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

os.environ.setdefault("DATABASE_URL", "postgresql://kma_user:kma_password@localhost:5432/kma")
os.environ.setdefault("JWT_SECRET_KEY", "dev-only-secret-key-change-in-production")

from alembic.config import Config

from alembic import command

config = Config("alembic.ini")
config.set_main_option("sqlalchemy.url", os.environ["DATABASE_URL"])
command.upgrade(config, "head")
print("Migrations complete.")
