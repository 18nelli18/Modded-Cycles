/* Entree MIDI externe du profil fixe : conserver la derniere note par piste.
 * Les files audio et recorder restent celles du firmware natif. Les adresses
 * CK sont fournies par le linker du profil, pas recalculees dans l'IRQ audio.
 */
typedef unsigned int u32;
typedef unsigned char u8;
struct modifier { const void *header; u32 value; };
extern volatile struct modifier ck_live[6], ck_prepared[6];
extern const void *ck_header(void);
extern u32 ck_config(u32);
extern u32 ck_active_key(u32);
extern u32 ck_irq_save(void);
extern void ck_irq_restore(u32);
extern void ck_gesture(u32,u32);
extern void ck_note(void *,u32,u32);
extern u32 ck_active_note(u32),ck_has_note(void);
extern volatile u32 ck_packets[6];
extern u32 mm_input_on(u32,u32,u32),mm_input_off(u32,u32);
extern u32 mi_lfo_encoder(const u32 *);
struct capture { const void *header; u32 note,velocity,source,extra,a,b,active; };
static struct capture external[6];
static u32 midi_owned[6][4];
static u8 midi_sources[6][128];
static u32 receive_skip;
static u32 arp_owned[6][4];
extern u32 mx_arp_wants(u32);
extern void mx_arp_on(u32,u32,u32);
volatile u32 mi_no_filter=0;
extern void mi_receive_on_original(u32,u32,u32,u32);
extern void mi_receive_off_original(u32,u32,u32);
#define MIDI_MACHINE 17
#define ON ((void(*)(u32,u32,u32,u32,u32,u32,u32))0x4008171e)
#define OFF ((void(*)(u32,u32,u32))0x4008145e)
static u32 enabled(u32 t) {
 return t<6 && (ck_config(t)&0x80000000u) &&
   ((int(*)(void*,u32))0x4001e318)(0,t)==5;
}
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
void mi_on(u32,u32,u32,u32,u32,u32,u32);
void mi_off(u32,u32,u32);
void mi_on_received(u32 raw,u32 channel,u32 t,u32 n,u32 v,u32 source,u32 extra,u32 a,u32 b) {
 (void)raw;
 if(t<6 && (receive_skip&(1u<<t)))return;
 if(receive_skip && !receives(t,channel))return;
 if(t<6 && ((int(*)(void*,u32))0x4001e318)(0,t)==MIDI_MACHINE) {
  return; /* Deja traite avant le mapping percussion. */
 }
 mi_on(t,n,v,source,extra,a,b);
}
void mi_off_received(u32 raw,u32 channel,u32 t,u32 n,u32 source) {
 (void)raw;
 if(t<6 && (receive_skip&(1u<<t)))return;
 if(receive_skip && !receives(t,channel))return;
 if(t<6 && ((int(*)(void*,u32))0x4001e318)(0,t)==MIDI_MACHINE)return;
 mi_off(t,n,source);
}
void mi_receive_on(u32 channel,u32 raw,u32 velocity,u32 source) {
 u32 mask=0,old=receive_skip;
 if(raw<128 && velocity && velocity<128)for(u32 t=0;t<6;t++)
  if(receives(t,channel) && ((int(*)(void*,u32))0x4001e318)(0,t)==MIDI_MACHINE) {
   mask|=1u<<t;
  }
 receive_skip=mask;mi_receive_on_original(channel,raw,velocity,source);receive_skip=old;
 /* Le mapper auto doit terminer l'ancienne attaque avant la nouvelle. */
 for(u32 t=0;t<6;t++)if(mask&(1u<<t)) {
  midi_sources[t][raw]=(u8)channel;mi_on(t,raw,velocity,source,0,0xffffffffu,0xffffffffu);
 }
}
void mi_receive_off(u32 channel,u32 raw,u32 source) {
 u32 mask=0,old=receive_skip;
 if(raw<128)for(u32 t=0;t<6;t++)
  if(((midi_owned[t][raw>>5]|arp_owned[t][raw>>5])&(1u<<(raw&31))) && midi_sources[t][raw]==(u8)channel) {
   mi_off(t,raw,source);mask|=1u<<t;
  }
 receive_skip=mask;mi_receive_off_original(channel,raw,source);receive_skip=old;
}
/* Le profil sans filtre doit absorber le geste retire avant les vues natives,
 * qui afficheraient sinon leur erreur de parametre non disponible.
 */
u32 mi_encoder_block(const u32 *event) {
 if(mi_lfo_encoder(event))return 1;
 if(!mi_no_filter || !event || event[0]!=0x400fbebcu || (event[3]!=6 && event[3]!=7))return 0;
 if(!((u32(*)(u32))0x4007faf4)(5))return 0;
 u32 root=((u32(*)(void))0x400cf866)();
 u32 state=((u32(*)(u32))0x4000eb90)(root);
 u32 track=((u32(*)(u32))0x40012412)(state);
 return track<6 && ((int(*)(void*,u32))0x4001e318)(0,track)!=MIDI_MACHINE;
}
void mi_on(u32 t,u32 n,u32 v,u32 source,u32 extra,u32 a,u32 b) {
 if(t<6&&n<128&&v&&v<128&&mx_arp_wants(t)){
  arp_owned[t][n>>5]|=1u<<(n&31);mx_arp_on(t,n,v);return;
 }
 if(t<6) {
  struct capture *h=&external[t];
  h->active=0;
  if(n<128 && v && v<128 && enabled(t)) {
   const void *header=ck_header();
   u32 sr=ck_irq_save();
   ck_live[t].header=header;
   ck_live[t].value=ck_prepared[t].header==header ? ck_prepared[t].value:0;
   ck_irq_restore(sr);
   h->header=header;h->note=n;h->velocity=v;h->source=source;
   h->extra=extra;h->a=a;h->b=b;h->active=1;
  }
 }
 if(t<6 && n<128 && v && v<128 &&
    ((int(*)(void*,u32))0x4001e318)(0,t)==MIDI_MACHINE) {
  /* Meme canal/port capture que les touches locales ; le producteur natif
   * de cette machine evite deja la seconde attaque differee. */
  mm_input_on(t,n,v);midi_owned[t][n>>5]|=1u<<(n&31);
 }
 ON(t,n,v,source,extra,a,b);
}
void mi_off(u32 t,u32 n,u32 source) {
 if(t<6&&n<128&&(arp_owned[t][n>>5]&(1u<<(n&31)))){
  arp_owned[t][n>>5]&=~(1u<<(n&31));
  ((void(*)(u32,u32,u32))0x4008145e)(t,n,0x40);return;
 }
 if(t<6 && n<128 && (midi_owned[t][n>>5]&(1u<<(n&31)))) {
  midi_owned[t][n>>5]&=~(1u<<(n&31));mm_input_off(t,n);
 }
 if(t<6 && external[t].note==n)external[t].active=0;
 OFF(t,n,source);
}
/* Appele apres la capture du pad et avant le retour sans TRIG physique.
 * Le recorder natif choisit le pas de la reattaque, y compris en step record.
 */
u32 mi_pad(u32 t,u32 pad,const void *header) {
 struct capture *h;
 u32 sr;
 if(t>=6 || pad>=6)return 0;
 h=&external[t];
 if(!h->active)return 0;
 if(h->header!=header || !enabled(t)){h->active=0;return 0;}
 sr=ck_irq_save();ck_live[t].header=header;ck_live[t].value=pad+1;ck_irq_restore(sr);
 OFF(t,h->note,h->source);
 ON(t,h->note,h->velocity,h->source,h->extra,h->a,h->b);
 return 1;
}
void mi_reset(u32 t) {
 if(t>=6)return;
 external[t].active=0;
 for(u32 n=0;n<128;n++)if(arp_owned[t][n>>5]&(1u<<(n&31))) {
  arp_owned[t][n>>5]&=~(1u<<(n&31));OFF(t,n,0x40);
 }
 for(u32 n=0;n<128;n++)if(midi_owned[t][n>>5]&(1u<<(n&31))) {
  midi_owned[t][n>>5]&=~(1u<<(n&31));mm_input_off(t,n);
 }
}
/* La publication DSP reste la seule source du nom et des omissions.
 * Ce getter remplace seulement la condition de visibilite du bandeau natif.
 * Aucun dessin, formatage ou acces aux polices depuis le traitement MIDI.
 */
u32 mi_visible_chord(void) {
 u32 physical=ck_has_note(),any=physical,t,packet,note;
 if(!any)for(t=0;t<6;t++)any|=external[t].active;
 if(!any)return 0; /* Projet pas encore construit au demarrage. */
 u32 root=((u32(*)(void))0x400cf866)();
 u32 state=((u32(*)(u32))0x4000eb90)(root);
 t=((u32(*)(u32))0x40012412)(state);
 if(!enabled(t))return 0;
 packet=ck_packets[t];note=ck_active_note(t);
 if(external[t].active && external[t].header==ck_header()) {
  u32 n=external[t].note>96?96:external[t].note;
  if((packet&127u)==n)return packet;
 }
 return physical && (packet&127u)==note?packet:0;
}
/* Step Recorder utilise les setters de note, pas le writer live. Capturer
 * HARMONY apres son ecriture, sur son propre curseur et sa vraie piste.
 */
void mi_step_on(unsigned char *message) {
 u32 t=message[8];
 ((void(*)(unsigned char*))0x467adf70)(message);
 if(enabled(t)) {
  u32 root=((u32(*)(void))0x400cf866)();
  u32 pattern=((u32(*)(u32))0x4000f208)(root);
  void *track=(void*)((u32(*)(u32,u32))0x4000cfcc)(pattern,t);
  ck_note(track,t,*(volatile unsigned char*)0x4233e8f6);
 }
}
