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
  }
 ],
 "samples": {
  "syx_sha256": "e11859b68deb7e5e3fe86ab32581212093849c4be5d3950add011eac398a2ce8",
  "main_sha256": "a351392c62ec1c6c3324a807baf46934690d54edfc76029a4b4882541cad1ab2",
  "download": "https://www.elektron.se/support-downloads/modelsamples"
 }
};
