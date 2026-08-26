import io
import os

from flask import Flask, render_template, request, send_file
from PIL import Image as PILImage
from pdf2image import convert_from_bytes
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import inch, cm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

app = Flask(__name__)


def generate_pdf(jpg_bytes, pdf_bytes):
    # Convert first page of uploaded PDF into an image
    pdf_images = convert_from_bytes(
        pdf_bytes,
        first_page=1,
        last_page=1
    )

    pdf_img_buffer = io.BytesIO()
    pdf_images[0].save(pdf_img_buffer, format="PNG")
    pdf_img_buffer.seek(0)

    # Output PDF buffer
    output = io.BytesIO()

    # Page setup
    page_width, page_height = landscape(A4)
    margin = 0.5 * inch
    gap = 1.5 * cm

    jpg_w = 4.0 * inch
    jpg_h = 6.0 * inch

    pdf_x = margin + jpg_w + gap
    pdf_w = page_width - margin - pdf_x
    pdf_h = page_height - (2 * margin)

    jpg_x = margin
    jpg_y = (page_height - jpg_h) / 2
    pdf_y = margin

    c = canvas.Canvas(output, pagesize=landscape(A4))
    c.setLineWidth(1)
    c.setStrokeColorRGB(0, 0, 0)

    # Left JPG
    jpg_reader = ImageReader(io.BytesIO(jpg_bytes))
    c.rect(jpg_x, jpg_y, jpg_w, jpg_h)
    c.drawImage(
        jpg_reader,
        jpg_x,
        jpg_y,
        width=jpg_w,
        height=jpg_h,
        preserveAspectRatio=False
    )

    # Right PDF
    pdf_reader = ImageReader(pdf_img_buffer)
    c.rect(pdf_x, pdf_y, pdf_w, pdf_h)
    c.drawImage(
        pdf_reader,
        pdf_x,
        pdf_y,
        width=pdf_w,
        height=pdf_h,
        preserveAspectRatio=True,
        anchor="c"
    )

    c.save()
    output.seek(0)
    return output


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        jpg_file = request.files.get("jpg_file")
        pdf_file = request.files.get("pdf_file")

        if not jpg_file or not pdf_file:
            return "Please upload both files.", 400

        try:
            output_pdf = generate_pdf(
                jpg_file.read(),
                pdf_file.read()
            )

            return send_file(
                output_pdf,
                mimetype="application/pdf",
                as_attachment=True,
                download_name="aligned_document.pdf"
            )

        except Exception as e:
            return f"Error processing files: {e}", 500

    return render_template("index.html")


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000))
    )
