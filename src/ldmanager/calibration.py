"""Real screenshot/template calibration helpers used by the Windows GUI.

They operate on captured PNG files and produce normal PNG template assets;
there is no mock image source or dry-run representation in this module.
"""

from __future__ import annotations

from pathlib import Path


TEMPLATE_SLOTS = (
    "mission_screen", "region_tab", "slot_1", "slot_2", "slot_3", "slot_4", "slot_5",
    "selected_slot", "refresh_button", "refresh_popup", "refresh_confirm", "mission_detail",
    "all_monsters", "quantity_200", "accept_confirm", "in_progress", "complete_state",
    "complete_button", "claim_reward", "reward_result", "close", "mission_list",
)


def crop_template(source_png: Path, output_png: Path, x: int, y: int, width: int, height: int) -> Path:
    """Crop a real PNG into a template asset, validating every boundary."""
    if min(x, y) < 0 or width <= 0 or height <= 0:
        raise ValueError("Crop x/y must be non-negative and width/height positive.")
    try:
        import cv2  # type: ignore
    except ImportError as exc:
        raise RuntimeError("OpenCV is required; run: pip install -e '.[recognition]'") from exc
    image = cv2.imread(str(source_png), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f"Cannot read PNG: {source_png}")
    image_height, image_width = image.shape[:2]
    if x + width > image_width or y + height > image_height:
        raise ValueError(f"Crop exceeds image bounds {image_width}x{image_height}.")
    output_png.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(output_png), image[y:y + height, x:x + width]):
        raise RuntimeError(f"Cannot save template: {output_png}")
    return output_png
