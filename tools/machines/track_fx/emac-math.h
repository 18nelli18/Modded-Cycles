/* Arithmetique du prototype dsp-emac-experiment ; integration conservative.
 * ACC3 et MACSR preserves a chaque produit. Aucun changement de routage. */
#ifndef FX_EMAC_ACC3_RESERVED
#define FX_EMAC_ACC3_RESERVED 0
#endif
#define INLINE static __inline__ __attribute__((always_inline))
INLINE u32 mask(u32 condition){return 0u-condition;}
INLINE u32 select_u(register u32 bits,register u32 yes,register u32 no){
 __asm__ volatile("eor.l %2,%0\n\tand.l %1,%0\n\teor.l %2,%0"
                  : "+&d"(yes):"d"(bits),"d"(no):"cc");
 return yes;
}
#ifdef FX_FAST_WRAPPER
INLINE s32 sat20(register s32 x){return x>1048575?1048575:x< -1048576?-1048576:x;}
#else
INLINE s32 sat20(register s32 x){
 register u32 hi,lo,bits;
 /* Masques explicites : GCC peut transformer du C bitwise en branches. */
 __asm__ volatile(
  "moveq #0,%1\n\t"
  "moveq #0,%2\n\t"
  "cmpi.l #1048575,%0\n\t"
  "sgt %1\n\t"
  "extb.l %1\n\t"
  "cmpi.l #-1048576,%0\n\t"
  "slt %2\n\t"
  "extb.l %2\n\t"
  "move.l %1,%3\n\t"
  "or.l %2,%3\n\t"
  "not.l %3\n\t"
  "and.l %3,%0\n\t"
  "andi.l #1048575,%1\n\t"
  "andi.l #-1048576,%2\n\t"
  "or.l %1,%0\n\t"
  "or.l %2,%0"
  : "+&d"(x),"=&d"(hi),"=&d"(lo),"=&d"(bits)::"cc");
 return x;
}
#endif
INLINE s32 q31(register s32 x){return (s32)((u32)sat20(x)<<11);}
/* floor(x*a/32768), a dans0..32768. Le cas unity ne devient jamais -1Q31.
 * La MAC fractionnaire ne demande aucun produit64bits logiciel.
 * Les sorties early-clobber empechent les entrees de partager leurs registres.
 */
INLINE s32 scaled(register s32 x,register u32 a){
 register u32 unity=mask(a==32768u),coefficient=(a-(a>>15))<<16;
 register s32 result;
#if FX_EMAC_ACC3_RESERVED
 __asm__ volatile(
  "move.l #0,%%acc3\n\t"
  "mac.l %1,%2,%%acc3\n\t"
  "movclr.l %%acc3,%0"
  : "=&d"(result):"d"(x),"d"(coefficient):"cc");
#else
 register u32 saved_status,saved_acc,saved_ext;
 __asm__ volatile(
  "move.l %%macsr,%1\n\t"
  "move.l #0,%%macsr\n\t"
  "move.l %%acc3,%2\n\t"
  "move.l %%accext23,%3\n\t"
  "move.l #0xa0,%%macsr\n\t"
  "move.l #0,%%acc3\n\t"
  "mac.l %4,%5,%%acc3\n\t"
  "movclr.l %%acc3,%0\n\t"
  "move.l #0,%%macsr\n\t"
  "move.l %2,%%acc3\n\t"
  "move.l %3,%%accext23\n\t"
  "move.l %1,%%macsr"
  : "=&d"(result),"=&d"(saved_status),"=&d"(saved_acc),"=&d"(saved_ext)
  : "d"(x),"d"(coefficient):"cc");
#endif
 return (s32)select_u(unity,(u32)x,(u32)result);
}

#ifdef FX_REVERB101
#ifdef FX_FAST_WRAPPER
static void wet_gain(register s32*p){for(register u32 n=64;n;--n,++p){register s32 x=*p>>11;register u32 a=x<0?0u-(u32)x:(u32)x;a=a<262144?a*2:524288+((a-262144)>>1);*p=q31(x<0?-(s32)a:(s32)a);}}
#else
static void wet_gain(register s32 *p){
 for(register u32 n=64;n;--n,++p){
  register s32 x=*p>>11;
  register u32 sign=mask(x<0),a=(((u32)x)^sign)-sign;
  register u32 knee=mask(a<262144u);
  a=select_u(knee,a<<1,524288u+((a-262144u)>>1));
  *p=q31((s32)((a^sign)-sign));
 }
}
#endif
#endif
static void fade_block(register s32 *p,register u32 previous,register u32 next){
 register s32 phase=(s32)(previous<<5),step=(s32)next-(s32)previous;
 for(register u32 n=32;n;--n,p+=2){
  phase+=step;
#ifdef FX_FAST_WRAPPER
  register s32 g=phase>>5;
  p[0]=q31(((p[0]>>11)*g)>>8);p[1]=q31(((p[1]>>11)*g)>>8);
#else
  register u32 g=(u32)(phase>>5)<<7;
  p[0]=q31(scaled(p[0]>>11,g));p[1]=q31(scaled(p[1]>>11,g));
#endif
 }
}
