# Catalogue ARCenal

Ce dépôt publie le catalogue ARCenal stable pour YunoHost. Le flux brut GitHub
est la source canonique consommée par les clients ; GitHub Pages en publie un
miroir lisible.

L'URL de base à configurer sur les clients est :

```text
https://raw.githubusercontent.com/arcenal-coder/arcenal-systeme-catalogue/main/stable
```

Le flux consommé par YunoHost est généré à l'adresse
`stable/v3/apps.json`. Toute modification de `config/catalogue-client.toml`
est validée puis fusionnée sur `main` avant publication.

Ne jamais ajouter de secret dans ce dépôt. Les paquets ARCenal référencés
doivent être publiquement accessibles aux serveurs clients.

## Diffusion contrôlée

Les fichiers `config/releases/development.json`, `preview.json` et
`stable.json` figent les révisions autorisées pour chaque canal. GitHub Pages
publie pour chacun le catalogue YunoHost v3 et un manifeste de diffusion v1.

La promotion est strictement séquentielle : `development → preview → stable`.
Le workflow **Promouvoir une diffusion ARCenal** est le seul chemin de
promotion : il doit être protégé par les environnements GitHub
`promotion-preview` et `promotion-stable`, avec une approbation ARCenal.
La branche `main` doit aussi être protégée (pull request obligatoire) et
l'environnement `github-pages` doit exiger la même approbation avant toute
publication. La procédure de recette est dans
[`acceptance/PROCEDURE.md`](acceptance/PROCEDURE.md).
