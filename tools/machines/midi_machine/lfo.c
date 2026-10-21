/* LFO MIDI sur l'horloge audio native, sans ordonnanceur B. Les mm_lfo_phases sont
 * privees aux pistes MIDI ; aucune E/S dans l'IRQ. Restaurer toute la tranche
 * MIDI apres les LFO audio afin qu'un CC ne devienne jamais une cible DSP.
 */
typedef unsigned int u32;
typedef signed int i32;
typedef unsigned short u16;
typedef unsigned char u8;
#ifndef MM_MACHINE
#define MM_MACHINE 6
#endif
extern u32 mm_lfo_read(const u16 *,u32,u32);
extern u32 mm_channel(const u16 *,u32),mm_port(const u16 *);
extern u32 mm_cc_put(u32,u32,u32,u32,u32,u32);
extern void mm_lfo_native(void *,u32,u32,void *);
volatile u32 mm_lfo_api[1]={0x40091ab2};
static u32 mm_lfo_phases[2][48],mm_lfo_last[12],mm_lfo_seen,mm_lfo_divider,mm_lfo_roundrobin;
/* Publication UI atomique : la copie audio du son peut attendre le prochain
 * trig. Une rotation Speed doit cependant agir sur la note deja tenue.
 * Le prochain trig reprend les valeurs du son et ses locks natifs. */
static volatile u32 mm_lfo_live_speed_words[12];
void mm_lfo_live_speed(u32 lane,u32 lfo,u32 value){
 if(lane<6&&lfo<2&&value<32768)mm_lfo_live_speed_words[lfo*6+lane]=0x80000000u|value;
}
void mm_lfo_dispatch(u8 *frame,u32 bpm,u32 triggers){
 u16 saved[6][33];u32 mask=0;
 for(u32 lane=0;lane<6;lane++){
  u16 *p=(u16 *)(frame+14+66*lane);
  if(p[9]!=(MM_MACHINE<<8)){
   mm_lfo_live_speed_words[lane]=mm_lfo_live_speed_words[6+lane]=0;continue;
  }
  if(triggers&(1u<<lane))mm_lfo_live_speed_words[lane]=mm_lfo_live_speed_words[6+lane]=0;
  mask|=1u<<lane;
  for(u32 i=0;i<33;i++)saved[lane][i]=p[i];
  p[4]=127<<8;
 }
 ((void (*)(void *,u32,u32))mm_lfo_api[0])(frame,bpm,triggers);
 for(u32 lane=0;lane<6;lane++)if(mask&(1u<<lane)){
  u16 *p=(u16 *)(frame+14+66*lane);
  for(u32 i=0;i<33;i++)p[i]=saved[lane][i];
 }
 if(!mask){mm_lfo_seen=0;return;}
 u32 active[2]={0,0};
 for(u32 lfo=0;lfo<2;lfo++)for(u32 lane=0;lane<6;lane++){
  if(!(mask&(1u<<lane)))continue;
  if(!(mm_lfo_seen&(1u<<lane))){
   for(u32 i=0;i<8;i++)mm_lfo_phases[lfo][lane*8+i]=0;
   mm_lfo_last[lfo*6+lane]=0xffffffffu;
  }
  if(mm_lfo_read(saved[lane],lfo,3)<128&&mm_lfo_read(saved[lane],lfo,7)!=16384)active[lfo]|=1u<<lane;
 }
 mm_lfo_seen=mask;
 for(u32 lfo=0;lfo<2;lfo++)if(active[lfo]){
  u32 temporary[119];u8 *copy=(u8 *)temporary;
  for(u32 i=0;i<119;i++)temporary[i]=0;
  for(u32 lane=0;lane<6;lane++){
   u16 *p=(u16 *)(copy+14+66*lane);p[4]=127<<8;
   if(!(active[lfo]&(1u<<lane)))continue;
   for(u32 i=0;i<8;i++){
    u32 value=mm_lfo_read(saved[lane],lfo,i);
    if(!i&&(mm_lfo_live_speed_words[lfo*6+lane]&0x80000000u))value=mm_lfo_live_speed_words[lfo*6+lane]&32767;
    p[1+i]=(i==1||i==3||i==4||i==6)?value<<8:value;
   }
   p[4]=11<<8;p[11]=16384;
  }
  mm_lfo_native(copy,bpm,triggers,mm_lfo_phases[lfo]);
 }
 if(++mm_lfo_divider<3)return;
 mm_lfo_divider=0;
 for(u32 scanned=0;scanned<12;scanned++){
  u32 index=mm_lfo_roundrobin++;if(mm_lfo_roundrobin==12)mm_lfo_roundrobin=0;
  u32 lfo=index/6,lane=index%6;if(!(active[lfo]&(1u<<lane)))continue;
  i32 value=(16384+(i32)mm_lfo_phases[lfo][lane*8+5])>>8;
  if(value<0)value=0;
  if(value>127)value=127;
  u32 cc=mm_lfo_read(saved[lane],lfo,3),channel=mm_channel(saved[lane],lane),port=mm_port(saved[lane]);
  u32 key=(channel<<24)|(port<<16)|(cc<<8)|(u32)value;
  if(mm_lfo_last[index]==key)continue;
  if(mm_cc_put(lane,12+lfo,channel,cc,(u32)value,port))mm_lfo_last[index]=key;
  break;
 }
}
