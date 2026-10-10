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
- **Conclusion provisoire :** le stockage est un octet, mais le callback stock normalise OUT/THRU en booléen. Cela explique pourquoi modifier seulement la logique stock ne suffit pas. La faisabilité du troisième état n'est pas établie : il faut aussi remplacer proprement le stockage, l'affichage et les trois portes MIDI, puis vérifier sur matériel.

### 5.2 Expérience locale, non publiée

`tools/gen_midi_bth_three_state.py` produit `45-midi-bth-three-state.json`, une expérience locale distincte du mod de secours `44-midi-both.json`. Elle n'est pas sûre à flasher et n'est pas exposée par le flasher. Elle réutilise le masque 35×35 libéré à `0x40167c50` comme code cave.

#### Incident du build test 04

L'utilisatrice a rapporté que le build test 04 a levé une exception et gelé l'appareil en entrant dans `CONFIG > MIDI > PORTS > OUT/THRU`. Il a fallu reflasher une version récupérable. La cause n'est pas prouvée : aucun numéro/code d'exception, PC de faute ou dump d'état n'a été relevé.

L'analyse statique révèle un défaut dans le toggle du build 04 : il exécute `move.b d0,-(sp)`, puis trois `pea` (12 octets), donc le pointeur de pile change de 14 octets avant l'appel à `0x40044b88`. Comme A7 réserve deux octets pour un byte-predecrement, la pile peut perdre son alignement de quatre octets. La routine lit ses arguments comme des longwords à `4(sp)`, `8(sp)` et `12(sp)`. Le `lea 14(sp),sp` restaure bien la pile après retour; le nettoyage de pile seul n'explique donc pas l'incident.

Cette anomalie est à corriger, mais elle ne suffit pas à expliquer le gel : le [manuel NXP MCF5441x, §20.4.8](https://www.nxp.com/docs/en/reference-manual/MCF54418RM.pdf) indique que le ColdFire MCF54418 accepte les opérandes de données non alignés (avec des cycles bus supplémentaires). Les offsets des arguments restent cohérents avec cette convention d'appel. Sans code d'exception, PC de faute ni dump de registres capturés avant le reflash, la cause exacte de l'exception du build 04 reste inconnue. La voie de configuration modifiée demeure le principal endroit à auditer, mais aucun nouveau build ne peut être qualifié de sûr sur cette seule base. Le mod de secours `44-midi-both.json`, testé et confirmé par l'utilisatrice, reste intact.

#### Vérifications de convention d'appel

- L'enregistrement du menu à `0x40035f60` place bien `0x4003560a` dans le champ callback de la ligne OUT/THRU. Le callback stock reçoit donc une adresse de retour et son argument de menu sur la pile. Il ignore cet argument, calcule la nouvelle valeur, puis tail-jump vers le setter. Le helper test 04 remplaçait le callback par un autre tail-call, gardait l'argument d'origine en place et rendait la main par `rts`; cette partie est cohérente avec le chemin stock.
- Le callback d'affichage commence à `0x40035fd2`, sauvegarde D2/D3, puis appelle son helper avec `jsr` depuis `0x40035fd8`. Le remplacement gardait ce `jsr` et le helper retournait par `rts`, ce qui respecte également la forme d'appel observée.
- `0x40044b88` lit ses arguments à `4(sp)` (destination), `8(sp)` (pointeur source) et `12(sp)` (longueur). Les instructions du helper 04 construisent ces trois champs dans cet ordre; le pointeur source vise bien l'octet temporaire. L'ordre des arguments et la durée de vie de la source ne révèlent pas de faute évidente.

Ces contrôles écartent quelques erreurs d'appel simples, mais ne démontrent pas la sûreté du callback. Ils ne disent pas si la notification du réglage (`0x40044b4e`), la transition de l'interface ou une hypothèse non relevée sur le menu provoque le défaut. La prochaine étape utile pour trancher serait un rapport de crash exploitable (code d'exception et PC, ou capture/debug trace); à défaut, il faut poursuivre l'analyse statique de ces fonctions avant tout nouvel essai sur appareil.

#### Différence entre les builds test 03 et 04

L'historique Git permet de comparer précisément les deux essais. Le build 04 a changé deux choses dans cette zone : il a remplacé le mauvais nettoyage de pile `addq.l #2,sp` par `lea 14(sp),sp`, et a déplacé le point d'entrée du callback d'affichage de `HELPER+46` à `HELPER+48`. Le premier changement corrige la pile laissée décalée de 12 octets après l'appel au setter. Le second corrige le fait que le callback d'affichage pointait sur le `rts` final du toggle au lieu du début du code d'affichage.

Le retour utilisateur (build 03 : valeur bloquée sur THRU; build 04 : exception/gèle) montre que ces changements ont modifié le comportement, mais ne permet pas d'isoler lequel a déclenché le défaut. Le diff ne montre pas d'autre changement fonctionnel dans ces deux essais. Un mécanisme déjà confirmé reste disponible pour basculer sans ajouter de chemin de menu firmware : le flasher de production possède le choix de build `MIDI OUT + THRU`. Coché, il conserve le menu stock OUT/THR et rend THR combiné; décoché, il laisse le comportement stock. Ce basculement se fait au build/flash, et non directement depuis l'appareil.

### 6. Bascule en direct FUNC + appui — expérience publiée sur le flasher test

Une voie plus prudente que le troisième état du menu consiste à garder entièrement le réglage stock OUT/THR et à ajouter un **drapeau temporaire en RAM** « THRU envoie aussi » : 0 au démarrage = comportement THRU stock; 1 = relais entrant + émission générée. Les trois portes `0x4000154a`, `0x4000156a` et `0x40001590` consultent ce drapeau. Le raccourci inverse le drapeau; il ne réécrit pas le réglage persistant et ne change pas le chemin MIDI entrant. En OUT, les portes conservent toujours le comportement stock.

Le geste proposé par l'utilisatrice est plus naturel et évite de réserver une touche : **quand la ligne OUT/THRU affiche THR, tenir FUNC et appuyer sur son encodeur de valeur**. Comme l'appui seul appelle déjà le callback de la ligne, l'accroche pourrait intercepter exactement cet événement : avec FUNC tenu, basculer le drapeau une seule fois et laisser l'octet OUT/THRU intact; sans FUNC, exécuter le callback stock. L'écran continue d'afficher THR. C'est préférable au tour d'encodeur, qui pourrait déplacer le curseur ou avoir un chemin d'événements différent.

Le firmware construit chaque `KeyEvent` avec le code de touche à `+12` et les indicateurs à `+16`; bit 1 signifie FUNC tenu ([note 33 §1](33-effacer-un-trig.md)). Le helper `0x40072490` lit précisément ce bit lorsqu'on lui passe un `KeyEvent`. Ce n'est pas encore la preuve que le gestionnaire de rotation reçoit cet objet : il faut tracer le chemin des événements d'encodeur et trouver comment connaître l'état de FUNC à cet endroit. Une solution de repli serait de lire l'état courant du panneau, si son accès est sûr depuis ce chemin.

Le callback stock n'est pas passé de `KeyEvent`. L'expérience `tools/gen_midi_live_both.py` interroge plutôt `0x4007faf4(10)`, qui lit le bit d'état de la touche FUNC dans le bitmap du panneau. Avec FUNC tenu et le réglage sur THR, le callback écrit 1 ou 2 dans l'octet de configuration via la routine de copie stock `0x40044b88`; le getter stock continue de lire les deux valeurs comme THR et le chemin de relais entrant reste intact. Les trois portes de sortie consultent le byte brut et bloquent seulement la valeur 1. Un appui normal continue d'appeler le callback stock.

Le tweak est `45-midi-live-both.json`. Il réutilise le masque libéré `0x40167c50`, garde une copie de secours indépendante (`44-midi-both.json`) et est offert uniquement sur `/flasher-test/` comme carte expérimentale. Il exclut les deux variantes MIDI qui écrivent les mêmes portes. Le sélecteur affiche THR dans les deux modes; le raccourci inverse l'émission du Cycles, tandis que le relais entrant est actif dans les deux cas.

**Statut : expérience publiée, pas encore exécutée dans un émulateur ni vérifiée sur la machine.** `0x4007faf4(10)` lit une entrée de touche du bitmap scanné, mais le moment exact où le scan reflète FUNC par rapport à l'appui de l'encodeur reste à confirmer sur le matériel. La routine d'écriture de préférence est la même que celle utilisée par le code stock; cela n'établit pas la sûreté de la nouvelle séquence complète. La page de test affiche un avertissement de risque et recommande de garder l'OS officiel prêt à restaurer. Ne pas marquer le tweak testé avant un essai matériel.


### 6.1 Retour utilisateur et correction FUNC 02 (10/10/2026)

L’utilisatrice précise que « l’encodeur » désigne le bouton-poussoir du knob LEVEL/DATA, sur la ligne OUT/THRU. Le premier build n’a rien changé. L’audit des appels montre que `0x4007faf4` attend un **code logique** de touche : `notes/32` l’appelle avec 4 pour RETRIG, et `notes/33` identifie FUNC par le code 1. Le build FUNC 01 passait 10 (un code différent), donc la condition FUNC était fausse. Le générateur passe maintenant 1. Aucun autre combo n’a été choisi : c’était la combinaison demandée, et l’erreur était dans l’identifiant transmis.

Le build FUNC 02 reste expérimental. Il n’a pas été validé sur émulateur ni sur la machine. La page avertit que le toggle est invisible à l’écran et demande de vérifier le MIDI reçu sur un appareil externe.
