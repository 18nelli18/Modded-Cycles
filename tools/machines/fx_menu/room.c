/* ROOM original : deux combs amortis et un allpass par canal,12kHz.
 * Memoire PS1 reutilisee seulement quand ROOM est selectionne. Initialisation
 * paresseuse par compteur : aucun long effacement dans l interruption.
 * La remise a zero du PS1 a chaque transition garde ses propres queues exactes.
 */
#include "fx.h"
extern s16 ps_comb[2][4][2056],ps_ap[2][1024];
static u32 room_w,room_fill,room_pos[2],room_apfill[2],room_decay,room_tone;
static s32 room_low[2][2],room_previous[2];
static s32 sat(s32 x){return x>32767?32767:x< -32768?-32768:x;}
void fx_room_reset(void){
 room_w=room_fill=room_decay=room_tone=0;
 for(u32 c=0;c<2;c++){room_pos[c]=room_apfill[c]=0;room_previous[c]=0;for(u32 k=0;k<2;k++)room_low[c][k]=0;}
}
void fx_room(s32*out,const s32*in,const s16*params){
 u32 size=params[0]<0?0:(u32)params[0]>>8,tone=params[1]<0?0:(u32)params[1]>>8;
 if(size>127)size=127;if(tone>127)tone=127;
 u32 decay=8192+size*22528/127,damp=2048+tone*26624/127;
 if(!room_fill){room_decay=decay;room_tone=damp;}
 else{room_decay=(u32)((s32)room_decay+(((s32)decay-(s32)room_decay)>>5));room_tone=(u32)((s32)room_tone+(((s32)damp-(s32)room_tone)>>5));}
 for(u32 i=0;i<32;i+=4){
  for(u32 c=0;c<2;c++){
   s32 input=(in[2*i+c]>>18)+(in[2*(i+1)+c]>>18)+(in[2*(i+2)+c]>>18)+(in[2*(i+3)+c]>>18),sum=0;
   for(u32 k=0;k<2;k++){
    u32 n=(k?349:223)+c*(k?31:17);s32 old=room_fill<n?0:ps_comb[c][k][(room_w-n)&1023];sum+=old;
    s32 low=room_low[c][k]+(((old-room_low[c][k])*(s32)room_tone)>>15);
    if(!input&&low>-2&&low<2)low=0;
    room_low[c][k]=low;ps_comb[c][k][room_w]=(s16)sat((input>>1)+((low*(s32)room_decay)>>15));
   }
   s32 x=sum/2;u32 p=room_pos[c],n=67+12*c;s32 z=room_apfill[c]<n?0:ps_ap[c][p];
   s32 y=sat(z-(x>>1));ps_ap[c][p]=(s16)sat(x+(y>>1));room_pos[c]=p+1==n?0:p+1;if(room_apfill[c]<n)room_apfill[c]++;
   s32 previous=room_previous[c];for(u32 j=0;j<4;j++)out[2*(i+j)+c]=(previous+(y-previous)*(s32)(j+1)/4)*65536;room_previous[c]=y;
  }
  room_w=(room_w+1)&1023;if(room_fill<1024)room_fill++;
 }
}
