# 49 — Envoyer et relayer le MIDI en même temps

Demande de l'utilisatrice : ajouter une troisième option globale dans `CONFIG > MIDI > PORTS > OUT/THRU`, qui combine OUT et THRU. Le tweak `44-midi-both.json` est généré par `tools/gen_midi_both.py`. Adresses : VA de l'OS 1.13.

## En bref

`BTH` (valeur 2) conserve les deux fonctions à la fois : l'horloge et les messages MIDI générés par le Cycles sortent, et les octets MIDI reçus sont relayés. OUT (0) et THR (1) gardent leur comportement. Le tweak est indépendant des machines ajoutées.

## 1. Chemins de l'OS

| VA | Rôle |
|---|---|
| `0x40035fd8` | Rend le libellé OUT ou THR à partir du réglage `0x50`. |
| `0x40036008` | Donne au menu le nombre d'options, initialement deux. |
| `0x40044df8` | Getter du réglage `0x50` OUT/THRU. Le code d'origine le traitait comme un booléen ; il faut conserver sa valeur brute pour reconnaître BTH (`2`). |
| `0x40044e32` | Getter d'un réglage voisin (`0x51`, OUT TO), pas de OUT/THRU. Ne pas l'utiliser pour BTH. |
| `0x400012d2` | Reçoit les octets MIDI et les relaie lorsque le getter booléen est vrai. |
| `0x4000154a`, `0x4000156a`, `0x40001590` | Trois portes qui omettent les messages générés lorsque le getter booléen indique THRU. |

Les trois portes d'émission ignorent les messages en THRU, alors que la route d'entrée utilise tout mode non nul pour relayer. Un troisième mode ne peut donc pas simplement réutiliser le getter booléen aux deux endroits.

## 2. Modifications et compatibilité

Le menu appelle un helper de 46 octets qui lit le réglage `0x50` et renvoie OUT, THR ou BTH. La liste passe de deux à trois choix. Les trois portes d'émission appellent un helper de 22 octets qui renvoie vrai seulement pour THRU : BTH laisse donc passer l'horloge et les messages de piste/paramètres. Le getter d'origine reste en place sur la réception ; BTH étant non nul, les octets entrants suivent la route THRU.

Les 68 octets de helpers occupent `0x40167c50`, le masque 35×35 identique aux autres masques du groupe. Le filtre par piste (PR #55, note 47 §4) laisse ce masque libre. Son constructeur `0x400b211e` est redirigé vers `0x4014a660`, masque identique conservé. L'emplacement est indépendant des masques de MACRO, Model-TG et des moteurs du Syntakt ; BTH peut donc être combiné avec eux.

## 3. Preuve en émulation

`tools/emu/test_midi_both.py` exécute le code ColdFire du menu, des portes d'émission et du relais d'entrée dans l'image stock puis modifiée ; le getter `0x50` est intercepté pour donner successivement les valeurs de menu. Ce test ne couvre pas l'interaction avec l'encodeur ni la persistance de la valeur, et ne suffit pas seul à valider le menu sur la machine.

| Mode | Libellé | Sorties générées | Relais entrant |
|---|---|---|---|
| OUT (0) | OUT | oui | non |
| THR (1) | THR | non | oui |
| BTH (2) | BTH | oui | oui |

Résultat initial du 10/10/2026 : les assertions des helpers passaient, mais la preuve interceptait un getter du réglage adjacent `0x51` au lieu du getter OUT/THRU `0x50`. Le rapport de Maxime sur son appareil (« It doesn't do anything on the current build ») montre que cette validation ne couvrait pas le réglage réel. Le générateur est corrigé pour appeler `0x40044df8`; il faut refaire la preuve complète et retester le menu sur l'appareil avant de déclarer le problème résolu.
