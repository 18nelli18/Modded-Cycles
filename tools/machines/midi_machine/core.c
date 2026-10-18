/* Machine MIDI uniquement : aucun oscillateur, aucune E/S depuis le rendu.
 * Le masque lit les parametres natifs du pattern, pas une preference globale.
 * Les services MIDI et leur interface seront relies separement.
 */
typedef unsigned char u8;
typedef unsigned int u32;
typedef signed int i32;
typedef unsigned short u16;
#ifndef MM_MACHINE
#define MM_MACHINE 6
#endif
#ifdef MM_CONTROLS
extern const u16 *mm_params(u32);
extern u32 mm_channel(const u16 *,u32);
extern u32 mm_port(const u16 *);
#endif

/* Chaque touche capture le canal ET le port de son attaque. Un relachement
 * apres changement de machine/canal ne depend plus des nouveaux reglages.
 * Acces depuis les consommateurs UI seulement, pas depuis le rendu audio.
 */
static u16 mm_live[6][128];
static void mm_send(u32 channel,u32 note,u32 velocity,u32 port) {
 u8 bytes[3];bytes[0]=(velocity?0x90:0x80)|channel;bytes[1]=note;bytes[2]=velocity;
 ((void (*)(u32,const u8 *,u32))0x400826b0)(3,bytes,port);
}
u32 mm_live_off(u32 track,u32 note) {
 if(track>=6||note>=128)return 0;
 u32 saved=mm_live[track][note];
 if(!(saved&0x8000))return 0;
 mm_live[track][note]=0;
 mm_send(saved&15,note,0,(saved>>4)&15);
 return 1;
}
#ifdef MM_CONTROLS
void mm_live_cleanup_track(u32 lane){
 if(lane>=6)return;
 for(u32 note=0;note<128;note++)if(mm_live[lane][note]&0x8000)mm_live_off(lane,note);
}
void mm_live_cleanup(void){
 for(u32 lane=0;lane<6;lane++)for(u32 note=0;note<128;note++)
  if(mm_live[lane][note]&0x8000)mm_live_off(lane,note);
}
#endif
u32 mm_live_on(u32 track,u32 note,u32 velocity) {
 if(track>=6||note>=128)return 0;
 /* Fermer une attaque MIDI precedente, meme si le son a change depuis. */
 mm_live_off(track,note);
 if(((u8 (*)(u32,u32))0x4001e318)(0,track)!=MM_MACHINE)return 0;
 if(!velocity||velocity>127)return 1;
 #ifdef MM_CONTROLS
 const u16 *params=mm_params(track);
 u32 channel=mm_channel(params,track),port=mm_port(params);
 #else
 u32 root=((u32 (*)(void))0x400cf866)();
 u32 state=((u32 (*)(u32))0x4000eb90)(root);
 u32 channel=((u32 (*)(u32,u32))0x40012e82)(state,track);
 if(channel>15)return 1;
 u32 port=((u32 (*)(void))0x40082686)();
 if(port==1)port=0;
 #endif
 if(channel>15)return 1;
 mm_live[track][note]=0x8000|(port<<4)|channel;
 mm_send(channel,note,velocity,port);
 return 1;
}

/* Prologue natif de MOut : instructions entieres, aucune adresse PC relative.
 * Le chemin ordinaire rejoue ces instructions puis reprend a +6.
 */
__asm__(".text\n.globl mm_mout_original\nmm_mout_original:\n"
        "move.l %a2,-(%sp)\nmove.l 8(%sp),%a2\n"
        "jmp 0x40016e96\n");
extern u32 mm_mout_original(void *track);
u32 mm_mout(void *track) {
 /* MOut recoit un objet piste du pattern, pas un objet son ! Ne jamais
  * interpreter les octets de trigs comme des parametres de machine.
  */
 /* L'OS renvoie ses pointeurs dans D0 ; GCC m68k-linux attend A0 pour
  * un retour type pointeur. Utiliser un entier sur cette frontiere ABI.
  */
 u32 root=((u32 (*)(void))0x400cf866)();
 u8 *pattern=(u8 *)((u32 (*)(u32))0x4000f208)(root);
 u32 delta=(u32)track-(u32)(pattern+112);
 if(delta<6*88 && delta%88==0) {
  /* Getter membre : premier argument this ignore, second = numero de piste. */
  if(((u8 (*)(u32,u32))0x4001e318)(0,delta/88)==MM_MACHINE)return 1;
 }
 return mm_mout_original(track);
}

void mm_update(i32 note, void *voice, const void *params) {
 (void)note;(void)voice;(void)params;
}
void mm_render(i32 *out, void *voice) {
 (void)voice;
 for(u32 i=0;i<32;i++)out[i]=0;
}
/* params pointe la premiere des six tranches natives de66octets, sans header. */
u32 mm_mask(const u8 *params,u32 machine) {
 if(!params||machine>127)return 0;
 u32 mask=0;
 for(u32 lane=0;lane<6;lane++)
  if(params[66*lane+18]==machine)mask|=1u<<lane;
 return mask;
}
