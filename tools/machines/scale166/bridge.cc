/* Adaptation MIDI de braids::Quantizer (Emilie Gillet, MIT).
 * La vraie construction du codebook/nearest-neighbour s'execute seulement
 * dans la tache UI. Le chemin note lit une table atomiquement publiee.
 * Les quatre choix historiques et leurs IDs sont conserves. */
#include "braids/quantizer.h"
#include "braids/quantizer_scales.h"
typedef unsigned int u32;typedef unsigned char u8;
extern "C" {extern volatile u8 bq_scale,bq_key;}
static u8 maps[2][128];static const u8*volatile active;static u32 bank,prior_scale,prior_key;
static u8 held[6][128],valid[6][128],refs[6][128];
extern "C" void bq_refresh(void){
 u32 scale=bq_scale,key=bq_key;if(!scale||scale>4)return;if(key>11)key=0;
 if(active&&scale==prior_scale&&key==prior_key)return;
 const u8 ids[5]={0,2,7,3,11};u8*dst=maps[bank^1];braids::Quantizer q;
 for(int n=0;n<127;n++){
  int input=n,output;
  do{q.Init();q.Configure(braids::scales[ids[scale]]);output=q.Process((input-60)*128,key*128)/128+60;if(output<0)input++;else if(output>126)input--;else break;}while(input>=0&&input<127);
  dst[n]=(u8)output;
 }
 dst[127]=127;prior_scale=scale;prior_key=key;bank^=1;active=dst;
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
 if(!bq_scale||bq_scale>4||!active)return note;
 if(valid[track][note])return held[track][note];
 u32 target=active[note];held[track][note]=target;valid[track][note]=1;refs[track][target]++;return target;
}
extern "C" void lp_frame(void),lp_old_frame(void);
extern "C" void bq_frame(void){bq_refresh();lp_frame();lp_old_frame();}
