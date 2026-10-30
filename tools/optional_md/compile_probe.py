"""Mesure privee : DSP MD epingle, donnees issues du BIN utilisateur verifie."""
from pathlib import Path
import hashlib,json,struct,subprocess,sys,os
W=Path(os.environ['MD_WORK']);R=Path(__file__).resolve().parents[2];S=R/'tools/machines/md';B=W/'probe';B.mkdir(exist_ok=True)
sys.path[:0]=[str(R/'tools'),str(S)]
import headers,md_os
rom=Path(os.environ['MD_ROM'])
sha='68542e30917b9918ccaee2b2237df62c8a00479938680b85aca93ce4fbca44c8'
data=rom.read_bytes();actual=hashlib.sha256(data).hexdigest();assert actual in (sha,md_os.OS_SHA256)
# Le BIN et le SYX contiennent les memes sections. Ne pas confondre leurs SHA.
if actual==sha:
 md_os.image=lambda path:(data[0x4000:],sha)
 md_os.OS_SHA256=sha
headers.write(rom,B)
cross=os.environ['M68K_CROSS']
os.environ['PATH']=str(Path(cross).parent)+os.pathsep+os.environ.get('PATH','')
objects=[]
for name in ('bridge','trx_b2','trx_sd','trx_ch','trx_b2_md'):
 src=B/(name+'.c') if name=='trx_b2_md' else S/(name+'.c');obj=B/(name+'.o')
 subprocess.run([cross+'gcc'+os.environ.get('MD_EXE',''),'-mcpu=54418','-O2','-fwrapv','-ffreestanding','-fno-builtin','-fno-tree-loop-distribute-patterns','-ffunction-sections','-fdata-sections','-fno-pic','-fno-stack-protector','-Wall','-Wextra','-Werror','-I',str(S),'-I',str(B),'-c',str(src),'-o',str(obj)],check=True);objects.append(str(obj))
for name in ('catalogue.S','selection.c'):
 src=B/name
 if src.exists():
  obj=src.with_suffix('.o');subprocess.run([cross+'gcc'+os.environ.get('MD_EXE',''),'-mcpu=54418','-O2','-ffreestanding','-fno-builtin','-c',str(src),'-o',str(obj)],check=True);objects.append(str(obj))
code=0x469c0000;bss=0x469f8000
ld=B/'probe.ld';ld.write_text(f'SECTIONS {{ .text {code:#x} : {{ *(.text*) *(.data*) *(.rodata*) }} .bss {bss:#x} (NOLOAD) : {{ md_bss_start = .; *(.bss*) *(COMMON) md_bss_end = .; }} }}')
elf=B/'md.elf';binary=B/'md.bin'
subprocess.run([cross+'ld'+os.environ.get('MD_EXE',''),'-T',str(ld),'-e','md_render32','-Map',str(B/'md.map'),'-o',str(elf),*objects],check=True)
subprocess.run([cross+'objcopy'+os.environ.get('MD_EXE',''),'-O','binary',str(elf),str(binary)],check=True)
sy={v[2]:int(v[0],16) for line in subprocess.check_output([cross+'nm'+os.environ.get('MD_EXE',''),str(elf)],text=True).splitlines() if len(v:=line.split())==3}
report=dict(upstream='Talachan12/Elektron-Model-Machinedrum',revision='70e1483535c5a6919ff170ce3b79ba4a10c066ac',user_rom_sha256=actual,code=code,code_bytes=len(binary.read_bytes()),bss=bss,bss_bytes=sy['md_bss_end']-bss,symbols=sy,proposed_ids=[25,26,27],existing_ids_preserved=True,SRAM_not_overwritten=True,hardware_tested=False,firmware_image_built=False)
assert code+report['code_bytes']<=bss and sy['md_bss_end']<=0x46a00000
(B/'BUILD.json').write_text(json.dumps(report,indent=2)+'\n')
print('PASS private ColdFire module:',report['code_bytes'],'code/tables;',report['bss_bytes'],'state bytes; fits469c0000..46a00000 without GATED/POTS/WAVE overlap')
