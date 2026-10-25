# 175 — Marge audio MACRO et HALL

Demande AveyCole, chat Codex25/10/2026 : apres144, maximum rapporte P100 O2 N5,
et demande explicite de ne pas oublier MACRO, lourd sur plusieurs modeles.
Recette privee `--audio-headroom` v145, `audio_headroom145_assets.py`,
`hall_hot145.py`, `tools/machines/macro/parallel145.S`.
Preuves natives : `tools/emu/test_headroom145.py`, scripts de noyaux et audit
copies dans la livraison. Adresses : VA de l'OS1.13.

## Reponse courte

[FAIT en emulation] Le filtre MACRO garde ses23coefficients et son rendu96kHz,
mais utilise les chargements paralleles EMAC :977 vers646instructions sur le
banc noyau. Les modeles LITE qui contournent ce filtre n'en ont pas besoin.
HALL garde ses formules et tout son etat, compile avec GCC13.1.0 -O3 et
-funroll-loops dans un emplacement reserve : environ20 % d'instructions
economisees sur le banc HALL. Pas de baisse de qualite ni de nouveaux seuils.
Le banc mixte economise environ3 % d'instructions de plus que144, pas de CPU%
physique revendique. Verification appareil145 encore attendue.

## 1. MACRO

[FAIT] Le noyau162octets est a0x4674260c, derive de macro_render+0xea depuis
la table de dispatch, et garde le hash des octets precedents. Les lectures des
echantillons sont combinees avec les produits16bits, sans masquage d'adresse.
A0 avance toujours de128octets, A1 de128, MACSR est restaure, MASK et ACC1..3
restent intacts et ACC0 termine vide. Pas de nouvel etat ni d'allocation.

[FAIT en emulation] Cent vecteurs, extremes signes compris :3200echantillons
de sortie identiques. Image livree :47modeles avec controles live, FINE rate/bits,
retrigger, Gate/release, MACSR/MASK compares a144. Braids et ses rythmes restent
inchangés. Licence MIT Emilie Gillet conservee dans les sources existantes.

## 2. HALL et placement

[FAIT] HALL original finit a0x46832f78, juste avant Sidechain0x46833000.
Son expansion est placee dans le trou libre PUNCH0x468a6000..0x468ae000.
Le constructeur exige que punch_code_end soit avant0x468a6000, que le nouvel
end soit avant l'art0x468ae000 et que tous les octets remplaces soient nuls.
La taille actuelle est2858octets. BSS PUNCH0x468af000 inchange.

[FAIT] Le nouveau C utilise les adresses de l'etat HALL existant, lues par nm
dans le module FX : hall_w/fill/pos/apfill/decay/tone/low/previous/error,
ps_comb et ps_ap. L'ancien reset reste utilise. Un JMP remplace uniquement
l'entree fx_hall ; taille du prologue decodee par Capstone, instructions entieres.
Le nouveau corps conserve son propre contrat C. Aucun nouvel etat ni buffer.

[FAIT en emulation]320blocs bruit/silence, Size0/64/127/100 et Tone variable :
PCM et toutes les queues/variables identiques au HALL144, y compris via le vrai
detour de l'image145. Test prolonge au-dela du remplissage des combs/allpass.

## 3. Composition et limites

[FAIT en emulation] Vrai mixeur, SPEAK/KIK/GNG/ZAP/ACID/Kick, Sidechain, HALL
et delay natif ; sept substitutions MACRO : audio exact, cout reduit et pic
d'initialisation reduit sur le banc. Reglages representatifs, pas une copie du
projet utilisateur. Instructions interpretees seulement ; caches et cycles
physiques peuvent changer le gain observe sur appareil.

[FAIT] Audit de l'image : seul le noyau MACRO162octets change dans le runtime ;
dans le tail, seuls l'entree HALL et son emplacement reserve changent. PUNCH,
autres effets, SPEAK, MIDI, QntM et regulateur identiques. Popups, retention MIDI
et QntM passent. Deux variantes standard/adult reproductibles avec --check,
reextraction verifiee, bootloader et updater conserves. Aucun principal publie.

[A FAIRE] Meme pattern/tempo/intervalle de diagnostic sur appareil, avec et
sans MACRO, y compris les retriggers. P sous100 et O/N a0 restent a confirmer.

## 4. Retour appareil et promotion2.46 — 25/10/2026

[FAIT sur appareil] AveyCole approuve145 : « push to main, consistently 75 99 00 during same pattern ». Resultat rapporte A75 P99 O0 N0 sur son pattern, sans generalisation a tous les projets. Principal2.46 sert le standard exact SHA `f7f9e92d902f92c6f56c5baa964216c14cb35175271db160d8d6557e0c52535d`. Il demande de conserver les guides puisque les commandes et le son ne changent pas. Les guides restent byte-identiques a2.45. Les recherches suivantes restent privees.
