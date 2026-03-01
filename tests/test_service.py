import unittest
from unittest.mock import patch

from phone_finder.billing import AdPlacement, FeatureLimitError, PayPalHelper, PricingPlan
from phone_finder.db import connect, list_users, upsert_user
from phone_finder.models import DeviceTarget, Role, Tier, User
from phone_finder.service import make_sql_service


class PhoneFinderServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.conn = connect(":memory:")
        self.service = make_sql_service(self.conn)

    def test_detect_phones_filters_non_phones(self) -> None:
        prof = self.service.resolve_user("prof")
        phones = self.service.detect_phones(
            prof,
            [
                {"kind": "phone", "serial_number": "P1", "is_powered_on": True},
                {"kind": "tablet", "serial_number": "T1", "is_powered_on": True},
            ],
        )
        self.assertEqual(1, len(phones))
        self.assertEqual("P1", phones[0].serial_number)

    def test_user_cannot_read_audit_log(self) -> None:
        prof = self.service.resolve_user("prof")
        with self.assertRaises(PermissionError):
            self.service.get_audit_log(prof)

    def test_download_adapter_for_microbit(self) -> None:
        prof = self.service.resolve_user("prof")
        direction = self.service.resolve_user("direction")
        phones = self.service.detect_phones(
            prof,
            [{"kind": "phone", "serial_number": "P1", "is_powered_on": True}],
        )
        program = self.service.download_adapter(direction, DeviceTarget.MICROBIT, phones)
        self.assertIn("from microbit import *", program)
        self.assertIn("phones_on = 1", program)

    def test_super_admin_has_full_rights(self) -> None:
        owner = self.service.resolve_user("owner")
        phones = self.service.detect_phones(
            owner,
            [{"kind": "phone", "serial_number": "P1", "is_powered_on": False}],
        )
        self.service.download_adapter(owner, DeviceTarget.MBLOCK, phones)
        self.assertGreaterEqual(len(self.service.get_audit_log(owner)), 2)

    def test_roles_are_stored_in_sql(self) -> None:
        upsert_user(self.conn, User(username="prof2", role=Role.USER))
        usernames = [user.username for user in list_users(self.conn)]
        self.assertIn("prof2", usernames)
        self.assertIn("owner", usernames)

    @patch("phone_finder.service.flash_microbit", return_value="/tmp/script.py")
    def test_deploy_microbit_uses_uflash_wrapper(self, mock_flash) -> None:
        admin = self.service.resolve_user("direction")
        result = self.service.deploy_adapter(
            admin,
            DeviceTarget.MICROBIT,
            "from microbit import *\n",
            port="/media/MICROBIT",
        )
        self.assertEqual("/tmp/script.py", result)
        mock_flash.assert_called_once()

    def test_deploy_mblock_requires_serial_port(self) -> None:
        admin = self.service.resolve_user("direction")
        with self.assertRaises(ValueError):
            self.service.deploy_adapter(admin, DeviceTarget.MBLOCK, "payload")

    @patch("phone_finder.service.upload_mblock_serial")
    def test_deploy_mblock_uses_pyserial_wrapper(self, mock_upload) -> None:
        admin = self.service.resolve_user("direction")
        result = self.service.deploy_adapter(
            admin,
            DeviceTarget.MBLOCK,
            "payload",
            port="COM3",
        )
        self.assertEqual("COM3", result)
        mock_upload.assert_called_once_with(payload="payload", port="COM3")

    def test_admin_can_manage_users(self) -> None:
        """Un admin peut accéder aux permissions de gestion utilisateurs."""
        from phone_finder.rbac import Permission, ensure_permission
        admin = self.service.resolve_user("direction")
        try:
            ensure_permission(admin.role, Permission.MANAGE_USERS)
        except PermissionError:
            self.fail("Admin devrait avoir la permission MANAGE_USERS")

    def test_user_cannot_manage_users(self) -> None:
        """Un utilisateur normal ne peut pas gérer les utilisateurs."""
        from phone_finder.rbac import Permission, ensure_permission
        prof = self.service.resolve_user("prof")
        with self.assertRaises(PermissionError):
            ensure_permission(prof.role, Permission.MANAGE_USERS)

    def test_user_cannot_view_audit_log_explicitly(self) -> None:
        """Un utilisateur ne peut vraiment pas voir les logs d'audit."""
        prof = self.service.resolve_user("prof")
        with self.assertRaises(PermissionError):
            self.service.get_audit_log(prof)

    def test_admin_can_view_audit_log(self) -> None:
        """Un admin peut voir les logs d'audit."""
        admin = self.service.resolve_user("direction")
        self.service.detect_phones(admin, [])
        logs = self.service.get_audit_log(admin)
        self.assertIsInstance(logs, list)
        self.assertGreaterEqual(len(logs), 1)

    def test_detect_phones_includes_power_state(self) -> None:
        """Vérifier que l'état d'alimentation des téléphones est préservé."""
        prof = self.service.resolve_user("prof")
        phones = self.service.detect_phones(
            prof,
            [
                {"kind": "phone", "serial_number": "ON", "is_powered_on": True},
                {"kind": "phone", "serial_number": "OFF", "is_powered_on": False},
            ],
        )
        self.assertEqual(2, len(phones))
        self.assertTrue(phones[0].is_powered_on)
        self.assertFalse(phones[1].is_powered_on)

    def test_free_tier_has_25_device_limit(self) -> None:
        """Les utilisateurs Free ont une limite de 25 appareils."""
        prof = self.service.resolve_user("prof")
        self.assertEqual(Tier.FREE, prof.tier)

        devices = [
            {"kind": "phone", "serial_number": f"P{i}", "is_powered_on": True}
            for i in range(26)
        ]
        with self.assertRaises(FeatureLimitError) as ctx:
            self.service.detect_phones(prof, devices)

        self.assertEqual(25, ctx.exception.max_devices)
        self.assertEqual(26, ctx.exception.current_count)

    def test_premium_tier_unlimited_devices(self) -> None:
        """Les utilisateurs Premium n'ont pas de limite."""
        direction = self.service.resolve_user("direction")
        self.assertEqual(Tier.PREMIUM, direction.tier)

        # Essayer de détecter 100 appareils
        devices = [
            {"kind": "phone", "serial_number": f"P{i}", "is_powered_on": True}
            for i in range(100)
        ]
        phones = self.service.detect_phones(direction, devices)
        self.assertEqual(100, len(phones))

    def test_pricing_plan_free_tier(self) -> None:
        """Vérifier les limites du plan Free."""
        self.assertEqual(25, PricingPlan.get_limit(Tier.FREE))
        self.assertEqual(0.0, PricingPlan.get_price(Tier.FREE))
        self.assertTrue(PricingPlan.needs_ads(Tier.FREE))

    def test_pricing_plan_premium_tier(self) -> None:
        """Vérifier les limites du plan Premium."""
        self.assertGreater(PricingPlan.get_limit(Tier.PREMIUM), 25)
        self.assertEqual(4.99, PricingPlan.get_price(Tier.PREMIUM))
        self.assertFalse(PricingPlan.needs_ads(Tier.PREMIUM))

    def test_ad_placement_for_free_users(self) -> None:
        """Vérifier que les pubs sont générées pour les utilisateurs Free."""
        ad = AdPlacement.get_free_tier_ad()
        self.assertEqual("interstitial", ad.ad_type)
        self.assertIn("25", ad.message)
        self.assertIn("publicité", ad.message)

    def test_watch_ad_bonus(self) -> None:
        """Un utilisateur Free regardant une pub obtient 5 devices."""
        prof = self.service.resolve_user("prof")
        initial_count = prof.device_count

        new_count = self.service.watch_ad_for_bonus(prof)
        self.assertGreater(new_count, initial_count)

    @patch("phone_finder.billing.PayPalHelper.verify_subscription", return_value=False)
    def test_upgrade_to_premium_requires_valid_subscription(self, mock_verify) -> None:
        """L'upgrade nécessite une souscription PayPal valide."""
        prof = self.service.resolve_user("prof")

        with self.assertRaises(ValueError):
            self.service.upgrade_to_premium(prof, "INVALID_SUB_ID")

    @patch("phone_finder.billing.PayPalHelper.verify_subscription", return_value=True)
    def test_upgrade_to_premium_success(self, mock_verify) -> None:
        """Un utilisateur Free peut upgrader vers Premium."""
        prof = self.service.resolve_user("prof")
        self.assertEqual(Tier.FREE, prof.tier)

        self.service.upgrade_to_premium(prof, "I-TEST123456")
        
        # Vérifier dans les logs
        logs = self.service.get_audit_log(self.service.resolve_user("direction"))
        self.assertTrue(any("Premium" in log for log in logs))

    def test_user_tier_persisted_in_db(self) -> None:
        """Vérifier que le tier est persisté en base de données."""
        # Créer un nouvel utilisateur avec un tier
        test_user = User(
            username="premium_user",
            role=Role.USER,
            tier=Tier.PREMIUM,
            device_count=50,
        )
        upsert_user(self.conn, test_user)

        # Récupérer et vérifier
        retrieved = list_users(self.conn)
        premium_user = next((u for u in retrieved if u.username == "premium_user"), None)
        self.assertIsNotNone(premium_user)
        self.assertEqual(Tier.PREMIUM, premium_user.tier)
        self.assertEqual(50, premium_user.device_count)


if __name__ == "__main__":
    unittest.main()
