/* Sortie MIDI sans gel (notes/79). Masque 27x27 libéré 0x4014a890 (tools/gen_midi_out_fix.py).

   0x40001232 range un octet pour la sortie MIDI (DIN). Quand un message part déjà (0x4049dca0 non nul), l'octet va
   dans l'anneau de 1 Kio *0x4049dcac ; s'il est plein (0x4049dccc > 1023), l'OS attend en 0x4000123a..0x40001246
   qu'une place se libère. Seule l'interruption de la liaison série le vide (0x40000e8c, source 53 du contrôleur
   d'interruptions 1, niveau 4 : 0x40001522) : appelée à un niveau d'interruption de 4 ou plus (le top d'horloge MIDI
   0x4005420c), l'attente ne finit jamais et tout se fige, son compris.

   Ici : la même attente tant qu'elle peut finir (niveau de 0 à 3 : à l'arrêt de l'interface, comme d'origine) ; au
   niveau 4 ou plus, l'octet est jeté (sortie sans rien ranger, le SR n'a pas encore été touché). Identique à l'OS
   d'origine dans tous les cas où celui-ci revient.

   Détour : 0x4000123a  move.l 0x4049dccc,%d0  (6 o)  ->  jmp ring_wait
   Contrat : d1 = l'octet (gardé), d2 et d3 sauvés par 0x40001232 ; d0 libre (rechargé après 0x40001248), comme
   d'origine il vaut le compte de l'anneau en 0x40001248. */
	.equ	RING_COUNT, 0x4049dccc
	.text
	.globl	ring_wait
ring_wait:
1:	move.l	RING_COUNT, %d0
	cmpi.l	#1023, %d0
	ble.s	2f			/* une place : la suite de l'OS */
	move.w	%sr, %d0
	andi.l	#0x0700, %d0
	cmpi.l	#0x0300, %d0
	bls.s	1b			/* niveau 0 à 3 : l'interruption de niveau 4 videra l'anneau, on attend */
	.globl	ring_drop
ring_drop:
	jmp	0x400012c6		/* niveau 4 ou plus : elle ne le peut pas, l'octet est jeté */
2:	jmp	0x40001248
