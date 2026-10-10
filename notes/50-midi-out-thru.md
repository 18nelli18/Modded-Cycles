# 50 — Envoyer et relayer le MIDI avec THRU

Demande de l'utilisatrice : combiner l'émission MIDI du Cycles et le relais des données reçues. Le troisième choix BTH du premier essai ne pouvait pas être sélectionné sur sa machine ; le correctif garde donc le sélecteur d'origine et ajoute l'émission au mode THRU. Tweak `44-midi-both.json`, généré par `tools/gen_midi_both.py`. Adresses : VA de l'OS 1.13.

## En bref

Avec le mod coché et **THR** choisi dans `CONFIG > MIDI > PORTS > OUT/THRU`, le Cycles relaie le MIDI entrant comme avant et envoie aussi son horloge et ses messages de piste/paramètres. **OUT** conserve son comportement d'origine. Le réglage et son menu restent ceux de l'OS stock.

## 1. Chemins MIDI observés

| VA | Rôle |
|---|---|
| `0x40035fd8` | Rend OUT ou THR selon le réglage OUT/THRU. La version finale ne le modifie pas. |
| `0x40036008` | Initialise l'éditeur du réglage. La version finale ne le modifie pas. |
| `0x40044df8` | Getter appelé par les trois portes d'émission. |
| `0x400012d2` | Chemin de réception et de relais ; la version finale ne le modifie pas. |
| `0x4000154a`, `0x4000156a`, `0x40001590` | Portes qui empêchent l'émission générée lorsque le réglage est THRU. |

## 2. Correctif

Le premier essai ajoutait un libellé et une valeur BTH, mais la propriétaire de l'appareil a confirmé que le réglage ne parcourait toujours que OUT et THR. Le nombre de choix et le libellé personnalisé n'ont donc pas permis de créer une troisième valeur réellement sélectionnable.

Le correctif final conserve le menu stock. Aux trois portes d'émission, il remplace l'appel au getter par `moveq #0,d0` (les quatre octets restants sont des NOP). Le test stock suivant reçoit donc zéro et laisse passer les messages générés en mode THRU. Le chemin de relais entrant reste intact ; THRU effectue alors les deux comportements. Le patch ne prend aucune code cave et s'applique avec les autres mods sans réserver de mémoire.

## 3. Vérifications et limites

Les données de patch sont générées depuis l'OS officiel 1.13 et comparées aux octets stock attendus. Les vérifications locales couvrent le générateur, les chevauchements, les empreintes du flasher et son build navigateur. L'émulateur M68K disponible sur l'hôte échoue au démarrage ; il n'est pas utilisé comme preuve. Le comportement doit rester expérimental jusqu'à vérification sur le Model:Cycles.

| Réglage | Envoi par le Cycles | Relais du MIDI entrant |
|---|---|---|
| OUT | oui | non |
| THR avec ce mod | oui | oui |

## 4. Test sur la machine

Le premier essai a été installé sans problème, mais l'appareil ne permettait pas de choisir BTH : l'encodeur faisait alterner OUT et THR. Le correctif ci-dessus est destiné à faire de THR le mode combiné. Le test matériel restant consiste à sélectionner THR, envoyer du MIDI vers l'entrée du Cycles, et vérifier à la fois le relais reçu et l'émission du Cycles (horloge et changements de paramètres).
