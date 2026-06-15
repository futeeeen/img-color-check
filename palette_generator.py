from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import cv2
import numpy as np
from PIL import Image, ImageOps
from sklearn.cluster import MiniBatchKMeans


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}


@dataclass(eq=False)
class PaletteColor:
    lab: np.ndarray
    rgb: tuple[int, int, int]
    score: float
    weight: float
    lightness: float
    chroma: float
    hue: float


def srgb_to_linear(rgb: np.ndarray) -> np.ndarray:
    rgb = np.clip(rgb, 0.0, 1.0)
    return np.where(rgb <= 0.04045, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4)


def linear_to_srgb(rgb: np.ndarray) -> np.ndarray:
    rgb = np.clip(rgb, 0.0, 1.0)
    return np.where(rgb <= 0.0031308, rgb * 12.92, 1.055 * np.power(rgb, 1 / 2.4) - 0.055)


def linear_rgb_to_oklab(rgb: np.ndarray) -> np.ndarray:
    lms = rgb @ np.array(
        [
            [0.4122214708, 0.2119034982, 0.0883024619],
            [0.5363325363, 0.6806995451, 0.2817188376],
            [0.0514459929, 0.1073969566, 0.6299787005],
        ]
    )
    lms_cbrt = np.cbrt(np.maximum(lms, 0.0))
    return lms_cbrt @ np.array(
        [
            [0.2104542553, 1.9779984951, 0.0259040371],
            [0.7936177850, -2.4285922050, 0.7827717662],
            [-0.0040720468, 0.4505937099, -0.8086757660],
        ]
    )


def oklab_to_linear_rgb(lab: np.ndarray) -> np.ndarray:
    l, a, b = lab[..., 0], lab[..., 1], lab[..., 2]
    l_ = l + 0.3963377774 * a + 0.2158037573 * b
    m_ = l - 0.1055613458 * a - 0.0638541728 * b
    s_ = l - 0.0894841775 * a - 1.2914855480 * b
    lms = np.stack([l_**3, m_**3, s_**3], axis=-1)
    return lms @ np.array(
        [
            [4.0767416621, -1.2684380046, -0.0041960863],
            [-3.3077115913, 2.6097574011, -0.7034186147],
            [0.2309699292, -0.3413193965, 1.7076147010],
        ]
    )


def rgb_to_oklab(rgb: np.ndarray) -> np.ndarray:
    return linear_rgb_to_oklab(srgb_to_linear(rgb))


def oklab_to_rgb8(lab: np.ndarray) -> tuple[int, int, int]:
    rgb = linear_to_srgb(oklab_to_linear_rgb(lab))
    rgb8 = np.clip(np.round(rgb * 255), 0, 255).astype(np.uint8)
    return int(rgb8[0]), int(rgb8[1]), int(rgb8[2])


def lab_to_lch(lab: np.ndarray) -> tuple[float, float, float]:
    lightness = float(lab[0])
    chroma = float(math.hypot(lab[1], lab[2]))
    hue = math.degrees(math.atan2(float(lab[2]), float(lab[1]))) % 360
    return lightness, chroma, hue


def load_image(path: Path) -> Image.Image:
    with Image.open(path) as image:
        return ImageOps.exif_transpose(image).convert("RGB")


def detect_palette_divider(image: Image.Image) -> int | None:
    arr = np.asarray(image.convert("RGB"), dtype=np.float32) / 255.0
    height = arr.shape[0]
    start = int(height * 0.48)
    end = int(height * 0.86)
    rows = arr[start:end]
    row_mean = rows.mean(axis=(1, 2))
    row_std = rows.std(axis=(1, 2))
    white_like = (row_mean > 0.88) & (row_std < 0.08)

    best_start = None
    best_length = 0
    current_start = None
    current_length = 0
    for index, value in enumerate(white_like):
        if value:
            if current_start is None:
                current_start = index
            current_length += 1
        else:
            if current_length > best_length:
                best_start = current_start
                best_length = current_length
            current_start = None
            current_length = 0
    if current_length > best_length:
        best_start = current_start
        best_length = current_length

    if best_start is None or best_length < 4:
        return None
    return start + best_start


def crop_source_region(image: Image.Image, mode: str) -> Image.Image:
    if mode == "none":
        return image
    if mode == "auto-palette":
        divider_y = detect_palette_divider(image)
        if divider_y is None:
            return trim_white_border(image)
        cropped = image.crop((0, 0, image.width, max(1, divider_y)))
        return trim_white_border(cropped)
    raise ValueError(f"Unknown crop mode: {mode}")


def trim_white_border(image: Image.Image, threshold: int = 238) -> Image.Image:
    arr = np.asarray(image.convert("RGB"), dtype=np.uint8)
    non_white = np.any(arr < threshold, axis=2)
    ys, xs = np.where(non_white)
    if len(xs) == 0 or len(ys) == 0:
        return image
    left = max(0, int(xs.min()))
    right = min(image.width, int(xs.max()) + 1)
    top = max(0, int(ys.min()))
    bottom = min(image.height, int(ys.max()) + 1)
    if right <= left or bottom <= top:
        return image
    return image.crop((left, top, right, bottom))


def resize_for_analysis(image: Image.Image, max_edge: int) -> Image.Image:
    width, height = image.size
    scale = min(1.0, max_edge / max(width, height))
    if scale >= 1.0:
        return image.copy()
    size = (max(1, round(width * scale)), max(1, round(height * scale)))
    return image.resize(size, Image.Resampling.LANCZOS)


def normalize01(values: np.ndarray) -> np.ndarray:
    values = values.astype(np.float32)
    min_value = float(values.min())
    max_value = float(values.max())
    if max_value - min_value < 1e-6:
        return np.zeros_like(values, dtype=np.float32)
    return (values - min_value) / (max_value - min_value)


def compute_weight_map(rgb: np.ndarray, saliency_strength: float, subject_boost: float) -> np.ndarray:
    gray = cv2.cvtColor((rgb * 255).astype(np.uint8), cv2.COLOR_RGB2GRAY).astype(np.float32) / 255.0
    hsv = cv2.cvtColor((rgb * 255).astype(np.uint8), cv2.COLOR_RGB2HSV).astype(np.float32)
    saturation = hsv[..., 1] / 255.0

    blur = cv2.GaussianBlur(gray, (0, 0), 2.5)
    local_contrast = normalize01(np.abs(gray - blur))
    edges = normalize01(cv2.Laplacian(gray, cv2.CV_32F, ksize=3))

    height, width = gray.shape
    yy, xx = np.mgrid[0:height, 0:width]
    cx = (width - 1) / 2.0
    cy = (height - 1) / 2.0
    radius = np.sqrt(((xx - cx) / max(width, 1)) ** 2 + ((yy - cy) / max(height, 1)) ** 2)
    center = np.exp(-radius * 4.0)

    exposure = 1.0 - np.clip(np.abs(gray - 0.5) * 1.7, 0.0, 0.85)
    shadow_floor = np.where(gray < 0.08, 0.65, 1.0)
    highlight_floor = np.where(gray > 0.95, 0.55, 1.0)
    exposure_quality = exposure * shadow_floor * highlight_floor

    saturation_weight = 0.75 + 0.85 * np.sqrt(np.clip(saturation, 0.0, 1.0))
    contrast_weight = 0.85 + 0.70 * local_contrast
    detail_weight = 0.90 + 0.45 * edges
    subject_weight = 1.0 + subject_boost * center
    saliency = 0.55 * center + 0.25 * local_contrast + 0.20 * edges
    saliency_weight = 1.0 + saliency_strength * saliency

    weights = saturation_weight * contrast_weight * detail_weight * subject_weight * saliency_weight * exposure_quality
    weights = np.nan_to_num(weights, nan=0.0, posinf=0.0, neginf=0.0)
    return np.clip(weights, 0.02, None).astype(np.float32)


def sample_pixels(lab: np.ndarray, weights: np.ndarray, max_samples: int, seed: int) -> tuple[np.ndarray, np.ndarray]:
    flat_lab = lab.reshape(-1, 3)
    flat_weights = weights.reshape(-1)
    count = flat_lab.shape[0]
    if count <= max_samples:
        return flat_lab, flat_weights

    rng = np.random.default_rng(seed)
    probabilities = flat_weights / flat_weights.sum()
    indices = rng.choice(count, size=max_samples, replace=False, p=probabilities)
    return flat_lab[indices], flat_weights[indices]


def cluster_colors(
    lab_pixels: np.ndarray,
    sample_weights: np.ndarray,
    cluster_count: int,
    seed: int,
) -> list[PaletteColor]:
    cluster_count = max(2, min(cluster_count, len(lab_pixels)))
    kmeans = MiniBatchKMeans(
        n_clusters=cluster_count,
        random_state=seed,
        batch_size=4096,
        n_init=5,
        reassignment_ratio=0.005,
    )
    labels = kmeans.fit_predict(lab_pixels, sample_weight=sample_weights)
    centers = kmeans.cluster_centers_

    candidates: list[PaletteColor] = []
    total_weight = float(sample_weights.sum())
    for index, center in enumerate(centers):
        mask = labels == index
        if not np.any(mask):
            continue
        weight = float(sample_weights[mask].sum())
        lightness, chroma, hue = lab_to_lch(center)
        area_score = weight / max(total_weight, 1e-6)
        mood_score = min(chroma * 5.5, 1.2)
        shadow_bonus = 0.22 if lightness < 0.24 and area_score > 0.015 else 0.0
        highlight_bonus = 0.16 if lightness > 0.78 and area_score > 0.01 else 0.0
        score = area_score * 4.5 + mood_score + shadow_bonus + highlight_bonus
        candidates.append(
            PaletteColor(
                lab=center,
                rgb=oklab_to_rgb8(center),
                score=float(score),
                weight=weight,
                lightness=lightness,
                chroma=chroma,
                hue=hue,
            )
        )
    return candidates


def build_palette_color(lab: np.ndarray, score: float, weight: float) -> PaletteColor:
    lightness, chroma, hue = lab_to_lch(lab)
    return PaletteColor(
        lab=lab,
        rgb=oklab_to_rgb8(lab),
        score=float(score),
        weight=float(weight),
        lightness=lightness,
        chroma=chroma,
        hue=hue,
    )


def local_region_candidates(
    lab: np.ndarray,
    weights: np.ndarray,
    strength: float,
) -> list[PaletteColor]:
    height, width, _ = lab.shape
    chroma = np.sqrt(lab[..., 1] ** 2 + lab[..., 2] ** 2)
    lightness = lab[..., 0]
    importance = weights * (0.65 + chroma * 8.0)
    protected: list[PaletteColor] = []

    # Multiple grids with half-cell offsets approximate a k-fold local scan.
    # This avoids baking in one fixed position while still protecting small regions.
    grid_specs = [(3, 3, 0.0, 0.0), (4, 4, 0.0, 0.0), (4, 4, 0.5, 0.5), (5, 5, 0.0, 0.5), (5, 5, 0.5, 0.0)]
    for rows, cols, y_offset, x_offset in grid_specs:
        tile_h = height / rows
        tile_w = width / cols
        y_start = -tile_h * y_offset
        x_start = -tile_w * x_offset
        for row in range(rows + 1):
            top = max(0, int(round(y_start + row * tile_h)))
            bottom = min(height, int(round(y_start + (row + 1) * tile_h)))
            if bottom - top < 8:
                continue
            for col in range(cols + 1):
                left = max(0, int(round(x_start + col * tile_w)))
                right = min(width, int(round(x_start + (col + 1) * tile_w)))
                if right - left < 8:
                    continue

                tile_lab = lab[top:bottom, left:right].reshape(-1, 3)
                tile_importance = importance[top:bottom, left:right].reshape(-1)
                tile_chroma = chroma[top:bottom, left:right].reshape(-1)
                tile_lightness = lightness[top:bottom, left:right].reshape(-1)

                keep = (tile_chroma > 0.028) & (tile_lightness > 0.08) & (tile_lightness < 0.94)
                if int(keep.sum()) < 12:
                    continue

                kept_importance = tile_importance[keep]
                threshold = np.quantile(kept_importance, 0.82)
                strong = keep.copy()
                strong[keep] = kept_importance >= threshold
                if int(strong.sum()) < 8:
                    continue

                selected_lab = tile_lab[strong]
                selected_weight = tile_importance[strong]
                total_weight = float(selected_weight.sum())
                if total_weight <= 1e-6:
                    continue

                center = np.average(selected_lab, axis=0, weights=selected_weight)
                local_lightness, local_chroma, _ = lab_to_lch(center)
                if local_chroma < 0.025:
                    continue

                area_ratio = strong.sum() / max(tile_lab.shape[0], 1)
                detail_bonus = min(float(selected_weight.mean()) * 0.22, 0.5)
                rarity_bonus = 1.0 - min(area_ratio * 3.5, 0.8)
                score = strength * (1.0 + local_chroma * 8.0 + detail_bonus + rarity_bonus)
                if local_lightness < 0.22:
                    score += strength * 0.25
                protected.append(build_palette_color(center, score=score, weight=total_weight * strength))

    return merge_similar_colors(protected, threshold=0.032)


def perceptual_distance(a: PaletteColor, b: PaletteColor) -> float:
    return float(np.linalg.norm(a.lab - b.lab))


def merge_similar_colors(candidates: list[PaletteColor], threshold: float) -> list[PaletteColor]:
    merged: list[PaletteColor] = []
    for color in sorted(candidates, key=lambda item: item.score, reverse=True):
        match_index = None
        for index, existing in enumerate(merged):
            if perceptual_distance(color, existing) < threshold:
                match_index = index
                break
        if match_index is None:
            merged.append(color)
            continue

        existing = merged[match_index]
        total = existing.weight + color.weight
        lab = (existing.lab * existing.weight + color.lab * color.weight) / max(total, 1e-6)
        lightness, chroma, hue = lab_to_lch(lab)
        merged[match_index] = PaletteColor(
            lab=lab,
            rgb=oklab_to_rgb8(lab),
            score=max(existing.score, color.score) + min(existing.score, color.score) * 0.25,
            weight=total,
            lightness=lightness,
            chroma=chroma,
            hue=hue,
        )
    return merged


def select_palette(candidates: list[PaletteColor], count: int, min_distance: float) -> list[PaletteColor]:
    if not candidates:
        return []

    selected: list[PaletteColor] = []
    sorted_by_score = sorted(candidates, key=lambda item: item.score, reverse=True)
    sorted_by_dark = sorted(candidates, key=lambda item: (item.lightness, -item.score))
    sorted_by_light = sorted(candidates, key=lambda item: (-item.lightness, -item.score))
    sorted_by_chroma = sorted(candidates, key=lambda item: (-item.chroma, -item.score))

    for source in (sorted_by_dark[:2], sorted_by_light[:2], sorted_by_chroma[:3], sorted_by_score):
        for color in source:
            if len(selected) >= count:
                break
            if color in selected:
                continue
            relaxed_distance = min_distance * (0.65 if len(selected) > count - 3 else 1.0)
            if all(perceptual_distance(color, other) >= relaxed_distance for other in selected):
                selected.append(color)
        if len(selected) >= count:
            break

    return selected[:count]


def circular_hue_distance(a: float, b: float) -> float:
    diff = abs(a - b) % 360
    return min(diff, 360 - diff)


def hue_band_order(colors: list[PaletteColor]) -> list[PaletteColor]:
    if len(colors) <= 2:
        return sorted(colors, key=lambda item: item.lightness)

    by_hue = sorted(colors, key=lambda item: item.hue)
    gaps: list[tuple[float, int]] = []
    for index, color in enumerate(by_hue):
        next_color = by_hue[(index + 1) % len(by_hue)]
        gap = (next_color.hue - color.hue) % 360
        gaps.append((gap, index))

    _, gap_index = max(gaps, key=lambda item: item[0])
    ascending = by_hue[gap_index + 1 :] + by_hue[: gap_index + 1]
    sequence = list(reversed(ascending))

    bands: list[list[PaletteColor]] = []
    for color in sequence:
        if not bands:
            bands.append([color])
            continue
        previous = bands[-1][-1]
        if circular_hue_distance(previous.hue, color.hue) <= 18:
            bands[-1].append(color)
        else:
            bands.append([color])

    ordered: list[PaletteColor] = []
    last_band_index = max(len(bands) - 1, 1)
    for index, band in enumerate(bands):
        if index / last_band_index < 0.55:
            ordered.extend(sorted(band, key=lambda item: item.lightness))
        else:
            ordered.extend(sorted(band, key=lambda item: item.lightness, reverse=True))
    return ordered


def order_palette(colors: list[PaletteColor], mode: str) -> list[PaletteColor]:
    if mode == "luminance":
        return sorted(colors, key=lambda item: (item.lightness, item.hue))
    if mode == "hue":
        neutral_dark = [color for color in colors if color.chroma < 0.04 and color.lightness < 0.38]
        neutral_light = [color for color in colors if color.chroma < 0.04 and color not in neutral_dark]
        chromatic = [color for color in colors if color not in neutral_dark and color not in neutral_light]
        return (
            sorted(neutral_dark, key=lambda item: item.lightness)
            + hue_band_order(chromatic)
            + sorted(neutral_light, key=lambda item: item.lightness)
        )
    if mode != "cinematic":
        raise ValueError(f"Unknown order mode: {mode}")

    neutral_dark = [color for color in colors if color.chroma < 0.035 and color.lightness < 0.34]
    tonal_colors = [color for color in colors if color not in neutral_dark]
    return sorted(neutral_dark, key=lambda item: item.lightness) + hue_band_order(tonal_colors)


def extract_palette(
    image: Image.Image,
    palette_count: int,
    max_edge: int,
    clusters: int,
    max_samples: int,
    saliency_strength: float,
    subject_boost: float,
    local_protection: float,
    seed: int,
    order: str,
) -> list[PaletteColor]:
    analysis = resize_for_analysis(image, max_edge)
    rgb = np.asarray(analysis, dtype=np.float32) / 255.0
    weights = compute_weight_map(rgb, saliency_strength=saliency_strength, subject_boost=subject_boost)
    lab = rgb_to_oklab(rgb.reshape(-1, 3)).reshape(rgb.shape)
    lab_pixels, sample_weights = sample_pixels(lab, weights, max_samples=max_samples, seed=seed)
    candidates = cluster_colors(lab_pixels, sample_weights, cluster_count=clusters, seed=seed)
    if local_protection > 0:
        candidates.extend(local_region_candidates(lab, weights, strength=local_protection))
    candidates = merge_similar_colors(candidates, threshold=0.035)
    selected = select_palette(candidates, count=palette_count, min_distance=0.045)

    if len(selected) < palette_count:
        for color in sorted(candidates, key=lambda item: item.score, reverse=True):
            if color not in selected:
                selected.append(color)
            if len(selected) >= palette_count:
                break

    return order_palette(selected[:palette_count], mode=order)


def cover_resize(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    target_width, target_height = size
    source_width, source_height = image.size
    scale = max(target_width / source_width, target_height / source_height)
    resized = image.resize(
        (math.ceil(source_width * scale), math.ceil(source_height * scale)),
        Image.Resampling.LANCZOS,
    )
    left = (resized.width - target_width) // 2
    top = (resized.height - target_height) // 2
    return resized.crop((left, top, left + target_width, top + target_height))


def render_palette_image(
    source: Image.Image,
    colors: list[PaletteColor],
    output: Path,
    canvas_width: int,
    image_height: int,
    swatch_height: int,
    padding: int,
    gutter: int,
) -> None:
    canvas_height = padding * 2 + image_height + gutter + swatch_height
    canvas = Image.new("RGB", (canvas_width, canvas_height), "white")

    content_width = canvas_width - padding * 2
    fitted = cover_resize(source, (content_width, image_height))
    canvas.paste(fitted, (padding, padding))

    swatch_top = padding + image_height + gutter
    swatch_count = len(colors)
    available_width = content_width - gutter * (swatch_count - 1)
    base_width = available_width // swatch_count
    remainder = available_width - base_width * swatch_count

    x = padding
    for index, color in enumerate(colors):
        width = base_width + (1 if index < remainder else 0)
        swatch = Image.new("RGB", (width, swatch_height), color.rgb)
        canvas.paste(swatch, (x, swatch_top))
        x += width + gutter

    output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output)


def write_palette_json(colors: list[PaletteColor], output: Path) -> None:
    payload = [
        {
            "hex": "#{:02X}{:02X}{:02X}".format(*color.rgb),
            "rgb": color.rgb,
            "oklab": [round(float(value), 6) for value in color.lab],
            "lightness": round(color.lightness, 6),
            "chroma": round(color.chroma, 6),
            "hue": round(color.hue, 3),
            "score": round(color.score, 6),
        }
        for color in colors
    ]
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def iter_inputs(path: Path) -> Iterable[Path]:
    if path.is_file():
        yield path
        return
    for child in sorted(path.rglob("*")):
        if child.suffix.lower() in IMAGE_EXTENSIONS:
            yield child


def build_output_path(input_path: Path, output_dir: Path | None, suffix: str) -> Path:
    if output_dir is None:
        return input_path.with_name(f"{input_path.stem}{suffix}.png")
    return output_dir / f"{input_path.stem}{suffix}.png"


def process_image(input_path: Path, args: argparse.Namespace) -> Path:
    image = load_image(input_path)
    source = crop_source_region(image, args.crop_source)
    colors = extract_palette(
        source,
        palette_count=args.palette_count,
        max_edge=args.analysis_max_edge,
        clusters=args.clusters,
        max_samples=args.max_samples,
        saliency_strength=args.saliency_strength,
        subject_boost=args.subject_boost,
        local_protection=args.local_protection,
        seed=args.seed,
        order=args.order,
    )
    output = build_output_path(input_path, args.output_dir, args.output_suffix)
    render_palette_image(
        source,
        colors,
        output,
        canvas_width=args.canvas_width,
        image_height=args.image_height,
        swatch_height=args.swatch_height,
        padding=args.padding,
        gutter=args.gutter,
    )
    if args.json:
        write_palette_json(colors, output.with_suffix(".json"))
    return output


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate perceptual color palette images from photos.")
    parser.add_argument("input", type=Path, help="Image file or directory to process.")
    parser.add_argument("--output-dir", type=Path, default=Path("output"), help="Directory for generated images.")
    parser.add_argument("--output-suffix", default="_palette", help="Suffix appended to generated image names.")
    parser.add_argument("--palette-count", type=int, default=10, help="Number of color swatches.")
    parser.add_argument("--clusters", type=int, default=22, help="Initial weighted KMeans cluster count.")
    parser.add_argument("--analysis-max-edge", type=int, default=768, help="Max edge size used for analysis.")
    parser.add_argument("--max-samples", type=int, default=80000, help="Maximum sampled pixels for clustering.")
    parser.add_argument("--saliency-strength", type=float, default=0.85, help="Strength of saliency weighting.")
    parser.add_argument("--subject-boost", type=float, default=0.45, help="Center subject weighting strength.")
    parser.add_argument("--local-protection", type=float, default=0.0, help="Local color protection strength.")
    parser.add_argument("--seed", type=int, default=7, help="Random seed for sampling and clustering.")
    parser.add_argument("--order", choices=["cinematic", "luminance", "hue"], default="cinematic")
    parser.add_argument("--crop-source", choices=["none", "auto-palette"], default="none")
    parser.add_argument("--canvas-width", type=int, default=1179)
    parser.add_argument("--image-height", type=int, default=650)
    parser.add_argument("--swatch-height", type=int, default=214)
    parser.add_argument("--padding", type=int, default=8)
    parser.add_argument("--gutter", type=int, default=8)
    parser.add_argument("--json", action="store_true", help="Also write palette metadata JSON.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    inputs = list(iter_inputs(args.input))
    if not inputs:
        raise SystemExit(f"No supported image files found: {args.input}")

    for input_path in inputs:
        output = process_image(input_path, args)
        print(f"{input_path} -> {output}")


if __name__ == "__main__":
    main()
