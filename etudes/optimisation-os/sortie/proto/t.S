	.text
	mvs.w 66(%a1),%d0
	tst.l (0,%a1,%d7.l)
	mac.l %d0,%d1,%acc0
