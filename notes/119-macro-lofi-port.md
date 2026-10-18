# 119 — Port test du controle lo-fi MACRO

AveyCole demande le 17/10/2026 la correction de reduction de frequence MACRO de 18nelli18, dans une copie test seulement. Source : https://github.com/18nelli18/Modded-Cycles/commit/cd905ac18b37d6012de85313673c70d36bd1603d et complement affichage https://github.com/18nelli18/Modded-Cycles/commit/62fb099ccefa0c2522fa31812a42811bd51c7fb3, presents dans d89267a. MIT ; credit conserve dans le code. Adresses : VA OS1.13.

## Reponse courte

FUNC + PITCH sur MACRO doit regler FINE (descripteur43) : centre64 OFF, a gauche reduction de frequence46K..4K, a droite profondeur12B..2B. Le calcul audio existant dans macro.cc reste intact. Le port reprend exactement les routines amont de pas, formatage et dessin ; notre choix dynamique de machines necessite un index MACRO configurable.

## 1. Contrat du detour

[FAIT] L'appel en 0x4001e8da appartient au lookup OS0x4001e814. A son entree : d2=potard, d5=FUNC, 36(sp)=machine ; retour vers0x4001e8e2. Le wrapper conserve le detour precedent pour tous les autres gestes en remettant son adresse sur la pile puis rts. Pour MACRO+FUNC+PITCH seulement, il installe les callbacks FINE amont, d2=43, retire son adresse retour et reprend en0x4001e910 : le descripteur est deja choisi, aucun argument record n'a ete pousse. Les registres sauvegardes et le retour de la fonction OS restent geres par le natif.

Les fonctions amont lofi_step, lofi_fmt et lofi_draw sont conservees ; la derniere remplace la jauge FINE par le texte en grandes lettres. Ce fork peut deja retourner FINE dans certaines recettes, mais toutes les variantes ne disposent pas de l'ensemble routage/pas/affichage corrige.

## 2. Placement et composition

Le helper relogeable de436 octets est ajoute a la fin de la derniere charge utile physique, apres son code et BSS. Les relogements sont verifies dans le generateur ; pas de nouvel espace sprite pris. Le dernier chargeur brut met a jour sa taille ; un bloc aplib est recompresse. Le hook utilise les octets effectivement composes comme garde et les references ecritures/payload sont regenerees. Sans MACRO, aucune modification n'est produite.

`tools/gen_macro_lofi_test.py --check` reconstruit la copie separee `docs/flasher-macro-lofi-test`. Elle conserve les reparations de combinaisons test3 et les diagnostics facultatifs CPU/CUT. Le principal1.85 et la909 ne changent pas.

## 3. Validation

`node tools/test_macro_lofi_flasher.js` construit les images signees avant/apres pour MACRO seule, avec ChordKeys/Wizard facultatifs, selection883 et banques completes1023, MIDI et repeat independants, dont le diagnostic. `python3 tools/emu/test_macro_lofi_port.py --watch` execute leurs vrais bootstraps, puis les vrais chemins lookup, edition FUNC, formatage et popup OS. La preuve compare tous les potards et les etats FUNC sur toutes les machines, 81 editions, 128 textes, huit fenetres pixel par pixel au chemin texte natif, les autres objets UI et la conservation du helper apres cache disque.

[À FAIRE] Validation materielle utilisateur ; statut experimental. Aucune promotion principale autorisee pour ce changement.

[FAIT en emulation] Les huit profils passent : 16 images signees avant/apres, vrais bootstraps, tous les potards de chaque machine avec/sans FUNC, 648 editions, 1 024 textes et 64 fenetres comparees au chemin texte natif ; autres objets UI et code apres cache conserves. Le generateur passe `--check`. Sans modification des corps audio.
