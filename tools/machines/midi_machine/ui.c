/* Interface MIDI seule : intercepter l'encodeur avant les vues de parametres.
 * Les retours pointeurs de l'OS sont declares entiers (ABI D0, pas A0 GCC).
 * Les locks utilisent les vrais setters du pattern, sans banque B.
 */
typedef unsigned int u32;
typedef signed int i32;
typedef unsigned short u16;
typedef unsigned char u8;
#ifndef MM_MACHINE
#define MM_MACHINE 6
#endif
extern u32 mm_cc_read(const u16 *,u32);
extern u32 mm_cc_edit(u16 *,u32,i32,u32);
extern i32 mm_cc_number(u32);
extern u32 mm_cc_value(u32);
extern void mm_popup(const char *);
extern void mm_menu_draw(u32,u32);
extern u32 mm_native_default(u32,u32);
extern void mm_setup(u16 *);
extern u32 mm_lfo_read(const u16 *,u32,u32);
extern u32 mm_lfo_edit(u16 *,u32,u32,i32);
extern u32 mm_route_read(const u16 *,u32);
extern u32 mm_route_edit(u16 *,u32,i32);
extern u32 mm_channel(const u16 *,u32);
extern u32 mm_port(const u16 *);
/* API[0/1] : adresses SETTINGS-held/mod-used du support commun si installe. */
volatile u32 mm_ui_api[5];
static u32 mm_settings_used,mm_settings_held,mm_func_held,mm_track_taken;
static u32 mm_page,mm_row,mm_edit,mm_page_lane=6;
static u32 mm_seen[6];
static void redraw(void){
 u32 app=*(volatile u32 *)0x40fe4178;
 if(app)((void (*)(u32))0x40076bee)(app+64);
}
static const char *fields[8]={"Speed","Mult","Fade","CC","Wave","Phase","Mode","Depth"};
static u32 selected(void) {
 u32 root=((u32 (*)(void))0x400cf866)();
 return ((u32 (*)(u32))0x40012412)(root+48);
}
static u32 midi(u32 lane) {
 if(lane<6&&((u8 (*)(u32,u32))0x4001e318)(0,lane)==MM_MACHINE){mm_seen[lane]=1;return 1;}
 return 0;
}
static u32 sound_object(u32 lane) {
 u32 root=((u32 (*)(void))0x400cf866)();
 u32 bank=((u32 (*)(u32))0x4000eb9c)(root);
 return ((u32 (*)(u32,u32))0x40009c1a)(bank,lane);
}
static const u16 *params_for(u32 object) {
 if(!object)return (const u16 *)0;
 u32 vt=*(u32 *)object;
 if(!vt)return (const u16 *)0;
 u32 raw=((u32 (*)(u32))*(u32 *)(vt+40))(object);
 return raw?(const u16 *)(raw+20):(const u16 *)0;
}
const u16 *mm_params(u32 lane){return lane<6?params_for(sound_object(lane)):(const u16 *)0;}
static char *number(char *p,u32 n,u32 digits) {
 if(digits==3)*p++='0'+n/100;
 if(digits>=2)*p++='0'+n/10%10;
 *p++='0'+n%10;return p;
}
static char *word(char *p,const char *s){while(*s)*p++=*s++;return p;}
static void cc_text(char *line,u32 knob,u32 packed,u32 assign) {
 char *p=word(line,"CC");p=number(p,knob+1,2);p=word(p,assign?" ASSIGN ":" ");
 i32 cc=mm_cc_number(packed);
 p=cc<0?word(p,"OFF"):number(p,(u32)cc,3);
 if(!assign){p=word(p," = ");p=number(p,mm_cc_value(packed),3);}
 *p=0;
}
/* Parametres publies ensemble avec la vraie notification OS, jamais rawmem. */
static void publish(u32 object,const u16 *before,const u16 *after) {
 u32 records[64],count=0;
 for(u32 slot=1;slot<=32;slot++){
  if(slot==9||slot==10)continue;
  if(before[slot]==after[slot])continue;
  records[2*count]=slot;records[2*count+1]=(u32)after[slot]<<16;count++;
 }
 if(count){
  u32 pair[2]={(u32)records,(u32)(records+2*count)};
  ((void (*)(u32,const u32 *))0x4001416c)(object,pair);
  redraw();
 }
}
/* Les mots MIDI ne sont pas des reglages audio : revenir aux defauts du
 * moteur cible, sans toucher machine, Pitch, notes ou donnees du pattern. */
void mm_audio_poll(void){
 for(u32 lane=0;lane<6;lane++){
  u32 machine=((u8 (*)(u32,u32))0x4001e318)(0,lane);
  if(machine==MM_MACHINE){mm_seen[lane]=1;continue;}
  if(!mm_seen[lane])continue;
  mm_seen[lane]=0;
  u32 object=sound_object(lane);const u16 *before=params_for(object);
  if(!before||(before[32]!=0x4d49&&before[32]!=0x4d4a))continue;
  u16 after[33];for(u32 i=0;i<33;i++)after[i]=before[i];
  for(u32 i=1;i<33;i++)if(i!=9&&i!=10)after[i]=(u16)mm_native_default(i,machine);
  after[32]=0;publish(object,before,after);
 }
}
static void page(u32 value,u32 lane){mm_page=value;mm_row=0;mm_edit=0;mm_page_lane=lane;redraw();}
/* Ne pas intercepter DATA quand une vraie fenetre native (MACHINES, CONFIG,
 * navigateur...) est au-dessus du panneau MIDI. Les potards gris restent CC.
 */
static u32 home_visible(void){
 if(!*(volatile u32 *)0x40fe4178)return 1;
 u32 app=((u32 (*)(void))0x400d0974)();
 u32 manager=((u32 (*)(u32))0x400060d8)(app);
 if(!manager)return 1;
 u32 head=manager+20,node=*(u32 *)(head+4);
 for(u32 i=0;node&&node!=head&&i<32;i++){
  u32 view=*(u32 *)(node+8);
  if(view&&!*(u8 *)(view+48)){
   u32 vt=*(u32 *)view;return vt==0x400ffe20;
  }
  node=*(u32 *)(node+4);
 }
 return 1;
}
/* FUNC a pu presenter QuickMute avant TRACK. Fermer cette seule vue pour
 * que le setup MIDI soit devant, sans armer le verrouillage mute. */
static void close_mute(void){
 u32 app=*(volatile u32 *)0x40fe4178;if(!app)return;
 u32 head=app+84,node=*(u32 *)(head+4);
 for(u32 i=0;node&&node!=head&&i<32;i++){
  u32 view=*(u32 *)(node+8);
  if(view&&*(u32 *)view==0x40100c3c&&!*(u8 *)(view+48)){
   ((void (*)(u32))0x40076126)(view);
   if(*(volatile u32 *)0x40100c44!=0x400234b6)*(volatile u16 *)0x401487ec=0;
   return;
  }
  node=*(u32 *)(node+4);
 }
}
static void prepare_setup(u32 lane){
 u32 object=sound_object(lane);const u16 *before=params_for(object);if(!before)return;
 u16 copy[33];for(u32 i=0;i<33;i++)copy[i]=before[i];mm_setup(copy);publish(object,before,copy);
}
static u32 track_object(u32 lane) {
 u32 root=((u32 (*)(void))0x400cf866)();
 u32 pattern=((u32 (*)(u32))0x4000f208)(root);
 return pattern?((u32 (*)(u32,u32))0x4000cfcc)(pattern,lane):0;
}
i32 mm_track_read(u32 lane,u32 pad){
 u32 object=track_object(lane);if(!object)return pad?60:0;
 if(pad)return ((u8 (*)(u32))0x40015a34)(object);
 return ((i32 (*)(u32))0x40016da6)(object);
}
void mm_track_edit(u32 lane,u32 pad,i32 delta){
 u32 object=track_object(lane);if(!object)return;
 i32 value=mm_track_read(lane,pad)+delta,lo=pad?0:-60,hi=pad?127:60;
 if(value<lo)value=lo;
 if(value>hi)value=hi;
 ((void (*)(u32,i32))(pad?0x40015a64:0x40016dd6))(object,value);redraw();
}
static void write_lock(u32 object,u32 step,u32 slot,u32 value) {
 if(step>=64||step>=((u32 (*)(u32))0x40016402)(object))return;
 if(!((u8 (*)(u32,u32))0x40015c20)(object,step)&&
    !((u8 (*)(u32,u32))0x40015c7c)(object,step))
  ((void (*)(u32,u32,u32))0x40017bb0)(object,step,1);
 ((void (*)(u32,u32,u32,u32))0x4001646a)(object,step,slot,value);
}
/* Les numeros de CC sont figes dans chaque lock. Tourner ensuite un potard
 * tenu sur plusieurs pas part de chaque valeur verrouillee, pas de la base.
 * Un geste sur des pas hors longueur reste consomme, sans changer le son.
 */
static u32 grid_locks(u32 lane,u32 knob,i32 delta,const u16 *base,u32 *shown) {
 u8 *state=(u8 *)((u32 (*)(void))0x400cf9a8)();
 if(!state||!state[357]||state[389])return 0;
 u32 hi=*(u32 *)(state+348),lo=*(u32 *)(state+352);
 if(!(hi|lo))return 0;
 u32 object=track_object(lane);if(!object)return 1;
 u32 limit=((u32 (*)(u32))0x40016402)(object);
 for(u32 step=0;step<64&&step<limit;step++){
  if(!((step<32?lo>>step:hi>>(step-32))&1))continue;
  i32 old=((i32 (*)(u32,u32,u32,u32))0x4000da2a)(*(u32 *)(object+44),lane,step,11+knob);
  u16 copy[33];for(u32 i=0;i<33;i++)copy[i]=base[i];
  if(old>=0&&old<=16511){copy[32]=0x4d49;copy[11+knob]=(u16)old;}
  u32 prior=mm_cc_read(copy,knob);
  *shown=mm_cc_edit(copy,knob,delta,0);
  if(*shown!=prior&&mm_cc_number(*shown)>=0)write_lock(object,step,11+knob,*shown);
 }
 return 1;
}
static void live_lock(u32 lane,u32 knob,u32 packed) {
 u32 state=((u32 (*)(void))0x400cf9a8)();
 if(!state||!((u8 (*)(u32))0x4006ba76)(state))return;
 u32 object=track_object(lane);if(!object)return;
 u32 clock=((u32 (*)(void))0x400cfd0e)();
 u32 step=((u32 (*)(u32,u32))0x4006a984)(clock,lane);
 write_lock(object,step,11+knob,packed);
}
u32 mm_encoder(const u32 *event) {
 if(!event||event[0]!=0x400fbebc||event[3]<1||event[3]>13)return 0;
 u32 lane=selected();if(!midi(lane))return 0;
 if(mm_page_lane!=lane)page(0,lane);
 if(event[3]==1&&(!mm_page||(mm_page!=3&&!home_visible()))){page(0,lane);return 0;}
 u32 object=sound_object(lane);const u16 *before=params_for(object);
 if(!before)return 1; /* Ne jamais laisser agir un parametre audio en repli. */
 u16 changed[33];for(u32 i=0;i<33;i++)changed[i]=before[i];
 i32 delta=((i32 (*)(const u32 *,u32,u32))0x4006f73a)(event,1,1);
 u32 assign=mm_ui_api[0]?*(volatile u32 *)mm_ui_api[0]:mm_settings_held||((u32 (*)(u32))0x4007faf4)(13);
 if(mm_page&&(event[3]==1||(mm_page<3&&!assign))){
  u32 count=mm_page==3?4:8,field=event[3]==1?mm_row:event[3]-2;
  if(event[3]==1&&!mm_edit){
   i32 row=(i32)mm_row+delta;if(row<0)row=0;if(row>=(i32)count)row=count-1;mm_row=(u32)row;redraw();return 1;
  }
  if(field>=count)return 1;
  mm_row=field;
  if(mm_page==3){
   if(field<2)mm_route_edit(changed,field,delta);
   else{mm_track_edit(lane,field-2,delta);return 1;}
  }
  else{
   if(field!=1&&field!=3&&field!=4&&field!=6)delta*=128;
   mm_lfo_edit(changed,mm_page-1,field,delta);
  }
  publish(object,before,changed);return 1;
 }
 if(event[3]==1)return 0; /* DATA reste natif, notamment dans FUNC+PAGE. */
 u32 knob=event[3]-2;
 u32 old=mm_cc_read(before,knob),packed=old;
 if(!assign&&mm_cc_number(old)<0)return 1; /* Non assigne : silence, aucun parametre audio. */
 if(!assign&&grid_locks(lane,knob,delta,before,&packed)){
  char line[32];cc_text(line,knob,packed,0);mm_popup(line);return 1;
 }
 packed=mm_cc_edit(changed,knob,delta,assign);
 publish(object,before,changed);
 if(assign){
  mm_settings_used=1;
  if(mm_ui_api[1])*(volatile u32 *)mm_ui_api[1]=1;
 }else if(packed!=old&&mm_cc_number(packed)>=0){
  live_lock(lane,knob,packed);
  u32 channel=mm_channel(changed,lane),port=mm_port(changed);
  if(channel<16){
   u8 bytes[3]={0xb0|channel,(u8)mm_cc_number(packed),(u8)mm_cc_value(packed)};
   ((void (*)(u32,const u8 *,u32))0x400826b0)(3,bytes,port);
  }
 }
 char line[32];cc_text(line,knob,packed,assign);mm_popup(line);
 return 1;
}
/* Relais autonome sans support Wizard : ne pas ouvrir CONFIG apres assignation.
 * Avec support commun, le getter existant traite la release et ses drapeaux.
 */
u32 mm_ui_key(const u32 *event) {
 if(!event)return 0;
 u32 lane=selected(),code=event[3],flags=event[4];
 if(code==13)mm_settings_held=(flags&1)!=0;
 if(code==1)mm_func_held=(flags&1)!=0;
 if(!midi(lane))return 0;
 /* Ce detour precede le getter commun : publier aussi l'appui brut, avant
  * toute consommation. Le premier test ne simulait que son resultat. */
 if(code==13&&!(flags&32)&&mm_ui_api[0])*(volatile u32 *)mm_ui_api[0]=mm_settings_held;
 if(mm_page_lane!=lane)page(0,lane);
 if(code==2&&(mm_track_taken||mm_func_held||(flags&2)||((u32 (*)(u32))0x4007faf4)(1))){
  if((flags&9)==1){close_mute();prepare_setup(lane);page(3,lane);mm_track_taken=1;}
  if(!(flags&1))mm_track_taken=0;
  return 1;
 }
 if(code==8&&home_visible()){
  if((flags&9)==1){prepare_setup(lane);page(mm_page==1?2:mm_page==2?0:1,lane);}
  return 1;
 }
 if(code==12&&mm_page){if((flags&9)==1)page(0,lane);return 1;}
 if(code==32){
  if(flags&16){
   if(mm_page){mm_edit=!mm_edit;redraw();}
  }
  return mm_page?1:0;
 }
 /* FUNC+PAGE conserve le vrai Scale Setup du pattern A. */
 if(code==2||code==3||code==4||code==5||code==14||code==15){page(0,lane);return 0;}
 if(code!=13)return 0;
 /* FUNC+SETTINGS reste la sauvegarde native, sans menu MIDI parasite. */
 if(((u32 (*)(u32))0x4007faf4)(1)){page(0,lane);return 0;}
 if(flags&1){if(!(flags&8)){mm_settings_used=0;if(mm_ui_api[1])*(volatile u32 *)mm_ui_api[1]=0;}return 0;}
 if(!mm_settings_used){page(0,lane);return 0;}
 mm_settings_used=0;return 1;
}
static void text(u32 canvas,u32 x,u32 y,const char *line) {
 ((void (*)(u32,u32,u32,u32,u32,const char *,...))0x40071a04)(canvas,0x40ea14cc,x,y,0x10,"%s",line);
}
u32 mm_menu_row(void){return mm_row;}
u32 mm_menu_edit(void){return mm_edit;}
void mm_menu_value(u32 self,u32 item,u32 canvas,u32 x,u32 y,u32 flags){
 (void)self;(void)flags;
 u32 lane=selected(),field=*(u32 *)(item+80)&255;
 const u16 *params=params_for(sound_object(lane));char line[32],*at=line;
 if(field==0){u32 value=mm_route_read(params,0);if(value==16)at=word(at,"Glob");else at=number(at,value+1,value+1>9?2:1);}
 else if(field==1){static const char *const ports[5]={"Glob","Off","USB","DIN","Both"};u32 value=mm_route_read(params,1);at=word(at,ports[value<=4?value:0]);}
 else if(field==2){i32 value=mm_track_read(lane,0);if(value<0){*at++='-';value=-value;}at=number(at,(u32)value,value>9?2:1);}
 else{static const char *const names[12]={"C","C#","D","D#","E","F","F#","G","G#","A","A#","B"};u32 value=(u32)mm_track_read(lane,1);value=value<128?value:60;at=word(at,names[value%12]);if(value<12){*at++='-';*at++='1';}else at=number(at,value/12-1,1);}
 *at=0;((void (*)(u32,u32,u32,u32,u32,const char *,...))0x40071a04)(canvas,0x40ea14cc,x+24,y,4,"%s",line);
 if(mm_edit&&field==mm_row)((void (*)(u32,u32,u32,u32,u32,u32))0x40070efc)(canvas,x+23-6*(u32)(at-line),y-2,x+25,y+10,0xffffffffu);
}
u32 mm_draw(u32 view,u32 canvas) {
 (void)view;mm_audio_poll();u32 lane=selected();if(!midi(lane))return 0;
 if(mm_page_lane!=lane)page(0,lane);
 if(!mm_page)return 0; /* L'ecran de piste et les editeurs stock restent visibles. */
 if(mm_page==3){mm_menu_draw(view,canvas);return 1;}
 ((void (*)(u32,u32,u32,u32,u32,u32))0x40070dea)(canvas,0,0,127,63,0);
 char line[32];char *p=word(line,"T");p=number(p,lane+1,1);p=word(p,mm_page==1?" MIDI LFO 1":mm_page==2?" MIDI LFO 2":mm_page==3?" MIDI SETUP":" MIDI OUT");*p=0;text(canvas,0,54,line);
 const u16 *params=params_for(sound_object(lane));
 if(!params){text(canvas,0,34,"MIDI setup unavailable");return 1;}
 if(mm_page){
  u32 count=mm_page==3?4:8;
  for(u32 field=0;field<count;field++){
   char *at=line;*at++=field==mm_row?(mm_edit?'*':'>'):' ';
   static const char *const setup_fields[4]={"Channel","Output","KbT","Pad Note"};
   at=word(at,mm_page==3?setup_fields[field]:fields[field]);at=word(at," ");
   u32 value=mm_page==3?(field<2?mm_route_read(params,field):(u32)mm_track_read(lane,field-2)):mm_lfo_read(params,mm_page-1,field);
   if(mm_page==3){
    if(field==1){static const char *const ports[5]={"Global","Off","USB","DIN","Both"};at=word(at,ports[value<=4?value:0]);}
    else if(field==0)at=value==16?word(at,"Global"):number(at,value+1,2);
    else if(field==2){if((i32)value<0){*at++='-';value=0-value;}at=number(at,value,2);}
    else{static const char *const names[12]={"C","C#","D","D#","E","F","F#","G","G#","A","A#","B"};value=value<128?value:60;at=word(at,names[value%12]);if(value<12){*at++='-';*at++='1';}else at=number(at,value/12-1,1);}
   }else if(field==3)at=value==128?word(at,"OFF"):number(at,value,3);
   else at=number(at,(field==1||field==4||field==6)?value:value>>8,3);
   *at=0;text(canvas,mm_page==3?0:64*(field/4),43-10*(field%4),line);
  }
  text(canvas,0,0,"DATA: select  BACK: exit");return 1;
 }
 for(u32 knob=0;knob<12;knob++){
  char *at=number(line,knob+1,2);at=word(at," ");u32 packed=mm_cc_read(params,knob);i32 cc=mm_cc_number(packed);
  at=cc<0?word(at,"OFF"):number(at,(u32)cc,3);at=word(at," ");at=number(at,mm_cc_value(packed),3);*at=0;
  text(canvas,64*(knob/6),44-8*(knob%6),line);
 }
 return 1;
}
