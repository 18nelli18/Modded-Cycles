"""Prototype sampler isolé et Slice varispeed, non flashable à ce stade."""
import pathlib,runpy,subprocess,json,shutil
from gen_seq_gen import symbols
from gen_model_tg_varispeed import generate
from chord_keys_pr87 import load_stock
p=pathlib.Path('work/sample-wizard-main');None # sources isolées déjà préparées
cross=next(c for c in ['m68k-elf-','m68k-linux-gnu-'] if shutil.which(c+'as'))
objects=[]
for name,source in [('sampler-guard','src/model_tg.s'),('phase1','src/phase1.s'),('adapters','sampler-adapters.s')]:
 o=p/(name+'.o');subprocess.run([cross+'as','-march=cfv4e','-I',str(p/'src'),'-o',str(o),str(p/source)],check=True);objects.append(str(o))
def link(end):
 subprocess.run([cross+'ld','-Ttext=0x401ab750','--defsym=blob_start=0x401ab750','--defsym=reserved_end='+hex(end),'-e','boot_extra_hook','-o',str(p/'guard.elf'),*objects],check=True)
 subprocess.run([cross+'objcopy','-O','binary',str(p/'guard.elf'),str(p/'guard.bin')],check=True)
 return (p/'guard.bin').read_bytes()
probe=link(0);end=0x401ab750+((len(probe)+15)&~15);code=link(end);assert len(code)==len(probe);code+=bytes(end-0x401ab750-len(code));(p/'guard.bin').write_bytes(code)
s=symbols(cross,p/'guard.elf');raw=bytes(0x1610)+code;base={'id':'model-tg','order':20,'writes':[],'symbols':{k:hex(v) for k,v in s.items()},'append':{'at':'0x401aa140','dest':'0x401aa140','size':len(raw),'parts':[{'dest':'0x401aa140','hex':raw.hex()}],'reloc':[]},'prototype_only':True,'flashable':False}
(p/'base.json').write_text(json.dumps(base));t=generate(base,p/'guard.elf',load_stock('firmware/model-cycles_OS1.13.syx'),cross);t.update(prototype_only=True,flashable=False);(p/'varispeed.json').write_text(json.dumps(t));print('PASS assembler/linker :',len(code),'octets ; réserve alignée',hex(end),'; Slice varispeed',t['varispeed_mask']['used'],'octets')
