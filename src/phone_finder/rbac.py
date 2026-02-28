from .models import Role


class Permission:
    DETECT_PHONES = "detect_phones"
    DOWNLOAD_ADAPTER = "download_adapter"
    VIEW_AUDIT_LOG = "view_audit_log"
    MANAGE_USERS = "manage_users"
    MANAGE_TARGETS = "manage_targets"


ROLE_PERMISSIONS = {
    Role.USER: {
        Permission.DETECT_PHONES,
        Permission.DOWNLOAD_ADAPTER,
    },
    Role.ADMIN: {
        Permission.DETECT_PHONES,
        Permission.DOWNLOAD_ADAPTER,
        Permission.VIEW_AUDIT_LOG,
        Permission.MANAGE_USERS,
    },
    Role.SUPER_ADMIN: {
        Permission.DETECT_PHONES,
        Permission.DOWNLOAD_ADAPTER,
        Permission.VIEW_AUDIT_LOG,
        Permission.MANAGE_USERS,
        Permission.MANAGE_TARGETS,
    },
}


def ensure_permission(role: Role, permission: str) -> None:
    if permission not in ROLE_PERMISSIONS[role]:
        raise PermissionError(f"Le rôle '{role}' ne peut pas exécuter '{permission}'.")
