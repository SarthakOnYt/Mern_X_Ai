from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
import os

def generate_pdf(metrics, chart_paths, model_name, output_path="benchmark_report.pdf"):
    c = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4

    # Title
    c.setFont("Helvetica-Bold", 20)
    c.drawString(2 * cm, height - 2 * cm, f"Benchmark Report - {model_name}")

    # Metrics
    c.setFont("Helvetica", 12)
    y = height - 4 * cm
    for key, value in metrics.items():
        c.drawString(2 * cm, y, f"{key.replace('_', ' ').capitalize()}: {value}")
        y -= 1 * cm
        if y < 5 * cm:
            c.showPage()
            y = height - 2 * cm
            c.setFont("Helvetica", 12)

    # Charts on one page (2 columns x 3 rows)
    chart_width = 8 * cm
    chart_height = 6 * cm
    padding_x = 2 * cm
    padding_y = 2 * cm
    spacing_x = 1.5 * cm
    spacing_y = 2 * cm

    c.showPage()
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width / 2, height - 2 * cm, "Benchmark Charts")

    # Adjusted top margin to shift charts down ~15px (≈0.4 cm)
    top_margin = height - 3 * cm

    x_positions = [padding_x, padding_x + chart_width + spacing_x]
    y_positions = [
        top_margin - chart_height,               # Row 1
        top_margin - chart_height * 2 - spacing_y,  # Row 2
        top_margin - chart_height * 3 - spacing_y * 2  # Row 3
    ]

    i = 0
    for title, img_path in chart_paths.items():
        if os.path.exists(img_path):
            col = i % 2
            row = i // 2
            x = x_positions[col]
            y = y_positions[row]
            c.setFont("Helvetica", 12)
            c.drawString(x, y + chart_height + 0.2 * cm, title.replace('_', ' ').capitalize())
            c.drawImage(img_path, x, y, width=chart_width, height=chart_height, preserveAspectRatio=True)
            i += 1

    c.save()
    print(f"✅ PDF report saved to: {output_path}")
