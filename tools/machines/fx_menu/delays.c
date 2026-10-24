#include "fx.h"
#ifdef FX_NEW_DELAYS
/* Ring/DMA, Time et Feedback restent natifs. Le retour interpole est traite
 * avant sa copie wet et son feedback. Les anciens candidats gardent leur DSP.
 * v64 : Shimmer1 octave integrale alignee, Shimmer2 branche v62 conservee. */
extern void fx_delay_previous(s32*,const s32*,const s16*);
extern u32 fx_delay_state[];
#ifdef FX_DELAY_QUALITY
#define ND_RING 8192
static s32 nd_filter[2][6];
#include "delay_windows.h"
#else
#define ND_RING 2048
#endif
#ifdef FX_OCTAVE_POLISH
/* FIR demi-bande31 original : sinc(fc=1/4), fenetre Hamming, somme Q15=32768.
 * Symetrie :8paires +centre. Precision Q20 conservee, produits signes bornes. */
static const s16 ND_AA[8]={-56,96,-221,462,-878,1609,-3176,10342};
#ifdef FX_CPU_OPT
#define ND_AA_STRIDE 64
#else
#define ND_AA_STRIDE 32
#endif
static s32 nd_aa[2][ND_AA_STRIDE];static u32 nd_aa_w;
#ifdef FX_IDLE_OPT
/* EMAC fractionnaire : floor(x*(a<<16)/2^31) == floor(x*a/2^15).
 * Produit borne, meme arrondi que le C ; ACC0 vide apres chaque terme. */
static s32 signed_mul15(s32 x,s32 a){
 s32 y,scale=(s32)((u32)a<<16);
 __asm__ volatile("mac.l %1,%2,%%acc0\n\tmovclr.l %%acc0,%0":"=d"(y):"d"(x),"d"(scale):"cc");
 return y;
}
#elif defined(FX_CPU_OPT)
/* Decoupage16+16 : produit signe exact, partie basse bornee a 65535*16412.
 * La separation au mot simplifie les decalages sur ColdFire. */
static s32 signed_mul15(s32 x,s32 a){return ((x>>16)*a)*2+(((s32)((u32)x&65535u)*a)>>15);}
#else
static s32 signed_mul15(s32 x,s32 a){return (x>>15)*a+(((s32)((u32)x&32767u)*a)>>15);}
#endif
#ifdef FX_CPU_OPT
__attribute__((noinline))
#endif
static s32 antialias(s32 x,u32 c){
#ifdef FX_CPU_OPT
 /* Historique duplique : memes32echantillons, lectures contigues sans modulo. */
 s32 *p=nd_aa[c]+nd_aa_w+32;p[0]=p[-32]=x;
 s32 y=signed_mul15(p[-15],16412);
 for(u32 k=0;k<8;k++)y+=signed_mul15(p[-(s32)(2*k)]+p[-(s32)(30-2*k)],ND_AA[k]);
 return y;
#else
 nd_aa[c][nd_aa_w]=x;s32 y=signed_mul15(nd_aa[c][(nd_aa_w-15)&31],16412);
 for(u32 k=0;k<8;k++)y+=signed_mul15(nd_aa[c][(nd_aa_w-2*k)&31]+nd_aa[c][(nd_aa_w-(30-2*k))&31],ND_AA[k]);
 return y;
#endif
}
#endif
#ifdef FX_CLOUD
s32 nd_ring[2][ND_RING];
static s32 nd_low[2],nd_feed[64];
#else
static s32 nd_ring[2][ND_RING],nd_low[2],nd_feed[64];
#endif
static u32 nd_w,nd_filled,nd_phase,nd_active,nd_ready,nd_gain,nd_prior;
#ifdef FX_IDLE_OPT
/* 258blocs a entree Q20 nulle : FIR6+31 et ring8192 entierement vides.
 * Le diffuseur Shimmer2 reste execute, meme pendant cette veille du pitch. */
static u32 nd_zero_blocks;
/* Sortie au premier sample utile : cout minimal sur les blocs actifs. */
static u32 pitch_input_present(const s32 *io){
 for(u32 j=0;j<64;j++)if(io[j]>>11)return 1;
 return 0;
}
#endif
#if (defined(FX_SHIMMER_CLEAN)||defined(FX_OCTAVE_POLISH))&&!defined(FX_LEAN_FX)
/* Branche octave diffusee separee : le retour natif reste propre. */
static s32 nd_clean[64],nd_pitch[64],nd_ap[2][1024];
static u32 nd_ap_pos[2][2],nd_ap_fill[2][2];
static s32 mul15(s32 x,u32 a){return (x>>15)*(s32)a+(s32)(((u32)x&32767u)*a>>15);}
static s32 diffuse(s32 x,u32 c){
 for(u32 k=0;k<2;k++){
  u32 len=k?307+c*23:211+c*17,pos=nd_ap_pos[c][k],at=k*256+pos;
  s32 old=nd_ap_fill[c][k]<len?0:nd_ap[c][at],y=old-(x>>1);
  nd_ap[c][at]=x+(y>>1);x=y;
  if(nd_ap_fill[c][k]<len)nd_ap_fill[c][k]++;
  nd_ap_pos[c][k]=pos+1==len?0:pos+1;
 }
 return x;
}
#endif
#ifdef FX_OCTAVE_DELAY
/* Alignement original par erreur quadratique : une recherche courte repartie
 * sur les16blocs avant chaque raccord, jamais un pic de travail au reset.
 * Un meme decalage stereo conserve l image et aligne les deux tetes. */
static s32 nd_offset[2],nd_best_lag;
static u32 nd_best_error,nd_search_index,nd_search_head,nd_search_channel,nd_search_ready;
static s32 mono_at(u32 c,s32 back){return nd_ring[c][(nd_w-(u32)back)&8191]>>11;}
#ifdef FX_CPU_OPT
__attribute__((noinline,optimize("O2","no-unroll-loops")))
#endif
static void align_heads(void){
 u32 half=nd_phase&2047;
 if(half==1536&&nd_filled>4544){
  nd_search_index=0;nd_best_error=0xffffffffu;nd_best_lag=0;nd_search_ready=0;nd_search_head=nd_phase<2048?1:0;
  u32 energy[2]={0,0};s32 back=2271+nd_offset[1-nd_search_head];
  for(u32 c=0;c<2;c++)for(u32 k=0;k<32;k++){s32 x=mono_at(c,back-(s32)(8*k));energy[c]+=(u32)(x*x);}
  nd_search_channel=energy[1]>energy[0]?1:0;
 }
 if(half>=1536&&nd_filled>4544&&nd_search_index<97){
  s32 ref=2271+nd_offset[1-nd_search_head];
#ifdef FX_IDLE_OPT
  /* La reference est constante pendant les sept candidats de ce bloc. */
  s32 reference[32];
  for(u32 k=0;k<32;k++)reference[k]=mono_at(nd_search_channel,ref-(s32)(8*k));
#endif
  for(u32 n=0;n<7&&nd_search_index<97;n++,nd_search_index++){
   s32 lag=-192+4*(s32)nd_search_index;u32 error=(u32)(lag<0?-lag:lag);
   for(u32 k=0;k<32;k++){s32 d=
#ifdef FX_IDLE_OPT
   reference[k]
#else
   mono_at(nd_search_channel,ref-(s32)(8*k))
#endif
   -mono_at(nd_search_channel,4319+lag-(s32)(8*k));error+=(u32)(d*d);}
   if(error<nd_best_error){nd_best_error=error;nd_best_lag=lag;}
  }
  if(nd_search_index==97)nd_search_ready=1;
 }
 if(!half&&nd_search_ready){u32 head=nd_phase<2048?0:1;if(head==nd_search_head){nd_offset[head]=nd_best_lag;nd_search_ready=0;}}
}
#endif
static s32 bound(s32 x){return x>1048575?1048575:x< -1048576?-1048576:x;}
void fx_shift_reset(void){nd_w=nd_filled=nd_phase=0;nd_low[0]=nd_low[1]=0;
#ifdef FX_IDLE_OPT
 nd_zero_blocks=0;
#endif
#ifdef FX_CLOUD
 fx_cloud_reset();
#endif
#ifdef FX_OCTAVE_POLISH
 nd_aa_w=0;for(u32 c=0;c<2;c++)for(u32 k=0;k<ND_AA_STRIDE;k++)nd_aa[c][k]=0;
#endif
#ifdef FX_OCTAVE_DELAY
 nd_offset[0]=nd_offset[1]=0;nd_search_index=97;nd_search_ready=0;
#endif
#ifdef FX_DELAY_QUALITY
 for(u32 c=0;c<2;c++)for(u32 k=0;k<6;k++)nd_filter[c][k]=0;
#if (defined(FX_SHIMMER_CLEAN)||defined(FX_OCTAVE_POLISH))&&!defined(FX_LEAN_FX)
 for(u32 c=0;c<2;c++)for(u32 k=0;k<2;k++)nd_ap_pos[c][k]=nd_ap_fill[c][k]=0;
#endif
#endif
}
static s32 tap(u32 c,u32 back){return back>=nd_filled?0:nd_ring[c][(nd_w-back)&(ND_RING-1)];}
#ifdef FX_IDLE_OPT
/* Relais assembleur fx_shift : sauvegarde physique48bits ACC0 et MACSR. */
void fx_shift(s32*);
void fx_shift_core(s32 *restrict io){
#elif defined(FX_CPU_OPT)
/* Les tampons wet/pitch sont distincts des historiques prives. */
void fx_shift(s32 *restrict io){
#else
void fx_shift(s32 *io){
#endif
#ifdef FX_OCTAVE_DELAY
#if defined(FX_OCTAVE_POLISH)&&!defined(FX_LEAN_FX)
 if(nd_active!=7)
#endif
 align_heads();
#endif
#ifdef FX_IDLE_OPT
 u32 input_present=pitch_input_present(io);
 if(nd_zero_blocks>=258){
  if(!input_present){
   for(u32 j=0;j<64;j++)io[j]=0;
   nd_w=(nd_w+32)&(ND_RING-1);nd_phase=(nd_phase+32)&4095;
   /* AA avance de32 : index modulo32 identique ; filled est deja8192. */
   return;
  }
 }
 /* Publier avant la boucle : aucun registre de detection vivant au sample. */
 nd_zero_blocks=input_present?0:nd_zero_blocks<258?nd_zero_blocks+1:258;
#endif
 for(u32 i=0;i<32;i++){
  if(nd_filled<ND_RING)nd_filled++;
#ifdef FX_DELAY_QUALITY
  u32 p=nd_phase,q=(p+2048)&4095,da=4127-p,db=4127-q;
#ifdef FX_OCTAVE_DELAY
#if defined(FX_OCTAVE_POLISH)&&!defined(FX_LEAN_FX)
 if(nd_active!=7){
#endif
 da=(u32)((s32)da+192+nd_offset[0]);db=(u32)((s32)db+192+nd_offset[1]);
#if defined(FX_OCTAVE_POLISH)&&!defined(FX_LEAN_FX)
 }
#endif
#endif
  u32 wi=p>>4,a=ND_HANN[wi]+(((s32)ND_HANN[wi+1]-(s32)ND_HANN[wi])*(s32)(p&15)>>4);
#else
  u32 p=nd_phase,q=(p+512)&1023,da=1055-p,db=1055-q,a=p<512?p:1024-p;
#endif
  for(u32 c=0;c<2;c++){
   s32 x=io[2*i+c]>>11;
#ifdef FX_DELAY_QUALITY
   /* FIR binomial7 : attenuation avant octave, sans IIR/residu ni clipping.
    * Fenetres Hann85ms : raccords a pente nulle plutot que grains courts. */
   s32 filtered=x;
   for(u32 k=0;k<6;k++){s32 z=filtered+nd_filter[c][k];nd_filter[c][k]=filtered;filtered=z/2;}
#ifdef FX_OCTAVE_POLISH
#ifdef FX_LEAN_FX
   filtered=antialias(filtered,c);
#else
   if(nd_active!=7)filtered=antialias(filtered,c);
#endif
#endif
   nd_ring[c][nd_w]=filtered;
   s32 one=tap(c,da),two=tap(c,db),d=one-two;
   s32 pitched=two+(d>>15)*(s32)a+(s32)(((u32)d&32767u)*a>>15);
#else
   nd_low[c]+=(x-nd_low[c])>>1;nd_ring[c][nd_w]=nd_low[c];
   s32 one=tap(c,da),two=tap(c,db),pitched=two+(((one-two)*(s32)a)>>9);
#endif
#ifdef FX_OCTAVE_POLISH
   /* Shimmer1 100% octave, -2.5dB avant recirculation. Plage Feedback native.
    * Shimmer2 garde le niveau exact de fx_shift v62. */
#ifdef FX_LEAN_FX
   io[2*i+c]=bound(pitched-(pitched>>2))*2048;
#else
   io[2*i+c]=bound(nd_active==7?pitched:pitched-(pitched>>2))*2048;
#endif
#elif defined(FX_OCTAVE_DELAY)
   io[2*i+c]=bound(pitched-(pitched>>3))*2048;
#elif defined(FX_SHIMMER_CLEAN)
   io[2*i+c]=bound(pitched)*2048;
#elif defined(FX_DELAY_REPAIR)
   io[2*i+c]=bound((x>>2)+pitched-(pitched>>2))*2048;
#else
   io[2*i+c]=bound((x>>1)+(pitched>>1))*2048;
#endif
  }
#ifdef FX_OCTAVE_POLISH
  nd_aa_w=(nd_aa_w+1)&31;
#endif
  nd_w=(nd_w+1)&(ND_RING-1);
#ifdef FX_DELAY_QUALITY
  nd_phase=(p+1)&4095;
#else
  nd_phase=(p+1)&1023;
#endif
 }
 }
#ifdef FX_DELAY_REPAIR
/* Retour deja interpole/filtre, juste avant sa copie wet et son feedback.
 * Les deux lectures DMA natives sont ainsi traitees, quelle que soit Time. */
void fx_delay_return(s32*work){
#ifdef FX_CLOUD
 if(nd_active==8){fx_cloud(work);return;}
#endif
 if(nd_active==5)for(u32 i=0;i<32;i++){s32 x=work[2*i];work[2*i]=work[2*i+1];work[2*i+1]=x;}
 else if(nd_active==6
#if defined(FX_OCTAVE_POLISH)&&!defined(FX_LEAN_FX)
 ||nd_active==7
#endif
 ){
#ifdef FX_LEAN_FX
  fx_shift(work);
#elif defined(FX_SHIMMER_CLEAN)||defined(FX_OCTAVE_POLISH)
#ifdef FX_OCTAVE_POLISH
  if(nd_active==7){
#endif
  for(u32 j=0;j<64;j++){nd_clean[j]=work[j]>>11;nd_pitch[j]=(work[j]>>1);}
#ifdef FX_IDLE_OPT
  /* Shimmer2 n utilise aucun MAC : pas de sauvegarde EMAC superflue. */
  fx_shift_core(nd_pitch);
#else
  fx_shift(nd_pitch);
#endif
  for(u32 i=0;i<32;i++)for(u32 c=0;c<2;c++){u32 j=2*i+c;nd_pitch[j]=diffuse(nd_pitch[j]>>11,c);}
#ifdef FX_OCTAVE_POLISH
  }else fx_shift(work);
#endif
#else
  fx_shift(work);
#endif
 }

}
#endif
void fx_delay(s32*out,const s32*in,const s16*params,const s32*dl,const s32*dr){
 u32 wanted=FX_SPECIAL_DELAY(cr_mode)?cr_mode:0;
 if(!nd_ready){nd_ready=1;nd_gain=nd_prior=256;}
 if(wanted!=nd_active){nd_gain=nd_gain>=8?nd_gain-8:0;if(!nd_gain){nd_active=wanted;fx_shift_reset();}}
 else if(nd_gain<256)nd_gain+=8;
 if(!nd_active){
  /* Appel C direct du split : a4/a5 explicites, pas de dependance aux registres. */
  extern void fx_legacy_split(s32*,const s32*,const s16*,const s32*,const s32*);
  fx_legacy_split(out,in,params,dl,dr);
 }else{
  u32 addr=*(volatile u32*)0x8000b570;
  /* Memes banques SRAM que le DSP stock ; aucun pointeur DMA arbitraire. */
#ifdef FX_DELAY_QUALITY
  /* Le pointeur stock initialise dans SRAM vaut b590, pas a560 du vieux banc.
   * Refuser cette vraie banque rendait nd_feed muet sur la machine. */
  if(addr==0x8000b590){
#else
  if(addr>=0x8000a560&&addr<=0x8000b470&&!(addr&3)){
#endif
#ifdef FX_DELAY_REPAIR
   if(nd_active==5)for(u32 i=0;i<32;i++){nd_feed[2*i]=(in[2*i]>>1)+(in[2*i+1]>>1);nd_feed[2*i+1]=0;}
#else
   s32*work=(s32*)addr;
   if(nd_active==5){for(u32 i=0;i<32;i++){s32 x=work[2*i];work[2*i]=work[2*i+1];work[2*i+1]=x;nd_feed[2*i]=(in[2*i]>>1)+(in[2*i+1]>>1);nd_feed[2*i+1]=0;}}
   else fx_shift(work);
#endif
  }
  fx_delay_state[4]=0; /* aucune correction crusher d'un bloc precedent */
#if (defined(FX_SHIMMER_CLEAN)||defined(FX_OCTAVE_POLISH))&&!defined(FX_LEAN_FX)
  s32 prior_feedback=*(volatile s32*)0x8000b7d8;
#endif
  ((void(*)(s32*,const s32*,const s16*))0x40057488)(out,nd_active==5?nd_feed:in,params);
#if (defined(FX_SHIMMER_CLEAN)||defined(FX_OCTAVE_POLISH))&&!defined(FX_LEAN_FX)
  if(nd_active==
#ifdef FX_OCTAVE_POLISH
   7
#else
   6
#endif
   &&addr==0x8000b590){
   s32 target_feedback=*(volatile s32*)0x8000b7d8,step=(target_feedback-prior_feedback)>>5;
   s32*work=(s32*)addr;
   for(u32 i=0;i<32;i++){
    s32 coeff=prior_feedback+step*(s32)i;u32 a=coeff<0?(0u-(u32)coeff)>>16:0;
    for(u32 c=0;c<2;c++){
     u32 j=2*i+c;s32 delta=(3*(nd_pitch[j]-(nd_clean[j]>>1)))>>2;
     work[j]=bound((work[j]>>11)+mul15(delta,a))*2048;
     /* 75% echo propre +25% octave diffusee ; aucun grain integral sur wet. */
     s32 clean=out[j]>>11;out[j]=bound(clean-(clean>>2)+(nd_pitch[j]>>1))*2048;
    }
   }
  }
#endif
 }
 if(nd_gain!=256||nd_prior!=256)for(u32 i=0;i<32;i++){
  s32 g=(s32)nd_prior+(((s32)nd_gain-(s32)nd_prior)*(s32)(i+1)>>5);
  for(u32 c=0;c<2;c++)out[2*i+c]=((out[2*i+c]>>8)*g);
 }
 nd_prior=nd_gain;
}
#endif
