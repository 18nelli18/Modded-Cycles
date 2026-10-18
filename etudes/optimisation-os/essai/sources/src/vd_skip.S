/* Prototype 1 — Volume + Dist (0x40056f58) : ne plus calculer le saturateur d'une paire de pistes quand sa part
   « wet » est nulle du début à la fin du bloc. Son identique : le fondu dry/wet (0x400571c4) multiplie la sortie
   du saturateur par ce wet (0x40a78c2c.. en début de bloc, pente vers le nouveau) ; s'il vaut 0 aux deux bouts,
   la contribution est exactement 0 et les tampons 0x8000bc98 / 0x8000bd18 (lus seulement par ce fondu) n'ont
   pas besoin d'être réécrits.
   Wet nul = VOL+DIST lissé <= 60 (15 360 en 8.8, test de 0x4005710a) sur les deux pistes, ET wet du bloc précédent
   nul (0x40a78c2c + 8p, 0x40a78c30 + 8p, écrits en fin de paire par 0x4005721e / 0x40057218).

   Détour : 0x40057062  movea.l 56(%sp),%a4 ; movea.l 64(%sp),%a0   (8 o)  ->  jmp vd_check ; nop
   Contrat : d7 = 8 x paire, sp inchangé (les cases sp@(44..112) de 0x40056f58 restent valables) ; libres ici :
   d0-d4, a1-a3 (rechargés avant usage) ; acc2 est vidé par 0x40057100 dans les deux chemins. */
	.equ	WET_OLD, 0x40a78c2c
	.text
	.globl	vd_check
vd_check:
	lea	WET_OLD,%a1
	tst.l	(0,%a1,%d7.l)
	bne.s	1f
	tst.l	(4,%a1,%d7.l)
	bne.s	1f
	movea.l	60(%sp),%a1		/* VOL+DIST lissé (k 19) de la piste 2p ; +66 : piste 2p+1 */
	mvs.w	(%a1),%d0
	cmpi.l	#15360,%d0
	bgt.s	1f
	mvs.w	66(%a1),%d0
	cmpi.l	#15360,%d0
	bgt.s	1f
	.globl	vd_hit
vd_hit:
	jmp	0x40057100		/* saturateur inutile : directement au calcul dry/wet */
1:	movea.l	56(%sp),%a4		/* les deux instructions déplacées */
	movea.l	64(%sp),%a0
	jmp	0x4005706a
