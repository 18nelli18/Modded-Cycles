# 185 — Marge LEGACY et ACID

Demande AveyCole25/10/2026 :152 reste a112–114P avec LEGACY a la place deMACRO ; «acid could use some help too maybe», puis demander des gains plus grands apres cette passe. Generateur --engine-headroom, dx7_assets.py/fundamentals_assets.py ; preuves test_legacy_exact153.py/test_acid_exact153.py/test_arithmetic153.py/test_engine_mix153.py. Adresses : VA OS1.13.

## Reponse courte

[FAIT en emulation]153 sur152, sans147/149 : LEGACY economise encore7.812% instructions dans70cas, ACID5.433% dans8bancs sixpistes. Aucun sample ni octet d'etat DSP change. Gains mixtes plus petits, voir JSON/log, plus gros bloc encore identique. Aucun gain CPU physique153 revendique. Banque151 confirmee par l'utilisateur et conservee.

## 1. LEGACY

Masques des carriers tires des32algorithmes MSFA (bitOUT_BUS_ADD), locaux a chaque appel, au lieu des appels repetes isCarrier dans note_on/active/block. Aucun nouveau champ DxTrack. Amod initial : coefficient au plus255 fois ld au plus2^24 tient dans32bits sans signe. Produits Q24 suivants remplaces par EMAC exact : a<<2, b<<4, mac.l<<, movclr ; a borne par17*2^24, b par2^24, ne sature pas. Le wrapper152 preserve MACSR/48bits physiques. LFOgetdelay : carry32bits equivalent a l'addition64bits, y compris overflow sans publication de delaystate. Port/core/enveloppes/pitch/LFO compiles-O3/-funroll-loops uniquement153, memes sources/precision/parametres. Les trois noyaux152 restent binaires exacts.

## 2. ACID

-O3/-funroll-loops/-fwrapv uniquementacid.c. Parametres acid_block restreints aux zones disjointes etat/entrees/sortie garanties par le contrat render ; permet de conserver les invariants du bloc sans relectures inutiles. Aucune reduction de poles, precision, polyBLEP, drive ou interpolation. Seule fusion : deux produits IDENTIQUES qmac2(a,b,a,b) de sortie vers un mac.l<<. Pour p=a*b : floor(2*floor(p/2^23)/256)=floor(p/2^30), memes resultats signes et saturation. Les paires de produits distincts des filtres sont conservees. Etats et controles exacts.

## 3. Correction du banc EMAC

Le decodeur historique ne couvrait pas toutes les nouvelles copies ACID/HALL. fixtures installe maintenant les octets finaux fundamentaux/PUNCH/LEGACY/HALL hors des plages historiques. EMAC.install idempotent : un deuxieme decodage ne doit pas installer deux callbacks pour le meme opcode. Les chiffres mixtes precedents (note184) n'etaient donc pas une preuve complete d'arithmetique ACID/HALL correcte ;153 les remplace avec cette couverture. Les preuves directes des operateurs LEGACY avaient deja leur propre installation explicite. Pas de changement du firmware par ce correctif d'emulateur.

## 4. Validation et disposition

1024cas bornes/aleatoires Q24 compares au produit entier exact ;1025cas produits ACID repetes signes/satures compares a qmac2 natif et aux entiers exacts. LEGACY :70cas/32algorithmes, tous octets des sixDxTrack et PCM exacts, modulation/pitch/velocite/relache. ACID :8cas sixpistes, notes0..127, scie/carre, cutoff/res/env/drive/decay extremes, velocite, editslive/retrigger/release ; PCM et tout BSS fondamental exacts. Mix SPEAK, LEGACY0/15/31 ouMACRO, deuxPUNCH,KICK,ACID, HALL/PingPong/Sidechain exact. Banqueburst/overflow/retry/DIN+USB/WAVE, popup/QntM/MIDI24machines passes.

Seuls objets LEGACY port/core/env/pitch/LFO etacid.c changent. TrampolineUI et modules FX/SPEAK/projet ne changent que les adresses de relais deplacees, normalisees dans l'audit. PUNCH/HALL/Sidechain/gouverneur et noyaux152 exacts. Fin codeDX7 0x4685e3d4 avant WAVE0x46860000 ; fin codeACID0x46842204 avant BSS0x46848000. Queue151 inchangee0x468a8000..0x468acd74. Standard/adulte reproductibles,152 --check exact, sections bootloader/updater et autres horsMAIN exactes. [A FAIRE appareil] comparer152/153 meme pattern/patchs et memes FX, verifier A/P/O/N et ecoute. Aucun principal/guide public change ; poursuivre ensuite une recherche separee de gains plus grands dans les chemins communs.
