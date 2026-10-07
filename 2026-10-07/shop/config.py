"""Validated, environment-backed application configuration."""

from __future__ import annotations

from dataclasses import dataclass
import os


class SettingsError(ValueError):
    """Raised when an environment setting has an invalid value."""


def _read_port(value: str) -> int:
    try:
        port = int(value)
    except ValueError as exc:
        raise SettingsError("MYSQL_PORT must be an integer") from exc
    if not 1 <= port <= 65_535:
        raise SettingsError("MYSQL_PORT must be between 1 and 65535")
    return port


@dataclass(frozen=True, slots=True)
class Settings:
    """Runtime configuration for the shop application."""

    mysql_host: str = "127.0.0.1"
    mysql_port: int = 3307
    mysql_user: str = "shop_user"
    mysql_password: str = ""
    mysql_database: str = "shop"

    @classmethod
    def from_env(cls) -> "Settings":
        defaults = cls()
        host = os.getenv("MYSQL_HOST", defaults.mysql_host).strip()
        user = os.getenv("MYSQL_USER", defaults.mysql_user).strip()
        database = os.getenv("MYSQL_DATABASE", defaults.mysql_database).strip()
        if not host or not user or not database:
            raise SettingsError("MYSQL_HOST, MYSQL_USER and MYSQL_DATABASE are required")
        return cls(
            mysql_host=host,
            mysql_port=_read_port(os.getenv("MYSQL_PORT", str(defaults.mysql_port))),
            mysql_user=user,
            mysql_password=os.getenv("MYSQL_PASSWORD", ""),
            mysql_database=database,
        )

    def mysql_kwargs(self) -> dict[str, object]:
        return {
            "host": self.mysql_host,
            "port": self.mysql_port,
            "user": self.mysql_user,
            "password": self.mysql_password,
            "database": self.mysql_database,
        }
