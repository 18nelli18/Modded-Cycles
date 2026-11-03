/* Deux divisions fractionnaires au lieu de trois, restes conserves.
 * ff + cc + feedback = den : reconstruire exactement les arrondis Q30.
 * Aucun flottant, aucun produit64bits et aucune approximation du filtre. */
#ifdef PF_SINGLE_DIV
/* ColdFire REMU ne rend pas aussi le quotient. Forcer DIVU puis mul/sub
 * evite un second passage dans le diviseur, sans approximation du reste. */
static u32 quotient(u32 n,u32 d){
 __asm__ volatile("divu.l %1,%0":"+d"(n):"d"(d):"cc");return n;
}
#else
static u32 quotient(u32 n,u32 d){return n/d;}
#endif
static u32 ratio(u32 n,u32 d,u32 *remainder){
 u32 result=0;
 /* den <= 2^24 and each remainder < den. Eight-bit chunks fit exactly
  * in 32 bits; four divisions produce the same 30 fractional bits. */
 for(u32 i=0;i<3;i++){n<<=8;u32 part=quotient(n,d);n-=part*d;result=(result<<8)|part;}
 n<<=6;u32 part=quotient(n,d);n-=part*d;result=(result<<6)|part;
 *remainder=n;return result;
}
#ifdef PF_ZERO_LUT
extern const u32 pf_zero_f[4096],pf_zero_r[4096];
#define PF_RATIO_NAME ratios_zero
#define PF_RATIO_EXTRA ,u32 cutoff,u32 damping
#else
#define PF_RATIO_NAME ratios
#define PF_RATIO_EXTRA
#endif
static void PF_RATIO_NAME(u32 ff,u32 feedback,u32 den,u32 type,s32*b,s32*a1,s32*a2 PF_RATIO_EXTRA){
 /* Control-All : reutiliser les coefficients identiques de la piste precedente.
  * Les caches par piste restent prioritaires ; aucune quantification ajoutee. */
 static struct {u32 valid,ff,feedback,den; s32 b[3],a1,a2;} shared;
 if(shared.valid&&shared.ff==ff&&shared.feedback==feedback&&shared.den==den){
  *b=shared.b[type];*a1=shared.a1;*a2=shared.a2;return;
 }
 u32 rf,rr,f,r;
#ifdef PF_ZERO_LUT
 if(damping==362){
  f=pf_zero_f[cutoff];r=pf_zero_r[cutoff];
  /* Restes exacts modulo2^32 : les vrais restes sont inferieurs a2^24.
   * Aucun produit64bits, aucune perte de precision du filtre. */
  rf=(ff<<30)-f*den;rr=(feedback<<30)-r*den;
 }else
#endif
 {f=ratio(ff,den,&rf);r=ratio(feedback,den,&rr);}
 u32 remain=rf*2+rr,carry=0;
 if(remain>=den){remain-=den;carry++;}
 if(remain>=den){remain-=den;carry++;}
 s32 diff=(s32)(2*f+r-1073741824u+carry);
 /* La fonction originale arrondit la valeur absolue vers zero. */
 *a1=(s32)(2u*(u32)diff+(diff<0&&remain?2u:0u));
 *a2=(s32)(1073741824u-2*r-(rr!=0)-(2*rr>den));
 u32 sum=rf+rr;
 *b=(s32)(type==0?f:type==2?r:1073741824u-f-r-(sum!=0)-(sum>den));
 shared.ff=ff;shared.feedback=feedback;shared.den=den;
 shared.b[0]=(s32)f;shared.b[1]=(s32)(1073741824u-f-r-(sum!=0)-(sum>den));shared.b[2]=(s32)r;
 shared.a1=*a1;shared.a2=*a2;shared.valid=1;
}
#ifdef PF_ZERO_LUT
#define ratios(ff,feedback,den,type,b,a1,a2) ratios_zero(ff,feedback,den,type,b,a1,a2,f,damping)
#endif
