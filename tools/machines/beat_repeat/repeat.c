/* Note 99 : repetition audio collective, uniquement TRACK + RETRIG maintenus.
 * Algorithme inspire de rtg_* de TinyGregAudio (MIT, licence jointe).
 * Aucune allocation dans le rendu, aucun menu ni effet master.
 */
typedef unsigned int u32;
typedef signed int i32;
typedef signed short i16;
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
const u32 br_divs[16]={QN/16,QN/12,QN/8,QN/6,QN/4,QN/3,QN/2,QN*2/3,
 QN*3/4,QN,QN*4/3,QN*3/2,QN*2,QN*8/3,QN*3,QN*4};
static u32 ipl(void){unsigned short sr;__asm__ volatile("move.w %%sr,%0":"=d"(sr));return sr&0x700;}
/* Publication du buffer apres initialisation, uniquement depuis l'UI. */
static int prepare(void){
 if(br_history)return 1;if(ipl())return 0;
 u32 count=(br_side?12:6)*N;
 i16 *p=(i16 *)((u32 (*)(u32))0x400802e0)(count*2);if(!p)return 0;
 for(u32 i=0;i<count;i++)p[i]=0;
 __asm__ volatile("":::"memory");br_history=p;return 1;
}
static void select_held(void){
 u32 newest=0;i32 selected=-1;
 for(u32 i=0;i<16;i++)if(br_held[i]>newest){newest=br_held[i];selected=(i32)i;}
 br_requested=selected;
}
/* Retour 1 : evenement pris. La clef est remplacee par 0 dans le wrapper,
 * donc meme un consommateur lisant directement +12 ne peut editer un pas.
 * Les releases dont le press etait natif restent transmis au natif.
 */
static u32 modifier(u32 code,u32 down,u32 fresh){
  u32 bit=code==TRACK?1:2,old=br_keys;
  if(down)br_keys|=bit;else br_keys&=~bit;
  if(br_keys==3&&old!=3){
   for(u32 i=0;i<16;i++)br_held[i]=0;br_requested=-1;
   br_cancel=0;if(!prepare())br_cancel=1;
  }
  if(br_keys!=3){br_requested=-1;for(u32 i=0;i<16;i++)br_held[i]=0;}
  if(code==RETRIG){
   if(fresh&&(br_keys&1)){br_retrig_owned=1;return 1;}
   if(br_retrig_owned){if(!down)br_retrig_owned=0;return 1;}
  }
  return 0;
}
u32 br_key(u32 *event){
 u32 code=event[3],flags=event[4],down=flags&1,fresh=down&&!(flags&0x28);
 if(code==TRACK||code==RETRIG)return modifier(code,down,fresh);
 if(code<16||code>31)return 0;
 u32 step=code-16,bit=1u<<step;
 if(!down){
  if(!(br_owned&bit))return 0;br_owned&=~bit;br_held[step]=0;select_held();return 1;
 }
 if(br_owned&bit)return 1;
 if(br_keys!=3)return 0;
 /* Un long/repeat d'un press anterieur au combo ne doit pas etre capture. */
 if(!fresh)return 0;
 br_owned|=bit;
 if(!++br_stamp){for(u32 i=0;i<16;i++)br_held[i]=0;br_stamp=1;}
 br_held[step]=br_stamp;select_held();return 1;
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
/* Un echantillon de chacun des six canaux avant gain/envois/mixage. */
static void frame(u32 now,u32 elapsed,u32 phase,u32 envelope,u32 wet){
 u32 record=!br_valid||elapsed<br_length||((elapsed&MASK)>=br_length);
 for(u32 track=0;track<(br_side?12u:6u);track++){
  u32 base=0x80001858,lane=track;
  if(track>=6){lane-=6;if(!((u32 *)br_side_on)[lane])continue;base=br_side;}
  i32 *channel=(i32 *)(base+128*lane+4*(now&31));i32 live=*channel;
  i16 *history=br_history+N*track;
  if(record){i32 q=live>>15;if(q>32767)q=32767;if(q< -32767)q=-32767;history[now&MASK]=(i16)q;}
  if(br_valid&&wet){
   i32 repeated=((i32)history[(br_start+phase)&MASK]*(i32)envelope)>>1;
   /* Difference reduite avant multiplication : arithmetique 32 bits bornee. */
   i32 difference=((repeated>>8)-(live>>8))>>1;
   *channel=(i32)((u32)live+(u32)difference*(wet>>9)*4u);
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
static void render(u32 now,i32 target){
 if(br_valid&&target!=br_active&&br_wet)target=-1;
 else if(!br_valid||target!=br_active)install(target,now);
 if(br_keys!=3&&!br_wet){br_valid=0;br_active=-1;return;}
 u32 wet=br_wet,length=br_length,elapsed=now-br_start;
 u32 phase=br_valid?elapsed%length:0,ramp=length/4;if(ramp>32)ramp=32;if(!ramp)ramp=1;
 u32 scale=65536/ramp;
 for(u32 i=0;i<32;i++){
  if(target>=0&&br_valid){wet+=1024;if(wet>65536)wet=65536;}else wet=wet>1024?wet-1024:0;
  u32 envelope=phase*scale,tail=(length-phase)*scale;
  if(envelope>tail)envelope=tail;if(envelope>65536)envelope=65536;
  frame(now+i,elapsed+i,phase,envelope,wet);
  if(++phase>=length)phase=0;
 }
 br_wet=wet;
}
void br_audio(void){i32 target=target_now();u32 now=br_blocks++<<5;if(br_history)render(now,target);}
