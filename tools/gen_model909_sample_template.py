#!/usr/bin/env python3
"""Kit complet public, sans échantillons ; table et pool remplis au build local."""
import argparse,json,pathlib
import gen_model909_additive as g9,gen_model909_acid_replacement as gen
from test_sdvintage import main_os_from_syx
p=argparse.ArgumentParser();p.add_argument('--cycles',required=True);p.add_argument('--tg',required=True);p.add_argument('--output',required=True);a=p.parse_args()
g9.SRC=pathlib.Path(__file__).parent/'machines/model909_full'
g9.MACHINES += [('HATS909','hh',(('HH Tone','TONE',64),('HH Type','TYPE',0,0,1),('HH Bits','BITS',0),('HH None','----',0))),('CYM909','cy',(('Cym Tone','TONE',64),('Cym Type','TYPE',0,0,1),('Cym Bits','BITS',0),('Cym None','----',0)))]
gen.SLOTS=[('BD909','bd',0),('SD909','sd',1),('HATS909','hh',4),('RC909','rc',2),('TOM909','tom',3),('CYM909','cy',5)]
out=gen.generate(main_os_from_syx(a.cycles),json.loads(pathlib.Path(a.tg).read_text()),sample_capacity=180000)
pathlib.Path(a.output).write_text(json.dumps(out,indent=1)+'\n');print('Template sans audio privé',out['sample_slots'])
