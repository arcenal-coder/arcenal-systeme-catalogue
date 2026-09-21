# Catalogue ARCenal

Ce dépôt publie le catalogue ARCenal stable pour YunoHost avec GitHub Pages.

L'URL de base à configurer sur les clients est :

```text
https://arcenal-coder.github.io/arcenal-systeme-catalogue/stable
```

Le flux consommé par YunoHost est généré à l'adresse
`stable/v3/apps.json`. Toute modification de `config/catalogue-client.toml`
est validée puis fusionnée sur `main` avant publication.

Ne jamais ajouter de secret dans ce dépôt. Les paquets ARCenal référencés
doivent être publiquement accessibles aux serveurs clients.
