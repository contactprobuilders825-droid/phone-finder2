from phone_finder.db import connect
from phone_finder.models import DeviceTarget, Tier
from phone_finder.service import make_sql_service


def demo() -> None:
    conn = connect(":memory:")
    service = make_sql_service(conn)

    # Test 1: Utilisateur Free avec limite
    print("=== Test 1: Utilisateur Free (25 devices max) ===")
    prof = service.resolve_user("prof")
    print(f"Prof: {prof.username}, Tier: {prof.tier.value}, Devices: {prof.device_count}")

    try:
        # 26 devices - dépasse la limite
        connected = [
            {"kind": "phone", "serial_number": f"P{i}", "is_powered_on": True}
            for i in range(26)
        ]
        phones = service.detect_phones(prof, connected)
    except Exception as e:
        print(f"❌ {type(e).__name__}: {e}")

    # Test 2: Utilisateurs avec limite respectée
    print("\n=== Test 2: Détection avec limite respectée ===")
    connected = [
        {"kind": "phone", "serial_number": "A1", "is_powered_on": True},
        {"kind": "phone", "serial_number": "B2", "is_powered_on": False},
        {"kind": "usb-key", "serial_number": "C3", "is_powered_on": True},
    ]
    phones = service.detect_phones(prof, connected)
    print(f"✓ Détectés: {len(phones)} téléphones")

    # Test 3: Utilisateur Premium
    print("\n=== Test 3: Utilisateur Premium (illimité) ===")
    direction = service.resolve_user("direction")
    print(f"Direction: {direction.username}, Tier: {direction.tier.value}")
    print(f"Direction peut détecter illimité: {direction.tier == Tier.PREMIUM}")

    mblock_code = service.download_adapter(prof, DeviceTarget.MBLOCK, phones)
    print("✓ Programme mBlock généré")

    microbit_code = service.download_adapter(direction, DeviceTarget.MICROBIT, phones)
    print("✓ Programme micro:bit généré")

    print("\n=== Test 4: Système de facturation ===")
    from phone_finder.billing import PricingPlan

    for tier in [Tier.FREE, Tier.PREMIUM]:
        plan = PricingPlan.PLANS[tier]
        print(
            f"  {tier.value.upper()}: "
            f"max_devices={plan['max_devices']}, "
            f"price=${plan['monthly_price']}, "
            f"ads={plan['show_ads']}"
        )

    print("\n=== Audit log (admin) ===")
    for line in service.get_audit_log(direction):
        print("-", line)


if __name__ == "__main__":
    demo()
