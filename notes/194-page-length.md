# 194 — Page Len et trigs inactifs eteints

Demande AveyCole (27/10/2026) : longueur1–16 commune aux pages dans Page
Setup, sur la base191 complete. Retour materiel193 : les pads inactifs
clignotent ; utiliser OFF plutot que le mode blink. Promotion194 autorisee
par « Push to main, make sure the file size thing doesn't happen again ».

## En bref

FUNC + PAGE, Page Len, appui DATA puis rotation. Valeur par pattern, defaut16.
Le span Len reste physique (64 = quatre pages) ; les pas hors de Page Len
ne consomment pas de temps et restent stockes. Une derniere page partielle
s'arrete a Len. Les25 choix de machines, SPEAK et Feral inclus, restent.

## Implementation

`tools/page193_assets.py`, `tools/machines/page193/` ; generateur cumulatif
`--page-dark`. Code dans468f7000..468fa000, reservation existante verifiee
vide, pas de nouvelle reservation RAM. Compteur natif40055344 saute les
positions inutilisees, limite maitre commune40055442 suit le nombre de pas
actifs. Timers, sous-pas, files et timestamps natifs conserves.

Tag PL/longueur/complement dans les quatre derniers octets reserves de
l'en-tete64octets (pattern+30702..30705). Le codec exporte les64octets ;
decodeur4005b3b4 valide ce tag et reprend16 sans tag valide. Init40061526
reinitialise le champ. Save/load/copy de pattern restent natifs, aucun
fichier auxiliaire. L'ancien firmware ignore le tag.

Ligne MenuItem native ajoutee avant le constructeur Scale/Key/Lock existant.
Le callback LED4002fd38 revendique les16pads avant son delegue, seulement
quand Page Len est selectionne. L'API booleenne native40005fe6 donne OFF=1
et ON=2 ;193 utilisait3 a tort pour OFF, ce qui clignotait.

## Preuves et livraison

`[FAIT en emulation]` Les16longueurs x63spans ;288 cas des vrais compteurs
six pistes, modes commun/par piste et retours natifs ; limite maitre,
setter/notificateur natif, codec complet, copies, tags invalides. Vrai
constructeur Page Setup (huit lignes), ABI std::string, handlers et claims
LED.256frames jouent/arret et huit phases : pads inactifs toujours OFF.
Runtime audio, payload hors Page Len et sections non-MAIN identiques a193.

Le principal2.54 sert exactement194 SHA
`da908d5ff722164d1fb8efaf38f508a1197a1a23b73fe27bd6e2c72d0ef4d6e1`.
Les locks avances Estus191 sont inclus ; le profil prive sans SPEAK/Feral
reste exclu. Approbation de publication ne vaut pas nouvelle mesure CPU.

La preparation Samples execute les tests contre **l'image courante de
BUILD.json**, dans les deux transports, puis le vrai bootstrap et les
verifications natives. La garde de non-chevauchement de41 reste active.
`Fixed main firmware delivery` en CI verifie les octets approuves, la
capacite flash et le layout du flux courant a chaque changement du flasheur.
