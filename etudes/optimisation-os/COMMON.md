# Contexte commun (à lire en entier)

Projet : Modded-Cycles, mods du firmware de l'Elektron Model:Cycles OS 1.13 (ColdFire MCF54415, m68k big-endian, EMAC,
pas de FPU). Dépôt : /home/user/Modded-Cycles (lis AGENTS.md, tools/AGENTS.md, notes/AGENTS.md ; notes techniques en
français dans notes/, index notes/README.md).

Demande de Maxime (le propriétaire, 17/10/2026), mot pour mot :
« mais y'a forcement un travail d'organisation lourd et efficace qui permetterai d'economiser et dameliorer la stabilité,
meme dans l'otpimisation de l'os natif. Creuse cette partie la en cherchant a optimiser en profondeur tout le
fonctionnement de la machine, en lisant et deduisant le code de l'os, etc etc. »
Contexte : on venait de lui montrer que passer à 44,1 kHz ne gagnerait que ~8 % (analyse :
/mnt/project-files/frequence-44k/analyse.md). Il veut maintenant des économies réelles, par réorganisation du travail
de l'OS d'origine, et plus de stabilité.

Fichiers officiels (ne jamais les committer, ni les envoyer nulle part, ni en recopier de gros morceaux) :
- /home/user/Modded-Cycles/firmware/model-cycles_OS1.13.syx, /home/user/Modded-Cycles/firmware/Syntakt_OS1.42.syx
- sections déjà décompressées : /tmp/claude-0/-home-user-Modded-Cycles/4cafd55d-d242-5df3-ad6a-3e64ee54ea56/scratchpad/os/sec3.bin
  (MAIN OS, VA = offset + 0x40000400), sec2.bin (bootstrap), sec4.bin (updater).
- Désassembler : m68k-linux-gnu-objdump -D -b binary -m m68k:cfv4e --adjust-vma=0x40000400 --start-address=0x... --stop-address=0x... <sec3.bin>
  (m68k-linux-gnu-as est aussi là pour assembler un prototype). Python 3 avec unicorn et numpy est installé.

Outils d'émulation du dépôt : tools/emu/mcengine.py (boucle des voix 0x400a7d4a seule), tools/emu/seqrig.py (le vrai
corps de l'interruption audio 0x40058ca0..0x40059382 puis 0x4005979e, mais mixeur, effets et sortie codec SAUTÉS :
0x40056f58, 0x40056ea8, 0x400567ba), tests tools/emu/test_*.py (exemples : test_idle.py, test_governor.py, test_meter.py,
test_track_filter.py, test_lfo_plus.py).

Ce qu'on sait déjà (vérifie si tes conclusions en dépendent) :
- Le son est calculé par blocs de 32 trames, 1 500 blocs/s, interruption DMA 0x400589c0 -> interruption de rendu
  0x40058c5e (séquenceur, USB, puis jsr 0x4005979e en 0x40059382, puis envoi USB 0x40002912). Un bloc = 90 112 ticks du
  minuteur DMA 0 (135,168 MHz) ; les notes comptent « % d'un bloc » avec 166 667 cycles par bloc et 1,54 cycle par
  instruction, plus 15 cycles par ligne de 16 o lue ou écrite en SDRAM (modèle de cache des notes 27-28 : 8 Ko
  d'instructions, 8 Ko de données).
- Mesures sur la machine (notes/23 §6 bis, 31 §6-7) : l'OS d'origine prend 77 % de chaque bloc en moyenne MÊME À
  L'ARRÊT (pic 80-87 %). Profil matériel avec Model-TG (notes/31 §7) : début d'interruption 1 %, fonction audio avant
  les voix 3 %, boucle des voix ~52 %, entre voix et sortie 5 %, sortie (mix, delay, reverb, master) 19-20 % (delay +
  reverb ~12 % même sans rien à traiter). L'interface étouffe au-dessus de ~85 % de moyenne, le son craque près de 100 %.
- Arrêt des voix muettes (notes/23 §7) : -77 % d'instructions dans la boucle des voix quand les 6 voix se taisent ; il
  n'existe que dans les firmwares avec moteurs du Syntakt ou Model-TG (code dans tools/gen_syntakt_engines.py et
  tools/machines/syntakt_bridge/, tools/gov_asm.py).
- La SRAM interne (64 Ko, 0x80000000) est entièrement prise par l'OS (notes/23 §3) ; mémoire 0x40000000..0x47ffffff en
  cache copyback (ACR0 = 0x4007e020) ; 0x4axxxxxx = alias non caché de la DDR (lignes du delay 0x4a400000, de la
  reverb 0x4a340000, anneau DMA 0x4a3ed080). La DDR2 est sur un bus de 8 bits.
- Notes utiles : 23, 25-31, 35, 36 (charge, régulateur, SRAM, profil), 38 (tempo), 09 §6 (mixeur), 21 (matériel),
  /mnt/project-files/frequence-44k/analyse.md (horloges, tables de 48 kHz).

Règles :
- Lecture seule sur le dépôt : n'édite aucun fichier suivi, ne committe rien, ne pousse rien, n'ouvre aucune PR.
- Écris tes fichiers de travail et ton rapport dans ton dossier
  /tmp/claude-0/-home-user-Modded-Cycles/4cafd55d-d242-5df3-ad6a-3e64ee54ea56/scratchpad/optim/<ton-dossier>/.
- N'appelle aucun outil mcp__hearthbot__. Ne publie rien. N'utilise aucun dépôt GitHub autre que 18nelli18/Modded-Cycles.
- Ne fais installer aucun paquet.
- Chaque affirmation porte sa preuve (adresse et instruction désassemblée, fichier:ligne, commande et sa sortie, section
  de note) et une étiquette : [FAIT] vérifié, [DÉDUIT] calculé à partir de faits, [HYP] plausible non vérifié.
- Une optimisation proposée doit dire : ce qu'elle change, le gain estimé (en % d'un bloc, avec la méthode), si le son
  reste identique à l'échantillon près (et comment le prouver en émulation), le risque (stabilité, récupération,
  conflits avec les mods existants : tweaks/model-cycles_OS1.13/REGISTRY.md), l'effort. Un prototype prouvé en
  émulation vaut mieux qu'une idée ; ne prétends jamais à un résultat matériel.
- Rapport final en français, dans <ton-dossier>/rapport.md, puis ton message final : un résumé de 15 lignes au plus
  et la liste classée des optimisations (gain, risque, son identique oui/non, effort), avec le chemin du rapport.
