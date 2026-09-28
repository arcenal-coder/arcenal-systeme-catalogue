#!/usr/bin/env python3
"""Promeut un manifeste ARCenal vers le canal suivant, sans modifier de paquet."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

SCHEMA = "arcenal-release/v1"
PROMOTIONS = {"development": "preview", "preview": "stable"}


class ErreurPromotion(ValueError):
    """Signale une demande de promotion qui ne respecte pas le flux ARCenal."""


def charger(chemin: Path) -> dict[str, object]:
    """Lit un manifeste de diffusion et vérifie sa structure minimale."""
    with chemin.open(encoding="utf-8") as fichier:
        contenu: object = json.load(fichier)
    if not isinstance(contenu, dict) or contenu.get("schema") != SCHEMA:
        raise ErreurPromotion("Le manifeste de diffusion est invalide.")
    if not isinstance(contenu.get("channel"), str) or not isinstance(contenu.get("applications"), dict):
        raise ErreurPromotion("Le manifeste doit déclarer son canal et ses applications.")
    return contenu


def selectionner_identifiants(
    source: dict[str, object], cible: dict[str, object], selection: Sequence[str] | None
) -> tuple[str, ...]:
    """Valide les applications à copier sans élargir la promotion."""
    disponibles = set(source)
    attendues = set(cible)
    if not attendues.issubset(disponibles):
        raise ErreurPromotion("Le canal source ne contient pas tous les paquets du canal cible.")
    identifiants = tuple(dict.fromkeys(selection)) if selection is not None else tuple(sorted(attendues))
    if not identifiants or not set(identifiants).issubset(attendues):
        raise ErreurPromotion("La sélection contient une application absente du canal cible.")
    return identifiants


def promouvoir(
    source: dict[str, object], cible: dict[str, object], selection: Sequence[str] | None = None
) -> dict[str, object]:
    """Copie les versions validées vers le seul canal suivant autorisé."""
    canal_source = source["channel"]
    canal_cible = cible["channel"]
    if not isinstance(canal_source, str) or not isinstance(canal_cible, str):
        raise ErreurPromotion("Les canaux doivent être des chaînes.")
    if PROMOTIONS.get(canal_source) != canal_cible:
        raise ErreurPromotion("Seules les promotions development→preview et preview→stable sont autorisées.")
    applications = source["applications"]
    applications_cible = cible["applications"]
    if not isinstance(applications, dict) or not isinstance(applications_cible, dict) or not applications:
        raise ErreurPromotion("Aucune application ARCenal à promouvoir.")
    identifiants = selectionner_identifiants(applications, applications_cible, selection)
    versions = dict(applications_cible)
    for identifiant in identifiants:
        versions[identifiant] = applications[identifiant]
    resultat = dict(cible)
    resultat["applications"] = {identifiant: versions[identifiant] for identifiant in sorted(versions)}
    resultat["promoted_from"] = canal_source
    return resultat


def ecrire(chemin: Path, contenu: dict[str, object]) -> None:
    """Écrit le manifeste cible de manière atomique."""
    temporaire = chemin.with_suffix(".tmp")
    temporaire.write_text(json.dumps(contenu, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temporaire.replace(chemin)


def arguments(argv: Sequence[str]) -> argparse.Namespace:
    """Déclare l'interface de promotion non interactive."""
    analyseur = argparse.ArgumentParser(description=__doc__)
    analyseur.add_argument("--source", required=True, type=Path)
    analyseur.add_argument("--target", required=True, type=Path)
    analyseur.add_argument("--application", action="append", dest="applications")
    return analyseur.parse_args(argv)


def executer(argv: Sequence[str]) -> int:
    """Promeut une diffusion ou retourne un code d'échec explicite."""
    options = arguments(argv)
    try:
        ecrire(options.target, promouvoir(charger(options.source), charger(options.target), options.applications))
    except (OSError, json.JSONDecodeError, ErreurPromotion) as erreur:
        print(f"Erreur de promotion : {erreur}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(executer(sys.argv[1:]))
