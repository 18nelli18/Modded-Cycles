# Track Setup privé B — prototype non publié

FUNC + TRACK ouvre une vue locale (`mlp_setup=3`) avec KbT et Pad.
DATA choisit une ligne ; clic DATA entre/sort de l'édition. BACK ferme
seulement la vue et conserve l'objet B, la voie et ses données. La bascule
FUNC + SETTINGS + TRACK refuse de fermer B derrière une vue de réglage,
Sequence Genie ou LFO CC : revenir à l'écran principal avant de quitter B.

KbT transpose le clavier chromatique de -60 à60 demi-tons, pour la seule
voie MIDI sélectionnée. Pad est le numéro MIDI joué par le pad, affiché en
nom de note (72=C5). Les pads émettent via la file clavier sûre, et leurs
releases libèrent la note. FUNC + pad conserve la fonction mute MIDI.

Header264 privé : octet6 signé KbT ; octet7 Pad XOR72. Les anciens zéros
conservent transpose0/PadC5. Le codec sidecar valide et préserve ces octets ;
aucune donnée audio A modifiée, aucune nouvelle taille de record MBK1.
Les réglages ne survivent pas encore au redémarrage dans le flasher publié.

Preuves : `test_midi_lane_track_setup.py`, `test_midi_lane_keyboard.py`,
`test_midi_lane_storage.py --asm`, `test_midi_storage_session.py`,
`test_midi_lane_clipboard.py`, `test_midi_lane_bank_key.py`. Le bundle complet
avec LFO CC compile ; publication et validation hardware restent à faire.

## Retrigger/Arp demandé ensuite

Les menus stock appartiennent à des données de pistes A : les appeler sans
adaptateur éditerait ces pistes. Rte est le champ natif514, Len513, A.On un
objet distinct ; l'arp installé utilise512 (notes/32). B nécessite ses propres
réglages de voie et locks de pas, une cadence infra-pas pour le retrigger,
et des Note Off réservés lors des répétitions. Le format courant n'a que
note/velocity/gate/flags par pas. Ne pas réinterpréter les octets gate ou
slide pour y cacher ces paramètres : prévoir une extension versionnée et
compatible au stockage. Cette partie n'est pas encore implémentée.

## Menu stock et clavier derrière la vue (12/10/2026)

Le rendu appelle maintenant TrackMenuView::draw (0x400423e4) avec un
modèle et deux lignes privés : KbT et Pad. Aucun constructeur,
observer ou setter de piste A n'est employé. Le panneau arrondi Track /
Setup, les polices, labels et surbrillance sont dessinés par le code natif.
MOut retiré à la demande d’AveyCole : la commande de sortie existe déjà ailleurs.

Dans Track Setup, les touches TRIG jouent le clavier même lorsque REC est
actif ; elles ne placent pas de pas. Le canal vient du header2 de la voie
(0..15), et non plus de 7+index. Les releases restent attachées au message
accepté, même si le menu ou la sélection change.

Preuves : test_midi_lane_track_setup.py, test_midi_lane_keyboard.py et
render_midi_bank.py --track-setup. Testé sur Model:Cycles par AveyCole le 12/10/2026 : affichage et commandes confirmés fonctionnels.
