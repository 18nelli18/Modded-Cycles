/* Genere par tools/gen_flasher_tweaks.py depuis tweaks/model-cycles_OS1.13/.
 * NE PAS editer a la main : relance le script apres avoir change un tweak. */
window.MC_TWEAKS = {
 "device": {
  "device": "Model:Cycles",
  "os": "1.13",
  "section_sha256": "cc99d4f0175d34d1e91d046e6ec85a5e8ab58ab9edbb3c24406acd48cb99ee98",
  "stock_syx_sha256": "44fe586269631a0ca7da25a3383fc6733c314809505fc3cc52f1e0ed9800640c",
  "cave_refs_ok": [
   {
    "ref": "0x40148564",
    "lo": "0x401485f0",
    "hi": "0x4014862e",
    "why": "pointeur vers la table caractere -> glyphe (256 x 16 bits, 0xFFFF = pas de glyphe) de la petite police de chiffres (0-9 % . /) ; les entrees des caracteres de controle 1..31 ne sont jamais dessinees (largeur 0 dans la table 0x401487ee). browser-scroll (drumkilla) y ecrit 16 o."
   }
  ]
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
   "id": "latching-mute",
   "order": 1,
   "name": "Latching track mute",
   "description": [
    "Hold TRK and tap FUNC: the mute mode latches and the FUNC key lights up.",
    "A short tap on FUNC alone leaves the mode.",
    "No FUNC combination drops it any more, including holding FUNC to turn the encoders fast.",
    "TRK, RETRIG and PATTERN bank select keep working while the mode is latched."
   ],
   "device": "Model:Cycles",
   "os": "1.13",
   "section": 3,
   "writes": [
    {
     "off": 143265,
     "old": "b9",
     "new": "f9"
    },
    {
     "off": 143267,
     "old": "0cfaf4",
     "new": "1486c6"
    },
    {
     "off": 143642,
     "old": "2f024eb9400740ca",
     "new": "4ef9401483284e71"
    },
    {
     "off": 1050693,
     "old": "0234b6",
     "new": "148744"
    },
    {
     "off": 1343272,
     "old": "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
     "new": "4eb9400cf9a82f004eb94006bb18588f4a00664e487800014eb94007faf4588f4a806630487800024eb94007faf4588f4a80662e487800034eb94007faf4588f4a80661e487800044eb94007faf4588f4a80660e2f024eb9400740ca4ef9400235224ef94002357e"
    },
    {
     "off": 1344098,
     "old": "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
     "new": "2f0a2f02242f0010246f000c2f024eb94007240c588f7201b280662e2f024eb940072470588f4a0067324eb9401486fc4a8066284e714e714e7120522f0a206800284e90588f420060142f4200102f4a000c241f245f4ef940075f3c7001241f245f4e754879404a8cb848780002487800184eb9400cfaf42f004eb940005f864fef0010201200800100000024804eb9400cfaf44ef9400233a61039401487ed671c1039401487ec6624203940a78e2890b9401487e00c80000004006410487800024eb94007faf4588f4a80670a700113c0401487ed4e754239401487ed70004e752f02242f000c2f024eb94007240c588f7201b0816700003a1039401487ed670000522f024eb9400724a0588f4a0067000042487800014eb94007faf4588f4a8067000030700113c0401487ec600000242f024eb9400724a0588f4a00670000144239401487ec203940a78e2823c0401487e0241f4ef940148662"
    },
    {
     "off": 1344480,
     "old": "ffffffff",
     "new": "00000000"
    },
    {
     "off": 1344492,
     "old": "ffff",
     "new": "0000"
    }
   ]
  },
  {
   "id": "trig-preview",
   "order": 2,
   "name": "Trig preview (TRIG + PAGE)",
   "description": [
    "With the sequencer stopped, hold a step and press PAGE: the step sounds with its own note, length, p-locks and sound-lock.",
    "The page does not turn.",
    "It sounds regardless of the trig condition and probability, and through a muted track. The trig is not erased."
   ],
   "device": "Model:Cycles",
   "os": "1.13",
   "section": 3,
   "writes": [
    {
     "off": 139502,
     "old": "2f034eb9400724a0",
     "new": "4ef9401489fa4e71"
    },
    {
     "off": 1345018,
     "old": "ffff",
     "new": "4fef"
    },
    {
     "off": 1345021,
     "old": "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
     "new": "d448d77cfc202e000c2f004eb9400724a0588f4a0067000158202e000c2f004eb940072490588f4a00660001444eb94005481a4a80660001384eb9400cf9a826402f0b4eb94006b978588f4a00670001202f0b4eb94006bb18588f4a00660001102f0b4eb94006bdfe588f4a00670001004eb9400cf8662f004eb94000eb90588f2f004eb940012412588f2400203940a7887c4a80670000d82840203940a788884a80670000ca2002e3882200e789d081e589d081e389d081e589d0812a4cdbc01c2d02cf70641b4002cf487800012f0b4eb94006b740508f282b01607a0076000704670000542e03de85204dd1c7122802042f0170"
    },
    {
     "off": 1345268,
     "old": "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
     "new": "1140020442a742a72f07203940a788882f002f0c2f024eb9400548ce4fef0018221f204dd1c7114102044a8067000014204072022141000c2f004eb940092116588f52830c83000000206600"
    },
    {
     "off": 1345345,
     "old": "ffffffffffffffffffffffffffffff",
     "new": "9e4a856600000c7a20282b015c6000"
    },
    {
     "off": 1345361,
     "old": "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
     "new": "8c1b4602cf7000154000744cd77cfc4fef002c74014ef940022ff44cd77cfc4fef002c2f034eb9400724a04ef9400224f6"
    }
   ]
  },
  {
   "id": "browser-scroll",
   "order": 3,
   "name": "Scroll long names in the browser",
   "description": [
    "A selected name in the sound/sample/folder browser scrolls left when it does not fit.",
    "About 0.17 s per character, with a ~0.5 s pause at each end. A name that already fits stays put."
   ],
   "device": "Model:Cycles",
   "os": "1.13",
   "section": 3,
   "writes": [
    {
     "off": 676257,
     "old": "07199c",
     "new": "147f22"
    },
    {
     "off": 1342242,
     "old": "ffff",
     "new": "4fef"
    },
    {
     "off": 1342245,
     "old": "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
     "new": "f048d7041c242f0028262f002445f9401485f0204278007200700010186706d280528460f620044840d0812212b081670c248042aa000442aa000c60604eb9400cf9a82f004eb940069b84588f203940a78e28220092aa0008e089674025400008200490836c027000222a0004b280640c4a81670c528125410004602072"
    },
    {
     "off": 1342372,
     "old": "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
     "new": "60027200202a000c52802540000c7603b083650a42aa000c528125410004202a0004d1af00284cd7041c4fef00104ef94007199c"
    },
    {
     "off": 1343984,
     "old": "ffffffffffffffffffffffffffffffff",
     "new": "00000000000000000000000000000000"
    }
   ]
  },
  {
   "id": "sdvintage-exact",
   "order": 21,
   "name": "Vrai moteur SD VINTAGE du Syntakt a la place de SNARE",
   "description": [
    "Le moteur SD VINTAGE du Syntakt (OS 1.41), extrait AU BUILD de TON Syntakt_OS1.41.syx",
    "(21 fonctions, 5200 o de code, avec ses tables), relocalise en SDRAM a 0x43000000",
    "au-dessus du BSS de l'OS Cycles, branche a la place de SNARE par une passerelle (notes/17).",
    "Potards au sens du Syntakt : PITCH=TUNE, COLOR=INHM, SHAPE=FCMP, SWEEP=SWEP, CONTOUR=MENV,",
    "PUNCH=PNCH, GATE, DECAY=DEC ; defauts du Syntakt. Demande : build.py --syntakt Syntakt_OS1.41.syx.",
    "Aucun octet Elektron dans ce fichier : recette de copie et table de relocalisation seulement."
   ],
   "device": "Model:Cycles",
   "os": "1.13",
   "section": 3,
   "conflicts": [
    "sdvintage-snare"
   ],
   "writes": [
    {
     "off": 178,
     "old": "4feffff048d700f0",
     "new": "4ef94016cae84e71"
    },
    {
     "off": 724230,
     "old": "4016cae8",
     "new": "40154ae4"
    },
    {
     "off": 1107024,
     "old": "00007f00",
     "new": "00006e00"
    },
    {
     "off": 1107080,
     "old": "00000800",
     "new": "00004a00"
    },
    {
     "off": 1107136,
     "old": "00000000",
     "new": "00005000"
    },
    {
     "off": 1107192,
     "old": "00002800",
     "new": "00002100"
    },
    {
     "off": 1147412,
     "old": "400ab6e8",
     "new": "43031196"
    },
    {
     "off": 1147436,
     "old": "400ab3b0",
     "new": "43031000"
    },
    {
     "off": 1492712,
     "old": "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
     "new": "41f9401aa14043f943000000203c0000c86422d8538066fa4feffff048d700f04ef9400004ba0000"
    }
   ],
   "append": {
    "at": "0x401aa140",
    "dest": "0x43000000",
    "size": 205200,
    "syntakt": {
     "os": "1.41",
     "syx_sha256": "8e2488f462c4a5656396a895f113bcd415e9900fa8709340dccf45d4cb9ed19e",
     "section": 7,
     "section_sha256": "daf6451cf9587c0b628e901b7bb6b25f4e2633d448c534c0c181dd35ec783bc2"
    },
    "parts": [
     {
      "dest": "0x43000000",
      "syntakt": [
       "0x40002544",
       "0x40008580"
      ]
     },
     {
      "dest": "0x43006100",
      "syntakt": [
       "0x40014980",
       "0x40014b80"
      ]
     },
     {
      "dest": "0x43006400",
      "syntakt": [
       "0x40028438",
       "0x4003a238"
      ]
     },
     {
      "dest": "0x43020000",
      "syntakt": [
       "0x4004f6e0",
       "0x40057670"
      ]
     },
     {
      "dest": "0x43028000",
      "syntakt": [
       "0x40057670",
       "0x4005df10"
      ]
     },
     {
      "dest": "0x43031000",
      "hex": "4fefffe448d77c04247cbdcf77d82a6f0024d5cd220a243c0000031c4c421001286f00282f6f00200018203c534456312441b0ad002c6710720141f9430320042b40002c1181a8004ab94303200066564aad0038670001362c7c43020000267c43028a604eb9430000002d4b056c2f0e4eb94300199c47eb0030588f4dee0708b7fc43028be066dc303c0101243c01010101720123c24303200423c14303200033c043032008200a243c000007084c0208002640d7fc43020000276d00340034222d003827410038276d003c003c4bf9430320041035a8004a81670000aa4a00672042022f0b4eb94300199c588f700172062740003870062741000426801b82a800200aed88720642422440d5fc4303200a15410022356c00140024356c00160026356c00180028356c001a002a356c001c002c356c001e002e302c0020354000307140356c0024003235420034274003ec2f0b4eb94300001a2f4a002c2f4b0028716c00224cef7c0400040680ffffc000e788d0af001c2f4000244fef00204ef943005b304a006700ff784cd77c044fef001c4e752f0a2f02206f000c4ab9430320006720243c0000031c43f943032004202f00100680bdcf77d84c4200004a310800671420080680000000804298b08866fa241f245f4e75223c000007084c0108002440d5fc430200002f0a2f084eb943005f36256a00340038508f60d4"
     }
    ],
    "reloc": [
     [
      "0x43000008",
      "4404f954",
      "43030954"
     ],
     [
      "0x43000014",
      "4404f958",
      "43030958"
     ],
     [
      "0x430000b8",
      "8000a888",
      "4302a888"
     ],
     [
      "0x43001a2a",
      "8000945c",
      "4302945c"
     ],
     [
      "0x43001a38",
      "80004b70",
      "43024b70"
     ],
     [
      "0x43001a50",
      "8000945c",
      "4302945c"
     ],
     [
      "0x43001a5c",
      "80008c60",
      "43028c60"
     ],
     [
      "0x43001ca0",
      "4404f954",
      "43030954"
     ],
     [
      "0x43001cb4",
      "4404f954",
      "43030954"
     ],
     [
      "0x43001cc4",
      "4404f954",
      "43030954"
     ],
     [
      "0x43001cd8",
      "4404f954",
      "43030954"
     ],
     [
      "0x43001ce8",
      "4404f954",
      "43030954"
     ],
     [
      "0x43001cf8",
      "4404f954",
      "43030954"
     ],
     [
      "0x43001d78",
      "40014b7c",
      "430062fc"
     ],
     [
      "0x43001d82",
      "40014980",
      "43006100"
     ],
     [
      "0x43005b42",
      "40004dc6",
      "43002882"
     ],
     [
      "0x43005b4e",
      "40039238",
      "43017200"
     ],
     [
      "0x43005b7c",
      "40039838",
      "43017800"
     ],
     [
      "0x43005b8e",
      "40039638",
      "43017600"
     ],
     [
      "0x43005ba0",
      "40039438",
      "43017400"
     ],
     [
      "0x43005bb6",
      "40039038",
      "43017000"
     ],
     [
      "0x43005bce",
      "40038e38",
      "43016e00"
     ],
     [
      "0x43005be6",
      "40038c38",
      "43016c00"
     ],
     [
      "0x43005c12",
      "4003a038",
      "43018000"
     ],
     [
      "0x43005c1c",
      "40039e38",
      "43017e00"
     ],
     [
      "0x43005c3a",
      "40039c38",
      "43017c00"
     ],
     [
      "0x43005c76",
      "40028438",
      "43006400"
     ],
     [
      "0x43005c92",
      "40038a38",
      "43016a00"
     ],
     [
      "0x43005cae",
      "40038838",
      "43016800"
     ],
     [
      "0x43005dea",
      "800097c8",
      "430297c8"
     ],
     [
      "0x43005dfe",
      "40038638",
      "43016600"
     ],
     [
      "0x43005e06",
      "800097c8",
      "430297c8"
     ],
     [
      "0x43005e28",
      "40038438",
      "43016400"
     ],
     [
      "0x43005e30",
      "8000a484",
      "4302a484"
     ],
     [
      "0x43005e3a",
      "80004b70",
      "43024b70"
     ],
     [
      "0x43005e50",
      "8000a080",
      "4302a080"
     ],
     [
      "0x43005e6c",
      "40039a38",
      "43017a00"
     ],
     [
      "0x43005f14",
      "40003cda",
      "43001796"
     ],
     [
      "0x43005f26",
      "40002596",
      "43000052"
     ],
     [
      "0x43005f4e",
      "40003c0e",
      "430016ca"
     ],
     [
      "0x43005f5a",
      "40003958",
      "43001414"
     ],
     [
      "0x43005f64",
      "4000290e",
      "430003ca"
     ],
     [
      "0x43005f82",
      "40003df2",
      "430018ae"
     ],
     [
      "0x43005f8e",
      "400044e2",
      "43001f9e"
     ],
     [
      "0x43005f9a",
      "40005016",
      "43002ad2"
     ],
     [
      "0x43005fa4",
      "40004e6c",
      "43002928"
     ],
     [
      "0x43005fbe",
      "40004674",
      "43002130"
     ],
     [
      "0x43005fcc",
      "8000945c",
      "4302945c"
     ],
     [
      "0x43005fd6",
      "80009580",
      "43029580"
     ],
     [
      "0x43005fe0",
      "800096a4",
      "430296a4"
     ],
     [
      "0x43005fee",
      "40004cd6",
      "43002792"
     ],
     [
      "0x43006016",
      "400047ea",
      "430022a6"
     ],
     [
      "0x4300601e",
      "40003d42",
      "430017fe"
     ],
     [
      "0x43006028",
      "400045a0",
      "4300205c"
     ]
    ]
   }
  },
  {
   "id": "sdvintage-7th",
   "order": 22,
   "name": "Vrai moteur SD VINTAGE du Syntakt en 7e machine (SDVtg), a cote de SNARE",
   "description": [
    "Le moteur SD VINTAGE du Syntakt (OS 1.41), extrait AU BUILD de TON Syntakt_OS1.41.syx",
    "(21 fonctions, 5200 o de code, avec ses tables), en 7e machine « SDVtg » :",
    "SNARE reste la SNARE d'origine. Potards propres, noms et defauts du Syntakt :",
    "COLOR=INHM (Inharmonicity), SHAPE=FCMP, SWEEP=SWEP (Pitch Sweep), CONTOUR=MENV (Mod Envelope),",
    "DECAY=DEC ; defauts 0 / 110 / 74 / 80 / 33. Menu MACHINES, machine locks et CC 70 (valeur 6).",
    "Table des descripteurs recopiee en SDRAM avec 5 entrees de plus (notes/18).",
    "Demande build.py --syntakt Syntakt_OS1.41.syx. Aucun octet Elektron dans ce fichier."
   ],
   "device": "Model:Cycles",
   "os": "1.13",
   "section": 3,
   "conflicts": [
    "sdvintage-snare",
    "sdvintage-exact"
   ],
   "writes": [
    {
     "off": 178,
     "old": "4feffff048d700f0",
     "new": "4ef94016cae84e71"
    },
    {
     "off": 42302,
     "old": "744c",
     "new": "7451"
    },
    {
     "off": 42318,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 42334,
     "old": "744c",
     "new": "7451"
    },
    {
     "off": 42372,
     "old": "704b",
     "new": "7050"
    },
    {
     "off": 42578,
     "old": "704b",
     "new": "7050"
    },
    {
     "off": 44552,
     "old": "724c",
     "new": "7251"
    },
    {
     "off": 44564,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 44586,
     "old": "724c",
     "new": "7251"
    },
    {
     "off": 44598,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 45028,
     "old": "724c",
     "new": "7251"
    },
    {
     "off": 45036,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 45174,
     "old": "724c",
     "new": "7251"
    },
    {
     "off": 45182,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 45338,
     "old": "724c",
     "new": "7251"
    },
    {
     "off": 45346,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 45658,
     "old": "724c",
     "new": "7251"
    },
    {
     "off": 45666,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 45804,
     "old": "724c",
     "new": "7251"
    },
    {
     "off": 45812,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 45960,
     "old": "724c",
     "new": "7251"
    },
    {
     "off": 45968,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 46406,
     "old": "704b",
     "new": "7050"
    },
    {
     "off": 82852,
     "old": "7005",
     "new": "7006"
    },
    {
     "off": 111260,
     "old": "7005",
     "new": "7001"
    },
    {
     "off": 119266,
     "old": "724c",
     "new": "7251"
    },
    {
     "off": 119278,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 120046,
     "old": "704b",
     "new": "7050"
    },
    {
     "off": 120066,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 120078,
     "old": "704b",
     "new": "7050"
    },
    {
     "off": 121894,
     "old": "724c",
     "new": "7251"
    },
    {
     "off": 121906,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 126758,
     "old": "704c",
     "new": "7051"
    },
    {
     "off": 126766,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 140924,
     "old": "704c",
     "new": "7051"
    },
    {
     "off": 140932,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 141054,
     "old": "724c",
     "new": "7251"
    },
    {
     "off": 141062,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 170616,
     "old": "744c",
     "new": "7451"
    },
    {
     "off": 170632,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 170648,
     "old": "744c",
     "new": "7451"
    },
    {
     "off": 176176,
     "old": "724c",
     "new": "7251"
    },
    {
     "off": 176184,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 289116,
     "old": "724c",
     "new": "7251"
    },
    {
     "off": 289124,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 318272,
     "old": "704c222f0004",
     "new": "4ef943033016"
    },
    {
     "off": 318370,
     "old": "704c222f0004",
     "new": "4ef94303302a"
    },
    {
     "off": 319262,
     "old": "704b",
     "new": "7050"
    },
    {
     "off": 319278,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 319418,
     "old": "704c",
     "new": "7051"
    },
    {
     "off": 368312,
     "old": "487800c0",
     "new": "487800e0"
    },
    {
     "off": 368318,
     "old": "40a79418",
     "new": "43035200"
    },
    {
     "off": 368350,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 368418,
     "old": "40a79418",
     "new": "43035200"
    },
    {
     "off": 368448,
     "old": "7005",
     "new": "7006"
    },
    {
     "off": 368488,
     "old": "704c",
     "new": "7051"
    },
    {
     "off": 368528,
     "old": "40a79418",
     "new": "43035200"
    },
    {
     "off": 368554,
     "old": "40a7ada4",
     "new": "43035300"
    },
    {
     "off": 368872,
     "old": "724c",
     "new": "7251"
    },
    {
     "off": 368884,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 368906,
     "old": "724c",
     "new": "7251"
    },
    {
     "off": 368918,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 368940,
     "old": "724c",
     "new": "7251"
    },
    {
     "off": 368952,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 368982,
     "old": "724c",
     "new": "7251"
    },
    {
     "off": 368994,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 369010,
     "old": "7205",
     "new": "7206"
    },
    {
     "off": 369026,
     "old": "724b",
     "new": "7250"
    },
    {
     "off": 369050,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 369100,
     "old": "724c",
     "new": "7251"
    },
    {
     "off": 369112,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 369150,
     "old": "724c",
     "new": "7251"
    },
    {
     "off": 369162,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 369192,
     "old": "724c",
     "new": "7251"
    },
    {
     "off": 369204,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 369244,
     "old": "704c",
     "new": "7051"
    },
    {
     "off": 369274,
     "old": "4010dce8",
     "new": "43034008"
    },
    {
     "off": 369318,
     "old": "7205",
     "new": "7206"
    },
    {
     "off": 369338,
     "old": "40a79418",
     "new": "43035200"
    },
    {
     "off": 369392,
     "old": "40a79418",
     "new": "43035200"
    },
    {
     "off": 369514,
     "old": "724b",
     "new": "7250"
    },
    {
     "off": 369534,
     "old": "4010dd00",
     "new": "43034020"
    },
    {
     "off": 369546,
     "old": "4010dd00",
     "new": "43034020"
    },
    {
     "off": 369578,
     "old": "724b",
     "new": "7250"
    },
    {
     "off": 369596,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 369616,
     "old": "724c",
     "new": "7251"
    },
    {
     "off": 369628,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 369656,
     "old": "724c",
     "new": "7251"
    },
    {
     "off": 369668,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 369690,
     "old": "724c",
     "new": "7251"
    },
    {
     "off": 369702,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 369724,
     "old": "724c",
     "new": "7251"
    },
    {
     "off": 369736,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 369758,
     "old": "724c",
     "new": "7251"
    },
    {
     "off": 369770,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 369904,
     "old": "7405b4816532",
     "new": "4ef94303305a"
    },
    {
     "off": 369938,
     "old": "40a7ada4",
     "new": "43035300"
    },
    {
     "off": 664032,
     "old": "7005",
     "new": "7006"
    },
    {
     "off": 664084,
     "old": "401177e4",
     "new": "43033800"
    },
    {
     "off": 664120,
     "old": "eb8c48780001",
     "new": "4ef943033078"
    },
    {
     "off": 664296,
     "old": "7006",
     "new": "7007"
    },
    {
     "off": 670886,
     "old": "7005",
     "new": "7001"
    },
    {
     "off": 674244,
     "old": "700541e8000a",
     "new": "4ef9430330d0"
    },
    {
     "off": 674736,
     "old": "7005",
     "new": "7001"
    },
    {
     "off": 686444,
     "old": "40118628",
     "new": "4303381c"
    },
    {
     "off": 686522,
     "old": "7205",
     "new": "7206"
    },
    {
     "off": 686580,
     "old": "7005",
     "new": "7006"
    },
    {
     "off": 686614,
     "old": "40118610",
     "new": "43033838"
    },
    {
     "off": 724230,
     "old": "4016cae8",
     "new": "40154ae4"
    },
    {
     "off": 1147462,
     "old": "00",
     "new": "06"
    },
    {
     "off": 1492712,
     "old": "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
     "new": "41f9401aa14043f943000000203c0000d50022d8538066fa4feffff048d700f04ef9400004ba0000"
    }
   ],
   "append": {
    "at": "0x401aa140",
    "dest": "0x43000000",
    "size": 218112,
    "syntakt": {
     "os": "1.41",
     "syx_sha256": "8e2488f462c4a5656396a895f113bcd415e9900fa8709340dccf45d4cb9ed19e",
     "section": 7,
     "section_sha256": "daf6451cf9587c0b628e901b7bb6b25f4e2633d448c534c0c181dd35ec783bc2"
    },
    "parts": [
     {
      "dest": "0x43000000",
      "syntakt": [
       "0x40002544",
       "0x40008580"
      ]
     },
     {
      "dest": "0x43006100",
      "syntakt": [
       "0x40014980",
       "0x40014b80"
      ]
     },
     {
      "dest": "0x43006400",
      "syntakt": [
       "0x40028438",
       "0x4003a238"
      ]
     },
     {
      "dest": "0x43020000",
      "syntakt": [
       "0x4004f6e0",
       "0x40057670"
      ]
     },
     {
      "dest": "0x43028000",
      "syntakt": [
       "0x40057670",
       "0x4005df10"
      ]
     },
     {
      "dest": "0x43031000",
      "hex": "4fefffe448d77c04247cbdcf77d82a6f0024d5cd220a243c0000031c4c421001286f00282f6f00200018203c534456312441b0ad002c6710720141f9430320042b40002c1181a8004ab94303200066564aad0038670001362c7c43020000267c43028a604eb9430000002d4b056c2f0e4eb94300199c47eb0030588f4dee0708b7fc43028be066dc303c0101243c01010101720123c24303200423c14303200033c043032008200a243c000007084c0208002640d7fc43020000276d00340034222d003827410038276d003c003c4bf9430320041035a8004a81670000aa4a00672042022f0b4eb94300199c588f700172062740003870062741000426801b82a800200aed88720642422440d5fc4303200a15410022356c00140024356c00160026356c00180028356c001a002a356c001c002c356c001e002e302c0020354000307140356c0024003235420034274003ec2f0b4eb94300001a2f4a002c2f4b0028716c00224cef7c0400040680ffffc000e788d0af001c2f4000244fef00204ef943005b304a006700ff784cd77c044fef001c4e752f0a2f02206f000c4ab9430320006720243c0000031c43f943032004202f00100680bdcf77d84c4200004a310800671420080680000000804298b08866fa241f245f4e75223c000007084c0108002440d5fc430200002f0a2f084eb943005f36256a00340038508f60d4"
     },
     {
      "dest": "0x43033000",
      "hex": "724cb081650e7251b081650470004e75721990814e75202f000461e472644c010800068040a717544e75202f000461d072644c010800068040a71768487940a715002f2f000c2f004eb9400ddf604fef000c203c40a715004e757405b481650c7406b480650c4ef94005a8fa4ef94005a9284ef94005a91c28037006b084660278012004e588eb8c988048780001487800174878002045f940071da4227940fe32ccd3c42f092f024e924fef00304878000148780022d8b940fe384c487800602f042f024e924fef00144ef9400a268041e8000a2f082f2e001020026a0270007205b2806c0270014ef9400a4dde"
     },
     {
      "dest": "0x43033800",
      "hex": "401300d8401300dd401300e3401300e940129960401300ee43033854400aa08c400ab3b0400aa49c400aa998400aa7b8400aae8843031000400aa3c4400ab6e8400aa712400aacc2400aa930400ab24c43031196534456746700496e6861726d6f6e6963697479004672657120436f6d706c6578005069746368205377656570004d6f6420456e76656c6f706500494e484d0046434d500053574550004d454e5600"
     },
     {
      "dest": "0x43034000",
      "cycles": [
       "0x4010dce0",
       "0x4010ed80"
      ]
     },
     {
      "dest": "0x430350a0",
      "hex": "000000060000000b0000000000007f0000000000000000000010ffffffffffff0000000000000600000000284303385a4012996f4303388e000000060000000c0000000000007f0000006e00000000000011ffffffffffff000000000000060000000032430338684012996f43033893000000060000000d0000000000007f0000004a00000000000012ffffffffffff00000000000006000000003c430338754012996f43033898000000060000000e0000000000007f0000005000000000000013ffffffffffff000000000000060000000046430338814012996f4303389d00000007000000120000000000007f0000002100000000000050ffff0000009a00000000000006000000001e401298784012988240129886"
     }
    ],
    "reloc": [
     [
      "0x43000008",
      "4404f954",
      "43030954"
     ],
     [
      "0x43000014",
      "4404f958",
      "43030958"
     ],
     [
      "0x430000b8",
      "8000a888",
      "4302a888"
     ],
     [
      "0x43001a2a",
      "8000945c",
      "4302945c"
     ],
     [
      "0x43001a38",
      "80004b70",
      "43024b70"
     ],
     [
      "0x43001a50",
      "8000945c",
      "4302945c"
     ],
     [
      "0x43001a5c",
      "80008c60",
      "43028c60"
     ],
     [
      "0x43001ca0",
      "4404f954",
      "43030954"
     ],
     [
      "0x43001cb4",
      "4404f954",
      "43030954"
     ],
     [
      "0x43001cc4",
      "4404f954",
      "43030954"
     ],
     [
      "0x43001cd8",
      "4404f954",
      "43030954"
     ],
     [
      "0x43001ce8",
      "4404f954",
      "43030954"
     ],
     [
      "0x43001cf8",
      "4404f954",
      "43030954"
     ],
     [
      "0x43001d78",
      "40014b7c",
      "430062fc"
     ],
     [
      "0x43001d82",
      "40014980",
      "43006100"
     ],
     [
      "0x43005b42",
      "40004dc6",
      "43002882"
     ],
     [
      "0x43005b4e",
      "40039238",
      "43017200"
     ],
     [
      "0x43005b7c",
      "40039838",
      "43017800"
     ],
     [
      "0x43005b8e",
      "40039638",
      "43017600"
     ],
     [
      "0x43005ba0",
      "40039438",
      "43017400"
     ],
     [
      "0x43005bb6",
      "40039038",
      "43017000"
     ],
     [
      "0x43005bce",
      "40038e38",
      "43016e00"
     ],
     [
      "0x43005be6",
      "40038c38",
      "43016c00"
     ],
     [
      "0x43005c12",
      "4003a038",
      "43018000"
     ],
     [
      "0x43005c1c",
      "40039e38",
      "43017e00"
     ],
     [
      "0x43005c3a",
      "40039c38",
      "43017c00"
     ],
     [
      "0x43005c76",
      "40028438",
      "43006400"
     ],
     [
      "0x43005c92",
      "40038a38",
      "43016a00"
     ],
     [
      "0x43005cae",
      "40038838",
      "43016800"
     ],
     [
      "0x43005dea",
      "800097c8",
      "430297c8"
     ],
     [
      "0x43005dfe",
      "40038638",
      "43016600"
     ],
     [
      "0x43005e06",
      "800097c8",
      "430297c8"
     ],
     [
      "0x43005e28",
      "40038438",
      "43016400"
     ],
     [
      "0x43005e30",
      "8000a484",
      "4302a484"
     ],
     [
      "0x43005e3a",
      "80004b70",
      "43024b70"
     ],
     [
      "0x43005e50",
      "8000a080",
      "4302a080"
     ],
     [
      "0x43005e6c",
      "40039a38",
      "43017a00"
     ],
     [
      "0x43005f14",
      "40003cda",
      "43001796"
     ],
     [
      "0x43005f26",
      "40002596",
      "43000052"
     ],
     [
      "0x43005f4e",
      "40003c0e",
      "430016ca"
     ],
     [
      "0x43005f5a",
      "40003958",
      "43001414"
     ],
     [
      "0x43005f64",
      "4000290e",
      "430003ca"
     ],
     [
      "0x43005f82",
      "40003df2",
      "430018ae"
     ],
     [
      "0x43005f8e",
      "400044e2",
      "43001f9e"
     ],
     [
      "0x43005f9a",
      "40005016",
      "43002ad2"
     ],
     [
      "0x43005fa4",
      "40004e6c",
      "43002928"
     ],
     [
      "0x43005fbe",
      "40004674",
      "43002130"
     ],
     [
      "0x43005fcc",
      "8000945c",
      "4302945c"
     ],
     [
      "0x43005fd6",
      "80009580",
      "43029580"
     ],
     [
      "0x43005fe0",
      "800096a4",
      "430296a4"
     ],
     [
      "0x43005fee",
      "40004cd6",
      "43002792"
     ],
     [
      "0x43006016",
      "400047ea",
      "430022a6"
     ],
     [
      "0x4300601e",
      "40003d42",
      "430017fe"
     ],
     [
      "0x43006028",
      "400045a0",
      "4300205c"
     ],
     [
      "0x43034904",
      "00000500",
      "00000600"
     ]
    ]
   }
  }
 ],
 "features": [
  {
   "id": "usb6",
   "label": "Sortie USB 6 canaux separes",
   "desc": "Chaque piste sort sur son propre canal USB (48 kHz / 32 bits). Le mix stereo n'est plus envoye en USB : tu melanges les 6 pistes dans ton logiciel.",
   "status": "tested",
   "credit": {
    "kind": "based",
    "who": "scottmetoyer",
    "repo": "scottmetoyer/ms-multi-output"
   },
   "variants": [
    {
     "id": "6ch-usbup",
     "label": null
    }
   ]
  },
  {
   "id": "latching-mute",
   "label": "Mode mute verrouille",
   "desc": "Maintiens TRK et tape FUNC : le mode mute reste actif, tu mutes les pistes sans tenir FUNC. Un appui court sur FUNC en sort.",
   "status": "tested",
   "credit": {
    "kind": "by",
    "who": "drumkilla",
    "repo": "drumkilla/elektron-model-tweaks"
   },
   "variants": [
    {
     "id": "latching-mute",
     "label": null
    }
   ]
  },
  {
   "id": "trig-preview",
   "label": "Ecoute d'un pas (TRIG + PAGE)",
   "desc": "Sequenceur a l'arret, maintiens un pas et appuie sur PAGE : le pas joue avec sa note, sa longueur et ses p-locks.",
   "status": "tested",
   "credit": {
    "kind": "by",
    "who": "drumkilla",
    "repo": "drumkilla/elektron-model-tweaks"
   },
   "variants": [
    {
     "id": "trig-preview",
     "label": null
    }
   ]
  },
  {
   "id": "browser-scroll",
   "label": "Defilement des noms longs",
   "desc": "Dans le navigateur de sons, un nom trop long pour l'ecran defile.",
   "status": "tested",
   "credit": {
    "kind": "by",
    "who": "drumkilla",
    "repo": "drumkilla/elektron-model-tweaks"
   },
   "variants": [
    {
     "id": "browser-scroll",
     "label": null
    }
   ]
  },
  {
   "id": "sdvintage",
   "label": "Vrai moteur SD VINTAGE du Syntakt",
   "desc": "Le moteur SD VINTAGE du Syntakt, extrait de TON fichier Syntakt_OS1.41.syx (a deposer a l'etape 2), a la place de SNARE ou en 7e machine SDVtg. Identique au Syntakt en emulation.",
   "status": "tested",
   "credit": null,
   "variants": [
    {
     "id": "sdvintage-exact",
     "label": "A la place de SNARE (teste sur un Model:Cycles le 30/09/2026)"
    },
    {
     "id": "sdvintage-7th",
     "label": "En 7e machine SDVtg, a cote de SNARE (nouveau, pas encore teste)"
    }
   ],
   "needs": "syntakt"
  }
 ],
 "samples": {
  "syx_sha256": "e11859b68deb7e5e3fe86ab32581212093849c4be5d3950add011eac398a2ce8",
  "main_sha256": "a351392c62ec1c6c3324a807baf46934690d54edfc76029a4b4882541cad1ab2",
  "download": "https://www.elektron.se/support-downloads/modelsamples"
 },
 "syntakt": {
  "download": "https://www.elektron.se/support-downloads/syntakt"
 }
};
