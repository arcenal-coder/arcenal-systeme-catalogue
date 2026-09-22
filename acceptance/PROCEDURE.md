# Procédure d'acceptation ARCenal

Cette procédure est exécutée sur un serveur de recette dédié, jamais sur un
client de production. Le serveur de recette utilise le canal `development`,
puis le canal `preview` après validation technique.

## Protection GitHub à configurer une fois

Dans les réglages du dépôt, protéger `main` en imposant une pull request et les
contrôles verts. Créer ensuite les environnements `promotion-preview`,
`promotion-stable` et `github-pages`, tous avec un approbateur ARCenal requis.
Sans ces protections, une personne pouvant écrire directement sur `main`
pourrait contourner la procédure d'acceptation.

## Avant promotion

1. Vérifier que les contrôles GitHub du paquet et du catalogue sont verts.
2. Installer ARCenal Store, puis ARCenal Système depuis le canal de recette.
3. Vérifier une installation neuve, puis une mise à jour depuis la version
   stable précédente.
4. Vérifier la création de la sauvegarde pré-mise à jour, la connexion, la
   déconnexion, le retour vers `/espace-perso`, l'administration et le
   catalogue autorisé.
5. Vérifier que les applications métier et le cœur YunoHost ne sont pas mis à
   jour par le minuteur ARCenal.

## Promotion

Après une recette validée, lancer le workflow GitHub **Promouvoir une diffusion
ARCenal** avec `development → preview`, puis `preview → stable`. Les
environnements GitHub `promotion-preview` et `promotion-stable` doivent exiger
une approbation ARCenal avant la publication.

La diffusion stable est consommée par les clients à l'adresse :

```text
https://raw.githubusercontent.com/arcenal-coder/arcenal-systeme-catalogue/main/stable/v1/release.json
```

Le minuteur client ne met à jour que `arcenal-store` et `arcenal-systeme`. Une
erreur interrompt le passage à l'étape suivante et reste visible dans le journal
du service `arcenal-systeme-update.service`.
