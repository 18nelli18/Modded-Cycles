/* Genere par tools/gen_flasher_tweaks.py depuis tweaks/model-cycles_OS1.13/.
 * NE PAS editer a la main : relance le script apres avoir change un tweak. */
window.MC_TWEAKS = {
 "device": {
  "device": "Model:Cycles",
  "os": "1.13",
  "section_sha256": "cc99d4f0175d34d1e91d046e6ec85a5e8ab58ab9edbb3c24406acd48cb99ee98",
  "stock_syx_sha256": "44fe586269631a0ca7da25a3383fc6733c314809505fc3cc52f1e0ed9800640c"
 },
 "tweaks": [
  {
   "id": "6ch-usbup",
   "order": 11,
   "name": "Sortie multipiste 6 canaux, upgrade USB conserve",
   "description": [
    "Meme sortie 6 canaux que 6ch-multiout : memes stubs, octet pour octet,",
    "mais loges dans la cave 0x4015c044 au lieu des descripteurs USB CDC et MIDI seule.",
    "Cette cave est le masque 0xFF d'un sprite : le sprite est redirige vers un masque",
    "identique (meme rendu), voir tools/sprites.py et notes/14.",
    "Descripteurs et table des modes USB restent d'origine : CONFIG > UPGRADE par USB devrait refonctionner.",
    "Genere par tools/relocate_6ch.py depuis 6ch-multiout (decalage des stubs : -0x3f020).",
    "ATTENTION : jamais flashe. Variante experimentale, voir notes/13."
   ],
   "device": "Model:Cycles",
   "os": "1.13",
   "section": 3,
   "conflicts": [
    "6ch-multiout"
   ],
   "writes": [
    {
     "off": 8507,
     "old": "0f20",
     "new": "0320"
    },
    {
     "off": 8548,
     "old": "9b8021",
     "new": "9e0021"
    },
    {
     "off": 9139,
     "old": "0f24",
     "new": "0724"
    },
    {
     "off": 9166,
     "old": "e788",
     "new": "ed88"
    },
    {
     "off": 9171,
     "old": "30ed8a9480",
     "new": "90ef8ad480"
    },
    {
     "off": 9192,
     "old": "203c0030008072302540000424bcdead0001254100204a",
     "new": "4ef94015c1164e714e714e714e714e714e714e714e714a"
    },
    {
     "off": 9247,
     "old": "0bb2",
     "new": "06b2"
    },
    {
     "off": 9657,
     "old": "0f20",
     "new": "0720"
    },
    {
     "off": 9682,
     "old": "e78ded899285",
     "new": "ed8def89d285"
    },
    {
     "off": 9700,
     "old": "e7882239404a05e8d28020",
     "new": "4ef94015c2244e714e7120"
    },
    {
     "off": 9734,
     "old": "206f002422414281d1c5b0816f122a18528102c522c560f22f",
     "new": "4ef94015c1c04e714e714e714e714e714e714e714e714e712f"
    },
    {
     "off": 9794,
     "old": "721320402004e3ace78843",
     "new": "4ef94015c1624e714e7143"
    },
    {
     "off": 10475,
     "old": "3800",
     "new": "a800"
    },
    {
     "off": 745524,
     "old": "4015c044",
     "new": "40154ae4"
    },
    {
     "off": 1424662,
     "old": "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
     "new": "4e71203c009000802540000424bcdead00017212e789254100204ef9400027fe"
    },
    {
     "off": 1424738,
     "old": "ffffffffffffffffffffffffffffffffffffffffffffffffffff",
     "new": "4e71204020042200e988e789d0812800484442444ef940002a4c"
    },
    {
     "off": 1424832,
     "old": "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
     "new": "4fefffd448d707ff2241781f2c03cc84e2886f000028247c8000185845f26c007e06241202c222c245ea008053876600fff25286cc8453806e00ffdc4cd707ff4fef002c4ef940002a26"
    },
    {
     "off": 1424932,
     "old": "ffffffffffffffffffffffffffffffffffffffffffff",
     "new": "2200e988e789d0812239404a05e8d2804ef9400029ee"
    },
    {
     "off": 1683194,
     "old": "0200",
     "new": "0600"
    },
    {
     "off": 1683335,
     "old": "0200",
     "new": "0600"
    },
    {
     "off": 1683351,
     "old": "3800",
     "new": "a800"
    }
   ]
  },
  {
   "id": "6ch-multiout",
   "order": 10,
   "name": "Sortie multipiste 6 canaux (pistes 1-6)",
   "description": [
    "Chaque piste sort sur son propre canal USB (1..6), 48 kHz / 32 bits, High Speed.",
    "Le mix stereo n'est plus envoye en USB ; melanger les stems dans le DAW.",
    "Portage du travail de scottmetoyer/ms-multi-output (MIT) au format model-tweaks.",
    "ATTENTION : jamais teste sur un vrai Model:Cycles."
   ],
   "device": "Model:Cycles",
   "os": "1.13",
   "section": 3,
   "conflicts": [
    "6ch-usbup"
   ],
   "writes": [
    {
     "off": 8507,
     "old": "0f20",
     "new": "0320"
    },
    {
     "off": 8548,
     "old": "9b8021",
     "new": "9e0021"
    },
    {
     "off": 9139,
     "old": "0f24",
     "new": "0724"
    },
    {
     "off": 9166,
     "old": "e788",
     "new": "ed88"
    },
    {
     "off": 9171,
     "old": "30ed8a9480",
     "new": "90ef8ad480"
    },
    {
     "off": 9192,
     "old": "203c0030008072302540000424bcdead0001254100204a",
     "new": "4ef94019b1364e714e714e714e714e714e714e714e714a"
    },
    {
     "off": 9247,
     "old": "0bb2",
     "new": "06b2"
    },
    {
     "off": 9657,
     "old": "0f20",
     "new": "0720"
    },
    {
     "off": 9682,
     "old": "e78ded899285",
     "new": "ed8def89d285"
    },
    {
     "off": 9700,
     "old": "e7882239404a05e8d28020",
     "new": "4ef94019b2444e714e7120"
    },
    {
     "off": 9734,
     "old": "206f002422414281d1c5b0816f122a18528102c522c560f22f",
     "new": "4ef94019b1e04e714e714e714e714e714e714e714e714e712f"
    },
    {
     "off": 9794,
     "old": "721320402004e3ace78843",
     "new": "4ef94019b1824e714e7143"
    },
    {
     "off": 10475,
     "old": "3800",
     "new": "a800"
    },
    {
     "off": 1302855,
     "old": "3f00",
     "new": "b600"
    },
    {
     "off": 1302858,
     "old": "006500",
     "new": "014800"
    },
    {
     "off": 1302894,
     "old": "b1da00",
     "new": "b2b600"
    },
    {
     "off": 1302898,
     "old": "006500",
     "new": "014800"
    },
    {
     "off": 1302934,
     "old": "b17d00",
     "new": "b2b600"
    },
    {
     "off": 1302938,
     "old": "004b00",
     "new": "014800"
    },
    {
     "off": 1302974,
     "old": "b13200",
     "new": "b2b600"
    },
    {
     "off": 1302978,
     "old": "004b00",
     "new": "014800"
    },
    {
     "off": 1682742,
     "old": "020100c003080b00020201010209040000",
     "new": "4e71203c009000802540000424bcdead00"
    },
    {
     "off": 1682760,
     "old": "020201020524001001042402000524",
     "new": "7212e789254100204ef9400027fe24"
    },
    {
     "off": 1682818,
     "old": "0100c003080b000202010102090400000102020102052400100104",
     "new": "4e71204020042200e988e789d0812800484442444ef940002a4c04"
    },
    {
     "off": 1682912,
     "old": "00c003090400000001010000092401000109000101090401000201030000072401000141000624020101000624020202000924030103010201000924030204010101000905010200020000",
     "new": "4fefffd448d707ff2241781f2c03cc84e2886f000028247c8000185845f26c007e06241202c222c245ea008053876600fff25286cc8453806e00ffdc4cd707ff4fef002c4ef940002a2600"
    },
    {
     "off": 1683012,
     "old": "0100c00309040000000101000009240100010900010109",
     "new": "2200e988e789d0812239404a05e8d2804ef9400029ee09"
    },
    {
     "off": 1683194,
     "old": "0200",
     "new": "0600"
    },
    {
     "off": 1683335,
     "old": "0200",
     "new": "0600"
    },
    {
     "off": 1683351,
     "old": "3800",
     "new": "a800"
    }
   ]
  },
  {
   "id": "sdvintage-snare",
   "order": 20,
   "name": "Machine SD VINTAGE a la place de SNARE (etape 1)",
   "description": [
    "Remplace le moteur de la machine SNARE par SD VINTAGE : caisse claire vintage",
    "(corps a 2 modes accordes + balayage de hauteur, bruit snappy filtre), clean-room.",
    "PITCH accord | DECAY longueur | COLOR snappy (bruit) | SHAPE brillance du bruit |",
    "SWEEP balayage du corps | CONTOUR duree du corps. PUNCH, GATE, LFO : comme d'origine.",
    "Code compile depuis tools/machines/sdvintage (828 o @ 0x4016cae8, 560 o @ 0x4018a788), dans deux masques de",
    "sprites liberes (tools/sprites.py). Defauts SNARE adaptes : COLOR 60, SHAPE 64, SWEEP 40, CONTOUR 40.",
    "ATTENTION : jamais flashe. Etape 1 = validation sur materiel, voir notes/14."
   ],
   "device": "Model:Cycles",
   "os": "1.13",
   "section": 3,
   "writes": [
    {
     "off": 708010,
     "old": "4018a788",
     "new": "40154ae4"
    },
    {
     "off": 724230,
     "old": "4016cae8",
     "new": "40154ae4"
    },
    {
     "off": 1106968,
     "old": "00000000",
     "new": "00003c00"
    },
    {
     "off": 1107024,
     "old": "00007f00",
     "new": "00004000"
    },
    {
     "off": 1107080,
     "old": "00000800",
     "new": "00002800"
    },
    {
     "off": 1107136,
     "old": "00000000",
     "new": "00002800"
    },
    {
     "off": 1147412,
     "old": "400ab6e8",
     "new": "4018a788"
    },
    {
     "off": 1147436,
     "old": "400ab3b0",
     "new": "4016cae8"
    },
    {
     "off": 1492712,
     "old": "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
     "new": "4fefffe848d70c3c246f0024206f0020736a001a0c8100007f006f08223c00007f0060064a816c024281756a0016302a001c0c8200007f006f08243c00007f0060064a826c024282776a00180c8300007f006f08263c00007f0060064a836c024283792a00244a846c024284e58c227c4012228cd3c421510250226800384a89670000d2203c01f10e1d2a3c001f7c5c21400278267c4012268c21400274203c7fffffff21450284214502802a3c83e21c3a2140029421400290203c803ef8b82145027c21400288d7c4215302484a6a001e6616267c200000004285203c7fffffff283cc028db9c6014267c7fffffff7a01203c40000000283c80000000214500482a3c7fffffff214402b8283c400000002140029c214b02a0214002a442a800702144007421450084214500802145008842a8009c42a8009842a8009442a800904aa8008c6662203c2545f4912140008c605671402a2800840c8000007f006f08203c00007f0060064a806c024280e080267c4012228c2800e78c9880e88420334c384480a0050800a1c07a0b2801eaa4214000842028008828334c204484a8000800a1c021400088716a0022796a00140680ffffc000e788e18cd0840680ffc00000d0af001c0c80007f00006f06707f484060064a806c0242800680ffb60000283c0aaaaaaba8000800a1c07a0f2800eba8484448c42a3c09e79bdb02807fff8000a0050800a1c506851d0c5fa9a0050800a1c506855903d9d4a0050800a1c0e2802a3c0258bf26068040000000aa000800a1c0d0804a846d04e9a860044484e8a0283c000102044c041800a2010800a1c1283c46666666a8010800a1c128280088a8010800a1c1a2000800a1c12a3c7fffffff9a80e485283c7fffffffb2856e06e5892801d8802144007c4a896704214400782a3c000102044c052800214200a4a4020800a1c2203c39999999a0020800a1c2203c7fffffff720b9082214000a074142003e2a0e5ab43f94016cde022310c0020310c04908102837ff00000a6000800a1c04cd70c3cd280214100a84fef00184e75129b499f157332b118ad3dd81c522d1b2069f7b524fb1c692a09c5962f96bf14359e44d63c16bc0442ef772f4a0fb88851563894589987355fa99fd76652f47d6c62fabb"
    },
    {
     "off": 1614728,
     "old": "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
     "new": "4fefffa4206f006448d77cfc226f0060246800782c2800802228007c928a202800849086ea81ea802e2800702a2800742628008c24280090286800942c6800982828009c2f48004c206800a02f4900542f410038223c600000002f4000402f4a00502f4700582f480044226f004c202900a4a2000800a1c7206900a82a6f0054224d2f47004843e900802e2f00582f49003c2f480030224ade89203c4f5c28f6a0090800a1c0721820402007e2a82207d1c9ef89da88e58802817fffff802040d1fc8000eee4246800042f50002c95ef002ca20a0800a1c0223c466666662f400034a2060800a1c1701824412205e0a92005ef88e58902807fffff802041d1fc8000eee422102068000491c1a0080800a1c0d280a4410800a1c1202f002ce281d0af0034e280d081ac000800a1c0222f0044a2000800a1c1203c0019660d4c0038002441200c207c7834793e06833c6ef35f2203e481d48128419480a4080800a1c22202928e202f0030a2000800a1c1ddc1220e9284a2000800a1c1202f0048d881a0040800a1c1e589d3ef0038dcaf0040d28a2ac1bbef003c6600fefc2c2f00382e3c000001d1202f0038206f0058dcaf00504c070800d1ef00502f2f004c2206eb89226f0050d088234500742343008c2369007c007823420090234c0094234e00989286d280234100702344009c45e9007c41e90084235000804eb9400a92522f2f00502f2f005c4eb9400a9430246f00602f4a006c4cef7cfc000c226f00582f4900704fef00684ef9400a967a"
    }
   ]
  }
 ],
 "features": [
  {
   "id": "usb6",
   "label": "Sortie USB 6 canaux separes",
   "desc": "Chaque piste sort sur son propre canal USB (48 kHz / 32 bits). Le mix stereo n'est plus envoye en USB : tu melanges les 6 pistes dans ton logiciel.",
   "variants": [
    {
     "id": "6ch-usbup",
     "label": "Garder la mise a jour de l'OS par USB (recommande)"
    },
    {
     "id": "6ch-multiout",
     "label": "Version de reference (la mise a jour par USB ne marche plus)"
    }
   ]
  },
  {
   "id": "sdvintage",
   "label": "Machine SD VINTAGE (caisse claire vintage)",
   "desc": "Ajoute un moteur de caisse claire facon Syntakt, a la place de la machine SNARE. PITCH l'accord, DECAY la longueur, COLOR le cote claquant, SHAPE la brillance, SWEEP le balayage, CONTOUR la duree du corps.",
   "variants": [
    {
     "id": "sdvintage-snare",
     "label": null
    }
   ]
  }
 ]
};
