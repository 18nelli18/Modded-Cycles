/* Le codec son stock normalise FINE et ignore plusieurs mots de modulation.
 * Le son MIDI seul garde ses33mots exacts en28..93 du record100octets et tag
 * en94. Nom/header et sentinelle finale natifs restent identiques. Le byte de
 * machine garde meme sa position native46. Aucun format audio n'est change.
 * Les wrappers executes apres les codecs Wizard/filtre restaurent MIDI seul.
 */
typedef unsigned short u16;
typedef unsigned char u8;
#ifndef MM_MACHINE
#define MM_MACHINE 6
#endif
/* Detours de sauvegarde deja installes (Wizard/filtre), zero = prologue OS.
 * Le composeur renseigne ces entrees avant le boot, jamais depuis l'IRQ.
 */
volatile unsigned int mm_storage_api[3] __attribute__((section(".data")))={0,0,0};
void mm_save_post(u8 *record,const u8 *sound) {
 u16 tag=*(const u16 *)(sound+84);
 if(sound[38]!=MM_MACHINE||(tag!=0x4d49&&tag!=0x4d4a))return;
 for(unsigned int i=0;i<66;i++)record[28+i]=sound[20+i];
 *(u16 *)(record+94)=0x4d32;
}
void mm_load_post(u8 *sound,const u8 *record) {
 if(sound[38]!=MM_MACHINE)return;
 u16 tag=*(const u16 *)(record+92);
 if(*(const u16 *)(record+94)==0x4d32&&(tag==0x4d49||tag==0x4d4a)){
  for(unsigned int i=0;i<66;i++)sound[20+i]=record[28+i];
 }else if(*(const u16 *)(record+90)==0x4d49&&*(const u16 *)(record+88)<=16511){
  *(u16 *)(sound+54)=*(const u16 *)(record+88);
  *(u16 *)(sound+84)=0x4d49;
 }else{
  /* Un ancien son ne doit jamais transformer des valeurs audio en CC. */
  for(unsigned int i=11;i<=22;i++)*(u16 *)(sound+20+2*i)=64;
  *(u16 *)(sound+84)=0x4d49;
 }
}
