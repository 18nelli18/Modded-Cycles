# 124 - MACRO : conversion96vers48kHz allegee

Demande AveyCole le18/10/2026 : certains reglages MACRO cliquent ou glitchent, filtre et repeat inactifs dans le premier rapport. Rapport suivant : sequence Kick/SDVtg/MACRO/ACID/Metal, glitch seulement avec pad de division repeat tenu, MACRO modele3 ; retirer une voix suffit a l'arreter. Ne pas confondre cout du rendu et clics inherents a une modulation/changement de modele. Aucun resultat hardware de correction invente.

## Reponse courte

[FAIT en emulation] Remplacer uniquement la boucle demi-bande de macro_render par une convolution entiere EMAC de meme taille162octets : 977 instructions contre1536 par bloc de conversion, sortie exactement identique. Les47 modeles restent disponibles, treize ont deja leur rendu allege sans cette conversion ; le test n'en retire aucun. Modele3 :16946vers16387 instructions en moyenne sur le scenario mesure (environ3,3% de la voix, pas36% de tout MACRO). Ce sont des instructions, pas des cycles ni une mesure CPU materielle. Le gain ne prouve pas encore la disparition des glitchs.

## 1. Boucle et contrat

Reference : tools/machines/macro/macro.cc (notes43/55), code propre deja compile dans25-macro.json. Rendu a+0x522 depuis sa base ; boucle a macro_render+0xea (0x4300060c..0x430006ae pour MACRO seule). Coefficients demi-bande inchanges : centre16384, paires10327/-3131/1579/-820/434/-197. Le C fait six produits32bits de sommes17bits ; le candidat accumule treize produits16bits signes, sans arrondi intermediaire. La somme bornee reste dans int32. ACC0 entier, vide apres chaque sortie ; MACSR restaure avant l'enveloppe/VCA/PUNCH. Cadre et epilogue originaux conservent les registres appelant. Les accumulateurs1..3 ne changent pas. Sortie et etat EMAC final sont compares sur le vrai pipeline complet, pas seulement la formule.

Code propre : tools/machines/macro/halfband_fast.s ; generateur tools/gen_macro_halfband_fast.py ; reference originale garde162octets depuis la recette MACRO, donnees generees localement build/macro-optimization. Aucun octet Elektron ou firmware publie. Sources Braids/stmlib telechargees aux commits deja epingles, non modifiees et conservees en build ignore.

## 2. Integration test

tools/gen_macro_render_test.py copie la release1.92 epinglee. Une fonction de build remplace exactement une occurrence du noyau original dans un seul payload lorsque MACRO est coche. References anciennes verifiees ; nouvelle reference du payload recalculee. Taille, adresses runtime, allocations et autres octets conserves. L'integration se fait dans la couche Swarm avant MIDI/repeat ; la correction ChordKeys de note123 recalcule la source depuis la nouvelle taille compressee. Les references originales sont restaurees avant une nouvelle resolution. Sans MACRO : retour identique, fichier signe compare. Aucune modification du principal ou909.

Diagnostic CPU/moyenne/pic/CUT facultatif conserve dans le test ; exige Beat Repeat et un moteur SY pour leurs compteurs. Pas de lecture CPU fabriquee pour une selection sans ces compteurs. Le test conserve aussi le correctif lo-fi MACRO1.86 et les voix/modeles existants.

## 3. Preuves

tools/emu/test_macro_halfband_fast.py :100 vecteurs86int16 dont zeros, extremes et aleatoires ;3200 sorties Q31 exactement identiques, MACSR et accumulateurs inutilises preserves. Puis les47 modeles,16blocs chacun avec retrigger et changement de timbre/couleur/enveloppe : audio natif et etat EMAC final identiques, aucun cout en instructions augmente. Trente-quatre modeles gagnent559instructions par bloc ; les treize chemins allegees restent identiques au point de mesure. Le gain ne s'extrapole pas aux cycles/caches du materiel.

tools/test_macro_render_flasher.js : sept profils signes avant/apres (Select All, complet sans MIDI, Wizard, MACRO+latching minimal, partiel ACID/WAVE/SY/Chord, sansMACRO et diagnostic). Exactement un noyau nouveau si MACRO installe ; aucun sinon. SansMACRO, composition/references et fichier signe complet identiques.

Tentative de banc mixte avec vrais boots et Kick/SDVtg/MACRO3/ACID/Metal, filtre neutre : audio avant/apres identique et cout plus bas dans le premier mode, mais Metal reste muet dans ce banc meme avant optimisation. La garde cinq voix audibles echoue ; cette tentative ne constitue PAS une preuve du rapport cinq voix et son script de recherche n'est pas publie. Le scenario reel est reserve au test hardware. Peripheriques et timing physique simules ; ne pas extrapoler un pourcentage CPU ou une correction de clicks.

## A verifier sur appareil

Le modele3 et la sequence rapportee, aux memes divisions de repeat ; CPU moyenne/pic/CUT apres relachement du combo et ecoute. Tester egalement plusieurs modeles96kHz, modeles deja alleges et lo-fi. Main reste1.92 tant que cette nouvelle optimisation n'est pas confirmee.

[FAIT en emulation] tools/emu/test_macro_render_boot.py passe sur Select All, partiel, minimal et diagnostic : vrai bootstrap, memes tailles/adresses runtime, tous les autres octets RAM des payloads identiques apres remplacement inverse du seul noyau162octets.
