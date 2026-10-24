# 156 — SPEAK et formats natifs Reverb

Demande AveyCole,23/10/2026 : une machine Speak and Spell a mots communs sur SHAPE, mots/hauteur et autres controles verrouillables, microphone/statistiques propres, avant MIDI Out. Puis gain un peu plus fort et diction plus claire. Adresses : VA OS1.13. Candidats prives partages seulement, aucun changement au principal.

## 1. Reponse courte

SPEAK ajoute l ID20 sans renumeroter les anciens. Banque128mots, pronunciations originales en phonemes, synthese originale fixe trois formants a8kHz avec interpolation48kHz. Pas de ROM, code ou samples TI. Pitch et duree des phonemes sont independants. COLOR Voice, SHAPE Word, SWEEP Speed, CONTOUR Articulation, Decay/Pitch/Fine/Punch/Gate/VCA natifs. Le choix Word est fige au trig ; les autres controles sont actualises par le chemin natif. Six etats prives separes. Mots et controles utilisent les descripteurs/slots natifs, donc les locks/CC/LFO, sans preference globale de mot.

## 2. Placement et interface

`--speak` implique v80 et le correctif format v81 ; produit v82. Sources `tools/machines/speak/speak.c`, `words.json`, tables generees par `speak_assets.py`. Code a0x46818000, artwork a0x46823000, BSS a0x46824000 ; fin avant0x46828000, sous le noyau PS1 chaud0x46830000 et apres BSS FX0x46815c70. Espace deja reserve par la charge utile FX ; tous les octets remplaces sont verifies nuls. Premier placement de l artwork dans les metadonnees rejetee par la garde anti-chevauchement Feral : aucun SysEx v82 produit avant correction.

Tables de machines21et descripteurs146 ; SPEAK141..145 (Voice/Word/Speed/Artic/Decay). Les20anciens IDs restent, ordre0..16,TINY18,Shadow19,SPEAK20,MIDI17. Les21reperes restent sur deux lignes (11colonnes, pas5pixels). Carte native microphone original, CLASS VOICE / STYLE TALK / STR1 DEX5 MAG5. Popup Word avec nom et index0..127, dessin precedent conserve pour tous autres descripteurs.

## 3. Formats Reverb apres Chorus

[FAIT reproduit] v80 : apres selection Chorus puis Reverb en lecture, les callbacks numeriques du chorus restent actives jusqu au prochain service arrete. Tone affiche0..127, Size perd sa notation stock ; l utilisateur confirme que l affichage revient ensuite. Echec reproduit sur le vrai popup : Size natif1..INF, Tone natif-64..0..63, mais ancienne callback affiche des nombres bruts.

`--stock-fx-format-fix` produit v81. La callback chorus verifie le mode et delegue directement au formateur natif deja sauvegarde si le mode n est ni1 ni2. Identifie les deux objets internes (row+20), pas les bases des rows. Ce sont uniquement des formats UI ; aucune valeur, borne, feedback, buffer ni DSP Reverb ne change. Preuve `test_reverb_format.py` compare sept valeurs par controle sur Reverb/Vinyl/PS1 sans appeler le service, et garde le format numerique des chorus.

## 4. Preuves et retour appareil v82

[FAIT emulation]128mots audibles/non nuls, bornes et fin de mot ; notes extremes, Voice/Artic/Punch, retrigger deterministe, durees identiques a plusieurs hauteurs et differents timbres. Pitch n affecte pas la vitesse. Noyau mesure2331..2629instructions sur les quatre blocs observes, pas cycles materiels. Six slots audio natifs20actifs,220blocs,24changements de mot par evenements, autres controles changeants, memoires de piste distinctes, aucun acces non mappe.128popups Word noms/index exacts, carte/bornes/ABI21machines ; bootstrap2623158octets exacts, pas de source compressee ecrasee. Menus FX/migrations/overlays et gesteDX controles ; v80 se reconstruit exact.

v82 SHA256 `b54863e848e723c98c6d60751ccee590a59c7e10c80305879af08b2e9527f641`. [FAIT appareil rapporte] AveyCole : « it s really great but perhaps a little quiet ... a liiiiitle bit clearer ». Qualite initiale appreciee ; pas de resultat CPU materiel chiffre.

## 5. v83 : niveau et consonnes

`--speak-clear` implique v82. Gain de sortie8192->16384 (+6,0206dB). Legere accentuation fixe a8kHz, y=x+(x-xprecedent)/4, avant le clip et l interpolation ; gain DC1, gain Nyquist1,5. Un entier d etat en plus par piste, aucun changement de word/phone/duree/hauteur/formants. Mots, popup, carte et controle natif identiques ; v82 conserve et reproductible.

v83 SHA256 `2dc0730b471fa3d605b41937d49a9fec22062f0e61635103f540392eb0125a88`. [A FAIRE appareil] Comparer volume/diction sur meme pattern et niveau ; locks de phrase/hauteur, deux pistes independantes, filtres/sends, Reverb Tone signe et INF apres Chorus en lecture, A/P/O/N. Guide/checklist +128mots dans `output/firmware/validation/v83-speak-guide-and-checklist.md`. Ne pas annoncer un cout materiel ni absence d overloads a partir des instructions emulees.

Demande suivante explicite : seulement apres livraison du test SPEAK, considerer de futurs FX dont cout serait inferieur ou comparable au stock. Aucun autre FX ajoute a v82/v83.

[FAIT en emulation v83]128mots complets/non nuls et notes/timbres extremes verifies ; noyau2356..2659instructions sur quatre blocs (environ25..30instructions ajoutees a v82). Six pistes natives220blocs,24changements de mot, peaks23513557..104884906, sans clipping32bits ni acces non mappe.128popups et format Reverb exacts ; bootstrap natif et images v82/v83 figees. Ces lectures PCM ne sont pas une mesure des overruns materiels.


## 6. Pistes FX considerees apres livraison du test SPEAK

Le test v83 a ete livre dans le chat avant cette recherche, conformement a la demande. Deux pistes prioritaires, sans nouvel effet ajoute dans ce candidat :

- DUB : conserver le delay natif et ses banques/retours, chercher d abord une variante de ses coefficients de filtrage HP/LP existants plutot qu ajouter un second moteur. Si cela ne demande que changer des coefficients, c est le meilleur candidat a un cout voisin du stock. [HYP] Budget reel a prouver par desassemblage, instructions et comparaison appareil ; aucune egalite CPU promise.
- ROOM : petit reseau stereo a deux combs amortis et un allpass par canal, a debit reduit, en reutilisant les invariants/cache du PS1. Moins de lignes et taps que le reseau PS1 actuel ; [HYP] budget sous le stock et densite suffisante a verifier avant de l ajouter au menu. Conserver PS1 tel quel, pas de nouveau mode combine.

Base theorique primaire consultee : [Julius O. Smith, Lowpass-Feedback Comb Filter](https://ccrma.stanford.edu/~jos/pasp/Lowpass_Feedback_Comb_Filter.html), structure ligne de retard + filtre un pole en feedback. Aucun code recopie. Le choix DUB en premier vient de notre chemin natif existant, pas d une comparaison CPU publiee ailleurs. Plate/Spring/Reverse restent hors de ce test : aucune evaluation achevee, pas de promesse de cout.


## 7. v84 : consonnes moins rapeuses apres retour appareil

[FAIT appareil rapporte] Harsh crunch derriere certaines consonnes, exemple fin de « us ». L utilisateur precise que le probleme existait deja en v82 : sa demande de clarte concernait en fait la durete des consonnes. Les peaks des anciens rendus n indiquent pas un clip de sortie au reglage nominal ; ne pas attribuer le probleme uniquement au gain v83 ni aux overruns sans preuve.

`--speak-smooth` implique v83, produit v84. Bruit des fricatives reequilibre : premier formant reduit (poids0,12 pour S/Z ;0,2 pour autres consonnes bruitees) et souffle F2/F3 conserve. Excitation bruitee0,7 pour S/Z,0,8 ailleurs. Deux enveloppes d excitation voix/bruit a constante16samples8kHz (~2ms) suppriment les marches aux transitions et apres les bursts d occlusives. Accentuation differentielle v83 retiree ; gain de sortie16384 (+6,02dB vs82) conserve. Mots/phonemes/durees/notes, carte et parametres identiques.

[FAIT emulation] `test_speak_consonants.py` : US398blocs pour82/83/84, voyelle a environ1,993fois le RMS82 ; S(150..230ms) energie sous1600Hz reduite a20,6% du82 non compense,4,37% du83, souffle2200..3900Hz present. Ce sont des mesures de spectre, pas un verdict d intelligibilite ou d absence de harshness auditive. Preview local82/83/84 au gain compense. Tous128mots complets, notes/timbres extremes, durees independantes du pitch ;2356..2773instructions selon bloc observe (v84 blocs mesures2451/2773). Six voix natives220blocs avec24changements de mot, aucun acces non mappe ; popups128et ReverbINF/Tone signes exacts. Bootstrap2623158octets exact et source preservee ; v83 reconstruit identique.

v84 SHA256 `5968fe69f8a5b2af98f3c2f6ec7ba11910a83b2630172db9d0c47f70d046fa51`. Checklist `output/firmware/validation/v84-speak-guide-and-checklist.md`. [A FAIRE appareil] Comparer surtout US8, SHE5, THIS13, SIX101, STOP51, FUTURE127, Punch Off, memes niveaux/FX et A/P/O/N. Versions82/83 gardees, principal inchange.


## 8. v85 : niveau SPEAK et suppression SCRAMBLE propre

[FAIT appareil rapporte] v84 moins dur mais encore trop faible : utilisateur souhaite entendre clairement a Vol+Dist60, doit presque monter au maximum. Le petit gain v83 n avait pas calibre le moteur par rapport aux machines natives.

`--speak-level` implique v84 et produit v85. Sortie lineaire524288 au lieu de16384 (+30,10dB pour les petits signaux). Genou continu sur la grandeur a8kHz au-dessus de2048, `2048+e*2048/(e+2048)`, plafond strict4095, puis interpolation48k et conversionQ31. Produit maximal4095*524288 reste signe32bits ; Punch applique avant le genou. Aucun changement des phonemes, des enveloppes lissees v84, de la hauteur ou des durees. Pas de nouvelle accentuation du bruit. La division ne survient que sur fortes excursions, a8kHz ; blocs mesures2345..2682instructions, pas cout CPU physique.

[FAIT emulation] Rendu HELLO, pitch60/Voice64/Speed64/Artic80/Decay127, vrai VCA puis mixeur natif Vol+Dist60. Mesure apres le fondu initial du mixeur, voies voisines muettes : v84 peak0,002366FS / RMS0,000914FS ; v85 peak0,075702FS / RMS0,029234FS. Le controle Tone natif est profile dans la meme configuration. Ce niveau numerique ne remplace pas la validation du volume percu sur appareil.

128mots complets avec extremes de commandes, pitch/vitesse independants ; six voix natives220blocs et24changements de mot, peaks325168554..859971928, aucun acces non mappe. Native Reverb Tone/INF, menus et modificateurs conserves, bootstrap2623158octets exact sans ecrasement source ; v84 reconstruit identique.

Demande additive : supprimer un trig marque SCRAMBLE doit laisser une position fraiche quand il est recree. La base privee appelle encore directement le clear natif a0x40022dd0, qui conserve bit6. Le wrapper deja prouve de notes/76 est compile dans le module SCRAMBLE prive (code libre avant BSS467cf000), et ce CALL devient un CALL vers `sc_step_delete`, pas un JMP. Il conserve le retour natif, libere les33locks et remet le mot de flags a0, puis notifie par le setter natif. Aucun nouveau geste/global/rendu audio. Preuve `test_scramble_delete_private.py` reproduit l echec84 puis verifie six pistes, quatre pages et neuf positions (54suppressions/recreations), autres pas/pistes intacts et release hors REC sans effet. Menus/masques SCRAMBLE et180runs live/180evenements de locks restent exacts.

v85 SHA256 `96f97b9fb98056978b3b30c039e43db28183cc6324d076b50f84e3d790de194a`. [A FAIRE appareil] Commencer par Vol+Dist60, comparer niveaux de HELLO31/US8 et mots voisines ; verifier consonnes/Punch et DX sur meme pattern. Marquer un trig SCRAMBLE, le supprimer puis le recreer : aucune marque ni randomisation heritee. Principal inchange.

[FAIT emulation niveau85] Controle Tone meme Vol+Dist60 : peak0,079654FS / RMS0,057273FS. HELLO85 atteint peak0,075702FS / RMS0,029234FS (environ meme peak, parole naturellement moins soutenue que le ton continu). Ce banc compare numeriquement le rendu natif et ne simule pas l ecoute sur appareil. Image85 figee en validation.

## 9. Promotion principale 2.30 (23/10/2026)

[FAIT appareil rapporte] AveyCole : « that worked, push v85 with updated controls and such ». Image85 exacte approuvee, SHA256 `96f97b9fb98056978b3b30c039e43db28183cc6324d076b50f84e3d790de194a`, MAIN `7912d7c2912da1bd42ef47a607465f32267d34e0ea77dd53a951fb343247c938`. Publication via le seul chemin fixe existant, guides EN/FR et PDF actualises. Les comparaisons privees restent intactes. Ce retour n affirme pas une absence d overruns sur toute composition.
