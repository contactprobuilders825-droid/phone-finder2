from phone_finder.db import connect
from phone_finder.models import DeviceTarget
from phone_finder.service import make_sql_service


def demo() -> None:
    conn = connect(":memory:")
    service = make_sql_service(conn)

    prof = service.resolve_user("prof")
    direction = service.resolve_user("direction")

    connected = [
        {"kind": "phone", "serial_number": "A1", "is_powered_on": True},
        {"kind": "phone", "serial_number": "B2", "is_powered_on": False},
        {"kind": "usb-key", "serial_number": "C3", "is_powered_on": True},
    ]

    phones = service.detect_phones(prof, connected)

    mblock_code = service.download_adapter(prof, DeviceTarget.MBLOCK, phones)
    print("=== Programme mBlock ===")
    print(mblock_code)

    microbit_code = service.download_adapter(direction, DeviceTarget.MICROBIT, phones)
    print("\n=== Programme micro:bit ===")
    print(microbit_code)

    print("\n=== Audit log (admin) ===")
    for line in service.get_audit_log(direction):
        print("-", line)


if __name__ == "__main__":
    demo()
