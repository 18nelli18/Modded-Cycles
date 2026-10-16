#!/usr/bin/env python3
"""Catalogue RETROSYN et references strictes du flasheur principal (note 96).

Lit exclusivement les recettes generees et les OS officiels locaux ; n'exporte
aucun octet extrait du Syntakt, seulement les recettes et empreintes.
"""
import argparse,copy,hashlib,json,pathlib,sys
HERE=pathlib.Path(__file__).resolve().parent
sys.path[:0]=[str(HERE),str(HERE/'emu')]
import gen_retrosyn as R,build,syntakt,ref_mainos

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--cycles',required=True);ap.add_argument('--syntakt',required=True);ap.add_argument('--check',action='store_true');a=ap.parse_args()
    stock=R.g7.cycles_main(a.cycles);st=syntakt.dsp_image(a.syntakt)
    names={'s':'27-retrosyn.json','sw':'37-retrosyn-wizard.json','a':'28-retrosyn-all-machines.json','aw':'29-retrosyn-all-machines-wizard.json'}
    data={'recipes':{},'samplers':{},'refs':{}}
    for key,name in names.items():
        t=json.loads((R.DEV/name).read_text());w=t.pop('sampler_recipe',None)
        if w:data['samplers'][key]=w
        data['recipes'][key]=t
        for recipe in [t]+([w] if w else []):
            rt=build.payload_runtime(recipe,stock,st)
            payload=build.payload_image(recipe,rt)
            data['refs'][recipe['id']]={'w':hashlib.sha256(ref_mainos.writes_bytes(recipe)).hexdigest(),'p':hashlib.sha256(payload).hexdigest()}
        print('ok references',key,flush=True)
    text='// Genere par tools/gen_retrosyn_flasher.py ; ne pas modifier.\nwindow.MCRetrosyn='+json.dumps(data,ensure_ascii=False,separators=(',',':'))+';\n'
    out=HERE.parent/'docs/flasher/retrosyn-data.js'
    if a.check:assert out.read_text(encoding='utf-8')==text
    else:out.write_text(text,encoding='utf-8')
if __name__=='__main__':main()
