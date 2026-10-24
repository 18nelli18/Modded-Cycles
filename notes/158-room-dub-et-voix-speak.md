# 158 — ROOM, DUB et voix SPEAK

Demande AveyCole : effets legers puis DUB plus distinct et voix plus claire, moins rapeuse, avec davantage de presence sans souffle. Adresses : VA OS1.13.

## 1. ROOM

Reseau original12kHz, deux combs amortis et un allpass par canal. Reutilise les buffers PS1 quand ROOM est actif ; init paresseuse, aucun long effacement audio. Memoire supplementaire de ring nulle. PCM1600blocs identique au v88 apprecie sur appareil, queues stereo bornees, reset silencieux ;2368..2804instructions observees selon etat, pas cycles materiels.

## 2. DUB

v88 utilisait seulement des coefficients natifs differents ; l utilisateur juge la difference trop discrete. v90 renforce le filtrage et reprend le rebond stereo natif. Lecture native des coefficients verifiee, ancien Delay/Ping Pong PCM exacts ; boucles feedback avec DMA modelisees. Instructions3359 DUB contre3352 Ping Pong et2786 Delay sur les blocs observes ; aucune inference de pourcentage de charge appareil. Ratio energie aigu/medium0,01574 contre0,11906 pour Delay, mouvements stereo alternes verifies.

## 3. SPEAK

Source glottale originale precalculee, RMS des resonateurs calibree par phoneme/banque hors ligne. Consonnes bruitees moins fortes, bursts plus doux et coarticulation ralentie. Apres preview89 juge meilleur, demande de plus d aigu sans hiss : preaccentuation de la source vocale et poids F2/F3 dans les tables, sans boucle DSP ajoutee ni amplification du souffle. Meme duree, pitch/vitesse independants. Test US89->90 : RMS voyelle0,11615->0,11554 ; souffle0,01743->0,01777 ; ratio aigu voyelle0,000183->0,001254. Pas un jugement perceptif ni une emulation de Microsoft Sam.

## 4. Publication

128mots reguliers et popups exacts, six pistes natives220blocs et24changements de mot ; bootstrap2623158octets exact sans ecrasement source. AveyCole approuve explicitement v90 pour principal2.32, SHA256 `218aebccdd0b5f13896f80310a041f8eb95c90e3a98ab62b1985c9083518d008`. Aucun lexique ni enregistrement utilisateur prive publie. Le futur DUCK reste un essai separe.
