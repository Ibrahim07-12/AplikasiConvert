"""Single source of truth for supported source and target extensions."""

from __future__ import annotations

from typing import Final


FORMAT_MAPPING: Final[dict[str, tuple[str, ...]]] = {
    "jpg": ("png", "webp", "pdf"),
    "jpeg": ("png", "webp", "pdf"),
    "png": ("jpg", "webp", "pdf"),
    "webp": ("jpg", "png", "pdf"),
    "pdf": ("jpg", "png"),
    "docx": ("pdf",),
    "doc": ("pdf",),
    "xlsx": ("pdf",),
    "xls": ("pdf",),
    "pptx": ("pdf",),
    "ppt": ("pdf",),
}
