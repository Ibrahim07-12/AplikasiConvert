"""FastAPI entry point for the Universal Converter PWA."""

from __future__ import annotations

import re
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Annotated

from fastapi import BackgroundTasks, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .converter import (
    EXTENSION_TO_PILLOW_FORMAT,
    SUPPORTED_FORMATS,
    ConversionError,
    convert_image,
    get_file_category,
)
from .document_converter import convert_office_to_pdf
from .format_mapping import FORMAT_MAPPING
from .pdf_converter import convert_pdf_to_images

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "frontend"
MAX_UPLOAD_SIZE = 25 * 1024 * 1024
MAX_BATCH_FILES = 10
SAFE_FILENAME = re.compile(r"[^A-Za-z0-9._-]+")

app = FastAPI(title="Universal Converter", version="1.0.0")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


def cleanup_directory(directory: Path) -> None:
    """Delete temporary input/output files after the response is sent."""
    shutil.rmtree(directory, ignore_errors=True)


@app.get("/", include_in_schema=False)
async def home() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/manifest.webmanifest", include_in_schema=False)
async def manifest() -> FileResponse:
    return FileResponse(STATIC_DIR / "manifest.webmanifest")


@app.get("/sw.js", include_in_schema=False)
async def service_worker() -> FileResponse:
    return FileResponse(STATIC_DIR / "sw.js", media_type="application/javascript")


@app.get("/api/formats")
@app.get("/supported-formats")
async def formats() -> dict[str, object]:
    """Expose the format list used by the frontend selector."""
    return {"categories": SUPPORTED_FORMATS, "mapping": FORMAT_MAPPING}


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


async def save_upload(file: UploadFile, directory: Path) -> Path:
    """Save an upload with a size limit and a safe filename."""
    safe_name = SAFE_FILENAME.sub("_", file.filename or "upload")
    input_path = directory / safe_name
    size = 0
    with input_path.open("wb") as destination:
        while chunk := await file.read(1024 * 1024):
            size += len(chunk)
            if size > MAX_UPLOAD_SIZE:
                raise HTTPException(
                    status_code=413, detail="Ukuran file melebihi batas 25 MB."
                )
            destination.write(chunk)
    return input_path


def convert_file(input_path: Path, category: str, target: str, directory: Path) -> list[Path]:
    """Route one file to the appropriate conversion engine."""
    output_path = directory / f"converted.{target}"
    if category == "image" and target in EXTENSION_TO_PILLOW_FORMAT:
        convert_image(input_path, output_path, target)
        return [output_path]
    if category == "document" and target == "pdf":
        return [convert_office_to_pdf(input_path, directory)]
    if category == "pdf" and target in {"jpg", "png"}:
        return convert_pdf_to_images(input_path, directory, target)
    raise ConversionError("Kombinasi format sumber dan tujuan belum didukung.")


@app.post("/api/convert")
@app.post("/convert")
async def convert(
    background_tasks: BackgroundTasks,
    file: Annotated[UploadFile, File(description="File yang akan dikonversi")],
    target_format: Annotated[str, Form(description="Format tujuan")],
) -> FileResponse:
    """Convert an upload and remove all temporary files after download."""
    target = target_format.lower().lstrip(".")
    category = get_file_category(file.filename or "", file.content_type)
    if category is None or target not in SUPPORTED_FORMATS.get(category, ()):
        raise HTTPException(status_code=415, detail="Format sumber atau tujuan tidak didukung.")

    temporary_directory = Path(tempfile.mkdtemp(prefix="universal-converter-"))

    try:
        input_path = await save_upload(file, temporary_directory)
        output_paths = convert_file(input_path, category, target, temporary_directory)
        if len(output_paths) > 1:
            output_path = temporary_directory / "converted-pages.zip"
            with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as archive:
                for converted_path in output_paths:
                    archive.write(converted_path, arcname=converted_path.name)
            download_name = f"{Path(file.filename or 'converted').stem}-pages.zip"
            download_type = "application/zip"
        else:
            output_path = output_paths[0]
            download_name = f"{Path(file.filename or 'converted').stem}.{target}"
            download_type = None
    except HTTPException:
        cleanup_directory(temporary_directory)
        raise
    except ConversionError as error:
        cleanup_directory(temporary_directory)
        raise HTTPException(status_code=422, detail=str(error)) from error
    except OSError as error:
        cleanup_directory(temporary_directory)
        raise HTTPException(
            status_code=500, detail="Gagal menyiapkan file konversi."
        ) from error
    finally:
        await file.close()

    background_tasks.add_task(cleanup_directory, temporary_directory)
    return FileResponse(
        output_path,
        filename=download_name,
        media_type=download_type,
        background=background_tasks,
    )


@app.post("/api/convert/batch")
@app.post("/convert/batch")
async def convert_batch(
    background_tasks: BackgroundTasks,
    files: Annotated[list[UploadFile], File(description="File yang akan dikonversi")],
    target_format: Annotated[str, Form(description="Format tujuan")],
) -> FileResponse:
    """Convert multiple files and return the results as a temporary ZIP."""
    if not files or len(files) > MAX_BATCH_FILES:
        raise HTTPException(status_code=400, detail="Batch harus berisi 1 sampai 10 file.")

    target = target_format.lower().lstrip(".")
    temporary_directory = Path(tempfile.mkdtemp(prefix="universal-converter-batch-"))
    try:
        converted_paths: list[Path] = []
        for file in files:
            category = get_file_category(file.filename or "", file.content_type)
            if category is None or target not in SUPPORTED_FORMATS.get(category, ()):
                raise HTTPException(
                    status_code=415,
                    detail=f"Format tidak didukung: {file.filename or 'file'}",
                )
            input_path = await save_upload(file, temporary_directory)
            converted_paths.extend(
                convert_file(input_path, category, target, temporary_directory)
            )
            await file.close()

        archive_path = temporary_directory / "converted-files.zip"
        with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as archive:
            for index, converted_path in enumerate(converted_paths, start=1):
                archive.write(converted_path, arcname=f"{index}-{converted_path.name}")
    except HTTPException:
        cleanup_directory(temporary_directory)
        raise
    except ConversionError as error:
        cleanup_directory(temporary_directory)
        raise HTTPException(status_code=422, detail=str(error)) from error
    except OSError as error:
        cleanup_directory(temporary_directory)
        raise HTTPException(status_code=500, detail="Batch konversi gagal.") from error

    background_tasks.add_task(cleanup_directory, temporary_directory)
    return FileResponse(
        archive_path,
        filename="converted-files.zip",
        media_type="application/zip",
        background=background_tasks,
    )
