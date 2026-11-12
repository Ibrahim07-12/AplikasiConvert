"""Safe image-tool operations used by the API."""

from __future__ import annotations

import base64
import io
from pathlib import Path

from PIL import Image, ImageDraw, ImageOps, UnidentifiedImageError

from ..converter import ConversionError

MAX_IMAGE_SIZE = 25 * 1024 * 1024
SUPPORTED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}


def open_image(input_path: Path) -> Image.Image:
    """Open an image and normalize it to a safe in-memory object."""
    try:
        image = Image.open(input_path)
        image.load()
        return image
    except (OSError, UnidentifiedImageError) as error:
        raise ConversionError("File gambar tidak valid atau rusak.") from error


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


def save_image(image: Image.Image, output_path: Path, extension: str, quality: int = 90) -> None:
    """Save an image using a format compatible with its output extension."""
    extension = extension.lower().lstrip(".")
    image_format = {"jpg": "JPEG", "jpeg": "JPEG", "png": "PNG", "webp": "WEBP"}.get(extension)
    if image_format is None:
        raise ConversionError(f"Format gambar tidak didukung: {extension}")
    if image_format == "JPEG" and image.mode in {"RGBA", "LA", "P"}:
        image = image.convert("RGB")
    image.save(output_path, format=image_format, quality=quality, optimize=True)


def resize_image(input_path: Path, output_path: Path, width: int, height: int) -> None:
    if width < 1 or height < 1 or width > 10000 or height > 10000:
        raise ConversionError("Ukuran resize harus antara 1 dan 10000 piksel.")
    image = open_image(input_path)
    resized = ImageOps.contain(image, (width, height))
    save_image(resized, output_path, output_path.suffix)


def crop_image(input_path: Path, output_path: Path, left: int, top: int, right: int, bottom: int) -> None:
    image = open_image(input_path)
    if not (0 <= left < right <= image.width and 0 <= top < bottom <= image.height):
        raise ConversionError("Area crop berada di luar ukuran gambar.")
    save_image(image.crop((left, top, right, bottom)), output_path, output_path.suffix)


def transform_image(input_path: Path, output_path: Path, tool: str, angle: int = 90) -> None:
    image = open_image(input_path)
    if tool == "rotate":
        if angle not in {90, 180, 270}:
            raise ConversionError("Rotasi hanya mendukung 90, 180, atau 270 derajat.")
        result = image.rotate(angle, expand=True)
    elif tool == "flip":
        result = ImageOps.mirror(image)
    elif tool == "grayscale":
        result = ImageOps.grayscale(image)
    else:
        raise ConversionError(f"Tool image tidak dikenal: {tool}")
    save_image(result, output_path, output_path.suffix)


def watermark_image(input_path: Path, output_path: Path, text: str) -> None:
    if not text.strip():
        raise ConversionError("Teks watermark tidak boleh kosong.")
    image = open_image(input_path).convert("RGBA")
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    draw.text((20, image.height - 45), text[:200], fill=(255, 255, 255, 180))
    save_image(Image.alpha_composite(image, overlay), output_path, output_path.suffix)


def remove_background(input_path: Path, output_path: Path) -> None:
    """Remove near-white pixels; this is a deterministic local tool, not AI segmentation."""
    image = open_image(input_path).convert("RGBA")
    pixels = []
    for red, green, blue, alpha in image.getdata():
        if red > 240 and green > 240 and blue > 240:
            pixels.append((red, green, blue, 0))
        else:
            pixels.append((red, green, blue, alpha))
    image.putdata(pixels)
    save_image(image, output_path, "png")


def image_to_svg(input_path: Path, output_path: Path) -> None:
    image = open_image(input_path).convert("RGBA")
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    output_path.write_text(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{image.width}" height="{image.height}" '
        f'viewBox="0 0 {image.width} {image.height}"><image width="100%" height="100%" '
        f'href="data:image/png;base64,{encoded}"/></svg>',
        encoding="utf-8",
    )
