# Modded-Cycles

Notes techniques pour un projet de **mod firmware de l'Elektron Model:Cycles** : faire sortir en USB les **6 pistes séparément**
au lieu du seul mix stéréo, puis explorer des extensions (mix + pistes, panoramique, effets).

> ⚠️ **Aucune image firmware Elektron n'est incluse dans ce dépôt** — ni originale, ni modifiée.
> On travaille sur sa **propre** copie de l'OS officiel, téléchargée légalement depuis elektron.se.
> Ce dépôt ne contient que de l'analyse, des tables de diff (octets), des sources assembleur et des outils.
> Projet non affilié à Elektron, sans lien ni soutien de leur part. Flasher un OS modifié se fait **à ses risques** et peut annuler la garantie.

## Contenu

| Document | Sujet |
|---|---|
| [`dossier-technique.md`](dossier-technique.md) | Synthèse du fil Elektronauts « Model:Cycles Q&A with Ess », chaque info sourcée par une citation |
| [`notes/README.md`](notes/README.md) | **Index des notes techniques** et chiffres clés |
| [`notes/01`](notes/01-ms-multi-output.md) … [`09`](notes/09-analyse-firmware-1.13.md) | Le mod 6 canaux existant, le format des OS, la plateforme ColdFire, l'USB audio, la méthode de patch, le flash, des snippets, la feuille de route, et l'analyse de l'image 1.13 |

## Où en est le projet

- Le mod « 6 pistes en USB » **existe déjà** en amont ([scottmetoyer/ms-multi-output](https://github.com/scottmetoyer/ms-multi-output), MIT),
  avec une cible Model:Cycles **vérifiée par code mais jamais flashée sur un vrai Model:Cycles**.
- L'OS officiel **1.13** (la dernière version) a été analysé ; le build se reproduit à l'octet près.
- **Prochain jalon** : valider ce build sur un vrai Model:Cycles. Rien n'a encore été flashé.

Détails et étapes : [`notes/08-feuille-de-route.md`](notes/08-feuille-de-route.md).

## Crédits (dépôts amont, tous MIT, sans firmware inclus)

- [`scottmetoyer/ms-multi-output`](https://github.com/scottmetoyer/ms-multi-output) — le mod 6 canaux (Model:Samples et Model:Cycles)
- [`mischa85/elektron-firmware-tool`](https://github.com/mischa85/elektron-firmware-tool) — dépaquetage / repaquetage / re-signature des `.syx`
- [`mxldyn/octamax`](https://github.com/mxldyn/octamax) — rétro-ingénierie de l'OS Octatrack (méthode, outils, pièges)
