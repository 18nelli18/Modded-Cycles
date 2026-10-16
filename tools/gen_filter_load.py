"""Note 105 : meme calcul EMAC, checks de saturation redondants supprimes."""
import argparse,json,hashlib,pathlib
from gen_filter_precision import generate,ROOT
def main():
 p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args();d=generate(ROOT/'tools/machines/track_filter/load.s')
 old=(ROOT/'docs/flasher/filter-precision-data.js').read_text();old=json.loads(old.split('=',1)[1].strip().rstrip(';'));d['old_sha256']=hashlib.sha256(bytes.fromhex(old['hex'])).hexdigest()
 target=ROOT/'build/filter-load-data.js';text='window.MCFilterLoad='+json.dumps(d,separators=(',',':'))+';\n'
 if a.check:assert target.read_text()==text
 else:target.write_text(text)
 print('PASS filtre charge',d['code_size'],'octets /',d['size'])
if __name__=='__main__':main()
