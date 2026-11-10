"""Conversion service and supported-format definitions."""

from __future__ import annotations

from pathlib import Path
from typing import Final

from PIL import Image, UnidentifiedImageError

from .format_mapping import FORMAT_MAPPING

SUPPORTED_FORMATS: Final[dict[str, tuple[str, ...]]] = {
    "image": ("png", "jpg", "webp", "pdf"),
    "pdf": ("jpg", "png"),
    "document": ("pdf",),
}

EXTENSION_TO_PILLOW_FORMAT: Final[dict[str, str]] = {
    "pdf": "PDF",
    "png": "PNG",
    "jpg": "JPEG",
    "webp": "WEBP",
    "gif": "GIF",
    "bmp": "BMP",
    "tiff": "TIFF",
    "ico": "ICO",
}


class ConversionError(Exception):
    """Raised when an input cannot be converted safely."""


def get_file_category(filename: str, content_type: str | None) -> str | None:
    """Return the supported category for an uploaded file."""
    extension = Path(filename).suffix.lower().lstrip(".")
    if extension == "pdf" or content_type == "application/pdf":
        return "pdf"
    if extension in EXTENSION_TO_PILLOW_FORMAT or (
        content_type and content_type.startswith("image/")
    ):
        return "image"
    if extension in {"doc", "docx", "xls", "xlsx", "ppt", "pptx"}:
        return "document"
    return None


def get_target_formats(filename: str) -> tuple[str, ...]:
    """Return targets for a filename extension, normalizing JPEG spelling."""
    extension = Path(filename).suffix.lower().lstrip(".")
    return FORMAT_MAPPING.get(extension, ())


def convert_image(input_path: Path, output_path: Path, target_format: str) -> None:
    """Convert one image and normalize modes that JPEG cannot store."""
    normalized_target = target_format.lower().lstrip(".")
    if normalized_target not in EXTENSION_TO_PILLOW_FORMAT:
        raise ConversionError(f"Format tujuan tidak didukung: {target_format}")

    try:
        with Image.open(input_path) as image:
            output_format = EXTENSION_TO_PILLOW_FORMAT[normalized_target]
            if output_format == "PDF":
                image.convert("RGB").save(output_path, format="PDF")
                return
            if output_format == "JPEG" and image.mode in ("RGBA", "LA", "P"):
                background = Image.new("RGB", image.size, "white")
                if image.mode == "P":
                    image = image.convert("RGBA")
                background.paste(image, mask=image.getchannel("A"))
                image = background
            elif output_format == "JPEG":
                image = image.convert("RGB")

            image.save(output_path, format=output_format)
    except (OSError, UnidentifiedImageError) as error:
        raise ConversionError("File bukan gambar yang valid atau rusak.") from error
