# 210 — Parite stock, masques et confirmation MACHINES

Demande AveyCole le31/10/2026 : conserver les sons/PUNCH natifs, reduire les chemins supplementaires inactifs, corriger Wizard en USB multipiste et confirmer MACHINES avec DATA. Isolation casque annulee explicitement. Adresses : VA OS1.13.

## Resultat experimental

Candidat Full2.65 cumulatif depuis Full2.64 SHA8d9d7df60e212c1c8e1848c0e3b2d015c8e9a2d91269efde5177431d4554e72f. Pas de promotion main et pas de test appareil annonce. Les coupures physiques des patterns A01/A11 restent a verifier sur la machine ; aucune mesure CPU materielle deduite des instructions emulees.

## Parite PUNCH

[FAIT] voice-punch.c appliquait des transients supplementaires aux IDs0..5, notamment un octave pluck a TONE. Ces IDs deleguent maintenant le PUNCH natif sans modification du frame. pp_custom_mask derive les six bits des seuls moteurs ajoutes/PUNCH actif ; le frame est restaure apres delegation. ACID conserve deja son PUNCH natif. test_feature_activity_masks.py couvre50 couples machine/PUNCH, bornes du masque et restauration. test_stock_machine_parity.py execute40 blocs reels48kHz des six machines avec PUNCH ON : PCM exact et cretes non nulles. Ce test synthetique ne remplace pas les vrais projets usine.

## Activite

li_active_tracks[3] decrit les destinations des banques LFO2..4 ; aucune phase native active n est sautee.384 comparaisons1..4LFO verifient frames, phases, etats et EMAC contre909e6a0. Les FX par piste conservent lt_active/lt_sent et leurs queues existantes. dsp.c remplace le pseudo hook fourni (adresse0804A12C hors carte ColdFire) par un masque auxiliaire derive des gains presents et cibles ; source compilee, pas encore reincorporee dans le module FX historique du candidat2.65. Ne pas annoncer que tous les frais DSP ont disparu.

## Wizard USB

[FAIT] voice_quiet401adb4c considere les gains main/sends dans vq_nop, meme si le flux USB6 lit le bus premix. La garde a401adbf6 saute ce test seulement si le paquet USB differe du mode stereo38h ; l enveloppe, les vrais mutes et le silence propre restent verifies. Le remplacement est installe apres les copies natives, a la continuation4000053a avant activation des caches ; ses8octets natifs sont rejoues puis reprise40000542. test_wizard_usb_activity.py execute boot, installation et garde native : main/sends nuls n arretent plus le calcul USB6. Ecoute/Outbox8 physique en attente.

## Choix MACHINES

Global conserve son MenuView natif. Mac est insere sous Pad : Sil differe le changement, Stk conserve le chemin immediat. Sil est le defaut. Preference8octets versionnee/validee dans /MachineBrowse.cfg, E/S UI seulement et transport arrete. DATA commit, BACK annule ; les releases sont absorbees sans latcher de modificateur. Le vrai DrumSelect/setMachine/snapshot est reutilise ; rm_step retourne le candidat seulement pendant ce commit. Un changement de piste invalide le choix precedent.

Preuves : test_machine_confirm.py (controle/persistence), test_machine_confirm_native.py (vrai commit, son exact pendant parcours), render_machine_confirm.py (polices et Bitmap natifs, rendu inspecte). Candidat distinct dans D:/Supermodel-workspace/CREATURE-source/activity-masks-test/browse/full. Le prototype ne promet pas encore ces modifications dans Lite/Optional.

## Memoire et distribution

Module4691a000..4691f000 ; BSS4691f000..46920000, apres lt_bss_end46919048 et avant la limite historique du module FX. Generateur refuse toute collision et garde les images2.64 epinglees. SysEx2.65 produit sur D:, non versionne/non publie. Les autres modifications preexistantes dans tweaks.js/licences restent hors de ce travail.

## Correction ecran MACHINES

AveyCole demande explicitement de conserver la presentation stock en modeSil. Le panneau textuel et le popup de parcours ont ete retires. mb_display_hook a400a25e0 substitue seulement l ID visuel dans d3, puis rejoue le moveq/lea natif et reprend400a25e8. Aucune ecriture dans les sons. Le dessinateur DrumSelect complet conserve noms, images et reperes. test_machine_confirm_native.py compare toutes les commandes graphiques du choix pending avec le meme choix natif engage, puis verifie le vrai commit DATA. Candidat corrige dans activity-masks-test/stock-screen/full ; meme version experimentale2.65, pas de publication.
