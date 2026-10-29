/* Lowpass deux poles inspire du caractere Polivoks, pas une copie du circuit.
 * Coefficients bilineaires Q30, trois produits par sample dans le noyau EMAC.
 * Le feedback sature fournit le caractere rugueux a forte resonance.
 * Aucun flottant, aucun malloc ; cache prive par piste de l'IRQ audio.
 */
typedef unsigned int u32;typedef int s32;
struct coefficients {u32 f,q;s32 b,a1,a2;};
static struct coefficients pf_cache[6];
/* Quotient Q30 par six divisions 32 bits ; reste < 2^24, donc <<5 sur 32 bits.
 * Calcul seulement quand cutoff ou resonance changent, jamais dans la boucle sample. */
#include "filter-ratio.h"
#ifndef PF_COEFF_NAME
#define PF_COEFF_NAME fast_pf_coeff
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
 if(p->f==f&&p->q==q)return p;
 u32 c=4096-f,ff=f*f,cc=c*c;
 u32 damping=362-((q*346)>>13); /* environ Q=0,707 a 16 ; pas de mode HP. */
 u32 feedback=(damping*(f*c))>>8;
 u32 denominator=ff+cc+feedback;
 ratios(ff,feedback,denominator,0,&p->b,&p->a1,&p->a2);
 p->f=f;p->q=q;return p;
}

