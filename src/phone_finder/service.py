from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field

from .adapters import build_adapter_program
from .billing import FeatureLimitError, PricingPlan
from .db import bootstrap_default_users, get_user, init_db
from .deployment import flash_microbit, upload_mblock_serial
from .models import DeviceTarget, Phone, Role, Tier, User
from .rbac import Permission, ensure_permission


@dataclass
class PhoneFinderService:
    """Service principal qui gère la détection et l'export vers des robots."""

    db_conn: sqlite3.Connection | None = None
    supported_targets: set[DeviceTarget] = field(
        default_factory=lambda: {DeviceTarget.MBLOCK, DeviceTarget.MICROBIT}
    )
    audit_log: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.db_conn is not None:
            init_db(self.db_conn)

    def resolve_user(self, username: str) -> User:
        if self.db_conn is None:
            # Mode sans DB : utilisateurs par défaut en mémoire
            default_users = {
                "prof": User(username="prof", role=Role.USER),
                "direction": User(username="direction", role=Role.ADMIN),
                "owner": User(username="owner", role=Role.SUPER_ADMIN),
            }
            if username not in default_users:
                raise LookupError(f"Utilisateur inconnu: {username}")
            return default_users[username]

        user = get_user(self.db_conn, username)
        if user is None:
            raise LookupError(f"Utilisateur inconnu: {username}")
        return user

    def detect_phones(self, actor: User, connected_devices: list[dict]) -> list[Phone]:
        ensure_permission(actor.role, Permission.DETECT_PHONES)

        phones = [
            Phone(
                serial_number=device["serial_number"],
                is_powered_on=bool(device.get("is_powered_on", False)),
            )
            for device in connected_devices
            if device.get("kind") == "phone"
        ]

        # Vérifier la limite de devices pour le tier Free
        max_devices = PricingPlan.get_limit(actor.tier)
        if len(phones) > max_devices:
            raise FeatureLimitError(max_devices, len(phones), actor.tier)

        self.audit_log.append(
            f"{actor.username} a lancé une détection: {len(phones)} téléphone(s)."
        )
        return phones

    def download_adapter(self, actor: User, target: DeviceTarget, phones: list[Phone]) -> str:
        ensure_permission(actor.role, Permission.DOWNLOAD_ADAPTER)

        if target not in self.supported_targets:
            raise ValueError(f"Cible {target} non prise en charge.")

        program = build_adapter_program(target, phones)
        self.audit_log.append(
            f"{actor.username} a généré un adaptateur {target} ({len(phones)} téléphone(s))."
        )
        return program

    def deploy_adapter(
        self,
        actor: User,
        target: DeviceTarget,
        program: str,
        *,
        port: str | None = None,
    ) -> str:
        ensure_permission(actor.role, Permission.DOWNLOAD_ADAPTER)

        if target == DeviceTarget.MICROBIT:
            flashed_source = flash_microbit(program_source=program, port=port)
            self.audit_log.append(f"{actor.username} a flashé micro:bit ({port or 'auto'}).")
            return flashed_source

        if target == DeviceTarget.MBLOCK:
            if not port:
                raise ValueError("Le port série est obligatoire pour mBlock.")
            upload_mblock_serial(payload=program, port=port)
            self.audit_log.append(f"{actor.username} a envoyé un programme mBlock ({port}).")
            return port

        raise ValueError(f"Cible {target} non prise en charge pour le déploiement.")

    def add_target(self, actor: User, target: DeviceTarget) -> None:
        ensure_permission(actor.role, Permission.MANAGE_TARGETS)
        self.supported_targets.add(target)
        self.audit_log.append(f"{actor.username} a ajouté la cible {target}.")

    def get_audit_log(self, actor: User) -> list[str]:
        ensure_permission(actor.role, Permission.VIEW_AUDIT_LOG)
        return list(self.audit_log)

    def upgrade_to_premium(self, actor: User, subscription_id: str) -> None:
        """Upgrade un utilisateur vers Premium via PayPal."""
        from .billing import PayPalHelper

        if not PayPalHelper.verify_subscription(subscription_id):
            raise ValueError("Souscription PayPal invalide ou expirée.")

        # Mettre à jour l'utilisateur
        updated_user = User(
            username=actor.username,
            role=actor.role,
            tier=Tier.PREMIUM,
            subscription_id=subscription_id,
            device_count=actor.device_count,
        )

        if self.db_conn:
            from .db import upsert_user

            upsert_user(self.db_conn, updated_user)

        self.audit_log.append(
            f"{actor.username} a upgrader vers Premium (subscription: {subscription_id[:8]}...)"
        )

    def watch_ad_for_bonus(self, actor: User) -> int:
        """Utilisateur regarde une pub, obtient 5 devices additionnels temporaires."""
        if actor.tier != Tier.FREE:
            raise ValueError("Seuls les utilisateurs Free peuvent regarder les pubs.")

        ad_bonus = 5
        max_devices = PricingPlan.get_limit(Tier.FREE)

        new_count = min(actor.device_count + ad_bonus, max_devices)

        # Mettre à jour
        updated_user = User(
            username=actor.username,
            role=actor.role,
            tier=actor.tier,
            subscription_id=actor.subscription_id,
            device_count=new_count,
        )

        if self.db_conn:
            from .db import upsert_user

            upsert_user(self.db_conn, updated_user)

        self.audit_log.append(
            f"{actor.username} a regardé une publicité (+{ad_bonus} devices temporaires)."
        )
        return new_count


# Note: make_default_users() est remplacée par bootstrap_default_users() qui
# persiste les utilisateurs en base de données. Cette fonction reste à titre de
# référence pour les configurations sans base de données.


def make_sql_service(db_conn: sqlite3.Connection) -> PhoneFinderService:
    init_db(db_conn)
    bootstrap_default_users(db_conn)
    return PhoneFinderService(db_conn=db_conn)
