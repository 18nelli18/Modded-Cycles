# 104 — Toutes machines et beat repeat sans Banque MIDI

Demande AveyCole du 16/10/2026 : le build sans MIDI OUT Bank refuse « Beat repeat: payload capacity ». Priorite explicite avant le nouveau probleme filtre en forte activite. Adresses : VA de l'OS 1.13.

## Reponse courte

[FAIT] Tout selectionner puis retirer MIDI laisse Wizard non compresse (93 216 octets) puis les moteurs compresses jusqu'a 15 octets de la limite 0x40200000. Beat repeat demande 2 572 octets. Augmenter la recherche du compresseur ne libere que quelques octets. Le chemin MIDI compresse deja les supports en commun ; retirer MIDI faisait donc paradoxalement grossir le firmware.

## 1. Nouveau chemin experimental

`tools/machines/beat_repeat/capacity.js` intervient uniquement sans Banque MIDI, beat repeat actif, et si la disposition d'origine ne tient pas. Les deux payloads Wizard + moteur aPLib sont verifies par empreintes. Le moteur garde toutes ses adresses ; une copie de Wizard et 52 octets propres de stage PIC sont ajoutes a sa fin en RAM. Le payload commun est compresse a partir de la fin de l'OS officiel. Le chargeur moteur existant decompresse le tout ; son ancien appel init passe par le stage, qui copie Wizard a sa place d'origine puis saute vers cette meme init. Clear et cache Wizard restent ceux du noyau teste. Aucun code ou machine MIDI ajoute.

Tous les champs source/init sont gardes. ABI D0-D7/A0-A6 et pile transmis identiques a l'init originale. Pas de travail audio ou de fonction musicale ajoutee ; environ 93 Ko de copie RAM supplementaire au boot. Le build complet passe a 303 318 octets compresses, puis 2 572 octets beat repeat ; environ 46 Ko de marge flash. Taille descompressee moteur/support 646 596 octets. Le stage se situe 0x4679dd90 ; beat repeat suit 0x4679ddd0. Ces adresses dependent du profil et ne sont pas des constantes du compositeur.

## 2. Preuves

`tools/emu/test_no_midi_capacity.py` execute le vrai SYX navigateur, boot puis constructeur cache. Wizard est compare octet pour octet avant l'init originale, apres boot et apres cache ; la source et le stage restent intacts. Init appelee une seule fois. Le stage est ensuite appele avec registres sentinelles pour verifier son ABI.

La preuve beat repeat existante est executee sur le build complet sans MIDI : boot, seize divisions, Control All 64 masques, releases, stereo Wizard et chaines gain/clavier. Six profils navigateur signes et parite Python : complet sans MIDI, animation alternative, sans RETROSYN, sans Wizard, avec MIDI et beat repeat seul. Les quatre derniers restent identiques au principal s'ils ne depassent pas la capacite ; les deux premiers reproduisent le refus sur le principal. Aucune suppression de fonction choisie.

```
python3 tools/gen_no_midi_capacity.py --check
python3 tools/gen_no_midi_capacity_flasher.py --check
node tools/test_no_midi_capacity_flasher.js
python3 tools/emu/test_no_midi_capacity.py --case build/no-midi-capacity/all-no-midi
python3 tools/emu/test_beat_repeat.py --data build/feedback-beat-data.json --case build/no-midi-capacity/all-no-midi
```

## 3. Materiel et filtre

Experimental, confirmation machine attendue. Testpage uniquement, principal 1.76 conserve. Verifier boot, TINY/RETROSYN et autres machines, sample Wizard, beat repeat et lecture habituelle.

Le 16/10/2026 AveyCole rapporte que le filtre se quantifie encore en forte activite : lecture chargee ordinaire confirmee, beat repeat probablement aussi. La confirmation de note 102 couvrait le symptome simple piste 6 ; elle ne suffit pas pour ce nouveau cas. Aucun DSP filtre modifie dans ce candidat. Investigation suivante, sans pretendre ce defaut resolu.

## 4. Promotion demandee — 16/10/2026

AveyCole demande de publier la possibilite de retirer Banque MIDI et de marquer cette banque experimentale. Principal 1.77, memes octets de packing que le candidat ; aucune affirmation de test materiel supplementaire inventee. AveyCole precise ensuite que la distorsion reste legerement audible en forte charge sans Banque aussi. Le statut MIDI est donc experimental pendant l enquete, sans attribuer exclusivement le probleme a sa presence. `tools/gen_no_midi_capacity_main.py --check` verifie les fichiers promus.
