import json, sys
pc={int(k,16):v/3 for k,v in json.load(open(sys.argv[1] if len(sys.argv)>1 else 'pc_silence.json')).items()}
def s(lo,hi): return sum(v for a,v in pc.items() if lo<=a<hi)
def it(a): return pc.get(a,0)
L=[
 ("vel gain: boucle 6 pistes x 32", 0x40056d9c,0x40056dfe),
 ("vol+dist: cibles dist 6 pistes", 0x40056f58,0x40056f9a),
 ("vol+dist: lissage gains", 0x40056f9a,0x40056fe8),
 ("vol+dist: préparation paire", 0x40056fe8,0x40057084),
 ("vol+dist: SATURATEUR 32 trames x 2 pistes", 0x40057084,0x40057100),
 ("vol+dist: dry/wet 2 pistes", 0x40057100,0x400571c4),
 ("vol+dist: FONDU dry/wet 32 x 2", 0x400571c4,0x400571f4),
 ("vol+dist: fin", 0x400571f4,0x4005725e),
 ("delay: préparation", 0x40057488,0x4005753e),
 ("delay: boucle 1 (2 prises, fondu, saturation douce)", 0x4005753e,0x4005759a),
 ("delay: boucle 2 (filtre)", 0x4005759a,0x40057624),
 ("delay: boucle 3 (sortie, contre-réaction)", 0x40057624,0x40057688),
 ("delay: boucle 4 (entrée + écriture ligne)", 0x40057688,0x4005770e),
 ("reverb: préparation", 0x400579c4,0x40057aa0),
 ("reverb: 0x40057aa0 (8 x 4)", 0x40057aa0,0x40057ac8),
 ("reverb: 0x40057b08 boucle 32", 0x40057ac8,0x40057b3c),
 ("reverb: 0x40057b4c 8 lignes x 32 (passe-tout)", 0x40057b3c,0x40057b96),
 ("reverb: 0x40057bc8 boucle 32 (A)", 0x40057b96,0x40057bfc),
 ("reverb: 0x40057c28 boucle 32 (B)", 0x40057bfc,0x40057c6a),
 ("reverb: 0x40057c9c boucle 32 (C)", 0x40057c6a,0x40057cec),
 ("reverb: 0x40057d12 boucle 32 (D, 4 lignes)", 0x40057cec,0x40057d72),
 ("reverb: 0x40057df2 boucle 32 (A')", 0x40057d72,0x40057e26),
 ("reverb: 0x40057e52 boucle 32 (B')", 0x40057e26,0x40057e94),
 ("reverb: 0x40057ec6 boucle 32 (C')", 0x40057e94,0x40057f20),
 ("reverb: 0x40057f3e boucle 32 (D')", 0x40057f20,0x40057fa8),
 ("mix: 0x4005802e dma ch30", 0x4005802e,0x400582c4),
 ("mix: gains 6 pistes", 0x400567ba,0x40056940),
 ("mix: loi de pan 0x40056524", 0x40056524,0x4005654a),
 ("mix: envois delay (2 appels)", 0x40056716,0x4005678a),
 ("mix: attente dma", 0x4005697e,0x4005698c),
 ("mix: entre delay et envois reverb", 0x400569a2,0x40056a36),
 ("mix: envois reverb (2 appels)", 0x40056698,0x40056716),
 ("mix: désentrelace (6 appels)", 0x400567a4,0x400567ba),
 ("mix: gains retours fx + mutes", 0x40056a42,0x40056ac8),
 ("mix: entre", 0x40056ac8,0x40056b38),
 ("mix: master 8 entrées (2 appels)", 0x40056610,0x40056698),
 ("mix: gain x4", 0x400565c6,0x40056610),
 ("mix: copie entrée USB -> ba90", 0x40056b38,0x40056b78),
 ("mix: variante A (vol courant)", 0x40056b78,0x40056c1e),
 ("mix: variante B (vol nouveau)", 0x40056c1e,0x40056c66),
 ("mix: passages par zéro", 0x40056c66,0x40056cc6),
 ("mix: choix A/B + bornes -> anneau (non caché)", 0x40056cc6,0x40056d58),
 ("mix: copie master -> USB 0x40fe4b90", 0x40056d58,0x40056d9c),
]
tot=0
for n,lo,hi in L:
    v=s(lo,hi); tot+=v
    print(f"{n:52s} {v:7.0f}")
print('total', tot)
