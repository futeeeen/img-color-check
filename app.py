from __future__ import annotations

import uuid
from io import BytesIO
from pathlib import Path

from flask import Flask, jsonify, render_template, request, send_file, url_for
from PIL import Image, ImageOps, UnidentifiedImageError

from palette_generator import extract_palette, render_palette_image


BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "ui-output"
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}


app = Flask(__name__)


def parse_int(name: str, default: int, minimum: int, maximum: int) -> int:
    try:
        value = int(request.form.get(name, default))
    except (TypeError, ValueError):
        return default
    return max(minimum, min(maximum, value))


def parse_float(name: str, default: float, minimum: float, maximum: float) -> float:
    try:
        value = float(request.form.get(name, default))
    except (TypeError, ValueError):
        return default
    return max(minimum, min(maximum, value))


def load_upload_image() -> Image.Image:
    upload = request.files.get("image")
    if upload is None or upload.filename == "":
        raise ValueError("請選擇圖片")

    suffix = Path(upload.filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise ValueError("不支援的圖片格式")

    try:
        image = Image.open(BytesIO(upload.read()))
        return ImageOps.exif_transpose(image).convert("RGB")
    except UnidentifiedImageError as exc:
        raise ValueError("圖片無法讀取") from exc


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/generate")
def generate():
    try:
        image = load_upload_image()
        palette_count = parse_int("palette_count", 10, 4, 14)
        order = request.form.get("order", "cinematic")
        if order not in {"cinematic", "luminance", "hue"}:
            order = "cinematic"

        canvas_width = parse_int("canvas_width", 1179, 720, 1800)
        image_height = parse_int("image_height", 650, 360, 1100)
        swatch_height = parse_int("swatch_height", 214, 96, 420)
        padding = parse_int("padding", 8, 0, 48)
        gutter = parse_int("gutter", 8, 0, 48)
        saliency_strength = parse_float("saliency_strength", 0.85, 0.0, 2.0)
        subject_boost = parse_float("subject_boost", 0.45, 0.0, 2.0)
        local_protection = parse_float("local_protection", 0.0, 0.0, 2.0)

        colors = extract_palette(
            image,
            palette_count=palette_count,
            max_edge=768,
            clusters=max(18, palette_count * 2 + 2),
            max_samples=80000,
            saliency_strength=saliency_strength,
            subject_boost=subject_boost,
            local_protection=local_protection,
            seed=7,
            order=order,
        )

        output_id = uuid.uuid4().hex
        output_path = OUTPUT_DIR / f"{output_id}.png"
        render_palette_image(
            image,
            colors,
            output_path,
            canvas_width=canvas_width,
            image_height=image_height,
            swatch_height=swatch_height,
            padding=padding,
            gutter=gutter,
        )

        hex_colors = ["#{:02X}{:02X}{:02X}".format(*color.rgb) for color in colors]
        return jsonify(
            {
                "image_url": url_for("preview", file_id=output_id),
                "download_url": url_for("download", file_id=output_id),
                "colors": hex_colors,
            }
        )
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400


@app.get("/preview/<file_id>")
def preview(file_id: str):
    return send_file(OUTPUT_DIR / f"{file_id}.png", mimetype="image/png")


@app.get("/download/<file_id>")
def download(file_id: str):
    return send_file(
        OUTPUT_DIR / f"{file_id}.png",
        mimetype="image/png",
        as_attachment=True,
        download_name="palette-result.png",
    )


if __name__ == "__main__":
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    app.run(host="127.0.0.1", port=7860, debug=False)
