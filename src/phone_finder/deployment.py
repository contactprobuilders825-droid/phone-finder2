from __future__ import annotations

import importlib
import tempfile
from pathlib import Path


def flash_microbit(program_source: str, *, port: str | None = None) -> str:
    """Flash un script MicroPython sur une carte micro:bit via uflash."""
    uflash = importlib.import_module("uflash")

    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as script_file:
        script_file.write(program_source)
        script_path = Path(script_file.name)

    kwargs = {"runtime": None}
    if port:
        kwargs["path_to_microbit"] = port

    uflash.flash(path_to_python=str(script_path), **kwargs)
    return str(script_path)


def upload_mblock_serial(payload: str, *, port: str, baudrate: int = 115200) -> None:
    """Envoie un payload vers un robot mBlock via pyserial."""
    serial = importlib.import_module("serial")
    with serial.Serial(port=port, baudrate=baudrate, timeout=1) as connection:
        connection.write(payload.encode("utf-8"))
        connection.flush()


async def probe_mblock_with_pymata(port: str) -> str:
    """Initialise une connexion pymata-express pour vérifier le robot mBlock."""
    pymata = importlib.import_module("pymata_express")
    board = pymata.pymata_express.PymataExpress(com_port=port)
    await board.shutdown()
    return port
