# 147 — Ordre TINY et demarrage Formula de Feral

Demande AveyCole du22/10/2026 : TINY avant MIDI Out, puis Feral muet au defaut et par endroits Color. Adresses : VA OS1.13.

## Reponse courte

[FAIT] v44 change seulement l’ordre de menu0..16,18,17 ; IDs sauvegardes inchanges. Le vrai increment4001488a et les19reperes sont verifies,133cas par variante. AveyCole confirme « i tested v44, it worked ».

[FAIT en emulation] Formula0 produit une constante au Color64 apres reset ; le bloqueur DC laisse un clic decroissant. Une mesure de crete seule ne prouvait donc pas un son soutenu. L’audit isole maintenant le generateur467d5412 avant ampli/DC. Au depart0, plusieurs groupes Color sont constants ;1234567 rend actifs les groupes sauf10, lequel utilise0. Un seul reset natif467d569c est detourne ; une entree suit le groupe de formule pour redemarrer lors de son changement. Seizeformules et dixmodeles restent. Etat prive dans les huitoctets inutilises de l’union Formula apres temps/phase ; aucun nouveau parcours par sample.

Les128positions Color au defaut produisent une onde variable en v45/v45nf. Cela ne prouve pas chaque combinaison de hauteur, Const et enveloppe. Source originale Glycinate conservee, main fixe pendant ce test. AveyCole rapporte « feral no longer silent at startup in45 ». Le changement est ensuite inclus dans le v46 approuve pour publication.
