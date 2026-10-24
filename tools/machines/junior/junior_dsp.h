/* Machine privee inspiree de Fors Junior : implementation originale.
 * Coeur entier, table32 valeurs quatre bits, LFSR7bits et quatre tables16pas.
 * Aucun code, preset ou ressource du plugin Fors n'est copie.
 * Wave : banque/morph ; Warp : width/fold/wrap/scan ; Noise : balance ;
 * Motion : statique, vibrato, PWM, wave sequence, arp majeur/mineur,
 * percussion one-shot, glitch. PUNCH ajoute un second oscillateur detune mono.
 * Les tables de modulation sont des presets, sans editeur libre dans cet essai.
 */
#ifndef JUNIOR_DSP_H
#define JUNIOR_DSP_H
typedef signed char s8;
typedef short s16;
typedef int s32;
typedef unsigned int u32;
#include "junior_tables.h"
typedef struct {
 u32 phase,phase2,noise_phase,lfsr,random;
 s32 clock,step,cache_wave,cache_warp;
 s8 wave[32];
} JuniorState;
typedef struct {s32 note,wave,warp,noise,motion,punch,trig;} JuniorInput;
static s32 jr_clip(s32 n,s32 lo,s32 hi){return n<lo?lo:n>hi?hi:n;}
static void junior_reset(JuniorState *s){
 s->phase=s->phase2=s->noise_phase=0;s->lfsr=127;s->random=0x6d2b79f5;
 s->clock=s->step=0;s->cache_wave=s->cache_warp=-1;
}
static u32 junior_inc(s32 note){
 s32 n=jr_clip(note,0,127<<16),i=n>>16;
 return JR_INC[i]+(((JR_INC[i+1]-JR_INC[i])>>10)*((u32)(n&65535)>>6));
}
static void junior_wave(JuniorState *s,s32 w,s32 warp){
 if(w==s->cache_wave && warp==s->cache_warp)return;
 s->cache_wave=w;s->cache_warp=warp;
 s32 a=w>>3,b=(a+1)&15,f=w&7,mode=warp>>5,amount=warp&31;
 for(s32 i=0;i<32;i++){
  s32 x=i,blank=0;
  if(mode==0){s32 width=32-amount;if(width<2)width=2;u32 inv=JR_WIDTH_RECIP[width];x=(s32)((i*inv+(inv>>1))>>10);blank=x>31;x&=31;}
  else if(mode==2)x=(i*(1+(amount>>2)))&31;
  else if(mode==3)x=(i+amount)&31;
  s32 v=(JR_WAVE[a][x]*(8-f)+JR_WAVE[b][x]*f+4)>>3;
  if(mode==1){s32 z=((v+8)*(1+(amount>>2)))&31;v=(z<16?z:31-z)-8;}
  s->wave[i]=(s8)(blank?0:jr_clip(v,-8,7));
 }
}
void junior_block(JuniorState *s,const JuniorInput *in,s32 *out){
 s32 motion=jr_clip(in->motion,0,127),mode=motion>>4,pos,delta=0;
 s32 wave=jr_clip(in->wave,0,127),warp=jr_clip(in->warp,0,127),mix=jr_clip(in->noise,0,127);
 if(in->trig)junior_reset(s);
 if(mode){
  if(!in->trig){s->clock+=32;if(s->clock>=JR_PERIOD[motion&15]){
   s->clock-=JR_PERIOD[motion&15];if(mode!=6||s->step<15)s->step=(s->step+1)&15;
   s->random^=s->random<<13;s->random^=s->random>>17;s->random^=s->random<<5;
  }}
 }else{s->clock=s->step=0;}
 pos=s->step;
 /* Quatre pistes de table : pitch, wave, warp et volume/bruit. */
 s32 pw=0,ww=0,fw=0,amp=128;
 switch(mode){
  case 1:pw=JR_VIB[pos]*4096;break;
  case 2:fw=JR_TRI[pos]*3;break;
  case 3:ww=JR_TRI[pos]*7;fw=JR_TRI[(pos+4)&15];break;
  case 4:pw=JR_MAJOR[pos]*65536;ww=JR_TRI[pos]*2;break;
  case 5:pw=JR_MINOR[pos]*65536;ww=JR_TRI[pos]*2;break;
  case 6:pw=(15-pos)*65536;fw=(15-pos);amp=JR_DECAY[pos];break;
  case 7:pw=JR_GLITCH[pos]*65536;ww=(s32)(s->random&31)-16;fw=(s32)((s->random>>8)&31)-16;break;
 }
 if(mode==2){warp=(warp&96)|jr_clip((warp&31)+fw,0,31);}
 else warp=jr_clip(warp+fw,0,127);
 junior_wave(s,jr_clip(wave+ww,0,127),warp);
 u32 inc=junior_inc(in->note+pw),inc2=inc;
 if(in->punch){delta=(s32)(inc>>8);inc2=inc-(u32)delta;inc+=(u32)delta;}
 u32 ninc=inc>0x1fffffff?0xffffffff:inc<<3;
 u32 ph=s->phase,ph2=s->phase2,np=s->noise_phase,l=s->lfsr;
 if(mix==127)mix=128;
 /* Une cadence LFSR bornee : jamais de boucle proportionnelle a la frequence. */
 for(s32 i=0;i<32;i++){
  s32 v=s->wave[ph>>27];ph+=inc;
  if(in->punch){v=(v+s->wave[ph2>>27])>>1;ph2+=inc2;}
  if(mix){u32 next=np+ninc;if(next<np)l=(l>>1)|(((l^(l>>1))&1)<<6);np=next;
   s32 noise=(l&1)?7:-8;v=(v*(128-mix)+noise*mix)>>7;
  }
  out[i]=v*amp*524288; /* Q31 : pic nominal -2^29, +7*2^26. */
 }
 s->phase=ph;s->phase2=ph2;s->noise_phase=np;s->lfsr=l;
}
#endif
