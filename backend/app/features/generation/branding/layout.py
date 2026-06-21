"""Slot geometry and collision resolution for branding elements."""

TOP_LEFT = "top-left"
TOP_RIGHT = "top-right"
CORNERS = (TOP_LEFT, TOP_RIGHT)


def _opposite(slot: str) -> str:
    return TOP_RIGHT if slot == TOP_LEFT else TOP_LEFT


def resolve_slots(
    logo_position: str, contact_position: str, has_logo: bool
) -> tuple[str, str]:
    logo_slot = logo_position if logo_position in CORNERS else TOP_LEFT
    contact_slot = contact_position if contact_position in CORNERS else TOP_RIGHT
    if has_logo and contact_slot == logo_slot:
        contact_slot = _opposite(logo_slot)
    return logo_slot, contact_slot


def corner_origin(
    slot: str, box_w: int, box_h: int, image_w: int, image_h: int, margin: int
) -> tuple[int, int]:
    y = margin
    if slot == TOP_RIGHT:
        x = image_w - margin - box_w
    else:
        x = margin
    return x, y
