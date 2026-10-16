# Diffusion ARCenal Store 1.2.0~ynh4

## Périmètre et autorisation

- Paquet : `arcenal-store`, révision `3a510983b4c832e442ca259901ae89882867c9dc`.
- Cause : les canaux annonçaient encore `1.2.0~ynh3` à la révision `70692faf369e5d9766e6a13516958e3e10186949`, malgré la publication du nouveau paquet sur GitHub.
- Mise à jour initiale limitée au canal development, puis promotions sélectives `development → preview → stable` par le workflow existant avec `application=arcenal-store`.
- Le client a explicitement autorisé la fusion après contrôles et ces deux promotions sur la base des contrôles automatisés, en connaissance de l'absence de recette sur serveur YunoHost.
- Les versions et révisions des autres applications ne sont pas promues.

## Preuves locales

| Contrôle | Résultat | Preuve |
| --- | --- | --- |
| Tests du paquet Store | RÉUSSI | 15 tests : `python3 -m unittest discover -s tests -v`, environnement virtuel avec PyYAML 6.0.3 |
| Syntaxe Bash du paquet | RÉUSSI | `bash -n` sur les huit scripts du paquet |
| Tests du catalogue | RÉUSSI | 18 tests : `python3 -m unittest discover -s tests -v` |
| Syntaxe Python du générateur et de la promotion | RÉUSSI | Analyse AST des deux scripts |
| Cohérence des trois flux v3 et manifestes v1 | RÉUSSI | Régénération en mémoire depuis les sources publiées, comparaison exacte avec les fichiers versionnés |
| Espaces et erreurs de patch | RÉUSSI | `git diff --check` |
| Installation et upgrade réels sur YunoHost | NON_EXÉCUTÉ | Aucun accès à un serveur de recette utilisé pour ce lot |
| Sauvegarde/restauration et retrait réels | NON_EXÉCUTÉ | Tests locaux des fonctions, sans cycle de vie complet sur YunoHost |
| Vérification visuelle des mises à jour dans la WebAdmin | NON_EXÉCUTÉ | À réaliser après actualisation du catalogue sur le serveur client |

## Publication et retour arrière

Les contrôles GitHub de la pull request doivent réussir avant fusion. Les deux
promotions sont lancées successivement avec une sélection limitée au Store.
Après publication, vérifier les références du Store dans les flux publics v1 et
v3 de chaque canal et conserver les liens des exécutions GitHub dans la PR.

En cas d'incident de diffusion, suspendre la publication suivante et préparer
une correction ciblée du Store suivant le même circuit. La référence précédente
était `1.2.0~ynh3` / `70692faf369e5d9766e6a13516958e3e10186949` ; rétablir une
référence de catalogue ne rétrograde pas un paquet déjà installé. Toute
restauration sur un serveur nécessite sa sauvegarde et une autorisation distincte.
