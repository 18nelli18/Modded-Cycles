"""Note 99 : module beat repeat propre relogeable et petit chargeur ROM.

python3 tools/gen_beat_repeat.py --catalog build/midi-persistence-main/all.json
  --output build/beat-repeat-data.json
Le catalogue reserve les masques existants. Aucune routine OS exportee.
"""
import argparse,json,pathlib,re,shutil,subprocess,tempfile
import build,sprites
ROOT=pathlib.Path(__file__).resolve().parents[1]
def symbols(cross,elf):
    return {x[2]:int(x[0],16) for line in subprocess.check_output([cross+'nm','--defined-only',str(elf)],text=True).splitlines() if len(x:=line.split())==3}
def generate(catalogs, source=None):
    used=[(build.BASE+w['off'],build.BASE+w['off']+len(bytes.fromhex(w['new']))) for cat in catalogs for t in cat['tweaks'] for w in t['writes']]
    gaps=[]
    for mask,row in sprites.MASKS.items():
        if len(row)!=4 or mask==0x4018dba8:continue
        cursor=mask
        for lo,hi in sorted((max(mask,lo),min(mask+row[0],hi)) for lo,hi in used if lo<mask+row[0] and mask<hi):
            if cursor<lo:gaps.append([((cursor+3)&~3),lo,mask])
            cursor=max(cursor,hi)
        if cursor<mask+row[0]:gaps.append([((cursor+3)&~3),mask+row[0],mask])
    cross=next((p for p in ('m68k-linux-gnu-','m68k-elf-') if shutil.which(p+'gcc')),None)
    if not cross:raise RuntimeError('GCC ColdFire requis')
    with tempfile.TemporaryDirectory() as tmp:
        p=pathlib.Path(tmp);src=pathlib.Path(source) if source else ROOT/'tools/machines/beat_repeat'
        subprocess.run([cross+'gcc','-std=gnu99','-mcpu=54418','-Os','-ffreestanding','-fno-builtin','-fno-common','-fno-pic','-fno-stack-protector','-fno-asynchronous-unwind-tables','-fno-inline','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-c',str(src/'repeat.c'),'-o',str(p/'c.o')],check=True)
        subprocess.run([cross+'gcc','-mcpu=54418','-c',str(src/'hooks.s' if (src/'hooks.s').exists() else ROOT/'tools/machines/beat_repeat/hooks.s'),'-o',str(p/'s.o')],check=True)
        subprocess.run([cross+'gcc','-mcpu=54418','-c',str(src/'popup.s' if (src/'popup.s').exists() else ROOT/'tools/machines/beat_repeat/popup.s'),'-o',str(p/'popup.o')],check=True)
        (p/'link.ld').write_text('SECTIONS { .text 0 : { *(.text*) *(.rodata*) } . = ALIGN(4); .state : { *(.br_state) *(.data*) *(.bss*) } . = ALIGN(4); br_end = .; }')
        subprocess.run([cross+'ld','--emit-relocs','-T',str(p/'link.ld'),'-o',str(p/'e.elf'),str(p/'c.o'),str(p/'s.o'),str(p/'popup.o')],check=True)
        subprocess.run([cross+'objcopy','-O','binary',str(p/'e.elf'),str(p/'e.bin')],check=True)
        syms=symbols(cross,p/'e.elf');body=(p/'e.bin').read_bytes();body+=bytes(syms['br_end']-len(body))
        rel=subprocess.check_output([cross+'readelf','-rW',str(p/'e.elf')],text=True)
        offsets=[int(m.group(1),16) for m in re.finditer(r'^([0-9a-f]+)\s+\S+\s+R_68K_32\b',rel,re.M)]
        for off in offsets:assert int.from_bytes(body[off:off+4],'big')<len(body)
        subprocess.run([cross+'gcc','-mcpu=54418','-c',str(src/'boot.s' if (src/'boot.s').exists() else ROOT/'tools/machines/beat_repeat/boot.s'),'-o',str(p/'boot.o')],check=True)
        size=int(next(line.split()[2] for line in subprocess.check_output([cross+'objdump','-h',str(p/'boot.o')],text=True).splitlines() if len(line.split())>3 and line.split()[1]=='.text'),16)
        fits=[g for g in gaps if g[1]-g[0]>=size];assert fits,('chargeur sans place',size)
        gap=min(fits,key=lambda g:g[1]-g[0]);at,_,mask=gap
        (p/'boot.ld').write_text(f'SECTIONS {{ .text {at:#x} : {{ *(.text*) }} }}')
        subprocess.run([cross+'ld','-T',str(p/'boot.ld'),'-o',str(p/'boot.elf'),str(p/'boot.o')],check=True)
        subprocess.run([cross+'objcopy','-O','binary',str(p/'boot.elf'),str(p/'boot.bin')],check=True)
        boot=(p/'boot.bin').read_bytes();assert len(boot)==size
        bs=symbols(cross,p/'boot.elf')
    return dict(hex=body.hex(),symbols=syms,reloc=offsets,boot=dict(at=at,hex=boot.hex(),symbols={k:v-at for k,v in bs.items()}),redirect=sprites.redirect_write(mask),history_bytes=1572864,status='experimental')
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--catalog',action='append',required=True);p.add_argument('--output',required=True);p.add_argument('--check',action='store_true');a=p.parse_args()
    data=generate([json.loads(pathlib.Path(c).read_text()) for c in a.catalog]);text=json.dumps(data,separators=(',',':'))+'\n';out=pathlib.Path(a.output)
    if a.check:assert out.read_text(encoding='utf-8')==text
    else:out.parent.mkdir(parents=True,exist_ok=True);out.write_text(text,encoding='utf-8')
    print('ok beat repeat experimental :',len(data['hex'])//2,'octets RAM ; chargeur ROM',len(data['boot']['hex'])//2,'octets ; aucun Model-TG requis')
if __name__=='__main__':main()
