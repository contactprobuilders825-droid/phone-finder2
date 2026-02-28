from __future__ import annotations

from .models import DeviceTarget, Phone


def build_adapter_program(target: DeviceTarget, phones: list[Phone]) -> str:
    powered_on_count = sum(1 for phone in phones if phone.is_powered_on)

    if target == DeviceTarget.MBLOCK:
        return _mblock_program(powered_on_count)
    if target == DeviceTarget.MICROBIT:
        return _microbit_program(powered_on_count)

    raise ValueError(f"Cible non supportée: {target}")


def _mblock_program(powered_on_count: int) -> str:
    return "\n".join(
        [
            "when green flag clicked",
            f"set [telephones_allumes v] to ({powered_on_count})",
            "if <(telephones_allumes) > [0]> then",
            '  say [Téléphones détectés et allumés] for (2) secs',
            "else",
            '  say [Aucun téléphone allumé] for (2) secs',
            "end",
        ]
    )


def _microbit_program(powered_on_count: int) -> str:
    icon = "Image.HAPPY" if powered_on_count else "Image.SAD"
    return "\n".join(
        [
            "from microbit import *",
            "",
            f"phones_on = {powered_on_count}",
            f"display.show({icon})",
            "while True:",
            "    if button_a.was_pressed():",
            "        display.scroll(str(phones_on))",
            "    sleep(100)",
        ]
    )
