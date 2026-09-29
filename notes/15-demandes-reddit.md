# 15 · Demandes de la communauté (Reddit) : réponses et plan

Le 29/09/2026, après la validation du 6 canaux et de SD VINTAGE sur un vrai Model:Cycles, l'utilisateur a relayé quatre
demandes d'utilisateurs de r/Elektron. Cette note les traite **une par une**, dans l'ordre le plus efficace :
d'abord ce qui existe déjà et se livre vite, ensuite ce qui demande de la recherche.

## 0. En bref

| # | Demande | État | Où |
|---|---|---|---|
| 1 | Un mode mute sans tenir FUNC | ✅ **livré** : tweak `latching-mute` de drumkilla, dans le flasher web | §1 |
| 2 | Regrouper avec le tweak « trig preview » | ✅ **livré** : `trig-preview` (et `browser-scroll`), dans le flasher web | §2 |
| 3 | Flasher l'OS Model:Samples, ou une machine « samples » dans l'OS Cycles | 🟠 **recherche** : il faut l'OS Model:Samples 1.13 pour l'analyser | §3 |
| 4 | Porter les machines numériques du Syntakt | 🟠 **recherche** : il faut l'OS Syntakt pour l'analyser | §4 |

Ordre proposé pour la suite : **§3 d'abord** (fichier de 686 Ko, une comparaison de deux OS 1.13 répond vite à la question
clé : le matériel est-il le même ?), **puis §4** (plus long, mais il s'appuie sur le banc d'émulation de SD VINTAGE).

---

## 1. Mode mute sans tenir FUNC — ✅ livré

**Demande** : pouvoir muter sans appuyer sur FUNC, via un raccourci plutôt que par le menu.
> Source : commentaire r/Elektron relayé par l'utilisateur le 29/09/2026.

**Réponse** : le tweak `latching-mute` de [drumkilla/elektron-model-tweaks](https://github.com/drumkilla/elektron-model-tweaks)
fait exactement ça.
- Maintenir **TRK** et taper **FUNC** : le mode mute reste verrouillé, la touche FUNC s'allume. Les trigs mutent alors les pistes sans tenir FUNC.
- Un appui court sur FUNC seul en sort. Les combinaisons avec FUNC (menus, encodeurs rapides) ne le font pas sortir.
- Le comportement d'origine (tenir FUNC) est inchangé.
> Source : README de drumkilla/elektron-model-tweaks, section *Latching track mute* (commit `6e0b4df`), et la description du tweak
> `tweaks/model-cycles_OS1.13/01-latching-mute.json`.

**Ce qui a été fait** :
- Le fichier du tweak est repris **sans modification** dans `tweaks/model-cycles_OS1.13/` (licence MIT, auteur crédité).
- Notre `build.py` produit **le même MAIN OS, octet pour octet**, que le `tweak.py` de drumkilla (vérifié le 29/09/2026).
- Il est proposé dans le flasher web, combinable avec le 6 canaux, avec l'auteur affiché sur la carte.
- Testé sur du vrai matériel **par son auteur** ; pas encore par nous.

## 2. Trig preview — ✅ livré

**Demande** : regrouper nos mods avec celui qui a ajouté le « trig preview » au Model:Cycles.
> Source : commentaire r/Elektron relayé par l'utilisateur, qui l'identifie à drumkilla/elektron-model-tweaks.

**Réponse** : c'est bien le tweak `trig-preview` du même dépôt.
- Séquenceur à l'arrêt : maintenir un pas et appuyer sur PAGE fait jouer ce pas, avec sa note, sa longueur, ses p-locks et son sound-lock.
- La page ne tourne pas. Il joue même si la condition de trig ou la probabilité l'excluraient, et même sur une piste mutée.
> Source : README de drumkilla/elektron-model-tweaks, section *Trig preview*.

Le troisième tweak du dépôt, `browser-scroll` (défilement des noms longs dans le navigateur), est livré avec.
Même vérification octet pour octet, même crédit.

### Point technique : une exception au contrôle des caves

Notre `build.py` refusait `browser-scroll` : une constante de l'OS (`0x40148564`) pointe vers la zone `0xFF` où il écrit.
Vérifié à la main :
- La zone `0x401485ee` est la **table caractère → glyphe** d'une petite police de chiffres (0-9, `%`, `.`, `/`) : 256 entrées de 16 bits, `0xFFFF` = pas de glyphe.
- Juste après, `0x401487ee` est la table des **largeurs**, qui vaut 0 pour tous les caractères sans glyphe.
- `browser-scroll` n'écrit que les entrées des caractères de contrôle 1 à 8, jamais dessinés. drumkilla a volontairement laissé l'entrée 0 intacte.
- Les caves de `latching-mute` (`0x40148662`, 396 o) sont les entrées 58 à 255 de la même table : même raisonnement, et aucune référence directe n'y pointe.

Plutôt que `--force-cave`, cette référence est déclarée dans `device.json` (`cave_refs_ok`), avec la partie réellement libre (`0x401485f0`–`0x4014862e`, caractères 1 à 31).
Le build l'accepte tant que les écritures restent dans cette partie, et refuse sinon. La règle est la même en Python et en JS, et elle est testée (`tools/webbuild_check.sh`).
> Source : octets de l'OS 1.13 officiel, décodés le 29/09/2026 (table des glyphes et des largeurs).

---

## 3. OS Model:Samples sur un Model:Cycles, ou une machine « samples » — 🟠 recherche

**Demande** (deux idées liées) :
- une voie pour flasher le logiciel du Model:Samples sur le Model:Cycles, et idéalement faire tourner « les deux en même temps » ;
- un utilisateur de Reddit dit avoir ajouté une machine « samples » au firmware Cycles, sans jamais donner de détails.
> Source : commentaire r/Elektron relayé par l'utilisateur, avec le lien vers le fil *Flashing Model:Cycles firmware into a Model:Samples*.
> Le fil lui-même n'a pas pu être lu d'ici : Reddit bloque l'accès automatisé, et la page Gearspace sur le même sujet affiche une vérification anti-robot.

**Ce qu'on sait déjà** :
- L'OS Cycles tourne sur un Model:Samples : c'est ainsi que le mod 6 canaux a été vérifié ([01](01-ms-multi-output.md)).
- L'inverse (OS Samples sur un vrai Model:Cycles) **n'a jamais été testé publiquement** : le Samples échantillonne et pourrait
  attendre une mémoire ou un stockage que le Cycles n'a pas.
  > Source : résumé du dépôt `bryantysinger/elektron-models-teardown` dans l'index d'un moteur de recherche. Le dépôt est supprimé
  > (vérifié le 29/09/2026 : `404`), on ne peut donc pas relire le texte d'origine.
- Le Model:Samples a 1 Go de stockage et 64 Mo de RAM pour les samples du projet.
  > Source : test du Model:Samples par Attack Magazine (attackmagazine.com), repris par les résultats de recherche.
- `[HYP]` Le Model:Cycles a probablement la même RAM : son moteur range l'état des voix à `0x42308828`, soit à plus de 35 Mo
  du début de la SDRAM (`0x40000000`), ce qui suppose au moins 64 Mo si la puce est standard ([14 §2.4](14-machine-sd-vintage.md)).
  Le stockage (flash du +Drive) reste inconnu.

**Plan** (sans matériel au début) :
1. `[À FAIRE]` Télécharger l'**OS Model:Samples 1.13** (`model-samples_OS1.13.zip`, 686 Ko, elektron.se), avec ton accord.
   Comme pour le Cycles, il ne sera **jamais versionné** (`firmware/` est ignoré par git).
2. `[À FAIRE]` Comparer les deux OS 1.13, section par section :
   - bootloader et updater identiques ? (même carte, même boot) ;
   - carte mémoire utilisée, pilotes du stockage (taille attendue, système de fichiers) ;
   - lecture du panneau (touches, encodeurs, LED) : le Cycles et le Samples ont-ils la même matrice ?
3. Décider selon le résultat :
   - **Voie A, OS Samples complet sur le Cycles** : c'est la « route de flash » demandée, sans « les deux en même temps ».
     Réalisable si le matériel est le même. Risques : le stockage des projets Cycles, et un panneau étiqueté Cycles.
     La récupération par le MIDI IN reste possible, car le bootloader n'est jamais touché.
   - **Voie B, une machine « sample » dans l'OS Cycles** : ce serait « les deux en même temps ». C'est de très loin le plus lourd :
     lecture de samples dans le moteur, chargement depuis le stockage, choix du sample dans l'UI, gestion par Transfer.
     La [note 10 §4](10-faisabilite-fonctionnalites.md) la jugeait hors de portée. La comparaison du point 2 dira si une version
     réduite est possible (par exemple quelques samples fixes).

## 4. Machines numériques du Syntakt — 🟠 recherche

**Demande** : porter les moteurs numériques supplémentaires du Syntakt, en partant de la ROM (l'OS) et d'un banc d'émulation pour la comprendre.
> Source : commentaire r/Elektron relayé par l'utilisateur.

**Ce qu'on sait déjà** :
- Les machines numériques du Syntakt sont à base de FM et dérivées de celles du Model:Cycles ([14 §1](14-machine-sd-vintage.md)).
- SD VINTAGE ([14](14-machine-sd-vintage.md)) a été écrite en **clean-room** : l'OS du Syntakt n'était pas accessible depuis
  l'environnement de travail d'alors. Elle marche sur le matériel (29/09/2026).
- Le banc d'émulation du moteur du M:C (`tools/emu/`) tourne désormais aussi sur ton Mac.
- L'OS actuel du Syntakt est la **1.41** (09/09/2026), 28 Mo.
  > Source : page de téléchargements Syntakt d'elektron.se, consultée le 29/09/2026 (taille confirmée par l'en-tête HTTP : 28 063 003 o).

**Plan** :
1. `[À FAIRE]` Télécharger l'**OS Syntakt 1.41** (`Syntakt-OS-1.41.zip`, 28 Mo), avec ton accord. Jamais versionné.
2. `[À FAIRE]` Identifier le format (conteneur, compression) et le **processeur**.
   S'il s'agit aussi d'un ColdFire avec EMAC, le code des machines se relit avec nos outils.
3. `[À FAIRE]` Localiser les machines numériques (tables de dispatch, descripteurs de paramètres, comme en [14 §2](14-machine-sd-vintage.md)).
   Les rejouer dans un banc d'émulation et mesurer leur son.
4. Porter une première machine en suivant le chemin déjà validé par SD VINTAGE : d'abord à la place d'une machine existante, puis en 7ᵉ machine.
   Premier candidat naturel : le **vrai SD VINTAGE**, pour le comparer à notre version.

**Règle de publication** : aucun code Elektron dans le dépôt, comme pour le reste du projet. Deux façons de porter :
- **Réécriture clean-room** (comme SD VINTAGE), réglée sur les mesures faites dans le banc : la plus sûre ;
- **Extraction au moment du build** depuis le fichier Syntakt que l'utilisateur fournit lui-même (le dépôt ne contiendrait que des adresses et des tables de patch).
  À réserver au cas où le processeur est le même, et en gardant en tête que la licence du firmware Syntakt n'autorise
  peut-être pas cet usage (non vérifié).
