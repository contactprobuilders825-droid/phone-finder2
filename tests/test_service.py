import unittest
from unittest.mock import patch

from phone_finder.db import connect, list_users, upsert_user
from phone_finder.models import DeviceTarget, Role, User
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


if __name__ == "__main__":
    unittest.main()
