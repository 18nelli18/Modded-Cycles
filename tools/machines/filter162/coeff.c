/* Lowpass deux poles inspire du caractere Polivoks, pas une copie du circuit.
 * Coefficients bilineaires Q30, trois produits par sample dans le noyau EMAC.
 * Le feedback sature fournit le caractere rugueux a forte resonance.
 * Aucun flottant, aucun malloc ; cache prive par piste de l'IRQ audio.
 */
typedef unsigned int u32;typedef int s32;
struct coefficients {u32 f,q;s32 b,a1,a2;u32 mode;};
extern volatile u32 fc_type[6];extern const unsigned short fc_native_table[128];
static struct coefficients pf_cache[6];
/* Quotient Q30 par six divisions 32 bits ; reste < 2^24, donc <<5 sur 32 bits.
 * Calcul seulement quand cutoff ou resonance changent, jamais dans la boucle sample. */
static u32 fraction(u32 n,u32 d){
 u32 result=0;
 for(u32 i=0;i<6;i++){
  n<<=5;u32 part=n/d;n-=part*d;result=(result<<5)|part;
 }
 return result;
}
#ifndef PF_COEFF_NAME
#define PF_COEFF_NAME fc_coeff
#define PF_F_ADDRESS 0x401bbd60
#define PF_Q_ADDRESS 0x401bbd7c
#endif
struct coefficients *PF_COEFF_NAME(u32 lane){
 struct coefficients *p=&pf_cache[lane];
 u32 f=((volatile u32*)PF_F_ADDRESS)[lane],q=((volatile u32*)PF_Q_ADDRESS)[lane];
 if(f>4095)f=4095;
 #ifdef PF_WIZARD
 /* Feedback du ladder natif :0..15000 ; meme course de potard, nouveau Q. */
 if(q>15000)q=15000;
 q=(q*8191)/15000;
#else
 if(q>8191)q=8191;
#endif
 u32 original=f,mode=fc_type[lane];
 if(p->f==original&&p->q==q&&p->mode==mode)return p;
 u32 index=127;
 if(f){u32 lo=0,hi=127;while(lo<hi){u32 mid=(lo+hi)/2;if(fc_native_table[mid]<f)lo=mid+1;else hi=mid;}index=lo;}
 if(mode==3){if(index==64){p->b=0;return p;}u32 mapped=index<64?index*2:(index-65)*127/62;if(mapped>127)mapped=127;f=fc_native_table[mapped];}
 else if(!f)f=fc_native_table[127];
 if(f>4095)f=4095;
 u32 c=4096-f,ff=f*f,cc=c*c;
 u32 damping=362-((q*346)>>13); /* environ Q=0,707 a 16 ; pas de mode HP. */
 u32 feedback=(damping*(f*c))>>8;
 u32 denominator=ff+cc+feedback;
 s32 difference=(s32)ff-(s32)cc;
 p->b=(s32)fraction(mode==1||(mode==3&&index>64)?cc:mode==2?feedback:ff,denominator);
 p->a1=difference<0?-(s32)(fraction((u32)-difference,denominator)<<1):(s32)(fraction((u32)difference,denominator)<<1);
 p->a2=(s32)fraction(ff+cc-feedback,denominator);
 p->f=original;p->q=q;p->mode=mode;return p;
}
