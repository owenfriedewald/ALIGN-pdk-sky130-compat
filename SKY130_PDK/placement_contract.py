"""Grid-aligned placement safety helpers for non-routing Sky130 layers."""

from __future__ import annotations


def half_spacing_halo(spacing: int, placement_pitch: int) -> int:
    """Return a per-side halo that guarantees ``spacing`` between cells.

    Two independently placed cells each contribute this halo.  Rounding the
    half-spacing upward to the placement grid keeps generated primitive
    bounding boxes legal for ALIGN's grid-snapped placer.
    """

    if spacing < 0:
        raise ValueError("spacing must be non-negative")
    if placement_pitch <= 0:
        raise ValueError("placement_pitch must be positive")
    half_grid_units = (spacing + 2 * placement_pitch - 1) // (
        2 * placement_pitch
    )
    return half_grid_units * placement_pitch


def expand_bbox(
    bbox: tuple[int, int, int, int], *, halo_x: int, halo_y: int
) -> tuple[int, int, int, int]:
    """Expand a primitive bounding box symmetrically by placement halos."""

    llx, lly, urx, ury = bbox
    if halo_x < 0 or halo_y < 0:
        raise ValueError("placement halos must be non-negative")
    return llx - halo_x, lly - halo_y, urx + halo_x, ury + halo_y
