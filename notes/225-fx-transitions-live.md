# 225 — FX et changements de pattern pendant lecture (05/11/2026)

Retour utilisateur sur3.06 : Save Project ne suffit pas, Reverb reste actif
et le resultat change selon le sens de navigation. L'utilisateur confirme que
le cas concerne les changements pendant lecture.

## Cause reproduite

Le test precedent passait par le raccord d'activation a l'arret et imposait
ensuite `mf_sync_audio`. Le raccord live `sg_live_switch` publiait le pattern
et notifiait Song, sans appeler `fxs_change`. L'audio pouvait donc appliquer
la banque MFT du nouveau pattern alors que la banque native FX suivait encore
l'ancien. Au prochain service UI, `store_current` enregistrait les FX du
nouveau pattern dans l'ancien. Le retour dans l'autre sens restaurait alors
ces valeurs erronees. Le test3.06 echoue exactement au retour sur B : Chorus
est actif alors que Reverb est attendu.

## Correctif prive3.83

`fx-live383.S` accroche le raccord live existant : sous masque IRQ, capturer
et appliquer la banque native FX avant publication, appeler le raccord Song
original, puis synchroniser MFT avant retour a l'audio. Aucun fichier,
allocation ou service UI n'est ajoute dans l'ISR. Registres, pile, niveau IPL,
X et CCR du MOVE de publication sont conserves.

Le code occupe la fin libre `467a0e00..467a0f00` de la reservation de vue
Global compacte. Le generateur controle la fin effective de cette vue, les
zeros disponibles, les six octets du MOVE original, la taille et les cibles
issues de `nm`. Aucune SRAM audio n'est modifiee. Generateur :
`tools/fx_live383.py`, option `rebuild300_pack.py --fx-live383`.

## Validation et limites

`test_fx_live383.py` execute le vrai raccord live installe, deux ordres
audio/UI, les deux sens, des repetitions du meme pattern et les deux slots
FX. Il verifie que la requete de changement reste differee avant frontiere,
les registres, IPL/CCR lus par MOVE SR reel, puis Save/Load Project dans une
nouvelle instance et de nouveaux changements en lecture.20frontieres par
edition passent pour Main/Optional Full/Lite, apres vrai bootstrap.

L'ancien firmware3.06 echoue dans cette preuve. Les E/S disque et certaines
frontieres de presentation restent simulees ; aucun resultat appareil n'est
annonce. Des valeurs erronees peuvent deja etre inscrites dans les anciennes
banques : rechoisir les effets voulus puis Save Project avant le test.

Livraison privee : `../fx-live383/delivery`.3.06 public reste inchange ; aucun
flash, push ou changement des flasheurs pour ce correctif avant retour du test.

## Publication sans changement de version

L utilisateur demande explicitement de pousser ce correctif en conservant
3.06. Les quatre images publiques gardent3.06 au demarrage ; seuls les SHA
et stamps de cache changent. Les recettes Optional/MD sont rebasees sur
les nouveaux socles et les notes3.06 sont completees sans doublon.
