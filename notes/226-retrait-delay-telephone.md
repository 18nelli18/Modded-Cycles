# 226 — Retrait du delay telephone

Demande utilisateur du6novembre2026 : retirer ce delay des quatre editions, conserver Control All Config et retirer les credits visibles. Les notices de licence du code conserve restent intactes. Version publique conservee :3.06.

[FAIT] Sept choix : Phaser, Duck, Dub, Ping Pong, Delay, Crush1, Crush2. Les anciens ID12 sont convertis en Delay standard dans la capture et l application des banques ; les autres choix et parametres sont conserves. Le format MFT1 reste lisible. Le noyau DSP et ses tables sont effaces, reset devient RTS ; le buffer commun reste reserve pour Echo.

[FAIT en emulation] Les quatre editions demarrent, parcourent les sept choix dans les deux sens et dessinent les deux chemins overlay. Les anciens fichiers MFT1 avec ID12 sont recharges sans perdre les autres patterns.20raccords live par edition, sauvegarde/relecture native, registres et SR conserves. Aucun nouveau resultat appareil.

Module : `tools/remove_delay384.py`, zone retiree0x46705860..0x46707870. Les remplacements controlent les octets de la reference3.06 ; seules les fonctions de menu, runtime/capture et le noyau retire changent. Les banques et SRAM ne sont pas deplacees. Preuve : `tools/emu/test_remove_delay384.py`. Guides EN/FR et PDF36/9pages regeneres et controles.
