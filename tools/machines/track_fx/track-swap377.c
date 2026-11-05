/* Permutation arretee : preflight complet avant toute ecriture.
 * Aucun appel depuis l audio, aucune allocation, aucun presse-papiers natif.
 * Les descripteurs sont construits par l adaptateur UI du build courant.
 */
typedef unsigned int u32;typedef unsigned char u8;
typedef struct {u8 *base;u32 stride,bytes,rows;} ts_block;
typedef struct {u8 *base;u32 stride,rows;} ts_masks;
typedef struct {ts_block *blocks;u32 count;ts_masks *masks;u32 mask_count;const volatile u32*owner;u32 expected_owner,expected_active,expected_generation;} ts_plan;
u32 ts_bits(u32 mask,u32 a,u32 b){
 u32 different=((mask>>a)^(mask>>b))&1u;
 return mask^((different<<a)|(different<<b));
}
static u32 stopped(void){return !*(volatile u32*)0x40a7883c&&!*(volatile u32*)0x40a78874;}
static u32 context(const ts_plan*p){return !p->owner||(*p->owner==p->expected_owner&&*(volatile u32*)0x40a7887c==p->expected_active&&*(volatile u32*)0x468f6e80==p->expected_generation&&*(const volatile u32*)(p->expected_owner+8)==*(volatile u32*)0x406fa02c);}
static u32 writable(u32 base,u32 bytes){
 /* Donnees natives SDRAM, SRAM ou heap des extensions, jamais les registres. */
 return bytes&&base>=0x40190000u&&base<0x80020000u&&bytes<=0x80020000u-base;
}
static u32 overlap(u32 a,u32 n,u32 b,u32 m){return a<b+m&&b<a+n;}
u32 ts_exchange(const ts_plan *p,u32 a,u32 b){
 if(!stopped()||a>=6||b>=6||a==b||!p||!p->blocks||!p->count||p->count>64||p->mask_count>16||(!p->masks&&p->mask_count))return 0;
 for(u32 i=0;i<p->count;i++){
  const ts_block*x=p->blocks+i;u32 base=(u32)x->base;
  if(x->rows!=6||!x->bytes||x->bytes>x->stride||x->stride>65536||!writable(base,x->stride*5+x->bytes))return 0;
  /* Refuser les alias : chaque octet appartient a un seul proprietaire. */
  for(u32 j=0;j<i;j++)for(u32 t=0;t<6;t++)for(u32 v=0;v<6;v++)
   if(overlap(base+t*x->stride,x->bytes,(u32)p->blocks[j].base+v*p->blocks[j].stride,p->blocks[j].bytes))return 0;
 }
 for(u32 i=0;i<p->mask_count;i++){
  const ts_masks*x=p->masks+i;
  if(x->rows!=6||!x->stride||x->stride>65536||!writable((u32)x->base,5*x->stride+1))return 0;
  for(u32 j=0;j<i;j++)for(u32 t=0;t<6;t++)for(u32 v=0;v<6;v++)
   if(x->base+t*x->stride==p->masks[j].base+v*p->masks[j].stride)return 0;
 }
 u32 sr;__asm__ volatile("move.w %%sr,%0\n\tmove.w #0x2700,%%sr":"=d"(sr)::"memory","cc");
 /* Le transport peut avoir change pendant le preflight. */
 if(!stopped()||!context(p)){__asm__ volatile("move.w %0,%%sr"::"d"(sr):"memory","cc");return 0;}
 for(u32 i=0;i<p->count;i++){
  const ts_block*x=p->blocks+i;u8 *left=x->base+a*x->stride,*right=x->base+b*x->stride;
  for(u32 k=0;k<x->bytes;k++){u8 value=left[k];left[k]=right[k];right[k]=value;}
 }
 for(u32 i=0;i<p->mask_count;i++)for(u32 t=0;t<6;t++){
  u8 *v=p->masks[i].base+t*p->masks[i].stride;*v=(u8)ts_bits(*v,a,b);
 }
 __asm__ volatile("move.w %0,%%sr"::"d"(sr):"memory","cc");return 1;
}
