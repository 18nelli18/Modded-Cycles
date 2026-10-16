#!/usr/bin/env python3
"""Reproduire la page MIDI experimentale depuis le flasheur principal.

python3 tools/gen_midi_current_flasher.py [--check]
Les deux fichiers midi-bank*.js restent les sources specifiques du candidat.
"""
import argparse,pathlib,re
ROOT=pathlib.Path(__file__).resolve().parents[1]
STAMP='2026-10-16-midi-main-tested'
BANNER='''<p class="alert"><span data-l="en"><strong>Experimental MIDI OUT Bank test.</strong> Select MIDI OUT Bank alone, or add your machines and options, including RETROSYN, TINY and optional Sample Wizard. FUNC + SETTINGS + TRACK opens B. B-side data stays in RAM and is lost at power-off. Hardware validation is pending. <a href="../flasher/">Main flasher</a>.</span><span data-l="fr"><strong>Test experimental Banque MIDI OUT.</strong> Choisissez la Banque seule ou ajoutez vos machines et options, dont RETROSYN, TINY et Sample Wizard facultatif. FUNC + SETTINGS + TRACK ouvre B. Les donnees B restent en RAM et disparaissent a extinction. Validation materielle attendue. <a href="../flasher/">Flasheur principal</a>.</span></p>'''
def files():
    base=ROOT/'docs/flasher'
    for src in sorted(base.iterdir()):
        if not src.is_file() or src.suffix=='.wav' or src.name in ('ABOUT.md','TEST-NOTES.md'):continue
        raw=src.read_bytes()
        if src.name=='index.html':
            s=raw.decode('utf-8');s=re.sub(r'(?<=\?v=)[\w.-]+',STAMP,s)
            s=re.sub(r"window.MC_BUILD='[^']+'",f"window.MC_BUILD='{STAMP}'",s)
            s=s.replace('<title>A.V.\'s Supermodel Edition.</title>','<title>MIDI OUT Bank — hardware tested</title>')
            if 'midi-bank.js?' not in s:s=s.replace('<main class="wrap fl">','<main class="wrap fl">'+BANNER)
            s=re.sub(r'<div class="notice" role="note"><span data-l="en">MIDI OUT Bank is now exclusive.*?</div>','',s,flags=re.S)
            s=s.replace('../assets/release.js?','release.js?')
            if 'midi-bank.js?' not in s:s=s.replace('</body>',f'<script src="midi-bank-data.js?v={STAMP}"></script><script src="midi-bank.js?v={STAMP}"></script></body>')
            raw=s.encode()
        if src.name=='app.js':
            s=raw.decode('utf-8')
            old='const r = window.MCBuilder.build(raw, window.MC_TWEAKS.device, tweaks, opts);'
            assert s.count(old)==1 or 'const prepared = window.MCMidiBankCompose' in s,'point integration app.js modifie'
            s=s.replace(old,'const prepared = window.MCMidiBankCompose ? window.MCMidiBankCompose(tweaks, raw, syntakt) : {tweaks, refMods: REF_MODS};\n    opts.refMods = prepared.refMods;\n    const r = window.MCBuilder.build(raw, window.MC_TWEAKS.device, prepared.tweaks, opts);')
            raw=s.encode()
        if src.suffix in ('.js','.html','.css','.md','.txt'):
            raw=('\n'.join(line.rstrip() for line in raw.decode('utf-8').splitlines()).rstrip()+'\n').encode()
        yield src.name,raw
    release='''// Version locale de la page experimentale ; aucun changement au main.
window.MC_RELEASES=[{version:"1.71-midi-preview",date:"2026-10-16",changes:[{en:"Experimental MIDI OUT Bank: install alone or alongside your selected machines, RETROSYN, TINY and optional Sample Wizard. Six MIDI lanes, CC locks/slides and native TEMPO. RAM only; hardware validation pending.",fr:"Banque MIDI OUT experimentale : seule ou avec les machines choisies, RETROSYN, TINY et Sample Wizard facultatif. Six voies MIDI, locks/slides CC et TEMPO natif. RAM uniquement ; validation materielle attendue."}]}];
'''
    if (base/'midi-bank.js').exists():release=(ROOT/'docs/assets/release.js').read_text(encoding='utf-8')
    yield 'release.js',release.encode()
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');a=p.parse_args()
    out=ROOT/'docs/flasher-midi-current-test';out.mkdir(exist_ok=True)
    for name,raw in files():
        dest=out/name
        if a.check:assert dest.read_bytes()==raw,name
        else:dest.write_bytes(raw)
    print('ok page MIDI experimentale reproductible ; main intact')
if __name__=='__main__':main()
