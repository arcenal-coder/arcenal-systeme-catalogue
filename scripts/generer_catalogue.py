#!/usr/bin/env python3
"""Construit un catalogue YunoHost v3 à partir d'une liste blanche ARCenal."""

from __future__ import annotations

import argparse
import copy
import json
import sys
import tomllib
import re
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Mapping, Sequence
from urllib.request import urlopen

CANEAUX_VALIDES = frozenset({"stable", "preview", "development"})
REVISION_GIT = re.compile(r"^[0-9a-f]{40}$")


class ErreurCatalogue(ValueError):
    """Signale une configuration ou une source de catalogue invalide."""


@dataclass(frozen=True)
class ApplicationArcenal:
    identifiant: str
    nom: str
    description_fr: str
    depot: str
    branche: str
    revision: str | None
    canaux: frozenset[str]
    version: str
    minimum_yunohost: str
    architectures: str
    multi_instance: bool
    ldap: bool
    sso: bool
    disque: str
    ram_build: str
    ram_runtime: str


@dataclass(frozen=True)
class DiffusionCanal:
    """Décrit les versions ARCenal autorisées dans un canal publié."""

    canal: str
    applications: Mapping[str, Mapping[str, str]]


def charger_toml(chemin: Path) -> dict[str, object]:
    """Charge la configuration TOML depuis un chemin explicite."""
    with chemin.open("rb") as fichier:
        contenu: dict[str, object] = tomllib.load(fichier)
    return contenu


def charger_diffusion(chemin: Path, canal: str) -> DiffusionCanal:
    """Charge et valide le manifeste immuable d'un canal ARCenal."""
    with chemin.open(encoding="utf-8") as fichier:
        contenu: object = json.load(fichier)
    if not isinstance(contenu, dict) or contenu.get("schema") != "arcenal-release/v1":
        raise ErreurCatalogue("Le manifeste de diffusion ARCenal est invalide.")
    if contenu.get("channel") != canal:
        raise ErreurCatalogue("Le manifeste de diffusion ne correspond pas au canal demandé.")
    applications = contenu.get("applications")
    if not isinstance(applications, dict):
        raise ErreurCatalogue("Le manifeste de diffusion doit contenir applications.")
    resultat: dict[str, Mapping[str, str]] = {}
    for identifiant, version in applications.items():
        if not isinstance(identifiant, str) or not isinstance(version, dict):
            raise ErreurCatalogue("Chaque version diffusée doit être un objet nommé.")
        revision = version.get("revision")
        paquet = version.get("version")
        if not isinstance(revision, str) or not REVISION_GIT.fullmatch(revision):
            raise ErreurCatalogue("Chaque révision diffusée doit être un SHA Git complet.")
        if not isinstance(paquet, str) or not paquet:
            raise ErreurCatalogue("Chaque version diffusée doit avoir une révision et une version.")
        resultat[identifiant] = {"revision": revision, "version": paquet}
    return DiffusionCanal(canal=canal, applications=resultat)


def lire_json_source(source: str) -> dict[str, object]:
    """Lit un catalogue JSON depuis une URL HTTPS ou un fichier local."""
    if source.startswith("https://"):
        with urlopen(source, timeout=30) as reponse:  # nosec B310: source administrée.
            contenu: object = json.load(reponse)
    else:
        with Path(source).open(encoding="utf-8") as fichier:
            contenu = json.load(fichier)
    if not isinstance(contenu, dict):
        raise ErreurCatalogue("La source officielle doit contenir un objet JSON.")
    return contenu


def exiger_chaine(valeur: object, champ: str) -> str:
    """Retourne une chaîne non vide ou lève une erreur de configuration."""
    if not isinstance(valeur, str) or not valeur.strip():
        raise ErreurCatalogue(f"Le champ {champ} doit être une chaîne non vide.")
    return valeur


def exiger_booleen(valeur: object, champ: str) -> bool:
    """Retourne un booléen explicite ou lève une erreur de configuration."""
    if not isinstance(valeur, bool):
        raise ErreurCatalogue(f"Le champ {champ} doit être un booléen.")
    return valeur


def creer_application_arc(enregistrement: object) -> ApplicationArcenal:
    """Valide une déclaration d'application ARCenal unique."""
    if not isinstance(enregistrement, dict):
        raise ErreurCatalogue("Chaque application ARCenal doit être une table TOML.")
    canaux_lus = enregistrement.get("canaux", [])
    if not isinstance(canaux_lus, list) or not all(isinstance(item, str) for item in canaux_lus):
        raise ErreurCatalogue("Le champ canaux doit être une liste de chaînes.")
    canaux = frozenset(canaux_lus)
    if not canaux or not canaux.issubset(CANEAUX_VALIDES):
        raise ErreurCatalogue("Chaque application ARCenal doit cibler des canaux valides.")
    depot = exiger_chaine(enregistrement.get("depot"), "applications.arcenal.depot")
    if not depot.startswith("https://"):
        raise ErreurCatalogue("Le dépôt d'une application ARCenal doit utiliser HTTPS.")
    revision_lue = enregistrement.get("revision")
    if revision_lue is not None and not isinstance(revision_lue, str):
        raise ErreurCatalogue("La révision d'une application ARCenal doit être une chaîne.")
    return ApplicationArcenal(
        identifiant=exiger_chaine(enregistrement.get("id"), "applications.arcenal.id"),
        nom=exiger_chaine(enregistrement.get("nom"), "applications.arcenal.nom"),
        description_fr=exiger_chaine(enregistrement.get("description_fr"), "applications.arcenal.description_fr"),
        depot=depot,
        branche=exiger_chaine(enregistrement.get("branche"), "applications.arcenal.branche"),
        revision=revision_lue,
        canaux=canaux,
        version=exiger_chaine(enregistrement.get("version"), "applications.arcenal.version"),
        minimum_yunohost=exiger_chaine(enregistrement.get("minimum_yunohost"), "applications.arcenal.minimum_yunohost"),
        architectures=exiger_chaine(enregistrement.get("architectures"), "applications.arcenal.architectures"),
        multi_instance=exiger_booleen(enregistrement.get("multi_instance"), "applications.arcenal.multi_instance"),
        ldap=exiger_booleen(enregistrement.get("ldap"), "applications.arcenal.ldap"),
        sso=exiger_booleen(enregistrement.get("sso"), "applications.arcenal.sso"),
        disque=exiger_chaine(enregistrement.get("disque"), "applications.arcenal.disque"),
        ram_build=exiger_chaine(enregistrement.get("ram_build"), "applications.arcenal.ram_build"),
        ram_runtime=exiger_chaine(enregistrement.get("ram_runtime"), "applications.arcenal.ram_runtime"),
    )


def applications_arcenal(
    configuration: Mapping[str, object], diffusion: DiffusionCanal | None = None
) -> tuple[ApplicationArcenal, ...]:
    """Transforme les déclarations internes en contrats applicatifs validés."""
    bloc = configuration.get("applications", {})
    declarations = bloc.get("arcenal", []) if isinstance(bloc, dict) else []
    if not isinstance(declarations, list):
        raise ErreurCatalogue("applications.arcenal doit être une liste.")
    resultat = tuple(creer_application_arc(item) for item in declarations)
    identifiants = tuple(application.identifiant for application in resultat)
    if len(identifiants) != len(set(identifiants)):
        raise ErreurCatalogue("Les identifiants d'applications ARCenal doivent être uniques.")
    if diffusion is None:
        return resultat
    versions = diffusion.applications
    attendues = {application.identifiant for application in resultat if diffusion.canal in application.canaux}
    if set(versions) != attendues:
        raise ErreurCatalogue("Le manifeste de diffusion doit référencer exactement les paquets ARCenal du canal.")
    return tuple(
        replace(
            application,
            revision=versions[application.identifiant]["revision"],
            version=versions[application.identifiant]["version"],
        )
        if application.identifiant in versions
        else application
        for application in resultat
    )


def identifiants_officiels(configuration: Mapping[str, object], canal: str) -> tuple[str, ...]:
    """Lit la liste blanche d'un canal et rejette tout canal inconnu."""
    if canal not in CANEAUX_VALIDES:
        raise ErreurCatalogue(f"Canal inconnu : {canal}.")
    canaux = configuration.get("canaux", {})
    declaration = canaux.get(canal, {}) if isinstance(canaux, dict) else {}
    identifiants = declaration.get("applications_yunohost", []) if isinstance(declaration, dict) else []
    if not isinstance(identifiants, list) or not all(isinstance(item, str) for item in identifiants):
        raise ErreurCatalogue(f"canaux.{canal}.applications_yunohost doit être une liste.")
    maintenues = declaration.get("applications_maintenues", []) if isinstance(declaration, dict) else []
    if not isinstance(maintenues, list) or not all(isinstance(item, str) for item in maintenues):
        raise ErreurCatalogue(f"canaux.{canal}.applications_maintenues doit être une liste.")
    return tuple(dict.fromkeys([*identifiants, *maintenues]))


def serialiser_application_arc(application: ApplicationArcenal) -> dict[str, object]:
    """Produit le sous-ensemble v3 nécessaire à une application interne."""
    git = {"url": application.depot, "branch": application.branche}
    if application.revision:
        git["revision"] = application.revision
    return {
        "id": application.identifiant,
        "state": "working",
        "level": 8,
        "maintained": True,
        "category": "system_tools",
        "subtags": [],
        "potential_alternative_to": [],
        "git": git,
        "manifest": {
            "id": application.identifiant,
            "name": application.nom,
            "description": {"fr": application.description_fr},
            "version": application.version,
            "packaging_format": 2,
            "integration": {
                "yunohost": application.minimum_yunohost,
                "architectures": application.architectures,
                "multi_instance": application.multi_instance,
                "ldap": application.ldap,
                "sso": application.sso,
                "disk": application.disque,
                "ram": {"build": application.ram_build, "runtime": application.ram_runtime},
            },
        },
    }


def construire_catalogue(
    source: Mapping[str, object],
    configuration: Mapping[str, object],
    canal: str,
    diffusion: DiffusionCanal | None = None,
) -> dict[str, object]:
    """Filtre la source officielle et y ajoute les paquets ARCenal du canal."""
    applications_source = source.get("apps")
    if not isinstance(applications_source, dict):
        raise ErreurCatalogue("La source officielle ne contient pas apps.")
    selection = identifiants_officiels(configuration, canal)
    manquantes = sorted(item for item in selection if item not in applications_source)
    if manquantes:
        raise ErreurCatalogue(f"Applications officielles introuvables : {', '.join(manquantes)}.")
    applications = {item: sans_logo(applications_source[item]) for item in selection}
    for application in applications_arcenal(configuration, diffusion):
        if canal in application.canaux:
            if application.identifiant in applications:
                raise ErreurCatalogue(f"Conflit d'identifiant : {application.identifiant}.")
            applications[application.identifiant] = serialiser_application_arc(application)
    return {"apps": applications, "categories": source.get("categories", []), "antifeatures": source.get("antifeatures", []), "security": source.get("security", [])}


def sans_logo(application: object) -> object:
    """Évite de référencer des logos qui ne sont pas publiés par ARCenal."""
    if not isinstance(application, dict):
        raise ErreurCatalogue("Chaque application officielle doit être un objet JSON.")
    copie = copy.deepcopy(application)
    copie.pop("logo_hash", None)
    return copie


def ecrire_json(catalogue: Mapping[str, object], sortie: Path) -> None:
    """Écrit le flux de manière atomique et lisible."""
    sortie.parent.mkdir(parents=True, exist_ok=True)
    temporaire = sortie.with_suffix(f"{sortie.suffix}.tmp")
    temporaire.write_text(json.dumps(catalogue, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temporaire.replace(sortie)


def analyser_arguments(arguments: Sequence[str]) -> argparse.Namespace:
    """Construit l'interface de ligne de commande du générateur."""
    analyseur = argparse.ArgumentParser(description=__doc__)
    sous_commandes = analyseur.add_subparsers(dest="commande", required=True)
    build = sous_commandes.add_parser("build", help="génère le catalogue ARCenal")
    build.add_argument("--config", required=True, type=Path)
    build.add_argument("--output", required=True, type=Path)
    build.add_argument("--channel", default="stable", choices=sorted(CANEAUX_VALIDES))
    build.add_argument("--source", help="URL ou fichier JSON, remplace la source configurée")
    build.add_argument("--release", type=Path, help="manifeste de diffusion du canal")
    return analyseur.parse_args(arguments)


def executer(arguments: Sequence[str]) -> int:
    """Exécute la commande demandée et retourne un code de sortie stable."""
    options = analyser_arguments(arguments)
    configuration = charger_toml(options.config)
    bloc_catalogue = configuration.get("catalogue", {})
    source = options.source or (bloc_catalogue.get("source_officielle") if isinstance(bloc_catalogue, dict) else None)
    try:
        diffusion = charger_diffusion(options.release, options.channel) if options.release else None
        catalogue = construire_catalogue(
            lire_json_source(exiger_chaine(source, "catalogue.source_officielle")),
            configuration,
            options.channel,
            diffusion,
        )
        ecrire_json(catalogue, options.output)
    except (OSError, json.JSONDecodeError, ErreurCatalogue) as erreur:
        print(f"Erreur de génération : {erreur}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(executer(sys.argv[1:]))
