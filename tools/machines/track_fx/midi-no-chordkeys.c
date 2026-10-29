/* MIDI ownership, routing and recorder without the removed chord-key feature. */
typedef unsigned int u32;
typedef unsigned char u8;
typedef unsigned short u16;
extern u32 mm_input_on(u32,u32,u32),mm_input_off(u32,u32);
extern u32 mi_lfo_encoder(const u32 *);
static u32 midi_owned[6][4];
static u8 midi_sources[6][128];
/* Capturer la vraie piste et la note traduite avant que le canal auto ou la
 * selection ne change. Le relachement appartient a cette attaque, pas a la
 * nouvelle piste selectionnee. Toutes les machines partagent cette regle. */
static u16 incoming_note[6][128];
static u8 incoming_channel[6][128];
static u32 receive_skip;
static u32 arp_owned[6][4];
extern u32 mx_arp_wants(u32);
extern void mx_arp_on(u32,u32,u32);
volatile u32 nc_no_filter=0;
extern void mi_receive_on_original(u32,u32,u32,u32);
extern void mi_receive_off_original(u32,u32,u32);
#define MIDI_MACHINE 17
#define ON ((void(*)(u32,u32,u32,u32,u32,u32,u32))0x4008171e)
#define OFF ((void(*)(u32,u32,u32))0x4008145e)
/* Les notes MIDI0..11 ont un sens percussion dans le routeur stock. Une
 * piste MIDI Out doit garder leur hauteur brute et son canal de reception.
 * Les autres machines conservent exactement le mapping de percussion natif.
 */
static u32 receives(u32 t,u32 channel) {
 if(t>=6)return 0;
 if(channel==0xffffffffu || channel==*(volatile u32*)0x40a70100)
  return t==*(volatile u32*)0x40a700c4;
 return channel==((volatile u32*)0x40a70104)[t];
}
void nc_on(u32,u32,u32,u32,u32,u32,u32);
void nc_off(u32,u32,u32);
void nc_on_received(u32 raw,u32 channel,u32 t,u32 n,u32 v,u32 source,u32 extra,u32 a,u32 b) {
 if(t<6 && (receive_skip&(1u<<t)))return;
 if(receive_skip && !receives(t,channel))return;
 if(t<6 && ((int(*)(void*,u32))0x4001e318)(0,t)==MIDI_MACHINE) {
  return; /* Deja traite avant le mapping percussion. */
 }
 if(t<6&&raw<128&&n<128&&v&&v<128){
  incoming_note[t][raw]=0x8000u|n;incoming_channel[t][raw]=(u8)channel;
 }
 nc_on(t,n,v,source,extra,a,b);
}
void nc_off_received(u32 raw,u32 channel,u32 t,u32 n,u32 source) {
 (void)raw;
 if(receive_skip)return; /* Les attaques capturees ont deja ete relachees. */
 if(t<6 && (receive_skip&(1u<<t)))return;
 if(receive_skip && !receives(t,channel))return;
 if(t<6 && ((int(*)(void*,u32))0x4001e318)(0,t)==MIDI_MACHINE)return;
 nc_off(t,n,source);
}
void nc_receive_on(u32 channel,u32 raw,u32 velocity,u32 source) {
 u32 mask=0,old=receive_skip;
 if(raw<128 && velocity && velocity<128)for(u32 t=0;t<6;t++)
  if(receives(t,channel) && ((int(*)(void*,u32))0x4001e318)(0,t)==MIDI_MACHINE) {
   mask|=1u<<t;
  }
 receive_skip=mask;mi_receive_on_original(channel,raw,velocity,source);receive_skip=old;
 /* Le mapper auto doit terminer l'ancienne attaque avant la nouvelle. */
 for(u32 t=0;t<6;t++)if(mask&(1u<<t)) {
  midi_sources[t][raw]=(u8)channel;nc_on(t,raw,velocity,source,0,0xffffffffu,0xffffffffu);
  incoming_note[t][raw]=0x8000u|raw;incoming_channel[t][raw]=(u8)channel;
 }
}
void nc_receive_off(u32 channel,u32 raw,u32 source) {
 u32 mask=0,old=receive_skip;
 if(raw<128)for(u32 t=0;t<6;t++)
  if((incoming_note[t][raw]&0x8000u)&&incoming_channel[t][raw]==(u8)channel){
   u32 note=incoming_note[t][raw]&127u;incoming_note[t][raw]=0;
   nc_off(t,note,source);mask|=1u<<t;
  }
 if(raw<128)for(u32 t=0;t<6;t++)
  if(!(mask&(1u<<t))&&((midi_owned[t][raw>>5]|arp_owned[t][raw>>5])&(1u<<(raw&31))) && midi_sources[t][raw]==(u8)channel) {
   nc_off(t,raw,source);mask|=1u<<t;
  }
 receive_skip=mask;mi_receive_off_original(channel,raw,source);receive_skip=old;
}
/* Le profil sans filtre doit absorber le geste retire avant les vues natives,
 * qui afficheraient sinon leur erreur de parametre non disponible.
 */
u32 nc_encoder_block(const u32 *event) {
 if(mi_lfo_encoder(event))return 1;
 if(!nc_no_filter || !event || event[0]!=0x400fbebcu || (event[3]!=6 && event[3]!=7))return 0;
 if(!((u32(*)(u32))0x4007faf4)(5))return 0;
 u32 root=((u32(*)(void))0x400cf866)();
 u32 state=((u32(*)(u32))0x4000eb90)(root);
 u32 track=((u32(*)(u32))0x40012412)(state);
 return track<6 && ((int(*)(void*,u32))0x4001e318)(0,track)!=MIDI_MACHINE;
}
void nc_on(u32 t,u32 n,u32 v,u32 source,u32 extra,u32 a,u32 b) {
 if(t<6&&n<128&&v&&v<128&&mx_arp_wants(t)){
  arp_owned[t][n>>5]|=1u<<(n&31);mx_arp_on(t,n,v);return;
 }
 if(t<6 && n<128 && v && v<128 &&
    ((int(*)(void*,u32))0x4001e318)(0,t)==MIDI_MACHINE) {
  /* Meme canal/port capture que les touches locales ; le producteur natif
   * de cette machine evite deja la seconde attaque differee. */
  mm_input_on(t,n,v);midi_owned[t][n>>5]|=1u<<(n&31);
 }
 ON(t,n,v,source,extra,a,b);
}
void nc_off(u32 t,u32 n,u32 source) {
 if(t<6&&n<128&&(arp_owned[t][n>>5]&(1u<<(n&31)))){
  arp_owned[t][n>>5]&=~(1u<<(n&31));
  ((void(*)(u32,u32,u32))0x4008145e)(t,n,0x40);return;
 }
 if(t<6 && n<128 && (midi_owned[t][n>>5]&(1u<<(n&31)))) {
  midi_owned[t][n>>5]&=~(1u<<(n&31));mm_input_off(t,n);
 }
 OFF(t,n,source);
}
/* Appele apres la capture du pad et avant le retour sans TRIG physique.
 * Le recorder natif choisit le pas de la reattaque, y compris en step record.
 */
u32 nc_pad(u32 t,u32 pad,const void *header) {(void)t;(void)pad;(void)header;return 0;}
void nc_reset(u32 t) {
 if(t>=6)return;
 for(u32 n=0;n<128;n++)incoming_note[t][n]=0;
 for(u32 n=0;n<128;n++)if(arp_owned[t][n>>5]&(1u<<(n&31))) {
  arp_owned[t][n>>5]&=~(1u<<(n&31));OFF(t,n,0x40);
 }
 for(u32 n=0;n<128;n++)if(midi_owned[t][n>>5]&(1u<<(n&31))) {
  midi_owned[t][n>>5]&=~(1u<<(n&31));mm_input_off(t,n);
 }
}
u32 nc_visible_chord(void) {return 0;}
void nc_step_on(unsigned char *message) {
 ((void(*)(unsigned char*))0x467adf70)(message);
}
