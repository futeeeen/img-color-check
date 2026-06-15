# Image Color Palette Generator Implementation Plan

## Goal

Build a tool that can analyze a photo, extract the image's main perceptual colors, generate a visually pleasing color palette, and export a composed image similar to the provided references:

- Original image on top.
- A row of color swatches below.
- White spacing and borders.
- Palette colors that preserve the image's subject, mood, contrast, and important visual information.

The tool should avoid naive "most frequent pixel color" extraction. Instead, it should consider color space conversion, saliency weighting, subject importance, color harmony, and palette ordering.

## Core Principle

The main colors of an image are not simply the colors with the largest pixel area.

A good palette should be selected by combining:

- Pixel area.
- Visual saliency.
- Subject importance.
- Saturation.
- Contrast.
- Exposure quality.
- Emotional relevance.
- Color diversity.

This makes the output feel closer to the image's theme and mood instead of producing dull, repetitive, or misleading colors.

## Recommended Pipeline

### 1. Image Loading And Preprocessing

Load the source image and prepare two versions:

- `original_image`: kept at full quality for final output.
- `analysis_image`: resized to a manageable size for faster analysis.

Recommended analysis size:

- Long edge: `512px` to `1024px`.
- Preserve aspect ratio.

Preprocessing steps:

1. Load image with Pillow or OpenCV.
2. Normalize orientation from EXIF metadata.
3. Convert image to RGB.
4. Optionally remove transparent pixels if PNG input contains alpha.
5. Resize for analysis.
6. Convert from sRGB to a perceptual color space.

## 2. Color Space Conversion

Do not cluster directly in RGB. RGB distances do not match human color perception.

Recommended working color spaces:

- `OKLab` / `OKLCH`: preferred for modern perceptual color work.
- `CIELAB` / `LCH`: mature and widely supported.
- `CAM16-UCS`: advanced option, useful if viewing conditions need to be modeled.

Recommended MVP:

- Use `OKLab` for clustering and distance calculation.
- Use `OKLCH` for palette ordering and lightness/chroma adjustment.

Basic flow:

```text
sRGB image
-> linear RGB
-> OKLab
-> OKLCH when hue/chroma/lightness ordering is needed
```

## 3. Pixel Weighting

Each pixel should have a final weight that represents its importance to the palette.

Recommended formula:

```text
final_weight =
  area_weight
  * saliency_weight
  * saturation_weight
  * contrast_weight
  * subject_weight
  * detail_weight
  * exposure_quality_weight
```

### Weight Components

#### Area Weight

Represents how often a color appears in the image.

Purpose:

- Preserve dominant atmosphere.
- Prevent tiny noise colors from entering the palette.

Risk:

- If used alone, large backgrounds such as sky, grass, sea, or shadows can dominate the whole palette.

#### Saliency Weight

Represents how visually noticeable a pixel or region is.

Possible methods:

- OpenCV saliency detection.
- Center-weighted saliency.
- Edge and contrast-based saliency.
- Deep learning saliency model.

Purpose:

- Preserve visual focus.
- Prevent important subjects from being ignored.

#### Saturation Weight

Boosts moderately saturated colors.

Purpose:

- Preserve emotional and expressive colors.
- Keep accent colors such as red clothing, golden light, cyan highlights, or skin warmth.

Important:

- Do not overboost extremely saturated noise or compression artifacts.
- Use a smooth curve instead of a hard multiplier.

#### Contrast Weight

Boosts colors that differ from nearby regions.

Purpose:

- Preserve important foreground/background separation.
- Keep small but meaningful colors.

Examples:

- Red sweater against dark green background.
- Bright cyan reflection in a dark blue scene.
- Warm skin tone against cool environment.

#### Subject Weight

Boosts pixels that belong to the main subject.

Possible methods:

- Face detection.
- Person detection.
- Semantic segmentation.
- Object detection.
- Center-weighted foreground estimation.

Recommended MVP:

- Use center weighting and edge/contrast as a lightweight proxy.

Recommended advanced version:

- Use segmentation or object detection to identify subject regions.

#### Detail Weight

Boosts visually detailed areas.

Possible signals:

- Edge density.
- Local variance.
- Laplacian magnitude.

Purpose:

- Preserve meaningful details.
- Avoid flat backgrounds completely dominating the palette.

#### Exposure Quality Weight

Reduces low-information pixels.

Downweight:

- Pure white overexposure.
- Crushed black without detail.
- Compression artifacts.

Important:

- Do not remove dark colors entirely.
- Some images rely on deep shadows as a key mood color.

## 4. Saliency Strategy

Use a tiered saliency design so the tool can evolve.

### MVP Saliency

Use lightweight signals:

- Center bias.
- Edge density.
- Local contrast.
- Saturation.
- Exposure quality.

This is fast and does not require large models.

### Intermediate Saliency

Add region-level detection:

- Foreground/background separation.
- Face/person detection.
- Sky, sea, vegetation, skin, and clothing segmentation.

### Advanced Saliency

Use semantic models:

- SAM for segmentation.
- YOLO for objects/person detection.
- MediaPipe for face and person signals.
- CLIP-like image-text models for theme-aware weighting.

## 5. Color Clustering

Use weighted clustering in a perceptual color space.

Recommended algorithm:

- Weighted KMeans or MiniBatchKMeans in OKLab.

Suggested process:

1. Sample pixels from the analysis image.
2. Convert sampled pixels to OKLab.
3. Compute pixel weights.
4. Run weighted clustering with more clusters than the final palette needs.
5. Generate candidate colors.
6. Merge colors that are too perceptually close.
7. Rank candidates.
8. Select final palette.

Recommended values:

```text
initial_cluster_count = 16 to 24
final_palette_count = 8 to 12
default_palette_count = 10
```

## 6. Candidate Color Merging

After clustering, merge colors that are too similar.

Use perceptual distance instead of RGB distance.

Possible distance metrics:

- OKLab Euclidean distance.
- Delta E in CIELAB.

Merge rules:

- Merge candidates with very close lightness, chroma, and hue.
- Preserve the candidate with higher combined importance.
- Or compute a weighted average in OKLab.

Purpose:

- Avoid repeated colors.
- Prevent palettes like five similar greens or four near-identical dark blues.

## 7. Candidate Ranking

Each candidate color should receive a score.

Recommended scoring factors:

```text
candidate_score =
  weighted_area_score
  + saliency_score
  + subject_score
  + saturation_score
  + contrast_score
  + mood_score
  + diversity_bonus
```

### Ranking Goals

The selected palette should include:

- Dominant atmosphere colors.
- Important subject colors.
- Accent colors.
- Shadow colors.
- Highlight colors.
- Enough diversity to describe the image.

## 8. Palette Role Allocation

Instead of selecting only the top N colors, allocate palette slots by role.

Recommended 10-color palette structure:

```text
3 dominant atmosphere colors
2 shadow or deep tone colors
2 subject colors
2 accent or emotional colors
1 highlight or air color
```

This structure helps avoid losing important information.

Example:

- A beach scene should not become only sky and sea colors.
- A portrait should not lose skin, clothing, or eye-catching accents.
- A dark cinematic scene should preserve deep blues and blacks while keeping luminous highlights.

## 9. Color Beautification

Raw extracted colors can be accurate but visually muddy.

Apply subtle perceptual cleanup:

- Slightly reduce dirty low-chroma noise.
- Preserve natural colors such as skin, sky, sea, and vegetation.
- Avoid oversaturating the image's mood.
- Keep hue shifts minimal.
- Preserve important dark and light colors.

Recommended adjustment space:

- Use `OKLCH`.

Possible adjustments:

- Clamp extreme chroma.
- Slightly raise chroma for dull but meaningful accent colors.
- Normalize near-black colors so they remain printable/viewable.
- Avoid pure white or pure black unless visually important.

Important:

- Beautification should be conservative.
- The palette should still feel extracted from the image, not redesigned from scratch.

## 10. Palette Ordering

Color order affects how the final image feels.

Supported ordering modes:

- `luminance`: dark to light.
- `hue`: sorted by hue angle.
- `narrative`: shadow -> background -> subject -> accent -> highlight.
- `mood`: arranged for visual rhythm and emotional progression.

Recommended default:

```text
Group by hue family.
Within each group, sort by lightness.
Place the darkest anchor color near the left.
Place the strongest accent or brightest highlight near the right.
```

This usually creates a cinematic progression similar to the references.

## 11. Output Image Composition

Generate a final image with:

- Original image area on top.
- Palette row below.
- White border and dividers.

Recommended layout:

```text
canvas_width = 1200
outer_padding = 8 to 12
image_area_height = 650
palette_height = 220
divider_size = 8
swatch_count = 10
```

Layout rules:

1. Fit or crop image into the top area.
2. Preserve a visually pleasing crop.
3. Add white separator between image and palette.
4. Draw equal-width color swatches.
5. Add white gutters between swatches.
6. Export as PNG or high-quality JPG.

## 12. MVP Feature Set

The first version should include:

1. Upload or provide an image file.
2. Normalize and resize image for analysis.
3. Convert colors to OKLab.
4. Compute pixel weights using:
   - Area.
   - Saturation.
   - Center bias.
   - Local contrast.
   - Edge/detail strength.
   - Exposure quality.
5. Run weighted KMeans.
6. Extract 16 to 24 candidate colors.
7. Merge similar colors.
8. Select final 10 colors.
9. Sort palette using the default cinematic ordering.
10. Render output image.

## 13. Advanced Feature Set

Future versions can add:

- Face detection.
- Person detection.
- Semantic segmentation.
- Subject/background separation.
- Multiple palette styles:
  - Natural.
  - Cinematic.
  - Brand.
  - Soft.
  - High contrast.
  - Pastel.
- Manual palette editing.
- Lock a color.
- Replace a swatch.
- Export:
  - PNG palette image.
  - JSON.
  - CSS variables.
  - ASE.
  - GPL.
  - SVG.
- Batch processing.

## 14. Suggested Python Stack

Recommended packages:

- `Pillow`: image loading and final rendering.
- `numpy`: pixel operations.
- `opencv-python`: saliency, edge detection, contrast maps.
- `scikit-learn`: weighted KMeans or MiniBatchKMeans.
- `scikit-image`: color utilities and image processing.
- `colour-science`: optional advanced color conversion.

Optional advanced packages:

- `mediapipe`: face/person landmarks.
- `ultralytics`: YOLO object detection.
- `segment-anything`: advanced segmentation.

## 15. Suggested Web App Stack

If building a web interface:

- Frontend: React or Next.js.
- Backend: Python FastAPI.
- Processing: Python image pipeline.
- Output: downloadable PNG/JPG.

Possible UI controls:

- Palette count.
- Extraction mode.
- Ordering mode.
- Mood/style mode.
- Saliency strength.
- Subject boost.
- Export format.

## 16. Quality Checks

Use these checks before accepting a generated palette:

- Are there enough distinct colors?
- Does the palette preserve the main subject?
- Does it include the image's emotional accent color?
- Does it avoid too many near-duplicate colors?
- Does it preserve both shadow and highlight mood?
- Does it avoid dead black/white unless important?
- Does the output look like it belongs to the original image?
- Would a designer find the palette usable?

## 17. Common Failure Modes

### Too Many Background Colors

Cause:

- Area weight dominates.

Fix:

- Increase saliency and subject weighting.
- Limit per-region palette slots.

### Important Accent Color Missing

Cause:

- Accent is small in area.

Fix:

- Increase contrast and saturation weights.
- Add accent color allocation.

### Palette Looks Muddy

Cause:

- Raw cluster centers are low-chroma averages.

Fix:

- Use OKLCH cleanup.
- Avoid averaging across different hue families.

### Palette Has Repeated Colors

Cause:

- Similar clusters were not merged.

Fix:

- Increase perceptual merge threshold.
- Add diversity bonus during selection.

### Palette Does Not Match Mood

Cause:

- Over-normalization or excessive beautification.

Fix:

- Preserve original color cast.
- Reduce correction strength.
- Keep shadow/highlight anchors.

## 18. Implementation Order

Recommended order:

1. Build a command-line prototype.
2. Implement image loading and output composition.
3. Implement OKLab conversion.
4. Implement basic pixel weighting.
5. Implement weighted clustering.
6. Implement candidate merging.
7. Implement palette selection.
8. Implement palette ordering.
9. Tune against the provided reference images.
10. Add web UI after the pipeline is stable.

