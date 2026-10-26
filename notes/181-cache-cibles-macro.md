# 181 — Cache des cibles Harmonics MACRO

Demande AveyCole25/10/2026 : conserver146, poursuivre les optimisations en test apres publication du correctifDUB. Generateur --macro-cache, macro_cache149_assets.py ; preuves test_macro_cache149.py et test_macro_models149.py. Adresses : VA OS1.13.

## Reponse courte

[FAIT en emulation] Test149 sur base148, sans147. Harmonics24 conserve chaque sample dans4scenarios six-voix et tous les47modeles MACRO passent les changements live/FINE/retrigger/gate/release. Gain instructions4,26–5,76% pour sixHarmonics,1,30% dans un banc mixte avec unHarmonics. Le banc mixte sansHarmonics reste identique, y compris compte instructions. Aucun gain CPU physique annonce. Ce cache ne concerne pas KIK/GNG/ZAP.

## 1. Calcul conserve

Braids MIT, revision08460a69a7e1f7a81c5a2abcc7189c9a6b7208d4 ; digital_oscillator.cc SHA256 canonique2b46fd3d702c4570af7fadc6e187a931d0f40d69532c3bf0a46ef4d1454bad84. RenderHarmonics recalcule douze cibles avec divisions entieres meme sans changement. Six entrees clefs proprietaire, phase_increment et parametres0/1 conservent uniquement ces cibles. Amplitudes courantes, phases, interpolation, synchro et samples evoluent chaque appel, exactement comme avant. Aucune taille de classe modifiee. Changement de voix/mode/reset couvert ; une cible identique reste mathematiquement valide.

## 2. Reservation et integrite

Prologue8octets a0x467449be verifie avant JMP+NOP. Code0x468a8000, cache408octets0x468ad000, fin avant artPUNCH0x468ae000 ; apres HALL0x468a6b2a. Blancs verifies par le generateur ; aucun acces a l'anneauGATED0x468c0000. Boot zero fourni par le payload existant. Flag exclusif de --bank-chunks pour tests isoles. PUNCH, Sidechain, HALL, gouverneur et objets existants byte-identiques148. Sections horsMAIN, dont bootloader/updater, exactes.

## 3. Validation et appareil

Standard/adulte reproductibles --check, meme module cache. Tous47modeles, quatre bancs sixHarmonics et banc mixte Speech/troisPUNCH/KICK/HALL/PingPong/Sidechain passes, PCM exact. [A FAIRE appareil] Comparer A/P/O/N avec148, meme pattern et memes modeles ; premier pic ne prouve pas un gain soutenu. Ne pas publier avant retour.146 reste disponible ; guide public inchange.
