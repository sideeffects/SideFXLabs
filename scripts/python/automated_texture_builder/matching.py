from __future__ import annotations

import re


IGNORED_LEADING_NAME_TOKENS = {
    "bake", "lp", "shop", "material", "materialpath", "shopmaterialpath",
}


def normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.casefold())


def normalize_usd_root(value: str) -> str:
    """Canonicalize any-depth USD hierarchy root for assignment searches."""
    segments = [segment for segment in value.strip().split("/") if segment]
    return "/" + "/".join(segments) if segments else "/"


def meaningful_name_tokens(value: str) -> list[str]:
    """Remove known export/import prefixes while preserving numeric identity."""
    tokens = [
        normalize(token)
        for token in re.split(r"[_\-.\s]+", value)
        if normalize(token)
    ]
    while tokens and tokens[0] in IGNORED_LEADING_NAME_TOKENS:
        tokens.pop(0)
    return tokens


def meaningful_path_tokens(path: str) -> list[str]:
    """Collect identity tokens from every USD path segment.

    Imported meshes often have generic leaf names such as ``mesh_0`` while
    their asset identity is carried by an ancestor Xform. Material matching
    must therefore consider the complete prim path, not only its leaf.
    """
    tokens = []
    for segment in path.strip("/").split("/"):
        tokens.extend(meaningful_name_tokens(segment))
    return tokens


def _longest_common_token_run(left: list[str], right: list[str]) -> tuple[int, int]:
    """Return matched character count and token count for a contiguous run."""
    best = (0, 0)
    for left_index in range(len(left)):
        for right_index in range(len(right)):
            characters = 0
            count = 0
            while (
                left_index + count < len(left)
                and right_index + count < len(right)
                and left[left_index + count] == right[right_index + count]
            ):
                characters += len(left[left_index + count])
                count += 1
            best = max(best, (characters, count))
    return best


def match_materials_to_paths(
    material_paths: dict[str, str], candidates: list[str | tuple[str, bool]],
    *, allow_single_fallback: bool = False,
) -> dict[str, str]:
    """Find unique exact or longest meaningful partial USD-name matches."""
    matches: dict[str, str] = {}
    for set_name in material_paths:
        set_raw = normalize(set_name)
        set_tokens = meaningful_name_tokens(set_name)
        set_key = "".join(set_tokens)
        ranked: list[tuple[tuple[int, int, int, int], str]] = []
        for candidate in candidates:
            if isinstance(candidate, tuple):
                path, is_subset = candidate
            else:
                path = candidate
                is_subset = path.rsplit("/", 1)[-1].casefold().startswith("shop_materialpath")
            prim_name = path.rsplit("/", 1)[-1]
            prim_raw = normalize(prim_name)
            leaf_tokens = meaningful_name_tokens(prim_name)
            leaf_key = "".join(leaf_tokens)
            path_tokens = meaningful_path_tokens(path)
            if prim_raw == set_raw or (leaf_key and leaf_key == set_key):
                # An exact semantic match is equally strong with or without
                # exporter prefixes. Prefer a GeomSubset when both the parent
                # Mesh and its material partition carry the same name.
                score = (5, len(leaf_key or prim_raw), len(leaf_tokens), int(is_subset))
            else:
                leaf_characters, leaf_token_count = _longest_common_token_run(
                    set_tokens, leaf_tokens,
                )
                path_characters, path_token_count = _longest_common_token_run(
                    set_tokens, path_tokens,
                )
                if leaf_token_count:
                    score = (
                        3, leaf_characters, leaf_token_count, int(is_subset),
                    )
                elif path_token_count >= 2:
                    # A single ancestor token such as "asset" is too generic;
                    # require a multi-token identity when matching ancestors.
                    score = (
                        3, path_characters, path_token_count, int(is_subset),
                    )
                else:
                    shorter = min((set_key, leaf_key), key=len) if set_key and leaf_key else ""
                    # Safe fallback for names such as Helmet and HelmetMesh.
                    # Do not partially match numbered names (Extract1/Extract12).
                    if (
                        len(shorter) >= 6
                        and not any(character.isdigit() for character in shorter)
                        and (set_key in leaf_key or leaf_key in set_key)
                    ):
                        score = (2, len(shorter), 1, int(is_subset))
                    else:
                        continue
            ranked.append((score, path))
        if ranked:
            best_score = max(score for score, _ in ranked)
            best_paths = [path for score, path in ranked if score == best_score]
            if len(best_paths) == 1:
                matches[set_name] = best_paths[0]
    if allow_single_fallback and len(material_paths) == 1 and not matches:
        normalized_candidates = []
        for candidate in candidates:
            if isinstance(candidate, tuple):
                normalized_candidates.append(candidate)
            else:
                normalized_candidates.append((
                    candidate,
                    candidate.rsplit("/", 1)[-1].casefold().startswith("shop_materialpath"),
                ))
        # A narrowed geometry root containing one Mesh and one child
        # GeomSubset is one logical assignment target. Prefer the subset.
        fallback = None
        if len(normalized_candidates) == 1:
            fallback = normalized_candidates[0][0]
        elif len(normalized_candidates) == 2:
            meshes = [path for path, is_subset in normalized_candidates if not is_subset]
            subsets = [path for path, is_subset in normalized_candidates if is_subset]
            if (
                len(meshes) == 1
                and len(subsets) == 1
                and subsets[0].startswith(meshes[0].rstrip("/") + "/")
            ):
                fallback = subsets[0]
        if fallback:
            matches[next(iter(material_paths))] = fallback
    return matches
