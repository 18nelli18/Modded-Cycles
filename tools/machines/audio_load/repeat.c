/* Note 112 : diagnostic CPU/CUT ; DSP repeat principal conserve.
 * Note 99 : repetition audio collective, uniquement TRACK + RETRIG maintenus.
 * Algorithme inspire de rtg_* de TinyGregAudio (MIT, licence jointe).
 * Aucune allocation dans le rendu, aucun menu ni effet master.
 */
typedef unsigned int u32;
typedef signed int i32;
typedef signed short i16;
typedef unsigned char u8;
#define STATE __attribute__((section(".br_state")))
#define N 131072u
#define MASK (N-1)
#define TRACK 2u
#define RETRIG 4u
#define QN 21600000u
volatile u32 br_keys STATE=0,br_cancel STATE=0;
u32 br_owned STATE=0,br_retrig_owned STATE=0;
u32 br_stamp STATE=0,br_held[16] STATE={0};
volatile i32 br_requested STATE=-1;
i32 br_active STATE=-1;
i16 *volatile br_history STATE=0;
u32 br_blocks STATE=0,br_bar STATE=0,br_pstep STATE=0,br_pattern STATE=0;
u32 br_valid STATE=0,br_start STATE=0,br_length STATE=0,br_wet STATE=0;
u32 br_old_key STATE=0,br_old_gain STATE=0x40056d9c;
u32 br_side STATE=0,br_side_on STATE=0;
u32 br_mask_address STATE=0,br_excluded STATE=0,br_lane_wet[6] STATE={0};
u32 br_old_track_keys STATE=0,br_old_track_leds STATE=0;
u32 br_filter_f_address STATE=0,br_filter_q_address STATE=0,br_filter_mk_address STATE=0,br_filter_modes_address STATE=0,br_function STATE=0;
u32 br_load_address STATE=0,br_avg_address STATE=0,br_load_peak STATE=0;
u32 br_fading_address STATE=0,br_stolen_address STATE=0,br_cut_seen STATE=0;
const u32 br_divs[16]={QN/16,QN/12,QN/8,QN/6,QN/4,QN/3,QN/2,QN*2/3,
 QN*3/4,QN,QN*4/3,QN*3/2,QN*2,QN*8/3,QN*3,QN*4};
static u32 ipl(void){unsigned short sr;__asm__ volatile("move.w %%sr,%0":"=d"(sr));return sr&0x700;}
static void repaint(void){u32 app=*(volatile u32 *)0x40fe4178;if(app)((void (*)(u32))0x40076c04)(app+64);}
/* Publication du buffer apres initialisation, uniquement depuis l'UI. */
static int prepare(void){
 if(br_history)return 1;if(ipl())return 0;
 u32 count=(br_side?12:6)*N;
 i16 *p=(i16 *)((u32 (*)(u32))0x400802e0)(count*2);if(!p)return 0;
 for(u32 i=0;i<count;i++)p[i]=0;
 __asm__ volatile("":::"memory");br_history=p;return 1;
}
extern void br_popup(const char *text);
static char *load_percent(char *p,u32 q){
 u32 v=q>2557?999:q*100/256;
 if(v>=100)*p++='0'+v/100;
 if(v>=10)*p++='0'+v/10%10;
 *p++='0'+v%10;*p++='%';return p;
}
/* Snapshot UI piste 6 ; lecture seule, aucun calcul audio ajoute. */
static char *filter_number(char *p,u32 v){
 if(v>99999){*p++='?';return p;}
 u32 d=10000;while(d>1&&v<d)d/=10;
 do{*p++='0'+v/d;v%=d;d/=10;}while(d);return p;
}
static void filter_popup(void){
 char text[32],*p=text;
 if(!br_filter_f_address||!br_filter_modes_address){br_popup("FILTER OFF");return;}
 *p++='6';*p++=' ';*p++='F';p=filter_number(p,((volatile u32 *)br_filter_f_address)[5]);
 *p++=' ';*p++='Q';p=filter_number(p,((volatile u32 *)br_filter_q_address)[5]);
 *p++=' ';*p++='K';p=filter_number(p,((volatile u32 *)br_filter_mk_address)[5]);
 *p++=' ';*p++='M';u32 mode=((volatile u32 *)br_filter_modes_address)[5];
 for(i32 shift=12;shift>=0;shift-=4)*p++="0123456789ABCDEF"[(mode>>shift)&15];
 *p=0;br_popup(text);
}
static void load_popup(void){
 if(!br_load_address||!br_avg_address||ipl())return;
 if(br_function){filter_popup();return;}
 char text[32],*p=text;*p++='C';*p++='P';*p++='U';*p++=' ';
 p=load_percent(p,*(volatile u32 *)br_avg_address);*p++='/';
 p=load_percent(p,br_load_peak);
 if(br_fading_address&&br_stolen_address){
  u32 count=0;for(u32 i=0;i<6;i++)count+=(br_cut_seen>>i)&1;
  *p++=' ';*p++='C';*p++='U';*p++='T';*p++=' ';*p++='0'+count;
 }
 *p=0;br_popup(text);
}
static const char *const labels[16]={"1/64","1/48","1/32","1/24","1/16","1/12","1/8","1/6","3/16","1/4","1/3","3/8","1/2","2/3","3/4","1 BAR"};
static void select_held(void){
 i32 previous=br_requested;
 u32 newest=0;i32 selected=-1;
 for(u32 i=0;i<16;i++)if(br_held[i]>newest){newest=br_held[i];selected=(i32)i;}
 br_requested=selected;
 /* Feedback UI seulement sur changement actif, jamais depuis le rendu. */
 if(selected>=0&&selected!=previous&&br_keys==3&&!br_cancel&&!ipl())br_popup(labels[selected]);
}
/* Retour 1 : evenement pris. La clef est remplacee par 0 dans le wrapper,
 * donc meme un consommateur lisant directement +12 ne peut editer un pas.
 * Les releases dont le press etait natif restent transmis au natif.
 */
static u32 modifier(u32 code,u32 down,u32 fresh){
  u32 bit=code==TRACK?1:2,old=br_keys;
  if(down)br_keys|=bit;else br_keys&=~bit;
  if(old!=br_keys)repaint();
  if(br_keys==3&&old!=3){
   for(u32 i=0;i<16;i++)br_held[i]=0;br_requested=-1;
   br_cancel=0;br_load_peak=0;br_cut_seen=0;if(!prepare())br_cancel=1;
  }
  if(old==3&&br_keys!=3)load_popup();
  if(br_keys!=3){br_requested=-1;for(u32 i=0;i<16;i++)br_held[i]=0;}
  if(code==RETRIG){
   if(fresh&&(br_keys&1)){br_retrig_owned=1;return 1;}
   if(br_retrig_owned){if(!down)br_retrig_owned=0;return 1;}
  }
  return 0;
}
u32 br_key(u32 *event){
 u32 code=event[3],flags=event[4],down=flags&1,fresh=down&&!(flags&0x28);
 if(code==1){br_function=down;return 0;}
 if(code==TRACK||code==RETRIG)return modifier(code,down,fresh);
 if(code<16||code>31)return 0;
 u32 step=code-16,bit=1u<<step;
 if(!down){
  if(!(br_owned&bit))return 0;br_owned&=~bit;br_held[step]=0;select_held();repaint();return 1;
 }
 if(br_owned&bit)return 1;
 if(br_keys!=3)return 0;
 /* Un long/repeat d'un press anterieur au combo ne doit pas etre capture. */
 if(!fresh)return 0;
 br_owned|=bit;
 if(!++br_stamp){for(u32 i=0;i<16;i++)br_held[i]=0;br_stamp=1;}
 br_held[step]=br_stamp;select_held();repaint();return 1;
}
/* La vue TRACK reserve les seize LEDs aux divisions tant que le combo tient.
 * Sa selection Control All normale est restauree par le wrapper a la sortie.
 */
void br_leds(u32 view,u32 available,u32 *out){
 (void)view;(void)available;
 u32 leds=((u32 (*)(void))0x400cfaf4)();
 for(u32 i=0;i<16;i++)((void (*)(u32,u32,u32,u32))0x40005f86)(leds,i+1,br_requested==(i32)i?2:1,0x404a8c68);
 *out|=0x1fffe;
}
/* Installer la derniere ligne de grille avant le geste, longueur reduite
 * par puissances de deux si le tempo lent depasse l'historique disponible.
 */
static void install(i32 target,u32 now){
 br_valid=0;br_active=target;if(target<0)return;
 u32 tempo=*(volatile u32 *)0x40149310;if(!tempo)return;
 u32 division=br_divs[target],length;
 do{length=(division<<4)/tempo;if(length>N-4096)division>>=1;else break;}while(division);
 if(!length||!division)return;
 u32 clock=*(volatile u32 *)0x8000184c-br_bar;
 u32 elapsed=((clock%division)<<4)/tempo;
 br_start=now-elapsed;br_length=length;br_valid=1;
}
/* Trajectoire commune aux voies, calculee une seule fois par bloc. */
struct br_frame {u32 phase,envelope,wet,record;};
static void render_channel(i32 *channel,i16 *history,u32 now,
 const struct br_frame *frames,const u32 *mix){
 u32 valid=br_valid,start=br_start;
 for(u32 i=0;i<32;i++){
  i32 live=channel[i];
  if(frames[i].record){
   i32 q=live>>15;if(q>32767)q=32767;if(q< -32767)q=-32767;
   history[(now+i)&MASK]=(i16)q;
  }
  if(valid&&mix[i]){
   i32 repeated=((i32)history[(start+frames[i].phase)&MASK]*(i32)frames[i].envelope)>>1;
   i32 difference=((repeated>>8)-(live>>8))>>1;
   channel[i]=(i32)((u32)live+(u32)difference*(mix[i]>>9)*4u);
  }
 }
}
/* Regimes etablis : ni table de mix par sample, ni multiplication variable.
 * Le chemin plein conserve exactement les bits bas du live comme auparavant.
 */
static void render_full(i32 *channel,i16 *history,u32 now,const struct br_frame *frames){
 u32 start=br_start;
 for(u32 i=0;i<32;i++){
  i32 live=channel[i];
  if(frames[i].record){i32 q=live>>15;if(q>32767)q=32767;if(q< -32767)q=-32767;history[(now+i)&MASK]=(i16)q;}
  i32 repeated=((i32)history[(start+frames[i].phase)&MASK]*(i32)frames[i].envelope)>>1;
  i32 difference=((repeated>>8)-(live>>8))>>1;
  channel[i]=(i32)((u32)live+((u32)difference<<9));
 }
}
static void render_dry(i32 *channel,i16 *history,u32 now,const struct br_frame *frames){
 for(u32 i=0;i<32;i++)if(frames[i].record){
  i32 q=channel[i]>>15;if(q>32767)q=32767;if(q< -32767)q=-32767;history[(now+i)&MASK]=(i16)q;
 }
}
static void render_mode(i32 *channel,i16 *history,u32 now,const struct br_frame *frames,const u32 *mix,u32 mode){
 if(mode==1)render_full(channel,history,now,frames);
 else if(mode==2)render_dry(channel,history,now,frames);
 else render_channel(channel,history,now,frames,mix);
}
/* Plateau plein : phase et bornes circulaires sont deja communes au bloc.
 * Conserver les bits bas du live ; conversion/arrondi strictement identiques.
 */
static void render_plain(i32 *channel,i16 *write,i16 *read,u32 record){
 if(record)for(u32 i=0;i<32;i++){
  i32 live=channel[i],q=live>>15;
  if(q>32767)q=32767;if(q< -32767)q=-32767;write[i]=(i16)q;
  i32 residual=(i32)(((u32)live&511u)^256u)-256;
  channel[i]=(i32)read[i]*32768+residual;
 }
 else for(u32 i=0;i<32;i++){
  i32 live=channel[i],residual=(i32)(((u32)live&511u)^256u)-256;
  channel[i]=(i32)read[i]*32768+residual;
 }
}
static void render_tracks(u32 now,const struct br_frame *frames){
 u32 mix[32],cached=0,cached_local=0,cached_excluded=0,cached_end=0;
 u32 write=now&MASK,read=(br_start+frames[0].phase)&MASK;
 u32 plain=br_length>=32&&frames[0].envelope==65536&&frames[31].envelope==65536
  &&frames[31].phase==frames[0].phase+31&&frames[0].record==frames[31].record
  &&write<=N-32&&read<=N-32;
 for(u32 lane=0;lane<6;lane++){
  u32 local=br_lane_wet[lane],excluded=!!(br_excluded&(1u<<lane));
  u32 mode=local==0&&(excluded||(frames[0].wet==0&&frames[31].wet==0))?2:
   (local==65536&&!excluded&&frames[0].wet==65536&&br_valid?1:0);
  if(!mode){
   if(cached&&local==cached_local&&excluded==cached_excluded)local=cached_end;
   else{
    cached=1;cached_local=local;cached_excluded=excluded;
    for(u32 i=0;i<32;i++){
     u32 goal=excluded?0:frames[i].wet;
     if(local<goal){local+=1024;if(local>goal)local=goal;}
     else if(local>goal)local=local-goal>1024?local-1024:goal;
     mix[i]=local;
    }
    cached_end=local;
   }
  }
  br_lane_wet[lane]=local;
  i32 *channel=(i32 *)(0x80001858+128*lane);i16 *history=br_history+N*lane;
  if(mode==1&&plain)render_plain(channel,history+write,history+read,frames[0].record);
  else if(!(mode==2&&plain&&!frames[0].record))render_mode(channel,history,now,frames,mix,mode);
  if(br_side&&((u32 *)br_side_on)[lane]){
   channel=(i32 *)(br_side+128*lane);history=br_history+N*(lane+6);
   if(mode==1&&plain)render_plain(channel,history+write,history+read,frames[0].record);
   else if(!(mode==2&&plain&&!frames[0].record))render_mode(channel,history,now,frames,mix,mode);
  }
 }
}
/* Une fois par bloc, avant le gain natif. Aucun effet sur les retours FX,
 * les donnees de pattern, les notes MIDI ou les parametres des machines.
 */
static i32 target_now(void){
 u32 pattern=*(volatile u32 *)0x40a78888;
 if(br_pattern&&br_pattern!=pattern)br_cancel=1;br_pattern=pattern;
 u32 step=*(volatile u32 *)0x40a78840;
 if(step==1&&br_pstep!=1)br_bar=*(volatile u32 *)0x40a78628;br_pstep=step;
 u32 playing=*(volatile u32 *)0x40a7883c==1;
 if(!playing)br_cancel=1;
 return br_keys==3&&!br_cancel&&playing?br_requested:-1;
}
/* Combo tenu sans division : historique seulement, aucune interpolation.
 * Ordre piste/sample pour lire chaque bloc contigu ; quantification identique.
 */
static void record_block(u32 now){
 for(u32 track=0;track<(br_side?12u:6u);track++){
  u32 lane=track,base=0x80001858;
  if(track>=6){lane-=6;if(!((u32 *)br_side_on)[lane])continue;base=br_side;}
  i32 *channel=(i32 *)(base+128*lane);
  i16 *history=br_history+N*track+(now&MASK);
  for(u32 i=0;i<32;i++){
   i32 q=channel[i]>>15;if(q>32767)q=32767;if(q< -32767)q=-32767;
   history[i]=(i16)q;
  }
 }
}
/* Eviter la trajectoire intermediaire quand toutes les voies sont deja
 * etablies et que le bloc ne traverse ni enveloppe ni bord circulaire.
 * Aucune ecriture avant validation complete des six fades.
 */
static u32 render_plain_block(u32 now,i32 target){
 if(!br_valid||target<0||target!=br_active||br_wet!=65536)return 0;
 u32 length=br_length,elapsed=now-br_start,phase=elapsed%length;
 u32 ramp=length/4;if(ramp>32)ramp=32;if(!ramp)ramp=1;
 u32 scale=65536/ramp,edge=(65536+scale-1)/scale;
 if(phase<edge||length-phase<31+edge)return 0;
 u32 record=elapsed<length||((elapsed&MASK)>=length);
 u32 last=elapsed+31,last_record=last<length||((last&MASK)>=length);
 u32 write=now&MASK,read=(br_start+phase)&MASK;
 if(record!=last_record||write>N-32||read>N-32)return 0;
 for(u32 lane=0;lane<6;lane++)
  if(br_lane_wet[lane]!=(br_excluded&(1u<<lane)?0u:65536u))return 0;
 for(u32 track=0;track<(br_side?12u:6u);track++){
  u32 lane=track<6?track:track-6;
  if(track>=6&&!((u32 *)br_side_on)[lane])continue;
  i32 *channel=(i32 *)((track<6?0x80001858:br_side)+128*lane);
  i16 *history=br_history+N*track;
  if(!(br_excluded&(1u<<lane)))render_plain(channel,history+write,history+read,record);
  else if(record)for(u32 i=0;i<32;i++){
   i32 q=channel[i]>>15;if(q>32767)q=32767;if(q< -32767)q=-32767;
   history[write+i]=(i16)q;
  }
 }
 return 1;
}
static void render(u32 now,i32 target){
 if(br_valid&&target!=br_active&&br_wet)target=-1;
 else if(!br_valid||target!=br_active)install(target,now);
 if(br_keys!=3&&!br_wet){br_valid=0;br_active=-1;return;}
 if(!br_valid&&!br_wet){
  u32 lanes=0;for(u32 i=0;i<6;i++)lanes|=br_lane_wet[i];
  if(!lanes){record_block(now);return;}
 }
 if(render_plain_block(now,target))return;
 u32 wet=br_wet,length=br_length,elapsed=now-br_start;
 u32 phase=br_valid?elapsed%length:0,ramp=length/4;if(ramp>32)ramp=32;if(!ramp)ramp=1;
 u32 scale=65536/ramp;struct br_frame frames[32];
 for(u32 i=0;i<32;i++){
  if(target>=0&&br_valid){wet+=1024;if(wet>65536)wet=65536;}else wet=wet>1024?wet-1024:0;
  u32 envelope=phase*scale,tail=(length-phase)*scale;
  if(envelope>tail)envelope=tail;if(envelope>65536)envelope=65536;
  frames[i].phase=phase;frames[i].envelope=envelope;frames[i].wet=wet;
  u32 age=elapsed+i;frames[i].record=!br_valid||age<length||((age&MASK)>=length);
  if(++phase>=length)phase=0;
 }
 render_tracks(now,frames);br_wet=wet;
}
void br_audio(void){if(br_load_address&&br_keys==3){u32 load=*(volatile u32 *)br_load_address;if(load>br_load_peak)br_load_peak=load;
 /* Observer seulement : aucun flag du regulateur n est modifie. */
 if(br_fading_address&&br_stolen_address)for(u32 i=0;i<6;i++)
  if(((volatile u8 *)br_fading_address)[i]||((volatile u8 *)br_stolen_address)[i])br_cut_seen|=1u<<i;
 }i32 target=target_now();u32 now=br_blocks++<<5;br_excluded=br_mask_address?*(volatile u8 *)br_mask_address:0;if(br_history)render(now,target);}
