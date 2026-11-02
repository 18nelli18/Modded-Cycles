/* Chargeur unique : decode avant de nettoyer le BSS natif, puis pose les
 * segments declares. Aucun ancien installateur ni chargeur sparse en chaine.
 * RB_SOURCE est fourni par le constructeur. Etat temporaire en DDR43000000.
 */
typedef unsigned int u32;
typedef unsigned char u8;
#if !RB_RAW
struct bits {const u8 *src;u32 tag;};
static u32 bit(struct bits *r){
 r->tag<<=1;
 if(!(r->tag&255u)){u32 b=*r->src++;r->tag=(b<<1)|1;return b>>7;}
 return(r->tag>>8)&1;
}
static u32 gamma(struct bits*r){u32 v=1;do{v=(v<<1)+bit(r);}while(!bit(r));return v;}
static void depack(const u8*src,u8*out){
 struct bits r={src,0};u32 prior=1;
 for(;;){
  if(bit(&r)){*out++=*r.src++;continue;}
  u32 g=gamma(&r),off=prior;
  if(g!=2){off=(g<<8)+*r.src++;if(off==767)return;off-=767;prior=off;}
  u32 n=bit(&r)*2;n+=bit(&r);if(!n)n=gamma(&r)+2;
  n+=1+(off>3328);const u8*from=out-off;while(n--)*out++=*from++;
 }
}
#endif
void rb_boot(void){
 u8*stage=(u8*)0x43000000;
#if RB_RAW
 /* Le navigateur peut ajouter des segments Optional sans recompiler le
  * chargeur. Lire source/taille avant clearBSS, qui efface cet en-tete. */
 const volatile u32*header=(const volatile u32*)0x401aa148;
 const u8*input=(const u8*)header[5];u32 bytes=header[6];
 for(u32 i=0;i<bytes;i++)stage[i]=input[i];
#else
 depack((const u8*)RB_SOURCE,stage);
#endif
 ((void(*)(void))0x400004b2)();
 /* Les etats ne doivent pas dependre du contenu DDR au demarrage. */
 volatile u32*zero=(volatile u32*)0x46700000;
 for(u32 n=0;n<0x300000/4;n++)zero[n]=0;
 zero=(volatile u32*)0x80000000;
 for(u32 n=0;n<0x10000/4;n++)zero[n]=0;
 const u32*table=(const u32*)stage;u32 count=*table++;
 for(u32 i=0;i<count;i++){
  volatile u32*dst=(volatile u32*)table[0];u32 length=table[1],n=(length&0x7fffffffu)/4;
  const u32*src=(const u32*)(stage+table[2]);table+=3;
  /* Tables sine MD : deltas16 signes, accumulation32 exacte au boot. */
  if(length&0x80000000u){const short*delta=(const short*)src;u32 value=0;while(n--){value+=(int)*delta++;*dst++=value;}}
  else while(n--)*dst++=*src++;
 }
 __asm__ volatile("move.l #0x000cc100,%%d0\n movec %%d0,%%cacr\n nop\n lea 0xfc044000,%%a0":::"d0","a0","memory");
}
