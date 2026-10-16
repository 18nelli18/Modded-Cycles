#!/usr/bin/env python3
"""Page MPI1 separee du principal ; copie les sources main, sans firmware."""
import argparse,pathlib,re
ROOT=pathlib.Path(__file__).resolve().parents[1]
STAMP='2026-10-16-midi-saving-test-1'
def files():
    for src in sorted((ROOT/'docs/flasher').iterdir()):
        if not src.is_file() or src.suffix=='.wav' or src.name=='ABOUT.md':continue
        raw=src.read_bytes()
        if src.name=='TEST-NOTES.md':
            raw=b'''# MIDI persistence hardware trial / Essai materiel de persistance MIDI

EN: Use a test project. Stop playback, edit B notes, CC locks and MIDI LFOs, then Save Project. Wait for MIDI SAVED. Restart, load the same saved project and open B. Check a second pattern and a different project. Report the exact MIDI SAVE E## or MIDI LOAD E## popup on failure. Keep normal backups: MIDI sidecars are outside Elektron backups. This candidate is experimental; main remains RAM-only.

FR : Utilisez un projet de test. Arretez, editez notes B, locks CC et LFO MIDI puis Save Project. Attendez MIDI SAVED. Redemarrez, chargez le meme projet et ouvrez B. Verifiez un autre pattern et un autre projet. Rapportez le popup MIDI SAVE E## ou MIDI LOAD E## exact en cas d'echec. Conservez les backups normaux : sidecars MIDI hors backups Elektron. Candidat experimental, principal RAM conserve.
'''
        if src.name=='index.html':
            s=raw.decode('utf-8');s=re.sub(r'(?<=\?v=)[\w.-]+',STAMP,s)
            s=re.sub(r"window.MC_BUILD='[^']+'",f"window.MC_BUILD='{STAMP}'",s)
            s=s.replace("<title>A.V.'s Supermodel Edition.</title>",'<title>MIDI saving — experimental test</title>')
            s=re.sub(r'<p class="alert"><span data-l="en"><strong>MIDI OUT Bank is hardware tested by AveyCole.*?</p>','',s,flags=re.S)
            banner='<p class="alert"><span data-l="en"><strong>Experimental MIDI saving test — hardware persistence unverified.</strong> Stop playback, choose Save Project, and check for MIDI SAVED. Open B after loading a project to restore MIDI. MIDI sidecars are outside Elektron backups. <a href="../flasher/">Hardware-tested RAM-only main flasher</a>.</span><span data-l="fr"><strong>Test de sauvegarde MIDI — persistance materielle non verifiee.</strong> Arretez, faites Save Project et verifiez MIDI SAVED. Ouvrez B apres chargement pour restaurer. Fichiers MIDI hors backups Elektron. <a href="../flasher/">Principal RAM teste sur machine</a>.</span></p>'
            s=s.replace('<main class="wrap fl">','<main class="wrap fl">'+banner)
            s=s.replace('href="convert.html"','href="../flasher/convert.html"')
            s=s.replace('</body>',f'<script src="midi-persistence-data.js?v={STAMP}"></script><script src="midi-persistence.js?v={STAMP}"></script></body>')
            s=s.replace('../assets/release.js?','release.js?');raw=s.encode()
        if src.name=='quick-reference.md':
            s=raw.decode('utf-8').replace('Independent RAM-only MIDI Bank is hardware tested by AveyCole and available alone or alongside your selected machines.','This MIDI saving candidate is experimental; hardware persistence is unverified.')
            s=s.replace('B-side sequences, MIDI LFOs and CCs are RAM-only: **lost on power-off**. Save Project saves A-side only.','In this experimental test, stop playback and use Save Project. Wait for MIDI SAVED. Restart, load the same saved project and open B to test recovery. MIDI files are outside standard Elektron backups. Unsaved edits are lost on power-off.')
            raw=s.encode()
        if src.name=='quick-reference-fr.md':
            s=raw.decode('utf-8').replace('Toutes les données de la banque MIDI restent en RAM et sont perdues à extinction. Save Project sauvegarde uniquement A.','Dans cet essai expérimental, arrêtez la lecture et faites Save Project ; attendez MIDI SAVED. Redémarrez, chargez le même projet et ouvrez B pour tester la reprise. Fichiers MIDI hors backups Elektron. Éditions non sauvegardées perdues à extinction ; persistance matérielle non vérifiée.')
            raw=s.encode()
        if src.suffix in ('.js','.html','.css','.md','.txt'):raw=('\n'.join(line.rstrip() for line in raw.decode('utf-8').splitlines()).rstrip()+'\n').encode()
        yield src.name,raw
    yield 'release.js',b'''window.MC_RELEASES=[{version:"1.72-saving-preview.1",date:"2026-10-16",changes:[{en:"Experimental MIDI persistence for the independent bank. Stop before Save Project. Two checked recovery copies include notes, retrigger/chance, CC locks and MIDI LFO settings. Hardware persistence unverified; main remains RAM-only.",fr:"Persistance MIDI experimentale pour la Banque autonome. Arreter avant Save Project. Deux copies verifiees : notes, retrigger/chance, locks CC et LFO MIDI. Persistance materielle non verifiee ; principal RAM conserve."}]}];\n'''
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');a=p.parse_args();out=ROOT/'docs/flasher-midi-save-current-test';out.mkdir(exist_ok=True)
    for name,raw in files():
        target=out/name
        if a.check:assert target.read_bytes()==raw,name
        else:target.write_bytes(raw)
    print('ok page sauvegarde MIDI separee ; main RAM intact')
if __name__=='__main__':main()
