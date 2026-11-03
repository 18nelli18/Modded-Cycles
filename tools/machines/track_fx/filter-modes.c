/* Lowpass deux poles inspire du caractere Polivoks, pas une copie du circuit.
 * Coefficients bilineaires Q30, trois produits par sample dans le noyau EMAC.
 * Le feedback sature fournit le caractere rugueux a forte resonance.
 * Aucun flottant, aucun malloc ; cache prive par piste de l'IRQ audio.
 */
typedef unsigned int u32;typedef int s32;
struct coefficients {u32 f,q;s32 b,a1,a2;u32 mode;};
extern volatile u32 fc_type[6];extern const unsigned short fc_native_table[128];
static struct coefficients pf_cache[6];
#ifdef PF_FULL_CACHE
static struct coefficients *pf_last;
#endif
/* Quotient Q30 par six divisions 32 bits ; reste < 2^24, donc <<5 sur 32 bits.
 * Calcul seulement quand cutoff ou resonance changent, jamais dans la boucle sample. */
#include "filter-ratio.h"
#ifndef PF_COEFF_NAME
#define PF_COEFF_NAME fast_fc_coeff
#define PF_F_ADDRESS 0x401bbd60
#define PF_Q_ADDRESS 0x401bbd7c
#endif
struct coefficients *PF_COEFF_NAME(u32 lane){
 struct coefficients *p=&pf_cache[lane];
 u32 f=((volatile u32*)PF_F_ADDRESS)[lane],q=((volatile u32*)PF_Q_ADDRESS)[lane];
 if(f>4095)f=4095;
 /* Le convertisseur natif publie0..15000 pour toutes les pistes.
  * Normaliser avant les coefficients : ne pas ecreter la moitie haute du potard. */
 if(q>15000)q=15000;
 u32 original_q=q;
 u32 original=f,mode=fc_type[lane];
 if(p->f==original&&p->q==original_q&&p->mode==mode)return p;
#ifdef PF_FULL_CACHE
 if(pf_last&&pf_last->f==original&&pf_last->q==original_q&&pf_last->mode==mode){
  p->b=pf_last->b;p->a1=pf_last->a1;p->a2=pf_last->a2;p->f=original;p->q=original_q;p->mode=mode;return p;
 }
#endif
#ifdef PF_ZERO_LUT
 if(q)q=(q*8191)/15000;
#else
 q=(q*8191)/15000;
#endif
 u32 index=127;
 if(mode==3&&f){u32 lo=0,hi=127;while(lo<hi){u32 mid=(lo+hi)/2;if(fc_native_table[mid]<f)lo=mid+1;else hi=mid;}index=lo;}
 if(mode==3){if(index==64){
#ifdef PF_FULL_CACHE
 /* Le centre ne met pas a jour la cle historique : invalider ce donneur. */
 if(pf_last==p)pf_last=0;
#endif
 p->b=0;return p;}u32 mapped=index<64?index*2:(index-65)*127/62;if(mapped>127)mapped=127;f=fc_native_table[mapped];}
 else if(!f)f=fc_native_table[127];
 if(f>4095)f=4095;
 u32 c=4096-f,ff=f*f,cc=c*c;
 u32 damping=362-((q*346)>>13); /* environ Q=0,707 a 16 ; pas de mode HP. */
 u32 feedback=(damping*(f*c))>>8;
 u32 denominator=ff+cc+feedback;
 ratios(ff,feedback,denominator,(mode==1||(mode==3&&index>64)?1:mode==2?2:0),&p->b,&p->a1,&p->a2);
 p->f=original;p->q=original_q;p->mode=mode;
#ifdef PF_FULL_CACHE
 pf_last=p;
#endif
 return p;
}

