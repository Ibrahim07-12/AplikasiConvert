"""Backend mirror of the frontend dual format mapping."""

from typing import Final

FORMAT_MAPPING: Final[dict[str, tuple[str, ...]]] = {
    "jpg": ("png", "webp", "pdf", "svg"),
    "jpeg": ("png", "webp", "pdf", "svg"),
    "png": ("jpg", "webp", "pdf", "svg"),
    "webp": ("jpg", "png", "pdf", "svg"),
    "svg": ("png", "jpg", "pdf"),
    "pdf": ("jpg", "png", "docx", "xlsx", "pptx"),
    "docx": ("pdf", "jpg", "png"),
    "doc": ("pdf", "jpg", "png"),
    "xlsx": ("pdf", "csv", "jpg"),
    "xls": ("pdf", "csv", "jpg"),
    "pptx": ("pdf", "jpg", "png", "docx"),
    "ppt": ("pdf", "docx", "jpg", "png"),
    "html": ("pdf", "jpg", "png"),
    "htm": ("pdf", "jpg", "png"),
}
