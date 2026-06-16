# Image Color Check

Generate cinematic color-palette images from photos. The first version extracts a perceptual palette, renders the original image on top, and draws equal-width color swatches below it.

## Development Tools Used

This project is currently implemented as a Python CLI.

Tools and libraries used during development:

- Python 3.13
- Pillow: image loading, EXIF orientation handling, and final PNG rendering
- NumPy: pixel and color-space calculations
- OpenCV: local contrast, edge/detail maps, and color conversion helpers
- scikit-learn: weighted MiniBatchKMeans clustering
- OKLab / OKLCH conversion implemented in `palette_generator.py`

Open-source projects evaluated while planning this MVP:

- [Color Thief](https://github.com/lokesh/color-thief): mature browser/Node.js dominant color extraction.
- [color-thief-py](https://github.com/fengsp/color-thief-py): Python port of Color Thief using Pillow.
- [vibrant-python](https://github.com/totallynotadi/vibrant-python): Python port inspired by Android-style vibrant/muted palette roles.

The current MVP does not vendor code from those projects. It uses Python image-processing libraries directly because this project needs custom weighting, OKLab distance, validation-crop handling, and the final reference-style image layout.

## Install

```powershell
python -m pip install -r requirements.txt
```

## Usage

Generate one palette image:

```powershell
python palette_generator.py path\to\photo.jpg --output-dir output
```

Start the local web UI:

```powershell
python app.py
```

Then open `http://127.0.0.1:7860`.

The UI supports:

- Image upload.
- Palette count.
- Sorting mode.
- Output dimensions.
- White border and divider thickness.
- Subject and saliency weighting.
- Local color protection with off / weak / medium / strong levels for small but important regions.
- Tooltips explaining what each parameter affects.
- PNG preview and download.

Generate palette images for a directory:

```powershell
python palette_generator.py valid-used --output-dir output\valid-used --crop-source auto-palette --json
```

`--crop-source auto-palette` is useful for validation images that already contain a palette strip. It detects the white divider and uses only the top photo region as the source image.

## Current MVP Pipeline

1. Load and normalize the source image.
2. Optionally crop away an existing palette strip for validation.
3. Resize a copy of the image for analysis.
4. Convert sampled pixels from sRGB to OKLab.
5. Build a pixel weight map from:
   - area
   - saturation
   - center subject bias
   - local contrast
   - edge/detail strength
   - exposure quality
6. Run weighted MiniBatchKMeans.
7. Merge perceptually similar colors.
8. Select a 10-color palette with dark, light, chromatic, and high-score candidates.
9. Sort colors with a cinematic hue-band order, using dark anchors first and then a continuous heavy-to-light or heavy-light-heavy color path.
10. Render the final palette image.

## Validation Target

The `valid-used/` folder contains final-target reference images. They are used as visual comparison material for the desired output format and color quality.

Run:

```powershell
python palette_generator.py valid-used --output-dir output\valid-used --crop-source auto-palette --json
```

Then compare generated files under `output/valid-used/` against the references in `valid-used/`.
