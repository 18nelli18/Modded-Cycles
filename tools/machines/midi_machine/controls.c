/* CC dans les douze mots de parametres du son MIDI, slots11..22.
 * L'encodage conserve numero ET valeur dans un lock natif : changer le CC
 * de base ne retargete donc pas un lock deja enregistre. Aucun fichier
 * annexe, aucune banque de notes B, aucune E/S depuis ces fonctions pures.
 * Ce format doit encore etre raccorde aux setters/locks/save natifs.
 */
typedef unsigned int u32;
typedef signed int i32;
typedef unsigned short u16;
#define MM_CC_MAGIC 0x4d49
#define INVALID 0xffffffffu

/* zero..127 = OFF avec sa valeur ; 128..16511 = CC0..127 + valeur. */
u32 mm_cc_pack(i32 cc,u32 value) {
 if(cc < -1 || cc>127 || value>127)return INVALID;
 return ((u32)(cc+1)<<7)|value;
}
i32 mm_cc_number(u32 word) {
 if(word>16511)return -1;
 return (i32)(word>>7)-1;
}
u32 mm_cc_value(u32 word) {return word<=16511?word&127:64;}
u32 mm_cc_read(const u16 *params,u32 knob) {
 if(!params||knob>=12)return INVALID;
 /* Speed, Swing et Chance gardent leurs commandes natives. */
 if(knob==8||knob==10||knob==11)return INVALID;
 if((params[32]!=MM_CC_MAGIC&&params[32]!=MM_CC_MAGIC+1&&params[32]!=MM_CC_MAGIC+2)||params[11+knob]>16511)return 64;
 return params[11+knob];
}
/* Mutation d'une copie UI seulement ; le caller publie via le setter OS.
 * Retourne le mot complet, pas un paquet MIDI : assigner ne transmet rien.
 */
u32 mm_cc_edit(u16 *params,u32 knob,i32 delta,u32 assign) {
 if(!params||knob>=12)return INVALID;
 if(knob==8||knob==10||knob==11)return INVALID;
 if(params[32]!=MM_CC_MAGIC&&params[32]!=MM_CC_MAGIC+1&&params[32]!=MM_CC_MAGIC+2){
  for(u32 i=0;i<12;i++)params[11+i]=64;
  params[32]=MM_CC_MAGIC;
 }
 if(delta>127)delta=127;
 if(delta < -127)delta=-127;
 u32 old=mm_cc_read(params,knob),value=mm_cc_value(old);
 i32 cc=mm_cc_number(old);
 if(assign){
  cc+=delta;if(cc < -1)cc=-1;if(cc>127)cc=127;
 }else{
  if(cc<0)return old;
  i32 next=(i32)value+delta;if(next<0)next=0;if(next>127)next=127;
  value=(u32)next;
 }
 return params[11+knob]=(u16)mm_cc_pack(cc,value);
}
