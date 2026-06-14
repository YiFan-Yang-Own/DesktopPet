"""Pet skin metadata shared by the pet window and settings UI."""

from __future__ import annotations


DEFAULT_PET_SKIN = "classic"
PET_ASSET_EXTENSIONS = ("gif", "png", "jpg", "jpeg")
PET_STATES = ("happy", "sad", "walk", "sleep", "eat", "play", "rest")

PET_SKINS = {
    "classic": "经典三花",
    "ginger": "暖橘小猫",
    "silver": "银灰小猫",
    "tuxedo": "黑白小猫",
    "latte": "奶茶小猫",
}


def normalize_pet_skin(value: object) -> str:
    """Return a known skin key, falling back to the default skin."""
    skin = str(value or DEFAULT_PET_SKIN)
    if skin in PET_SKINS:
        return skin
    return DEFAULT_PET_SKIN


def pet_skin_label(value: object) -> str:
    """Return the display label for a skin key."""
    return PET_SKINS[normalize_pet_skin(value)]
