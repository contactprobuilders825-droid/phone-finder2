"""Core package for Phone Finder."""

from .db import bootstrap_default_users, connect, get_user, init_db, list_users, upsert_user
from .deployment import flash_microbit, probe_mblock_with_pymata, upload_mblock_serial
from .models import DeviceTarget, Phone, Role, User
from .service import PhoneFinderService, make_sql_service

__all__ = [
    "DeviceTarget",
    "Phone",
    "Role",
    "User",
    "PhoneFinderService",
    "make_sql_service",
    "connect",
    "init_db",
    "upsert_user",
    "get_user",
    "list_users",
    "bootstrap_default_users",
    "flash_microbit",
    "upload_mblock_serial",
    "probe_mblock_with_pymata",
]
