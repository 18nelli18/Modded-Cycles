# 50 — Envoyer et relayer le MIDI avec THRU

Demande de l'utilisatrice : combiner l'émission MIDI du Cycles et le relais des données reçues. Le troisième choix BTH du premier essai ne pouvait pas être sélectionné sur sa machine ; le correctif garde donc le sélecteur d'origine et ajoute l'émission au mode THRU. Tweak `44-midi-both.json`, généré par `tools/gen_midi_both.py`. Adresses : VA de l'OS 1.13.

## En bref

Avec le mod coché et **THR** choisi dans `CONFIG > MIDI > PORTS > OUT/THRU`, le Cycles relaie le MIDI entrant comme avant et envoie aussi son horloge et ses messages de piste/paramètres. **OUT** conserve son comportement d'origine. Le réglage et son menu restent ceux de l'OS stock.

## 1. Chemins MIDI observés

| VA | Rôle |
|---|---|
| `0x40035fd8` | Affiche OUT ou THR à partir de la valeur lue. |
| `0x4003560a` | Callback d'appui : le code stock transforme explicitement la valeur en bascule booléenne 0↔1. |
| `0x40044df8` | Lit l'octet de réglage `0x50` sans le réduire à un booléen. |
| `0x40044dc2` | Écrit un octet de réglage `0x50`. |
| `0x400012d2` | Chemin de réception et de relais ; la version finale ne le modifie pas. |
| `0x4000154a`, `0x4000156a`, `0x40001590` | Portes qui empêchent l'émission générée lorsque le réglage est THRU. |

## 2. Correctif

Le premier essai ajoutait un libellé et modifiait le rendu du menu, mais la propriétaire de l'appareil a confirmé que le réglage ne parcourait toujours que OUT et THR. Le callback d'appui n'avait pas été modifié : il inversait explicitement un booléen.

Le correctif final conserve le menu stock. Aux trois portes d'émission, il remplace l'appel au getter par `moveq #0,d0` (les quatre octets restants sont des NOP). Le test stock suivant reçoit donc zéro et laisse passer les messages générés en mode THRU. Le chemin de relais entrant reste intact ; THRU effectue alors les deux comportements. Le patch ne prend aucune code cave et s'applique avec les autres mods sans réserver de mémoire.

## 3. Vérifications et limites

Les données de patch sont générées depuis l'OS officiel 1.13 et comparées aux octets stock attendus. Les vérifications locales couvrent le générateur, les chevauchements, les empreintes du flasher et son build navigateur. L'émulateur M68K disponible sur l'hôte échoue au démarrage ; le comportement a donc été confirmé sur la machine.

| Réglage | Envoi par le Cycles | Relais du MIDI entrant |
|---|---|---|
| OUT | oui | non |
| THR avec ce mod | oui | oui |

## 4. Test sur la machine

Le premier essai a été installé sans problème, mais l'appareil ne permettait pas de choisir BTH : l'encodeur faisait alterner OUT et THR. Le correctif ci-dessus fait de THR le mode combiné.

### 4.1 Testé le 10/10/2026

Après avoir installé le build avec ce mod, l'utilisatrice a confirmé : « I tested this on my Model Cycles and it functions as intended! » THR relaie donc le MIDI reçu et transmet en même temps l'horloge et les messages générés par le Cycles. Le statut du flasher passe à **testé**.

## 5. Faisabilité d'un troisième état (10/10/2026)

### 5.1 Limite trouvée dans le menu stock

- **`[FAIT]`** Le getter `0x40044df8` renvoie une valeur booléenne : il teste l'octet à `0x404e9b50`, puis produit `0` ou `-1`.
- **`[FAIT]`** Le setter `0x40044dc2` booléanise également son argument avant de l'écrire. C'est pourquoi le premier essai restait bloqué en THRU : l'appui suivant partait du getter normalisé et le setter ramenait toute valeur non nulle à `1`.
- **`[FAIT]`** La valeur brute du réglage est conservée à `0x404e9b50`. La routine générique de copie/notification `0x40044b88` permet de mettre à jour cet octet sans passer par le setter booléen.
- **Conclusion :** un troisième état est **faisable dans le firmware**. Le correctif doit lire et écrire la valeur brute, afficher les trois valeurs et faire en sorte que les trois portes de sortie ne bloquent que THR (`1`). Le relais entrant d'origine accepte déjà les valeurs non nulles, donc BTH (`2`) est relayé.

### 5.2 Expérience locale, non publiée

`tools/gen_midi_bth_three_state.py` produit `45-midi-bth-three-state.json`, séparé du mod de secours `44-midi-both.json`. La version corrigée lit l'octet brut pour obtenir `0→1→2→0`, l'écrit via `0x40044b88`, nettoie toute sa pile d'arguments avant de rendre la main, associe les libellés OUT/THR/BTH et adapte les trois portes pour bloquer uniquement à `1`. Elle réutilise le masque 35×35 libéré à `0x40167c50`. Les deux mods sont déclarés incompatibles : le secours rend aussi THR émetteur et empêcherait de retrouver le comportement stock de THR.

Le générateur et la construction complète du fichier `.syx` ont réussi sur l'OS officiel 1.13. Les premières versions du test publiées séparément reproduisaient OUT↔THR seulement ; l'analyse a identifié la normalisation booléenne du getter et du setter, puis une pile d'arguments non nettoyée après l'appel à la routine de configuration. La nouvelle version corrige ces chemins et reste expérimentale jusqu'au prochain essai matériel. Le mod de secours, déjà confirmé par l'utilisatrice sur son appareil, reste disponible sur `main`.
