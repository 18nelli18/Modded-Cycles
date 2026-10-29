window.MC_RELEASES=[
{
  "version": "2.58",
  "date": "2026-10-29",
  "changes": [
    {
      "en": "New sounds reliably start with LOW filtering even when track setup finishes late. Saved filter choices remain preserved.",
      "fr": "Les nouveaux sons demarrent avec le filtre LOW meme si la preparation des pistes se termine plus tard. Les choix de filtre sauvegardes sont conserves."
    },
    {
      "en": "Double STOP now clears reverb and delay tails, including PS1. The first STOP keeps tails. ACID no longer receives the added Punch transient; its native Punch behavior remains.",
      "fr": "Un double STOP coupe les queues de reverb et de delay, PS1 compris. Le premier STOP les conserve. ACID ne recoit plus le transitoire Punch ajoute ; son comportement Punch natif reste present."
    },
    {
      "en": "Full, Lite and Machine Optional startup screens and flashers display 2.58. Optional retains Legacy, ChordKeys and Vinyl. Checked in emulation; hardware confirmation is pending.",
      "fr": "Les ecrans de demarrage et flasheurs Full, Lite et Machine Optional affichent 2.58. Optional conserve Legacy, ChordKeys et Vinyl. Verification en emulation ; confirmation materielle en attente."
    }
  ]
},
  {
    "version": "2.57",
    "date": "2026-10-29",
    "changes": [
      {
        "en": "Release 2.57: startup screens and flasher versions now match. Full retains the inactive track-FX bypass and the corrected effect selector in every menu view. Lite keeps its existing audio behavior with an updated startup number.",
        "fr": "Version 2.57 : les ecrans de demarrage et les flasheurs affichent le meme numero. Full conserve le bypass des effets par piste inactifs et le selecteur corrige dans chaque vue. Lite conserve son comportement audio avec un numero de demarrage actualise."
      },
      {
        "en": "Machine Optional gains per-track FX, pattern/project FX persistence, the later LFO/filter and audio-path fixes, and the inactive-FX optimization while retaining its extra machine choices, Legacy, ChordKeys and Vinyl. Validation is by emulation; hardware timing and every mixed selection are not verified.",
        "fr": "Machine Optional ajoute les effets par piste, leur memorisation par pattern/projet, les corrections LFO/filtre et audio recentes et le bypass des effets inactifs, tout en conservant ses choix supplementaires, Legacy, ChordKeys et Vinyl. Validation en emulation ; le timing materiel et tous les choix mixtes ne sont pas verifies."
      }
    ]
  },
  {
    "version": "2.56",
    "date": "2026-10-28",
    "changes": [
      {
        "en": "Full fixes the remaining retired-effect entry in the stacked FX menu and skips unnecessary processing when no track effect is active. Menu and startup checks pass in emulation; physical-device testing remains pending.",
        "fr": "Full corrige l’entrée d’effet retiré encore visible dans le menu FX superposé et évite les calculs inutiles lorsqu’aucun effet par piste n’est actif. Les contrôles des menus et du démarrage passent en émulation ; les essais sur machine restent à effectuer."
      },
      {
        "en": "Full and Lite add distinct Punch attacks, per-track FX and LFO/filter performance improvements. Full offers 23 sound machines plus MIDI Out; Lite keeps the six stock machines.",
        "fr": "Full et Lite ajoutent des attaques Punch propres à chaque machine, des effets par piste et des optimisations LFO/filtre. Full propose 23 machines sonores plus MIDI Out ; Lite conserve les six machines d’origine."
      },
      {
        "en": "Emulator checks cover default Punch audio, unchanged Punch-off audio, LFO/filter state, USB duplex, startup and recovery. The reported held-step Punch/Gate lock issue remains unreproduced; rhythmic Chord/filter clicking still needs device confirmation. No new hardware verification is claimed.",
        "fr": "Les contrôles en émulation couvrent les sons Punch par défaut, le son inchangé avec Punch désactivé, les LFO/filtres, l’USB duplex, le démarrage et la récupération. Le problème de locks Punch/Gate sur pas maintenus reste non reproduit ; les clics rythmiques Chord/filtre demandent une confirmation sur machine. Aucun nouveau test matériel n’est annoncé."
      },
      {
        "en": "Choose Supermodel Full or Supermodel Lite in the main flasher. Full now serves the approved v215 with complete LFO pattern storage, playable LFO menus, TINY sustain/PUNCH and clipboard fixes. Lite now serves the approved v216, adding the LFO pattern storage, playable LFO menus and clipboard fixes to its six stock machines.",
        "fr": "Choisissez Supermodel Full ou Supermodel Lite dans le flasheur principal. Full sert le v215 approuvé : réglages LFO par pattern, commandes musicales dans les menus LFO, sustain/PUNCH TINY et correction du presse-papiers. Lite sert maintenant le v216 approuvé : réglages LFO par pattern, commandes musicales dans les menus LFO et correction du presse-papiers, avec ses six machines d’origine."
      },
      {
        "en": "Lite includes Kick, Snare, Metal, Perc, Tone and Chord with all shared Supermodel quality-of-life features, including Sequence Genie, Scramble, four LFOs, filters, FX, sidechain and PTN/TRK Page Len/Warp. No Syntakt OS file is needed for Lite.",
        "fr": "Lite inclut Kick, Snare, Metal, Perc, Tone et Chord avec toutes les fonctions communes Supermodel : Sequence Genie, Scramble, quatre LFO, filtres, effets, sidechain et Page Len/Warp en PTN/TRK. Aucun fichier OS Syntakt requis pour Lite."
      },
      {
        "en": "New and cleared audio sounds start with a fully open LOW filter and zero resonance. Existing loaded sounds keep their settings. Native Undo restores the previous filter type and cutoff. Both startup screens display release 2.56.",
        "fr": "Les sons audio neufs et effacés commencent avec un filtre LOW ouvert et une résonance nulle. Les sons chargés conservent leurs réglages. Undo natif restaure le type et la coupure précédents. Les deux écrans de démarrage affichent la version2.56."
      },
      {
        "en": "Lite defers added preference writes until controls have been idle for a second. Changes stay live in RAM and save afterward. Every delivered image has separate immutable URLs, checksum verification and native Model:Samples layout/capacity checks.",
        "fr": "Lite diffère les sauvegardes des préférences ajoutées après une seconde sans geste. Les changements restent actifs en RAM puis se sauvegardent. Chaque image dispose d’URL immuables, d’une vérification SHA et de contrôles natifs de layout/capacité Model:Samples."
      }
    ]
  },
  {
    "version": "2.55",
    "date": "2026-10-27",
    "changes": [
      {
        "en": "Page Setup adds Warp Off/On. With Warp On, a shortened page fills the duration of a normal16-step page at the selected pattern scale. The timer fix keeps Warp working across repeated playback.",
        "fr": "Page Setup ajoute Warp Off/On. Avec Warp On, une page raccourcie occupe la duree d une page normale de16pas a l echelle du pattern. Le correctif du timer conserve Warp pendant la lecture repetee."
      },
      {
        "en": "Steps beyond Page Len stay fully dark in GRID RECORD and ignore trig gestures. Their saved notes and locks are preserved and return when Page Len increases.",
        "fr": "Les pas au-dela de Page Len restent eteints en GRID RECORD et ignorent les gestes sur leurs trigs. Notes et locks sauvegardes sont conserves et redeviennent accessibles si Page Len augmente."
      },
      {
        "en": "Publishes the exact v199 tested and approved by AveyCole. All prior machines and features remain. TINY sustain/PUNCH work is not included.",
        "fr": "Publication du v199 exact teste et approuve par AveyCole. Machines et fonctions precedentes conservees. Le travail sustain/PUNCH de TINY n est pas inclus."
      }
    ]
  },
  {
    "version": "2.54",
    "date": "2026-10-27",
    "changes": [
      {
        "en": "Page Setup adds Page Len (1–16, default16). Every full page plays that many steps without waiting through unused pads. While Page Len is selected, active trigs stay lit and inactive trigs stay fully dark. Saved with the pattern; hidden trigs and locks are preserved.",
        "fr": "Page Setup ajoute Page Len (1–16,16 par defaut). Chaque page complete joue ce nombre de pas sans attendre les pads inutilises. Sur Page Len, les trigs actifs restent allumes et les autres restent eteints. Sauvegarde dans le pattern ; trigs et locks masques conserves."
      },
      {
        "en": "Estus SETTINGS controls support native step locks and live recording: COLOR waveform, SHAPE ratio, SWEEP drive, CONTOUR transient. All25 machine choices remain, including SPEAK and Feral.",
        "fr": "Les commandes SETTINGS d Estus acceptent les locks natifs et le live recording : COLOR forme d onde, SHAPE ratio, SWEEP drive, CONTOUR transient. Les25 choix de machines restent disponibles, dont SPEAK et Feral."
      },
      {
        "en": "Model:Samples preparation keeps the safe bootstrap-layout and flash-capacity checks. Both Samples options are checked against this exact release image.",
        "fr": "La preparation Model:Samples conserve les controles du chargement bootstrap et de capacite flash. Les deux options Samples sont verifiees avec cette image exacte."
      }
    ]
  },
  {
    "version": "2.53",
    "date": "2026-10-27",
    "changes": [
      {
        "en": "Clearing a track sound or full pattern now resets all four audio LFOs. LFO1 destination labels follow the selected destination, including on ESTUS.",
        "fr": "Effacer un son de piste ou un pattern complet remet les quatre LFO audio a zero. Le nom de destination du LFO1 suit la selection, y compris sur ESTUS."
      },
      {
        "en": "ESTUS SETTINGS + knob controls now work while the sequencer runs. Main serves the exact user-confirmed v189 firmware.",
        "fr": "Les commandes SETTINGS + potentiometre d ESTUS fonctionnent pendant la lecture. Le principal sert exactement le firmware v189 confirme par l utilisateur."
      }
    ]
  },
  {
    "version": "2.52",
    "date": "2026-10-26",
    "changes": [
      {
        "en": "Estus Refilled.",
        "fr": "Estus Refilled."
      }
    ]
  },
  {
    "version": "2.51",
    "date": "2026-10-26",
    "changes": [
      {
        "en": "Choose 1, 2, 3 or 4 audio LFOs in Mod Setup > Global > LFOs (default 2). Repeated LFO presses cycle through enabled pages. LFOs 3/4 match LFO 2 controls and save separately per project, pattern and track; their settings are outside ordinary Elektron sound exports and native parameter locks.",
        "fr": "Choisissez 1, 2, 3 ou 4 LFO audio dans Mod Setup > Global > LFOs (2 par defaut). Les appuis LFO parcourent les pages actives. Les LFO 3/4 reprennent les commandes du LFO 2 et se sauvegardent separement par projet, pattern et piste ; hors exports de sons Elektron et parameter locks natifs."
      },
      {
        "en": "Scale Lock adds Off, ORGN (original scale-degree mapping) and BRDS (nearest in-scale note), with 19 whole-semitone scales. Open FUNC + PAGE and choose Lock, Scl and Key. One-shot and Hold remain available in the LFO Mode row. Uni square and signed depth are corrected. Polarity following native sound copies is still being worked on.",
        "fr": "Scale Lock propose Off, ORGN (degres successifs) et BRDS (note de gamme la plus proche), avec 19 gammes par demi-tons. FUNC + PAGE ouvre Lock, Scl et Key. One-shot et Hold restent accessibles dans Mode des LFO. Carre Uni et sens de Depth corriges. La conservation de polarite lors des copies de sons reste en cours."
      },
      {
        "en": "Fixes the GATED pre-delay overwrite triggered by FUNC + REVERB SIZE and separates WAVE file buffers from feature memory. Keeps compact LFO memory and deferred startup work. Main serves exactly the v175 approved by AveyCole as Supermodel_2.51.syx.",
        "fr": "Corrige l ecrasement memoire du pre-delay GATED declenche par FUNC + REVERB SIZE et separe les fichiers WAVE de la memoire des fonctions. Memoire LFO compacte et travail de demarrage differe conserves. Le principal sert exactement le v175 approuve par AveyCole : Supermodel_2.51.syx."
      }
    ]
  },
  {
    "version": "2.50",
    "date": "2026-10-26",
    "changes": [
      {
        "en": "The normal Resonance parameter popup now displays its full label using the smaller native font. Audio, filter modes, LFO polarity and saved settings are unchanged from main2.49.",
        "fr": "Le popup normal Resonance affiche son libelle entier avec la petite police native. Audio, types de filtre, polarite LFO et sauvegardes identiques au principal2.49."
      },
      {
        "en": "Main serves the exact approved standard v164 as Supermodel_2.50.syx. The separate popup overlap reported with Mod Setup open remains under investigation.",
        "fr": "Le principal sert le v164 standard exact approuve : Supermodel_2.50.syx. Le chevauchement de popup signale avec Mod Setup ouvert reste en cours d analyse."
      }
    ]
  },
  {
    "version": "2.49",
    "date": "2026-10-26",
    "changes": [
      {
        "en": "Four new filter modes and LFO Polarity options. Main now serves the exact approved v163 as Supermodel_2.49.syx.",
        "fr": "Quatre nouveaux modes de filtre et des options de polarité du LFO. Le principal sert le v163 exact approuvé : Supermodel_2.49.syx."
      },
      {
        "en": "Everything from 2.48 is retained. No hardware result is claimed for this release.",
        "fr": "Tout le contenu de 2.48 est conservé. Aucun résultat de test sur machine n'est annoncé pour cette version."
      }
    ]
  },
  {
    "version": "2.48",
    "date": "2026-10-25",
    "changes": [
      {
        "en": "Sample Wizard gets a sample title, wide waveform and track/duration footer with a segmented track-volume display. File browsing and sequencer note entry keep their controls. Parameter previews retain their text labels.",
        "fr": "Sample Wizard affiche titre, grande forme d onde, piste/duree et volume par rectangles. Navigateur et saisie des notes conservent leurs commandes. Les previews de parametres gardent leurs labels."
      },
      {
        "en": "Mod Setup opens to Global and Track. Global > Grv adds separate On/Off and Type controls, seven grooves using the Swing knob for strength, and bidirectional CHORD Strum. Off keeps stock Swing. Track > Human adjusts timing/velocity per track.",
        "fr": "Mod Setup ouvre Global et Track. Global > Grv propose On/Off et Type separes, sept grooves doses par Swing et CHORD Strum bidirectionnel. Off conserve Swing natif. Track > Human regle temps/velocite par piste."
      }
    ]
  },
  {
    "version": "2.47",
    "date": "2026-10-25",
    "changes": [
      {
        "en": "DUB delay now returns a centered source on both channels from its first echo, even with zero feedback. Stereo input and its existing filtering, Time, Feedback and Send controls are preserved.",
        "fr": "Le delay DUB restitue maintenant une source centree sur les deux canaux des le premier echo, meme sans feedback. Entree stereo, filtrage et commandes Time, Feedback et Send conserves."
      },
      {
        "en": "Based on v146; the v147 test optimizations are excluded. Ping Pong keeps its alternating routing. Main serves the exact approved standard v148 as Supermodel_2.47.syx.",
        "fr": "Base v146 ; les optimisations du test v147 sont exclues. Ping Pong conserve ses echos alternes. Le principal sert le v148 standard exact approuve : Supermodel_2.47.syx."
      }
    ]
  },
  {
    "version": "2.46",
    "date": "2026-10-25",
    "changes": [
      {
        "en": "More audio headroom for PUNCH, MACRO and HALL, with the same sound and controls. MACRO keeps its full output filter and HALL keeps its existing reverb quality.",
        "fr": "Plus de marge audio pour PUNCH, MACRO et HALL, avec les mêmes sons et commandes. MACRO conserve son filtre de sortie complet et HALL sa qualité de réverbération."
      },
      {
        "en": "AveyCole reports A75, P99, O0 and N0 consistently on the same tested pattern. Main serves the exact approved standard v145; download Supermodel_2.46.syx.",
        "fr": "AveyCole relève régulièrement A75, P99, O0 et N0 sur le même pattern testé. Le principal sert le v145 standard exact approuvé ; téléchargement Supermodel_2.46.syx."
      }
    ]
  },
  {
    "version": "2.45",
    "date": "2026-10-25",
    "changes": [
      {
        "en": "Quantized mute/solo: open Mod Setup (SETTINGS + TRACK), choose QntM, switch it on and select the time division your mutes and solos are quantized to. Off by default.",
        "fr": "Mute/solo quantifiés : ouvrez Mod Setup (SETTINGS + TRACK), choisissez QntM, activez-le et sélectionnez la division temporelle sur laquelle vos mutes et solos sont quantifiés. Désactivé par défaut."
      },
      {
        "en": "Main serves the exact standard v142 approved by AveyCole. Download: Supermodel_2.45.syx.",
        "fr": "Le principal sert le v142 standard exact approuvé par AveyCole. Téléchargement : Supermodel_2.45.syx."
      }
    ]
  },
  {
    "version": "2.44",
    "date": "2026-10-25",
    "changes": [
      {
        "en": "MIDI Out now preserves the audio settings when you scroll back to a synth. Unassigned MIDI controls stay OFF until you assign a CC.",
        "fr": "MIDI Out conserve les réglages audio lorsque vous revenez à un synthé. Les commandes MIDI non assignées restent sur OFF jusqu’à l’affectation d’un CC."
      },
      {
        "en": "Open Mod Setup from machine selection and adjust sound knobs without losing your menu position. Parameter popups stay visible for two seconds; BACK returns to machine selection.",
        "fr": "Ouvrez Mod Setup depuis la sélection des machines et réglez les commandes du son sans perdre votre position. Les fenêtres de paramètres restent visibles deux secondes ; BACK revient à la sélection des machines."
      },
      {
        "en": "PUNCH adds twelve FM percussion models, including kicks, toms, bongos and metallic sounds. On Shadow, engaging PUNCH adds distortion while retaining its punch transient.",
        "fr": "PUNCH ajoute douze modèles de percussions FM, dont kicks, toms, bongos et sons métalliques. Sur Shadow, activer PUNCH ajoute de la distorsion tout en conservant son transitoire."
      },
      {
        "en": "Main serves the exact standard v141 approved by AveyCole. Download: Supermodel_2.44.syx. PUNCH and TINY decay behavior is unchanged.",
        "fr": "Le principal sert le v141 standard exact approuvé par AveyCole. Téléchargement : Supermodel_2.44.syx. Le comportement Decay de PUNCH et TINY est inchangé."
      }
    ]
  },
  {
    "version": "2.43",
    "date": "2026-10-25",
    "changes": [
      {
        "en": "Sidechain now offers Rev. and Del. target checkboxes below the five other tracks in S.Chn. Choose either stereo effect return, both, or any mix of track and effect targets. All selected targets use the source’s Dpt, Atk, Hld and Rel controls and its Mute policy.",
        "fr": "Sidechain propose les cases Rev. et Del. sous les cinq autres pistes dans S.Chn. Choisissez un retour FX stéréo, les deux, ou un mélange de pistes et de retours. Les cibles partagent Dpt, Atk, Hld et Rel ainsi que le choix Mute de la source."
      },
      {
        "en": "Rev. and Del. choices save per source and pattern with Save Project. The wet returns duck while their internal tails continue. Main serves the exact regular v130 approved after AveyCole’s test; the adult build stays private. Download: Supermodel_2.43.syx.",
        "fr": "Les choix Rev. et Del. se sauvegardent par source et pattern avec Save Project. Les retours sont atténués tandis que les queues internes continuent. Le principal sert le v130 régulier exact approuvé après essai par AveyCole ; le build adulte reste privé. Téléchargement : Supermodel_2.43.syx."
      },
      {
        "en": "Earlier projects load with Rev. and Del. unchecked. For a downgrade to v129 or earlier, keep an older project copy: those versions cannot restore the added FX, Scramble and Sidechain settings of patterns saved with either new target selected. Patterns without either target keep the previous record format.",
        "fr": "Les anciens projets chargent Rev. et Del. décochés. Gardez une copie antérieure pour revenir au v129 ou avant : ces versions ne restaurent pas les réglages FX ajoutés, Scramble et Sidechain des patterns sauvegardés avec une nouvelle cible active. Sans ces cibles, le format précédent est conservé."
      }
    ]
  },
  {
    "version": "2.42",
    "date": "2026-10-24",
    "changes": [
      {
        "en": "MACHINES now closes Mod Setup and gives the dial to machine selection immediately. This also works from the Scramble and S.Chn submenus, including while editing a control. You no longer need BACK to make machine selection respond.",
        "fr": "MACHINES ferme désormais Mod Setup et rend immédiatement la molette au choix de machine. Cela fonctionne aussi depuis Scramble et S.Chn, même pendant l’édition d’un réglage. Plus besoin de BACK pour débloquer la sélection."
      },
      {
        "en": "Main serves the exact regular v129 approved by AveyCole, with all v128 features and saved settings retained. Download: Supermodel_2.42.syx. The adult build remains private.",
        "fr": "Le principal sert le v129 régulier exact approuvé par AveyCole, avec toutes les fonctions et sauvegardes du v128. Téléchargement : Supermodel_2.42.syx. Le build adulte reste privé."
      }
    ]
  },
  {
    "version": "2.41",
    "date": "2026-10-24",
    "changes": [
      {
        "en": "S.Chn now has a Mute On/Off choice for each source track. On makes Sidechain follow the source mute, including solo exclusion. Off keeps targets ducking while the source is muted, as before; Off is the default. Click DATA on Mute to toggle.",
        "fr": "S.Chn propose Mute On/Off pour chaque piste source. On fait suivre le mute de la source, y compris son exclusion par solo. Off conserve l’atténuation quand la source est muette ; Off est le défaut. Cliquez DATA sur Mute pour basculer."
      },
      {
        "en": "The Mute choice saves per source in each pattern with Save Project. Main serves the exact regular v128 approved by AveyCole. The adult build remains private. Firmware downloads are named Supermodel_2.41.syx.",
        "fr": "Le choix Mute se sauvegarde par source dans chaque pattern avec Save Project. Le principal sert le v128 régulier exact approuvé par AveyCole. Le build adulte reste privé. Téléchargement : Supermodel_2.41.syx."
      },
      {
        "en": "Older projects load with Mute Off. If you need to return to v127 or earlier, keep an earlier project copy: those versions cannot restore the added FX, Scramble and Sidechain settings of patterns saved with Mute On. Patterns whose Mute choices are all Off keep the older settings format.",
        "fr": "Les anciens projets démarrent avec Mute Off. Gardez une copie antérieure pour revenir au v127 ou avant : ces versions ne restaurent pas les réglages FX ajoutés, Scramble et Sidechain des patterns sauvegardés avec Mute On. Si tous les choix sont Off, l’ancien format est conservé."
      }
    ]
  },
  {
    "version": "2.40",
    "date": "2026-10-24",
    "changes": [
      {
        "en": "Tap SETTINGS + TRACK and release to open Mod Setup. Hold the combo to Scramble once; keeping it held does not repeat the randomization. With steps held, a quick tap still toggles only their Scramble marks.",
        "fr": "SETTINGS + TRACK bref ouvre Mod Setup au relâchement. Le maintien lance Scramble une seule fois, sans répétition. Avec des pas tenus, un appui bref bascule uniquement leurs marques Scramble."
      },
      {
        "en": "The Sidechain submenu is now S.Chn >. Targets use Trk. 1–6 and its controls read Dpt, Atk, Hld and Rel, aligned inside the selection highlight. Per-pattern saving remains unchanged.",
        "fr": "Le sous-menu Sidechain devient S.Chn >. Cibles Trk. 1–6 et commandes Dpt, Atk, Hld, Rel alignées dans la surbrillance. Sauvegarde par pattern conservée."
      },
      {
        "en": "Elder returns to its original volume; Shadow is raised 12 dB over its original level. Main serves the exact regular v127 approved by AveyCole. The adult vocabulary remains private.",
        "fr": "Elder retrouve son volume original ; Shadow gagne 12 dB par rapport à son niveau original. Le principal sert le v127 régulier exact approuvé par AveyCole. Le lexique adulte reste privé."
      }
    ]
  },
  {
    "version": "2.39",
    "date": "2026-10-24",
    "changes": [
      {
        "en": "Sidechain adds trigger-based rhythmic volume ducking: select a source track, then choose any of the other five tracks in Mod Setup > Sidechain. Depth, Attack, Hold and Release shape the response. Multiple sources can control different targets. This is separate from the DUCK delay effect.",
        "fr": "Sidechain ajoute une atténuation rythmique déclenchée par les notes : choisissez la source puis les pistes cibles parmi les cinq autres dans Mod Setup > Sidechain. Depth, Attack, Hold et Release règlent la réponse. Plusieurs sources peuvent avoir leurs propres cibles. Fonction distincte de l’effet delay DUCK."
      },
      {
        "en": "Sidechain routing/settings and each track’s Scramble checklist now save per pattern with the project. Blank patterns start with Sidechain off, Pitch/Decay unchecked and Color/Shape/Sweep/Contour checked. Queued pattern changes apply when the new pattern starts.",
        "fr": "Routage et réglages Sidechain et listes Scramble de chaque piste sauvegardés par pattern avec le projet. Pattern vierge : Sidechain désactivé, Pitch/Decay décochés et Color/Shape/Sweep/Contour cochés. Les changements en attente s’appliquent au démarrage du nouveau pattern."
      },
      {
        "en": "Main serves the exact regular v122 approved by AveyCole after testing. The compact menu uses a stacked Side / Chain title and readable values. Older v121 project FX load into this build; older firmware does not restore custom FX records saved by v122. Adult SPEAK remains private.",
        "fr": "Le principal sert le v122 régulier exact approuvé par AveyCole après essai. Menu compact avec titre Side / Chain et valeurs lisibles. Les FX des projets v121 sont acceptés ; les anciens firmwares ne restaurent pas les nouveaux records FX sauvegardés par v122. SPEAK adulte reste privé."
      }
    ]
  },
  {
    "version": "2.38",
    "date": "2026-10-24",
    "changes": [
      {
        "en": "Each pattern now remembers its selected Delay/Reverb types and the added effects’ settings, including extra sends. Blank patterns start with standard Delay and Reverb. Queued changes switch effects when the next pattern actually starts. Save the project to keep these settings after reloading.",
        "fr": "Chaque pattern garde ses types Delay/Reverb et les réglages des FX ajoutés, dont leurs envois. Les patterns vierges commencent avec Delay et Reverb standard. Les changements en attente appliquent les FX au démarrage du prochain pattern. Sauvegardez le projet pour les retrouver au chargement."
      },
      {
        "en": "WAVE output is 6 dB louder for both the included starter table and imported tables. The starter and folder BACK navigation remain available.",
        "fr": "WAVE gagne 6 dB avec la table initiale et les tables importées. La table initiale et le retour BACK dans les dossiers restent disponibles."
      }
    ]
  },
  {
    "version": "2.37",
    "date": "2026-10-24",
    "changes": [
      {
        "en": "WAVE starts ready to play with the original 16-frame AV-WAVE-Morph table. Custom imports take priority on their track. Starter state is initialized during boot and restored through the native engine entry when needed.",
        "fr": "WAVE joue immediatement avec la table originale AV-WAVE-Morph de16trames. Une table importee prend la priorite sur sa piste. Etat initial charge au demarrage et repli dans l entree native du moteur."
      },
      {
        "en": "In the WAVE browser, BACK goes up one folder and closes the selector only at /Wavetables. Holding or releasing BACK after moving up leaves the browser open. Custom WAVE file buffers are kept clear of the added FX runtime.",
        "fr": "Dans le navigateur WAVE, BACK remonte un dossier et ferme la selection seulement a /Wavetables. Maintien et relachement apres une remontee laissent la vue ouverte. Tampons des fichiers WAVE separes du runtime des FX ajoutes."
      },
      {
        "en": "Main serves the exact regular v115 approved by AveyCole after hardware testing. All v111 features remain, including Acid, fine SY BITS detune, louder Elder and RETROSYN before MIDI Out. Adult SPEAK remains private.",
        "fr": "Le principal sert le v115 regulier exact approuve par AveyCole apres essai appareil. Fonctions111 conservees : Acid,detune fin SY BITS,Elder plus fort et RETROSYN avant MIDI Out. SPEAK adulte reste prive."
      }
    ]
  },
  {
    "version": "2.36",
    "date": "2026-10-24",
    "changes": [
      {
        "en": "ACID Decay now controls the filter envelope only. Notes sustain for their gate length and use a short fixed release. Velocity 97-127 adds progressively stronger filter and level Accent while retaining native velocity response.",
        "fr": "DECAY ACID agit uniquement sur l enveloppe du filtre. Les notes tiennent pendant leur longueur et utilisent un relachement court fixe. Velocite97-127 : Accent progressif du filtre et du niveau, reponse native de velocite conservee."
      },
      {
        "en": "SY BITS: hold FUNC and turn COLOR for hundredth-semitone detuning. The compact signed two-decimal popup updates live, including +1.68 and +24.00 without clipping. Ordinary COLOR turns preserve the fraction; fine values use the native sound storage.",
        "fr": "SY BITS : FUNC + COLOR ajuste le detune par centiemes de demi-ton. Le popup compact signe a deux decimales se met a jour en direct, dont +1.68 et +24.00 sans rognage. COLOR ordinaire conserve la fraction ; valeurs fines dans le stockage natif du son."
      }
    ]
  },
  {
    "version": "2.35",
    "date": "2026-10-24",
    "changes": [
      {
        "en": "Main now serves the approved v105 Retro build: RETROSYN joins the machine list immediately before MIDI Out, with existing machine IDs preserved. Regular SPEAK vocabulary only.",
        "fr": "Le principal sert le v105 Retro approuve : RETROSYN rejoint la liste juste avant MIDI Out, sans changer les IDs existants. Vocabulaire SPEAK regulier uniquement."
      }
    ]
  },
  {
    "version": "2.34",
    "date": "2026-10-24",
    "changes": [
      {
        "en": "GATED reverb: REVERB SEND / SIZE, FUNC + SIZE or SETTINGS + SIZE for Gate Time and Pre-delay and Tone. Gate Time 0-127 runs from about 40 ms to 6.7 s after the input falls quiet; Pre-delay goes up to 568 ms. No added echoes. Try Gate Time 16-32 and Pre-delay 25-40 ms on a snare.",
        "fr": "Reverb GATED : REVERB SEND / SIZE, FUNC + SIZE ou SETTINGS + SIZE pour Gate Time, Pre-delay et Tone. Gate Time 0-127 va d'environ 40 ms a 6,7 s apres que l'entree devient silencieuse ; Pre-delay jusqu'a 568 ms. Pas d'echos ajoutes. Essayer Gate Time 16-32 et Pre-delay 25-40 ms sur une caisse claire."
      },
      {
        "en": "HALL reverb: a wide stereo tail with longer reflections than ROOM. Hall Send per track, Decay and Tone.",
        "fr": "Reverb HALL : queue stereo large aux reflexions plus longues que ROOM. Hall Send par piste, Decay et Tone."
      },
      {
        "en": "Main serves the exact v101 image supplied by AveyCole. Updated printable guide (PDF). No hardware result is recorded with this release.",
        "fr": "Le principal sert exactement l'image v101 fournie par AveyCole. Guide imprimable (PDF) actualise. Aucun resultat de test sur la machine n'est enregistre avec cette version."
      }
    ]
  },
  {
    "version": "2.33",
    "date": "2026-10-23",
    "changes": [
      {
        "en": "RING MOD joins the reverb FX menu above ROOM: REVERB SEND is Ring Send, SIZE is Frequency, FUNC + SIZE or SETTINGS + SIZE is Depth. Adds metallic sine modulation using a shared stereo return.",
        "fr": "RING MOD rejoint le menu FX reverb au-dessus de ROOM : REVERB SEND = Ring Send, SIZE = Frequency, FUNC + SIZE ou SETTINGS + SIZE = Depth. Modulation metallique sinusoidale sur retour stereo commun."
      },
      {
        "en": "PHASER joins the delay FX menu above DUCK: DELAY SEND is Phaser Send, TIME is Rate and FUNC + TIME is Depth. Hold FUNC first, then TRACK + TIME for Feedback, or use SETTINGS + TIME.",
        "fr": "PHASER rejoint le menu FX delay au-dessus de DUCK : DELAY SEND = Phaser Send, TIME = Rate, FUNC + TIME = Depth. Tenir FUNC puis TRACK + TIME pour Feedback, ou SETTINGS + TIME."
      },
      {
        "en": "DUCK makes native delay repeats recede while notes play and swell into the gaps. Native Time, Feedback and Send stay accessible. Hold FUNC first, then TRACK: TIME adjusts Amount, DELAY SEND adjusts Release. Try Amount 127 and Release 32-64; Amount 0 restores standard Delay.",
        "fr": "DUCK attenue les repetitions du delay natif pendant les notes et les fait remonter dans les espaces. Time, Feedback et Send natifs restent accessibles. Tenir FUNC puis TRACK : TIME = Amount, DELAY SEND = Release. Essayer Amount 127, Release 32-64 ; Amount 0 retrouve Delay standard."
      },
      {
        "en": "Main serves exact regular-word v94 approved by AveyCole after the live-trigger knob report. Includes FX encoder replay protection, fewer popup creations during rapid turns, idle settings writes and cheaper new FX processing. Updated EN/FR controls and printable guide; original ROOM, DUB and 128-word SPEAK retained.",
        "fr": "Le principal sert exactement v94 a mots reguliers approuve par AveyCole apres le signalement encodeur avec triggers live. Protection des replays encodeur FX, moins de creations de popups en rotation rapide, ecritures apres repos et calcul FX allege. Commandes EN/FR et guide imprimable actualises ; ROOM, DUB et SPEAK 128 mots conserves."
      }
    ]
  },
  {
    "version": "2.32",
    "date": "2026-10-23",
    "changes": [
      {
        "en": "ROOM adds a compact stereo reverb: TRACK + REVERB SIZE, left/up above PS1. REVERB SEND is Room Send; SIZE is Decay; FUNC + SIZE or SETTINGS + SIZE is Tone. Its sound is unchanged from the v88 test.",
        "fr": "ROOM ajoute une petite reverb stereo : TRACK + REVERB SIZE, gauche/haut au-dessus de PS1. REVERB SEND : Room Send ; SIZE : Decay ; FUNC + SIZE ou SETTINGS + SIZE : Tone. Son identique au test v88."
      },
      {
        "en": "DUB is now clearly distinct from standard Delay: stronger filtering and alternating stereo repeats. TRACK + DELAY TIME, left/up above Ping Pong. TIME, Feedback and per-track Delay Send retain their native controls. Standard Delay and Ping Pong audio remain unchanged.",
        "fr": "DUB se distingue du Delay standard : filtrage plus marque et repetitions stereo alternees. TRACK + DELAY TIME, gauche/haut au-dessus de Ping Pong. Time, Feedback et Delay Send par piste gardent les commandes natives. Audio Delay standard et Ping Pong conserve."
      },
      {
        "en": "SPEAK has a smoother voiced source, balanced phoneme levels and gentler consonant transitions. Brighter voiced harmonics add presence while the reduced S/F/SH hiss stays low. The regular 128-word bank, word locks and independent pitch/speed remain; low-speed idle repair retained.",
        "fr": "SPEAK : source vocale plus douce, niveaux des phonemes equilibres et transitions consonantiques adoucies. Harmoniques vocales plus claires, sans renforcer le souffle S/F/SH reduit. Banque reguliere de 128 mots, locks et hauteur/vitesse independantes conserves, ainsi que le correctif idle aux faibles vitesses."
      },
      {
        "en": "Main serves exact regular-word v90 approved by AveyCole. Updated EN/FR shortcuts and printable PDF. Native checks cover both word rendering and FX controls, ROOM output, stereo delay feedback, recovery and instruction counts; these counts are not hardware CPU percentages.",
        "fr": "Le principal sert exactement v90 a mots reguliers approuve par AveyCole. Raccourcis EN/FR et PDF actualises. Preuves natives : mots, commandes FX, audio ROOM, feedback delay stereo, recuperation et instructions ; ces comptes ne sont pas des pourcentages CPU appareil."
      }
    ]
  },
  {
    "version": "2.31",
    "date": "2026-10-23",
    "changes": [
      {
        "en": "SPEAK consonants are softer, including noisy S/F sounds and the K transition between syllables. Vowel loudness, word timing, pitch and the original 128-word bank remain.",
        "fr": "Consonnes SPEAK plus douces : bruits S/F et transition K entre syllabes. Niveau des voyelles, durees, hauteur et banque originale de 128 mots conserves."
      },
      {
        "en": "Fixed speech going silent at slow Speed settings, even with Decay 127. Quiet gaps inside an unfinished word no longer trigger idle suspension. Decay, note release and genuine load-related voice stealing remain active.",
        "fr": "Correction du silence aux vitesses lentes, meme a Decay 127. Les silences internes a un mot inacheve ne declenchent plus la suspension idle. Decay, fin de note et coupures liees a une vraie surcharge restent actifs."
      },
      {
        "en": "Main serves exact regular-word v87 approved by AveyCole. All v85 features remain; controls and printable guide updated. Native checks cover all 128 words, word popups, six speech tracks, low-speed playback and recovery.",
        "fr": "Le principal sert exactement v87 a mots reguliers approuve par AveyCole. Fonctions v85 conservees ; commandes et PDF actualises. Preuves natives : 128 mots, popups, six pistes vocales, lecture lente et recuperation."
      }
    ]
  },
  {
    "version": "2.30",
    "date": "2026-10-23",
    "changes": [
      {
        "en": "SPEAK: a new 128-word voice machine before MIDI Out, with a microphone icon. COLOR is Voice, SHAPE selects Word, SWEEP is Speed and CONTOUR is Articulation. Lock words and notes to form pitched sentences; pitch and speed are independent. Calibrated volume and softer consonants.",
        "fr": "SPEAK : nouvelle machine vocale de 128 mots avant MIDI Out, avec icone microphone. COLOR : Voice ; SHAPE : Word ; SWEEP : Speed ; CONTOUR : Articulation. Locks de mots et notes pour des phrases chantees ; hauteur et vitesse independantes. Niveau calibre et consonnes adoucies."
      },
      {
        "en": "DX shortcut: with DX On in Mod Setup, tap FUNC, press FUNC again within 350 ms, hold at least 0.5 seconds, then release. Other controls cancel. Replaces TRACK + RETRIG diagnostics. Deleting a SCRAMBLE trig clears its mark and locks. Reverb Size INF and signed Tone return immediately after Chorus.",
        "fr": "DX On dans Mod Setup : appui FUNC, second appui sous 350 ms, maintien au moins 0,5 seconde, puis relacher. Autres commandes annulent. Remplace le diagnostic TRACK + RETRIG. Supprimer un trig SCRAMBLE retire marque et locks. Reverb Size INF et Tone signe reviennent immediatement apres Chorus."
      },
      {
        "en": "Main serves the exact shared-filter v85 tested and approved by AveyCole. EN/FR controls, the complete SPEAK word index and printable PDF are updated. Native emulation checks all words, six speech tracks, output level, menus and SCRAMBLE deletion; hardware load still depends on the pattern.",
        "fr": "Le principal sert exactement v85 avec filtre partage, teste et approuve par AveyCole. Commandes EN/FR, lexique SPEAK complet et PDF actualises. Emulation native : tous les mots, six pistes vocales, niveau, menus et suppression SCRAMBLE ; charge appareil selon le pattern."
      }
    ]
  },
  {
    "version": "2.28",
    "date": "2026-10-23",
    "changes": [
      {
        "en": "The Decay checkbox in Mod Setup > SCRM now controls the actual Decay parameter. Short SETTINGS + TRACK randomizes Decay when checked; marked SCRAMBLE steps vary it on each pass. Punch stays unchanged unless you edit it yourself. Unticked parameters remain unchanged.",
        "fr": "La case Decay de Mod Setup > SCRM agit maintenant sur le vrai Decay. SETTINGS+TRACK bref tire Decay si coche ; les pas SCRAMBLE le font varier a chaque passage. Punch reste inchange hors edition volontaire. Les parametres decoches sont conserves."
      }
    ]
  },
  {
    "version": "2.27",
    "date": "2026-10-23",
    "changes": [
      {
        "en": "New delays: TRACK + DELAY TIME, turn left/up past CRUSH 1/2 for PING PONG, SHIMMER 1 and SHIMMER 2. Release TRACK to apply. Ping Pong alternates stereo echoes. Shimmer 1 shifts every echo up an octave; Shimmer 2 keeps the earlier mixed, diffuse sound. TIME adjusts time, FUNC + TIME or SETTINGS + TIME adjusts feedback, DELAY SEND sets the per-track amount.",
        "fr": "Nouveaux delays : TRACK+DELAY TIME gauche/haut apres CRUSH1/2 pour PING PONG,SHIMMER1,SHIMMER2. Relacher TRACK applique. Ping Pong alterne les echos stereo. Shimmer1 transpose chaque echo d une octave ; Shimmer2 garde le melange diffuse precedent. TIME : temps ; FUNC+TIME ou SETTINGS+TIME : feedback ; DELAY SEND : dosage par piste."
      },
      {
        "en": "Shimmer 1 has aligned transitions, extra filtering and headroom for cleaner full-octave repeats. Shimmer 2 preserves the earlier v62 clean-echo/diffuse-octave blend. Both use native Time, Feedback and per-track Delay Send, with the full Feedback control range. No combined variants.",
        "fr": "Shimmer1 : raccords alignes,filtrage et marge pour des repetitions octavees plus propres. Shimmer2 conserve le melange v62 d echo propre et octave diffusee. Time,Feedback et Delay Send natifs,plage de Feedback complete. Sans variantes combinees."
      }
    ]
  },
  {
    "version": "2.23",
    "date": "2026-10-22",
    "changes": [
      {
        "en": "In Both 1 and Both 2, DELAY SEND controls the normal per-track delay send. Hold FUNC and turn DELAY SEND to adjust a separate crusher amount for that track, from 0 to 127. Crusher send 0 gives clean delay. Both 1 leaves direct sound clean; Both 2 also blends the direct sound from clean to crushed, even with delay send at zero. The crushed portion feeds the native delay, so echoes inherit its grain.",
        "fr": "En Both1/Both2, DELAY SEND dose le delay natif par piste. Maintenez FUNC et tournez DELAY SEND pour regler un envoi crusher distinct de0a127 sur cette piste. Crusher0 donne un delay propre. Both1 garde le direct propre ; Both2 melange aussi le direct propre/ecrase, meme avec Delay Send a zero. La portion ecrasee alimente le delay natif : les echos en gardent le grain."
      },
      {
        "en": "Crusher sends start at zero when no preferences exist, save per track after playback stops and return after reboot. They have no p-lock or LFO destination. Native Delay Send keeps its locks and modulation; Delay, Crush 1 and Crush 2 keep their previous controls. Fixes the v52 FUNC + DELAY SEND exception by passing the correct selected-track object. AveyCole reported that v53 worked and approved this exact shared-filter file.",
        "fr": "Les envois crusher commencent a zero sans preferences, se sauvegardent par piste apres arret et reviennent au redemarrage. Pas de destination p-lock/LFO pour ces nouveaux envois. Delay Send natif conserve locks et modulation ; commandes Delay/Crush1/Crush2 inchangees. Corrige l’exception v52 de FUNC+DELAY SEND en fournissant le bon objet piste. AveyCole confirme v53 fonctionnel et approuve ce fichier exact avec filtre partage."
      },
      {
        "en": "The remaining machine letter icons are replaced: Swarm has bees, SY Toy a spinning top, Clap Vintage clapping hands, SD Vintage a snare drum, MACRO a DNA helix and SY Bits a binary chip. Includes Shadow after TINY before MIDI Out, all previous icons, Wizard control isolation and cumulative fixes.",
        "fr": "Les dernieres initiales des machines sont remplacees : abeilles pour Swarm,toupie pour SY Toy,mains pour Clap Vintage,caisse claire pour SD Vintage,ADN pour MACRO et puce binaire pour SY Bits. Shadow reste apres TINY et avant MIDI Out ; icones precedentes,isolation Wizard et correctifs cumules conserves."
      }
    ]
  },
  {
    "version": "2.22",
    "date": "2026-10-22",
    "changes": [
      {
        "en": "In MACHINES, Shadow appears after TINY and before MIDI Out, with existing machine IDs preserved. It is an original pulsar/noise synth inspired by Opal Dust by Fors, using three windowed oscillator trains. Color controls Grain, Shape Density, Sweep Spread and Contour Chaos; Punch adds a ratcheting attack. Pitch, Fine, Decay and Gate remain available.",
        "fr": "Dans MACHINES, Shadow apparait apres TINY et avant MIDI Out, sans changer les IDs existants. Synthese pulsar/bruit originale inspiree de Opal Dust de Fors, avec trois trains d’oscillateurs fenetres. Color : Grain ; Shape : Density ; Sweep : Spread ; Contour : Chaos. Punch ajoute une attaque repetee. Pitch,Fine,Decay et Gate restent disponibles."
      },
      {
        "en": "New machine icons: a figure with a looming shadow for Shadow, stacked waveforms for WAVE, a magnifying glass for TINY, a five-pin DIN cable for MIDI Out, a TB-303-style panel for ACID and a cheetah for Feral. Sample Wizard keeps its hat and the six stock machine cards remain unchanged.",
        "fr": "Nouvelles icones : personnage et ombre pour Shadow,ondes superposees pour WAVE,loupe pour TINY,cable DIN cinq broches pour MIDI Out,panneau inspire TB-303 pour ACID et guepard pour Feral. Chapeau Wizard et six cartes stock conserves."
      }
    ]
  },
  {
    "version": "2.21",
    "date": "2026-10-22",
    "changes": [
      {
        "en": "Machine browsing retains Pitch, Decay, Color, Shape, Sweep and Contour instead of loading new defaults. Values are limited to the destination engine’s range. MIDI Out keeps its existing transition behavior.",
        "fr": "La selection de machine conserve Pitch,Decay,Color,Shape,Sweep et Contour au lieu de charger les valeurs par defaut. Les valeurs respectent les limites du moteur choisi. Transitions MIDI Out conservees."
      },
      {
        "en": "Sample Wizard keeps its four dial values separate from the other engines while MACHINES stays open. Passing through Wizard preserves the synth values you had before entering it; returning to Wizard restores its own dial values, including Slice start/end and filter settings. Its saved modes and options are retained. Closing and reopening MACHINES starts a fresh stock-style snapshot; this is not a separate preset bank for every engine.",
        "fr": "Les quatre commandes Sample Wizard restent separees des autres moteurs tant que MACHINES reste ouvert. Traverser Wizard conserve les valeurs du synth precedent ; revenir a Wizard restaure ses propres valeurs, dont debut/fin Slice et filtre. Modes et options sauvegardes conserves. Fermer puis rouvrir MACHINES renouvelle le snapshot comme sur le stock ; pas de banque de presets par moteur."
      }
    ]
  },
  {
    "version": "2.20",
    "date": "2026-10-22",
    "changes": [
      {
        "en": "SCRAMBLE now has six checkboxes per track: Pitch, Decay, Color, Shape, Sweep and Contour. Hold SETTINGS + TRACK for Mod Setup, scroll to Scramble and press DATA. Turn DATA to select a parameter and press to toggle. BACK returns to Mod Setup; BACK again closes it. Pitch/Decay default Off; the original four default On. Quick SCRAMBLE and marked steps follow the same choices. Preferences persist per track across projects and power cycles; saving waits until playback stops.",
        "fr": "SCRAMBLE propose six cases par piste : Pitch,Decay,Color,Shape,Sweep,Contour. Maintenez SETTINGS + TRACK pour Mod Setup, choisissez Scramble et appuyez DATA. Tournez pour choisir, appuyez pour cocher. BACK revient a Mod Setup puis ferme. Pitch/Decay desactives par defaut, quatre commandes originales activees. Appui bref et pas marques suivent ces choix. Preferences de chaque piste conservees entre projets et apres extinction ; sauvegarde a l’arret."
      },
      {
        "en": "Feral’s Formula model starts with an active waveform instead of the click-only DC output at its default Color setting. Formula changes select a playable starting point; all sixteen formulas and ten Feral models remain. Feral is by Glycinate.",
        "fr": "Le modele Formula de Feral demarre avec une onde active au lieu du clic/DC au Color par defaut. Changer de formule choisit un depart jouable ; seize formules et dix modeles conserves. Feral est de Glycinate."
      },
      {
        "en": "TINY appears immediately before MIDI Out in machine browsing. Saved machine IDs stay unchanged, so existing sounds keep their engines. All prior CPU fixes, shared/Wizard Polivoks-style lowpass filters, Elder, chorus/crusher routes and retrig latch remain. Main serves the exact shared-filter v46 tested and approved by AveyCole.",
        "fr": "TINY apparait juste avant MIDI Out dans la selection. IDs sauvegardes inchanges : les sons gardent leurs moteurs. Correctifs CPU, passe-bas partages/Wizard inspires du Polivoks,Elder,routes chorus/crusher et verrou retrig conserves. Le principal sert exactement le v46 avec filtre partage teste et approuve par AveyCole."
      }
    ]
  },
  {
    "version": "2.19",
    "date": "2026-10-22",
    "changes": [
      {
        "en": "TINY returns as an additional engine with all 52 original models. Feral, Elder, MIDI Out and every other machine remain. Existing machine IDs and saved sounds keep their engines. TINY uses Color for Tone, Shape for Model, Sweep for Mod and Contour for Excite.",
        "fr": "TINY revient comme machine supplementaire avec ses52modeles originaux. Feral,Elder,MIDI Out et toutes les autres machines restent presents. Numeros internes et moteurs des sons sauvegardes conserves. Color regle Tone,Shape Model,Sweep Mod,Contour Excite."
      },
      {
        "en": "All v42 features remain: five crusher routes and low-bit repair, correct Tone name, chorus graphics, retrig mode latch with BACK exit and edit protection, shared and Wizard Polivoks-style lowpass filters, and cumulative CPU fixes.",
        "fr": "Fonctions v42 conservees : cinq routes crusher et correctif bits faibles,nom Tone correct,graphiques chorus,verrou retrig avec BACK et protection edition,passe-bas partages/Wizard inspires du Polivoks et correctifs CPU cumules."
      },
      {
        "en": "Main serves the approved all-features shared-filter v43. Native menu/descriptor checks cover all nineteen machines; TINY audio is compared with its original implementation. Updated guides retain the credits, including Feral by Glycinate.",
        "fr": "Le principal sert le v43 complet approuve avec filtre partage. Menus et descripteurs natifs verifies pour les19machines ; audio TINY compare a son implementation originale. Guides actualises,credits conserves dont Feral de Glycinate."
      }
    ]
  },
  {
    "version": "2.18",
    "date": "2026-10-22",
    "changes": [
      {
        "en": "Five effect positions: Delay, Crush 1 (clean direct + crushed send), Crush 2 (direct blends to fully crushed at maximum Delay Send), Both 1 (clean direct + crushed echoes), and Both 2 (crushed direct and echoes). Rate/Bits stay separate from native delay settings. Low bits 2–4 remain audible on quieter signals; silence stays silent. Both 2 uses more processing.",
        "fr": "Cinq positions : Delay, Crush1 (direct propre et envoi ecrase), Crush2 (direct entierement ecrase a Delay Send maximal), Both1 (direct propre et echos ecrases), Both2 (direct et echos ecrases). Rate/Bits restent distincts du delay natif. Bits2–4 audibles sur les signaux faibles ; silence conserve. Both2 coute plus de calcul."
      },
      {
        "en": "The Tone machine name stays correct while using chorus. Chorus Speed/Depth popups keep the native animated graphics. Effect-mode selectors require two encoder events per change for more room between modes.",
        "fr": "Le nom de la machine Tone reste correct avec le chorus. Popups Speed/Depth et graphiques natifs animes conserves. Deux evenements encodeur par changement espacent les modes d’effets."
      },
      {
        "en": "Hold TRACK and double-tap RETRIG to latch audio beat-repeat mode, then release both. Steps remain momentary: hold a step to repeat and release it to stop. BACK exits. Copy/paste/clear shortcuts are blocked in the latch; plain PLAY/STOP remain available. The original hold gesture still works. The latch is temporary.",
        "fr": "Maintenez TRACK et tapez deux fois RETRIG pour verrouiller le mode beat repeat, puis relachez les deux. Pas momentanes : maintenir pour repeter, relacher pour arreter. BACK quitte. Copier/coller/effacer bloques dans le verrou ; PLAY/STOP simples disponibles. Geste maintenu initial conserve. Verrou temporaire."
      }
    ]
  },
  {
    "version": "2.17",
    "date": "2026-10-22",
    "changes": [
      {
        "en": "Elder replaces ChpHzrd / Retrosyn with an original chip synth inspired by Junior by Fors. Color, Shape, Sweep and Contour control Wave, Warp, Noise and Motion. Existing Retrosyn sounds now play Elder and change timbre.",
        "fr": "Elder remplace ChpHzrd / Retrosyn par un synthé chip original inspiré de Junior de Fors. Color, Shape, Sweep et Contour règlent Wave, Warp, Noise et Motion. Les anciens sons Retrosyn jouent Elder et changent de timbre."
      },
      {
        "en": "Choose Reverb, Chorus I or Chorus II with TRACK + Reverb Size. Chorus uses Size for Speed, FUNC + Size for Depth and the track Reverb Send for amount. Includes the sustained-ring repair and native animated graphics with two-line labels.",
        "fr": "Choisissez Reverb, Chorus I ou Chorus II avec TRACK + Reverb Size. Size règle Speed, FUNC + Size règle Depth et Reverb Send dose par piste. Correctif du sifflement continu et graphiques natifs animés avec labels sur deux lignes inclus."
      },
      {
        "en": "Choose Delay, Crush or Both with TRACK + Delay Time. In Crush/Both, Time sets Rate and FUNC + Time sets Bits; Delay Send controls each track’s amount. Both crushes the echoes. Delay Time/Feedback stay separate: switch to Delay to adjust them, then return to Both. Modes and crusher settings save globally after stopping playback; Rate/Bits are not p-lock destinations.",
        "fr": "Choisissez Delay, Crush ou Both avec TRACK + Delay Time. En Crush/Both, Time règle Rate, FUNC + Time règle Bits et Delay Send dose par piste. Both écrase les échos. Time/Feedback restent distincts : revenez à Delay pour les régler, puis à Both. Modes et réglages crusher sauvegardés globalement après arrêt ; Rate/Bits sans destinations p-lock."
      }
    ]
  },
  {
    "version": "2.16",
    "date": "2026-10-22",
    "changes": [
      {
        "en": "Lighter Polivoks-style two-pole lowpass filters replace the shared per-track filter and Sample Wizard’s internal filter. Their slope and resonance character change; existing filter controls, modulation and bypass remain.",
        "fr": "Des passe-bas deux poles plus legers, inspires du Polivoks, remplacent le filtre par piste et celui de Sample Wizard. Pente et resonance changent ; commandes, modulation et bypass sont conserves."
      },
      {
        "en": "Overload detection now uses the real audio-block deadline. Recovery from interrupted voice-steal fades blends over 32 samples. DX remains saved and Off by default, with average/peak load, overloaded-block and new-cut readings. This does not guarantee that demanding patterns cannot overload.",
        "fr": "La detection des surcharges utilise la vraie echeance du bloc audio. La reprise apres un fondu de vol de voix interrompu est raccordee sur 32 samples. DX reste sauvegarde et desactive par defaut, avec moyenne/pic, blocs surcharges et nouvelles coupures. Les patterns exigeants peuvent encore surcharger."
      },
      {
        "en": "Feral by Glycinate replaces TINY with ten models (0–9), using Color, Model, Sweep and Contour plus Pitch, Decay, Punch, Gate and Fine. Existing TINY sounds now play Feral and will sound different. The release is the exact shared-filter v33 file; validation uses emulation and instruction counts, not a claimed device-wide CPU percentage.",
        "fr": "Feral de Glycinate remplace TINY par dix modeles (0–9), avec Color, Model, Sweep, Contour, Pitch, Decay, Punch, Gate et Fine. Les anciens sons TINY jouent desormais Feral et changent de son. Version identique au fichier v33 avec filtre partage ; validation par emulation et comptage d’instructions, sans pourcentage CPU global revendique."
      }
    ]
  },
  {
    "version": "1.99",
    "date": "2026-10-20",
    "changes": [
      {
        "en": "The fixed main firmware now starts USB audio in standard stereo (2ch). Switch to six-channel audio from Mod Setup on the device; the per-track filter remains included.",
        "fr": "Le firmware principal demarre maintenant l’audio USB en stereo standard (2ch). Choisissez six canaux dans Mod Setup sur l’appareil ; le filtre par piste reste inclus."
      }
    ]
  },
  {
    "version": "1.98",
    "date": "2026-10-19",
    "changes": [
      {
        "en": "The main firmware includes an on-device USB audio switch: start in six-channel mode, or choose two-channel from Pad Setup. Changing modes makes the computer re-detect the Model:Cycles. The per-track filter remains included.",
        "fr": "Le firmware principal inclut le choix audio USB sur la machine : démarrage en six canaux ou choix deux canaux dans Pad Setup. Le changement fait redétecter le Model:Cycles par l’ordinateur. Le filtre par piste reste inclus."
      }
    ]
  },
  {
    "version": "1.97",
    "date": "2026-10-18",
    "changes": [
      {
        "en": "Pad Setup: SETTINGS + TRACK, press DATA, choose Silent or Stock. Choice resets to Silent after reboot. Pad mode only is promoted; sample-lock filter experiment and diagnostics excluded.",
        "fr": "Pad Setup : SETTINGS + TRACK, presser DATA, choisir Silent ou Stock. Retour Silent apres redemarrage. Seul le mode pads est publie ; filtre experimental sample locks et diagnostics exclus."
      }
    ]
  },
  {
    "version": "1.96",
    "date": "2026-10-18",
    "changes": [
      {
        "en": "Hardware-verified MACRO fine tune on SETTINGS + PITCH, saved with the sound. Plain PITCH keeps stock behavior and FUNC + PITCH remains Lo-Fi. Diagnostics excluded from main.",
        "fr": "Accord fin MACRO verifie sur appareil : SETTINGS + PITCH, sauvegarde avec le son. PITCH seul conserve le comportement stock ; FUNC + PITCH reste Lo-Fi. Aucun diagnostic dans le principal."
      }
    ]
  },
  {
    "version": "1.95",
    "date": "2026-10-18",
    "changes": [
      {
        "en": "Track Setup follows the selected track while open: MIDI Out settings for MIDI tracks, stock setup for audio tracks. MACRO fine tune remains in test; no diagnostics in main.",
        "fr": "Track Setup suit la piste selectionnee : reglages MIDI Out pour les pistes MIDI, menu stock pour les pistes audio. Accord fin MACRO conserve en test ; aucun diagnostic dans le principal."
      }
    ]
  },
  {
    "version": "1.94",
    "date": "2026-10-18",
    "changes": [
      {
        "en": "Complete firmware with MIDI Out as an A-side machine, Supermodel startup and a single optional six-track USB audio setting. CC assignment does not transmit changes; leaving MIDI Out closes its notes.",
        "fr": "Firmware complet avec machine MIDI Out sur A, demarrage Supermodel et seul choix audio USB six pistes. Assignation CC sans transmission ; quitter MIDI Out ferme ses notes."
      }
    ]
  },
  {
    "version": "1.93",
    "date": "2026-10-18",
    "changes": [
      {
        "en": "Hardware-confirmed MACRO converter optimization reduces processing work while preserving all 47 models and identical audio samples in emulation. Existing lower-rate models are unchanged.",
        "fr": "Optimisation du convertisseur MACRO confirmee sur machine : calcul allege, 47 modeles conserves et samples identiques en emulation. Modeles deja alleges inchanges."
      },
      {
        "en": "Diagnostics remain test-only. Heavy arrangements can still produce clicks and governor voice cuts; this release does not change the governor or claim to resolve those reports.",
        "fr": "Diagnostics reserves aux tests. Les arrangements charges peuvent encore cliquer ou subir des extinctions par le regulateur ; cette version ne change pas le regulateur et ne pretend pas corriger ces rapports."
      }
    ]
  },
  {
    "version": "1.92",
    "date": "2026-10-18",
    "changes": [
      {
        "en": "Select All signed firmware remains byte-for-byte identical. Synthesis payload contents are unchanged; diagnostics remain test-only.",
        "fr": "Le fichier signe Select All reste identique octet pour octet. Contenu des voix conserve ; diagnostics reserves aux tests."
      }
    ]
  },
  {
    "version": "1.91",
    "date": "2026-10-18",
    "changes": [
      {
        "en": "Hardware-tested optional Silent track selection: plain T1-T6 pads select without sound; TRACK + pad selects and plays, including live recording. Preset-browser preview is preserved.",
        "fr": "Selection silencieuse facultative testee sur machine : pads T1-T6 seuls selectionnent sans son ; TRACK + pad selectionne et joue, y compris en live record. Apercu du navigateur conserve."
      },
      {
        "en": "Unchecked by default. Existing selections keep the same firmware behavior until you enable it. Diagnostics remain test-only.",
        "fr": "Non coche par defaut. Les selections existantes gardent leur comportement tant que ce module reste desactive. Diagnostics reserves aux tests."
      }
    ]
  },
  {
    "version": "1.90",
    "date": "2026-10-18",
    "changes": [
      {
        "en": "Hardware-tested Attack, Filter and Resonance LFO destinations and quick assignment. Hold LFO + MACHINES and turn DECAY / SWEEP / CONTOUR; further turns adjust depth. Both LFO menus stay open after assignment, without opening machine selection.",
        "fr": "Destinations LFO attaque, filtre et resonance et assignation rapide testees sur machine. Tenir LFO + MACHINES et tourner DECAY / SWEEP / CONTOUR ; continuer ajuste la profondeur. Les deux menus restent ouverts sans ouvrir le selecteur de machine."
      },
      {
        "en": "Sample Wizard uses its native Filter/Resonance destinations and keeps correct names during knob movement. Retrosyn controls now read Timbre, Oscillator, Pitch Sweep and Chord Arp. Diagnostics remain test-only.",
        "fr": "Sample Wizard utilise ses cibles natives filtre/resonance et garde les bons noms pendant la rotation. Retrosyn affiche Timbre, Oscillator, Pitch Sweep et Chord Arp. Diagnostics reserves aux tests."
      }
    ]
  },
  {
    "version": "1.89",
    "date": "2026-10-18",
    "changes": [
      {
        "en": "Hardware-tested shared A/B pattern length can now be edited from MIDI B-side through FUNC + PAGE. Press DATA to select Length before turning edits it. PAGE advances through 16/32/48/64 regardless of edit selection.",
        "fr": "Longueur commune A/B testee sur machine, editable depuis B par FUNC + PAGE. Appuyez sur DATA pour activer Len avant de tourner. PAGE passe par16/32/48/64 meme hors edition."
      },
      {
        "en": "Per-track mode retains independent MIDI lengths. Page LED behavior and page carryover are preserved. Diagnostics remain excluded from the main flasher.",
        "fr": "Mode par piste : longueurs MIDI independantes conservees. LEDs et reprise de page preservees. Aucun diagnostic dans le flasheur principal."
      }
    ]
  },
  {
    "version": "1.88",
    "date": "2026-10-17",
    "changes": [
      {
        "en": "Hardware-tested MIDI B-side page LEDs now follow stock record and non-record modes: available pages stay lit outside record mode, with the playing page blinking. Record-mode behavior is retained.",
        "fr": "LEDs des pages MIDI B testees sur machine : modes natifs avec et sans enregistrement. Hors enregistrement, pages disponibles allumees et page jouee clignotante. Comportement en enregistrement conserve."
      },
      {
        "en": "Entering MIDI B-side in normal pattern-length mode inherits A-side’s selected page. Per-track mode keeps independent page selection. Diagnostics remain test-only.",
        "fr": "En mode longueur normale, ouvrir B reprend la page selectionnee dans A. En mode par piste, selection de page independante. Diagnostics reserves aux tests."
      }
    ]
  },
  {
    "version": "1.87",
    "date": "2026-10-17",
    "changes": [
      {
        "en": "Approved MIDI B-side page behavior: selected edit page solid, playing page blinking with stock timing. When they coincide, that page blinks; stopped playback shows the selected page solid.",
        "fr": "Comportement des pages MIDI B valide : page editee fixe, page jouee clignotante au rythme natif. Si elles coincident, cette page clignote ; a l arret, page editee fixe."
      },
      {
        "en": "Normal pattern length follows A-side. Per-track length mode keeps independent MIDI lane lengths. Diagnostic tools remain exclusive to test pages.",
        "fr": "Longueur normale du pattern liee a A. Le mode par piste garde des longueurs MIDI independantes. Les diagnostics restent reserves aux pages de test."
      }
    ]
  },
  {
    "version": "1.86",
    "date": "2026-10-17",
    "changes": [
      {
        "en": "Includes 18nelli18’s MACRO lo-fi control fix, approved by AveyCole for main: hold FUNC and turn PITCH. Left reduces sample rate (46K–4K), right reduces bit depth (12B–2B), centre is OFF. The value popup shows the setting.",
        "fr": "Integre la correction lo-fi MACRO de 18nelli18, validee par AveyCole pour le principal : maintenir FUNC et tourner PITCH. A gauche frequence reduite (46K–4K), a droite profondeur reduite (12B–2B), centre OFF. Valeur affichee dans la fenetre."
      },
      {
        "en": "Works with selectable machine layouts; synthesis code is unchanged. Diagnostics remain exclusive to test pages.",
        "fr": "Compatible avec les machines au choix ; code de synthese conserve. Les diagnostics restent reserves aux pages de test."
      }
    ]
  },
  {
    "version": "1.85",
    "date": "2026-10-17",
    "changes": [
      {
        "en": "Promotes machine-combinations test 3: TINY and RETROSYN work with partial machine selections, with or without Sample Wizard. Fixes Select All MIDI startup and RETROSYN + WAVE without Wizard.",
        "fr": "Integre le test 3 des combinaisons : TINY et RETROSYN avec les selections partielles, avec ou sans Sample Wizard. Corrige le demarrage Select All MIDI et RETROSYN + WAVE sans Wizard."
      },
      {
        "en": "AveyCole approved test 3 for main. 8,192 composition checks and 76 signed startup/project/cache tests passed in emulation. Diagnostic tools remain test-only.",
        "fr": "AveyCole valide le test 3 pour le principal. 8 192 compositions et 76 tests signes de demarrage/projet/cache passent en emulation. Les diagnostics restent dans les tests."
      }
    ]
  },
  {
    "version": "1.84",
    "date": "2026-10-17",
    "changes": [
      {
        "en": "TINY and RETROSYN now work with any selection of the other added machines, with or without Sample Wizard. Fixes the undefined engine error when preparing partial machine sets. Only checked machines appear in MACHINES.",
        "fr": "TINY et RETROSYN se combinent librement avec les autres machines ajoutees, avec ou sans Sample Wizard. Corrige l’erreur engine lors de la preparation des sous-ensembles. Seules les machines cochees apparaissent dans MACHINES."
      },
      {
        "en": "AveyCole confirmed the reported machine combination on hardware. All 1,536 expanded selections passed menu checks in emulation, plus signed builds and six-track audio comparisons. Voice code is unchanged. Diagnostics remain excluded from main.",
        "fr": "AveyCole confirme la combinaison signalee sur machine. Les 1 536 selections etendues passent les menus en emulation, avec builds signes et comparaisons audio six pistes. Code des voix conserve. Aucun diagnostic dans le principal."
      }
    ]
  },
  {
    "version": "1.83",
    "date": "2026-10-17",
    "changes": [
      {
        "en": "Hardware confirmed: Octave 0 cycles only the held notes on both arpeggiators. Oct 1–3 add octave copies; existing saved settings keep their sound.",
        "fr": "Confirme sur machine : Octave 0 parcourt seulement les notes tenues sur les deux arpegiateurs. Oct 1–3 ajoutent des octaves ; sons sauvegardes conserves."
      },
      {
        "en": "MIDI Out Bank and audio beat repeat remain independently selectable. Diagnostics stay in test builds only. MIDI saving still loads on B-side entry with playback stopped.",
        "fr": "Banque MIDI et beat repeat audio restent selectionnables independamment. Diagnostics reserves aux tests. MIDI sauvegarde charge toujours a entree B, lecture arretee."
      }
    ]
  },
  {
    "version": "1.82",
    "date": "2026-10-17",
    "changes": [
      {
        "en": "Main flasher: hardware-tested quick save now closes the underlying mute view, so FUNCTION no longer remains lit in mute mode after leaving the save menu. Hold FUNCTION + SETTINGS as usual. Diagnostic tools remain test-only.",
        "fr": "Flasheur principal : sauvegarde rapide testee sur machine ferme la vue mute ; FUNCTION ne reste plus allume en mode mute apres sortie du menu sauvegarde. Maintenir FUNCTION + SETTINGS comme auparavant. Diagnostics reserves aux tests."
      }
    ]
  },
  {
    "version": "1.81",
    "date": "2026-10-17",
    "changes": [
      {
        "en": "Main flasher: restore stock permanent quick save by holding FUNCTION + SETTINGS when Sample Wizard is installed. Other SETTINGS shortcuts retain their behavior. Diagnostic tools remain test-only.",
        "fr": "Flasheur principal : restaure la sauvegarde rapide permanente stock en maintenant FUNCTION + SETTINGS avec Sample Wizard installe. Les autres raccourcis SETTINGS sont conserves. Diagnostics reserves aux tests."
      }
    ]
  },
  {
    "version": "1.80",
    "date": "2026-10-17",
    "changes": [
      {
        "en": "Main flasher: hardware-tested repair for distorted filtering on added machines after switching away from Sample Wizard. Removes an obsolete second filter pass and retains efficient processing. Diagnostic tools remain exclusive to test builds.",
        "fr": "Flasheur principal : correction testee sur machine du filtre distordu sur les machines ajoutees apres sortie de Sample Wizard. Supprime un ancien second passage filtre et conserve le traitement efficace. Les outils diagnostic restent reserves aux builds de test."
      }
    ]
  },
  {
    "version": "1.79",
    "date": "2026-10-16",
    "changes": [
      {
        "en": "Swarm LITE replaces the original seven-oscillator Swarm in the checklist with three oscillators: fundamental plus two detuned saws. Lower processing load; a leaner, potentially quieter sound. AveyCole reports significantly reduced load and clicks on hardware. Heavy arrangements may still click. Filter, beat repeat and governor behavior are unchanged.",
        "fr": "Swarm LITE remplace Swarm sept oscillateurs dans la selection par trois oscillateurs : fondamental et deux dents de scie desaccordees. Charge reduite ; son plus fin, parfois moins fort. AveyCole signale une nette reduction de charge et des clicks sur machine. Les arrangements lourds peuvent encore cliquer. Filtre, repeat et regulateur inchanges."
      }
    ]
  },
  {
    "version": "1.78",
    "date": "2026-10-16",
    "changes": [
      {
        "en": "Filter and beat-repeat load repairs are hardware tested by AveyCole, including the reported multiple-Syn-Swarm setup. Main now uses exactly the firmware code from filter-load test 4: reduced filter work, lighter history recording and lighter active repeat, preserving the existing sound calculations and controls. MIDI OUT Bank stays optional and experimental.",
        "fr": "Corrections de charge filtre et beat repeat testees sur machine par AveyCole, dont la configuration avec plusieurs SY SWARM signalee. Principal avec code firmware identique au test filtre 4 : filtre allege, capture historique et repetition active allegees, calculs sonores et commandes conserves. Banque MIDI OUT facultative et experimentale."
      }
    ]
  },
  {
    "version": "1.76",
    "date": "2026-10-16",
    "changes": [
      {
        "en": "Sequence Genie timing restoration is hardware tested by AveyCole. Both audio A-side and MIDI B-side show Queue with Loop/Page instead of Sound 0/1. Loop generates at the selected track loop; Page at the next 16-step page. Includes the confirmed track 6 filter repair.",
        "fr": "Timing Sequence Genie retabli et teste sur machine par AveyCole. A audio et B MIDI affichent Queue avec Loop/Page au lieu de Sound 0/1. Loop genere a la boucle de piste choisie ; Page a la prochaine page de 16 pas. Correction filtre piste 6 confirmee conservee."
      }
    ]
  },
  {
    "version": "1.75",
    "date": "2026-10-16",
    "changes": [
      {
        "en": "Per-track filter precision repair is hardware tested by AveyCole: lowering cutoff on track 6 no longer produces the reported bit-crushed sound. Same filter DSP as the verified precision test, with existing cutoff/resonance controls and exact fully-open, zero-resonance bypass.",
        "fr": "Correction de precision du filtre par piste testee sur machine par AveyCole : baisser la coupure piste 6 ne produit plus le son quantifie signale. Meme DSP que le test precision confirme, commandes coupure/resonance et bypass ouvert/resonance nulle conserves."
      }
    ]
  },
  {
    "version": "1.74",
    "date": "2026-10-16",
    "changes": [
      {
        "en": "Published at AveyCole’s request: beat repeat briefly displays the selected division. MIDI B mute LEDs follow stock during FUNC: unmuted pads stay steadily lit; muted pads stay dark except B-note pulses. No selected-track highlight during FUNC; release restores it. Exact feedback-test firmware.",
        "fr": "Publie a la demande AveyCole : popup bref de division beat repeat. LEDs mute B selon le natif pendant FUNC : pistes actives fixes, coupees sombres sauf pulses B. Aucun surlignage de selection pendant FUNC ; relachement le restaure. Noyau identique au test feedback."
      }
    ]
  },
  {
    "version": "1.73",
    "date": "2026-10-16",
    "changes": [
      {
        "en": "Control All Beat Repeat is hardware tested by AveyCole and available in main, alone or alongside your machines. Hold TRACK + RETRIG, then a TRIG to repeat included audio tracks. Follows Control All Config selection; its options give way to all sixteen repeat divisions while both modifiers are held. Release either modifier to stop. Exact test 2 firmware.",
        "fr": "Beat Repeat collectif teste sur machine par AveyCole, disponible au principal seul ou avec vos machines. Maintenez TRACK + RETRIG puis un TRIG pour repeter les pistes incluses. Suit Control All Config ; ses choix laissent place aux seize divisions pendant le combo. Relachez un modificateur pour arreter. Noyau identique au test 2."
      }
    ]
  },
  {
    "version": "1.72",
    "date": "2026-10-16",
    "changes": [
      {
        "en": "MIDI saving is hardware tested by AveyCole, including saving into an empty project slot. Stop playback before Save Project and wait for MIDI SAVED. Saved MIDI data loads only when you enter B-side and only while playback is stopped. FUNC + SETTINGS + TRACK opens B-side. Install alone or with your machines, including RETROSYN and TINY; Sample Wizard stays optional. MIDI files are outside Elektron backups and SysEx exports.",
        "fr": "Sauvegarde MIDI testee sur machine par AveyCole, y compris vers un slot projet vide. Arretez avant Save Project et attendez MIDI SAVED. Les donnees MIDI sauvegardees se chargent uniquement en entrant cote B et uniquement lorsque la lecture est arretee. FUNC + SETTINGS + TRACK ouvre B. Seule ou avec vos machines, dont RETROSYN et TINY ; Sample Wizard facultatif. Fichiers MIDI hors backups et exports SysEx Elektron."
      }
    ]
  },
  {
    "version": "1.71",
    "date": "2026-10-16",
    "changes": [
      {
        "en": "Independent MIDI OUT Bank joins main, hardware tested by AveyCole. Install alone or with the current machine set including RETROSYN, TINY and optional Sample Wizard. Six MIDI lanes with CC locks/slides, two MIDI CC LFOs and native TEMPO. B data remains RAM-only; Save Project saves A only. Model-TG stays blocked.",
        "fr": "Banque MIDI OUT autonome au principal, testee sur machine par AveyCole. Seule ou avec les machines actuelles dont RETROSYN, TINY et Sample Wizard facultatif. Six voies MIDI avec locks/slides CC, deux LFO CC et TEMPO natif. Donnees B en RAM ; Save Project sauvegarde A seulement. Model-TG reste bloque."
      }
    ]
  },
  {
    "version": "1.70-preview",
    "date": "2026-10-16",
    "changes": [
      {
        "en": "RETROSYN preview: six retro oscillator types, alone or alongside the complete machine set including WAVE and TINY. Independent Sample Wizard is optional. Hardware testing pending. Main rejects Model-TG recipes and feature registration.",
        "fr": "Apercu RETROSYN : six oscillateurs retro, seuls ou avec toutes les machines dont WAVE et TINY. Sample Wizard independant facultatif. Test materiel attendu. Le main refuse les recettes et la carte Model-TG."
      }
    ]
  },
  {
    "version": "1.69",
    "date": "2026-10-13",
    "changes": [
      {
        "en": "TEMPO opens the stock global tempo menu from MIDI B-side and returns to B-side when closed. The bank-exit combo is limited to the B-side home screen. Published on request after emulation, full-build and transfer checks; hardware confirmation of this TEMPO change is pending.",
        "fr": "TEMPO ouvre le menu tempo global natif depuis B et revient à B à sa fermeture. L’accord de sortie est limité à l’accueil B. Publié sur demande après vérifications émulation, build complet et transfert ; confirmation matérielle de ce changement TEMPO attendue."
      },
      {
        "en": "Removed the redundant MIDI OUT while THRU checklist choice; Live MIDI OUT + THRU remains. Current 18nelli18 release 1.54 was checked: all its selectable mods are already represented.",
        "fr": "Choix MIDI OUT pendant THRU redondant retiré ; MIDI OUT + THRU en direct reste. Version 1.54 courante de 18nelli18 vérifiée : tous ses mods sélectionnables sont déjà représentés."
      }
    ]
  },
  {
    "version": "1.68",
    "date": "2026-10-13",
    "changes": [
      {
        "en": "RAM-only MIDI OUT Bank and SUPERMODEL startup marked hardware tested following AveyCole’s confirmation. MIDI sequences, CC assignments/locks and MIDI LFO settings remain RAM-only and are lost on power-off.",
        "fr": "Banque MIDI OUT en RAM et démarrage SUPERMODEL marqués testés sur matériel après confirmation d’AveyCole. Séquences MIDI, assignations/locks CC et réglages LFO MIDI restent en RAM, perdus à extinction."
      },
      {
        "en": "All flasher descriptions now use brief functionality summaries and verified shortcut lists. Added a downloadable quick reference. Firmware behavior is unchanged.",
        "fr": "Toutes les descriptions du flasher emploient désormais un bref résumé et une liste de raccourcis vérifiés. Ajout d’un mémo téléchargeable. Fonctionnement du firmware inchangé."
      }
    ]
  },
  {
    "version": "1.67",
    "date": "2026-10-13",
    "changes": [
      {
        "en": "MIDI OUT Bank returns to RAM-only operation while retaining the CC knobs, assignments, step locks, trigless locks, CC slides, base restoration, B-side SCRAMBLE, MIDI LFOs, live recording and editing controls. SUPERMODEL remains preferred by Select All. MIDI sequences and CC settings are lost on power-off; Save Project saves the normal A-side project only.",
        "fr": "Banque MIDI OUT revenue au fonctionnement RAM seul avec potards/assignations CC, locks par pas et trigless, slides CC, retour de base, SCRAMBLE B, LFO MIDI, live-rec et édition conservés. SUPERMODEL reste prioritaire dans Tout sélectionner. Séquences et CC perdus à extinction ; Save Project sauvegarde uniquement le projet A natif."
      },
      {
        "en": "The MIDI Save/Load hooks, disk guards and automatic restoration are disabled following failed saves, dead transport controls, project-load freezes and screen corruption reported on previous saving builds, including main. Existing MIDI files are untouched. The rollback is verified in emulation; hardware confirmation is pending.",
        "fr": "Hooks Save/Load MIDI, gardes disque et restauration automatique désactivés après échecs Save, transport inactif, blocages Load et corruption écran signalés sur les builds de sauvegarde, principal compris. Fichiers MIDI existants intacts. Retrait vérifié en émulation, confirmation matérielle attendue."
      }
    ]
  },
  {
    "version": "1.66",
    "date": "2026-10-13",
    "changes": [
      {
        "en": "SUPERMODEL startup animation with a smaller right-aligned by A.V. signature. Select All prefers it; the Modded Cycles animation is mutually exclusive. Normal startup duration is retained.",
        "fr": "Animation de démarrage SUPERMODEL avec petite signature by A.V. à droite. Tout sélectionner la préfère ; animation Modded Cycles exclusive. Durée normale conservée."
      },
      {
        "en": "Only the animation is added to the existing main firmware. Experimental CC-saving changes are excluded. The CC-saving test is withdrawn after reported failed persistence and a full-device project-load freeze. Animation checked in native emulation; hardware verification pending.",
        "fr": "Seule l’animation est ajoutée au firmware principal existant. Sauvegarde CC expérimentale exclue. Test CC retiré après perte de persistance et blocage complet au chargement de projet signalés. Animation vérifiée en émulation native ; matériel à tester."
      }
    ]
  },
  {
    "version": "1.65",
    "date": "2026-10-13",
    "changes": [
      {
        "en": "B-side LFO1/2 destinations now use DATA to edit and DATA again to confirm. Browsing keeps the last confirmed CC active; BACK cancels the draft. DATA right browses OFF then CC0–127. Long destination names scroll in a narrower five-character window to avoid clipping.",
        "fr": "Destinations LFO1/2 B : DATA pour éditer, DATA pour confirmer. Parcourir conserve le CC confirmé ; BACK annule le brouillon. DATA vers la droite parcourt OFF puis CC0–127. Les noms longs défilent dans une fenêtre de cinq caractères pour éviter le débordement."
      },
      {
        "en": "CC slides and all existing features are retained. New LFO selection behavior is checked in emulation and awaits hardware verification. CC assignments and CC locks remain RAM-only while saving integration continues.",
        "fr": "Slides CC et fonctions existantes conservés. Nouvelle sélection LFO vérifiée en émulation, en attente de test matériel. Assignations et locks CC restent en RAM pendant l’intégration de leur sauvegarde."
      }
    ]
  },
  {
    "version": "1.64",
    "date": "2026-10-13",
    "changes": [
      {
        "en": "B-side CC slides are hardware tested and included in the main flasher. Hold SETTINGS and press the destination TRIG to toggle Slide on/off, with the Model-TG popup and double-blink. CC values glide into that step following tempo and lane speed.",
        "fr": "Slides CC B testés sur matériel et inclus dans le flasher principal. SETTINGS + TRIG cible bascule Slide on/off, avec popup et double clignotement Model-TG. Les CC glissent vers ce pas au tempo et à la vitesse de la voie."
      },
      {
        "en": "All existing mods and the Supermodel layout are retained. CC assignments and CC locks remain RAM-only; MIDI note and LFO project saving is unchanged.",
        "fr": "Mods existants et présentation Supermodel conservés. Assignations et locks CC restent en RAM ; sauvegarde projet des notes MIDI et LFO inchangée."
      }
    ]
  },
  {
    "version": "1.63",
    "date": "2026-10-13",
    "changes": [
      {
        "en": "Hardware-tested B-side CC step locks, trigless parameter steps, assigned-CC Scramble, Settings return and stock Note/Vel/Len highlighting are now in the main flasher. CC bases return on the next active note without the corresponding CC lock.",
        "fr": "Locks CC par pas, trigs de paramètres, Scramble des CC assignés, retour SETTINGS au côté B et surbrillance Note/Vel/Len testés sur matériel arrivent dans le flasher principal. Les bases CC reviennent au prochain trig de note sans le lock CC correspondant."
      },
      {
        "en": "CC assignments and CC locks are still RAM-only. Existing MIDI note/LFO project saving and the Supermodel checklist layout are retained. CC slides remain separate work in progress.",
        "fr": "Assignations et locks CC restent en RAM. Sauvegarde projet MIDI/LFO et présentation Supermodel conservées. Slides CC en cours de développement séparé."
      }
    ]
  },
  {
    "version": "1.62",
    "date": "2026-10-13",
    "changes": [
      {
        "en": "A.V.’s Supermodel Edition: compact mod and engine checklists, with every existing selection retained.",
        "fr": "Édition Supermodel A.V. : listes compactes de mods et moteurs, sélections existantes conservées."
      },
      {
        "en": "B-side gray-knob CC assignment and return to B-side are hardware tested by AveyCole. SETTINGS + knob assigns a CC; turning it sends its value. Assignments remain RAM-only.",
        "fr": "Assignation CC des potards gris B et retour côté B testés par AveyCole. SETTINGS + potard assigne le CC ; tournez pour transmettre sa valeur. Assignations en RAM seulement."
      },
      {
        "en": "A separate experimental CC step-lock test is available; these new locks are not included in the main firmware.",
        "fr": "Un test séparé propose les locks CC par pas ; ces nouveaux locks ne sont pas inclus au firmware principal."
      }
    ]
  },
  {
    "version": "1.61",
    "date": "2026-10-13",
    "changes": [
      {
        "en": "MIDI OUT Bank now saves its six parallel MIDI sequencing lanes with Save Project and restores them after project loading or power cycles. Existing and new projects, plus quantized/unquantized live recording, are hardware tested by AveyCole.",
        "fr": "MIDI OUT Bank sauvegarde désormais ses six voies MIDI parallèles avec Save Project et les restaure au chargement ou après extinction. Projets existants/nouveaux et live-rec quantifié/libre testés sur matériel par AveyCole."
      },
      {
        "en": "Notes, velocity, step lengths, timing offsets, locks and MIDI LFO settings are retained. Unsaved changes are not autosaved; MIDI files are separate from normal Elektron backups and SysEx. All existing mod selections remain available.",
        "fr": "Notes, vélocité, durées, microtiming, locks et LFO MIDI conservés. Pas d’autosave des éditions ; fichiers MIDI séparés des backups Elektron et SysEx. Sélections de mods existantes conservées."
      }
    ]
  },
  {
    "version": "1.60",
    "date": "2026-10-13",
    "changes": [
      {
        "en": "LFO SPEED knob routing is hardware tested by AveyCole and now included in Second LFO on the main flasher. With LFO 2 open, the knob edits its speed with the stock range and direction; on B-side, it edits the selected MIDI LFO. Quick assign, keyboard playback and other A-side synth controls remain available.",
        "fr": "Routage LFO SPEED testé sur matériel par AveyCole, désormais inclus dans Second LFO du flasher principal. Page LFO 2 ouverte, le potard édite sa vitesse avec plage et direction natives ; côté B, il édite le LFO MIDI sélectionné. Quick assign, clavier jouable et autres potards synthé A conservés."
      },
      {
        "en": "Only five audio LFO 2 settings are saved with the sound: speed, multiplier, waveform, destination and depth. Fade, start phase and mode reset on load. Unfinished MIDI saving remains on its separate test page and is excluded from main.",
        "fr": "Cinq réglages LFO 2 audio sauvés avec le son seulement : vitesse, multiplicateur, forme, destination et profondeur. Fondu, phase initiale et mode remis aux défauts au chargement. Sauvegarde MIDI inachevée limitée à sa page test séparée, exclue de main."
      }
    ]
  },
  {
    "version": "1.59",
    "date": "2026-10-13",
    "changes": [
      {
        "en": "Second LFO now keeps the trig keyboard and pads playable while open. On A-side, ordinary synth knob turns reach the stock controls; hold LFO and turn a knob for quick assignment. B-side MIDI LFO pages keep note input routed to their MIDI lanes. The description belongs to the Second LFO card. Emulation and full browser-transfer checks passed; published at AveyCole's request.",
        "fr": "Second LFO garde clavier TRIG et pads jouables dans la page. Côté A, les potards ordinaires passent aux contrôles synthé natifs ; LFO maintenu + potard conserve l’assignation rapide. Les pages LFO MIDI B gardent le jeu sur leurs voies MIDI. Description placée sur la carte Second LFO. Émulation et transfert navigateur intégral vérifiés ; publié à la demande d’AveyCole."
      },
      {
        "en": "The existing five-field audio LFO2 sound saving is retained. Unfinished MIDI sequence saving stays on its separate diagnostic page and is excluded from main.",
        "fr": "Sauvegarde existante des cinq réglages LFO2 audio conservée. Sauvegarde MIDI inachevée limitée à sa page de diagnostic séparée, exclue de main."
      }
    ]
  },
  {
    "version": "1.58",
    "date": "2026-10-12",
    "changes": [
      {
        "en": "Sequence Genie now clears per-step chance on the selected MIDI B-side lane in every generation mode, including Notes only, mutation and Euclidean generation. Undo restores the previous chance locks. Queued generation cancels if chance is edited before commit. Verified in emulation; published at AveyCole's request. MIDI saving remains separate and unfinished.",
        "fr": "Sequence Genie efface la chance de pas de la voie MIDI B choisie dans tous les modes, dont Notes seules, mutation et Euclide. Undo restaure les locks chance précédents. Une édition chance avant commit annule la génération en attente. Vérifié en émulation ; publié à la demande d’AveyCole. Sauvegarde MIDI séparée et inachevée."
      }
    ]
  },
  {
    "version": "1.57",
    "date": "2026-10-12",
    "changes": [
      {
        "en": "B-side live recording, hardware tested by AveyCole, is now included in the main MIDI OUT Bank. RECORD + PLAY starts live recording; press PLAY again with RECORD held to switch quantized/unquantized recording.",
        "fr": "Live-rec côté B testé sur matériel par AveyCole, désormais inclus dans la Banque MIDI OUT principale. RECORD + PLAY démarre le live-rec ; PLAY avec RECORD maintenu bascule quantifié/libre."
      },
      {
        "en": "Deleting a B-side trig now resets its note, velocity, length and all per-step locks. Re-adding starts at C5, velocity 100 and length 1. This clear fix passed emulation. MIDI sequence saving remains unfinished and is excluded.",
        "fr": "Supprimer un trig B réinitialise note, vélocité, durée et locks de pas. Le recréer donne C5, vélocité 100, durée 1. Correction validée en émulation. Sauvegarde des séquences MIDI inachevée et exclue."
      }
    ]
  },
  {
    "version": "1.56",
    "date": "2026-10-12",
    "changes": [
      {
        "en": "Second LFO sound saving hardware tested by AveyCole. Only five settings are saved: speed, multiplier, waveform, destination and depth. Fade, start phase and mode reset to stock defaults on load. MIDI sequence and MIDI LFO saving remain unfinished.",
        "fr": "Sauvegarde du Second LFO testée sur matériel par AveyCole. Cinq réglages sauvés seulement : vitesse, multiplicateur, forme, destination et profondeur. Fondu, phase initiale et mode remis aux défauts au chargement. Sauvegarde des séquences et LFO MIDI toujours inachevée."
      }
    ]
  },
  {
    "version": "1.55",
    "date": "2026-10-12",
    "changes": [
      {
        "en": "MIDI OUT Bank update, hardware tested by AveyCole: B-side Sequence Genie, two MIDI LFOs with scrolling CC destinations, track copy/paste/clear and stock Track Setup. FUNC + TRACK opens KbT and Pad; the trig keyboard keeps playing on the assigned MIDI channel while this menu is open, including with REC enabled.",
        "fr": "Mise à jour Banque MIDI OUT testée sur machine par AveyCole : Sequence Genie côté B, deux LFO MIDI avec destinations CC défilantes, copier/coller/effacer la voie et Track Setup stock. FUNC + TRACK ouvre KbT et Pad ; le clavier TRIG continue sur le canal MIDI assigné, même avec REC actif."
      },
      {
        "en": "Sequences follow pattern changes in RAM. Persistent MIDI sequence/LFO saving and B-side retrigger/arp locks remain in development and are not included.",
        "fr": "Les séquences suivent les changements de pattern en RAM. Sauvegarde persistante MIDI/LFO et verrous retrigger/arp côté B encore en développement, non inclus."
      }
    ]
  },
  {
    "version": "1.50",
    "date": "2026-10-11",
    "changes": [
      {
        "en": "Second LFO joins the main flasher, hardware tested by AveyCole. Press LFO twice for six independent secondary LFOs, with stock labels and destination names. Settings remain in RAM and are lost on restart; they are not saved with patterns/projects.",
        "fr": "Second LFO rejoint le flasher principal, testé sur machine par AveyCole. Appuyez deux fois sur LFO : six LFO secondaires indépendants, libellés et destinations natifs. Réglages en RAM, perdus au redémarrage ; sans sauvegarde pattern/projet."
      }
    ]
  },
  {
    "version": "1.49",
    "date": "2026-10-11",
    "changes": [
      {
        "en": "Sequence Genie and optional Queued Generation join the main flasher, including the playback-format and velocity fix confirmed on hardware by AveyCole. Generate during playback applies at the selected track’s next loop; stop to Undo. Shared/per-track length and speed, without pattern chains. The expanded ranges, rhythm/notes, mutation and Euclidean controls are included.",
        "fr": "Sequence Genie et la génération optionnelle au prochain cycle rejoignent le flasher principal, avec la correction du format et de la vélocité confirmée sur machine par AveyCole. Generate en lecture s’applique au prochain cycle de la piste choisie ; arrêtez pour Undo. Longueur/vitesse communes ou par piste, sans chaîne. Plages, rythme/notes, mutation et Euclid inclus."
      }
    ]
  },
  {
    "version": "1.48",
    "date": "2026-10-11",
    "changes": [
      {
        "en": "Step SCRAMBLE is now in the main flasher, hardware tested by AveyCole. Hold one or more trigs, then SETTINGS and TRACK, to toggle fresh random values for the four machine controls every pass. Base sound stays unchanged; immediate SCRAMBLE remains available.",
        "fr": "SCRAMBLE par pas rejoint le flasher principal, testé sur machine par AveyCole. Maintenez un ou plusieurs trigs, puis SETTINGS et TRACK, pour activer/retirer des valeurs fraîches des quatre contrôles machine à chaque passage. Le son de base est conservé ; SCRAMBLE immédiat reste disponible."
      }
    ]
  },
  {
    "version": "1.47",
    "date": "2026-10-11",
    "changes": [
      {
        "en": "Select all now selects compatible mods in the main flasher, prioritizing Model-TG and Live MIDI OUT + THRU over MIDI OUT while in THRU.",
        "fr": "Tout sélectionner choisit les mods compatibles dans le flasher principal, en privilégiant Model-TG et MIDI OUT + THRU en direct plutôt que MIDI OUT en mode THRU."
      }
    ]
  },
  {
    "version": "1.46",
    "date": "2026-10-11",
    "changes": [
      {
        "en": "SCRAMBLE: hold SETTINGS and press TRACK to randomize the current machine’s four controls, with a SCRAMBLE popup and no menu. Independently selectable; requires Model-TG; Sampler excluded. Hardware confirmed by AveyCole. Queued generation remains in Test Flasher 2.",
        "fr": "SCRAMBLE : maintenez SETTINGS et appuyez sur TRACK pour tirer les quatre contrôles machine, avec popup et sans menu. Option indépendante ; demande Model-TG ; Sampler exclu. Confirmé sur machine par AveyCole. La génération différée reste dans le flasher de test 2."
      }
    ]
  },
  {
    "version": "1.45",
    "date": "2026-10-10",
    "changes": [
      {
        "en": "Sequence generator: PLAY/STOP previews your sequence inside the menu without losing Undo. Separate Rand velocity, Rand decay and Rand pan toggles default Off. Stop before Generate or Undo; Undo restores notes, velocity and parameter locks. Tested on hardware by AveyCole. All existing mods remain available.",
        "fr": "Générateur : PLAY/STOP permet d’écouter dans le menu sans perdre Undo. Trois options Rand velocity, Rand decay et Rand pan, désactivées au départ. Arrêtez avant Generate ou Undo ; Undo restaure notes, velocity et p-locks. Testé sur machine par AveyCole. Tous les mods existants restent disponibles."
      }
    ]
  },
  {
    "version": "1.44",
    "date": "2026-10-10",
    "changes": [
      {
        "en": "Scale sequence generator: a four-row scrolling menu keeps the current font with more spacing and screen margins. Turn DATA to reach all seven options. Generate and Undo controls are unchanged. AveyCole confirms the updated layout has been tested on hardware.",
        "fr": "Générateur de séquence en gamme : menu défilant à quatre lignes, police conservée, espacement et marges renforcés. Tournez DATA pour accéder aux sept options. Generate et Undo restent identiques. AveyCole confirme que cet affichage a été testé sur machine."
      }
    ]
  },
  {
    "version": "1.43",
    "date": "2026-10-10",
    "changes": [
      {
        "en": "Scale sequence generator, tested on a Model:Cycles by AveyCole. With playback stopped, press SETTINGS + PAGE to generate notes and trigs in your chosen scale, root, note range and density. Undo remains available while the page is open. Requires Model-TG; works with the available machines.",
        "fr": "Générateur de séquence en gamme, testé sur un Model:Cycles par AveyCole. Lecture arrêtée, appuyez sur SETTINGS + PAGE pour générer notes et trigs selon la gamme, la fondamentale, la plage de notes et la densité choisies. Undo reste disponible dans la page. Demande Model-TG ; fonctionne avec les machines disponibles."
      }
    ]
  },
  {
    "version": "1.42",
    "date": "2026-10-10",
    "changes": [
      {
        "en": "The flasher now waits for you to click Allow MIDI access before it connects to MIDI devices, avoiding automatic MIDI enumeration during page load on Windows.",
        "fr": "Le flasher attend maintenant que vous cliquiez sur Autoriser l’accès MIDI avant de se connecter aux appareils MIDI, afin d’éviter l’énumération automatique au chargement sous Windows."
      }
    ]
  },
  {
    "version": "1.41",
    "date": "2026-10-10",
    "changes": [
      {
        "en": "Volume and pan readouts on the main screen, with one-step LEVEL/DATA changes; dimmed trigless step lights; and the latest multi-line browser, all from 18nelli18's flasher. Your MIDI options and tested FUNC + LEVEL/DATA live toggle remain available.",
        "fr": "Affichage numérique du volume et du pan sur l'écran principal, réglage par pas de 1 ; LEDs des trigless trigs atténuées ; et dernière version du navigateur sur plusieurs lignes, du flasher de 18nelli18. Vos options MIDI et la bascule FUNC + LEVEL/DATA testée restent disponibles."
      }
    ]
  },
  {
    "version": "1.40",
    "date": "2026-10-10",
    "changes": [
      {
        "en": "MACRO and the Syntakt engines can now be selected together. Each engine combination has a matching build with MACRO last; with Model-TG, MACRO follows the Sampler and selected engines. The tested hardware configuration used Model-TG and all five engines; other combinations remain experimental",
        "fr": "MACRO et les moteurs du Syntakt peuvent maintenant être choisis ensemble. Chaque combinaison de moteurs a son build avec MACRO en dernier ; avec Model-TG, MACRO vient après le Sampler et les moteurs choisis. La combinaison testée sur machine utilisait Model-TG et les cinq moteurs ; les autres restent expérimentales"
      },
      {
        "en": "Multi-line browser: three preset names at once, from 18nelli18's flasher. The MIDI options remain available",
        "fr": "Navigateur sur plusieurs lignes : trois noms de presets à la fois, du flasher de 18nelli18. Les options MIDI restent disponibles"
      }
    ]
  },
  {
    "version": "1.39",
    "date": "2026-10-10",
    "changes": [
      {
        "en": "New tested Multi-line browser option, from 18nelli18's flasher: three preset names at once, with the cursor and loaded sound marked. Works with Scroll long names, Model-TG, and the existing mods",
        "fr": "Nouvelle option testée Navigateur sur plusieurs lignes, du flasher de 18nelli18 : trois presets à la fois, avec repères du curseur et du son chargé. Compatible avec Noms qui défilent, Model-TG et les mods existants"
      },
      {
        "en": "The MIDI OUT + THRU live toggle and its fixed THRU fallback remain available",
        "fr": "La bascule MIDI OUT + THRU en direct et son option THRU combinée restent disponibles"
      }
    ]
  },
  {
    "version": "1.38",
    "date": "2026-10-10",
    "changes": [
      {
        "en": "New hardware-tested live MIDI toggle: in THR, hold FUNC and press LEVEL/DATA to switch the Cycles' own MIDI output on or off while incoming MIDI keeps passing through. The stock OUT/THR menu stays unchanged",
        "fr": "Nouvelle bascule MIDI testée sur machine : en THR, tenez FUNC et appuyez sur LEVEL/DATA pour activer ou couper le MIDI généré par le Cycles tandis que le MIDI reçu continue de passer. Le menu OUT/THR d'origine reste inchangé"
      },
      {
        "en": "The existing MIDI OUT while in THRU option remains available; select either MIDI mod, not both",
        "fr": "L'option MIDI OUT pendant THRU reste disponible ; choisissez l'un des deux mods MIDI, pas les deux"
      }
    ]
  },
  {
    "version": "1.37",
    "date": "2026-10-10",
    "changes": [
      {
        "en": "Tested on a Model:Cycles: with the MIDI OUT during THRU mod installed and THR selected, incoming MIDI is forwarded while the Cycles' own clock and track/parameter messages are sent",
        "fr": "Testé sur un Model:Cycles : avec le mod MIDI OUT pendant THRU installé et THR choisi, le MIDI reçu est relayé tandis que l'horloge et les messages de piste/paramètres du Cycles sont envoyés"
      }
    ]
  },
  {
    "version": "1.36",
    "date": "2026-10-10",
    "changes": [
      {
        "en": "The MIDI option now keeps the stock OUT/THRU selector: with THR selected, incoming MIDI is forwarded and the Cycles' own clock and track/parameter messages are also sent. This avoids the third BTH value, which the previous build could not select",
        "fr": "L'option MIDI conserve maintenant le sélecteur OUT/THRU d'origine : avec THR, le MIDI reçu est relayé et l'horloge ainsi que les messages de piste/paramètres du Cycles sont aussi envoyés. Cela évite la troisième valeur BTH, que le build précédent ne permettait pas de choisir"
      },
      {
        "en": "Experimental: patch, overlap and browser-build checks passed; the mode still needs a hardware test",
        "fr": "Expérimental : vérifications du patch, des chevauchements et du build navigateur réussies ; le mode doit encore être testé sur la machine"
      }
    ]
  },
  {
    "version": "1.35",
    "date": "2026-10-10",
    "changes": [
      {
        "en": "First attempt at a third BTH option; later hardware feedback showed it could not be selected. The current version keeps the stock OUT/THRU menu and makes THR send the Cycles' own MIDI while forwarding incoming MIDI",
        "fr": "Premier essai d'une troisième option BTH ; le retour matériel a montré qu'elle ne pouvait pas être choisie. La version actuelle garde le menu OUT/THRU d'origine et fait envoyer par THR le MIDI du Cycles tout en relayant le MIDI reçu"
      },
      {
        "en": "The generated firmware and browser builder checks pass. The M68K emulator could not run on this host, so the fix remains experimental and still needs a hardware check.",
        "fr": "Le firmware généré et les contrôles du générateur Web passent. L'émulateur M68K n'a pas pu s'exécuter sur cet ordinateur ; le correctif reste expérimental et doit encore être vérifié sur la machine."
      }
    ]
  },
  {
    "version": "1.34",
    "date": "2026-10-10",
    "changes": [
      {
        "en": "New experimental MIDI option: BTH combines OUT and THRU, so the Model:Cycles sends MIDI clock and track/parameter messages while forwarding incoming MIDI. Select it under CONFIG > MIDI > PORTS > OUT/THRU; OUT and THR keep their original behavior",
        "fr": "Nouvelle option MIDI expérimentale : BTH combine OUT et THRU, pour que le Model:Cycles envoie l'horloge MIDI et les messages de piste/paramètres tout en relayant le MIDI reçu. Choisissez-la dans CONFIG > MIDI > PORTS > OUT/THRU ; OUT et THR gardent leur comportement d'origine"
      },
      {
        "en": "Checked in the emulator; still needs a test on a real Model:Cycles",
        "fr": "Vérifiée en émulation ; reste à tester sur un vrai Model:Cycles"
      }
    ]
  },
  {
    "version": "1.33",
    "date": "2026-10-10",
    "changes": [
      {
        "en": "Every mod you tick is now checked against its reference build, whatever the combination. Until now the page carried the expected result of each of the 10,559 possible combinations and checked only those; that list doubled with every new mod. It now keeps one reference per mod, plus a sample of 464 combinations checked whole (each mod alone, every pair, the largest ones)",
        "fr": "Chaque mod coché est maintenant vérifié contre son build de référence, quelle que soit la combinaison. Jusqu'ici la page contenait le résultat attendu de chacune des 10 559 combinaisons possibles et ne vérifiait que celles-là ; cette liste doublait à chaque nouveau mod. Elle garde maintenant une référence par mod, plus un échantillon de 464 combinaisons vérifiées en entier (chaque mod seul, chaque paire, les plus grandes)"
      },
      {
        "en": "The page is lighter (about 1.3 MB less to load) and ready for many more mods. Nothing changes on the machine: for the same choice of mods, the firmware built and sent is exactly the same as before, as checked by rebuilding and comparing every combination of the previous version",
        "fr": "La page est plus légère (environ 1,3 Mo de moins à charger) et prête pour beaucoup plus de mods. Rien ne change sur la machine : pour un même choix de mods, le firmware construit et envoyé est exactement le même qu'avant, ce qui a été vérifié en reconstruisant et en comparant toutes les combinaisons de la version précédente"
      }
    ]
  },
  {
    "version": "1.32",
    "date": "2026-10-07",
    "changes": [
      {
        "en": "New mod, Sample preview (with Model-TG): on a Sampler track, press FUNC + MACHINES (preset menu) and move the cursor onto a sample: the track's pad (or its trig keys in keyboard mode) plays it, the way the original OS lets you hear a preset before you pick it. Nothing plays while you scroll. It has its own row in the flasher, under Screen & browsing; ticking it ticks Model-TG too",
        "fr": "Nouveau mod, Écoute des samples (avec Model-TG) : sur une piste Sampler, appuyez sur FUNC + MACHINES (menu des presets) et placez le curseur sur un échantillon : le pad de la piste (ou ses touches de pas en mode clavier) le joue, comme l'OS d'origine fait écouter un preset avant de le choisir. Rien ne joue pendant le défilement. Il a sa propre ligne dans le flasher, sous Écran et navigation ; le cocher coche aussi Model-TG"
      },
      {
        "en": "A sample that isn't in memory yet loads on the first press (a short wait), into free memory or in place of samples your project doesn't use; the next presses usually play at once. If there isn't enough free memory (a preview keeps room for recording and never removes a sample your project uses), or while Model-TG is resampling, the press plays nothing",
        "fr": "Un échantillon qui n'est pas encore en mémoire se charge au premier appui (une courte attente), dans la mémoire libre ou à la place d'échantillons que votre projet n'utilise pas ; les appuis suivants jouent en général tout de suite. S'il n'y a pas assez de mémoire libre (une écoute garde de la place pour l'enregistrement et ne retire jamais un échantillon utilisé par votre projet), ou pendant que Model-TG rééchantillonne, l'appui ne joue rien"
      },
      {
        "en": "The track keeps its own sample: its trigs still play it, and so does its pad once you leave the menu. Sampler presets that remember their sample should also play that sample instead of the track's",
        "fr": "La piste garde son propre échantillon : ses trigs le jouent toujours, et son pad aussi dès que vous quittez le menu. Les presets du Sampler qui gardent leur échantillon devraient aussi faire entendre cet échantillon plutôt que celui de la piste"
      },
      {
        "en": "Tested on a Model:Cycles, alone with Model-TG and with the other mods, and checked in the emulator on the OS's and Model-TG's own code, from the preset menu to the Sampler's voice; with the new MACRO machine, it is checked in the emulator only. Without it, Model-TG firmwares stay exactly the same",
        "fr": "Testé sur un Model:Cycles, seul avec Model-TG et avec les autres mods, et vérifié en émulation sur le code même de l'OS et de Model-TG, du menu des presets à la voix du Sampler ; avec la nouvelle machine MACRO, il est vérifié en émulation seulement. Sans lui, les firmwares Model-TG restent exactement les mêmes"
      }
    ]
  },
  {
    "version": "1.31",
    "date": "2026-10-07",
    "changes": [
      {
        "en": "New mod, MACRO machine: one extra machine with the 47 synthesis models of Braids, Émilie Gillet's open-source macro-oscillator, compiled from her own code (MIT license). SHAPE picks the model (0 to 46), COLOR and SWEEP shape it, CONTOUR lets the amp envelope open the timbre; DECAY, GATE and PUNCH work as on Tone",
        "fr": "Nouveau mod, Machine MACRO : une machine ajoutée avec les 47 modèles de synthèse de Braids, le macro-oscillateur libre d'Émilie Gillet, compilés depuis son propre code (licence MIT). SHAPE choisit le modèle (0 à 46), COLOR et SWEEP le façonnent, CONTOUR laisse l'enveloppe d'ampli ouvrir le timbre ; DECAY, GATE et PUNCH marchent comme sur Tone"
      },
      {
        "en": "MACRO is the 7th machine, or the 8th with Model-TG. Tested on a Model:Cycles, and checked in the emulator: all 47 models give exactly the samples of the original code",
        "fr": "MACRO est la 7e machine, ou la 8e avec Model-TG. Testée sur un Model:Cycles, et vérifiée en émulation : les 47 modèles donnent exactement les échantillons du code d'origine"
      },
      {
        "en": "A MACRO voice computes about twice as much as an original voice (less for the noises, up to 3.5 times for the wave maps), and there is no load governor yet: several MACRO tracks playing at once can make the sound crackle, so start with one or two. It goes with every mod except the Syntakt engines",
        "fr": "Une voix MACRO calcule environ deux fois plus qu'une voix d'origine (moins pour les bruits, jusqu'à 3,5 fois pour les cartes d'ondes), et il n'y a pas encore de régulateur de charge : plusieurs pistes MACRO qui jouent en même temps peuvent faire craquer le son ; commencez avec une ou deux. Elle se combine avec tous les mods sauf les moteurs du Syntakt"
      }
    ]
  },
  {
    "version": "1.28",
    "date": "2026-10-07",
    "changes": [
      {
        "en": "A tidier list of mods in the flasher: they are sorted into sections (Packs, Sounds & machines, Sequencer, Live playing, Screen & browsing, USB & MIDI), with one short line each. The buttons at the top jump to a section and light up when it holds a ticked mod; a section folds away with a click on its title",
        "fr": "Une liste de mods plus claire dans le flasher : ils sont rangés par rubriques (Packs, Sons et machines, Séquenceur, Jeu en live, Écran et navigation, USB et MIDI), avec une ligne courte chacun. Les boutons du haut mènent à une rubrique et s'allument quand elle contient un mod coché ; un clic sur le titre d'une rubrique la replie"
      },
      {
        "en": "Details opens the full description of a mod, how it was tested and its guide link. A Your selection bar stays at the bottom of the screen with the ticked mods, the experimental ones, an × to untick each and a button to step 2. When two mods can't go together, the row says so before you tick, and Undo puts things back",
        "fr": "Détails ouvre la description complète d'un mod, comment il a été testé et le lien vers le guide. Une barre « Votre sélection » reste en bas de l'écran avec les mods cochés, les expérimentaux, une × pour décocher chacun et un bouton vers l'étape 2. Quand deux mods ne vont pas ensemble, la ligne le dit avant de cocher, et Annuler remet tout comme avant"
      },
      {
        "en": "Display only: for the same choice of mods, the firmware built and sent is exactly the same as before (checked on every combination)",
        "fr": "Affichage seulement : pour un même choix de mods, le firmware construit et envoyé est exactement le même qu'avant (vérifié sur toutes les combinaisons)"
      }
    ]
  },
  {
    "version": "1.22",
    "date": "2026-10-07",
    "changes": [
      {
        "en": "Samples OS tab, the other way round (experimental): a Model:Samples can now start as a Model:Cycles. Choose “Model:Samples → Cycles OS”: the page puts the official Model:Cycles OS inside your Model:Samples firmware, whose startup menu, updater and signature stay in place, and sends it over USB",
        "fr": "Onglet OS Samples, dans l'autre sens (expérimental) : un Model:Samples peut maintenant démarrer en Model:Cycles. Choisissez « Model:Samples → OS Cycles » : la page place l'OS officiel du Model:Cycles dans le firmware de votre Model:Samples, dont le menu de démarrage, l'updater et la signature restent en place, et l'envoie par USB"
      },
      {
        "en": "The way back works over USB too, no MIDI interface needed: “Model:Samples: back to its OS” sends the official Model:Samples OS, unchanged. The Model:Cycles OS put on by the page checks updates with the Model:Samples signature (a 32-byte change); an unmodified one would refuse it, which is why going back used to need the MIDI IN",
        "fr": "Le retour marche aussi par USB, sans interface MIDI : « Model:Samples : retour à son OS » envoie l'OS officiel du Model:Samples, sans le modifier. L'OS Cycles installé par la page vérifie les mises à jour avec la signature du Model:Samples (une modification de 32 octets) ; un OS Cycles non modifié le refuserait, d'où le passage obligé par le MIDI IN jusqu'ici"
      },
      {
        "en": "Checked in the emulator on the update checks of both OSes and on the Model:Samples startup code that loads the new OS (way there, way back, and the firmwares they must refuse); not yet tried on a real Model:Samples. The existing choice, the Samples OS on a Model:Cycles, is unchanged",
        "fr": "Vérifié en émulation sur les contrôles de mise à jour des deux OS et sur le code de démarrage du Model:Samples qui charge le nouvel OS (aller, retour, et les firmwares qu'ils doivent refuser) ; pas encore essayé sur un vrai Model:Samples. Le choix existant, l'OS Samples sur un Model:Cycles, ne change pas"
      }
    ]
  },
  {
    "version": "1.21",
    "date": "2026-10-05",
    "changes": [
      {
        "en": "New mod, Startup animation: when the Model:Cycles starts, the four rounded squares of the modded-cycles logo pop in one by one, the top right one hollows out, then “modded-cycles” types itself underneath, instead of the original tile animation",
        "fr": "Nouveau mod, Animation de démarrage : au démarrage du Model:Cycles, les quatre carrés arrondis du logo modded-cycles apparaissent un par un, celui en haut à droite se creuse, puis « modded-cycles » s'écrit dessous, à la place de l'animation de carreaux d'origine"
      },
      {
        "en": "It lasts as long as the original animation, so startup is not slower. Tested on a Model:Cycles, and checked in the emulator on the OS's own screen code, image by image. It goes with every other mod",
        "fr": "Elle dure autant que l'animation d'origine : le démarrage n'est pas plus long. Testée sur un Model:Cycles, et vérifiée en émulation sur le code d'écran de l'OS, image par image. Elle se combine avec tous les autres mods"
      }
    ]
  },
  {
    "version": "1.20",
    "date": "2026-10-05",
    "changes": [
      {
        "en": "Clearer Model-TG card: Model-TG already holds drumkilla's three tweaks (latching mute, trig preview, scrolling names), so ticking it now shows them ticked and locked, “included with Model-TG”, instead of unticking them. Unticking Model-TG frees them again",
        "fr": "Carte Model-TG plus claire : Model-TG contient déjà les trois tweaks de drumkilla (mute verrouillé, écoute d'un pas, noms qui défilent), donc le cocher les affiche maintenant cochés et verrouillés, « inclus avec Model-TG », au lieu de les décocher. Décocher Model-TG les libère"
      },
      {
        "en": "Display only: for the same choice of mods, the firmware built and sent is exactly the same as before",
        "fr": "Affichage seulement : pour un même choix de mods, le firmware construit et envoyé est exactement le même qu'avant"
      }
    ]
  },
  {
    "version": "1.19",
    "date": "2026-10-04",
    "changes": [
      {
        "en": "New mod, Tempo up to 546 BPM: the TEMPO knob, tap tempo, incoming MIDI clock and saved projects go beyond 300, up to 546.0 BPM. 546 is the ceiling of the project format (the tempo is saved in 1/120 of a BPM on 16 bits); the sequencer itself would keep up far beyond",
        "fr": "Nouveau mod, Tempo jusqu'à 546 BPM : le potard TEMPO, le tap tempo, l'horloge MIDI reçue et les projets enregistrés dépassent 300, jusqu'à 546,0 BPM. 546 est le plafond du format des projets (le tempo y est enregistré en 1/120 de BPM sur 16 bits) ; le séquenceur, lui, suivrait bien au-delà"
      },
      {
        "en": "It also fixes the original OS's tempo-synced LFO, which left its cycle above 351.6 BPM at its highest speed and multiplier. Above 300 BPM, the processor may struggle to keep up with busy patterns: push it knowingly. A project saved above 300 BPM reopens at 120 BPM on the original OS",
        "fr": "Il corrige aussi le LFO synchronisé de l'OS d'origine, qui sortait de son cycle au-delà de 351,6 BPM à sa vitesse et à son multiplicateur les plus hauts. Au-delà de 300 BPM, le processeur peut avoir plus de mal à suivre la cadence sur des patterns chargés : à utiliser en connaissance de cause. Un projet enregistré au-dessus de 300 BPM se rouvre à 120 BPM sur l'OS d'origine"
      },
      {
        "en": "Tested on a Model:Cycles, and checked in the emulator on the OS's own code (knob, tap tempo, MIDI clock, project loading, LFOs). It goes with every other mod",
        "fr": "Testé sur un Model:Cycles, et vérifié en émulation sur le code même de l'OS (potard, tap tempo, horloge MIDI, chargement des projets, LFO). Il se combine avec tous les autres mods"
      }
    ]
  },
  {
    "version": "1.18",
    "date": "2026-10-04",
    "changes": [
      {
        "en": "Fast flashing over USB: about 30 seconds instead of 5 to 10 minutes. The flasher now speaks the update protocol of Elektron Transfer (worked out by Elektroid): the Model:Cycles stays on its usual screen, checks every block as it arrives, then asks you to confirm the update",
        "fr": "Flash rapide en USB : une trentaine de secondes au lieu de 5 à 10 minutes. Le flasher parle maintenant le protocole de mise à jour d'Elektron Transfer (décrypté par Elektroid) : le Model:Cycles reste sur son écran habituel, vérifie chaque bloc à son arrivée, puis demande de confirmer la mise à jour"
      },
      {
        "en": "Before sending, the page asks the machine who it is and shows its OS version; it refuses to send a Model:Cycles firmware to a machine that answers as a Model:Samples (Samples OS, or Model-TG with Transfer on SMP). After the update, it follows the restart and reads the new version",
        "fr": "Avant l'envoi, la page demande à la machine qui elle est et affiche sa version d'OS ; elle refuse d'envoyer un firmware Model:Cycles à une machine qui répond comme un Model:Samples (OS Samples, ou Model-TG avec Transfer sur SMP). Après la mise à jour, elle suit le redémarrage et relit la nouvelle version"
      },
      {
        "en": "The classic method (CONFIG › UPGRADE) stays one click away, as the fallback. A Download button in step 4 gives the prepared .syx, to drop onto Elektron Transfer if you prefer",
        "fr": "La méthode classique (CONFIG › UPGRADE) reste à un clic, en secours. Un bouton Télécharger à l'étape 4 donne le .syx préparé, à déposer sur Elektron Transfer si vous préférez"
      },
      {
        "en": "Tested on a real Model:Cycles: 33 seconds for the transfer, then YES on the machine, which installs the firmware and restarts. Every byte the page sends also matches Elektroid's code",
        "fr": "Testé sur un vrai Model:Cycles : 33 secondes de transfert, puis YES sur la machine, qui installe le firmware et redémarre. Chaque octet envoyé par la page correspond aussi au code d'Elektroid"
      }
    ]
  },
  {
    "version": "1.17",
    "date": "2026-10-04",
    "changes": [
      {
        "en": "Syntakt engines, fewer cut notes: the load governor no longer reacts to a single heavy block (a busy step, or the screen redrawing), which is already over when it is measured; only load that lasts two blocks, or a sustained load, fades a voice out",
        "fr": "Moteurs du Syntakt, moins de notes coupées : le régulateur de charge ne réagit plus à un bloc lourd isolé (un pas chargé, l'écran qui se redessine), déjà passé quand il est mesuré ; seule une charge qui dure deux blocs, ou une charge soutenue, éteint une voix en fondu"
      },
      {
        "en": "When a voice must go, it is the one heard least in the mix (its level times its mixer volume and sends; a muted track goes first), the oldest note on a tie; it used to be the quietest voice before the mixer, so often the same track",
        "fr": "Quand une voix doit partir, c'est celle qu'on entend le moins dans le mix (son niveau multiplié par son volume et ses envois au mixeur ; une piste mutée part la première), la note la plus ancienne à égalité ; c'était la voix la plus faible avant le mixeur, donc souvent la même piste"
      },
      {
        "en": "The sustained-load rule (fade a voice out when the load stays above 86 % for a fraction of a second, so the screen and knobs keep enough time) never actually ran: its slow average could not rise, a rounding issue. It now works, without a chain of cuts: it also looks at the recent load and counts the voices it has just stopped",
        "fr": "La règle de charge soutenue (éteindre une voix quand la charge reste au-dessus de 86 % une fraction de seconde, pour que l'écran et les potards gardent assez de temps) n'agissait en fait jamais : sa moyenne lente ne pouvait pas monter, un problème d'arrondi. Elle marche maintenant, sans coupures en chaîne : elle regarde aussi la charge récente et compte les voix qu'elle vient d'arrêter"
      },
      {
        "en": "Lighter on the processor, same sound: the per-voice bookkeeping of the governor with Model-TG, and the original OS's scaling of each track (6-channel audio, Model-TG and the Syntakt engines)",
        "fr": "Plus léger pour le processeur, même son : le suivi de chaque voix par le régulateur avec Model-TG, et la mise à l'échelle de chaque piste par l'OS d'origine (audio 6 canaux, Model-TG et moteurs du Syntakt)"
      },
      {
        "en": "Checked in the emulator: same sound and same voice stops as before at normal load, then the new rules under overload",
        "fr": "Vérifié en émulation : même son et mêmes arrêts de voix qu'avant en charge normale, puis les nouvelles règles en surcharge"
      }
    ]
  },
  {
    "version": "1.16",
    "date": "2026-10-04",
    "changes": [
      {
        "en": "USB audio: no more dropouts when the processor load changes (Model-TG, muted tracks, effects turning off). The stock OS sends each block to the computer right after computing it, so the moment moved with the load, and the 6-channel mod's buffer only tolerated 0.2 ms of it; each block now leaves at the start of the next one, always at the same moment (0.67 ms more latency), and the 6-channel buffer gains a slot",
        "fr": "Audio USB : plus de trous quand la charge du processeur change (Model-TG, pistes mutées, effets qui s'éteignent). L'OS d'origine envoie chaque bloc à l'ordinateur juste après l'avoir calculé, donc à un instant qui bougeait avec la charge, et le tampon du mod 6 canaux n'en tolérait que 0,2 ms ; chaque bloc part maintenant au début du suivant, toujours au même instant (0,67 ms de latence en plus), et le tampon du 6 canaux gagne une case"
      },
      {
        "en": "6-channel audio with Model-TG: a muted track's stem is no longer cut off (its note rings out, as without Model-TG) and no longer restarts frozen when unmuted",
        "fr": "Audio 6 canaux avec Model-TG : la piste USB d'une piste mutée n'est plus coupée net (sa note sonne jusqu'au bout, comme sans Model-TG) et ne repart plus figée au démute"
      },
      {
        "en": "6-channel audio: the copy of the six tracks to USB is lighter on the processor (same bytes)",
        "fr": "Audio 6 canaux : la copie des six pistes vers l'USB est plus légère pour le processeur (mêmes octets)"
      },
      {
        "en": "Checked in the emulator, with the original OS's USB driver, and tested on a real Model:Cycles",
        "fr": "Vérifié en émulation, avec le pilote USB de l'OS d'origine, et testé sur un vrai Model:Cycles"
      }
    ]
  },
  {
    "version": "1.15",
    "date": "2026-10-04",
    "changes": [
      {
        "en": "Trig preview, fix: it also works with the sequencer paused. A MIDI Stop (from the computer on USB, for instance when the DAW stops) pauses the sequencer even when stopped, and PAGE then turned the page instead of playing the step, until a restart",
        "fr": "Écoute d'un pas, correction : elle marche aussi séquenceur en pause. Un Stop MIDI (de l'ordinateur en USB, par exemple quand le logiciel de musique s'arrête) met le séquenceur en pause même à l'arrêt, et PAGE tournait alors la page au lieu de faire sonner le pas, jusqu'au redémarrage"
      },
      {
        "en": "The same fix inside Model-TG, which includes the trig preview. Tested on a real Model:Cycles",
        "fr": "La même correction dans Model-TG, qui contient l'écoute d'un pas. Testé sur un vrai Model:Cycles"
      }
    ]
  },
  {
    "version": "1.14",
    "date": "2026-10-04",
    "changes": [
      {
        "en": "Arpeggiator, fix: in live recording, the notes the arpeggiator plays are recorded one by one, each on its step with its length; the pattern only kept one of the notes, repeated (the retrig of the last key pressed)",
        "fr": "Arpégiateur, correction : en live rec, les notes que joue l'arpégiateur sont enregistrées une à une, chacune sur son pas avec sa durée ; le pattern ne gardait qu'une des notes, répétée (le retrig de la dernière touche)"
      },
      {
        "en": "A single held note on 1 octave is still recorded as one trig with retrig, as with the original retrig. Tested on a real Model:Cycles",
        "fr": "Une seule note tenue sur 1 octave s'enregistre toujours en un trig avec retrig, comme le retrig d'origine. Testé sur un vrai Model:Cycles"
      },
      {
        "en": "Guide: live recording, in the Arpeggiator section",
        "fr": "Guide : l'enregistrement en live, dans la section Arpégiateur"
      }
    ]
  },
  {
    "version": "1.13",
    "date": "2026-10-03",
    "changes": [
      {
        "en": "New: easier trig removal. On the stock OS, a press on a trig longer than 0.2 s counts as a hold and the trig stays, so the soft keys often needed a second press; with this mod, letting go within half a second removes it",
        "fr": "Nouveau : effacer un trig plus facilement. Avec l'OS d'origine, un appui sur un trig de plus de 0,2 s compte comme un maintien et le trig reste, si bien que les touches souples demandaient souvent un second appui ; avec ce mod, relâcher en moins d'une demi-seconde l'efface"
      },
      {
        "en": "Tested on a real Model:Cycles, with Model-TG, the 5 Syntakt engines, 6-channel audio and the arpeggiator",
        "fr": "Testé sur un vrai Model:Cycles, avec Model-TG, les 5 moteurs du Syntakt, l'audio 6 canaux et l'arpégiateur"
      },
      {
        "en": "Guide: a Removing trigs section, with a key to try the delay",
        "fr": "Guide : une section Effacer un trig, avec une touche pour essayer le délai"
      }
    ]
  },
  {
    "version": "1.12",
    "date": "2026-10-03",
    "changes": [
      {
        "en": "New: an arpeggiator in place of the retrig. Hold several notes with RETRIG (or A.On) and they play one after another; FUNC + RETRIG gains Arp (direction) and Oct (1 to 4 octaves), saved with the pattern",
        "fr": "Nouveau : un arpégiateur à la place du retrig. Tenez plusieurs notes avec RETRIG (ou A.On) et elles se jouent l'une après l'autre ; FUNC + RETRIG gagne Arp (le sens) et Oct (1 à 4 octaves), enregistrés avec le pattern"
      },
      {
        "en": "Tested on a real Model:Cycles: the arpeggiator, and Model-TG 1.1 with the 5 Syntakt engines and 6-channel audio",
        "fr": "Testés sur un vrai Model:Cycles : l'arpégiateur, et Model-TG 1.1 avec les 5 moteurs du Syntakt et l'audio 6 canaux"
      },
      {
        "en": "Model-TG: in mute mode (held or latched), each track key mutes at once, as with the latching mute alone; Model-TG queued them until you left the mode",
        "fr": "Model-TG : en mode mute (tenu ou verrouillé), chaque touche de piste mute tout de suite, comme avec le mute verrouillé seul ; Model-TG les mettait en attente jusqu'à la sortie du mode"
      },
      {
        "en": "Guide: an Arpeggiator section",
        "fr": "Guide : une section Arpégiateur"
      }
    ]
  },
  {
    "version": "1.11",
    "date": "2026-10-03",
    "changes": [
      {
        "en": "Model-TG updated to its version 1.1: slide trigs (hold SETTINGS and press a trig key) glide the parameters from one trig to the next, on every machine, the Syntakt engines included",
        "fr": "Model-TG passe à sa version 1.1 : les slide trigs (maintenir SETTINGS et appuyer sur une touche de pas) font glisser les paramètres d'un trig au suivant, sur toutes les machines, moteurs du Syntakt compris"
      },
      {
        "en": "Model-TG 1.1 with the 5 Syntakt engines worked on a real Model:Cycles; its choices stay marked experimental until a firmware built by this page is tried",
        "fr": "Model-TG 1.1 avec les 5 moteurs du Syntakt a fonctionné sur un vrai Model:Cycles ; ses choix restent marqués expérimentaux jusqu'à l'essai d'un firmware construit par cette page"
      },
      {
        "en": "Guide: how to use slide trigs, in the Model-TG section",
        "fr": "Guide : l'utilisation des slide trigs, dans la section Model-TG"
      }
    ]
  },
  {
    "version": "1.10",
    "date": "2026-10-03",
    "changes": [
      {
        "en": "Guide: a Model-TG section (loading samples, playback modes, Attack and Filter, shortcuts)",
        "fr": "Guide : une section Model-TG (charger des échantillons, modes de lecture, Attack et filtre, raccourcis)"
      }
    ]
  },
  {
    "version": "1.9",
    "date": "2026-10-02",
    "changes": [
      {
        "en": "Model-TG with the 5 Syntakt engines is now tested on a real Model:Cycles",
        "fr": "Model-TG avec les 5 moteurs du Syntakt est maintenant testé sur un vrai Model:Cycles"
      }
    ]
  },
  {
    "version": "1.8",
    "date": "2026-10-02",
    "changes": [
      {
        "en": "MACHINES screen: with more than 7 machines, the position dots go on two rows instead of running over the machine picture",
        "fr": "Écran MACHINES : au-delà de 7 machines, les points de position passent sur deux lignes au lieu de déborder sur l'image de la machine"
      }
    ]
  },
  {
    "version": "1.8",
    "date": "2026-10-02",
    "changes": [
      {
        "en": "Syntakt engines: the flasher takes Syntakt OS 1.42, the version now on elektron.se (1.41 still works: same engines, same firmware)",
        "fr": "Moteurs du Syntakt : le flasher accepte l'OS Syntakt 1.42, la version désormais sur elektron.se (la 1.41 marche toujours : mêmes moteurs, même firmware)"
      }
    ]
  },
  {
    "version": "1.7",
    "date": "2026-10-02",
    "changes": [
      {
        "en": "Model-TG with the Syntakt engines: a little lighter on the CPU (our busiest code in the fast internal memory, silent tails of the original machines stopped sooner under heavy load)",
        "fr": "Model-TG avec les moteurs du Syntakt : un peu plus léger pour le processeur (notre code le plus appelé en mémoire interne rapide, fins de notes inaudibles des machines d'origine arrêtées plus tôt sous forte charge)"
      }
    ]
  },
  {
    "version": "1.6",
    "date": "2026-10-01",
    "changes": [
      {
        "en": "Model-TG together with the Syntakt engines: the Sampler stays the 7th machine, the engines follow it (checked in the emulator)",
        "fr": "Model-TG avec les moteurs du Syntakt : le Sampler reste la 7e machine, les moteurs le suivent (vérifié en émulation)"
      }
    ]
  },
  {
    "version": "1.5",
    "date": "2026-10-01",
    "changes": [
      {
        "en": "Model-TG by TinyGregAudio: a Sampler machine, resampling, retrig and master FX (on its own for now)",
        "fr": "Model-TG de TinyGregAudio : machine Sampler, rééchantillonnage, retrig et effets master (seul pour l'instant)"
      }
    ]
  },
  {
    "version": "1.4",
    "date": "2026-10-01",
    "changes": [
      {
        "en": "Fewer cut notes when Syntakt voices play together: only sustained load or a really long block cuts a voice",
        "fr": "Moins de notes coupées quand les voix du Syntakt jouent ensemble : seule une charge soutenue ou un bloc vraiment trop long coupe une voix"
      }
    ]
  },
  {
    "version": "1.3",
    "date": "2026-10-01",
    "changes": [
      {
        "en": "Syntakt voices keep their state in the fast internal memory too",
        "fr": "Les voix du Syntakt gardent aussi leur état en mémoire interne rapide"
      }
    ]
  },
  {
    "version": "1.2",
    "date": "2026-10-01",
    "changes": [
      {
        "en": "Syntakt engines even lighter: their code now runs from the fast internal memory",
        "fr": "Moteurs du Syntakt encore plus légers : leur code s'exécute en mémoire interne rapide"
      }
    ]
  },
  {
    "version": "1.1",
    "date": "2026-10-01",
    "changes": [
      {
        "en": "Syntakt engines lighter on the CPU: their work buffers now use the fast internal memory",
        "fr": "Moteurs du Syntakt plus légers pour le processeur : leurs tampons de calcul passent en mémoire interne rapide"
      }
    ]
  }
];
