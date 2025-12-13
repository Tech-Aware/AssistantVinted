from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers internes
# ---------------------------------------------------------------------------


def _safe_clean(value: Optional[Any]) -> str:
    try:
        if value is None:
            return ""
        text = str(value).strip()
        return text
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("_safe_clean: erreur sur %r -> %s", value, exc)
        return ""


def _format_percent(value: Optional[Any]) -> Optional[int]:
    try:
        if value is None or value == "":
            return None
        return int(float(value))
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("_format_percent: conversion impossible pour %r (%s)", value, exc)
        return None


def _format_rise_label(rise_type: Optional[str], rise_cm: Optional[Any]) -> str:
    try:
        if rise_type:
            normalized = rise_type.strip().lower()
        else:
            normalized = ""

        if normalized in {"low", "ultra_low"} or "basse" in normalized:
            return "taille basse"
        if normalized == "high" or "haute" in normalized:
            return "taille haute"
        if normalized == "mid" or "moy" in normalized:
            return "taille moyenne"

        if rise_cm is not None:
            try:
                value = float(rise_cm)
                if value < 23:
                    return "taille basse"
                if value >= 26:
                    return "taille haute"
                return "taille moyenne"
            except (TypeError, ValueError):
                logger.debug("_format_rise_label: rise_cm non exploitable: %r", rise_cm)

        return "taille moyenne"
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("_format_rise_label: erreur inattendue %s", exc)
        return "taille moyenne"


def _build_composition(cotton_percent: Optional[Any], elasthane_percent: Optional[Any]) -> str:
    try:
        cotton_val = _format_percent(cotton_percent)
        elas_val = _format_percent(elasthane_percent)

        fibers: List[str] = []
        if cotton_val is not None:
            fibers.append(f"{cotton_val}% coton")
        if elas_val is not None:
            fibers.append(f"{elas_val}% élasthanne")

        if fibers:
            return "Composition : " + " et ".join(fibers) + "."
        return "Composition non lisible (voir étiquettes en photo)."
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("_build_composition: erreur %s", exc)
        return "Composition non lisible (voir étiquettes en photo)."


def _build_state_sentence(defects: Optional[str]) -> str:
    try:
        clean_defects = _normalize_defects(defects)
        if not clean_defects:
            return "Très bon état."
        return (
            "Très bon état. Légères traces d'usage : "
            f"{clean_defects} (voir photos)."
        )
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("_build_state_sentence: erreur %s", exc)
        return "État non précisé (voir photos)."


def _build_hashtags(
    brand: str,
    model: str,
    fit: str,
    color: str,
    size_fr: str,
    size_us: str,
    length: str,
    gender: str,
    rise_label: str,
    durin_tag: str,
) -> str:
    try:
        tokens: List[str] = []

        def add(token: str) -> None:
            if token and token not in tokens:
                tokens.append(token)

        brand_token = brand.lower().replace("'", "") if brand else "levis"
        add(f"#{brand_token}")
        add("#jeanlevis")
        add("#jeandenim")

        if gender:
            gender_token = gender.lower().replace(" ", "")
            add(f"#levis{gender_token}")

        if model:
            model_low = model.lower().strip()
            model_number = ""
            try:
                import re  # local import pour rester défensif

                match = re.search(r"(\d{3})", model_low)
                if match:
                    model_number = match.group(1)
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning("_build_hashtags: extraction modèle échouée (%s)", exc)

            if model_number:
                add(f"#levis{model_number}")
                add(f"#{model_number}")

            model_tokens: List[str] = []
            drop_markers = {"demi", "curve", "curvy", "cut"}
            for token in model_low.replace("/", " ").split():
                token_clean = token.replace("'", "").replace("-", "")
                if token_clean == model_number or token_clean.isdigit():
                    continue
                if token_clean in drop_markers:
                    logger.debug(
                        "_build_hashtags: token modèle ignoré (marker): %s", token
                    )
                    continue
                if token_clean:
                    model_tokens.append(token_clean)

            try:
                tokens_lower = {t.lower() for t in model_tokens}
                if "super" in tokens_lower and "skinny" in tokens_lower:
                    add("#superskinny")
                    model_tokens = [t for t in model_tokens if t.lower() not in {"super", "skinny"}]
                if "super" in tokens_lower and "slim" in tokens_lower:
                    add("#superslim")
                    model_tokens = [t for t in model_tokens if t.lower() not in {"super", "slim"}]
            except Exception as exc:  # pragma: no cover - defensive
                logger.debug("_build_hashtags: combinaison tokens modèle impossible (%s)", exc)

            for token_clean in model_tokens:
                add(f"#{token_clean}")

        if fit:
            fit_low = fit.lower().strip()
            fit_key = fit_low.replace("é", "e")
            boot_markers = {"bootcut", "boot cut", "boot-cut", "flare", "curve", "curvy"}
            if any(marker in fit_key for marker in boot_markers):
                fit_token = "bootcut"
            elif "skinny" in fit_key or "slim" in fit_key:
                fit_token = "skinny"
            elif "straight" in fit_key or "droit" in fit_key:
                fit_token = "straightdroit"
            else:
                fit_token = fit_key.replace(" ", "").replace("/", "")
            add(f"#{fit_token}jean")

        if color:
            color_clean = color.lower().replace(" ", "")
            add(f"#jean{color_clean}")

        rise_clean = rise_label.lower().replace(" ", "") if rise_label else ""
        if rise_clean:
            add(f"#{rise_clean}")

        if size_fr:
            add(f"#fr{size_fr.lower()}")
        if size_us:
            add(f"#w{size_us.lower().replace('w', '')}")
        if length:
            add(f"#l{length.lower().replace('l', '')}")

        if durin_tag:
            add(durin_tag)

        return " ".join(tokens)
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("_build_hashtags: erreur %s", exc)
        return ""


def _normalize_defects(defects: Optional[str]) -> str:
    try:
        base = _safe_clean(defects)
        if not base:
            return ""

        lowered = base.lower()
        if "voir photos" in lowered:
            cut = lowered.split("voir photos", 1)[0].strip()
        else:
            cut = base.strip()

        cleaned = cut.rstrip(". ,;")
        return cleaned
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("_normalize_defects: erreur %s", exc)
        return ""


def _strip_footer_lines(description: str) -> str:
    try:
        if not description:
            return ""

        filtered_lines: List[str] = []
        for line in description.split("\n"):
            lowered = line.strip().lower()
            if lowered.startswith("marque :"):
                logger.debug("_strip_footer_lines: ligne marque supprimée: %s", line)
                continue
            if lowered.startswith("couleur :"):
                logger.debug("_strip_footer_lines: ligne couleur supprimée: %s", line)
                continue
            if lowered.startswith("sku"):
                logger.debug("_strip_footer_lines: ligne SKU supprimée: %s", line)
                continue
            filtered_lines.append(line)

        cleaned = "\n".join(filtered_lines)
        return cleaned
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("_strip_footer_lines: erreur %s", exc)
        return description


def _build_pull_tommy_composition(
    material: Optional[str], cotton_percent: Optional[Any], wool_percent: Optional[Any]
) -> str:
    try:
        cotton_val = _format_percent(cotton_percent)
        wool_val = _format_percent(wool_percent)

        fibers: List[str] = []
        if cotton_val is not None:
            fibers.append(f"{cotton_val}% coton")
        if wool_val is not None:
            fibers.append(f"{wool_val}% laine")

        if fibers:
            return "Composition : " + " et ".join(fibers) + "."

        clean_material = _safe_clean(material)
        if clean_material:
            return f"Composition (étiquette) : {clean_material}."

        return "Composition non lisible (voir photos)."
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("_build_pull_tommy_composition: erreur %s", exc)
        return "Composition non lisible (voir photos)."


def _normalize_fit_display(raw_fit: Optional[str], model_hint: Optional[str] = None) -> str:
    try:
        if not raw_fit and not model_hint:
            return "coupe non précisée"

        value = (raw_fit or model_hint or "").strip()
        low = value.lower()
        secondary_low = (model_hint or "").strip().lower()

        boot_markers = (
            "boot",
            "flare",
            "évas",
            "evase",
            "curve",
            "curvy",
        )
        if any(marker in low for marker in boot_markers) or any(
            marker in secondary_low for marker in boot_markers
        ):
            return "Bootcut/Évasé"

        if "skinny" in low or "slim" in low:
            return "Skinny"

        if "straight" in low or "droit" in low:
            return "Straight/Droit"

        return value or "coupe non précisée"
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("_normalize_fit_display: erreur %s", exc)
        return "coupe non précisée"


# ---------------------------------------------------------------------------
# Génération de description pour jean Levi's
# ---------------------------------------------------------------------------


def build_jean_levis_description(
    features: Dict[str, Any],
    ai_description: Optional[str] = None,
    ai_defects: Optional[str] = None,
) -> str:
    """
    Génère une description structurée d'un jean Levi's à partir des features
    normalisés. En cas d'erreur, on retombe sur la description IA brute.
    """
    try:
        logger.info("build_jean_levis_description: features reçus = %s", features)

        brand = _safe_clean(features.get("brand")) or "Levi's"
        model = _safe_clean(features.get("model"))
        raw_fit = _safe_clean(features.get("fit"))
        fit = _normalize_fit_display(raw_fit, model_hint=model)
        color = _safe_clean(features.get("color"))
        size_fr = _safe_clean(features.get("size_fr"))
        size_us = _safe_clean(features.get("size_us"))
        length = _safe_clean(features.get("length"))
        gender = _safe_clean(features.get("gender")) or "femme"
        sku = _safe_clean(features.get("sku"))
        rise_label = _format_rise_label(features.get("rise_type"), features.get("rise_cm"))

        title_intro_parts = ["Jean", brand]
        if model:
            title_intro_parts.append(model)
        title_intro = " ".join(title_intro_parts)

        # --- Phrases structurées ------------------------------------------
        intro_sentence = f"{title_intro} pour {gender}."

        size_sentence_parts = []
        if size_us and size_fr:
            size_sentence_parts.append(
                f"Taille {size_us} US (équivalent {size_fr} FR)"
            )
        elif size_fr:
            size_sentence_parts.append(f"Taille {size_fr} FR")
        elif size_us:
            size_sentence_parts.append(f"Taille {size_us} US")
        if fit:
            size_sentence_parts.append(f"coupe {fit}")
        if rise_label:
            size_sentence_parts.append(f"à {rise_label}")
        if size_sentence_parts:
            size_sentence_parts.append(
                "pour une silhouette ajustée et confortable"
            )
        size_sentence = ", ".join(size_sentence_parts).strip()
        size_sentence = f"{size_sentence}." if size_sentence else "Taille non précisée."

        color_has_fade = "lavé" in color.lower() if color else False
        if color:
            nuance = " légèrement délavé" if not color_has_fade else ""
            color_sentence = (
                f"Coloris {color}{nuance}, très polyvalent et facile à assortir."
            )
        else:
            color_sentence = "Coloris non précisé, se référer aux photos pour les nuances."
        composition_sentence = _build_composition(
            features.get("cotton_percent"), features.get("elasthane_percent")
        )
        closure_sentence = "Fermeture zippée + bouton gravé Levi’s."
        state_sentence = _build_state_sentence(ai_defects or features.get("defects"))

        logistics_sentence = "📏 Mesures visibles en photo."
        shipping_sentence = "📦 Envoi rapide et soigné"

        cta_lot_sentence = (
            "💡 Pensez à un lot pour profiter d’une réduction supplémentaire et économiser des frais d’envoi !"
        )
        durin_tag = f"#durin31fr{(size_fr or 'nc').lower()}"
        cta_durin_sentence = (
            f"✨ Retrouvez tous mes articles Levi’s à votre taille ici 👉 {durin_tag}"
        )

        hashtags = _build_hashtags(
            brand=brand,
            model=model,
            fit=fit,
            color=color,
            size_fr=size_fr,
            size_us=size_us,
            length=length,
            gender=gender,
            rise_label=rise_label,
            durin_tag=durin_tag,
        )

        paragraphs = [
            intro_sentence,
            size_sentence,
            color_sentence,
            composition_sentence,
            closure_sentence,
            state_sentence,
            logistics_sentence,
            shipping_sentence,
            cta_durin_sentence,
            cta_lot_sentence,
            hashtags,
        ]

        description = "\n\n".join(part for part in paragraphs if part)
        description = _strip_footer_lines(description)
        logger.debug("build_jean_levis_description: description générée = %s", description)
        return description

    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("build_jean_levis_description: fallback description IA (%s)", exc)
        return _safe_clean(ai_description)


def build_pull_tommy_description(
    features: Dict[str, Any],
    ai_description: Optional[str] = None,
    ai_defects: Optional[str] = None,
) -> str:
    """Construit une description structurée pour un pull Tommy Hilfiger."""
    try:
        logger.info("build_pull_tommy_description: features reçus = %s", features)

        brand = _safe_clean(features.get("brand")) or "Tommy Hilfiger"
        garment_type = _safe_clean(features.get("garment_type")) or "pull"
        gender = _safe_clean(features.get("gender")) or "femme"
        neckline = _safe_clean(features.get("neckline"))
        pattern = _safe_clean(features.get("pattern"))
        material = _safe_clean(features.get("material"))
        cotton_percent = features.get("cotton_percent")
        wool_percent = features.get("wool_percent")
        colors_raw = features.get("main_colors")
        size = _safe_clean(features.get("size"))
        size_source = (_safe_clean(features.get("size_source")) or "").lower()
        measurement_mode = (_safe_clean(features.get("measurement_mode")) or "").lower()
        defects = ai_defects or features.get("defects")

        colors = ""
        try:
            if isinstance(colors_raw, list):
                colors = ", ".join([_safe_clean(c) for c in colors_raw if _safe_clean(c)])
            else:
                colors = _safe_clean(colors_raw)
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("build_pull_tommy_description: couleurs non exploitables (%s)", exc)
            colors = ""

        intro_parts: List[str] = []
        intro_parts.append(f"{garment_type.capitalize()} {brand}")
        if gender:
            intro_parts.append(f"pour {gender}")
        intro_sentence = " ".join(intro_parts).strip() + "."

        if size:
            if size_source == "estimated" or measurement_mode == "mesures":
                size_sentence = (
                    f"Taille estimée {size}. Estimée à la main à partir des mesures à plat."
                )
            else:
                size_sentence = f"Taille indiquée sur étiquette : {size}."
        else:
            size_sentence = "Taille non précisée."

        neckline_sentence = f"Col {neckline}." if neckline else ""
        pattern_sentence = f"Motif : {pattern}." if pattern else ""
        color_sentence = f"Coloris : {colors}." if colors else ""

        composition_sentence = _build_pull_tommy_composition(
            material=material,
            cotton_percent=cotton_percent,
            wool_percent=wool_percent,
        )

        state_sentence = _build_state_sentence(defects)
        logistics_sentence = "Envoi rapide et soigné. Article conforme aux photos."

        tokens_hashtag: List[str] = []
        try:
            def _add_tag(token: str) -> None:
                if token and token not in tokens_hashtag:
                    tokens_hashtag.append(token)

            _add_tag("#tommyhilfiger")
            if garment_type:
                _add_tag(f"#{garment_type.replace(' ', '').lower()}")
            if gender:
                _add_tag(f"#{gender.lower()}")
            if colors:
                for color_token in colors.split(","):
                    clean_color = color_token.strip().lower().replace(" ", "")
                    if clean_color:
                        _add_tag(f"#{clean_color}")
            if size:
                _add_tag(f"#taille{size.lower()}")
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("build_pull_tommy_description: hashtags réduits (%s)", exc)

        paragraphs = [
            intro_sentence,
            size_sentence,
            " ".join(token for token in [neckline_sentence, pattern_sentence, color_sentence] if token).strip(),
            composition_sentence,
            state_sentence,
            logistics_sentence,
        ]

        hashtags = " ".join(tokens_hashtag)
        if hashtags:
            paragraphs.append(hashtags)

        description = "\n".join([p for p in paragraphs if p])
        cleaned = _strip_footer_lines(description)
        logger.debug("build_pull_tommy_description: description générée = %s", cleaned)
        return cleaned
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("build_pull_tommy_description: fallback description IA (%s)", exc)
        return _safe_clean(ai_description)
