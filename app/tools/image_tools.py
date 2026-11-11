"""Safe image-tool operations used by the API."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, UnidentifiedImageError

from ..converter import ConversionError

MAX_IMAGE_SIZE = 25 * 1024 * 1024
SUPPORTED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}


def compress_image(
    input_path: Path, output_path: Path, quality: int
) -> None:
    """Compress an image while preserving a usable output format."""
    if not 1 <= quality <= 100:
        raise ConversionError("Quality harus berada di antara 1 dan 100.")
    if input_path.stat().st_size > MAX_IMAGE_SIZE:
        raise ConversionError("Ukuran gambar melebihi batas 25 MB.")

    try:
        with Image.open(input_path) as image:
            source_format = (image.format or "").lower()
            if source_format not in SUPPORTED_IMAGE_EXTENSIONS:
                raise ConversionError(
                    "Format compress yang didukung: JPG, PNG, dan WEBP."
                )

            output_format = "JPEG" if source_format in {"jpg", "jpeg"} else image.format
            if output_format == "JPEG":
                if image.mode in {"RGBA", "LA", "P"}:
                    image = image.convert("RGB")
                image.save(output_path, format="JPEG", quality=quality, optimize=True)
            elif output_format == "PNG":
                image.save(
                    output_path,
                    format="PNG",
                    optimize=True,
                    compress_level=max(0, min(9, round((100 - quality) / 12))),
                )
            else:
                image.save(output_path, format="WEBP", quality=quality, method=6)
    except (OSError, UnidentifiedImageError) as error:
        raise ConversionError("File gambar tidak valid atau rusak.") from error
