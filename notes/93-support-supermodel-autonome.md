# 93 — Support Supermodel autonome, sans sampler Model-TG

Le 14 octobre 2026, A.V. annule WAVE et demande de reprendre la séparation des
fonctions propres de Supermodel. Les éditions main et909 restent inchangées.
Adresses : VA de l’OS1.13.

## Source locale

Les modules nécessaires au noyau performance sont maintenant dans
`tools/machines/supermodel_support/performance_modules.s`, MIT TinyGregAudio,
commit `70b39dd6787770ebefc7a2d78dea1678ec012679`, licence et empreinte jointes.
Le constructeur n’exige plus de clone TG. Les anciennes cibles servent seulement
au remplacement des références par les symboles du support local.
Le noyau compilé fait5862 octets ; aucun sampler, effet master ou service disque.

## Profils sans Banque

Huit profils selon Genie, SCRAMBLE et ChordKeys. LFO2 reste son mod natif.
Le support relie les accroches clavier et compteur audio, menus, slides et Scale Lock.
ChordKeys est relogé après le bloc privé du support. Un ou deux blocs cache privés.
Le chargement des127 combinaisons moteurs sans TG mène au même bootstrap propre.
Les cartes restent indépendantes ; Select All évite TG et ses options sampler.
Un TG explicitement sélectionné garde la chaîne main précédente.

## Validation

Boot/clear/cache natifs, cinq gammes × douze tonalités ×128 notes, combo slides et
PCM des six machines stock exact ; rampe des slides identique à la référence.
SCRAMBLE : constructeur, quatre locks, marques, retrait et combo natifs sur six machines.
Genie s’ouvre via le dispatcher propre. Chord : 96 touches/releases, vrais getters,
ABI, PCM avec Keys OFF et rendu actif ; tous sans sampler ni code Banque.
Profils du navigateur : core, Genie, Genie+SCRAMBLE, +LFO2, +Chord et Select All sans TG :
images Python/navigateur identiques, décompression, clear et cache natifs réussis.
TG facultatif conserve sa construction signée. Références strictes toujours actives.

La compilation indépendante de la Banque a aussi passé notes/releases, génération
isolée B et scheduler simulé, sans sampler. Elle reste hors de cette page main copiée
et n’est pas promue dans l’édition909.

## Limites

Expérimental. MOVEC/cache physique, périphériques et cycle de vie complet non simulés.
Les résultats précédents d’écran blanc ne sont pas déclarés corrigés ; ce test
sans Banque doit être essayé sur machine avant promotion. Les options liées au
sampler et les autres conflits réels de dispatch restent protégés.

## Testé sur machine le14/10/2026

A.V. : « That seems to work, publish it to main. » Le support sans Banque est
promu sur demande utilisateur ; la réintégration Banque reste un test séparé.
