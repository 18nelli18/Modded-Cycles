/* Attribution par piste des vrais fondus : aucun changement de seuil ou de victime.
 * Aucun formatage dans l IRQ ; instrumentation seulement si DX est actif. */
typedef unsigned int u32;typedef unsigned char u8;
extern volatile u32 dt_enabled,dt_api[3];
extern void mf_old_audio_end(void);
volatile u32 dt_cuts[6],dt_t5_s,dt_t5_l,dt_t5_valid;
static void (*dt_old_popup)(const char*);
static u32 mask(void){const volatile u8*p=(const volatile u8*)0x46732058;u32 v=0;if(p[0])v|=1;if(p[1])v|=2;if(p[2])v|=4;if(p[3])v|=8;if(p[4])v|=16;if(p[5])v|=32;return v;}
void dt_audio_end(void){
 if(!dt_enabled){mf_old_audio_end();return;}
 u32 before=mask();mf_old_audio_end();u32 added=mask()&~before;
 if(added&16){u32 fast=*(volatile u32*)0x46732f10>>3,slow=*(volatile u32*)0x46732f14>>8;dt_t5_s=fast<slow?fast:slow;dt_t5_l=*(volatile u32*)0x4673207c;dt_t5_valid=1;}
 if(added)for(u32 t=0;t<6;t++)if((added&(1u<<t))&&dt_cuts[t]<99)dt_cuts[t]++;
}
static void dt_popup(const char*text){
 if(text&&text[0]=='A'&&text[1]>='0'&&text[1]<='9'){
  u32 sustained,load,valid,sr;char line[40];
  __asm__ volatile("move.w %%sr,%0\nmove.w #0x2700,%%sr":"=d"(sr)::"memory","cc");
  sustained=dt_t5_s;load=dt_t5_l;valid=dt_t5_valid;dt_t5_valid=0;for(u32 t=0;t<6;t++)dt_cuts[t]=0;
  __asm__ volatile("move.w %0,%%sr"::"d"(sr):"memory","cc");
  if(valid)((u32(*)())0x40000e6e)(line,"T5 S%u L%u",(sustained*100+128)/256,(load*100+128)/256);else ((u32(*)())0x40000e6e)(line,"T5 NO CUT");
  dt_old_popup(line);
 }else dt_old_popup(text);
}
void dt_init(void){if(dt_api[2]==(u32)dt_popup)return;dt_old_popup=(void(*)(const char*))dt_api[2];dt_api[2]=(u32)dt_popup;}
