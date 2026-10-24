"""Conserver les six valeurs pendant le changement audio UI ; note149.
Le shim recoit l'ancien ID d5 avant l'appel reset. Contexte local sur pile,
aucun etat global ni parcours IRQ. Les limites du nouveau moteur sont natives.
"""
import subprocess,struct
CODE=0x467ee100;END=0x467ef000
C=r"""
typedef unsigned int u32;typedef unsigned short u16;typedef short i16;typedef unsigned char u8;
#define N(a) ((u32(*)())(a))
extern u32 kr_native(u32);extern void kr_bounds(u32,int*);
static const u32 slot[6]={10,18,11,12,13,14};
static u8 *sound(u32 obj){u32 vt=*(u32*)obj;return vt?(u8*)N(*(u32*)(vt+40))(obj):0;}
u32 kr_reset(u32 obj,u32 old){u8*p=sound(obj);if(!p)return kr_native(obj);u32 machine=p[38];if(old==17||machine==17||old>18||machine>18)return kr_native(obj);
 u32 packed=*(u32*)(p+72),tag=packed>>28;
 u16 before[6];for(u32 i=0;i<6;i++)before[i]=*(u16*)(p+20+slot[i]*2);
 u32 result=kr_native(obj);p=sound(obj);if(!p||p[38]!=machine)return result;
 if(machine==6&&(tag==7||tag==15))*(u32*)(p+72)=packed;
 for(u32 i=0;i<6;i++){if(i>=2&&(old==6||machine==6))continue;u32 desc=N(0x4005a692)(slot[i],machine);if(!desc)continue;int b[3];kr_bounds(desc,b);int value=(i16)before[i];if(value<b[0])value=b[0];if(value>b[1])value=b[1];*(u16*)(p+20+slot[i]*2)=(u16)value;}
 return result;}
void kr_fix_snapshot(u32 obj,u32 *v){u8*p=sound(obj);if(!p||p[38]!=6||v[1]-v[0]!=40)return;u32 *pairs=(u32*)v[0];
 static const u32 ws[5]={18,11,12,13,14};for(u32 i=0;i<5;i++){pairs[2*i]=ws[i];pairs[2*i+1]=(u32)*(u16*)(p+20+2*ws[i])<<16;}}
"""
S=r""".text
.globl kr_snapshot
kr_snapshot:
 lea -12(%sp),%sp
 movem.l %d2/%a2-%a3,(%sp)
 move.l %a0,%a2
 move.l 16(%sp),%a3
 move.l %a3,-(%sp)
 jsr 0x400148dc
 addq.l #4,%sp
 move.l %a2,-(%sp)
 move.l %a3,-(%sp)
 jsr kr_fix_snapshot
 addq.l #8,%sp
 move.l %a2,%d0
 movem.l (%sp),%d2/%a2-%a3
 lea 12(%sp),%sp
 rts
.globl kr_reset_hook
kr_reset_hook:
 move.l %d5,-(%sp)
 move.l %a2,-(%sp)
 jsr kr_reset
 addq.l #8,%sp
 jmp 0x40014804
"""
def apply(root,build,prefix,tail,meta,patch,isolate=False,max_machine=18):
 from gen_governor_recovery_test import TAIL
 c_source=C;s_source=S
 if isolate:
  from wizard_isolation_assets import C as c_source,S as s_source
 if max_machine!=18:c_source=c_source.replace('old>18||machine>18','old>'+str(max_machine)+'||machine>'+str(max_machine))
 cross=str(root.parent/'retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-');objects=[]
 for name,source in [('keep_params.c',c_source),('keep_params.S',s_source)]:
  src=build/name;src.write_text(source);obj=src.with_suffix(src.suffix+'.o');objects.append(obj);subprocess.run([cross+'gcc.exe','-mcpu=54418','-Os','-ffreestanding','-fno-builtin','-fno-pic','-fno-stack-protector','-Wall','-Wextra','-Werror','-c',str(src),'-o',str(obj)],check=True)
 ld=build/'keep_params.ld';elf=ld.with_suffix('.elf');binary=ld.with_suffix('.bin');bound=meta['scramble_mask']['symbols']['sx_bounds']
 bss=' .bss 0x467eed00 : { *(.bss*) *(COMMON) } kr_bss_end = .;' if isolate else ''
 ld.write_text(f'SECTIONS {{ .text {CODE:#x} : {{ *(.text*) *(.rodata*) }} . = ALIGN(4); .data : {{ *(.data*) }} kr_end = .; {bss} }}\nkr_native = 0x40014072;\nkr_bounds = {bound:#x};\n')
 subprocess.run([cross+'ld.exe','-T',str(ld),'-o',str(elf),*map(str,objects)],check=True);subprocess.run([cross+'objcopy.exe','-O','binary','-j','.text','-j','.data',str(elf),str(binary)],check=True)
 sy={v[2]:int(v[0],16) for line in subprocess.check_output([cross+'nm.exe',str(elf)],text=True).splitlines() if len(v:=line.split())==3};blob=binary.read_bytes();assert sy['kr_end']<END and not any(tail[CODE-TAIL:CODE-TAIL+len(blob)])
 patch(CODE,bytes(len(blob)),blob,tail);patch(0x400147fc,bytes.fromhex('2f0a4ebaf872'),b'\x4e\xf9'+struct.pack('>I',sy['kr_reset_hook']),prefix)
 patch(0x400a242a,bytes.fromhex('4df9400148dc'),b'\x4d\xf9'+struct.pack('>I',sy['kr_snapshot']),prefix)
 # Autoriser le retour au snapshot Wizard dans les deux chemins MACHINES natifs.
 # Les echantillons/options restent dans leur stockage existant; aucun cache global.
 if isolate:
  assert sy['kr_end']<0x467eed00 and sy['kr_bss_end']<END
  assert not any(tail[0x467eed00-TAIL:sy['kr_bss_end']-TAIL])
  patch(0x400a2712,bytes.fromhex('4fefffc448d77cfc'),b'\x4e\xf9'+struct.pack('>I',sy['kr_menu'])+b'\x4e\x71',prefix)
 else:
  patch(0x400a278e,bytes.fromhex('4bf9401bb194'),bytes.fromhex('4bf94001416c'),prefix)
  patch(0x400a2832,bytes.fromhex('4eb9401bb194'),bytes.fromhex('4eb94001416c'),prefix)
 return dict(code=CODE,code_bytes=len(blob),end=sy['kr_end'],symbols=sy,parameters=['Pitch','Decay','Color','Shape','Sweep','Contour'],clamp_to_destination_bounds=True,midi_transition_native=True,wizard_preserve_pitch_decay_only=True,wizard_isolated_banks=isolate,wizard_menu_snapshot_restored=not isolate,wizard_snapshot_slots=[18,11,12,13,14],wizard_packed_options_tags=[7,15],status='experimental',hardware_tested=False)
