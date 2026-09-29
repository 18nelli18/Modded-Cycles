#!/usr/bin/env python3
"""Cross-flash : l'OS d'un Model dans le conteneur de l'autre (notes/15 §3).

Le Model:Cycles et le Model:Samples OS 1.13 partagent le meme bootstrap (section 2, meme code a
l'identifiant produit pres, meme initialisation de la RAM DDR), le meme updater (section 4, octet pour
octet) et les memes adresses de chargement. Seul le MAIN OS (section 3) fait la difference.

Ce script prend TES deux fichiers officiels (aucune image n'est fournie) et produit :

    --to cycles   l'OS Model:Samples dans un conteneur Model:Cycles : a flasher sur un Model:Cycles.
                  Bootstrap, updater et cle de signature restent ceux du Cycles : le menu de demarrage
                  du Cycles (FUNC + allumage, TRIG 4, par le MIDI IN) reste la voie de retour.
                  Teste avec succes sur un vrai Model:Cycles le 29/09/2026 (notes/15 §3).
    --to samples  l'inverse (OS Cycles pour un Model:Samples).
    --back        Emballe l'OS Cycles officiel pour qu'il passe la 1re verification de l'OS Samples
                  (produit 0x0F, marqueur 0x0A, HMAC clef Samples). /!\\ NE SUFFIT PAS au retour :
                  une MAJ USB est verifiee DEUX fois, avec deux clefs. Depuis l'OS Samples installe sur
                  un Cycles, le bootstrap present est celui du Cycles (clef "REVERB SEND") et re-verifie
                  a l'installation au redemarrage ; ce fichier, signe clef Samples, est alors rejete et
                  l'ancien OS revient. Il n'y a PAS de retour par USB dans cet etat : il faut une
                  interface MIDI (menu de demarrage). Conserve pour la 1re porte et la doc (notes/15 §3.4bis).

Technique : garder le conteneur de la machine hote et ne remplacer que la section 3. Elle a ete trouvee par un
utilisateur de r/Elektron et verifiee sur un Model:Samples par scottmetoyer/ms-multi-output (cible
cycles-crossflash, vendor/ms-multi-output/README.md). Le bootloader ignore en silence un conteneur d'un autre
produit, et comme le bootstrap de l'hote n'est pas touche, le .syx officiel de l'hote reste l'image de secours.

    python3 tools/crossflash.py --cycles model-cycles_OS1.13.syx --samples model-samples_OS1.13.syx --to cycles

Controles : les deux .syx et leurs MAIN OS doivent etre les officiels 1.13 (SHA-256) ; la section 3 est
reprise telle quelle (flux aPLib d'origine, rien n'est recompresse) ; apres construction, le fichier est
relu : checksums de chaque paquet, HMAC-SHA256 avec la cle du conteneur hote, sections 2/4/5 identiques a
l'hote, section 3 identique a l'OS invite une fois decompressee.
"""
import argparse
import hashlib
import hmac
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from mtlib import aplib, container            # noqa: E402
from mtlib.syx import unwrap, wrap, BYTES_PER_MSG  # noqa: E402

# Fichiers officiels OS 1.13 (elektron.se) : SHA-256 du .syx et du MAIN OS decompresse (notes/09, notes/15)
OFFICIAL = {
    "cycles": {"product": 0x11, "name": "Model:Cycles",
               "syx": "44fe586269631a0ca7da25a3383fc6733c314809505fc3cc52f1e0ed9800640c",
               "main": "cc99d4f0175d34d1e91d046e6ec85a5e8ab58ab9edbb3c24406acd48cb99ee98"},
    "samples": {"product": 0x0F, "name": "Model:Samples",
                "syx": "e11859b68deb7e5e3fe86ab32581212093849c4be5d3950add011eac398a2ce8",
                "main": "a351392c62ec1c6c3324a807baf46934690d54edfc76029a4b4882541cad1ab2"},
}


# MAIN OS Samples 1.13 : derivation de la cle HMAC qu'il verifie lui-meme (fonction 0x40051728, notes/15 §3.4)
SMP_KEY_STR_VA = 0x4012A35F      # "DELAY TIME\0"
SMP_KEY_CONST_VA = 0x4012A37E    # 32 octets
MAIN_BASE = 0x40000400


def sha(b):
    return hashlib.sha256(b).hexdigest()


def load(path, which):
    """.syx officiel -> (info, container, {id: octets stockes}, {id: octets decompresses})."""
    raw = pathlib.Path(path).read_bytes()
    ref = OFFICIAL[which]
    if sha(raw) != ref["syx"]:
        raise SystemExit(f"!! {path} n'est pas le .syx officiel {ref['name']} OS 1.13 (SHA-256 {sha(raw)[:16]}...)")
    stream, info = unwrap(raw)                  # verifie aussi le checksum de chaque paquet
    if info["product"] != ref["product"]:
        raise SystemExit(f"!! {path} : produit 0x{info['product']:02x}, attendu 0x{ref['product']:02x}")
    c = container.parse(stream)
    stored, plain = {}, {}
    for s in c["sections"]:
        stored[s["id"]] = c["blob"][s["off"]:s["off"] + s["size"]]
        try:
            plain[s["id"]] = aplib.depack(stored[s["id"]])[0]
        except Exception:
            plain[s["id"]] = stored[s["id"]]    # sections brutes (meta, updater)
    if sha(plain[3]) != ref["main"]:
        raise SystemExit(f"!! {path} : MAIN OS inattendu ({sha(plain[3])[:16]}...)")
    return info, c, stored, plain


def cross(host, guest):
    """Conteneur de l'hote, MAIN OS de l'invite. host/guest = resultats de load()."""
    h_info, h_c, h_stored, h_plain = host
    _, _, g_stored, g_plain = guest
    msg = h_c["blob"][:len(h_c["blob"]) - container.DIGEST_LEN]
    expect = h_c["blob"][len(h_c["blob"]) - container.DIGEST_LEN:]
    key = container.find_key(list(h_plain.values()), msg, expect)
    if not key:
        raise SystemExit("!! cle HMAC de l'hote introuvable")
    blob = container.rebuild(h_c, {3: g_stored[3]}, key)
    out = wrap(container.build_stream(blob, BYTES_PER_MSG), h_info["product"], h_info["start_seq"])

    # relecture complete du resultat
    stream, info = unwrap(out)
    c = container.parse(stream)
    if info["product"] != h_info["product"]:
        raise SystemExit("!! relecture : identifiant produit change")
    got = {s["id"]: c["blob"][s["off"]:s["off"] + s["size"]] for s in c["sections"]}
    for sid in h_stored:
        want = g_stored[3] if sid == 3 else h_stored[sid]
        if got.get(sid) != want:
            raise SystemExit(f"!! relecture : section {sid} differente de l'attendu")
    if sha(aplib.depack(got[3])[0]) != sha(g_plain[3]):
        raise SystemExit("!! relecture : le MAIN OS decompresse ne correspond pas")
    plain = [aplib.depack(got[s])[0] if s == 3 else h_plain[s] for s in got]
    m, e = c["blob"][:len(c["blob"]) - container.DIGEST_LEN], c["blob"][len(c["blob"]) - container.DIGEST_LEN:]
    if container.find_key(plain, m, e) != key:
        raise SystemExit("!! relecture : HMAC invalide")
    return out


def key_from_main_os(main3):
    """Cle HMAC derivee par le MAIN OS Samples lui-meme (et non par le bootstrap) : sha256(s) ^ sha256(s inverse) ^ C."""
    o = SMP_KEY_STR_VA - MAIN_BASE
    text = main3[o:main3.index(b"\0", o)]
    const = main3[SMP_KEY_CONST_VA - MAIN_BASE:SMP_KEY_CONST_VA - MAIN_BASE + 32]
    h, hr = hashlib.sha256(text).digest(), hashlib.sha256(text[::-1]).digest()
    return bytes(a ^ b ^ c for a, b, c in zip(h, hr, const))


def back_to_cycles(cyc, smp):
    """Contenu Cycles officiel (sections 2, 3, 4, 5 inchangees), cle HMAC Samples, transport Samples."""
    c_info, c_c, c_stored, c_plain = cyc
    s_info, s_c, s_stored, s_plain = smp
    msg = s_c["blob"][:len(s_c["blob"]) - container.DIGEST_LEN]
    expect = s_c["blob"][len(s_c["blob"]) - container.DIGEST_LEN:]
    key = container.find_key(list(s_plain.values()), msg, expect)
    if not key:
        raise SystemExit("!! cle HMAC Samples introuvable")
    if key != key_from_main_os(s_plain[3]):
        raise SystemExit("!! la cle du MAIN OS Samples differe de celle du bootstrap : abandon")
    blob = container.rebuild(c_c, {}, key)
    out = wrap(container.build_stream(blob, BYTES_PER_MSG), s_info["product"], s_info["start_seq"])
    check_back(out, cyc, smp, key)
    return out


def check_back(out, cyc, smp, key):
    """Rejoue, sur le fichier produit, ce que fait l'OS Samples a la reception (notes/15 §3.4) :
    routeur (produit), marqueur (octet appareil), checksum de chaque paquet, checksum de contenu, HMAC."""
    c_info, c_c, c_stored, c_plain = cyc
    head = out[:out.find(0xF7) + 1]                  # marqueur de debut
    if head[4] != 0x0F:
        raise SystemExit(f"!! produit 0x{head[4]:02x} : l'OS Samples ne route la mise a jour que pour 0x0F")
    if head[6:8] != b"\x7f\x01" or head[8] != 0x0A:
        raise SystemExit("!! marqueur de debut : l'OS Samples exige l'octet appareil 0x0A")
    stream, info = unwrap(out)                       # checksums de chaque paquet, base = octet appareil
    c = container.parse(stream)
    blob = c["blob"]
    if int.from_bytes(stream[4:8], "big") != container.content_checksum(blob):
        raise SystemExit("!! checksum de contenu invalide")
    body, dig = blob[:len(blob) - container.DIGEST_LEN], blob[len(blob) - container.DIGEST_LEN:]
    if hmac.new(key, body, hashlib.sha256).digest() != dig:
        raise SystemExit("!! HMAC invalide avec la cle Samples")
    if hmac.new(container.find_key(list(c_plain.values()), c_c["blob"][:len(c_c["blob"]) - container.DIGEST_LEN],
                                   c_c["blob"][len(c_c["blob"]) - container.DIGEST_LEN:]), body, hashlib.sha256).digest() == dig:
        raise SystemExit("!! signature aussi valide avec la cle Cycles : incoherent")
    got = {s["id"]: blob[s["off"]:s["off"] + s["size"]] for s in c["sections"]}
    if got != c_stored:
        raise SystemExit("!! les sections ne sont pas celles de l'OS Cycles officiel")
    if blob[:0x20] != c_c["blob"][:0x20]:
        raise SystemExit("!! en-tete du conteneur different de l'officiel Cycles")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cycles", required=True, help="model-cycles_OS1.13.syx officiel")
    ap.add_argument("--samples", required=True, help="model-samples_OS1.13.syx officiel")
    ap.add_argument("--to", choices=("cycles", "samples"), help="machine qui recevra le fichier")
    ap.add_argument("--back", action="store_true",
                    help="retour a l'OS Cycles depuis l'OS Samples, par USB (CONFIG > UPGRADE), sans interface MIDI")
    ap.add_argument("-o", "--output", help="fichier de sortie")
    args = ap.parse_args()
    if bool(args.to) == args.back:
        ap.error("choisis --to cycles|samples, ou --back")

    cyc, smp = load(args.cycles, "cycles"), load(args.samples, "samples")
    if args.back:
        out = back_to_cycles(cyc, smp)
        name = args.output or str(pathlib.Path(args.cycles).with_name("model-cycles_OS1.13_back-from-samples-os.syx"))
        pathlib.Path(name).write_bytes(out)
        print(f"ecrit : {name} ({len(out)} o, SHA-256 {sha(out)[:16]}...)")
        print("  OS Cycles officiel 1.13 (sections 2, 3, 4, 5 inchangees), signe avec la cle Samples.")
        print("  Passe la 1re verification de l'OS Samples (produit, marqueur, checksums, HMAC).")
        print("\n  /!\\ CE FICHIER NE SUFFIT PAS au retour a l'OS Cycles.")
        print("  Une MAJ USB est verifiee 2 fois : (1) l'OS Samples qui tourne, cle Samples ; puis")
        print("  (2) au redemarrage le bootstrap Cycles present sur la machine, cle Cycles. Un fichier")
        print("  ne porte qu'un HMAC : signe Samples il passe (1) et est rejete a (2). Teste par")
        print("  l'utilisateur le 29/09/2026 : la MAJ 'a semblé marcher' mais l'OS Samples est reste.")
        print("  => Retour uniquement par une interface MIDI (menu de demarrage). Voir notes/15 §3.4bis.")
        return
    host, guest = (cyc, smp) if args.to == "cycles" else (smp, cyc)
    out = cross(host, guest)
    # par defaut, a cote du fichier de l'OS invite (comme build.py ecrit a cote de son entree)
    guest_path = pathlib.Path(args.samples if args.to == "cycles" else args.cycles)
    name = args.output or str(guest_path.with_name("model-samples_OS1.13_for-model-cycles.syx" if args.to == "cycles"
                                                   else "model-cycles_OS1.13_for-model-samples.syx"))
    pathlib.Path(name).write_bytes(out)
    h, g = OFFICIAL[args.to], OFFICIAL["samples" if args.to == "cycles" else "cycles"]
    print(f"ecrit : {name} ({len(out)} o, SHA-256 {sha(out)[:16]}...)")
    print(f"  OS {g['name']} 1.13 dans un conteneur {h['name']} (produit 0x{h['product']:02x}) : "
          f"bootstrap, updater et cle de signature du {h['name']}")
    print("  relu et verifie : paquets, sections, MAIN OS, HMAC")
    if args.to == "cycles":
        print("\n  Teste sur un vrai Model:Cycles (29/09/2026). Avant de flasher, lis notes/15 §3 :")
        print("  sauvegarde tes projets (Transfer), garde ton interface MIDI branchee sur le MIDI IN,")
        print("  et n'utilise pas CONFIG > UPGRADE depuis l'OS Samples. Retour : menu de demarrage")
        print("  (FUNC + allumage, TRIG 4) et l'OS Cycles officiel par le MIDI IN (flash.sh / flash.bat).")


if __name__ == "__main__":
    main()
