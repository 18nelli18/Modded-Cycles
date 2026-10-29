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
    "date": "2026-10-27",
    "changes": [
      {
        "en": "Full and Lite add distinct Punch attacks, per-track FX and LFO/filter performance improvements. Full offers 23 sound machines plus MIDI Out; Lite keeps the six stock machines.",
        "fr": "Full et Lite ajoutent des attaques Punch propres à chaque machine, des effets par piste et des optimisations LFO/filtre. Full propose 23 machines sonores plus MIDI Out ; Lite conserve les six machines d’origine."
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
    "version": "2.29",
    "date": "2026-10-23",
    "changes": [
      {
        "en": "Native emulation checks stereo tails, Decay/Tone, send-zero dry behavior, old effects, controls, saving and recovery. Updated bilingual shortcut guide and printable PDF.",
        "fr": "Emulation native : queues stereo,Decay/Tone,envoi nul sec,anciens effets,commandes,sauvegarde et recuperation. Guide bilingue et PDF actualises."
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
    "version": "2.25",
    "date": "2026-10-23",
    "changes": [
      {
        "en": "In CRU1+DEL and CRU2+DEL, plain TIME keeps native Delay Time. Hold SETTINGS and turn DELAY TIME to adjust native Delay Feedback; release SETTINGS to return to Time. FUNC first, then TRACK + DELAY SEND still adjusts Feedback.",
        "fr": "En CRU1+DEL et CRU2+DEL, TIME simple garde Delay Time natif. Maintenez SETTINGS et tournez DELAY TIME pour regler Delay Feedback natif ; relachez SETTINGS pour revenir a Time. FUNC puis TRACK+DELAY SEND regle toujours Feedback."
      },
      {
        "en": "The Reverb and Delay selectors are now opaque popups over the normal screen. Browsing still leaves the sound unchanged; release TRACK to apply, or press BACK to cancel.",
        "fr": "Les selecteurs Reverb et Delay sont maintenant des fenetres opaques par-dessus l’ecran normal. Parcourir ne change toujours pas le son ; relachez TRACK pour appliquer, ou BACK pour annuler."
      },
      {
        "en": "Main serves the exact shared-filter v57 approved by AveyCole on 23 October 2026. Includes all v55 work, machines, filters, icons and cumulative fixes. New effect controls and auxiliary sends save after playback stops and have no new p-lock/LFO destinations.",
        "fr": "Le principal sert le v57 exact avec filtre partage,approuve par AveyCole le23octobre2026. Inclut tout v55,machines,filtres,icones et correctifs precedents. Nouveaux controles et envois auxiliaires sauvegardes apres arret,sans nouvelles destinations p-lock/LFO."
      }
    ]
  },
  {
    "version": "2.24",
    "date": "2026-10-23",
    "changes": [
      {
        "en": "Both effect selectors now show boxed scrolling lists. Hold TRACK and turn DELAY TIME or REVERB SIZE: left moves up, right moves down. Browsing leaves the sound unchanged; release TRACK to apply, or press BACK to cancel. Stock Delay/Reverb sits between the solo and combined choices.",
        "fr": "Les deux selecteurs affichent une liste encadree. Maintenez TRACK et tournez DELAY TIME ou REVERB SIZE : gauche monte, droite descend. Parcourir ne change pas le son ; relachez TRACK pour appliquer, ou BACK pour annuler. Delay/Reverb stock se trouve entre les choix seuls et combines."
      },
      {
        "en": "CRU1+DEL/CRU2+DEL retain native Delay Time on plain TIME. FUNC + TIME adjusts Rate; hold FUNC first, then TRACK and turn TIME for Bits. The same modifier order gives chorus Depth in chorus/reverb combinations. FUNC first, then TRACK + DELAY SEND adjusts Delay Feedback. Set Reverb Tone in standard REVERB mode with FUNC + REVERB SIZE, then return to the combined mode; Tone carries over.",
        "fr": "CRU1+DEL/CRU2+DEL gardent Delay Time sur TIME simple. FUNC+TIME regle Rate ; maintenez FUNC puis TRACK et tournez TIME pour Bits. Ce meme ordre donne Depth en chorus/reverb. FUNC puis TRACK+DELAY SEND regle Delay Feedback. Reglez Reverb Tone en mode REVERB standard avec FUNC+REVERB SIZE,puis revenez au mode combine ; Tone est conserve."
      },
      {
        "en": "FUNC-first TRACK holds support effect edits without opening Track Setup; a quick tap keeps the stock shortcut. TRACK-first FUNC still supports latching mute. Machine browsing is slightly slower to avoid skipping Sample Wizard. Stock FUNC + SETTINGS/PATTERN temp save/reload can pass through while retrig is latched. DX appears only after a physical TRACK + RETRIG hold of at least 350 ms, never from entering or exiting the latch.",
        "fr": "Maintenir FUNC puis TRACK permet les reglages FX sans ouvrir Track Setup ; un appui bref garde le raccourci stock. TRACK puis FUNC conserve le mute verrouille. Defilement machines un peu ralenti pour eviter de sauter Wizard. FUNC+SETTINGS/PATTERN save/reload temporaires passent pendant retrig verrouille. DX demande un maintien physique TRACK+RETRIG d’au moins350ms,jamais l’entree/sortie du verrou."
      },
      {
        "en": "Main serves the exact shared-filter v55 tested and approved by AveyCole on 23 October 2026. Includes all v54 work, previous machines, filters, icons and cumulative fixes. New effect controls and auxiliary sends save after playback stops and have no new p-lock/LFO destinations. SETTINGS + Size/Time shortcuts are not part of this release.",
        "fr": "Le principal sert le v55 exact avec filtre partage,teste et approuve par AveyCole le23octobre2026. Inclut tout v54,machines,filtres,icones et correctifs precedents. Nouveaux controles et envois auxiliaires sauvegardes apres arret,sans nouvelles destinations p-lock/LFO. Les raccourcis SETTINGS+Size/Time ne font pas partie de cette version."
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
    "version": "2.15",
    "date": "2026-10-21",
    "changes": [
      {
        "en": "MACRO now shows each algorithm’s number (0–46) underneath its name, on a second or third line. All 47 layouts fit without clipping. The existing BACK/reset reference, algorithm order and sound are preserved. Includes the per-track filter and all previous machine-card and DX features.",
        "fr": "MACRO affiche maintenant le numero0–46 sous le nom de chaque algorithme, sur une deuxieme ou troisieme ligne. Les47affichages tiennent sans troncature. Reference BACK/reset, ordre et son conserves. Filtre par piste et fonctions precedentes de cartes machines et DX inclus."
      }
    ]
  },
  {
    "version": "2.14",
    "date": "2026-10-21",
    "changes": [
      {
        "en": "MACRO now displays its 47 algorithm names instead of numbers. Long names use two lines in the smaller native font so every label fits. Algorithm order, sound and saved values stay the same. Includes the per-track filter, new machine cards, original Wizard hat and saved DX toggle.",
        "fr": "MACRO affiche maintenant les noms de ses47algorithmes au lieu des nombres. Les noms longs utilisent deux lignes avec la petite police native pour tenir a l ecran. Ordre des algorithmes, son et valeurs sauvegardees identiques. Filtre par piste, nouvelles cartes machines, chapeau Wizard original et DX sauvegarde conserves."
      }
    ]
  },
  {
    "version": "2.13",
    "date": "2026-10-21",
    "changes": [
      {
        "en": "The twelve added machines now have distinct STR, DEX and MAG character profiles. Eleven get angular initial icons; Sample Wizard keeps its original hat and two-line title. The six stock machine cards stay the same. Includes the per-track filter, LTC/SIL menu values and saved DX toggle, Off by default.",
        "fr": "Les douze machines ajoutees ont des profils STR, DEX et MAG distincts. Onze recoivent des icones d initiales anguleuses ; Sample Wizard garde son chapeau et son titre sur deux lignes. Les six cartes stock restent identiques. Filtre par piste, valeurs LTC/SIL et DX sauvegarde, Off par defaut, conserves."
      }
    ]
  },
  {
    "version": "2.12",
    "date": "2026-10-21",
    "changes": [
      {
        "en": "Main includes the per-track filter and the saved DX diagnostic toggle in Mod Setup, Off by default. Enable DX for the P/O/N popup after beat repeat. Mute Latch is shown as LTC and Silent pad mode as SIL so the values fit. Includes the CHORD Attack retrigger fade, MIDI Swing encoder and note-release fixes.",
        "fr": "Le principal inclut le filtre par piste et le diagnostic DX sauvegarde dans Mod Setup, Off par defaut. Activez DX pour le popup P/O/N apres beat repeat. Mute Latch devient LTC et le mode pads Silent devient SIL pour eviter le chevauchement. Inclut le raccord CHORD Attack et les correctifs du potard Swing MIDI et des relachements de notes."
      }
    ]
  },
  {
    "version": "2.11",
    "date": "2026-10-21",
    "changes": [
      {
        "en": "MIDI Out now has nine assignable CC knobs, stock Chance/Swing controls and timing, and keyboard arpeggiation with A. On. MIDI LFO values are visible, Speed updates held notes, and Destination browsing sends no modulation while editing. TRACK + FUNC latch timing is reliable. Machine selection shows Sample above Wizard with the right-side hat. User-tested filter build, no diagnostics.",
        "fr": "MIDI Out propose neuf potards CC assignables, Chance/Swing stock avec timing, et arpege clavier avec A. On. Valeurs LFO MIDI visibles, Speed agit sur les notes tenues et parcourir Destination ne transmet aucune modulation pendant l edition. TRACK + FUNC entre de facon fiable en mute verrouille. Selection de machine : Sample au-dessus de Wizard, chapeau a droite. Version avec filtre testee par l utilisateur, sans diagnostic."
      }
    ]
  },
  {
    "version": "2.10",
    "date": "2026-10-21",
    "changes": [
      {
        "en": "ACID output is 6 dB louder, with DRIVE and synth behavior preserved. Main includes the per-track filter and all previous MIDI, Slice and USB fixes. No diagnostics. AveyCole tested the sound and reported no crash with beat repeat in this build.",
        "fr": "Sortie ACID augmentÃ©e de 6 dB, avec DRIVE et comportement du synthÃ© conservÃ©s. Le principal inclut le filtre par piste et tous les correctifs MIDI, Slice et USB prÃ©cÃ©dents. Aucun diagnostic. AveyCole a testÃ© le son et ne signale aucun crash avec beat repeat dans cette version."
      }
    ]
  },
  {
    "version": "2.09",
    "date": "2026-10-21",
    "changes": [
      {
        "en": "Fix computer-to-Cycles USB audio breaking up or sounding distorted in 6ch mode. The return audio buffer is enlarged while six-track transmission keeps its existing queue and timing. User reported that the test worked; native send/return and saved-mode checks pass. All prior features and the per-track filter remain included. No diagnostics in main.",
        "fr": "Correction du retour audio USB ordinateur vers Cycles hachÃ© ou distordu en mode 6ch. Tampon de rÃ©ception agrandi ; file et timing de lâ€™envoi six pistes conservÃ©s. Test signalÃ© fonctionnel par lâ€™utilisateur ; envoi/retour natifs et mode sauvegardÃ© vÃ©rifiÃ©s. Fonctions prÃ©cÃ©dentes et filtre par piste conservÃ©s. Aucun diagnostic dans le principal."
      }
    ]
  }
];
