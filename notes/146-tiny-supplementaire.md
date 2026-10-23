# 146 — TINY supplementaire, dix-neuf machines

Demande AveyCole apres verification publique2.18 le22/10/2026 : remettre TINY comme moteur supplementaire, sans retirer Feral ni aucune machine. Apres essai depuis le dossier source : « that worked, push 43 all features to main ». Adresses : VA OS1.13.

## Reponse courte

[FAIT en emulation] TINY index18 reutilise le DSP original encore resident0x4677c000/0x4677c2f2. Feral reste15, Elder16,MIDI Out17. Aucun changement des numeros existants. v43/v43nf ; principal2.19 approuve. Un changement suivant doit placer TINY avant MIDI Out dans le menu sans renumeroter les projets ; audit Feral suivant demande apres cela.

## 1. Metadonnees

`tools/tiny_extra_assets.py`, option `--tiny-extra`, au-dessus du v42. Nouvelles tables19noms/update/render/vecteurs/map a0x467ea000,136descripteurs a0x467ea200,metadata assemblee a0x467ec000 et carteTINY a0x467ed000. Fin0x467ef000 avant BSS Elder0x467f0000 : padding verifie integralement nul avant utilisation, pas d'extension de reservation RAM.

Les131descripteurs existants sont recopies sans changer les controles actuels ; cinqdescripteurs131..135 reprennent ceux du TINY original v17, Tone/Model/Mod/Excite/Decay. Les14entrees de metadonnees sont regenerees depuis les helpers existants, prologues gardes et instructions entieres. Les voix et regles CPU ne sont pas recompilees. References connues relogees ;40bornes32bits131/130 deviennent136/135 ; troisautres sites conservent leurs wrappers LFO/applicabilite. `ld_api[3]` passe a136 pour les labels nouveaux. Selecteur/dispatch jusqu'a18,19rangees. Les enregistrements et les tables rows/CC ont encore la place requise. Dixcolonnes a6pixels sur deuxlignes :19reperes dans la moitie droite. Carte T originale par le systeme d'initiales existant.

## 2. Preuves

Deuxvariantes : vrai constructeur19rangees, tous noms/IDs/controles existants preserves, labels/controlleurs TINY accessibles, indices>=136 refuses ;19reperes dans64..127, carte native TINY avec statistiques/icone, pile/registres conserves. Image inspectee.

TINY18 vs TINY15 v32 :52modeles,416blocs PCM exacts par variante, tous audibles au reglage de test, retrigs inclus.24blocs sixvoix avec Feral,Elder,Wizard stereo et ChordKeys exacts au v42. Bootstrap natif sans ecrasement. Generateur verifie les sections horsMAIN byte-exactes. Verification physique rapportee par AveyCole, version exacte du fichier essaye non archivee ; pas de pourcentage CPU materiel deduit.

## 3. Publication2.19

Partage :106fe446fdc9a43cd3ea89c241b65ba198ae8a2b347913a4453cf81b1392ac67.
MAIN :20eb3afbef4977f8318cbd21b5f166afab037fcd6918d72d80d9bf30b8b73cf4.
Sanspartage :c6ecba16ade022a6c780aceb511e16946d28d439b5c3dfb24925915c8195cd3b.

Guide EN/FR47lignes et PDF4pages actualises ; les quatrepages rendues/inspectees. Credits conserves. Le navigateur doit telecharger l'image exacte avec OS officiels et refuser une corruption ; controle publique apres push. v42 est conserve comme comparaison. Aucune correction Feral ou reorganisation du menu n'est ajoutee a cette promotion.
