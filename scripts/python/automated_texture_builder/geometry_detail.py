from __future__ import annotations


def geometry_detail_plan(maps: dict, mode: str) -> tuple[str | None, str | None]:
    """Return (bump channel, true-displacement channel) by map semantics."""
    scalar = "height" if "height" in maps else (
        "displacement" if "displacement" in maps else None
    )
    preferred_displacement = "vector_displacement" if "vector_displacement" in maps else (
        "displacement" if "displacement" in maps else (
            "height" if "height" in maps else None
        )
    )
    if mode == "off":
        return None, None
    if mode == "bump":
        return scalar, None
    if mode == "displacement":
        return None, preferred_displacement
    # Painter's displacement source defaults to Height. Automatic therefore
    # selects one best true-displacement signal and avoids simultaneously
    # applying Height as bump, which would duplicate the same authored detail.
    return None, preferred_displacement
