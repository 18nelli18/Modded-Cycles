/* Exact loaded LFO2 restore with four word copies per track. Native transition
 * and import paths still call the original restore in the pinned firmware. */
typedef unsigned int u32;typedef unsigned char u8;
extern volatile u32 ls_storage,ls_polarity[12],ls_lp_one[6];
void ls_restore(u32 ctx,u32 id){
 const u8*row=(const u8*)(ls_storage+11152+id*116);
 u32 sr;__asm__ volatile("move.w %%sr,%0\n\tmove.w #0x2700,%%sr":"=d"(sr)::"memory","cc");
 for(u32 t=0;t<6;t++){
  const u32*s=(const u32*)(row+t*16);volatile u32*d=(volatile u32*)(ctx+192+t*16);
  u32 table=*(volatile u32*)0x40a78888;const u8*raw=table?(const u8*)(table+28+t*100):0;
  u32 one=raw&&(raw[79]&0xfc)==0xa0?raw[79]&1:ls_lp_one[t]&1;
  d[0]=s[0]|0xa0|one|((u32)row[96+t]<<1);d[1]=s[1];d[2]=s[2];d[3]=s[3];
 }
 for(u32 i=0;i<12;i++)ls_polarity[i]=row[102+i];
 __asm__ volatile("move.w %0,%%sr"::"d"(sr):"memory","cc");
}
