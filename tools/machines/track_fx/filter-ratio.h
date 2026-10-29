/* Deux divisions fractionnaires au lieu de trois, restes conserves.
 * ff + cc + feedback = den : reconstruire exactement les arrondis Q30.
 * Aucun flottant, aucun produit64bits et aucune approximation du filtre. */
static u32 ratio(u32 n,u32 d,u32 *remainder){
 u32 result=0;
 /* den <= 2^24 and each remainder < den. Eight-bit chunks fit exactly
  * in 32 bits; four divisions produce the same 30 fractional bits. */
 for(u32 i=0;i<3;i++){n<<=8;u32 part=n/d;n-=part*d;result=(result<<8)|part;}
 n<<=6;u32 part=n/d;n-=part*d;result=(result<<6)|part;
 *remainder=n;return result;
}
static void ratios(u32 ff,u32 feedback,u32 den,u32 type,s32*b,s32*a1,s32*a2){
 /* Control-All : reutiliser les coefficients identiques de la piste precedente.
  * Les caches par piste restent prioritaires ; aucune quantification ajoutee. */
 static struct {u32 valid,ff,feedback,den; s32 b[3],a1,a2;} shared;
 if(shared.valid&&shared.ff==ff&&shared.feedback==feedback&&shared.den==den){
  *b=shared.b[type];*a1=shared.a1;*a2=shared.a2;return;
 }
 u32 rf,rr,f=ratio(ff,den,&rf),r=ratio(feedback,den,&rr);
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
