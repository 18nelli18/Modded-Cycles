#include "fx.h"

/* Masque derive des gains courants ET cibles : conserver les rampes de sortie.
 * Proprietaire unique IRQ audio ; aucun setter UI ni adresse native supposee. */
u32 fx_aux_active_mask;
extern volatile u32 fx_side,fx_side_on;
extern u8 ch_state[];
struct vinyl_state {s32 ring[2][2048];u32 w,filled,phase,seed; s32 delay,last[2];};
static struct vinyl_state vi;
static s32 gain_aux[2][6],left[192],right[192],aux[64],effect[64],correction[64];
static u32 active,ready,gain=256,prior_gain=256,correction_on;
#ifdef FX_DUST
/* Couche independante du signal, deux graines et filtres non correles.
 * Q20 audio / Q15 gain. Aucun bruit si tous les sends sont a zero. */
static u32 dust_seed[2]={0x5a17c9e3u,0xc41d8b27u},dust_target[2],dust_gain[2];
static s32 dust_pop[2],dust_low[2],dust_slow[2];
static u32 dust_rand(u32 c){u32 x=dust_seed[c];x^=x<<13;x^=x>>17;x^=x<<5;return dust_seed[c]=x;}
static s32 dust_sample(u32 c,u32 amount){
 if(!amount){dust_pop[c]=dust_low[c]=dust_slow[c]=0;return 0;}
 u32 r=dust_rand(c),r2=dust_rand(c);s32 pulse=0;
 /* Grain fin de poussiere : environ 3..282 petits evenements/seconde. */
 if((r&65535u)<4+3*amount){s32 a=(s32)((8192u+((r>>16)&65535u))*amount>>7);pulse=(r&0x10000u)?a:-a;}
 /* Pop plus rare, petite rafale bruitee amortie plutot qu'un grave thump. */
 if((r2&1048575u)<1+(amount>>2))dust_pop[c]=(s32)((65536u+((r>>16)&65535u))*amount>>7);
 if(dust_pop[c]){s32 burst=(s32)(r2>>20)-2048;pulse+=(burst*(dust_pop[c]>>3))>>8;dust_pop[c]-=dust_pop[c]>>4;if(dust_pop[c]<4)dust_pop[c]=0;}
 /* Bande poussiere audible : deux poles differents, sans grave ni DC.
  * Le gain fait partie du DSP livre ; aucun gain cache dans le preview. */
 dust_low[c]+=(pulse-dust_low[c])>>1;dust_slow[c]+=(pulse-dust_slow[c])>>3;
 if(!pulse&&dust_low[c]>-2&&dust_low[c]<2)dust_low[c]=0;
 if(!pulse&&dust_slow[c]>-8&&dust_slow[c]<8)dust_slow[c]=0;
 return (dust_low[c]-dust_slow[c])*12;
}
#endif
static s32 sat20(s32 x){return x>1048575?1048575:x< -1048576?-1048576:x;}
static s32 q31(s32 x){return sat20(x)*2048;}
static s32 scaled(s32 x,u32 a){return (x>>15)*(s32)a+(s32)(((u32)x&32767u)*a>>15);}
static s32 wave(u32 p){u32 q=p>>16;return q<32768?(s32)q*2-32768:98303-(s32)q*2;}
void fx_vinyl_reset(void){
#ifdef FX_REVERB101
 fx_hall_reset();
#endif
#ifdef FX_GATED
 fx_gate_reset();
#endif
#ifdef FX_EXTRA
 fx_extra_reset(0);
#endif
#ifdef FX_CHEAP
 fx_room_reset();
#endif
#ifdef FX_PS1
 fx_ps1_reset();
#endif
#ifdef FX_DUST
 for(u32 c=0;c<2;c++){dust_pop[c]=dust_low[c]=dust_slow[c]=0;dust_gain[c]=0;}
#endif
vi.w=vi.filled=vi.phase=0;vi.delay=0;vi.last[0]=vi.last[1]=0;if(!vi.seed)vi.seed=0x76a921u;}
void fx_vinyl(s32*out,const s32*in){
 u32 crack=fx_crackle<128?fx_crackle:127,amount=fx_warble<128?fx_warble:127,speed=fx_wspeed<128?fx_wspeed:127;
 s32 target=(s32)(amount*192u)*128+((wave(vi.phase)*(s32)amount)>>1),step=(target-vi.delay)>>5;
 vi.phase+=229065u+speed*180380u;
#ifdef FX_DUST
 s32 dust_delta[2];for(u32 c=0;c<2;c++)dust_delta[c]=(s32)dust_target[c]-(s32)dust_gain[c];
#endif
 for(u32 i=0;i<32;i++){
  if(vi.filled<2048)vi.filled++;
  u32 rnd=vi.seed; rnd^=rnd<<13;rnd^=rnd>>17;rnd^=rnd<<5;vi.seed=rnd;
  for(u32 c=0;c<2;c++){
   s32 x=in[2*i+c]>>11;vi.ring[c][vi.w]=x;s32 wet=x;
   if(amount){u32 d=vi.delay<0?0:(u32)vi.delay,back=d>>16,f=(d>>8)&255,at=(vi.w-back)&2047;
    s32 a=back>=vi.filled?0:vi.ring[c][at],b=back+1>=vi.filled?0:vi.ring[c][(at-1)&2047];wet=a+(((b-a)*(s32)f)>>8);
   }
#ifdef FX_DUST
   u32 dg=(u32)((s32)dust_gain[c]+((dust_delta[c]*(s32)(i+1))>>5));
   s32 noise=dust_sample(c,crack);noise=scaled(noise,dg);
   out[2*i+c]=q31(wet+noise);
#else
   /* Poussiere bipolaire, liee a l'energie du signal ; aucune fuite a send0. */
   u32 mag=x<0?(u32)-x:(u32)x;u32 threshold=crack*12u;
   s32 noise=((rnd&65535u)<threshold)?(s32)((mag*(crack+1))>>9):0;if(rnd&0x10000u)noise=-noise;
   vi.last[c]-=vi.last[c]>>2;if(vi.last[c]>-4&&vi.last[c]<4)vi.last[c]=0;vi.last[c]=sat20(vi.last[c]+noise);
   out[2*i+c]=q31(wet+vi.last[c]);
#endif
  }
  vi.delay+=step;vi.w=(vi.w+1)&2047;
 }
#ifdef FX_DUST
 for(u32 c=0;c<2;c++)dust_gain[c]=dust_target[c];
#endif
}
/* Mixeur EMAC natif. Le coefficient maximal normalise le dry complet. */
static void sum_bus(s32*out,const s32*src,s32*g,const s32*target){s32 d[6];for(u32 t=0;t<6;t++)d[t]=(s32)((u32)target[t]-(u32)g[t])>>5;
 ((void(*)(s32*,const s32*,s32*,const s32*))0x40056716)(out,src,g,d);for(u32 t=0;t<6;t++)g[t]=target[t];}
#ifdef FX_VOICE_OPT
static void aux_pair(s32*out,const s32*ls,const s32*rs,s32 target[2][6]){
 u32 same=ls==rs;
 for(u32 t=0;t<6&&same;t++)if(gain_aux[0][t]!=gain_aux[1][t]||target[0][t]!=target[1][t])same=0;
 sum_bus(out,ls,gain_aux[0],target[0]);
 if(same){for(u32 i=0;i<32;i++)out[2*i+1]=out[2*i];for(u32 t=0;t<6;t++)gain_aux[1][t]=gain_aux[0][t];}
 else sum_bus(out+1,rs,gain_aux[1],target[1]);
}
#endif
static u32 make_aux(const u16*mix,const s32*dl,const s32*dr,u32 mode){
 s32 target[2][6];u32 nonzero=0,track_mask=0;const s32*mid=(const s32*)0x80001858,*side=(const s32*)fx_side;const u32*on=(const u32*)fx_side_on;
#ifdef FX_DUST
 dust_target[0]=dust_target[1]=0;
#endif
 for(u32 t=0;t<6;t++){
  u32 v=mode==3?(*(const u16*)((const u8*)mix+56+66*t)>>8):mode==4?fx_aux_vi[t]:fx_aux_ch[t];if(v>127)v=127;u32 a=v*v*32768u/16129u;
  for(u32 c=0;c<2;c++){
   s32 dry=((const s32*)(c?0x40a78be8:0x40a78c08))[t];dry=(s32)((u32)dry+((u32)(c?dr:dl)[t]<<5));
   if(dry>0||(*(volatile u8*)0x404e9b53&(1u<<t)))dry=0;
   target[c][t]=scaled(dry,a);if(target[c][t]||gain_aux[c][t]){nonzero=1;track_mask|=1u<<t;}
#ifdef FX_DUST
   if(mode==3||mode==4){u32 level=mix[t]>>8;if(level>127)level=127;u32 p=*(const u16*)((const u8*)mix+58+66*t)>>8;if(p>127)p=127;
    u32 weight=dry?((a*level*level)/16129u):0;weight=weight*(c?p:127-p)/127u;
    /* Une seule surface de disque : max, pas six couches empilees. */
    if(weight>dust_target[c])dust_target[c]=weight;
   }
#endif
  }
#ifndef FX_VOICE_OPT
  for(u32 i=0;i<32;i++){u32 j=32*t+i;s32 m=mid[j],s=side&&on&&on[t]?side[j]:0;left[j]=s?q31((m>>11)+(s>>11)):m;right[j]=s?q31((m>>11)-(s>>11)):m;}
#endif
 }
#ifdef FX_VOICE_OPT
 if(nonzero){
  /* Sources mono : mixer directement le bus natif, sans384copies prealables.
   * Source side stereo : reconstruire exactement les deux bus historiques. */
  u32 stereo=0;if(side&&on)for(u32 t=0;t<6;t++)if(track_mask&(1u<<t))stereo|=on[t];
  if(stereo){
   for(u32 t=0;t<6;t++)if(track_mask&(1u<<t))for(u32 i=0;i<32;i++){u32 j=32*t+i;s32 m=mid[j],s=on[t]?side[j]:0;left[j]=s?q31((m>>11)+(s>>11)):m;right[j]=s?q31((m>>11)-(s>>11)):m;}
   aux_pair(aux,left,right,target);
  }else aux_pair(aux,mid,mid,target);
 }
#else
 if(nonzero){sum_bus(aux,left,gain_aux[0],target[0]);sum_bus(aux+1,right,gain_aux[1],target[1]);}
#endif
 else for(u32 i=0;i<64;i++)aux[i]=0;
 fx_aux_active_mask=track_mask;
 return nonzero;
}
void fx_reverb(s32*out,const s32*in,const s16*params,const u16*mix,const s32*dl,const s32*dr){
 u32 wanted=
#ifdef FX_LEAN_FX
fx_clean_rev(ch_mode);
#else
ch_mode<FX_REV_COUNT?ch_mode:0;
#endif
 if(!ready){ready=1;active=0;gain=prior_gain=256;}
 if(wanted!=active){gain=gain>=8?gain-8:0;if(!gain){active=wanted;fx_vinyl_reset();for(u32 i=2048;i<2062;i++)((u32*)ch_state)[i]=0;for(u32 c=0;c<2;c++)for(u32 t=0;t<6;t++)gain_aux[c][t]=0;}}
 else if(gain<256)gain+=8;
 correction_on=0;
 if(active==0)ch_native(out,in,params);
#ifdef FX_PS1
 else if(active==7)fx_ps1(out,in,params);
#ifdef FX_CHEAP
 else if(active==8)fx_room(out,in,params);
#ifdef FX_REVERB101
 else if(active==11)fx_hall(out,in,params);
#endif
#endif
#endif
#ifdef FX_EXTRA
 else if(active==9)fx_ring(out,in);
#ifdef FX_GATED
 else if(active==10)fx_gated(out,in,params);
#endif
#endif
 else if(active==1||active==2){s16 p[2]={(s16)(fx_speed*256),(s16)(fx_depth*256)};ch_chorus(out,in,p,active,256);}
#ifdef FX_LEAN_FX
 else{
  u32 present=make_aux(mix,dl,dr,3);
  for(u32 i=0;i<64;i++)out[i]=0;
  if(present){fx_vinyl(effect,aux);correction_on=1;for(u32 i=0;i<32;i++){
   s32 g=(s32)prior_gain+(((s32)gain-(s32)prior_gain)*(s32)(i+1)>>5);
   for(u32 c=0;c<2;c++){u32 j=2*i+c;s32 d=(effect[j]>>11)-(aux[j]>>11);correction[j]=((d>>8)*g)+(((d&255)*g)>>8);}
  }}else fx_vinyl_reset();
 }
#else
 else{
  u32 present=make_aux(mix,dl,dr,active);
  if(active==3)for(u32 i=0;i<64;i++)out[i]=0;else ch_native(out,in,params);
  if(active==3||active==4){
   if(present){fx_vinyl(effect,aux);correction_on=1;for(u32 i=0;i<32;i++){
    s32 g=(s32)prior_gain+(((s32)gain-(s32)prior_gain)*(s32)(i+1)>>5);
    for(u32 c=0;c<2;c++){u32 j=2*i+c;s32 d=(effect[j]>>11)-(aux[j]>>11);correction[j]=((d>>8)*g)+(((d&255)*g)>>8);}
   }}else fx_vinyl_reset();
  }else if(present){s16 p[2]={(s16)(fx_speed*256),(s16)(fx_depth*256)};ch_chorus(effect,aux,p,active==6?2:1,256);for(u32 i=0;i<64;i++)out[i]=q31((out[i]>>11)+(effect[i]>>11));}
 }
#endif
#ifdef FX_REVERB101
 /* Gain wet seul, +6dB dans la zone utile. Genou continu au-dessus de-6dB
  * de sortie pour garder de la marge aux transitoires sans wrap/clip dur. */
 if(active==7||active==8
#ifdef FX_POLISH
 ||active==11
#endif
)for(u32 i=0;i<64;i++){
  s32 x=out[i]>>11;u32 a=x<0?0u-(u32)x:(u32)x;
  a=a<262144?a*2:524288+((a-262144)>>1);out[i]=q31(x<0?-(s32)a:(s32)a);
 }
#endif
 if(gain!=256||prior_gain!=256)for(u32 i=0;i<32;i++){s32 g=(s32)prior_gain+(((s32)gain-(s32)prior_gain)*(s32)(i+1)>>5);for(u32 c=0;c<2;c++)out[2*i+c]=q31(((out[2*i+c]>>11)*g)>>8);}
#ifdef FX_SIDECHAIN_RETURNS
 /* Vinyl est une correction wet/dry ajoutee au postmix ; sa composante
  * seule est attenuee. Les autres types ont un retour stereo classique. */
 N(0x46835ff0)(correction_on?correction:out,0);
#endif
 prior_gain=gain;
}
void fx_post(s32*mix){cr_post(mix);if(correction_on){for(u32 i=0;i<64;i++)mix[i]=q31((mix[i]>>11)+correction[i]);correction_on=0;}}
void fx_copy(void *p,const void*q,u32 n){u8*d=p;const u8*s=q;while(n--)*d++=*s++;}
void *memcpy(void*p,const void*q,u32 n){fx_copy(p,q,n);return p;}
void *memset(void*p,int v,u32 n){u8*d=p;while(n--)*d++=v;return p;}
