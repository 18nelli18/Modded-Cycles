# 149 — Valeurs machines et commandes Wizard separees

Demande AveyCole, conversation du 22/10/2026 : Contour retourne au defaut lors du changement de machine ; garder les six commandes et proteger Slice. Adresses : VA OS1.13. Generateurs prives `tools/keep_params_assets.py`, `tools/wizard_isolation_assets.py`, option `--wizard-isolation` du reconstructeur prive.

## Reponse courte

[FAIT en emulation] v48 conserve Pitch,Decay,Color,Shape,Sweep,Contour dans les bornes du moteur cible. Wizard dispose de quatre valeurs distinctes des synths pendant la session MACHINES. Aucun ajout dans le rendu audio. La duree de vie stock du menu a ete acceptee explicitement ; pas de promesse de banques de presets apres fermeture.

## 1. Parcours et memoire

- `0x4001477e` setMachine ecrit ID puis appelle `0x40014072` : detour du seul appel `0x400147fc`, pas du reset explicite.
- Banque locale sur pile pour six valeurs, appel natif, relecture du son COW puis restauration bornee via descripteurs natifs. MIDI17 conserve son parcours.
- `0x400a242a` capture native du menu : initialise six banques UI identifiees par objet piste, sans toucher les donnees sauvegardees.
- `0x400a2712` parcours molette : wrapper de huit octets entiers, trampoline vers `0x400a271a`, contexte actif seulement pendant l'appel. Hors menu, la banque n'est jamais consultee.
- Code `0x467ee100` jusqu'avant `0x467eed00`, BSS `0x467eed00` jusqu'avant `0x467ef000`, dans la reserve TINY deja nulle. Six banques Wizard/synth, 148octets, aucune allocation audio. Les preuves de zero/cave bornent code et BSS.
- Ancien controle de tag Wizard signale seulement l'ancien format negatif : le helper conserve les mots d'options valides tags7/F au changement. Aucun changement au format sauvegarde.
- A la sortie Wizard, restaurer les quatre valeurs synth precedentes. A son retour, restaurer ses quatre valeurs sauvegardees ; au premier passage, utiliser ses defauts natifs. Toute modification active est capturee au depart suivant. Reouvrir le menu reinitialise les banques depuis les sons actuels.

## 2. Diagnostic et preuves

[FAIT] Le prototype v47 passait les retours simples mais n'isolait pas les deux familles de valeurs. AveyCole rapporte les valeurs Wizard heritees par les autres machines, avec leurs labels normaux. v48 remplace cette approche par les deux banques UI. Les captures natives Wizard reviennent au chemin natif excluant Wizard ; sa banque dediee effectue la restauration.

- `test_keep_machine_params.py` : 361paires et 19resets explicites par variante ; 42retours Wizard (7modes x6pistes), contexte ControlAll avec6objets distincts.
- `test_wizard_isolation.py` : sixpistes, passages repetes Wizard/synth, editions de chaque famille, contexte actif relache, ancienne banque ignoree hors menu, nouveau menu remplace les valeurs.
- `test_scramble_mask.py` : navigation/sauvegarde puis 162cas live et162cas locks natifs par variante. Labels SCRM/Cnt raccourcis dans les pixels natifs.
- Bootstrap, sections de recuperation intactes et reconstruction `--check`. Les mesures ne constituent pas un pourcentage CPU physique.

## 3. Test materiel et publication

AveyCole teste `validation/all-features-polivoks-cpu-trim-test-v48.syx`, puis rapporte « this worked, push to main ». Promotion exacte vers2.21, SHA256 `ec6717091c7e016ead30d5d5b3e1be7a0d72c936b5c833913594830373fd92d6`. La variante sans filtre partage reste privee, avec filtre interne Wizard, sans resultat materiel revendique. Credits et historique conserves ; image main delivree par le chemin fixe existant.
