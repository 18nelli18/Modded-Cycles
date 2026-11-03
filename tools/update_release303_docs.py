"""Met a jour les commandes du guide et les liens de l'historique3.03."""
from pathlib import Path
import argparse
import json
import re

p=argparse.ArgumentParser();p.add_argument('--repo',type=Path,required=True);a=p.parse_args();root=a.repo
def put(path,text):path.write_text(text,encoding='utf-8',newline='\n')
for folder in ('flasher','flasher-optional'):
    file=root/'docs'/folder/'index.html';text=file.read_text(encoding='utf-8')
    marker='<section class="alert" id="bug-report-section"'
    card='<section class="alert release-update" aria-labelledby="release-update-title"><h2 id="release-update-title"><span data-l="en">What changed in this version…</span><span data-l="fr">Changements de cette version…</span></h2><div data-rel="changes"></div><p><a href="../version-history.html"><span data-l="en">Version history</span><span data-l="fr">Historique des versions</span></a></p></section>\n'
    assert marker in text;text=text.replace(marker,card+marker,1)
    text=re.sub(r'((?:shortcut-guide|user-manual)\.pdf\?v=)[^"\s]+',r'\g<1>2026-11-03-guide303',text)
    put(file,text)
file=root/'docs/index.html';text=file.read_text(encoding='utf-8')
text=text.replace('<div data-rel="changes"></div>', '<h3><span data-l="en">What changed in this version…</span><span data-l="fr">Changements de cette version…</span></h3><div data-rel="changes"></div><p><a href="version-history.html"><span data-l="en">Version history</span><span data-l="fr">Historique des versions</span></a></p>')
text=re.sub(r'((?:shortcut-guide|user-manual)\.pdf\?v=)[^"\s]+',r'\g<1>2026-11-03-guide303',text);put(file,text)
file=root/'tools/shortcut_guide_content.json';data=json.loads(file.read_text(encoding='utf-8'));data['release']='3.03';data['stamp']='2026-11-03-guide303'
for section in data['sections']:
    for row in section['rows']:
        for lang in ('en','fr'):
            values=row[lang]
            values[:]=[v.replace('3.02','3.03').replace('start at the first row','start at the highlighted row').replace('demarrer a la premiere ligne','demarrer sur la ligne selectionnee') for v in values]
            if values[0]=='Step Recorder':
                values[2]+=(' Octaves: FUNC + TRACK > KBT; +/-12 semitones shifts one octave.' if lang=='en' else ' Octaves : FUNC + TRACK > KBT ; +/-12 demi-tons deplace une octave.')
            if values[0] in ('End behavior','Fin de lecture'):
                values[2]+=(' PLAY while stopped starts at the highlighted row. LOOP wraps through the whole arrangement.' if lang=='en' else ' PLAY a l arret demarre sur la ligne selectionnee. LOOP parcourt tout l arrangement.')
put(file,json.dumps(data,ensure_ascii=False,indent=2)+'\n')
for name in ('gen_shortcut_guide.py','gen_user_manual.py','gen_print_shortcut_guide.py'):
    file=root/'tools'/name;text=file.read_text(encoding='utf-8').replace('3.02','3.03').replace('manual302','manual303').replace('guide302','guide303')
    text=text.replace('to begin at the first row','to begin at the highlighted row').replace('Press PLAY to continue.','Press PLAY while stopped to start from the highlighted row.')
    text=text.replace('Supermodel3.03 - 30 octobre2026','Supermodel3.03 - 3 novembre2026')
    if name=='gen_user_manual.py':
        text=text.replace("'Play notes to enter steps. <b>PLAY</b> advances one step; <b>STOP</b> moves back. Press <b>REC</b> again to leave Step Recorder.'", "'Play notes to enter steps. <b>PLAY</b> advances one step; <b>STOP</b> moves back. <b>FUNC + TRACK &gt; KBT</b> shifts the trig keyboard; +/-12 semitones moves an octave. Press <b>REC</b> again to leave Step Recorder.'")
    put(file,text)
print('Updated3.03 guide sources, controls, history links and guide cache stamps')
