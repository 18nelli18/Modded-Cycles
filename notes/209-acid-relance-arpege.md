# 209 — Relancer l'enveloppe ACID sous arpege

Demande d'AveyCole le 30/10/2026 : l'enveloppe ACID doit repartir a chaque
note de l'arpegiateur. Adresses : VA de l'OS 1.13.

## Reponse courte

[FAIT en emulation] La base2.63 considere les notes repetees avec LEN tenue
comme des slides : `in.trig=ACID_SLIDE`, sans remise a zero de l'enveloppe.
Le candidat prive2.64 force ces notes dans le chemin de relance natif, tout
en conservant les slides ordinaires. Le firmware public reste2.63.

## 1. Etat natif et correction

- Le retrig natif est a `0x40a78d58`, pas de28 octets par piste ; +4 est
  sa duree active (notamment -1 pour une note tenue), +20 son evenement garde.
  `arp.c` utilise deja ces deux champs pour identifier une liste encore active.
- `tools/machines/acid_arp/retrigger.c` execute un garde avant `ae_update`.
  Seulement sur une nouvelle note `v+0x34`, avec ces deux champs non nuls,
  il efface le marqueur `held` de la piste ACID. `ae_update` reetablit ce
  marqueur et laisse l'OS relancer l'ampli, puis son impulsion retardee
  `v+0x38` relance l'enveloppe du filtre au bloc suivant.
- Le type `struct track` est importe de la source commune. Assertions de
  compilation : pas140 octets, `held` a+112. Les trois bases2.63 sont epinglees
  par SHA ; prologue de8 octets verifie avant installation du detour.
- Le trampoline rejoue `lea -48(sp),sp` et la sauvegarde des registres,
  puis reprend `ae_update+8`. Le render et son DSP restent ceux de2.63.
- Petit module de152 octets a `0x46932000`, apres le garde Wizard. Un mot
  de garde BSS a `0x4693f800` ; chargeur chaine avant celui du garde Wizard.
  Bootloader et updater ne sont pas modifies. Aucun fichier, allocation ou
  appel UI dans l'audio. Aucun travail ajoute a la boucle par sample.

## 2. Preuves et limites

`tools/emu/test_acid_arp_retrigger.py` execute la boucle audio native et EMAC
avec le vrai DSP2.63. Les notes d'essai sont injectees dans la boucle et
l'etat natif du retrig est prepare par le banc ; cela ne constitue pas un
test complet du clavier ou du minuteur de l'arpegiateur sur appareil.

| Cas | Base2.63 | Candidat2.64 |
| --- | --- | --- |
| Notes normales avec LEN INF | slide, enveloppe continue | identique |
| Retrig/arpege actif, mode F | slide incorrect | relance du filtre |
| Retrig/arpege actif, mode A | slide incorrect | relance de l'ampli |
| Retrig/arpege actif, mode AF | slide incorrect | relance ampli et filtre |

Le banc compare les etats et les pics des slides ordinaires, identiques.
Les modes A/AF montrent aussi le retour de l'ampli a son niveau initial.
Les trois editions Full (main, Optional, Optional MD) passent le boot et
les regressions du garde Wizard. Les variantes Lite n'ont pas ACID.
Le generateur est `tools/gen_acid_arp_retrigger.py`, avec `--check`.

[A FAIRE] Confirmation sur appareil avec notes internes, MIDI, A.On,
RETRIG tenu, vitesses lentes/rapides, ainsi que charge polyphonique. Aucun
resultat materiel ni mesure de cycles physiques annonce.

## Publication complete2.64

AveyCole demande ensuite explicitement de publier toutes les fonctions.
Le build combine utilise ACID_ARP_RETRIGGER dans le noyau partage, avant
le choix glide/legato. Le meme banc confirme F/A/AF ; le banc articulation
confirme les cinq couples glide/legato. Le wrapper autonome ci-dessus
reste seulement le prototype intermediaire, pas la recette publiee.
