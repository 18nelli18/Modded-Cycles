/* Adaptation MIDI de braids::Quantizer (Emilie Gillet, MIT).
 * La vraie construction du codebook/nearest-neighbour s'execute seulement
 * dans la tache UI. Le chemin note lit une table atomiquement publiee.
 * Les quatre choix historiques et leurs IDs sont conserves. */
#include "braids/quantizer.h"
#include "braids/quantizer_scales.h"
typedef unsigned int u32;typedef unsigned char u8;
extern "C" {extern volatile u8 bq_scale,bq_key;}
struct Map {u8 nearest[128];u32 original[128];};
static Map maps[2];static const Map*volatile active;
extern "C" {volatile u8 bq_mode;
#ifdef BQ_STARTUP_SAFE
volatile u8 bq_dirty;
#endif
}static u32 bank,prior_scale,prior_key;
static u8 held[6][128],valid[6][128],refs[6][128];
extern "C" void bq_refresh(void){
 u32 scale=bq_scale,key=bq_key;if(scale>18)return;
#ifdef BQ_STARTUP_SAFE
 if(!bq_mode)return;
#endif
 if(key>11)key=0;
 if(active&&scale==prior_scale&&key==prior_key)return;
 const u8 ids[19]={1,2,7,3,11,4,5,6,8,9,10,12,13,14,15,16,17,18,19};Map*dst=&maps[bank^1];braids::Quantizer q;
 const braids::Scale &def=braids::scales[ids[scale]];
 for(int n=0;n<127;n++){
  int input=n,output;
  do{int octave=(input-60)/12;if(input<60&&(input-60)%12)octave--;int shift=octave*12;q.Init();q.Configure(braids::scales[ids[scale]]);output=q.Process((input-60-shift)*128,key*128)/128+60+shift;if(output<0)input++;else if(output>126)input--;else break;}while(input>=0&&input<127);
  dst->nearest[n]=(u8)output;
  int count=(int)def.num_notes,offset=n-52,oct=offset/count,degree=offset%count;
  if(degree<0){degree+=count;oct--;}
  dst->original[n]=(u32)(48+key+12*oct+def.notes[degree]/128);
 }
 dst->nearest[127]=127;dst->original[127]=127;prior_scale=scale;prior_key=key;bank^=1;active=dst;
}
extern "C" u32 bq_note(u32 track,u32 note,u32 off){
 if(track>=6||note>=127)return note;
 if(off){
  if(!valid[track][note])return note;
  u32 target=held[track][note];valid[track][note]=0;
  if(refs[track][target])refs[track][target]--;
  return refs[track][target]?128:target;
 }
 /* Off : les nouvelles notes sont exactement natives. Une release d'une
  * note verrouillee auparavant continue de viser sa vraie note On. */
 if(!bq_mode||bq_mode>2||bq_scale>18||!active)return note;
 if(valid[track][note])return held[track][note];
 u32 target=bq_mode==1?active->original[note]:active->nearest[note];if(target>=127)return target;held[track][note]=target;valid[track][note]=1;refs[track][target]++;return target;
}
extern "C" void lp_frame(void),lp_old_frame(void);
#define N(a) ((u32(*)(...))(a))
static u32 loaded,last=0xffffffff;
#ifdef BQ_STARTUP_SAFE
static u32 seeded;
#endif
static void settings(void){
 u32 h[4]={0};u8 b[8],extra;
 if(!loaded){loaded=1;if(!N(0x4007bc5e)("/ScaleLock.cfg","r",h)){
  u32 ok=N(0x4007baaa)(b,8,h)==8&&!N(0x4007baaa)(&extra,1,h);N(0x4007bc1c)(h);
  if(ok&&b[0]=='S'&&b[1]=='L'&&b[2]==1&&b[3]<3&&b[4]<19&&b[5]<12&&b[6]==(u8)~b[3]&&b[7]==90){bq_mode=b[3];bq_scale=b[4];bq_key=b[5];}
 }}
 u32 now=(bq_mode<<16)|(bq_scale<<8)|bq_key;
#ifdef BQ_STARTUP_SAFE
 if(!seeded){seeded=1;if(!bq_dirty){last=now;return;}}
#endif
 if(now!=last&&!*(volatile u32*)0x40a78874&&!*(volatile u32*)0x40a7883c){
  b[0]='S';b[1]='L';b[2]=1;b[3]=bq_mode;b[4]=bq_scale;b[5]=bq_key;b[6]=~bq_mode;b[7]=90;
  if(!N(0x4007bc5e)("/ScaleLock.cfg","w",h)){u32 ok=!N(0x4007bb76)(h,0,8)&&N(0x4007bb0a)(b,8,h)==8&&!N(0x4007e2f6)(h);if(N(0x4007bc1c)(h))ok=0;if(ok){last=now;
#ifdef BQ_STARTUP_SAFE
 bq_dirty=0;
#endif
 }}
 }
}
extern "C" void bq_frame(void){
#ifdef BQ_STARTUP_SAFE
 lp_frame();lp_old_frame();
 u32 sr;__asm__ volatile("move.w %%sr,%0":"=d"(sr));
 if((sr&0x700)||!*(volatile u32*)0x40fe4178||*(volatile u32*)0x40a7883c==1||!N(0x400d0a10)())return;
 settings();bq_refresh();
#else
 settings();bq_refresh();lp_frame();lp_old_frame();
#endif
}
