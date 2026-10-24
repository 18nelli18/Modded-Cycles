/* Fallback WAVE partage en lecture seule : pas de fichier/heap dans l IRQ.
 * Le chargeur existant remplace normalement ces pointeurs par piste. */
typedef unsigned int u32;typedef int s32;
extern const short wave_factory_pcm[];
extern void wave_previous_update(s32,char*,const char*);
#define WT_BASE ((volatile u32*)0x4677b2b8)
#define WT_COUNT ((volatile u32*)0x4677b2a0)
/* Le premier pad conserve le chargement natif du fichier deja choisi.
 * Laisser BASE en place pendant le test : l IRQ ne republie pas COUNT. */
void wave_allow_pad_import(u32 lane){
 u32 sounds=*(volatile u32*)0x40a78888;
 if(lane<6&&sounds&&*(volatile unsigned char*)(sounds+28+100*lane+38)==14&&WT_BASE[lane]==(u32)wave_factory_pcm){
  u32 handle=*(volatile u32*)(0x4677ab72+16*lane);
  if(handle&&handle!=0xffffffffu)WT_COUNT[lane]=0;
 }
}
void wave_starter_update(s32 pitch,char*voice,const char*params){
 u32 lane=((u32)voice-0x42308828u)/0x31cu;
 if(lane<6&&!WT_BASE[lane]){
  WT_COUNT[lane]=68608;
  WT_BASE[lane]=(u32)wave_factory_pcm;
 }
 wave_previous_update(pitch,voice,params);
}
