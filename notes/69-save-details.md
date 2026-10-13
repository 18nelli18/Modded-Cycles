# Test3 : précision des échecs de sauvegarde

Build2026-10-12-test-3-tg-save-details. Model-TG, catalogue et moteurs conservés ; principal inchangé. Suite aux résultats matériels INIT puis CREATE après chargement d’un projet : séparer les gardes IRQ, LOADING, CONTEXT, BANK et SLOT ; séparer la création en BUFFERS, LOOKUP A, LOOKUP B et GUARD.

Correction : ne plus tenter la création initiale lorsqu’un writer de renouvellement a déjà échoué. Son erreur OPEN/ALLOC/WRITE/FLUSH/CLOSE doit rester visible. La preuve injecte une erreur WRITE et vérifie le code17 conservé. Les24messages sont testés sur le code placé ; contexte absent et chargement actif ont des erreurs distinctes. Save/Load complet, récupération, migrations et working96 passent en simulation ; build navigateur avec/sansUSB6 et transfert684blocs vérifiés.

Un changement de projet bloquant l’ouverture B a été signalé. La garde load_ready empêche l’exposition de données du projet précédent après un Load échoué. Aucun contournement de cette garde dans ce candidat ; contexte exact du changement à confirmer. Persistance matérielle encore non validée. Quick assign LFO2 encore absent.
