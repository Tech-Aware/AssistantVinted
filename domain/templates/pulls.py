# domain/templates/pulls.py

from __future__ import annotations

import logging
from typing import Dict

from .base import AnalysisProfile, AnalysisProfileName, BASE_LISTING_SCHEMA

logger = logging.getLogger(__name__)


def _build_pull_profiles() -> Dict[AnalysisProfileName, AnalysisProfile]:
    """Construit les profils liés aux pulls avec logs et gestion d'erreurs."""

    try:
        profiles: Dict[AnalysisProfileName, AnalysisProfile] = {
            AnalysisProfileName.PULL_TOMMY: AnalysisProfile(
                name=AnalysisProfileName.PULL_TOMMY,
                prompt_suffix=r"""
PROFILE TYPE: PULL TOMMY HILFIGER / TOUS STYLES DE MAILLE

The item is a knit sweater (pull, gilet, cardigan) from Tommy Hilfiger (ou assimilé), couvrant toutes les coupes et styles (preppy, casual, torsadé, jacquard, colorblock, marinière, etc.).

FOCUS ON:

1) BRAND & LOGO:
   - Look for:
     - small flag logo on the chest,
     - internal neck label (Tommy Hilfiger, Tommy Jeans, etc.).
   - If the brand is clearly visible:
     - Set "brand" to exactly that name.
   - If you cannot read the brand clearly:
     - Set "brand" to null (do NOT guess).

2) NECKLINE:
   - Identify:
     - col rond (crew neck),
     - col V (v-neck),
     - col zippé / col montant zippé,
     - col roulé,
     - cardigan / gilet boutonné ou zippé.
   - Set "neckline" accordingly when obvious and mention it in the French description.

3) PATTERN & COLORS (TOUJOURS DANS TITRE + DESCRIPTION):
   - Identify the pattern: uni, rayé, marinière, colorblock, jacquard, torsadé, à motifs géométriques, etc.
   - Describe visible color combinations for rayures/colorblock: "rayures bleu marine et rouge", "colorblock bleu/rouge/blanc", etc.
   - Set "pattern" with a short value: "rayé", "uni", "colorblock", "torsadé", etc.

4) STYLE:
   - Capture the perceived style: preppy, casual, smart casual, college, minimal, etc. only if it fits the visual.

5) MATERIAL / COMPOSITION (LOGIQUE TITRE & DESCRIPTION):
   - Read composition from any label if clearly legible; do NOT invent if unreadable.
   - Rules for the title when composition is lisible:
     - If coton > 60%: mention the percentage in the title (ex: "65% coton").
     - If coton ≤ 60%: mention "coton" sans pourcentage.
     - If the composition includes laine, cachemire, lin ou satin: remplacer la mention de coton par la matière concernée dans le titre (sans pourcentage).
     - If a label says "Pima Coton" or "100% pima coton": the title MUST include "premium".
   - In description:
     - Mention composition exacte lue sur l'étiquette quand visible.
     - If pima coton: mentionner "Premium" et "100% pima coton" explicitement.

6) SEASON:
   - Based on thickness/knit: "hiver", "mi-saison", or similar without over-claiming warmth.

7) CONDITION & DEFECTS:
   - Look carefully for pilling/boulochage, loose threads, snags, stains/discoloration, deformation at cuffs/hem/neckline.
   - "defects": short French summary ("Léger boulochage sur les manches", etc.) or null / "Aucun défaut majeur visible" if clean.

8) TAILLE ET MESURES À PLAT:
   - Respect the UI measurement mode:
     - If the UI says "étiquettes lisibles" (measurement_mode=etiquette): do NOT estimate size from measurements; rely only on labels. Ne pas lister de mesures chiffrées dans la description, même si elles sont visibles sur les photos.
     - If the UI says "analyser les mesures" (measurement_mode=mesures): consider the size label missing and estimate the size (XS, S, M, L, XL, XXL, ...) from flat measurements. Ne pas lister les valeurs de mesures; déduire la taille et ajouter la mention ci-dessous.
   - In the description, immediately after the size mention: add "Taille estimée à la main à partir des mesures à plat (voir photos)." when the size is deduced.

9) ÉTIQUETTES MANQUANTES:
   - If size label missing only: mention "Etiquette de taille coupée pour plus de confort" in the description.
   - If composition label missing only: mention "Etiquette de composition coupée pour plus de confort".
   - If both missing: mention "Etiquette taille et composition coupées pour plus de confort".

10) TITLE & DESCRIPTION (FRENCH):
   - title (format cible):
     - Inclure systématiquement: marque si lisible + type (pull/gilet/cardigan) + genre (femme/homme/unisexe) + taille (étiquette ou estimée) + motif/pattern + matière principale selon les règles ci-dessus + type de col si clair + suffixe SKU (ex: "- PTF118").
     - Exemples: "Pull Tommy Hilfiger femme taille M 100% coton rouge torsadé col V - PTF118", "Gilet Tommy Hilfiger homme taille L laine bleu rayé col châle - PTF42".
   - description (pas de markdown, pas de valeurs chiffrées de mesures):
     - Utilise la mise en forme inspirée des jeans Levi's avec des paragraphes courts séparés par des lignes vides pour l'aération. Suis l'ordre suivant et insère une ligne vide entre chaque bloc ; ajoute aussi une ligne vide juste avant les hashtags :
       1) accroche : "Pull/Gilet Tommy Hilfiger pour <Genre> taille <Taille>." (ajoute la mention d'estimation si mode mesures),
       2) motif + couleurs + type de col (ex: "Maille torsadée rouge avec col V."),
       3) composition lisible + mention Premium/pima coton si applicable (ex: "Composition : 100% coton.", "Composition : mélange avec laine.", "Premium 100% pima coton."),
       4) saison d'usage (ex: "Idéal mi-saison" ou "Pour l'hiver"),
       5) état/défauts (ex: "Très bon état" ou "Léger boulochage sur manches"),
       6) mention étiquettes coupées si applicable ("Etiquette de taille coupée pour plus de confort", etc.),
       7) phrase mesures en photo sans chiffres : "📏 Mesures détaillées visibles en photo pour plus de précisions.",
       8) phrase livraison : "📦 Envoi rapide et soigné",
       9) call-to-action vers la collection (ex: "✨ Retrouvez tous mes pulls Tommy femme ici 👉 #durin31tfXL"),
       10) conseil lot/réduction (ex: "💡 Pensez à faire un lot..."),
       11) hashtags de recherche en fin de texte après une ligne vide, sans ligne SKU.
     - Interdiction formelle d'ajouter une ligne "SKU" ou un numéro interne dans la description (les SKU ne doivent apparaître que dans le suffixe du titre). Ne jamais insérer de valeurs de mesures chiffrées dans la description, même si elles sont visibles sur les photos. Les lignes vides servent uniquement à séparer clairement les blocs et à aérer la lecture.

JSON SCHEMA:
- Use the SAME JSON keys as defined in the main prompt contract:
  "title", "description", "brand", "style", "pattern", "neckline", "season", "defects".
- Do NOT add extra keys, and do NOT change key names.
""",
                json_schema=BASE_LISTING_SCHEMA,
            ),
        }

        logger.debug(
            "Profil PULL_TOMMY chargé avec schéma %s",
            list(BASE_LISTING_SCHEMA["properties"].keys()),
        )
        return profiles
    except Exception:
        logger.exception("Erreur lors de la construction des profils PULL_TOMMY")
        raise


PULLS_PROFILES: Dict[AnalysisProfileName, AnalysisProfile] = _build_pull_profiles()
