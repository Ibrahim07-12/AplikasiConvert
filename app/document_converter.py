"""Office document conversion through LibreOffice headless mode."""

from __future__ import annotations

import shutil
import subprocess
import os
from pathlib import Path

from .converter import ConversionError


OFFICE_EXTENSIONS = {"doc", "docx", "xls", "xlsx", "ppt", "pptx"}


def find_libreoffice() -> str | None:
    """Find LibreOffice from PATH or standard Windows/Linux locations."""
    executable = shutil.which("soffice") or shutil.which("libreoffice")
    if executable:
        return executable

    candidates = [
        Path(os.environ.get("PROGRAMFILES", "")) / "LibreOffice/program/soffice.exe",
        Path(os.environ.get("PROGRAMFILES(X86)", ""))
        / "LibreOffice/program/soffice.exe",
        Path("/usr/bin/soffice"),
        Path("/usr/lib/libreoffice/program/soffice"),
    ]
    return next((str(path) for path in candidates if path.is_file()), None)


def convert_office_to_pdf(input_path: Path, output_directory: Path) -> Path:
    """Convert an Office document to PDF and return the generated path."""
    executable = find_libreoffice()
    if executable is None:
        raise ConversionError(
            "LibreOffice belum terpasang di server ini. "
            "Install LibreOffice atau jalankan aplikasi melalui Docker."
        )

    output_directory.mkdir(parents=True, exist_ok=True)
    command = [
        executable,
        "--headless",
        "--convert-to",
        "pdf",
        "--outdir",
        str(output_directory),
        str(input_path),
    ]
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise ConversionError("LibreOffice gagal menjalankan konversi.") from error

    output_path = output_directory / f"{input_path.stem}.pdf"
    if result.returncode != 0 or not output_path.is_file():
        detail = result.stderr.strip() or result.stdout.strip()
        raise ConversionError(
            f"Konversi dokumen ke PDF gagal{': ' + detail if detail else '.'}"
        )
    return output_path
