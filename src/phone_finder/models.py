from dataclasses import dataclass
from enum import Enum


class Role(str, Enum):
    USER = "utilisateur"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"


class DeviceTarget(str, Enum):
    MBLOCK = "mblock"
    MICROBIT = "microbit"


@dataclass(frozen=True)
class User:
    username: str
    role: Role


@dataclass(frozen=True)
class Phone:
    serial_number: str
    is_powered_on: bool
