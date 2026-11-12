"""PDF conversion helpers using PyMuPDF."""

from __future__ import annotations

from pathlib import Path

import fitz

from .converter import ConversionError


def convert_pdf_to_images(
    input_path: Path, output_directory: Path, target_format: str
) -> list[Path]:
    """Render every PDF page as an image."""
    output_directory.mkdir(parents=True, exist_ok=True)
    extension = target_format.lower().lstrip(".")
    image_format = "jpeg" if extension in {"jpg", "jpeg"} else extension
    output_paths: list[Path] = []
    try:
        document = fitz.open(input_path)
        with document:
            for page_number, page in enumerate(document, start=1):
                pixmap = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5), alpha=False)
                output_path = output_directory / f"page-{page_number}.{extension}"
                pixmap.save(str(output_path), output=image_format)
                output_paths.append(output_path)
    except (OSError, fitz.FileDataError, ValueError) as error:
        raise ConversionError("File PDF tidak valid atau gagal dirender.") from error
    return output_paths
