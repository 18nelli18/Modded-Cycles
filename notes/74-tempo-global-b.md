# 74 — TEMPO global natif depuis la banque MIDI B

Demande d’AveyCole du 13/10/2026 : rendre le bouton TEMPO et son menu natif
accessibles en B ; revenir à B en fermant le menu. Le combo de sortie B ne
doit agir que depuis son écran principal. Adresses : VA OS Model:Cycles 1.13.

## Réponse courte

[FAIT] Le handler B ne transmet pas le code touche **14** (TEMPO) au handler
global. La liste ne comprend que PATTERN3, LFO8, REC9 et SETTINGS13.
[FAIT en émulation] La correction transmet TEMPO et empile le menu natif sans
fermer B. Aucun dessin, option, moteur tempo ou hook disque n’est remplacé.

## Raccordement et réserve

- `tools/gen_midi_tempo.py` transforme la recette RAM courante ; refuse une
  base qui réactive Save/Load MIDI ou dont les octets/symboles diffèrent.
- `tools/machines/midi_lanes/tempo.s` : dispatch REC9/SETTINGS13/TEMPO14,
  présentation native sans groupe de fermeture B, toggle TEMPO par type,
  garde du combo selon la vue au sommet.
- Nouveau hook natif : appel toggle à `0x4001c23a`, vérifié contre
  `jsr 0x40077da8`. Le constructeur tempo `0x4003d50e`, la vtable
  `0x40107d50`, le rendu et le handler natif `0x4003d99e` restent intacts.
- Réserve propre déjà présente : corps inutilisé de `ml_store_save_notice`
  entre son RTS conservé et `ml_store_save_hook`, 362 octets. Aucun nouveau
  masque natif, aucune extension de RAM, aucun déplacement de symbole musical.
- `ViewManager` est à contexte UI +64 ; sa liste double à +20 est insérée en
  fin par `0x400f5a80`. Le dernier nœud doit désigner B pour autoriser le combo.
- Le vecteur de groupes du menu est temporairement vide à la présentation,
  puis restauré. Les groupes natifs des autres vues et le comportement A sont
  conservés. Un second objet Tempo ferme la vue Tempo déjà ouverte par type.

## Vérifications

`tools/emu/test_midi_tempo.py` compare dispatch ancien/corrigé, exécute le
ViewManager natif et le handler BACK natif du menu Tempo, vérifie plusieurs
ouvertures/fermetures, la garde du combo et le passage A inchangé. Les frontières
mutex/refcount/focus et callbacks de fermeture sont simulées : ce n’est pas
une validation matérielle de l’écran.

Les preuves placées CC locks, slides et live-rec passent. Le build complet
avec Select All tient avec **83 octets de marge**. Le navigateur reconstruit
les deux variantes USB6/sans USB6 aux hashes Python attendus ; transfert simulé
de 687 blocs identique octet pour octet. Build/transport restent ceux du principal.

[À FAIRE] AveyCole doit vérifier le bouton TEMPO, ses options, le changement
global du tempo des douze pistes et le retour B sur son appareil. Données B
toujours RAM uniquement ; sauvegarde MIDI désactivée.
