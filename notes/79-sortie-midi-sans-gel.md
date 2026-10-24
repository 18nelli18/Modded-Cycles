# 79 — La sortie MIDI sans gel, et le gel de MACHINES déjà corrigé

Demande de Maxime (24/10/2026), en attendant d'avoir la machine pour tester : « corriger les deux gels ». Ce sont les
deux gels de l'OS 1.13 d'Elektron relevés par l'étude de l'OS optimisé (notes/70 §5, sur la branche de la PR #98 :
D1 et D2). Générateur `tools/gen_midi_out_fix.py`, source
`tools/machines/midi_out_fix/ring_wait.S`, tweak `52-midi-out-fix.json`, preuve `tools/emu/test_midi_out_fix.py`.

## En bref

| | État |
|---|---|
| D1 : MACHINES gèle sur une machine que le firmware n'a pas | `[FAIT]` déjà corrigé dans le Modded Cycles OS par les détours des enregistrements ([20 §5](20-moteurs-syntakt-a-cocher.md), testé sur la machine le 30/09/2026) ; vérifié sur l'OS actuel (§1) |
| D2 : l'horloge MIDI sortante fige tout après une longue surcharge | `[FAIT]` corrigé : l'attente de l'OS gardée là où elle peut finir, l'octet jeté là où elle ne le peut pas (§2, §3) |
| Le correctif de l'OS optimisé (D2) | pas repris : il jetait l'octet même quand l'attente aurait fini (§2) |
| Preuve | `[FAIT en émulation]` identique à l'OS d'origine partout où il revient, à chaque niveau d'interruption (§4) |
| Sur la machine | à tester (§5) |

## 1. D1 : déjà corrigé

- `[FAIT]` Dans l'OS d'origine, les accesseurs des enregistrements par machine (`0x4004df5c`, `0x4004df76`) rendent,
  pour une machine hors limites, l'entrée −1 : 76 o avant le tableau `0x40a71540`, que l'écran MACHINES suit comme
  des pointeurs (notes/70 §5, notes/20 §5).
- `[FAIT]` Dans le Modded Cycles OS, ces deux accesseurs sont détournés par le tweak des moteurs
  (`tg_records` de `gen_syntakt_engines.py` : `record_at`, `record_of`) avant ceux de Model-TG ; une machine ou un
  index hors limites y devient KICK. Corrigé ainsi depuis le 30/09/2026 (notes/20 §5), testé sur la machine.
- Vérifié sur l'OS actuel (`test_midi_out_fix.py` §4) : machines 15, 16, 100, 255 et −1 → l'enregistrement de KICK,
  jamais 76 o avant le tableau ; potards de l'écran principal ceux de KICK ; aucun accès hors mémoire. Rien à faire.
- Reste vrai : un projet fait avec le Modded Cycles OS, rouvert sous l'OS officiel, y retrouve le gel d'origine. C'est
  pourquoi le guide demande de remettre les pistes sur une machine d'origine avant de revenir à l'OS officiel.

## 2. D2 : le gel

- `[FAIT]` `0x40001232` range un octet pour la sortie MIDI (DIN). Il est appelé par `0x40001564` (le top d'horloge
  `0x400824ec`, les messages `0x40081092`, `0x400810e6`, `0x40081176`, `0x400812ca`) et par `0x400012e0`.
- `[FAIT]` Quand un message part déjà (`0x4049dca0` non nul), l'octet va dans l'anneau de 1 Kio `*0x4049dcac`. S'il
  est plein (`0x4049dccc` > 1 023), l'OS attend (`0x4000123a..0x40001246`) qu'une place se libère, **avant** de
  toucher au registre d'état.
- `[FAIT]` Seule l'interruption de la liaison série vide l'anneau : `0x40000e8c` (source 53 du contrôleur
  d'interruptions 1, vecteur `0x400002d4`), la seule qui décrémente `0x4049dccc` (`0x40000ef4` ; `0x40001424` le remet
  à zéro à l'initialisation). Son niveau : 4 (`0x40001522 : move.b d1,0xfc04c075`, d1 = 4).
- Un niveau d'interruption de 4 ou plus masque cette interruption : l'attente ne peut alors jamais finir. C'est le cas
  du top d'horloge MIDI `0x4005420c`, dont le corps tourne à IPL 7. Après une longue surcharge (le niveau 4 jamais
  servi pendant 1 024 tops : 4,7 s à 546 BPM, 21 s à 120 BPM), tout se fige, son compris (notes/70 §5).
- Le correctif de l'OS optimisé (`0x40001246 : bgt.s 0x4000123a` → `bgt.s 0x400012c6`) jette l'octet dans tous les
  cas, même appelé depuis l'interface (niveau 0), où l'attente aurait fini et l'octet serait parti : un message
  pourrait perdre des octets quand l'anneau se remplit. Pas repris.

## 3. Le correctif

`ring_wait.S`, dans le masque 27×27 libéré `0x4014a890` (42 o), détour `0x4000123a` (`move.l 0x4049dccc,%d0`, 6 o) :

```
ring_wait: le compte de l'anneau ; <= 1 023 : la suite de l'OS (0x40001248)
           sinon, le niveau du SR : 0 à 3 -> on recommence (l'attente de l'OS)
                                    4 ou plus -> 0x400012c6 (rend d2, d3 ; rts) : l'octet est jeté
```

- Identique à l'OS d'origine dans tous les cas où celui-ci revient : mêmes lectures, même `d0` (le compte) et mêmes
  drapeaux en `0x40001248`.
- Là où l'OS d'origine tourne pour toujours (anneau plein, niveau ≥ 4), le correctif revient sans rien ranger, SR et
  pile intacts : le SR n'a pas encore été changé à cet endroit.
- `0x40001310` (vider l'anneau avant une réinitialisation de la liaison) attend aussi le compte à zéro ; il n'est
  appelé que depuis l'interface `[HYP]` et n'est pas touché.

## 4. Preuve en émulation

`tools/emu/test_midi_out_fix.py`, l'OS de `os.json` sans le correctif (« base ») contre avec, `[FAIT en émulation]`
le 24/10/2026, **TOUT OK** :

1. 49 octets changés dans l'image, tous dans les 3 écritures du tweak ;
2. `0x40001232` appelé directement à chaque niveau d'interruption (0 à 7), l'anneau vide, à moitié plein, plein à une
   place près et plein (1 024, 1 500), message en cours ou non, liaison série libre ou non (160 cas) :
   - là où la base revient, le corrigé rend exactement le même état (anneau, index, compte, registres de la liaison
     et des contrôleurs, d1 à d3, pile, niveau du SR) : 96 cas ;
   - anneau plein à un niveau de 4 ou plus : la base reste dans l'attente, le corrigé revient sans rien ranger : 32 cas ;
   - anneau plein à un niveau de 0 à 3 : les deux attendent (32 cas) ; vidé par l'interruption de niveau 4 (simulée
     après 50 tours), ils rangent l'octet de la même façon ;
3. le top d'horloge MIDI sous une surcharge où le niveau 4 n'est jamais servi : la base range 1 024 tops puis reste
   dans l'attente au 1 025e (PC `0x40001246`, IPL 7) ; le corrigé revient aux 1 030 tops, les 1 024 premiers
   identiques, les suivants sans rien changer ; liaison série libre : 0xF8 envoyé tout de suite, identique ;
4. D1 (§1).

## 5. À tester sur la machine

- Rien ne doit changer en temps normal : l'horloge MIDI et les notes envoyées en MIDI comme avant.
- Le gel lui-même est difficile à provoquer exprès : un projet très chargé (plusieurs pistes MODAL) avec CONFIG ›
  MIDI › SYNC › CLOCK SEND activé et un câble sur MIDI OUT, joué longtemps. Avant : gel complet possible ; maintenant :
  la machine continue (l'horloge MIDI peut perdre des tops pendant la surcharge).

## Chronologie

- 24/10/2026 : demande ; D1 constaté déjà corrigé ; D2 corrigé, preuve.
