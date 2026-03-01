from dataclasses import dataclass
from enum import Enum


class Role(str, Enum):
    USER = "utilisateur"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"


class DeviceTarget(str, Enum):
    MBLOCK = "mblock"
    MICROBIT = "microbit"


class Tier(str, Enum):
    FREE = "free"
    PREMIUM = "premium"


@dataclass(frozen=True)
class User:
    username: str
    role: Role
    tier: Tier = Tier.FREE
    subscription_id: str | None = None
    device_count: int = 0

    def __post_init__(self) -> None:
        if not self.username or not isinstance(self.username, str):
            raise ValueError("L'utilisateur doit avoir un nom valide.")
        if not isinstance(self.role, Role):
            raise ValueError("Le rôle doit être une valeur Role valide.")
        if not isinstance(self.tier, Tier):
            raise ValueError("Le tier doit être une valeur Tier valide.")
        if self.device_count < 0:
            raise ValueError("device_count ne peut pas être négatif.")
        if (
            self.subscription_id is not None
            and not isinstance(self.subscription_id, str)
        ):
            raise ValueError("subscription_id doit être une chaîne ou None.")


@dataclass(frozen=True)
class Phone:
    serial_number: str
    is_powered_on: bool

    def __post_init__(self) -> None:
        if not self.serial_number or not isinstance(self.serial_number, str):
            raise ValueError("Le numéro de série du téléphone doit être non vide.")
        if not isinstance(self.is_powered_on, bool):
            raise ValueError("is_powered_on doit être un booléen.")
