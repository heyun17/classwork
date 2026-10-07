"""Backward-compatible entry point for the database diagnostic command."""

from scripts_db_check import main


if __name__ == "__main__":
    raise SystemExit(main())
