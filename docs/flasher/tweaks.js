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
   "id": "sdvintage-7th",
   "order": 22,
   "name": "Vrai moteur SD VINTAGE du Syntakt en 7e machine (SDVtg), a cote de SNARE",
   "description": [
    "Le moteur SD VINTAGE du Syntakt (OS 1.41), extrait AU BUILD de TON Syntakt_OS1.41.syx",
    "(21 fonctions, 5200 o de code, avec ses tables), en 7e machine « SDVtg » :",
    "SNARE reste la SNARE d'origine. Potards propres, noms et defauts du Syntakt :",
    "COLOR=INHM (Inharm), SHAPE=FCMP, SWEEP=SWEP (Pitch Sweep), CONTOUR=MENV (Mod Envelope),",
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
     "off": 83114,
     "old": "7205",
     "new": "7206"
    },
    {
     "off": 83122,
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
     "off": 124122,
     "old": "202f0020226a0068",
     "new": "4eb9430331a84e71"
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
     "off": 318300,
     "old": "7206202f0004",
     "new": "4ef9430330ee"
    },
    {
     "off": 318326,
     "old": "7205202f0004",
     "new": "4ef94303310e"
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
     "new": "41f9401aa14043f943000000203c0000d51822d8538066fa4feffff048d700f04ef9400004ba0000"
    }
   ],
   "append": {
    "at": "0x401aa140",
    "dest": "0x43000000",
    "size": 218208,
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
      "hex": "724cb081650e7251b081650470004e75721990814e75202f000461e472644c010800068040a717544e75202f000461d072644c010800068040a71768487940a715002f2f000c2f004eb9400ddf604fef000c203c40a715004e757405b481650c7406b480650c4ef94005a8fa4ef94005a9284ef94005a91c28037006b084660278012004e588eb8c988048780001487800174878002045f940071da4227940fe32ccd3c42f092f024e924fef00304878000148780022d8b940fe384c487800602f042f024e924fef00144ef9400a268041e8000a2f082f2e001020026a0270007205b2806c0270014ef9400a4dde202f00047207b08167467206b280640270ff724c4c010800068040a715404e75202f00047206b08167267205b280651041f9401091b4713008007206b280640270ff724c4c010800068040a715404e754a394303544c665a2f02487940a715d84879430354004eb9400f8f02508f487940a715dc4879430354044eb9400f8f02508f41f940a715e043f943035408741020187233b0816d0a7237b2806d047219d08122c053826ae8700113c04303544c241f203c430354004e75202f0024226a00687206b081660643f9430338544e75"
     },
     {
      "dest": "0x43033800",
      "hex": "401300d8401300dd401300e3401300e940129960401300ee43033870400aa08c400ab3b0400aa49c400aa998400aa7b8400aae8843031000400aa3c4400ab6e8400aa712400aacc2400aa930400ab24c4303119600000001000000020000000300000004000000050000000600000007534456746700496e6861726d004672657120436f6d706c6578005069746368205377656570004d6f6420456e76656c6f706500494e484d0046434d500053574550004d454e5600"
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
      "hex": "000000060000000b0000000000007f0000000000000000000010ffffffffffff000000000000060000000028430338764012996f430338a3000000060000000c0000000000007f0000006e00000000000011ffffffffffff0000000000000600000000324303387d4012996f430338a8000000060000000d0000000000007f0000004a00000000000012ffffffffffff00000000000006000000003c4303388a4012996f430338ad000000060000000e0000000000007f0000005000000000000013ffffffffffff000000000000060000000046430338964012996f430338b200000007000000120000000000007f0000002100000000000050ffff0000009a00000000000006000000001e401298784012988240129886"
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
  },
  {
   "id": "syntakt-cp",
   "order": 24,
   "name": "Vrais moteurs du Syntakt en machines ajoutées : CPVtg (CP VINTAGE)",
   "description": [
    "Moteurs du Syntakt (OS 1.41) extraits AU BUILD de TON Syntakt_OS1.41.syx, en machines ajoutées après",
    "les 6 d'origine (notes/20) : CPVtg = CP VINTAGE (machine 7).",
    "Potards propres, noms et défauts du Syntakt. Généré par tools/gen_syntakt_engines.py.",
    "Demande build.py --syntakt Syntakt_OS1.41.syx. Aucun octet Elektron dans ce fichier."
   ],
   "device": "Model:Cycles",
   "os": "1.13",
   "section": 3,
   "conflicts": [
    "sdvintage-7th",
    "sdvintage-exact",
    "sdvintage-snare",
    "syntakt-cp-toy",
    "syntakt-sd-cp-toy",
    "syntakt-sd-toy",
    "syntakt-toy",
    "syntakt-vintage"
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
     "off": 83114,
     "old": "7205",
     "new": "7206"
    },
    {
     "off": 83122,
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
     "off": 124122,
     "old": "202f0020226a0068",
     "new": "4eb9430331de4e71"
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
     "new": "4ef943033028"
    },
    {
     "off": 318300,
     "old": "7206202f0004",
     "new": "4ef943033116"
    },
    {
     "off": 318326,
     "old": "7205202f0004",
     "new": "4ef943033138"
    },
    {
     "off": 318370,
     "old": "704c222f0004",
     "new": "4ef94303303e"
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
     "new": "43035800"
    },
    {
     "off": 368350,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 368418,
     "old": "40a79418",
     "new": "43035800"
    },
    {
     "off": 368448,
     "old": "7005b085643e",
     "new": "4ef94303322a"
    },
    {
     "off": 368488,
     "old": "704c",
     "new": "7051"
    },
    {
     "off": 368528,
     "old": "40a79418",
     "new": "43035800"
    },
    {
     "off": 368554,
     "old": "40a7ada4",
     "new": "43035a00"
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
     "old": "724c202f0004",
     "new": "4ef9430331f4"
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
     "new": "43035800"
    },
    {
     "off": 369392,
     "old": "40a79418",
     "new": "43035800"
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
     "new": "4ef943033070"
    },
    {
     "off": 369938,
     "old": "40a7ada4",
     "new": "43035a00"
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
     "new": "4ef94303309a"
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
     "new": "4ef9430330ee"
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
     "off": 686532,
     "old": "40118640",
     "new": "43033870"
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
     "off": 1492712,
     "old": "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
     "new": "41f9401aa14043f943000000203c0000e00022d8538066fa4feffff048d700f04ef9400004ba0000"
    }
   ],
   "append": {
    "at": "0x401aa140",
    "dest": "0x43000000",
    "size": 229376,
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
       "0x40008e0c"
      ]
     },
     {
      "dest": "0x430068c8",
      "syntakt": [
       "0x4000e488",
       "0x40010490"
      ]
     },
     {
      "dest": "0x430088d0",
      "syntakt": [
       "0x40014980",
       "0x40016b90"
      ]
     },
     {
      "dest": "0x4300aae0",
      "syntakt": [
       "0x40028438",
       "0x4003be38"
      ]
     },
     {
      "dest": "0x43036000",
      "syntakt": [
       "0x4003be38",
       "0x4003de38"
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
      "hex": "4fefffe448d77c04247cbdcf77d82a6f0024d5cd220a243c0000031c4c421001286f00282f6f0020001841f943032004203c534456312441b0ad002c660a71b018005f804a80671c70077201243c534456312b42002c1180a80041f94303200a1181a8004ab94303200066564aad0038670001362c7c43020000267c43028a604eb9430000002d4b056c2f0e4eb94300199c47eb0030588f4dee0708b7fc43028be066dc303c0101243c01010101720123c24303200a23c14303200033c04303200e200a243c000007084c0208002640d7fc43020000276d00340034222d003827410038276d003c003c4bf94303200a1035a8004a81670000aa4a00672042022f0b4eb94300199c588f700172072740003870072741000426801b82a800200aed88720742422440d5fc4303201015410022356c00140024356c00160026356c00180028356c001a002a356c001c002c356c001e002e302c0020354000307140356c0024003235420034274003ec2f0b4eb94300001a2f4a002c2f4b0028716c00224cef7c0400040680ffffc000e788d0af001c2f4000244fef00204ef94300603c4a006700ff784cd77c044fef001c4e752f0a2f02206f000c4ab9430320006730243c0000031c43f94303200a202f00100680bdcf77d84c4200004a310800661043f94303200473b108005f814a81671420080680000000804298b08866fa241f245f4e75223c000007084c0108002440d5fc430200002f0a2f084eb943006444256a00340038508f60d4"
     },
     {
      "dest": "0x43033000",
      "hex": "724cb081650000200c8000000051650470004e75724c90817205b0816504908160f67233d0814e75202f00046100ffd272644c010800068040a717544e75202f00046100ffbc72644c010800068040a71768487940a715002f2f000c2f004eb9400ddf604fef000c203c40a715004e757405b481650c7406b480650c4ef94005a8fa4ef94005a9284ef94005a91c7206b081660470034e754e7520036100fff02800e588eb8c988048780001487800174878002045f940071da4227940fe32ccd3c42f092f024e924fef00304878000148780022d8b940fe384c487800602f042f024e924fef00144ef9400a268041e8000a2f082f2e001020026a0270007205b2806c0c6100ff887205b2806c0270054ef9400a4dde202f00047207b0816700004a7206b280640270ff724c4c010800068040a715404e75202f00047206b081670000287205b280651041f9401091b4713008007206b280640270ff724c4c010800068040a715404e7541f943035c007019600000024a28004c6600005e2f022f0a24482400487940a715d82f0a4eb9400f8f02508f487940a715dc486a00044eb9400f8f02508f41f940a715e043ea000872102f0120187233b0816d087237b2806d02d08222c053976aea588f70011540004c204a245f241f20084e75202f0024226a00687206b0816d0643f9430338544e75202f00040c800000004c650c0c800000004f620470064e750c8000000051650270002200e789ed88908141f943034000203008004e757006b0856500001e0c820000004c650e0c820000004f62067a06600000024ef94005a3844ef94005a346"
     },
     {
      "dest": "0x43033800",
      "hex": "401300d8401300dd401300e3401300e940129960401300ee43033878400aa08c400ab3b0400aa49c400aa998400aa7b8400aae8843031000400aa3c4400ab6e8400aa712400aacc2400aa930400ab24c430311b2000000010000000200000003000000040000000500000006000000070001020304050600435056746700426f6479204368617200424f44590042616c616e63650042414c0053706163696e67204372756e6368005350435200426f647920456e76656c6f70650042454e5600"
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
      "hex": "000000060000000b0000000000007f0000001800000000000010ffffffffffff0000000000000600000000284303387e4012996f43033888000000060000000c0000000000007f0000001900000000000011ffffffffffff0000000000000600000000324303388d4012996f43033895000000060000000d0000000000007f0000002e00000000000012ffffffffffff00000000000006000000003c430338994012996f430338a8000000060000000e0000000000007f0000002500000000000013ffffffffffff000000000000060000000046430338ad4012996f430338bb00000007000000120000000000007f0000002000000000000050ffff0000009a00000000000006000000001e401298784012988240129886"
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
      "43008acc"
     ],
     [
      "0x43001d82",
      "40014980",
      "430088d0"
     ],
     [
      "0x43002e04",
      "40014b80",
      "43008ad0"
     ],
     [
      "0x43002e22",
      "40015b80",
      "43009ad0"
     ],
     [
      "0x43002e3a",
      "80004a50",
      "43024a50"
     ],
     [
      "0x43002e66",
      "4000f48c",
      "430078cc"
     ],
     [
      "0x43002e9c",
      "4000e488",
      "430068c8"
     ],
     [
      "0x43002eda",
      "4000f48c",
      "430078cc"
     ],
     [
      "0x43002f2c",
      "4000e488",
      "430068c8"
     ],
     [
      "0x43002f3a",
      "4000e488",
      "430068c8"
     ],
     [
      "0x43002f4a",
      "80004a50",
      "43024a50"
     ],
     [
      "0x43002fb2",
      "80004a50",
      "43024a50"
     ],
     [
      "0x43002fc2",
      "80004a70",
      "43024a70"
     ],
     [
      "0x43003000",
      "80004a70",
      "43024a70"
     ],
     [
      "0x43003006",
      "80004af0",
      "43024af0"
     ],
     [
      "0x43003014",
      "80004a50",
      "43024a50"
     ],
     [
      "0x4300301e",
      "80004a54",
      "43024a54"
     ],
     [
      "0x43003028",
      "80004a58",
      "43024a58"
     ],
     [
      "0x43003032",
      "80004a5c",
      "43024a5c"
     ],
     [
      "0x4300303c",
      "80004a60",
      "43024a60"
     ],
     [
      "0x4300304c",
      "80004a64",
      "43024a64"
     ],
     [
      "0x4300307c",
      "80004af0",
      "43024af0"
     ],
     [
      "0x4300309a",
      "80004a68",
      "43024a68"
     ],
     [
      "0x430030a0",
      "80004a6c",
      "43024a6c"
     ],
     [
      "0x4300330a",
      "8000a07c",
      "4302a07c"
     ],
     [
      "0x43005b42",
      "40004dc6",
      "43002882"
     ],
     [
      "0x43005b4e",
      "40039238",
      "4301b8e0"
     ],
     [
      "0x43005b7c",
      "40039838",
      "4301bee0"
     ],
     [
      "0x43005b8e",
      "40039638",
      "4301bce0"
     ],
     [
      "0x43005ba0",
      "40039438",
      "4301bae0"
     ],
     [
      "0x43005bb6",
      "40039038",
      "4301b6e0"
     ],
     [
      "0x43005bce",
      "40038e38",
      "4301b4e0"
     ],
     [
      "0x43005be6",
      "40038c38",
      "4301b2e0"
     ],
     [
      "0x43005c12",
      "4003a038",
      "4301c6e0"
     ],
     [
      "0x43005c1c",
      "40039e38",
      "4301c4e0"
     ],
     [
      "0x43005c3a",
      "40039c38",
      "4301c2e0"
     ],
     [
      "0x43005c76",
      "40028438",
      "4300aae0"
     ],
     [
      "0x43005c92",
      "40038a38",
      "4301b0e0"
     ],
     [
      "0x43005cae",
      "40038838",
      "4301aee0"
     ],
     [
      "0x43005dea",
      "800097c8",
      "430297c8"
     ],
     [
      "0x43005dfe",
      "40038638",
      "4301ace0"
     ],
     [
      "0x43005e06",
      "800097c8",
      "430297c8"
     ],
     [
      "0x43005e28",
      "40038438",
      "4301aae0"
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
      "4301c0e0"
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
      "0x4300605a",
      "80004b70",
      "43024b70"
     ],
     [
      "0x43006060",
      "80009580",
      "43029580"
     ],
     [
      "0x43006090",
      "40004dc6",
      "43002882"
     ],
     [
      "0x4300609c",
      "4003b238",
      "4301d8e0"
     ],
     [
      "0x430060ba",
      "4003b638",
      "4301dce0"
     ],
     [
      "0x430060cc",
      "4003b438",
      "4301dae0"
     ],
     [
      "0x430060e8",
      "4003a838",
      "4301cee0"
     ],
     [
      "0x4300613a",
      "400052f8",
      "43002db4"
     ],
     [
      "0x4300614e",
      "4003bc38",
      "4301e2e0"
     ],
     [
      "0x430061d8",
      "4003b038",
      "4301d6e0"
     ],
     [
      "0x430061ea",
      "4003ae38",
      "4301d4e0"
     ],
     [
      "0x4300631c",
      "4003ac38",
      "4301d2e0"
     ],
     [
      "0x43006332",
      "4003ba38",
      "4301e0e0"
     ],
     [
      "0x43006344",
      "4003aa38",
      "4301d0e0"
     ],
     [
      "0x43006366",
      "4003b838",
      "4301dee0"
     ],
     [
      "0x430063a4",
      "4003a438",
      "4301cae0"
     ],
     [
      "0x430063c2",
      "4003a238",
      "4301c8e0"
     ],
     [
      "0x430063d6",
      "4003a638",
      "4301cce0"
     ],
     [
      "0x43006434",
      "40002596",
      "43000052"
     ],
     [
      "0x43006452",
      "40005728",
      "430031e4"
     ],
     [
      "0x43006460",
      "40004e6c",
      "43002928"
     ],
     [
      "0x4300647e",
      "40003c0e",
      "430016ca"
     ],
     [
      "0x43006488",
      "400058e8",
      "430033a4"
     ],
     [
      "0x43006494",
      "40003958",
      "43001414"
     ],
     [
      "0x4300649e",
      "4000290e",
      "430003ca"
     ],
     [
      "0x430064aa",
      "400044e2",
      "43001f9e"
     ],
     [
      "0x430064b8",
      "800096a4",
      "430296a4"
     ],
     [
      "0x430064be",
      "40003eb4",
      "43001970"
     ],
     [
      "0x430064cc",
      "800096a4",
      "430296a4"
     ],
     [
      "0x430064de",
      "800096a4",
      "430296a4"
     ],
     [
      "0x430064f0",
      "80008c60",
      "43028c60"
     ],
     [
      "0x43006510",
      "800096a4",
      "430296a4"
     ],
     [
      "0x43006516",
      "400049f4",
      "430024b0"
     ],
     [
      "0x4300652c",
      "400054e6",
      "43002fa2"
     ],
     [
      "0x43006538",
      "40004f74",
      "43002a30"
     ],
     [
      "0x43006544",
      "4000569a",
      "43003156"
     ],
     [
      "0x4300657c",
      "80008c60",
      "43028c60"
     ],
     [
      "0x43006590",
      "400047ea",
      "430022a6"
     ],
     [
      "0x430065c2",
      "4003dc38",
      "43037e00"
     ],
     [
      "0x430065c8",
      "40004dc6",
      "43002882"
     ],
     [
      "0x430065e6",
      "4003c838",
      "43036a00"
     ],
     [
      "0x430065f8",
      "4003c638",
      "43036800"
     ],
     [
      "0x4300660a",
      "4003c438",
      "43036600"
     ],
     [
      "0x4300661c",
      "4003c238",
      "43036400"
     ],
     [
      "0x43006626",
      "800098ec",
      "430298ec"
     ],
     [
      "0x4300663a",
      "4003d038",
      "43037200"
     ],
     [
      "0x43006658",
      "4003d238",
      "43037400"
     ],
     [
      "0x43006674",
      "4003c038",
      "43036200"
     ],
     [
      "0x4300667c",
      "80004b70",
      "43024b70"
     ],
     [
      "0x430066b6",
      "4003ce38",
      "43037000"
     ],
     [
      "0x430066cc",
      "4003cc38",
      "43036e00"
     ],
     [
      "0x430066de",
      "4003ca38",
      "43036c00"
     ],
     [
      "0x430067b2",
      "4003da38",
      "43037c00"
     ],
     [
      "0x430067c4",
      "4003d838",
      "43037a00"
     ],
     [
      "0x430067d6",
      "4003d638",
      "43037800"
     ],
     [
      "0x430067e8",
      "4003d438",
      "43037600"
     ],
     [
      "0x43006804",
      "40002596",
      "43000052"
     ],
     [
      "0x4300682c",
      "40003c0e",
      "430016ca"
     ],
     [
      "0x43006838",
      "400035de",
      "4300109a"
     ],
     [
      "0x43006842",
      "4000290e",
      "430003ca"
     ],
     [
      "0x4300686e",
      "80008c60",
      "43028c60"
     ],
     [
      "0x43006878",
      "80009580",
      "43029580"
     ],
     [
      "0x43006882",
      "800096a4",
      "430296a4"
     ],
     [
      "0x4300688c",
      "800097c8",
      "430297c8"
     ],
     [
      "0x43006896",
      "40004cd6",
      "43002792"
     ],
     [
      "0x4300689e",
      "40003d42",
      "430017fe"
     ],
     [
      "0x430068ac",
      "400045a0",
      "4300205c"
     ],
     [
      "0x430068b6",
      "400047ea",
      "430022a6"
     ],
     [
      "0x43034904",
      "00000500",
      "00000600"
     ]
    ]
   }
  },
  {
   "id": "syntakt-toy",
   "order": 24,
   "name": "Vrais moteurs du Syntakt en machines ajoutées : SYToy (SY TOY)",
   "description": [
    "Moteurs du Syntakt (OS 1.41) extraits AU BUILD de TON Syntakt_OS1.41.syx, en machines ajoutées après",
    "les 6 d'origine (notes/20) : SYToy = SY TOY (machine 7).",
    "Potards propres, noms et défauts du Syntakt. Généré par tools/gen_syntakt_engines.py.",
    "Demande build.py --syntakt Syntakt_OS1.41.syx. Aucun octet Elektron dans ce fichier."
   ],
   "device": "Model:Cycles",
   "os": "1.13",
   "section": 3,
   "conflicts": [
    "sdvintage-7th",
    "sdvintage-exact",
    "sdvintage-snare",
    "syntakt-cp",
    "syntakt-cp-toy",
    "syntakt-sd-cp-toy",
    "syntakt-sd-toy",
    "syntakt-vintage"
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
     "off": 83114,
     "old": "7205",
     "new": "7206"
    },
    {
     "off": 83122,
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
     "off": 124122,
     "old": "202f0020226a0068",
     "new": "4eb9430331de4e71"
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
     "new": "4ef943033028"
    },
    {
     "off": 318300,
     "old": "7206202f0004",
     "new": "4ef943033116"
    },
    {
     "off": 318326,
     "old": "7205202f0004",
     "new": "4ef943033138"
    },
    {
     "off": 318370,
     "old": "704c222f0004",
     "new": "4ef94303303e"
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
     "new": "43035800"
    },
    {
     "off": 368350,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 368418,
     "old": "40a79418",
     "new": "43035800"
    },
    {
     "off": 368448,
     "old": "7005b085643e",
     "new": "4ef94303322a"
    },
    {
     "off": 368488,
     "old": "704c",
     "new": "7051"
    },
    {
     "off": 368528,
     "old": "40a79418",
     "new": "43035800"
    },
    {
     "off": 368554,
     "old": "40a7ada4",
     "new": "43035a00"
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
     "old": "724c202f0004",
     "new": "4ef9430331f4"
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
     "new": "43035800"
    },
    {
     "off": 369392,
     "old": "40a79418",
     "new": "43035800"
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
     "new": "4ef943033070"
    },
    {
     "off": 369938,
     "old": "40a7ada4",
     "new": "43035a00"
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
     "new": "4ef94303309a"
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
     "new": "4ef9430330ee"
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
     "off": 686532,
     "old": "40118640",
     "new": "43033870"
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
     "off": 1492712,
     "old": "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
     "new": "41f9401aa14043f943000000203c0000e00022d8538066fa4feffff048d700f04ef9400004ba0000"
    }
   ],
   "append": {
    "at": "0x401aa140",
    "dest": "0x43000000",
    "size": 229376,
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
       "0x40008e0c"
      ]
     },
     {
      "dest": "0x430068c8",
      "syntakt": [
       "0x4000e488",
       "0x40010490"
      ]
     },
     {
      "dest": "0x430088d0",
      "syntakt": [
       "0x40014980",
       "0x40016b90"
      ]
     },
     {
      "dest": "0x4300aae0",
      "syntakt": [
       "0x40028438",
       "0x4003be38"
      ]
     },
     {
      "dest": "0x43036000",
      "syntakt": [
       "0x4003be38",
       "0x4003de38"
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
      "hex": "4fefffe448d77c04247cbdcf77d82a6f0024d5cd220a243c0000031c4c421001286f00282f6f0020001841f943032004203c534456312441b0ad002c660a71b0180051804a80671c70087201243c534456312b42002c1180a80041f94303200a1181a8004ab94303200066564aad0038670001362c7c43020000267c43028a604eb9430000002d4b056c2f0e4eb94300199c47eb0030588f4dee0708b7fc43028be066dc303c0101243c01010101720123c24303200a23c14303200033c04303200e200a243c000007084c0208002640d7fc43020000276d00340034222d003827410038276d003c003c4bf94303200a1035a8004a81670000aa4a00672042022f0b4eb94300199c588f700172082740003870082741000426801b82a800200aed88720842422440d5fc4303201015410022356c00140024356c00160026356c00180028356c001a002a356c001c002c356c001e002e302c0020354000307140356c0024003235420034274003ec2f0b4eb94300001a2f4a002c2f4b0028716c00224cef7c0400040680ffffc000e788d0af001c2f4000244fef00204ef9430065a44a006700ff784cd77c044fef001c4e752f0a2f02206f000c4ab9430320006730243c0000031c43f94303200a202f00100680bdcf77d84c4200004a310800661043f94303200473b1080051814a81671420080680000000804298b08866fa241f245f4e75223c000007084c0108002440d5fc430200002f0a2f084eb943006814256a00340038508f60d4"
     },
     {
      "dest": "0x43033000",
      "hex": "724cb081650000200c8000000051650470004e75724c90817205b0816504908160f67233d0814e75202f00046100ffd272644c010800068040a717544e75202f00046100ffbc72644c010800068040a71768487940a715002f2f000c2f004eb9400ddf604fef000c203c40a715004e757405b481650c7406b480650c4ef94005a8fa4ef94005a9284ef94005a91c7206b081660470044e754e7520036100fff02800e588eb8c988048780001487800174878002045f940071da4227940fe32ccd3c42f092f024e924fef00304878000148780022d8b940fe384c487800602f042f024e924fef00144ef9400a268041e8000a2f082f2e001020026a0270007205b2806c0c6100ff887205b2806c0270054ef9400a4dde202f00047207b0816700004a7206b280640270ff724c4c010800068040a715404e75202f00047206b081670000287205b280651041f9401091b4713008007206b280640270ff724c4c010800068040a715404e7541f943035c007019600000024a28004c6600005e2f022f0a24482400487940a715d82f0a4eb9400f8f02508f487940a715dc486a00044eb9400f8f02508f41f940a715e043ea000872102f0120187233b0816d087237b2806d02d08222c053976aea588f70011540004c204a245f241f20084e75202f0024226a00687206b0816d0643f9430338544e75202f00040c800000004c650c0c800000004f620470064e750c8000000051650270002200e789ed88908141f943034000203008004e757006b0856500001e0c820000004c650e0c820000004f62067a06600000024ef94005a3844ef94005a346"
     },
     {
      "dest": "0x43033800",
      "hex": "401300d8401300dd401300e3401300e940129960401300ee43033878400aa08c400ab3b0400aa49c400aa998400aa7b8400aae8843031000400aa3c4400ab6e8400aa712400aacc2400aa930400ab24c430311b20000000100000002000000030000000400000005000000060000000700010203040506005359546f7900466f726d00464f524d00496d7061637400494d50004272696768740042524947005061727469616c204465636179005041525400"
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
      "hex": "000000060000000b0000000000007f0000001800000000000010ffffffffffff0000000000000600000000284303387e4012996f43033883000000060000000c0000000000007f0000003c00000000000011ffffffffffff000000000000060000000032430338884012996f4303388f000000060000000d0000000000007f0000006e00000000000012ffffffffffff00000000000006000000003c430338934012996f4303389a000000060000000e0000000000007f0000004000000000000013ffffffffffff0000000000000600000000464303389f4012996f430338ad00000007000000120000000000007f0000003c00000000000050ffff0000009a00000000000006000000001e401298784012988240129886"
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
      "43008acc"
     ],
     [
      "0x43001d82",
      "40014980",
      "430088d0"
     ],
     [
      "0x43002e04",
      "40014b80",
      "43008ad0"
     ],
     [
      "0x43002e22",
      "40015b80",
      "43009ad0"
     ],
     [
      "0x43002e3a",
      "80004a50",
      "43024a50"
     ],
     [
      "0x43002e66",
      "4000f48c",
      "430078cc"
     ],
     [
      "0x43002e9c",
      "4000e488",
      "430068c8"
     ],
     [
      "0x43002eda",
      "4000f48c",
      "430078cc"
     ],
     [
      "0x43002f2c",
      "4000e488",
      "430068c8"
     ],
     [
      "0x43002f3a",
      "4000e488",
      "430068c8"
     ],
     [
      "0x43002f4a",
      "80004a50",
      "43024a50"
     ],
     [
      "0x43002fb2",
      "80004a50",
      "43024a50"
     ],
     [
      "0x43002fc2",
      "80004a70",
      "43024a70"
     ],
     [
      "0x43003000",
      "80004a70",
      "43024a70"
     ],
     [
      "0x43003006",
      "80004af0",
      "43024af0"
     ],
     [
      "0x43003014",
      "80004a50",
      "43024a50"
     ],
     [
      "0x4300301e",
      "80004a54",
      "43024a54"
     ],
     [
      "0x43003028",
      "80004a58",
      "43024a58"
     ],
     [
      "0x43003032",
      "80004a5c",
      "43024a5c"
     ],
     [
      "0x4300303c",
      "80004a60",
      "43024a60"
     ],
     [
      "0x4300304c",
      "80004a64",
      "43024a64"
     ],
     [
      "0x4300307c",
      "80004af0",
      "43024af0"
     ],
     [
      "0x4300309a",
      "80004a68",
      "43024a68"
     ],
     [
      "0x430030a0",
      "80004a6c",
      "43024a6c"
     ],
     [
      "0x4300330a",
      "8000a07c",
      "4302a07c"
     ],
     [
      "0x43005b42",
      "40004dc6",
      "43002882"
     ],
     [
      "0x43005b4e",
      "40039238",
      "4301b8e0"
     ],
     [
      "0x43005b7c",
      "40039838",
      "4301bee0"
     ],
     [
      "0x43005b8e",
      "40039638",
      "4301bce0"
     ],
     [
      "0x43005ba0",
      "40039438",
      "4301bae0"
     ],
     [
      "0x43005bb6",
      "40039038",
      "4301b6e0"
     ],
     [
      "0x43005bce",
      "40038e38",
      "4301b4e0"
     ],
     [
      "0x43005be6",
      "40038c38",
      "4301b2e0"
     ],
     [
      "0x43005c12",
      "4003a038",
      "4301c6e0"
     ],
     [
      "0x43005c1c",
      "40039e38",
      "4301c4e0"
     ],
     [
      "0x43005c3a",
      "40039c38",
      "4301c2e0"
     ],
     [
      "0x43005c76",
      "40028438",
      "4300aae0"
     ],
     [
      "0x43005c92",
      "40038a38",
      "4301b0e0"
     ],
     [
      "0x43005cae",
      "40038838",
      "4301aee0"
     ],
     [
      "0x43005dea",
      "800097c8",
      "430297c8"
     ],
     [
      "0x43005dfe",
      "40038638",
      "4301ace0"
     ],
     [
      "0x43005e06",
      "800097c8",
      "430297c8"
     ],
     [
      "0x43005e28",
      "40038438",
      "4301aae0"
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
      "4301c0e0"
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
      "0x4300605a",
      "80004b70",
      "43024b70"
     ],
     [
      "0x43006060",
      "80009580",
      "43029580"
     ],
     [
      "0x43006090",
      "40004dc6",
      "43002882"
     ],
     [
      "0x4300609c",
      "4003b238",
      "4301d8e0"
     ],
     [
      "0x430060ba",
      "4003b638",
      "4301dce0"
     ],
     [
      "0x430060cc",
      "4003b438",
      "4301dae0"
     ],
     [
      "0x430060e8",
      "4003a838",
      "4301cee0"
     ],
     [
      "0x4300613a",
      "400052f8",
      "43002db4"
     ],
     [
      "0x4300614e",
      "4003bc38",
      "4301e2e0"
     ],
     [
      "0x430061d8",
      "4003b038",
      "4301d6e0"
     ],
     [
      "0x430061ea",
      "4003ae38",
      "4301d4e0"
     ],
     [
      "0x4300631c",
      "4003ac38",
      "4301d2e0"
     ],
     [
      "0x43006332",
      "4003ba38",
      "4301e0e0"
     ],
     [
      "0x43006344",
      "4003aa38",
      "4301d0e0"
     ],
     [
      "0x43006366",
      "4003b838",
      "4301dee0"
     ],
     [
      "0x430063a4",
      "4003a438",
      "4301cae0"
     ],
     [
      "0x430063c2",
      "4003a238",
      "4301c8e0"
     ],
     [
      "0x430063d6",
      "4003a638",
      "4301cce0"
     ],
     [
      "0x43006434",
      "40002596",
      "43000052"
     ],
     [
      "0x43006452",
      "40005728",
      "430031e4"
     ],
     [
      "0x43006460",
      "40004e6c",
      "43002928"
     ],
     [
      "0x4300647e",
      "40003c0e",
      "430016ca"
     ],
     [
      "0x43006488",
      "400058e8",
      "430033a4"
     ],
     [
      "0x43006494",
      "40003958",
      "43001414"
     ],
     [
      "0x4300649e",
      "4000290e",
      "430003ca"
     ],
     [
      "0x430064aa",
      "400044e2",
      "43001f9e"
     ],
     [
      "0x430064b8",
      "800096a4",
      "430296a4"
     ],
     [
      "0x430064be",
      "40003eb4",
      "43001970"
     ],
     [
      "0x430064cc",
      "800096a4",
      "430296a4"
     ],
     [
      "0x430064de",
      "800096a4",
      "430296a4"
     ],
     [
      "0x430064f0",
      "80008c60",
      "43028c60"
     ],
     [
      "0x43006510",
      "800096a4",
      "430296a4"
     ],
     [
      "0x43006516",
      "400049f4",
      "430024b0"
     ],
     [
      "0x4300652c",
      "400054e6",
      "43002fa2"
     ],
     [
      "0x43006538",
      "40004f74",
      "43002a30"
     ],
     [
      "0x43006544",
      "4000569a",
      "43003156"
     ],
     [
      "0x4300657c",
      "80008c60",
      "43028c60"
     ],
     [
      "0x43006590",
      "400047ea",
      "430022a6"
     ],
     [
      "0x430065c2",
      "4003dc38",
      "43037e00"
     ],
     [
      "0x430065c8",
      "40004dc6",
      "43002882"
     ],
     [
      "0x430065e6",
      "4003c838",
      "43036a00"
     ],
     [
      "0x430065f8",
      "4003c638",
      "43036800"
     ],
     [
      "0x4300660a",
      "4003c438",
      "43036600"
     ],
     [
      "0x4300661c",
      "4003c238",
      "43036400"
     ],
     [
      "0x43006626",
      "800098ec",
      "430298ec"
     ],
     [
      "0x4300663a",
      "4003d038",
      "43037200"
     ],
     [
      "0x43006658",
      "4003d238",
      "43037400"
     ],
     [
      "0x43006674",
      "4003c038",
      "43036200"
     ],
     [
      "0x4300667c",
      "80004b70",
      "43024b70"
     ],
     [
      "0x430066b6",
      "4003ce38",
      "43037000"
     ],
     [
      "0x430066cc",
      "4003cc38",
      "43036e00"
     ],
     [
      "0x430066de",
      "4003ca38",
      "43036c00"
     ],
     [
      "0x430067b2",
      "4003da38",
      "43037c00"
     ],
     [
      "0x430067c4",
      "4003d838",
      "43037a00"
     ],
     [
      "0x430067d6",
      "4003d638",
      "43037800"
     ],
     [
      "0x430067e8",
      "4003d438",
      "43037600"
     ],
     [
      "0x43006804",
      "40002596",
      "43000052"
     ],
     [
      "0x4300682c",
      "40003c0e",
      "430016ca"
     ],
     [
      "0x43006838",
      "400035de",
      "4300109a"
     ],
     [
      "0x43006842",
      "4000290e",
      "430003ca"
     ],
     [
      "0x4300686e",
      "80008c60",
      "43028c60"
     ],
     [
      "0x43006878",
      "80009580",
      "43029580"
     ],
     [
      "0x43006882",
      "800096a4",
      "430296a4"
     ],
     [
      "0x4300688c",
      "800097c8",
      "430297c8"
     ],
     [
      "0x43006896",
      "40004cd6",
      "43002792"
     ],
     [
      "0x4300689e",
      "40003d42",
      "430017fe"
     ],
     [
      "0x430068ac",
      "400045a0",
      "4300205c"
     ],
     [
      "0x430068b6",
      "400047ea",
      "430022a6"
     ],
     [
      "0x43034904",
      "00000500",
      "00000600"
     ]
    ]
   }
  },
  {
   "id": "syntakt-vintage",
   "order": 23,
   "name": "Vrais moteurs SD VINTAGE et CP VINTAGE du Syntakt en 7e et 8e machines (SDVtg, CPVtg)",
   "description": [
    "Les moteurs SD VINTAGE et CP VINTAGE du Syntakt (OS 1.41), extraits AU BUILD de TON Syntakt_OS1.41.syx",
    "(30 fonctions, 8258 o de code, avec leurs tables), en 7e et 8e machines",
    "« SDVtg » et « CPVtg » : les 6 machines d'origine ne changent pas. Potards propres, noms et",
    "défauts du Syntakt. SDVtg : Inharm, Freq Complex, Pitch Sweep, Mod Envelope (0/110/74/80, DEC 33).",
    "CPVtg : Body Char, Balance, Spacing Crunch, Body Envelope (24/25/46/37, DEC 32). Notes/19.",
    "Demande build.py --syntakt Syntakt_OS1.41.syx. Aucun octet Elektron dans ce fichier."
   ],
   "device": "Model:Cycles",
   "os": "1.13",
   "section": 3,
   "conflicts": [
    "sdvintage-snare",
    "sdvintage-exact",
    "sdvintage-7th"
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
     "new": "7456"
    },
    {
     "off": 42318,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 42334,
     "old": "744c",
     "new": "7456"
    },
    {
     "off": 42372,
     "old": "704b",
     "new": "7055"
    },
    {
     "off": 42578,
     "old": "704b",
     "new": "7055"
    },
    {
     "off": 44552,
     "old": "724c",
     "new": "7256"
    },
    {
     "off": 44564,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 44586,
     "old": "724c",
     "new": "7256"
    },
    {
     "off": 44598,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 45028,
     "old": "724c",
     "new": "7256"
    },
    {
     "off": 45036,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 45174,
     "old": "724c",
     "new": "7256"
    },
    {
     "off": 45182,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 45338,
     "old": "724c",
     "new": "7256"
    },
    {
     "off": 45346,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 45658,
     "old": "724c",
     "new": "7256"
    },
    {
     "off": 45666,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 45804,
     "old": "724c",
     "new": "7256"
    },
    {
     "off": 45812,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 45960,
     "old": "724c",
     "new": "7256"
    },
    {
     "off": 45968,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 46406,
     "old": "704b",
     "new": "7055"
    },
    {
     "off": 82852,
     "old": "7005",
     "new": "7007"
    },
    {
     "off": 83114,
     "old": "7205",
     "new": "7207"
    },
    {
     "off": 83122,
     "old": "7005",
     "new": "7007"
    },
    {
     "off": 111260,
     "old": "7005",
     "new": "7001"
    },
    {
     "off": 119266,
     "old": "724c",
     "new": "7256"
    },
    {
     "off": 119278,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 120046,
     "old": "704b",
     "new": "7055"
    },
    {
     "off": 120066,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 120078,
     "old": "704b",
     "new": "7055"
    },
    {
     "off": 121894,
     "old": "724c",
     "new": "7256"
    },
    {
     "off": 121906,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 124122,
     "old": "202f0020226a0068",
     "new": "4eb9430331e24e71"
    },
    {
     "off": 126758,
     "old": "704c",
     "new": "7056"
    },
    {
     "off": 126766,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 140924,
     "old": "704c",
     "new": "7056"
    },
    {
     "off": 140932,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 141054,
     "old": "724c",
     "new": "7256"
    },
    {
     "off": 141062,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 170616,
     "old": "744c",
     "new": "7456"
    },
    {
     "off": 170632,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 170648,
     "old": "744c",
     "new": "7456"
    },
    {
     "off": 176176,
     "old": "724c",
     "new": "7256"
    },
    {
     "off": 176184,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 289116,
     "old": "724c",
     "new": "7256"
    },
    {
     "off": 289124,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 318272,
     "old": "704c222f0004",
     "new": "4ef943033020"
    },
    {
     "off": 318300,
     "old": "7206202f0004",
     "new": "4ef94303310e"
    },
    {
     "off": 318326,
     "old": "7205202f0004",
     "new": "4ef943033134"
    },
    {
     "off": 318370,
     "old": "704c222f0004",
     "new": "4ef943033034"
    },
    {
     "off": 319262,
     "old": "704b",
     "new": "7055"
    },
    {
     "off": 319278,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 319418,
     "old": "704c",
     "new": "7056"
    },
    {
     "off": 368312,
     "old": "487800c0",
     "new": "48780100"
    },
    {
     "off": 368318,
     "old": "40a79418",
     "new": "43035300"
    },
    {
     "off": 368350,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 368418,
     "old": "40a79418",
     "new": "43035300"
    },
    {
     "off": 368448,
     "old": "7005b085643e",
     "new": "4ef943033228"
    },
    {
     "off": 368488,
     "old": "704c",
     "new": "7056"
    },
    {
     "off": 368528,
     "old": "40a79418",
     "new": "43035300"
    },
    {
     "off": 368554,
     "old": "40a7ada4",
     "new": "43035400"
    },
    {
     "off": 368872,
     "old": "724c",
     "new": "7256"
    },
    {
     "off": 368884,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 368906,
     "old": "724c202f0004",
     "new": "4ef9430331f8"
    },
    {
     "off": 368918,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 368940,
     "old": "724c",
     "new": "7256"
    },
    {
     "off": 368952,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 368982,
     "old": "724c",
     "new": "7256"
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
     "new": "7255"
    },
    {
     "off": 369050,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 369100,
     "old": "724c",
     "new": "7256"
    },
    {
     "off": 369112,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 369150,
     "old": "724c",
     "new": "7256"
    },
    {
     "off": 369162,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 369192,
     "old": "724c",
     "new": "7256"
    },
    {
     "off": 369204,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 369244,
     "old": "704c",
     "new": "7056"
    },
    {
     "off": 369274,
     "old": "4010dce8",
     "new": "43034008"
    },
    {
     "off": 369318,
     "old": "7205",
     "new": "7207"
    },
    {
     "off": 369338,
     "old": "40a79418",
     "new": "43035300"
    },
    {
     "off": 369392,
     "old": "40a79418",
     "new": "43035300"
    },
    {
     "off": 369514,
     "old": "724b",
     "new": "7255"
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
     "new": "7255"
    },
    {
     "off": 369596,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 369616,
     "old": "724c",
     "new": "7256"
    },
    {
     "off": 369628,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 369656,
     "old": "724c",
     "new": "7256"
    },
    {
     "off": 369668,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 369690,
     "old": "724c",
     "new": "7256"
    },
    {
     "off": 369702,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 369724,
     "old": "724c",
     "new": "7256"
    },
    {
     "off": 369736,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 369758,
     "old": "724c",
     "new": "7256"
    },
    {
     "off": 369770,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 369904,
     "old": "7405b4816532",
     "new": "4ef943033064"
    },
    {
     "off": 369938,
     "old": "40a7ada4",
     "new": "43035400"
    },
    {
     "off": 664032,
     "old": "7005",
     "new": "7007"
    },
    {
     "off": 664084,
     "old": "401177e4",
     "new": "43033800"
    },
    {
     "off": 664120,
     "old": "eb8c48780001",
     "new": "4ef943033096"
    },
    {
     "off": 664226,
     "old": "7850",
     "new": "7849"
    },
    {
     "off": 664296,
     "old": "7006",
     "new": "7008"
    },
    {
     "off": 670886,
     "old": "7005",
     "new": "7001"
    },
    {
     "off": 674244,
     "old": "700541e8000a",
     "new": "4ef9430330e8"
    },
    {
     "off": 674736,
     "old": "7005",
     "new": "7001"
    },
    {
     "off": 686444,
     "old": "40118628",
     "new": "43033820"
    },
    {
     "off": 686522,
     "old": "7205",
     "new": "7207"
    },
    {
     "off": 686580,
     "old": "7005",
     "new": "7007"
    },
    {
     "off": 686614,
     "old": "40118610",
     "new": "43033840"
    },
    {
     "off": 724230,
     "old": "4016cae8",
     "new": "40154ae4"
    },
    {
     "off": 1147462,
     "old": "0000",
     "new": "0607"
    },
    {
     "off": 1492712,
     "old": "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
     "new": "41f9401aa14043f943000000203c0000d57022d8538066fa4feffff048d700f04ef9400004ba0000"
    }
   ],
   "append": {
    "at": "0x401aa140",
    "dest": "0x43000000",
    "size": 218560,
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
       "0x40008ae8"
      ]
     },
     {
      "dest": "0x43006600",
      "syntakt": [
       "0x4000e488",
       "0x40010490"
      ]
     },
     {
      "dest": "0x43008800",
      "syntakt": [
       "0x40014980",
       "0x40016b90"
      ]
     },
     {
      "dest": "0x4300ac00",
      "syntakt": [
       "0x40028438",
       "0x4003be38"
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
      "hex": "4fefffe048d77c0c247cbdcf77d82a6f002cd5cd220a263c0000031c4c431001242f0024286f00302f6f0028001c41f943032004203c534456312441b0ad002c660871b01800b480671a76011182a80041f94303200a223c534456312b41002c1183a8004ab94303200066564aad0038670001382c7c43020000267c43028a604eb9430000002d4b056c2f0e4eb94300199c47eb0030588f4dee0708b7fc43028be066dc323c0101203c01010101760123c04303200a23c34303200033c14303200e223c00000708200a4c0108002640d7fc43020000276d00340034222d003827410038276d003c003c4bf94303200a1035a8004a81670000ac4a00671c2f0b76014eb94300199c420027430038274200042682588f1b80a800220aed8942432441d5fc43032010154200225f82356c00140024356c00160026356c00180028356c001a002a356c001c002c356c001e002e302c0020354000307140356c0024003235430034274003ec2f0b4eb94300001a588f4a82663c227c4300603c2f4a002c2f4b0028716c00224cd77c0c0680ffffc000e788d0af001c2f4000244fef00204ed14a006700ff724cd77c0c4fef00204e75227c43005b3060c22f0a2f02206f00104ab943032000661420080680000000804298b08866fa241f245f4e75202f0014243c0000031c0680bdcf77d84c42000043f94303200a4a31080066cc43f94303200473b10800b2af000c66bc243c000007085f814c0208002440d5fc430200004a816616227c430064442f0a2f084e91256a00340038508f609c227c43005f3660e82f2f000c2f2f000c2f2f000c487800064eb9430310004fef00104e752f2f000c2f2f000c2f2f000c487800074eb9430310004fef00104e752f2f00082f2f0008487800064eb9430311bc4fef000c4e752f2f00082f2f0008487800074eb9430311bc4fef000c4e750000"
     },
     {
      "dest": "0x43033000",
      "hex": "724cb08165187256b081650470004e757251b081650472059081721990814e75202f000461da72644c010800068040a717544e75202f000461c672644c010800068040a71768487940a715002f2f000c2f004eb9400ddf604fef000c203c40a715004e757405b481650c7407b480650c4ef94005a8fa4ef94005a9284ef94005a91c7206b081660470014e757207b081660270034e75200361e82800e588eb8c988048780001487800174878002045f940071da4227940fe32ccd3c42f092f024e924fef00304878000148780022d8b940fe384c487800602f042f024e924fef00144ef9400a268041e8000a2f082f2e001020026a0270007205b2806c0a61827205b2806c0270054ef9400a4dde202f00047207b08167527208b08167567206b280640270ff724c4c010800068040a715404e75202f00047206b081672c7207b08167307205b280651041f9401091b4713008007206b280640270ff724c4c010800068040a715404e7541f9430355007019600841f943035560701e4a28004c665c2f022f0a24482400487940a715d82f0a4eb9400f8f02508f487940a715dc486a00044eb9400f8f02508f41f940a715e043ea000872102f0120187233b0816d087237b2806d02d08222c053976aea588f70011540004c204a245f241f20084e75202f0024226a00687206b0816d0643f9430338604e75202f00047251b081650a7254b280650470074e757256b280620270002200e789ed88908141f943034000203008004e757006b08565147051b48065087054b08265027a074ef94005a3844ef94005a346"
     },
     {
      "dest": "0x43033800",
      "hex": "401300d8401300dd401300e3401300e940129960401300ee4303388043033886400aa08c400ab3b0400aa49c400aa998400aa7b8400aae884303124643031262400aa3c4400ab6e8400aa712400aacc2400aa930400ab24c4303127e430312960000000100000002000000030000000400000005000000060000000700000008534456746700435056746700496e6861726d00494e484d004672657120436f6d706c65780046434d500050697463682053776565700053574550004d6f6420456e76656c6f7065004d454e5600426f6479204368617200424f44590042616c616e63650042414c0053706163696e67204372756e6368005350435200426f647920456e76656c6f70650042454e5600"
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
      "hex": "000000060000000b0000000000007f0000000000000000000010ffffffffffff0000000000000600000000284303388c4012996f43033893000000060000000c0000000000007f0000006e00000000000011ffffffffffff000000000000060000000032430338984012996f430338a5000000060000000d0000000000007f0000004a00000000000012ffffffffffff00000000000006000000003c430338aa4012996f430338b6000000060000000e0000000000007f0000005000000000000013ffffffffffff000000000000060000000046430338bb4012996f430338c800000007000000120000000000007f0000002100000000000050ffff0000009a00000000000006000000001e401298784012988240129886000000060000000b0000000000007f0000001800000000000010ffffffffffff000000000000060000000028430338cd4012996f430338d7000000060000000c0000000000007f0000001900000000000011ffffffffffff000000000000060000000032430338dc4012996f430338e4000000060000000d0000000000007f0000002e00000000000012ffffffffffff00000000000006000000003c430338e84012996f430338f7000000060000000e0000000000007f0000002500000000000013ffffffffffff000000000000060000000046430338fc4012996f4303390a00000007000000120000000000007f0000002000000000000050ffff0000009a00000000000006000000001e401298784012988240129886"
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
      "430089fc"
     ],
     [
      "0x43001d82",
      "40014980",
      "43008800"
     ],
     [
      "0x43002e04",
      "40014b80",
      "43008a00"
     ],
     [
      "0x43002e22",
      "40015b80",
      "43009a00"
     ],
     [
      "0x43002e3a",
      "80004a50",
      "43024a50"
     ],
     [
      "0x43002e66",
      "4000f48c",
      "43007604"
     ],
     [
      "0x43002e9c",
      "4000e488",
      "43006600"
     ],
     [
      "0x43002eda",
      "4000f48c",
      "43007604"
     ],
     [
      "0x43002f2c",
      "4000e488",
      "43006600"
     ],
     [
      "0x43002f3a",
      "4000e488",
      "43006600"
     ],
     [
      "0x43002f4a",
      "80004a50",
      "43024a50"
     ],
     [
      "0x43002fb2",
      "80004a50",
      "43024a50"
     ],
     [
      "0x43002fc2",
      "80004a70",
      "43024a70"
     ],
     [
      "0x43003000",
      "80004a70",
      "43024a70"
     ],
     [
      "0x43003006",
      "80004af0",
      "43024af0"
     ],
     [
      "0x43003014",
      "80004a50",
      "43024a50"
     ],
     [
      "0x4300301e",
      "80004a54",
      "43024a54"
     ],
     [
      "0x43003028",
      "80004a58",
      "43024a58"
     ],
     [
      "0x43003032",
      "80004a5c",
      "43024a5c"
     ],
     [
      "0x4300303c",
      "80004a60",
      "43024a60"
     ],
     [
      "0x4300304c",
      "80004a64",
      "43024a64"
     ],
     [
      "0x4300307c",
      "80004af0",
      "43024af0"
     ],
     [
      "0x4300309a",
      "80004a68",
      "43024a68"
     ],
     [
      "0x430030a0",
      "80004a6c",
      "43024a6c"
     ],
     [
      "0x4300330a",
      "8000a07c",
      "4302a07c"
     ],
     [
      "0x43005b42",
      "40004dc6",
      "43002882"
     ],
     [
      "0x43005b4e",
      "40039238",
      "4301ba00"
     ],
     [
      "0x43005b7c",
      "40039838",
      "4301c000"
     ],
     [
      "0x43005b8e",
      "40039638",
      "4301be00"
     ],
     [
      "0x43005ba0",
      "40039438",
      "4301bc00"
     ],
     [
      "0x43005bb6",
      "40039038",
      "4301b800"
     ],
     [
      "0x43005bce",
      "40038e38",
      "4301b600"
     ],
     [
      "0x43005be6",
      "40038c38",
      "4301b400"
     ],
     [
      "0x43005c12",
      "4003a038",
      "4301c800"
     ],
     [
      "0x43005c1c",
      "40039e38",
      "4301c600"
     ],
     [
      "0x43005c3a",
      "40039c38",
      "4301c400"
     ],
     [
      "0x43005c76",
      "40028438",
      "4300ac00"
     ],
     [
      "0x43005c92",
      "40038a38",
      "4301b200"
     ],
     [
      "0x43005cae",
      "40038838",
      "4301b000"
     ],
     [
      "0x43005dea",
      "800097c8",
      "430297c8"
     ],
     [
      "0x43005dfe",
      "40038638",
      "4301ae00"
     ],
     [
      "0x43005e06",
      "800097c8",
      "430297c8"
     ],
     [
      "0x43005e28",
      "40038438",
      "4301ac00"
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
      "4301c200"
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
      "0x4300605a",
      "80004b70",
      "43024b70"
     ],
     [
      "0x43006060",
      "80009580",
      "43029580"
     ],
     [
      "0x43006090",
      "40004dc6",
      "43002882"
     ],
     [
      "0x4300609c",
      "4003b238",
      "4301da00"
     ],
     [
      "0x430060ba",
      "4003b638",
      "4301de00"
     ],
     [
      "0x430060cc",
      "4003b438",
      "4301dc00"
     ],
     [
      "0x430060e8",
      "4003a838",
      "4301d000"
     ],
     [
      "0x4300613a",
      "400052f8",
      "43002db4"
     ],
     [
      "0x4300614e",
      "4003bc38",
      "4301e400"
     ],
     [
      "0x430061d8",
      "4003b038",
      "4301d800"
     ],
     [
      "0x430061ea",
      "4003ae38",
      "4301d600"
     ],
     [
      "0x4300631c",
      "4003ac38",
      "4301d400"
     ],
     [
      "0x43006332",
      "4003ba38",
      "4301e200"
     ],
     [
      "0x43006344",
      "4003aa38",
      "4301d200"
     ],
     [
      "0x43006366",
      "4003b838",
      "4301e000"
     ],
     [
      "0x430063a4",
      "4003a438",
      "4301cc00"
     ],
     [
      "0x430063c2",
      "4003a238",
      "4301ca00"
     ],
     [
      "0x430063d6",
      "4003a638",
      "4301ce00"
     ],
     [
      "0x43006434",
      "40002596",
      "43000052"
     ],
     [
      "0x43006452",
      "40005728",
      "430031e4"
     ],
     [
      "0x43006460",
      "40004e6c",
      "43002928"
     ],
     [
      "0x4300647e",
      "40003c0e",
      "430016ca"
     ],
     [
      "0x43006488",
      "400058e8",
      "430033a4"
     ],
     [
      "0x43006494",
      "40003958",
      "43001414"
     ],
     [
      "0x4300649e",
      "4000290e",
      "430003ca"
     ],
     [
      "0x430064aa",
      "400044e2",
      "43001f9e"
     ],
     [
      "0x430064b8",
      "800096a4",
      "430296a4"
     ],
     [
      "0x430064be",
      "40003eb4",
      "43001970"
     ],
     [
      "0x430064cc",
      "800096a4",
      "430296a4"
     ],
     [
      "0x430064de",
      "800096a4",
      "430296a4"
     ],
     [
      "0x430064f0",
      "80008c60",
      "43028c60"
     ],
     [
      "0x43006510",
      "800096a4",
      "430296a4"
     ],
     [
      "0x43006516",
      "400049f4",
      "430024b0"
     ],
     [
      "0x4300652c",
      "400054e6",
      "43002fa2"
     ],
     [
      "0x43006538",
      "40004f74",
      "43002a30"
     ],
     [
      "0x43006544",
      "4000569a",
      "43003156"
     ],
     [
      "0x4300657c",
      "80008c60",
      "43028c60"
     ],
     [
      "0x43006590",
      "400047ea",
      "430022a6"
     ],
     [
      "0x43034904",
      "00000500",
      "00000700"
     ]
    ]
   }
  },
  {
   "id": "syntakt-sd-toy",
   "order": 24,
   "name": "Vrais moteurs du Syntakt en machines ajoutées : SDVtg (SD VINTAGE), SYToy (SY TOY)",
   "description": [
    "Moteurs du Syntakt (OS 1.41) extraits AU BUILD de TON Syntakt_OS1.41.syx, en machines ajoutées après",
    "les 6 d'origine (notes/20) : SDVtg = SD VINTAGE (machine 7), SYToy = SY TOY (machine 8).",
    "Potards propres, noms et défauts du Syntakt. Généré par tools/gen_syntakt_engines.py.",
    "Demande build.py --syntakt Syntakt_OS1.41.syx. Aucun octet Elektron dans ce fichier."
   ],
   "device": "Model:Cycles",
   "os": "1.13",
   "section": 3,
   "conflicts": [
    "sdvintage-7th",
    "sdvintage-exact",
    "sdvintage-snare",
    "syntakt-cp",
    "syntakt-cp-toy",
    "syntakt-sd-cp-toy",
    "syntakt-toy",
    "syntakt-vintage"
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
     "new": "7456"
    },
    {
     "off": 42318,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 42334,
     "old": "744c",
     "new": "7456"
    },
    {
     "off": 42372,
     "old": "704b",
     "new": "7055"
    },
    {
     "off": 42578,
     "old": "704b",
     "new": "7055"
    },
    {
     "off": 44552,
     "old": "724c",
     "new": "7256"
    },
    {
     "off": 44564,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 44586,
     "old": "724c",
     "new": "7256"
    },
    {
     "off": 44598,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 45028,
     "old": "724c",
     "new": "7256"
    },
    {
     "off": 45036,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 45174,
     "old": "724c",
     "new": "7256"
    },
    {
     "off": 45182,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 45338,
     "old": "724c",
     "new": "7256"
    },
    {
     "off": 45346,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 45658,
     "old": "724c",
     "new": "7256"
    },
    {
     "off": 45666,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 45804,
     "old": "724c",
     "new": "7256"
    },
    {
     "off": 45812,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 45960,
     "old": "724c",
     "new": "7256"
    },
    {
     "off": 45968,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 46406,
     "old": "704b",
     "new": "7055"
    },
    {
     "off": 82852,
     "old": "7005",
     "new": "7007"
    },
    {
     "off": 83114,
     "old": "7205",
     "new": "7207"
    },
    {
     "off": 83122,
     "old": "7005",
     "new": "7007"
    },
    {
     "off": 111260,
     "old": "7005",
     "new": "7001"
    },
    {
     "off": 119266,
     "old": "724c",
     "new": "7256"
    },
    {
     "off": 119278,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 120046,
     "old": "704b",
     "new": "7055"
    },
    {
     "off": 120066,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 120078,
     "old": "704b",
     "new": "7055"
    },
    {
     "off": 121894,
     "old": "724c",
     "new": "7256"
    },
    {
     "off": 121906,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 124122,
     "old": "202f0020226a0068",
     "new": "4eb9430332044e71"
    },
    {
     "off": 126758,
     "old": "704c",
     "new": "7056"
    },
    {
     "off": 126766,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 140924,
     "old": "704c",
     "new": "7056"
    },
    {
     "off": 140932,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 141054,
     "old": "724c",
     "new": "7256"
    },
    {
     "off": 141062,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 170616,
     "old": "744c",
     "new": "7456"
    },
    {
     "off": 170632,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 170648,
     "old": "744c",
     "new": "7456"
    },
    {
     "off": 176176,
     "old": "724c",
     "new": "7256"
    },
    {
     "off": 176184,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 289116,
     "old": "724c",
     "new": "7256"
    },
    {
     "off": 289124,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 318272,
     "old": "704c222f0004",
     "new": "4ef943033028"
    },
    {
     "off": 318300,
     "old": "7206202f0004",
     "new": "4ef943033120"
    },
    {
     "off": 318326,
     "old": "7205202f0004",
     "new": "4ef94303314a"
    },
    {
     "off": 318370,
     "old": "704c222f0004",
     "new": "4ef94303303e"
    },
    {
     "off": 319262,
     "old": "704b",
     "new": "7055"
    },
    {
     "off": 319278,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 319418,
     "old": "704c",
     "new": "7056"
    },
    {
     "off": 368312,
     "old": "487800c0",
     "new": "48780100"
    },
    {
     "off": 368318,
     "old": "40a79418",
     "new": "43035800"
    },
    {
     "off": 368350,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 368418,
     "old": "40a79418",
     "new": "43035800"
    },
    {
     "off": 368448,
     "old": "7005b085643e",
     "new": "4ef943033264"
    },
    {
     "off": 368488,
     "old": "704c",
     "new": "7056"
    },
    {
     "off": 368528,
     "old": "40a79418",
     "new": "43035800"
    },
    {
     "off": 368554,
     "old": "40a7ada4",
     "new": "43035a00"
    },
    {
     "off": 368872,
     "old": "724c",
     "new": "7256"
    },
    {
     "off": 368884,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 368906,
     "old": "724c202f0004",
     "new": "4ef94303321a"
    },
    {
     "off": 368918,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 368940,
     "old": "724c",
     "new": "7256"
    },
    {
     "off": 368952,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 368982,
     "old": "724c",
     "new": "7256"
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
     "new": "7255"
    },
    {
     "off": 369050,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 369100,
     "old": "724c",
     "new": "7256"
    },
    {
     "off": 369112,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 369150,
     "old": "724c",
     "new": "7256"
    },
    {
     "off": 369162,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 369192,
     "old": "724c",
     "new": "7256"
    },
    {
     "off": 369204,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 369244,
     "old": "704c",
     "new": "7056"
    },
    {
     "off": 369274,
     "old": "4010dce8",
     "new": "43034008"
    },
    {
     "off": 369318,
     "old": "7205",
     "new": "7207"
    },
    {
     "off": 369338,
     "old": "40a79418",
     "new": "43035800"
    },
    {
     "off": 369392,
     "old": "40a79418",
     "new": "43035800"
    },
    {
     "off": 369514,
     "old": "724b",
     "new": "7255"
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
     "new": "7255"
    },
    {
     "off": 369596,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 369616,
     "old": "724c",
     "new": "7256"
    },
    {
     "off": 369628,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 369656,
     "old": "724c",
     "new": "7256"
    },
    {
     "off": 369668,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 369690,
     "old": "724c",
     "new": "7256"
    },
    {
     "off": 369702,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 369724,
     "old": "724c",
     "new": "7256"
    },
    {
     "off": 369736,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 369758,
     "old": "724c",
     "new": "7256"
    },
    {
     "off": 369770,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 369904,
     "old": "7405b4816532",
     "new": "4ef943033070"
    },
    {
     "off": 369938,
     "old": "40a7ada4",
     "new": "43035a00"
    },
    {
     "off": 664032,
     "old": "7005",
     "new": "7007"
    },
    {
     "off": 664084,
     "old": "401177e4",
     "new": "43033800"
    },
    {
     "off": 664120,
     "old": "eb8c48780001",
     "new": "4ef9430330a4"
    },
    {
     "off": 664226,
     "old": "7850",
     "new": "7849"
    },
    {
     "off": 664296,
     "old": "7006",
     "new": "7008"
    },
    {
     "off": 670886,
     "old": "7005",
     "new": "7001"
    },
    {
     "off": 674244,
     "old": "700541e8000a",
     "new": "4ef9430330f8"
    },
    {
     "off": 674736,
     "old": "7005",
     "new": "7001"
    },
    {
     "off": 686444,
     "old": "40118628",
     "new": "43033820"
    },
    {
     "off": 686522,
     "old": "7205",
     "new": "7207"
    },
    {
     "off": 686532,
     "old": "40118640",
     "new": "43033880"
    },
    {
     "off": 686580,
     "old": "7005",
     "new": "7007"
    },
    {
     "off": 686614,
     "old": "40118610",
     "new": "43033840"
    },
    {
     "off": 724230,
     "old": "4016cae8",
     "new": "40154ae4"
    },
    {
     "off": 1492712,
     "old": "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
     "new": "41f9401aa14043f943000000203c0000e00022d8538066fa4feffff048d700f04ef9400004ba0000"
    }
   ],
   "append": {
    "at": "0x401aa140",
    "dest": "0x43000000",
    "size": 229376,
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
       "0x40008e0c"
      ]
     },
     {
      "dest": "0x430068c8",
      "syntakt": [
       "0x4000e488",
       "0x40010490"
      ]
     },
     {
      "dest": "0x430088d0",
      "syntakt": [
       "0x40014980",
       "0x40016b90"
      ]
     },
     {
      "dest": "0x4300aae0",
      "syntakt": [
       "0x40028438",
       "0x4003be38"
      ]
     },
     {
      "dest": "0x43036000",
      "syntakt": [
       "0x4003be38",
       "0x4003de38"
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
      "hex": "4fefffe048d77c0c247cbdcf77d82a6f002cd5cd220a263c0000031c4c431001242f0024286f00302f6f0028001c41f943032004203c534456312441b0ad002c660871b01800b480671a76011182a80041f94303200a223c534456312b41002c1183a8004ab94303200066564aad0038670001382c7c43020000267c43028a604eb9430000002d4b056c2f0e4eb94300199c47eb0030588f4dee0708b7fc43028be066dc323c0101203c01010101760123c04303200a23c34303200033c14303200e223c00000708200a4c0108002640d7fc43020000276d00340034222d003827410038276d003c003c4bf94303200a1035a8004a81670000ac4a00671c2f0b76014eb94300199c420027430038274200042682588f1b80a800220aed8942432441d5fc43032010154200225182356c00140024356c00160026356c00180028356c001a002a356c001c002c356c001e002e302c0020354000307140356c0024003235430034274003ec2f0b4eb94300001a588f4a82673c227c43005b302f4a002c2f4b0028716c00224cd77c0c0680ffffc000e788d0af001c2f4000244fef00204ed14a006700ff724cd77c0c4fef00204e75227c430065a460c22f0a2f02206f00104ab943032000661420080680000000804298b08866fa241f245f4e75202f0014243c0000031c0680bdcf77d84c42000043f94303200a4a31080066cc43f94303200473b10800b2af000c66bc243c0000070851814c0208002440d5fc430200004a816716227c43005f362f0a2f084e91256a00340038508f609c227c4300681460e82f2f000c2f2f000c2f2f000c487800064eb9430310004fef00104e752f2f00082f2f0008487800064eb9430311bc4fef000c4e752f2f000c2f2f000c2f2f000c487800084eb9430310004fef00104e752f2f00082f2f0008487800084eb9430311bc4fef000c4e750000"
     },
     {
      "dest": "0x43033000",
      "hex": "724cb081650000200c8000000056650470004e75724c90817205b0816504908160f67233d0814e75202f00046100ffd272644c010800068040a717544e75202f00046100ffbc72644c010800068040a71768487940a715002f2f000c2f004eb9400ddf604fef000c203c40a715004e757405b481650c7407b480650c4ef94005a8fa4ef94005a9284ef94005a91c7206b081660470014e757207b081660470044e754e7520036100ffe62800e588eb8c988048780001487800174878002045f940071da4227940fe32ccd3c42f092f024e924fef00304878000148780022d8b940fe384c487800602f042f024e924fef00144ef9400a268041e8000a2f082f2e001020026a0270007205b2806c0c6100ff7e7205b2806c0270054ef9400a4dde202f00047207b0816700005a7208b0816700005e7206b280640270ff724c4c010800068040a715404e75202f00047206b081670000307207b081670000347205b280651041f9401091b4713008007206b280640270ff724c4c010800068040a715404e7541f943035c0070196000000e41f943035c60701e600000024a28004c6600005e2f022f0a24482400487940a715d82f0a4eb9400f8f02508f487940a715dc486a00044eb9400f8f02508f41f940a715e043ea000872102f0120187233b0816d087237b2806d02d08222c053976aea588f70011540004c204a245f241f20084e75202f0024226a00687206b0816d0643f9430338604e75202f00040c800000004c650c0c800000004f620470064e750c8000000051650c0c8000000054620470074e750c8000000056650270002200e789ed88908141f943034000203008004e757006b085650000340c820000004c650e0c820000004f62067a06600000180c8200000051650e0c820000005462067a07600000024ef94005a3844ef94005a346"
     },
     {
      "dest": "0x43033800",
      "hex": "401300d8401300dd401300e3401300e940129960401300ee430338884303388e400aa08c400ab3b0400aa49c400aa998400aa7b8400aae88430312464303127a400aa3c4400ab6e8400aa712400aacc2400aa930400ab24c4303126243031296000000010000000200000003000000040000000500000006000000070000000800010203040506075344567467005359546f7900496e6861726d00494e484d004672657120436f6d706c65780046434d500050697463682053776565700053574550004d6f6420456e76656c6f7065004d454e5600466f726d00464f524d00496d7061637400494d50004272696768740042524947005061727469616c204465636179005041525400"
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
      "hex": "000000060000000b0000000000007f0000000000000000000010ffffffffffff000000000000060000000028430338944012996f4303389b000000060000000c0000000000007f0000006e00000000000011ffffffffffff000000000000060000000032430338a04012996f430338ad000000060000000d0000000000007f0000004a00000000000012ffffffffffff00000000000006000000003c430338b24012996f430338be000000060000000e0000000000007f0000005000000000000013ffffffffffff000000000000060000000046430338c34012996f430338d000000007000000120000000000007f0000002100000000000050ffff0000009a00000000000006000000001e401298784012988240129886000000060000000b0000000000007f0000001800000000000010ffffffffffff000000000000060000000028430338d54012996f430338da000000060000000c0000000000007f0000003c00000000000011ffffffffffff000000000000060000000032430338df4012996f430338e6000000060000000d0000000000007f0000006e00000000000012ffffffffffff00000000000006000000003c430338ea4012996f430338f1000000060000000e0000000000007f0000004000000000000013ffffffffffff000000000000060000000046430338f64012996f4303390400000007000000120000000000007f0000003c00000000000050ffff0000009a00000000000006000000001e401298784012988240129886"
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
      "43008acc"
     ],
     [
      "0x43001d82",
      "40014980",
      "430088d0"
     ],
     [
      "0x43002e04",
      "40014b80",
      "43008ad0"
     ],
     [
      "0x43002e22",
      "40015b80",
      "43009ad0"
     ],
     [
      "0x43002e3a",
      "80004a50",
      "43024a50"
     ],
     [
      "0x43002e66",
      "4000f48c",
      "430078cc"
     ],
     [
      "0x43002e9c",
      "4000e488",
      "430068c8"
     ],
     [
      "0x43002eda",
      "4000f48c",
      "430078cc"
     ],
     [
      "0x43002f2c",
      "4000e488",
      "430068c8"
     ],
     [
      "0x43002f3a",
      "4000e488",
      "430068c8"
     ],
     [
      "0x43002f4a",
      "80004a50",
      "43024a50"
     ],
     [
      "0x43002fb2",
      "80004a50",
      "43024a50"
     ],
     [
      "0x43002fc2",
      "80004a70",
      "43024a70"
     ],
     [
      "0x43003000",
      "80004a70",
      "43024a70"
     ],
     [
      "0x43003006",
      "80004af0",
      "43024af0"
     ],
     [
      "0x43003014",
      "80004a50",
      "43024a50"
     ],
     [
      "0x4300301e",
      "80004a54",
      "43024a54"
     ],
     [
      "0x43003028",
      "80004a58",
      "43024a58"
     ],
     [
      "0x43003032",
      "80004a5c",
      "43024a5c"
     ],
     [
      "0x4300303c",
      "80004a60",
      "43024a60"
     ],
     [
      "0x4300304c",
      "80004a64",
      "43024a64"
     ],
     [
      "0x4300307c",
      "80004af0",
      "43024af0"
     ],
     [
      "0x4300309a",
      "80004a68",
      "43024a68"
     ],
     [
      "0x430030a0",
      "80004a6c",
      "43024a6c"
     ],
     [
      "0x4300330a",
      "8000a07c",
      "4302a07c"
     ],
     [
      "0x43005b42",
      "40004dc6",
      "43002882"
     ],
     [
      "0x43005b4e",
      "40039238",
      "4301b8e0"
     ],
     [
      "0x43005b7c",
      "40039838",
      "4301bee0"
     ],
     [
      "0x43005b8e",
      "40039638",
      "4301bce0"
     ],
     [
      "0x43005ba0",
      "40039438",
      "4301bae0"
     ],
     [
      "0x43005bb6",
      "40039038",
      "4301b6e0"
     ],
     [
      "0x43005bce",
      "40038e38",
      "4301b4e0"
     ],
     [
      "0x43005be6",
      "40038c38",
      "4301b2e0"
     ],
     [
      "0x43005c12",
      "4003a038",
      "4301c6e0"
     ],
     [
      "0x43005c1c",
      "40039e38",
      "4301c4e0"
     ],
     [
      "0x43005c3a",
      "40039c38",
      "4301c2e0"
     ],
     [
      "0x43005c76",
      "40028438",
      "4300aae0"
     ],
     [
      "0x43005c92",
      "40038a38",
      "4301b0e0"
     ],
     [
      "0x43005cae",
      "40038838",
      "4301aee0"
     ],
     [
      "0x43005dea",
      "800097c8",
      "430297c8"
     ],
     [
      "0x43005dfe",
      "40038638",
      "4301ace0"
     ],
     [
      "0x43005e06",
      "800097c8",
      "430297c8"
     ],
     [
      "0x43005e28",
      "40038438",
      "4301aae0"
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
      "4301c0e0"
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
      "0x4300605a",
      "80004b70",
      "43024b70"
     ],
     [
      "0x43006060",
      "80009580",
      "43029580"
     ],
     [
      "0x43006090",
      "40004dc6",
      "43002882"
     ],
     [
      "0x4300609c",
      "4003b238",
      "4301d8e0"
     ],
     [
      "0x430060ba",
      "4003b638",
      "4301dce0"
     ],
     [
      "0x430060cc",
      "4003b438",
      "4301dae0"
     ],
     [
      "0x430060e8",
      "4003a838",
      "4301cee0"
     ],
     [
      "0x4300613a",
      "400052f8",
      "43002db4"
     ],
     [
      "0x4300614e",
      "4003bc38",
      "4301e2e0"
     ],
     [
      "0x430061d8",
      "4003b038",
      "4301d6e0"
     ],
     [
      "0x430061ea",
      "4003ae38",
      "4301d4e0"
     ],
     [
      "0x4300631c",
      "4003ac38",
      "4301d2e0"
     ],
     [
      "0x43006332",
      "4003ba38",
      "4301e0e0"
     ],
     [
      "0x43006344",
      "4003aa38",
      "4301d0e0"
     ],
     [
      "0x43006366",
      "4003b838",
      "4301dee0"
     ],
     [
      "0x430063a4",
      "4003a438",
      "4301cae0"
     ],
     [
      "0x430063c2",
      "4003a238",
      "4301c8e0"
     ],
     [
      "0x430063d6",
      "4003a638",
      "4301cce0"
     ],
     [
      "0x43006434",
      "40002596",
      "43000052"
     ],
     [
      "0x43006452",
      "40005728",
      "430031e4"
     ],
     [
      "0x43006460",
      "40004e6c",
      "43002928"
     ],
     [
      "0x4300647e",
      "40003c0e",
      "430016ca"
     ],
     [
      "0x43006488",
      "400058e8",
      "430033a4"
     ],
     [
      "0x43006494",
      "40003958",
      "43001414"
     ],
     [
      "0x4300649e",
      "4000290e",
      "430003ca"
     ],
     [
      "0x430064aa",
      "400044e2",
      "43001f9e"
     ],
     [
      "0x430064b8",
      "800096a4",
      "430296a4"
     ],
     [
      "0x430064be",
      "40003eb4",
      "43001970"
     ],
     [
      "0x430064cc",
      "800096a4",
      "430296a4"
     ],
     [
      "0x430064de",
      "800096a4",
      "430296a4"
     ],
     [
      "0x430064f0",
      "80008c60",
      "43028c60"
     ],
     [
      "0x43006510",
      "800096a4",
      "430296a4"
     ],
     [
      "0x43006516",
      "400049f4",
      "430024b0"
     ],
     [
      "0x4300652c",
      "400054e6",
      "43002fa2"
     ],
     [
      "0x43006538",
      "40004f74",
      "43002a30"
     ],
     [
      "0x43006544",
      "4000569a",
      "43003156"
     ],
     [
      "0x4300657c",
      "80008c60",
      "43028c60"
     ],
     [
      "0x43006590",
      "400047ea",
      "430022a6"
     ],
     [
      "0x430065c2",
      "4003dc38",
      "43037e00"
     ],
     [
      "0x430065c8",
      "40004dc6",
      "43002882"
     ],
     [
      "0x430065e6",
      "4003c838",
      "43036a00"
     ],
     [
      "0x430065f8",
      "4003c638",
      "43036800"
     ],
     [
      "0x4300660a",
      "4003c438",
      "43036600"
     ],
     [
      "0x4300661c",
      "4003c238",
      "43036400"
     ],
     [
      "0x43006626",
      "800098ec",
      "430298ec"
     ],
     [
      "0x4300663a",
      "4003d038",
      "43037200"
     ],
     [
      "0x43006658",
      "4003d238",
      "43037400"
     ],
     [
      "0x43006674",
      "4003c038",
      "43036200"
     ],
     [
      "0x4300667c",
      "80004b70",
      "43024b70"
     ],
     [
      "0x430066b6",
      "4003ce38",
      "43037000"
     ],
     [
      "0x430066cc",
      "4003cc38",
      "43036e00"
     ],
     [
      "0x430066de",
      "4003ca38",
      "43036c00"
     ],
     [
      "0x430067b2",
      "4003da38",
      "43037c00"
     ],
     [
      "0x430067c4",
      "4003d838",
      "43037a00"
     ],
     [
      "0x430067d6",
      "4003d638",
      "43037800"
     ],
     [
      "0x430067e8",
      "4003d438",
      "43037600"
     ],
     [
      "0x43006804",
      "40002596",
      "43000052"
     ],
     [
      "0x4300682c",
      "40003c0e",
      "430016ca"
     ],
     [
      "0x43006838",
      "400035de",
      "4300109a"
     ],
     [
      "0x43006842",
      "4000290e",
      "430003ca"
     ],
     [
      "0x4300686e",
      "80008c60",
      "43028c60"
     ],
     [
      "0x43006878",
      "80009580",
      "43029580"
     ],
     [
      "0x43006882",
      "800096a4",
      "430296a4"
     ],
     [
      "0x4300688c",
      "800097c8",
      "430297c8"
     ],
     [
      "0x43006896",
      "40004cd6",
      "43002792"
     ],
     [
      "0x4300689e",
      "40003d42",
      "430017fe"
     ],
     [
      "0x430068ac",
      "400045a0",
      "4300205c"
     ],
     [
      "0x430068b6",
      "400047ea",
      "430022a6"
     ],
     [
      "0x43034904",
      "00000500",
      "00000700"
     ]
    ]
   }
  },
  {
   "id": "syntakt-cp-toy",
   "order": 24,
   "name": "Vrais moteurs du Syntakt en machines ajoutées : CPVtg (CP VINTAGE), SYToy (SY TOY)",
   "description": [
    "Moteurs du Syntakt (OS 1.41) extraits AU BUILD de TON Syntakt_OS1.41.syx, en machines ajoutées après",
    "les 6 d'origine (notes/20) : CPVtg = CP VINTAGE (machine 7), SYToy = SY TOY (machine 8).",
    "Potards propres, noms et défauts du Syntakt. Généré par tools/gen_syntakt_engines.py.",
    "Demande build.py --syntakt Syntakt_OS1.41.syx. Aucun octet Elektron dans ce fichier."
   ],
   "device": "Model:Cycles",
   "os": "1.13",
   "section": 3,
   "conflicts": [
    "sdvintage-7th",
    "sdvintage-exact",
    "sdvintage-snare",
    "syntakt-cp",
    "syntakt-sd-cp-toy",
    "syntakt-sd-toy",
    "syntakt-toy",
    "syntakt-vintage"
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
     "new": "7456"
    },
    {
     "off": 42318,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 42334,
     "old": "744c",
     "new": "7456"
    },
    {
     "off": 42372,
     "old": "704b",
     "new": "7055"
    },
    {
     "off": 42578,
     "old": "704b",
     "new": "7055"
    },
    {
     "off": 44552,
     "old": "724c",
     "new": "7256"
    },
    {
     "off": 44564,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 44586,
     "old": "724c",
     "new": "7256"
    },
    {
     "off": 44598,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 45028,
     "old": "724c",
     "new": "7256"
    },
    {
     "off": 45036,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 45174,
     "old": "724c",
     "new": "7256"
    },
    {
     "off": 45182,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 45338,
     "old": "724c",
     "new": "7256"
    },
    {
     "off": 45346,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 45658,
     "old": "724c",
     "new": "7256"
    },
    {
     "off": 45666,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 45804,
     "old": "724c",
     "new": "7256"
    },
    {
     "off": 45812,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 45960,
     "old": "724c",
     "new": "7256"
    },
    {
     "off": 45968,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 46406,
     "old": "704b",
     "new": "7055"
    },
    {
     "off": 82852,
     "old": "7005",
     "new": "7007"
    },
    {
     "off": 83114,
     "old": "7205",
     "new": "7207"
    },
    {
     "off": 83122,
     "old": "7005",
     "new": "7007"
    },
    {
     "off": 111260,
     "old": "7005",
     "new": "7001"
    },
    {
     "off": 119266,
     "old": "724c",
     "new": "7256"
    },
    {
     "off": 119278,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 120046,
     "old": "704b",
     "new": "7055"
    },
    {
     "off": 120066,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 120078,
     "old": "704b",
     "new": "7055"
    },
    {
     "off": 121894,
     "old": "724c",
     "new": "7256"
    },
    {
     "off": 121906,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 124122,
     "old": "202f0020226a0068",
     "new": "4eb9430332044e71"
    },
    {
     "off": 126758,
     "old": "704c",
     "new": "7056"
    },
    {
     "off": 126766,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 140924,
     "old": "704c",
     "new": "7056"
    },
    {
     "off": 140932,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 141054,
     "old": "724c",
     "new": "7256"
    },
    {
     "off": 141062,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 170616,
     "old": "744c",
     "new": "7456"
    },
    {
     "off": 170632,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 170648,
     "old": "744c",
     "new": "7456"
    },
    {
     "off": 176176,
     "old": "724c",
     "new": "7256"
    },
    {
     "off": 176184,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 289116,
     "old": "724c",
     "new": "7256"
    },
    {
     "off": 289124,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 318272,
     "old": "704c222f0004",
     "new": "4ef943033028"
    },
    {
     "off": 318300,
     "old": "7206202f0004",
     "new": "4ef943033120"
    },
    {
     "off": 318326,
     "old": "7205202f0004",
     "new": "4ef94303314a"
    },
    {
     "off": 318370,
     "old": "704c222f0004",
     "new": "4ef94303303e"
    },
    {
     "off": 319262,
     "old": "704b",
     "new": "7055"
    },
    {
     "off": 319278,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 319418,
     "old": "704c",
     "new": "7056"
    },
    {
     "off": 368312,
     "old": "487800c0",
     "new": "48780100"
    },
    {
     "off": 368318,
     "old": "40a79418",
     "new": "43035800"
    },
    {
     "off": 368350,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 368418,
     "old": "40a79418",
     "new": "43035800"
    },
    {
     "off": 368448,
     "old": "7005b085643e",
     "new": "4ef943033264"
    },
    {
     "off": 368488,
     "old": "704c",
     "new": "7056"
    },
    {
     "off": 368528,
     "old": "40a79418",
     "new": "43035800"
    },
    {
     "off": 368554,
     "old": "40a7ada4",
     "new": "43035a00"
    },
    {
     "off": 368872,
     "old": "724c",
     "new": "7256"
    },
    {
     "off": 368884,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 368906,
     "old": "724c202f0004",
     "new": "4ef94303321a"
    },
    {
     "off": 368918,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 368940,
     "old": "724c",
     "new": "7256"
    },
    {
     "off": 368952,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 368982,
     "old": "724c",
     "new": "7256"
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
     "new": "7255"
    },
    {
     "off": 369050,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 369100,
     "old": "724c",
     "new": "7256"
    },
    {
     "off": 369112,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 369150,
     "old": "724c",
     "new": "7256"
    },
    {
     "off": 369162,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 369192,
     "old": "724c",
     "new": "7256"
    },
    {
     "off": 369204,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 369244,
     "old": "704c",
     "new": "7056"
    },
    {
     "off": 369274,
     "old": "4010dce8",
     "new": "43034008"
    },
    {
     "off": 369318,
     "old": "7205",
     "new": "7207"
    },
    {
     "off": 369338,
     "old": "40a79418",
     "new": "43035800"
    },
    {
     "off": 369392,
     "old": "40a79418",
     "new": "43035800"
    },
    {
     "off": 369514,
     "old": "724b",
     "new": "7255"
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
     "new": "7255"
    },
    {
     "off": 369596,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 369616,
     "old": "724c",
     "new": "7256"
    },
    {
     "off": 369628,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 369656,
     "old": "724c",
     "new": "7256"
    },
    {
     "off": 369668,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 369690,
     "old": "724c",
     "new": "7256"
    },
    {
     "off": 369702,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 369724,
     "old": "724c",
     "new": "7256"
    },
    {
     "off": 369736,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 369758,
     "old": "724c",
     "new": "7256"
    },
    {
     "off": 369770,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 369904,
     "old": "7405b4816532",
     "new": "4ef943033070"
    },
    {
     "off": 369938,
     "old": "40a7ada4",
     "new": "43035a00"
    },
    {
     "off": 664032,
     "old": "7005",
     "new": "7007"
    },
    {
     "off": 664084,
     "old": "401177e4",
     "new": "43033800"
    },
    {
     "off": 664120,
     "old": "eb8c48780001",
     "new": "4ef9430330a4"
    },
    {
     "off": 664226,
     "old": "7850",
     "new": "7849"
    },
    {
     "off": 664296,
     "old": "7006",
     "new": "7008"
    },
    {
     "off": 670886,
     "old": "7005",
     "new": "7001"
    },
    {
     "off": 674244,
     "old": "700541e8000a",
     "new": "4ef9430330f8"
    },
    {
     "off": 674736,
     "old": "7005",
     "new": "7001"
    },
    {
     "off": 686444,
     "old": "40118628",
     "new": "43033820"
    },
    {
     "off": 686522,
     "old": "7205",
     "new": "7207"
    },
    {
     "off": 686532,
     "old": "40118640",
     "new": "43033880"
    },
    {
     "off": 686580,
     "old": "7005",
     "new": "7007"
    },
    {
     "off": 686614,
     "old": "40118610",
     "new": "43033840"
    },
    {
     "off": 724230,
     "old": "4016cae8",
     "new": "40154ae4"
    },
    {
     "off": 1492712,
     "old": "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
     "new": "41f9401aa14043f943000000203c0000e00022d8538066fa4feffff048d700f04ef9400004ba0000"
    }
   ],
   "append": {
    "at": "0x401aa140",
    "dest": "0x43000000",
    "size": 229376,
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
       "0x40008e0c"
      ]
     },
     {
      "dest": "0x430068c8",
      "syntakt": [
       "0x4000e488",
       "0x40010490"
      ]
     },
     {
      "dest": "0x430088d0",
      "syntakt": [
       "0x40014980",
       "0x40016b90"
      ]
     },
     {
      "dest": "0x4300aae0",
      "syntakt": [
       "0x40028438",
       "0x4003be38"
      ]
     },
     {
      "dest": "0x43036000",
      "syntakt": [
       "0x4003be38",
       "0x4003de38"
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
      "hex": "4fefffe048d77c0c247cbdcf77d82a6f002cd5cd220a263c0000031c4c431001242f0024286f00302f6f0028001c41f943032004203c534456312441b0ad002c660871b01800b480671a76011182a80041f94303200a223c534456312b41002c1183a8004ab94303200066564aad0038670001382c7c43020000267c43028a604eb9430000002d4b056c2f0e4eb94300199c47eb0030588f4dee0708b7fc43028be066dc323c0101203c01010101760123c04303200a23c34303200033c14303200e223c00000708200a4c0108002640d7fc43020000276d00340034222d003827410038276d003c003c4bf94303200a1035a8004a81670000ac4a00671c2f0b76014eb94300199c420027430038274200042682588f1b80a800220aed8942432441d5fc43032010154200225182356c00140024356c00160026356c00180028356c001a002a356c001c002c356c001e002e302c0020354000307140356c0024003235430034274003ec2f0b4eb94300001a588f4a82673c227c4300603c2f4a002c2f4b0028716c00224cd77c0c0680ffffc000e788d0af001c2f4000244fef00204ed14a006700ff724cd77c0c4fef00204e75227c430065a460c22f0a2f02206f00104ab943032000661420080680000000804298b08866fa241f245f4e75202f0014243c0000031c0680bdcf77d84c42000043f94303200a4a31080066cc43f94303200473b10800b2af000c66bc243c0000070851814c0208002440d5fc430200004a816716227c430064442f0a2f084e91256a00340038508f609c227c4300681460e82f2f000c2f2f000c2f2f000c487800074eb9430310004fef00104e752f2f00082f2f0008487800074eb9430311bc4fef000c4e752f2f000c2f2f000c2f2f000c487800084eb9430310004fef00104e752f2f00082f2f0008487800084eb9430311bc4fef000c4e750000"
     },
     {
      "dest": "0x43033000",
      "hex": "724cb081650000200c8000000056650470004e75724c90817205b0816504908160f67233d0814e75202f00046100ffd272644c010800068040a717544e75202f00046100ffbc72644c010800068040a71768487940a715002f2f000c2f004eb9400ddf604fef000c203c40a715004e757405b481650c7407b480650c4ef94005a8fa4ef94005a9284ef94005a91c7206b081660470034e757207b081660470044e754e7520036100ffe62800e588eb8c988048780001487800174878002045f940071da4227940fe32ccd3c42f092f024e924fef00304878000148780022d8b940fe384c487800602f042f024e924fef00144ef9400a268041e8000a2f082f2e001020026a0270007205b2806c0c6100ff7e7205b2806c0270054ef9400a4dde202f00047207b0816700005a7208b0816700005e7206b280640270ff724c4c010800068040a715404e75202f00047206b081670000307207b081670000347205b280651041f9401091b4713008007206b280640270ff724c4c010800068040a715404e7541f943035c0070196000000e41f943035c60701e600000024a28004c6600005e2f022f0a24482400487940a715d82f0a4eb9400f8f02508f487940a715dc486a00044eb9400f8f02508f41f940a715e043ea000872102f0120187233b0816d087237b2806d02d08222c053976aea588f70011540004c204a245f241f20084e75202f0024226a00687206b0816d0643f9430338604e75202f00040c800000004c650c0c800000004f620470064e750c8000000051650c0c8000000054620470074e750c8000000056650270002200e789ed88908141f943034000203008004e757006b085650000340c820000004c650e0c820000004f62067a06600000180c8200000051650e0c820000005462067a07600000024ef94005a3844ef94005a346"
     },
     {
      "dest": "0x43033800",
      "hex": "401300d8401300dd401300e3401300e940129960401300ee430338884303388e400aa08c400ab3b0400aa49c400aa998400aa7b8400aae88430312464303127a400aa3c4400ab6e8400aa712400aacc2400aa930400ab24c4303126243031296000000010000000200000003000000040000000500000006000000070000000800010203040506074350567467005359546f7900426f6479204368617200424f44590042616c616e63650042414c0053706163696e67204372756e6368005350435200426f647920456e76656c6f70650042454e5600466f726d00464f524d00496d7061637400494d50004272696768740042524947005061727469616c204465636179005041525400"
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
      "hex": "000000060000000b0000000000007f0000001800000000000010ffffffffffff000000000000060000000028430338944012996f4303389e000000060000000c0000000000007f0000001900000000000011ffffffffffff000000000000060000000032430338a34012996f430338ab000000060000000d0000000000007f0000002e00000000000012ffffffffffff00000000000006000000003c430338af4012996f430338be000000060000000e0000000000007f0000002500000000000013ffffffffffff000000000000060000000046430338c34012996f430338d100000007000000120000000000007f0000002000000000000050ffff0000009a00000000000006000000001e401298784012988240129886000000060000000b0000000000007f0000001800000000000010ffffffffffff000000000000060000000028430338d64012996f430338db000000060000000c0000000000007f0000003c00000000000011ffffffffffff000000000000060000000032430338e04012996f430338e7000000060000000d0000000000007f0000006e00000000000012ffffffffffff00000000000006000000003c430338eb4012996f430338f2000000060000000e0000000000007f0000004000000000000013ffffffffffff000000000000060000000046430338f74012996f4303390500000007000000120000000000007f0000003c00000000000050ffff0000009a00000000000006000000001e401298784012988240129886"
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
      "43008acc"
     ],
     [
      "0x43001d82",
      "40014980",
      "430088d0"
     ],
     [
      "0x43002e04",
      "40014b80",
      "43008ad0"
     ],
     [
      "0x43002e22",
      "40015b80",
      "43009ad0"
     ],
     [
      "0x43002e3a",
      "80004a50",
      "43024a50"
     ],
     [
      "0x43002e66",
      "4000f48c",
      "430078cc"
     ],
     [
      "0x43002e9c",
      "4000e488",
      "430068c8"
     ],
     [
      "0x43002eda",
      "4000f48c",
      "430078cc"
     ],
     [
      "0x43002f2c",
      "4000e488",
      "430068c8"
     ],
     [
      "0x43002f3a",
      "4000e488",
      "430068c8"
     ],
     [
      "0x43002f4a",
      "80004a50",
      "43024a50"
     ],
     [
      "0x43002fb2",
      "80004a50",
      "43024a50"
     ],
     [
      "0x43002fc2",
      "80004a70",
      "43024a70"
     ],
     [
      "0x43003000",
      "80004a70",
      "43024a70"
     ],
     [
      "0x43003006",
      "80004af0",
      "43024af0"
     ],
     [
      "0x43003014",
      "80004a50",
      "43024a50"
     ],
     [
      "0x4300301e",
      "80004a54",
      "43024a54"
     ],
     [
      "0x43003028",
      "80004a58",
      "43024a58"
     ],
     [
      "0x43003032",
      "80004a5c",
      "43024a5c"
     ],
     [
      "0x4300303c",
      "80004a60",
      "43024a60"
     ],
     [
      "0x4300304c",
      "80004a64",
      "43024a64"
     ],
     [
      "0x4300307c",
      "80004af0",
      "43024af0"
     ],
     [
      "0x4300309a",
      "80004a68",
      "43024a68"
     ],
     [
      "0x430030a0",
      "80004a6c",
      "43024a6c"
     ],
     [
      "0x4300330a",
      "8000a07c",
      "4302a07c"
     ],
     [
      "0x43005b42",
      "40004dc6",
      "43002882"
     ],
     [
      "0x43005b4e",
      "40039238",
      "4301b8e0"
     ],
     [
      "0x43005b7c",
      "40039838",
      "4301bee0"
     ],
     [
      "0x43005b8e",
      "40039638",
      "4301bce0"
     ],
     [
      "0x43005ba0",
      "40039438",
      "4301bae0"
     ],
     [
      "0x43005bb6",
      "40039038",
      "4301b6e0"
     ],
     [
      "0x43005bce",
      "40038e38",
      "4301b4e0"
     ],
     [
      "0x43005be6",
      "40038c38",
      "4301b2e0"
     ],
     [
      "0x43005c12",
      "4003a038",
      "4301c6e0"
     ],
     [
      "0x43005c1c",
      "40039e38",
      "4301c4e0"
     ],
     [
      "0x43005c3a",
      "40039c38",
      "4301c2e0"
     ],
     [
      "0x43005c76",
      "40028438",
      "4300aae0"
     ],
     [
      "0x43005c92",
      "40038a38",
      "4301b0e0"
     ],
     [
      "0x43005cae",
      "40038838",
      "4301aee0"
     ],
     [
      "0x43005dea",
      "800097c8",
      "430297c8"
     ],
     [
      "0x43005dfe",
      "40038638",
      "4301ace0"
     ],
     [
      "0x43005e06",
      "800097c8",
      "430297c8"
     ],
     [
      "0x43005e28",
      "40038438",
      "4301aae0"
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
      "4301c0e0"
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
      "0x4300605a",
      "80004b70",
      "43024b70"
     ],
     [
      "0x43006060",
      "80009580",
      "43029580"
     ],
     [
      "0x43006090",
      "40004dc6",
      "43002882"
     ],
     [
      "0x4300609c",
      "4003b238",
      "4301d8e0"
     ],
     [
      "0x430060ba",
      "4003b638",
      "4301dce0"
     ],
     [
      "0x430060cc",
      "4003b438",
      "4301dae0"
     ],
     [
      "0x430060e8",
      "4003a838",
      "4301cee0"
     ],
     [
      "0x4300613a",
      "400052f8",
      "43002db4"
     ],
     [
      "0x4300614e",
      "4003bc38",
      "4301e2e0"
     ],
     [
      "0x430061d8",
      "4003b038",
      "4301d6e0"
     ],
     [
      "0x430061ea",
      "4003ae38",
      "4301d4e0"
     ],
     [
      "0x4300631c",
      "4003ac38",
      "4301d2e0"
     ],
     [
      "0x43006332",
      "4003ba38",
      "4301e0e0"
     ],
     [
      "0x43006344",
      "4003aa38",
      "4301d0e0"
     ],
     [
      "0x43006366",
      "4003b838",
      "4301dee0"
     ],
     [
      "0x430063a4",
      "4003a438",
      "4301cae0"
     ],
     [
      "0x430063c2",
      "4003a238",
      "4301c8e0"
     ],
     [
      "0x430063d6",
      "4003a638",
      "4301cce0"
     ],
     [
      "0x43006434",
      "40002596",
      "43000052"
     ],
     [
      "0x43006452",
      "40005728",
      "430031e4"
     ],
     [
      "0x43006460",
      "40004e6c",
      "43002928"
     ],
     [
      "0x4300647e",
      "40003c0e",
      "430016ca"
     ],
     [
      "0x43006488",
      "400058e8",
      "430033a4"
     ],
     [
      "0x43006494",
      "40003958",
      "43001414"
     ],
     [
      "0x4300649e",
      "4000290e",
      "430003ca"
     ],
     [
      "0x430064aa",
      "400044e2",
      "43001f9e"
     ],
     [
      "0x430064b8",
      "800096a4",
      "430296a4"
     ],
     [
      "0x430064be",
      "40003eb4",
      "43001970"
     ],
     [
      "0x430064cc",
      "800096a4",
      "430296a4"
     ],
     [
      "0x430064de",
      "800096a4",
      "430296a4"
     ],
     [
      "0x430064f0",
      "80008c60",
      "43028c60"
     ],
     [
      "0x43006510",
      "800096a4",
      "430296a4"
     ],
     [
      "0x43006516",
      "400049f4",
      "430024b0"
     ],
     [
      "0x4300652c",
      "400054e6",
      "43002fa2"
     ],
     [
      "0x43006538",
      "40004f74",
      "43002a30"
     ],
     [
      "0x43006544",
      "4000569a",
      "43003156"
     ],
     [
      "0x4300657c",
      "80008c60",
      "43028c60"
     ],
     [
      "0x43006590",
      "400047ea",
      "430022a6"
     ],
     [
      "0x430065c2",
      "4003dc38",
      "43037e00"
     ],
     [
      "0x430065c8",
      "40004dc6",
      "43002882"
     ],
     [
      "0x430065e6",
      "4003c838",
      "43036a00"
     ],
     [
      "0x430065f8",
      "4003c638",
      "43036800"
     ],
     [
      "0x4300660a",
      "4003c438",
      "43036600"
     ],
     [
      "0x4300661c",
      "4003c238",
      "43036400"
     ],
     [
      "0x43006626",
      "800098ec",
      "430298ec"
     ],
     [
      "0x4300663a",
      "4003d038",
      "43037200"
     ],
     [
      "0x43006658",
      "4003d238",
      "43037400"
     ],
     [
      "0x43006674",
      "4003c038",
      "43036200"
     ],
     [
      "0x4300667c",
      "80004b70",
      "43024b70"
     ],
     [
      "0x430066b6",
      "4003ce38",
      "43037000"
     ],
     [
      "0x430066cc",
      "4003cc38",
      "43036e00"
     ],
     [
      "0x430066de",
      "4003ca38",
      "43036c00"
     ],
     [
      "0x430067b2",
      "4003da38",
      "43037c00"
     ],
     [
      "0x430067c4",
      "4003d838",
      "43037a00"
     ],
     [
      "0x430067d6",
      "4003d638",
      "43037800"
     ],
     [
      "0x430067e8",
      "4003d438",
      "43037600"
     ],
     [
      "0x43006804",
      "40002596",
      "43000052"
     ],
     [
      "0x4300682c",
      "40003c0e",
      "430016ca"
     ],
     [
      "0x43006838",
      "400035de",
      "4300109a"
     ],
     [
      "0x43006842",
      "4000290e",
      "430003ca"
     ],
     [
      "0x4300686e",
      "80008c60",
      "43028c60"
     ],
     [
      "0x43006878",
      "80009580",
      "43029580"
     ],
     [
      "0x43006882",
      "800096a4",
      "430296a4"
     ],
     [
      "0x4300688c",
      "800097c8",
      "430297c8"
     ],
     [
      "0x43006896",
      "40004cd6",
      "43002792"
     ],
     [
      "0x4300689e",
      "40003d42",
      "430017fe"
     ],
     [
      "0x430068ac",
      "400045a0",
      "4300205c"
     ],
     [
      "0x430068b6",
      "400047ea",
      "430022a6"
     ],
     [
      "0x43034904",
      "00000500",
      "00000700"
     ]
    ]
   }
  },
  {
   "id": "syntakt-sd-cp-toy",
   "order": 24,
   "name": "Vrais moteurs du Syntakt en machines ajoutées : SDVtg (SD VINTAGE), CPVtg (CP VINTAGE), SYToy (SY TOY)",
   "description": [
    "Moteurs du Syntakt (OS 1.41) extraits AU BUILD de TON Syntakt_OS1.41.syx, en machines ajoutées après",
    "les 6 d'origine (notes/20) : SDVtg = SD VINTAGE (machine 7), CPVtg = CP VINTAGE (machine 8), SYToy = SY TOY (machine 9).",
    "Potards propres, noms et défauts du Syntakt. Généré par tools/gen_syntakt_engines.py.",
    "Demande build.py --syntakt Syntakt_OS1.41.syx. Aucun octet Elektron dans ce fichier."
   ],
   "device": "Model:Cycles",
   "os": "1.13",
   "section": 3,
   "conflicts": [
    "sdvintage-7th",
    "sdvintage-exact",
    "sdvintage-snare",
    "syntakt-cp",
    "syntakt-cp-toy",
    "syntakt-sd-toy",
    "syntakt-toy",
    "syntakt-vintage"
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
     "new": "745b"
    },
    {
     "off": 42318,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 42334,
     "old": "744c",
     "new": "745b"
    },
    {
     "off": 42372,
     "old": "704b",
     "new": "705a"
    },
    {
     "off": 42578,
     "old": "704b",
     "new": "705a"
    },
    {
     "off": 44552,
     "old": "724c",
     "new": "725b"
    },
    {
     "off": 44564,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 44586,
     "old": "724c",
     "new": "725b"
    },
    {
     "off": 44598,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 45028,
     "old": "724c",
     "new": "725b"
    },
    {
     "off": 45036,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 45174,
     "old": "724c",
     "new": "725b"
    },
    {
     "off": 45182,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 45338,
     "old": "724c",
     "new": "725b"
    },
    {
     "off": 45346,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 45658,
     "old": "724c",
     "new": "725b"
    },
    {
     "off": 45666,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 45804,
     "old": "724c",
     "new": "725b"
    },
    {
     "off": 45812,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 45960,
     "old": "724c",
     "new": "725b"
    },
    {
     "off": 45968,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 46406,
     "old": "704b",
     "new": "705a"
    },
    {
     "off": 82852,
     "old": "7005",
     "new": "7008"
    },
    {
     "off": 83114,
     "old": "7205",
     "new": "7208"
    },
    {
     "off": 83122,
     "old": "7005",
     "new": "7008"
    },
    {
     "off": 111260,
     "old": "7005",
     "new": "7001"
    },
    {
     "off": 119266,
     "old": "724c",
     "new": "725b"
    },
    {
     "off": 119278,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 120046,
     "old": "704b",
     "new": "705a"
    },
    {
     "off": 120066,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 120078,
     "old": "704b",
     "new": "705a"
    },
    {
     "off": 121894,
     "old": "724c",
     "new": "725b"
    },
    {
     "off": 121906,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 124122,
     "old": "202f0020226a0068",
     "new": "4eb94303322a4e71"
    },
    {
     "off": 126758,
     "old": "704c",
     "new": "705b"
    },
    {
     "off": 126766,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 140924,
     "old": "704c",
     "new": "705b"
    },
    {
     "off": 140932,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 141054,
     "old": "724c",
     "new": "725b"
    },
    {
     "off": 141062,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 170616,
     "old": "744c",
     "new": "745b"
    },
    {
     "off": 170632,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 170648,
     "old": "744c",
     "new": "745b"
    },
    {
     "off": 176176,
     "old": "724c",
     "new": "725b"
    },
    {
     "off": 176184,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 289116,
     "old": "724c",
     "new": "725b"
    },
    {
     "off": 289124,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 318272,
     "old": "704c222f0004",
     "new": "4ef943033028"
    },
    {
     "off": 318300,
     "old": "7206202f0004",
     "new": "4ef94303312a"
    },
    {
     "off": 318326,
     "old": "7205202f0004",
     "new": "4ef94303315c"
    },
    {
     "off": 318370,
     "old": "704c222f0004",
     "new": "4ef94303303e"
    },
    {
     "off": 319262,
     "old": "704b",
     "new": "705a"
    },
    {
     "off": 319278,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 319418,
     "old": "704c",
     "new": "705b"
    },
    {
     "off": 368312,
     "old": "487800c0",
     "new": "48780120"
    },
    {
     "off": 368318,
     "old": "40a79418",
     "new": "43035800"
    },
    {
     "off": 368350,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 368418,
     "old": "40a79418",
     "new": "43035800"
    },
    {
     "off": 368448,
     "old": "7005b085643e",
     "new": "4ef94303329e"
    },
    {
     "off": 368488,
     "old": "704c",
     "new": "705b"
    },
    {
     "off": 368528,
     "old": "40a79418",
     "new": "43035800"
    },
    {
     "off": 368554,
     "old": "40a7ada4",
     "new": "43035a00"
    },
    {
     "off": 368872,
     "old": "724c",
     "new": "725b"
    },
    {
     "off": 368884,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 368906,
     "old": "724c202f0004",
     "new": "4ef943033240"
    },
    {
     "off": 368918,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 368940,
     "old": "724c",
     "new": "725b"
    },
    {
     "off": 368952,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 368982,
     "old": "724c",
     "new": "725b"
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
     "new": "725a"
    },
    {
     "off": 369050,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 369100,
     "old": "724c",
     "new": "725b"
    },
    {
     "off": 369112,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 369150,
     "old": "724c",
     "new": "725b"
    },
    {
     "off": 369162,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 369192,
     "old": "724c",
     "new": "725b"
    },
    {
     "off": 369204,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 369244,
     "old": "704c",
     "new": "705b"
    },
    {
     "off": 369274,
     "old": "4010dce8",
     "new": "43034008"
    },
    {
     "off": 369318,
     "old": "7205",
     "new": "7208"
    },
    {
     "off": 369338,
     "old": "40a79418",
     "new": "43035800"
    },
    {
     "off": 369392,
     "old": "40a79418",
     "new": "43035800"
    },
    {
     "off": 369514,
     "old": "724b",
     "new": "725a"
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
     "new": "725a"
    },
    {
     "off": 369596,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 369616,
     "old": "724c",
     "new": "725b"
    },
    {
     "off": 369628,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 369656,
     "old": "724c",
     "new": "725b"
    },
    {
     "off": 369668,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 369690,
     "old": "724c",
     "new": "725b"
    },
    {
     "off": 369702,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 369724,
     "old": "724c",
     "new": "725b"
    },
    {
     "off": 369736,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 369758,
     "old": "724c",
     "new": "725b"
    },
    {
     "off": 369770,
     "old": "4010dce0",
     "new": "43034000"
    },
    {
     "off": 369904,
     "old": "7405b4816532",
     "new": "4ef943033070"
    },
    {
     "off": 369938,
     "old": "40a7ada4",
     "new": "43035a00"
    },
    {
     "off": 664032,
     "old": "7005",
     "new": "7008"
    },
    {
     "off": 664084,
     "old": "401177e4",
     "new": "43033800"
    },
    {
     "off": 664120,
     "old": "eb8c48780001",
     "new": "4ef9430330ae"
    },
    {
     "off": 664226,
     "old": "7850",
     "new": "7842"
    },
    {
     "off": 664296,
     "old": "7006",
     "new": "7009"
    },
    {
     "off": 670886,
     "old": "7005",
     "new": "7001"
    },
    {
     "off": 674244,
     "old": "700541e8000a",
     "new": "4ef943033102"
    },
    {
     "off": 674736,
     "old": "7005",
     "new": "7001"
    },
    {
     "off": 686444,
     "old": "40118628",
     "new": "43033824"
    },
    {
     "off": 686522,
     "old": "7205",
     "new": "7208"
    },
    {
     "off": 686532,
     "old": "40118640",
     "new": "43033890"
    },
    {
     "off": 686580,
     "old": "7005",
     "new": "7008"
    },
    {
     "off": 686614,
     "old": "40118610",
     "new": "43033848"
    },
    {
     "off": 724230,
     "old": "4016cae8",
     "new": "40154ae4"
    },
    {
     "off": 1492712,
     "old": "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
     "new": "41f9401aa14043f943000000203c0000e00022d8538066fa4feffff048d700f04ef9400004ba0000"
    }
   ],
   "append": {
    "at": "0x401aa140",
    "dest": "0x43000000",
    "size": 229376,
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
       "0x40008e0c"
      ]
     },
     {
      "dest": "0x430068c8",
      "syntakt": [
       "0x4000e488",
       "0x40010490"
      ]
     },
     {
      "dest": "0x430088d0",
      "syntakt": [
       "0x40014980",
       "0x40016b90"
      ]
     },
     {
      "dest": "0x4300aae0",
      "syntakt": [
       "0x40028438",
       "0x4003be38"
      ]
     },
     {
      "dest": "0x43036000",
      "syntakt": [
       "0x4003be38",
       "0x4003de38"
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
      "hex": "4fefffe048d77c0c247cbdcf77d82a6f002cd5cd220a263c0000031c4c431001242f0024286f00302f6f0028001c41f943032004203c534456312441b0ad002c660871b01800b480671a76011182a80041f94303200a223c534456312b41002c1183a8004ab94303200066564aad0038670001362c7c43020000267c43028a604eb9430000002d4b056c2f0e4eb94300199c47eb0030588f4dee0708b7fc43028be066dc323c0101203c01010101760123c04303200a23c34303200033c14303200e223c00000708200a4c0108002640d7fc43020000276d00340034222d003827410038276d003c003c4bf94303200a1035a8004a81670000aa4a00671c2f0b76014eb94300199c420027430038274200042682588f1b80a800220aed8942432441d5fc4303201015420022356c00140024356c00160026356c00180028356c001a002a356c001c002c356c001e002e302c0020354000307140356c0024003235430034274003ec2f0b4eb94300001a2f4a00302f4b002c716c002241f9430312dc22702ce80680ffffc000e7884cef7c0c0004d0af00202f4000284fef00244ed14a006700ff744cd77c0c4fef00204e752f0a2f02206f00104ab943032000661420080680000000804298b08866fa241f245f4e75202f0014243c0000031c0680bdcf77d84c42000043f94303200a4a31080066cc43f94303200473b10800b2af000c66bc243c000007084c0208002440d5fc430200002f0a2f0841f9430312d020701ce84e90256a00340038508f609e2f2f000c2f2f000c2f2f000c487800064eb9430310004fef00104e752f2f00082f2f0008487800064eb9430311b24fef000c4e752f2f000c2f2f000c2f2f000c487800074eb9430310004fef00104e752f2f00082f2f0008487800074eb9430311b24fef000c4e752f2f000c2f2f000c2f2f000c487800084eb9430310004fef00104e752f2f00082f2f0008487800084eb9430311b24fef000c4e75000043005f36430064444300681443005b304300603c430065a4"
     },
     {
      "dest": "0x43033000",
      "hex": "724cb081650000200c800000005b650470004e75724c90817205b0816504908160f67233d0814e75202f00046100ffd272644c010800068040a717544e75202f00046100ffbc72644c010800068040a71768487940a715002f2f000c2f004eb9400ddf604fef000c203c40a715004e757405b481650c7408b480650c4ef94005a8fa4ef94005a9284ef94005a91c7206b081660470014e757207b081660470034e757208b081660470044e754e7520036100ffdc2800e588eb8c988048780001487800174878002045f940071da4227940fe32ccd3c42f092f024e924fef00304878000148780022d8b940fe384c487800602f042f024e924fef00144ef9400a268041e8000a2f082f2e001020026a0270007205b2806c0c6100ff747205b2806c0270054ef9400a4dde202f00047207b0816700006a7208b0816700006e7209b081670000727206b280640270ff724c4c010800068040a715404e75202f00047206b081670000387207b0816700003c7208b081670000407205b280651041f9401091b4713008007206b280640270ff724c4c010800068040a715404e7541f943035c0070196000001a41f943035c60701e6000000e41f943035cc07023600000024a28004c6600005e2f022f0a24482400487940a715d82f0a4eb9400f8f02508f487940a715dc486a00044eb9400f8f02508f41f940a715e043ea000872102f0120187233b0816d087237b2806d02d08222c053976aea588f70011540004c204a245f241f20084e75202f0024226a00687206b0816d0643f94303386c4e75202f00040c800000004c650c0c800000004f620470064e750c8000000051650c0c8000000054620470074e750c8000000056650c0c8000000059620470084e750c800000005b650270002200e789ed88908141f943034000203008004e757006b0856500004a0c820000004c650e0c820000004f62067a066000002e0c8200000051650e0c820000005462067a07600000180c8200000056650e0c820000005962067a08600000024ef94005a3844ef94005a346"
     },
     {
      "dest": "0x43033800",
      "hex": "401300d8401300dd401300e3401300e940129960401300ee4303389c430338a2430338a8400aa08c400ab3b0400aa49c400aa998400aa7b8400aae8843031232430312664303129a400aa3c4400ab6e8400aa712400aacc2400aa930400ab24c4303124e43031282430312b60000000100000002000000030000000400000005000000060000000700000008000000090001020304050607080000005344567467004350567467005359546f7900496e6861726d00494e484d004672657120436f6d706c65780046434d500050697463682053776565700053574550004d6f6420456e76656c6f7065004d454e5600426f6479204368617200424f44590042616c616e63650042414c0053706163696e67204372756e6368005350435200426f647920456e76656c6f70650042454e5600466f726d00464f524d00496d7061637400494d50004272696768740042524947005061727469616c204465636179005041525400"
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
      "hex": "000000060000000b0000000000007f0000000000000000000010ffffffffffff000000000000060000000028430338ae4012996f430338b5000000060000000c0000000000007f0000006e00000000000011ffffffffffff000000000000060000000032430338ba4012996f430338c7000000060000000d0000000000007f0000004a00000000000012ffffffffffff00000000000006000000003c430338cc4012996f430338d8000000060000000e0000000000007f0000005000000000000013ffffffffffff000000000000060000000046430338dd4012996f430338ea00000007000000120000000000007f0000002100000000000050ffff0000009a00000000000006000000001e401298784012988240129886000000060000000b0000000000007f0000001800000000000010ffffffffffff000000000000060000000028430338ef4012996f430338f9000000060000000c0000000000007f0000001900000000000011ffffffffffff000000000000060000000032430338fe4012996f43033906000000060000000d0000000000007f0000002e00000000000012ffffffffffff00000000000006000000003c4303390a4012996f43033919000000060000000e0000000000007f0000002500000000000013ffffffffffff0000000000000600000000464303391e4012996f4303392c00000007000000120000000000007f0000002000000000000050ffff0000009a00000000000006000000001e401298784012988240129886000000060000000b0000000000007f0000001800000000000010ffffffffffff000000000000060000000028430339314012996f43033936000000060000000c0000000000007f0000003c00000000000011ffffffffffff0000000000000600000000324303393b4012996f43033942000000060000000d0000000000007f0000006e00000000000012ffffffffffff00000000000006000000003c430339464012996f4303394d000000060000000e0000000000007f0000004000000000000013ffffffffffff000000000000060000000046430339524012996f4303396000000007000000120000000000007f0000003c00000000000050ffff0000009a00000000000006000000001e401298784012988240129886"
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
      "43008acc"
     ],
     [
      "0x43001d82",
      "40014980",
      "430088d0"
     ],
     [
      "0x43002e04",
      "40014b80",
      "43008ad0"
     ],
     [
      "0x43002e22",
      "40015b80",
      "43009ad0"
     ],
     [
      "0x43002e3a",
      "80004a50",
      "43024a50"
     ],
     [
      "0x43002e66",
      "4000f48c",
      "430078cc"
     ],
     [
      "0x43002e9c",
      "4000e488",
      "430068c8"
     ],
     [
      "0x43002eda",
      "4000f48c",
      "430078cc"
     ],
     [
      "0x43002f2c",
      "4000e488",
      "430068c8"
     ],
     [
      "0x43002f3a",
      "4000e488",
      "430068c8"
     ],
     [
      "0x43002f4a",
      "80004a50",
      "43024a50"
     ],
     [
      "0x43002fb2",
      "80004a50",
      "43024a50"
     ],
     [
      "0x43002fc2",
      "80004a70",
      "43024a70"
     ],
     [
      "0x43003000",
      "80004a70",
      "43024a70"
     ],
     [
      "0x43003006",
      "80004af0",
      "43024af0"
     ],
     [
      "0x43003014",
      "80004a50",
      "43024a50"
     ],
     [
      "0x4300301e",
      "80004a54",
      "43024a54"
     ],
     [
      "0x43003028",
      "80004a58",
      "43024a58"
     ],
     [
      "0x43003032",
      "80004a5c",
      "43024a5c"
     ],
     [
      "0x4300303c",
      "80004a60",
      "43024a60"
     ],
     [
      "0x4300304c",
      "80004a64",
      "43024a64"
     ],
     [
      "0x4300307c",
      "80004af0",
      "43024af0"
     ],
     [
      "0x4300309a",
      "80004a68",
      "43024a68"
     ],
     [
      "0x430030a0",
      "80004a6c",
      "43024a6c"
     ],
     [
      "0x4300330a",
      "8000a07c",
      "4302a07c"
     ],
     [
      "0x43005b42",
      "40004dc6",
      "43002882"
     ],
     [
      "0x43005b4e",
      "40039238",
      "4301b8e0"
     ],
     [
      "0x43005b7c",
      "40039838",
      "4301bee0"
     ],
     [
      "0x43005b8e",
      "40039638",
      "4301bce0"
     ],
     [
      "0x43005ba0",
      "40039438",
      "4301bae0"
     ],
     [
      "0x43005bb6",
      "40039038",
      "4301b6e0"
     ],
     [
      "0x43005bce",
      "40038e38",
      "4301b4e0"
     ],
     [
      "0x43005be6",
      "40038c38",
      "4301b2e0"
     ],
     [
      "0x43005c12",
      "4003a038",
      "4301c6e0"
     ],
     [
      "0x43005c1c",
      "40039e38",
      "4301c4e0"
     ],
     [
      "0x43005c3a",
      "40039c38",
      "4301c2e0"
     ],
     [
      "0x43005c76",
      "40028438",
      "4300aae0"
     ],
     [
      "0x43005c92",
      "40038a38",
      "4301b0e0"
     ],
     [
      "0x43005cae",
      "40038838",
      "4301aee0"
     ],
     [
      "0x43005dea",
      "800097c8",
      "430297c8"
     ],
     [
      "0x43005dfe",
      "40038638",
      "4301ace0"
     ],
     [
      "0x43005e06",
      "800097c8",
      "430297c8"
     ],
     [
      "0x43005e28",
      "40038438",
      "4301aae0"
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
      "4301c0e0"
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
      "0x4300605a",
      "80004b70",
      "43024b70"
     ],
     [
      "0x43006060",
      "80009580",
      "43029580"
     ],
     [
      "0x43006090",
      "40004dc6",
      "43002882"
     ],
     [
      "0x4300609c",
      "4003b238",
      "4301d8e0"
     ],
     [
      "0x430060ba",
      "4003b638",
      "4301dce0"
     ],
     [
      "0x430060cc",
      "4003b438",
      "4301dae0"
     ],
     [
      "0x430060e8",
      "4003a838",
      "4301cee0"
     ],
     [
      "0x4300613a",
      "400052f8",
      "43002db4"
     ],
     [
      "0x4300614e",
      "4003bc38",
      "4301e2e0"
     ],
     [
      "0x430061d8",
      "4003b038",
      "4301d6e0"
     ],
     [
      "0x430061ea",
      "4003ae38",
      "4301d4e0"
     ],
     [
      "0x4300631c",
      "4003ac38",
      "4301d2e0"
     ],
     [
      "0x43006332",
      "4003ba38",
      "4301e0e0"
     ],
     [
      "0x43006344",
      "4003aa38",
      "4301d0e0"
     ],
     [
      "0x43006366",
      "4003b838",
      "4301dee0"
     ],
     [
      "0x430063a4",
      "4003a438",
      "4301cae0"
     ],
     [
      "0x430063c2",
      "4003a238",
      "4301c8e0"
     ],
     [
      "0x430063d6",
      "4003a638",
      "4301cce0"
     ],
     [
      "0x43006434",
      "40002596",
      "43000052"
     ],
     [
      "0x43006452",
      "40005728",
      "430031e4"
     ],
     [
      "0x43006460",
      "40004e6c",
      "43002928"
     ],
     [
      "0x4300647e",
      "40003c0e",
      "430016ca"
     ],
     [
      "0x43006488",
      "400058e8",
      "430033a4"
     ],
     [
      "0x43006494",
      "40003958",
      "43001414"
     ],
     [
      "0x4300649e",
      "4000290e",
      "430003ca"
     ],
     [
      "0x430064aa",
      "400044e2",
      "43001f9e"
     ],
     [
      "0x430064b8",
      "800096a4",
      "430296a4"
     ],
     [
      "0x430064be",
      "40003eb4",
      "43001970"
     ],
     [
      "0x430064cc",
      "800096a4",
      "430296a4"
     ],
     [
      "0x430064de",
      "800096a4",
      "430296a4"
     ],
     [
      "0x430064f0",
      "80008c60",
      "43028c60"
     ],
     [
      "0x43006510",
      "800096a4",
      "430296a4"
     ],
     [
      "0x43006516",
      "400049f4",
      "430024b0"
     ],
     [
      "0x4300652c",
      "400054e6",
      "43002fa2"
     ],
     [
      "0x43006538",
      "40004f74",
      "43002a30"
     ],
     [
      "0x43006544",
      "4000569a",
      "43003156"
     ],
     [
      "0x4300657c",
      "80008c60",
      "43028c60"
     ],
     [
      "0x43006590",
      "400047ea",
      "430022a6"
     ],
     [
      "0x430065c2",
      "4003dc38",
      "43037e00"
     ],
     [
      "0x430065c8",
      "40004dc6",
      "43002882"
     ],
     [
      "0x430065e6",
      "4003c838",
      "43036a00"
     ],
     [
      "0x430065f8",
      "4003c638",
      "43036800"
     ],
     [
      "0x4300660a",
      "4003c438",
      "43036600"
     ],
     [
      "0x4300661c",
      "4003c238",
      "43036400"
     ],
     [
      "0x43006626",
      "800098ec",
      "430298ec"
     ],
     [
      "0x4300663a",
      "4003d038",
      "43037200"
     ],
     [
      "0x43006658",
      "4003d238",
      "43037400"
     ],
     [
      "0x43006674",
      "4003c038",
      "43036200"
     ],
     [
      "0x4300667c",
      "80004b70",
      "43024b70"
     ],
     [
      "0x430066b6",
      "4003ce38",
      "43037000"
     ],
     [
      "0x430066cc",
      "4003cc38",
      "43036e00"
     ],
     [
      "0x430066de",
      "4003ca38",
      "43036c00"
     ],
     [
      "0x430067b2",
      "4003da38",
      "43037c00"
     ],
     [
      "0x430067c4",
      "4003d838",
      "43037a00"
     ],
     [
      "0x430067d6",
      "4003d638",
      "43037800"
     ],
     [
      "0x430067e8",
      "4003d438",
      "43037600"
     ],
     [
      "0x43006804",
      "40002596",
      "43000052"
     ],
     [
      "0x4300682c",
      "40003c0e",
      "430016ca"
     ],
     [
      "0x43006838",
      "400035de",
      "4300109a"
     ],
     [
      "0x43006842",
      "4000290e",
      "430003ca"
     ],
     [
      "0x4300686e",
      "80008c60",
      "43028c60"
     ],
     [
      "0x43006878",
      "80009580",
      "43029580"
     ],
     [
      "0x43006882",
      "800096a4",
      "430296a4"
     ],
     [
      "0x4300688c",
      "800097c8",
      "430297c8"
     ],
     [
      "0x43006896",
      "40004cd6",
      "43002792"
     ],
     [
      "0x4300689e",
      "40003d42",
      "430017fe"
     ],
     [
      "0x430068ac",
      "400045a0",
      "4300205c"
     ],
     [
      "0x430068b6",
      "400047ea",
      "430022a6"
     ],
     [
      "0x43034904",
      "00000500",
      "00000800"
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
   "id": "syntakt",
   "label": "Vrais moteurs du Syntakt",
   "desc": "Les moteurs du Syntakt, extraits de TON fichier Syntakt_OS1.41.syx (a deposer a l'etape 2), en machines supplementaires apres les 6 d'origine : coche ceux que tu veux. Identiques au Syntakt en emulation.",
   "status": "tested",
   "credit": null,
   "engines": [
    {
     "code": "sd",
     "name": "SDVtg",
     "label": "SD VINTAGE"
    },
    {
     "code": "cp",
     "name": "CPVtg",
     "label": "CP VINTAGE"
    },
    {
     "code": "toy",
     "name": "SYToy",
     "label": "SY TOY"
    }
   ],
   "combos": [
    {
     "id": "sdvintage-7th",
     "engines": [
      "sd"
     ],
     "tested": true,
     "label": "SDVtg"
    },
    {
     "id": "syntakt-cp",
     "engines": [
      "cp"
     ],
     "tested": false,
     "label": "CPVtg"
    },
    {
     "id": "syntakt-toy",
     "engines": [
      "toy"
     ],
     "tested": false,
     "label": "SYToy"
    },
    {
     "id": "syntakt-vintage",
     "engines": [
      "sd",
      "cp"
     ],
     "tested": true,
     "label": "SDVtg, CPVtg"
    },
    {
     "id": "syntakt-sd-toy",
     "engines": [
      "sd",
      "toy"
     ],
     "tested": false,
     "label": "SDVtg, SYToy"
    },
    {
     "id": "syntakt-cp-toy",
     "engines": [
      "cp",
      "toy"
     ],
     "tested": false,
     "label": "CPVtg, SYToy"
    },
    {
     "id": "syntakt-sd-cp-toy",
     "engines": [
      "sd",
      "cp",
      "toy"
     ],
     "tested": false,
     "label": "SDVtg, CPVtg, SYToy"
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
