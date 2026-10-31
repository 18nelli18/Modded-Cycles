# 211 — Comparaisons DSP EMAC et reseaux de reverbe

Demande AveyCole31/10/2026 : integrer son dsp.c puis optimiser les combs/allpass, verifier jump tables, fade invariant, SRAM, alignementUSB et hooks. Priorite : sons stock inchanges. Prototypes Full2.65 prives, aucune promotion main ni mesure de cycles materiels.

## Deux fichiers exactement compares

Activity Masks stock-screen SHA011b1ab5905e51ef77086515bfecc1bba2936c6092a8a54d4ab43218c0f13911 contre EMAC_DSP_Comparison (SHA dans BUILD.json). Le premier candidat conserve tous les chemins/reset/etats FX historiques ; il importe seulement les helpers arithmetiques. Aucun remplacement par le prototype tronque. Aucun processeur retire n est reactive.

measure_emac_wrapper_cost.py :8blocs aleatoires par mode/phase, noyaux interceptes identiquement. Exemples steady : ROOM1286,875 vers3010 ; HALL1285,5 vers3013 ; PS11285,5 vers3010 instructions. Le fader EMAC conserve ACC3 et MACSR par produit, ce qui coute beaucoup. La saturation branchless n est pas gratuitement plus rapide.

measure_full_reverb_cost.py execute les vrais noyaux :320blocs de preparation puis8appels par mesure. Le callback sidechain inchange est intercepte. ROOM3792,625 vers5596,75 (+47,57%), HALL6449,875 vers8272,5 (+28,26%), PS19066,375 vers10877 (+19,97%). Pendant changement : ROOM4754,125 vers8489,125 ; HALL7468,375 vers11163,75 ; PS110038,625 vers13758,875. Ces pourcentages concernent les instructions de cet appel, pas le CPU total. PCM exact. Le baseline Activity Masks reste preferable selon cette preuve.

## Candidat reseaux distinct

--emac-dsp --reverb-network-opt ajoute un second module468a8000..468ae000 apres le HALL historique, region vide verifiee sur le baseline. Les etats et buffers restent aux adresses originales, aucun BSS/audio RAM supplementaire. Copie finale a la continuation native avant activation des caches ; le test recharge aussi la fin d image apres40200000, absente du petit snapshot boot historique.

Le dernier candidat garde la saturation C et le gain entier historiques, avec phase incrementale pour le fade. Son switch est compile en sauts indexes reels (objdump). A l instruction pres, ce wrapper gagne seulement1instruction steady et0pendant le fade : le compilateur optimisait deja largement ces operations. Ne pas annoncer un gainCPU massif.

Combs : ringsROOM1024, HALL/PS12048 deja masques ; stride2056 PS1 conserve son padding anti-conflit cache, sans changer le ring2048. Allpass : stockage circulaireROOM128echantillons par canal (taps67/79), HALL256 par diffuseur (taps149/166/211/234), PS1512 par diffuseur (taps277/308/397/444). Les reserves physiques existantes sont reutilisees :0octet audio ajoute. L adresse lue est write-minus-delay masque ; les longueurs audibles restent exactes.

Feedback/amortissementROOM/HALL/PS1froid : produits entiers EMAC, meme shift/division signes et reste fractionnaire HALL. Sauvegarde48bitsACC3/ACCExt23/MACSR une fois par bloc ; movclr remet ACC3 a zero entre produits. PS1chaud possedait deja des combsEMAC ; son allpass est masque et deroule deux iterations. Les C kernels utilisent -O3 -funroll-loops et des scalaires register la ou utiles.

test_reverb_network.py :4x320vrais blocsROOM/HALL/PS1/Gated, demarrage, wraps, passage froid/chaud, taille127, tonalite, queues/resetGated ; PCM et EMAC exacts. Instructions d un appel en fin de scenario : ROOM2803 vers2925, HALL5185 vers5965, PS17798 vers7896 ; Gated1143/1143 a la fin de sa queue. Le resultat sonore est conserve, mais aucune acceleration materielle prouvee. Ne pas presenter ce candidat comme un correctif de dropouts garanti.

test_emac_dsp_integration.py :612blocs du wrapper, dispatch/parametres, PCM, transitions, sidechain et tous les accumulateurs identiques. Les noyaux sont interceptes dans ce test seulement ; le test reseau les execute vraiment. Navigation native/DATA, WizardUSB et40blocs des sixmachines stock avecPUNCH sont reverifies.

## Audit des autres propositions

- Le MAIN en40000400 est enDDR selon notes03, pas du code execute directement enFlash. test_sram_code.py concerne deja les moteursSyntakt recopies dans la SRAM liberee par deplacement de tablesCHORD ; ne pas confondreCHORD natif et ChordKeys retire. Aucune reserveSRAM libre globale et aucun gain massif n ont ete prouves ; pas de nouvelle relocalisation speculative.
- USB6 : base80009800 et stride168 sont divisibles par4 ; chaque slot reste aligne. Reception80009de8 alignee aussi. Les descriptors sont a80008000 avec stride64. Pas de nouveau padding ni de changementDMA requis.
- trigless_dim.S utilise deja des masques/etats caches et une liste de mots en assembleur.333Hz de modulation ne signifie pas un timer panneau simple a333Hz. Le PIT multiplexe aussi les boutons et les strobesGPIO. Aucun nouveauDMA/panneau introduit sans mesure.
- Les nouveaux controles sont regroupes dans4691a000..4691f000 et les nouveaux noyaux dans468a8000..468ae000. Cela ne prouve pas une baisse des missesI-cache ; aucun changement arbitraire des autres trampolines.
- ChordKeys reste retire du Full. Le code MIDI actuel midi-no-chordkeys.c et les choix de machines existants sont preserves.
