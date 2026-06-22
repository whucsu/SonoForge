"""Export measurement report text to PDF."""

from __future__ import annotations

from pathlib import Path


class PdfExportError(RuntimeError):
    """Raised when PDF export cannot be completed."""


def export_measurement_report_pdf(text: str, output_path: Path) -> Path:
    """Write report text to a PDF file and return the path."""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.pdfgen import canvas
    except ImportError as exc:
        raise PdfExportError(
            "Для экспорта PDF установите зависимость reportlab: "
            "pip install 'echo-personal-tool[phase2]'"
        ) from exc

    font_name = _register_cyrillic_font(pdfmetrics, TTFont)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    page_width, page_height = A4
    margin_x = 18 * mm
    margin_y = 18 * mm
    line_height = 5 * mm
    font_size = 10

    pdf = canvas.Canvas(str(output_path), pagesize=A4)
    pdf.setTitle("Результаты измерений")
    pdf.setFont(font_name, font_size)

    y = page_height - margin_y
    for raw_line in text.splitlines():
        line = raw_line or " "
        if y < margin_y:
            pdf.showPage()
            pdf.setFont(font_name, font_size)
            y = page_height - margin_y
        pdf.drawString(margin_x, y, line)
        y -= line_height

    pdf.save()
    return output_path


def _register_cyrillic_font(pdfmetrics: object, TTFont: object) -> str:
    candidates = (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/TTF/DejaVuSans.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    )
    for path in candidates:
        font_path = Path(path)
        if font_path.is_file():
            pdfmetrics.registerFont(TTFont("ReportCyrillic", str(font_path)))
            return "ReportCyrillic"
    raise PdfExportError(
        "Не найден TTF-шрифт с кириллицей (DejaVu/Liberation) для PDF-экспорта."
    )
