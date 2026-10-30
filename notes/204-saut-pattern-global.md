# 204 — Direct Pattern Jump global

Demande AveyCole,30/10/2026 : porter Direct Pattern Jump de PPPCCC et proposer
`Global > JUMP > OFF/ON`, avec sauvegarde globale. Adresses : VA OS1.13.

## Reponse courte

[FAIT en emulation] OFF par defaut ; ON active PATTERN puis FUNC + TRIG.
Le changement conserve le prochain pas de chaque piste modulo sa nouvelle longueur.
TRIG seul conserve le changement normal en fin de pattern. La preference est
unique pour toutes les pistes et projets, dans `/DirectJump.cfg`.
Les ecritures sont differees pendant lecture ou enregistrement.

## 1. Provenance

Source : `gialloinfuso/PPPCCC-M-S-Mods`, revision
`43b894bd14f55313cef6381af9a008acec3ed0f1`, MIT, copyright2026
PPPCCC/gialloinfuso. `tools/machines/direct_jump/upstream.py` conserve le
generateur amont (seuls les imports changent). Les instructions natives rejouees
sont extraites du fichier officiel au build. Licence jointe, aucun octet ROM
ni firmware ajoute au depot.

## 2. Integration

Generateur : `tools/gen_direct_jump.py`. Entrees epinglees : les quatre socles
publies2.61 et le candidat MD all22 prive2.62. Les hooks natifs sont verifies
contre leurs empreintes amont et contre le socle avant chaque ecriture.

Code : `0x46920000`, quatre blocs amont de512octets ; wrappers, menu et UI
a partir de `0x46921000`, tous avant `0x46930000`. BSS propre a partir de
`0x46930000`, moins de `0x46940000` (GATED). Ni POTS, ni MD, ni WAVE ne sont
recouverts. Le chargeur sparse conserve les registres et chaine le callback
de boot precedent. Avec MD il conserve le chargeur MD et ses adresses absolues.

Les sept portes OFF conservent registres, pile et CCR puis rejouent le chemin
natif. Desactiver annule aussi REQ/FIX/KEEP pour eviter un saut deja demande.
Global compte12lignes en Full,11en Lite ; FX et ACID restent editables.
Le titre experimental affiche2.62 ; les flasheurs publics restent2.61.

## 3. Preuves

`tools/emu/test_direct_jump.py` : vrai bootstrap et ISR,3000ticks sans requete,
changements normaux et per-track, sept positions de saut16vers12, neuf cas de
longueurs/vitesses par piste, saut vers le meme pattern, MIDI PC, controles
PATTERN/FUNC/TRIG et observateur de fenetre. OFF :700ticks et gestes identiques
au socle. Execution sur les quatre editions et Optional MD all22.

`tools/emu/test_direct_jump_ui.py` : vraies lignes MenuView, navigation DATA et
BACK, OFF/ON, ecriture differee, cold reload, rejet de quatre fichiers invalides,
choix change avant lecture du fichier conserve, maintien de FX/ACID.

Fichiers et rapports locaux : `../direct-jump-test/`. HMAC, capacite flash,
bootstrap Samples natif et ses deux verificateurs sont controles a la livraison.
Marge MD all22 :82192octets. Aucun resultat appareil ou pourcentage CPU mesure.
Les fichiers de test directs ne possedent pas le popup diagnostic CPU/CUT.

## 4. Essai demande

[A FAIRE sur appareil] Activer JUMP, essayer plusieurs variations et longueurs,
confirmer le groove, les longueurs/vitesses par piste et les Program Changes.
Redemarrer pour confirmer ON ; remettre OFF et verifier les changements normaux.
Ces images restent privees experimentales et ne sont pas poussees.
