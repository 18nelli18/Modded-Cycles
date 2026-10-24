#include "fx.h"
/* Oscillateurs et filtres originaux, 48 kHz, etats stereo fixes ; aucun ring.
 * Audio Q20 et gains Q15, produit fractionne pour eviter un overflow 32 bits. */
static __attribute__((unused)) s32 mul(s32 x,s32 a){return (x>>15)*a+(((x&32767)*a)>>15);}
static __attribute__((unused)) s32 sat(s32 x){return x>1048575?1048575:x< -1048576?-1048576:x;}
static const s16 sinus[128]={0,1608,3212,4808,6393,7962,9512,11039,12539,14010,15446,16846,18204,19519,20787,22005,23170,24279,25329,26319,27245,28105,28898,29621,30273,30852,31356,31785,32137,32412,32609,32728,32767,32728,32609,32412,32137,31785,31356,30852,30273,29621,28898,28105,27245,26319,25329,24279,23170,22005,20787,19519,18204,16846,15446,14010,12539,11039,9512,7962,6393,4808,3212,1608,0,-1608,-3212,-4808,-6393,-7962,-9512,-11039,-12539,-14010,-15446,-16846,-18204,-19519,-20787,-22005,-23170,-24279,-25329,-26319,-27245,-28105,-28898,-29621,-30273,-30852,-31356,-31785,-32137,-32412,-32609,-32728,-32767,-32728,-32609,-32412,-32137,-31785,-31356,-30852,-30273,-29621,-28898,-28105,-27245,-26319,-25329,-24279,-23170,-22005,-20787,-19519,-18204,-16846,-15446,-14010,-12539,-11039,-9512,-7962,-6393,-4808,-3212,-1608};
static const u32 ring_step[128]={178957,189565,200801,212703,225311,238667,252813,267799,283673,300487,318298,337166,357151,378321,400746,424500,449662,476315,504549,534456,566136,599693,635240,672893,712779,755029,799783,847190,897407,950600,1006947,1066633,1129857,1196829,1267771,1342918,1422519,1506838,1596155,1690767,1790987,1897147,2009599,2128718,2254897,2388555,2530136,2680109,2838972,3007251,3185505,3374324,3574336,3786204,4010630,4248359,4500179,4766926,5049484,5348790,5665838,6001679,6357427,6734261,7133432,7556264,8004159,8478603,8981170,9513526,10077437,10674774,11307518,11977767,12687746,13439808,14236448,15080309,15974190,16921055,17924045,18986487,20111905,21304032,22566822,23904463,25321392,26822310,28412194,30096318,31880267,33769960,35771664,37892018,40138055,42517225,45037420,47706999,50534817,53530252,56703240,60064307,63624600,67395928,71390800,75622467,80104965,84853161,89882805,95210580,100854157,106832255,113164703,119872505,126977910,134504485,142477196,150922487,159868369,169344516,179382359,190015191,201278281,213208988,225846883,239233885,253414398,268435456};
static const u32 phase_step[128]={3579,3732,3891,4056,4229,4409,4597,4793,4997,5210,5432,5663,5905,6156,6419,6692,6977,7274,7584,7907,8244,8595,8962,9343,9741,10156,10589,11040,11510,12001,12512,13045,13601,14180,14784,15414,16071,16756,17469,18214,18989,19798,20642,21521,22438,23394,24391,25430,26513,27643,28820,30048,31328,32663,34054,35505,37017,38594,40239,41953,43740,45603,47546,49572,51684,53885,56181,58574,61070,63671,66384,69212,72161,75235,78440,81781,85265,88898,92685,96634,100750,105042,109517,114183,119047,124119,129407,134920,140667,146660,152908,159422,166214,173295,180677,188374,196399,204766,213490,222584,232067,241953,252261,263008,274212,285894,298073,310772,324011,337815,352206,367210,382854,399164,416169,433899,452384,471656,491749,512698,534540,557312,581055,605808,631617,658524,686579,715828};
static const s16 allpass[128]={-32427,-32415,-32403,-32391,-32378,-32365,-32351,-32337,-32323,-32308,-32292,-32276,-32259,-32242,-32224,-32206,-32187,-32168,-32147,-32126,-32105,-32082,-32059,-32036,-32011,-31985,-31959,-31932,-31904,-31875,-31845,-31814,-31782,-31749,-31715,-31680,-31643,-31606,-31567,-31527,-31485,-31443,-31398,-31353,-31306,-31257,-31207,-31155,-31102,-31046,-30989,-30931,-30870,-30807,-30743,-30676,-30607,-30536,-30463,-30387,-30309,-30228,-30145,-30060,-29971,-29880,-29786,-29690,-29590,-29487,-29381,-29271,-29159,-29043,-28923,-28800,-28673,-28542,-28408,-28269,-28126,-27979,-27828,-27672,-27512,-27347,-27178,-27003,-26824,-26639,-26449,-26254,-26053,-25847,-25635,-25418,-25194,-24964,-24729,-24486,-24238,-23983,-23721,-23452,-23176,-22893,-22603,-22306,-22001,-21688,-21368,-21040,-20704,-20359,-20006,-19645,-19275,-18896,-18509,-18112,-17706,-17290,-16865,-16431,-15986,-15531,-15065,-14589};
static u32 ring_phase,phase_phase;
static s32 phase_z[2][2],phase_last[2];
#ifdef FX_GATED96
static u32 phase_silent;
#endif
static s32 sine(u32 p){u32 i=p>>25,f=(p>>17)&255;return sinus[i]+(((s32)sinus[(i+1)&127]-sinus[i])*(s32)f>>8);}
void fx_extra_reset(u32 delay){if(!delay)ring_phase=0;else{phase_phase=0;for(u32 c=0;c<2;c++){phase_last[c]=0;for(u32 k=0;k<2;k++)phase_z[c][k]=0;}}}
void fx_ring(s32*out,const s32*in){
 u32 f=fx_ring_freq&127,d=fx_ring_depth&127,step=ring_step[f];
 for(u32 i=0;i<32;i++){s32 g=sine(ring_phase)*(s32)d/127;ring_phase+=step;for(u32 c=0;c<2;c++)out[2*i+c]=
#ifdef FX_INPUT_FIX
 ((in[2*i+c]>>16)*g)*2;
#else
 mul(in[2*i+c]>>11,g)*2048;
#endif
}
}
#ifdef FX_INPUT_FIX
static s32 psat(s32 x){return x>65535?65535:x< -65535?-65535:x;}
static s32 pmul(s32 x,s32 a){
#ifdef FX_GATED96
return (x*a)/32768;
#else
return (x*a)>>15;
#endif
}
#else
#define psat sat
#define pmul mul
#endif
void fx_phaser(s32*out,const s32*in){
 u32 rate=fx_phase_rate&127,depth=fx_phase_depth&127,feedback=fx_phase_feedback&127;
 s32 coef[2];for(u32 c=0;c<2;c++){s32 lfo=sine(phase_phase+c*0x20000000u);u32 index=(u32)(64+((lfo*(s32)depth)>>16));if(index>127)index=127;coef[c]=allpass[index];}
 phase_phase+=phase_step[rate]*32u;
#ifdef FX_GATED96
 u32 silent=1;for(u32 i=0;i<64;i++)if(in[i]){silent=0;break;}
 if(silent){if(phase_silent<128)phase_silent++;}else phase_silent=0;
 if(phase_silent==128){for(u32 c=0;c<2;c++){phase_last[c]=0;for(u32 k=0;k<2;k++)phase_z[c][k]=0;}for(u32 i=0;i<64;i++)out[i]=0;return;}
#endif
 for(u32 i=0;i<32;i++)for(u32 c=0;c<2;c++){
  s32 x=psat((in[2*i+c]>>
#ifdef FX_INPUT_FIX
16
#else
12
#endif
)+pmul(phase_last[c],(s32)feedback*160));
  for(u32 k=0;k<2;k++){s32 y=psat(phase_z[c][k]+pmul(x,coef[c]));phase_z[c][k]=psat(x-pmul(y,coef[c]));x=y;}
  phase_last[c]=x;out[2*i+c]=psat(x)*
#ifdef FX_INPUT_FIX
32768
#else
2048
#endif
;
 }
}

#ifdef FX_GATED
/* Meme reseau ROOM, decay dense fixe ; fermeture douce8ms, aucun ring ajoute.
 * Le gate est relance par le signal envoye, pas par les six voix separees. */
u32 fx_gate_time=64;
static u32 gate_remaining,gate_gain;
#ifdef FX_GATE_PREDELAY
/* Retard stereo Q31, sans feedback. Remplissage paresseux : aucune lecture
 * SDRAM avant ecriture et aucune remise a zero de64Ko en interruption. */
u32 fx_gate_predelay;
#ifdef FX_REVERB101
#define GATE_RING 32768
u32 fx_gate_delay_ms(u32 v){v&=127;return v<=64?v:64+(v-64)*8;}
#else
#define GATE_RING 8192
#endif
static s32 gate_predelay_ring[GATE_RING][2] __attribute__((section(".gatebuffer")));
static s32 gate_delayed[64];
static u32 gate_write,gate_filled,gate_last_delay;
const s32 *fx_gate_wait(const s32 *in){
 u32 delay=
#ifdef FX_REVERB101
fx_gate_delay_ms(fx_gate_predelay)*48;
#else
(fx_gate_predelay&127)*48;
#endif
 if(delay!=gate_last_delay||!delay){gate_write=gate_filled=0;gate_last_delay=delay;}
 if(!delay)return in;
 for(u32 i=0;i<32;i++){
  u32 read=(gate_write-delay)&(GATE_RING-1);
  for(u32 c=0;c<2;c++){
   gate_delayed[2*i+c]=gate_filled>=delay?gate_predelay_ring[read][c]:0;
   gate_predelay_ring[gate_write][c]=in[2*i+c];
  }
  gate_write=(gate_write+1)&(GATE_RING-1);if(gate_filled<GATE_RING)gate_filled++;
 }
 return gate_delayed;
}
#endif
void fx_gate_reset(void){gate_remaining=gate_gain=0;
#ifdef FX_GATE_PREDELAY
 gate_write=gate_filled=gate_last_delay=0;
#endif
}
void fx_gated(s32*out,const s32*in,const s16*params){
#ifdef FX_GATE_PREDELAY
 in=fx_gate_wait(in);
#endif
 u32 peak=0;for(u32 i=0;i<64;i++){s32 x=in[i];u32 a=(x<0?0u-(u32)x:(u32)x)>>16;if(a>peak)peak=a;}
 if(peak>16){u32 v=fx_gate_time&127;gate_remaining=60+v*16;
#ifdef FX_REVERB101
if(v>64)gate_remaining+=(v-64)*(v-64)*2;
#endif
}
 else if(gate_remaining)gate_remaining--;
 u32 old=gate_gain;if(gate_remaining)gate_gain=32768;else gate_gain=gate_gain>2731?gate_gain-2731:0;
 if(!gate_gain&&!old){for(u32 i=0;i<64;i++)out[i]=0;return;}
 s16 p[2]={112*256,params[1]};
#ifdef FX_REVERB101
if(fx_gate_time>64)p[0]=(112+(fx_gate_time-64)*15/63)*256;
#endif
 fx_room(out,in,p);
 if(gate_gain!=32768||old!=32768){s32 d=(s32)gate_gain-(s32)old;
  for(u32 i=0;i<32;i++){s32 g=(s32)old+((d*(s32)(i+1))>>5);for(u32 c=0;c<2;c++){u32 j=2*i+c;out[j]=mul(out[j]>>11,g)*2048;}}
 }
 if(!gate_gain&&old)fx_room_reset();
}
void fx_gate_settings(void){
 static u32 once;u32 h[4]={0};u8 b[10]={0},extra;
 if(!once){once=1;if(!N(0x4007bc5e)("/Gated.cfg","r",h)){
  u32 ok=N(0x4007baaa)(b,10,h)==10&&!N(0x4007baaa)(&extra,1,h);if(N(0x4007bc1c)(h))ok=0;
  if(ok&&!fx_dirty&&b[0]==71&&b[1]==65&&b[2]==48&&b[3]==49&&b[4]<128&&
#ifdef FX_GATE_PREDELAY
b[5]<128&&b[6]==(u8)~b[4]&&b[7]==(u8)~b[5]
#else
b[5]==0&&b[6]==(u8)~b[4]&&b[7]==255
#endif
&&b[8]==165&&b[9]==90){fx_gate_time=b[4];
#ifdef FX_GATE_PREDELAY
fx_gate_predelay=b[5];
#endif
}
 }}
 if(fx_dirty&&fx_input_quiet()&&!N(0x4007faf4)(2)&&!fx_menu_open){
  u8 out[10]={71,65,48,49,fx_gate_time,
#ifdef FX_GATE_PREDELAY
fx_gate_predelay,(u8)~fx_gate_time,(u8)~fx_gate_predelay,
#else
0,(u8)~fx_gate_time,255,
#endif
165,90};
  if(!N(0x4007bc5e)("/Gated.cfg","w",h)){if(!N(0x4007bb76)(h,0,10))N(0x4007bb0a)(out,10,h);N(0x4007e2f6)(h);N(0x4007bc1c)(h);}
 }
}
#endif
