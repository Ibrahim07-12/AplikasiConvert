"""Local PDF tool operations powered by PyMuPDF."""

from __future__ import annotations

import zipfile
from pathlib import Path

import fitz
from docx import Document
from docx.shared import Inches
from openpyxl import Workbook
from openpyxl.drawing.image import Image as SpreadsheetImage
from pptx import Presentation
from pptx.util import Inches as PptInches

from ..converter import ConversionError


def pdf_tool(
    input_paths: list[Path],
    output_directory: Path,
    tool: str,
    target_format: str = "png",
    pages: str = "",
    angle: int = 90,
    password: str = "",
) -> list[Path]:
    """Run a PDF tool and return generated files."""
    if not input_paths:
        raise ConversionError("Minimal satu file PDF diperlukan.")
    source = input_paths[0]
    try:
        if tool == "merge":
            result = fitz.open()
            for path in input_paths:
                with fitz.open(path) as document:
                    result.insert_pdf(document)
            output = output_directory / "merged.pdf"
            result.save(output)
            result.close()
            return [output]

        with fitz.open(source) as document:
            if tool == "split" or tool == "remove-pages":
                selected = _page_numbers(pages, len(document))
                if tool == "remove-pages":
                    selected = [number for number in range(len(document)) if number not in selected]
                outputs = []
                for number in selected:
                    result = fitz.open()
                    result.insert_pdf(document, from_page=number, to_page=number)
                    output = output_directory / f"page-{number + 1}.pdf"
                    result.save(output)
                    result.close()
                    outputs.append(output)
                return _zip_outputs(outputs, output_directory, "pdf-pages.zip") if len(outputs) > 1 else outputs
            if tool in {"rotate-pages", "compress", "add-page-numbers", "protect"}:
                result = fitz.open()
                result.insert_pdf(document)
                if tool == "rotate-pages":
                    for page in result:
                        page.set_rotation((page.rotation + angle) % 360)
                elif tool == "add-page-numbers":
                    for index, page in enumerate(result, start=1):
                        page.insert_text((36, page.rect.height - 20), str(index), fontsize=9)
                output = output_directory / f"{tool}.pdf"
                if tool == "protect":
                    if not password:
                        raise ConversionError("Password wajib diisi untuk protect.")
                    result.save(output, encryption=fitz.PDF_ENCRYPT_AES_256, owner_pw=password, user_pw=password)
                elif tool == "compress":
                    result.save(output, garbage=4, deflate=True, clean=True)
                else:
                    result.save(output)
                result.close()
                return [output]
            if tool in {"to-images", "convert"}:
                extension = target_format.lower().lstrip(".")
                outputs = []
                for index, page in enumerate(document, start=1):
                    pixmap = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5), alpha=False)
                    output = output_directory / f"page-{index}.{extension}"
                    pixmap.save(str(output), output="jpeg" if extension in {"jpg", "jpeg"} else extension)
                    outputs.append(output)
                return _zip_outputs(outputs, output_directory, "pdf-images.zip") if len(outputs) > 1 else outputs
            if tool == "extract-text":
                output = output_directory / "extracted-text.txt"
                output.write_text("\n\n".join(page.get_text() for page in document), encoding="utf-8")
                return [output]
    except (OSError, fitz.FileDataError, ValueError) as error:
        raise ConversionError("Operasi PDF gagal. Pastikan file PDF valid.") from error
    raise ConversionError(f"Tool PDF belum dikenali: {tool}")


def pdf_to_office(input_path: Path, output_directory: Path, target_format: str) -> Path:
    """Create an editable Office container with each PDF page as an image."""
    target = target_format.lower().lstrip(".")
    if target not in {"docx", "xlsx", "pptx"}:
        raise ConversionError(f"Output Office tidak didukung: {target}")
    image_paths: list[Path] = []
    with fitz.open(input_path) as document:
        for index, page in enumerate(document, start=1):
            image_path = output_directory / f"office-page-{index}.png"
            page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5), alpha=False).save(str(image_path))
            image_paths.append(image_path)

    output = output_directory / f"converted.{target}"
    if target == "docx":
        document = Document()
        for index, image_path in enumerate(image_paths):
            if index:
                document.add_page_break()
            document.add_picture(str(image_path), width=Inches(6.5))
        document.save(output)
    elif target == "xlsx":
        workbook = Workbook()
        sheet = workbook.active
        for index, image_path in enumerate(image_paths, start=1):
            if index > 1:
                sheet = workbook.create_sheet(f"Page {index}")
            sheet.add_image(SpreadsheetImage(str(image_path)), "A1")
        workbook.save(output)
    else:
        presentation = Presentation()
        presentation.slide_width = PptInches(10)
        presentation.slide_height = PptInches(7.5)
        blank_layout = presentation.slide_layouts[6]
        for image_path in image_paths:
            slide = presentation.slides.add_slide(blank_layout)
            slide.shapes.add_picture(str(image_path), 0, 0, width=presentation.slide_width)
        presentation.save(output)
    return output


def _page_numbers(value: str, total: int) -> list[int]:
    try:
        numbers = {int(item.strip()) - 1 for item in value.split(",") if item.strip()}
    except ValueError as error:
        raise ConversionError("Nomor halaman harus berupa angka, contoh: 1,3.") from error
    if not numbers or any(number < 0 or number >= total for number in numbers):
        raise ConversionError(f"Nomor halaman harus berada antara 1 dan {total}.")
    return sorted(numbers)


def _zip_outputs(paths: list[Path], directory: Path, name: str) -> list[Path]:
    archive_path = directory / name
    with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in paths:
            archive.write(path, arcname=path.name)
    return [archive_path]
