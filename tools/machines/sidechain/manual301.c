/* Correctif live301 : etats DSP existants, aucun changement des reglages. */
typedef unsigned int u32;typedef int s32;typedef unsigned char u8;
extern volatile u8 du_config[6][5],du_fx[6];
extern volatile u32 du_pending,du_enabled;
extern u32 du_follow,initialized,working,gain[6],du_fx_goal[2],du_fx_gain[2],br_side,br_side_on;
extern const u32 du_attack_ms[8],du_hold_ms[4],du_release_ms[16];
struct envelope{u32 level,stage,ticks,step;};extern struct envelope env[6];
extern void du_refresh(void);
static u32 du_live_pending,du_live_active;
void sc_reset(void){du_live_pending=du_live_active=0;du_pending=0;for(u32 i=0;i<6;i++){env[i].level=env[i].stage=0;if(!initialized)gain[i]=65536;}
#ifdef DU_RETURNS
for(u32 i=0;i<2;i++){du_fx_goal[i]=65536;if(!initialized)du_fx_gain[i]=65536;}
#endif
initialized=1;du_refresh();}
void sc_note(u32*e){if(e&&du_enabled&&e[0]==0&&e[1]==1&&e[2]<6&&e[3]!=0xffffffffu&&(e[3]!=1||(e[10]&1))){u32 bit=(1u<<e[2])&du_enabled;du_pending|=bit;if(e[3]!=1)du_live_pending|=bit;}}
void sc_voice(u32 mask){mask&=du_enabled;du_pending|=mask;
#ifdef DU_MUTE
 /* Le masque voix natif arrive APRES le mute sequence ; une voix jouee
  * sur une piste mutee provient donc du jeu live. */
 u32 solo=*(volatile u32*)0x800017b0;du_live_pending|=mask&(solo?~solo:*(volatile u32*)0x800017ac)&du_follow;
#endif
}
static u32 blocks(u32 ms){return (ms*3+1)/2;}
static void release(struct envelope*e,u32 t){e->stage=3;e->ticks=blocks(du_release_ms[du_config[t][4]]);if(!e->ticks)e->ticks=1;e->step=(e->level+e->ticks-1)/e->ticks;}
static u32 advance(u32 t,u32 pulse){
 struct envelope*e=&env[t];u32 target=du_config[t][1]*4369;
 if(pulse){e->ticks=blocks(du_attack_ms[du_config[t][2]]);e->stage=e->ticks?1:2;e->step=e->ticks&&target>e->level?(target-e->level+e->ticks-1)/e->ticks:0;if(!e->ticks){e->level=target;e->ticks=blocks(du_hold_ms[du_config[t][3]]);}}
 if(e->stage==1){if(e->level<target){e->level+=e->step;if(e->level>target)e->level=target;}else e->level=target;if(e->ticks)--e->ticks;if(!e->ticks){e->level=target;e->stage=2;e->ticks=blocks(du_hold_ms[du_config[t][3]]);}}
 else if(e->stage==2){if(e->ticks)--e->ticks;else release(e,t);}
 else if(e->stage==3){e->level=e->level>e->step?e->level-e->step:0;if(e->ticks)--e->ticks;if(!e->ticks)e->level=e->stage=0;}
 return e->level;
}
static s32 multiply(s32 x,u32 g){return (s32)((u32)((x>>16)*(s32)g)+((((u32)x&65535)*g)>>16));}
void sc_process(void){
 if(!du_enabled&&!working){du_live_pending=du_live_active=du_pending=0;return;}if(!initialized)sc_reset();
 u32 pending=du_pending,live=du_live_pending&du_enabled;du_pending=du_live_pending=0;du_live_active=(du_live_active|live)&du_enabled;
#ifdef DU_RETURNS
u32 goals[8]={65536,65536,65536,65536,65536,65536,65536,65536};
#else
u32 goals[6]={65536,65536,65536,65536,65536,65536};
#endif
#ifdef DU_MUTE
 u32 muted=0;if(du_follow){u32 solo=*(volatile u32*)0x800017b0;muted=(solo?~solo:*(volatile u32*)0x800017ac)&du_follow;}
#endif
 for(u32 src=0;src<6;src++)if(du_enabled&(1u<<src)){
#ifdef DU_MUTE
  if(muted&(1u<<src)){pending=(pending&~(1u<<src))|(live&(1u<<src));if(!(du_live_active&(1u<<src))){env[src].level=env[src].stage=env[src].ticks=env[src].step=0;continue;}}
#endif
  u32 amount=advance(src,pending&(1u<<src));if(!env[src].stage)du_live_active&=~(1u<<src);u32 mask=du_config[src][0]&~(1u<<src),want=65536-amount;
  for(u32 dst=0;dst<6;dst++)if((mask&(1u<<dst))&&want<goals[dst])goals[dst]=want;
#ifdef DU_RETURNS
  for(u32 f=0;f<2;f++)if((du_fx[src]&(1u<<f))&&want<goals[6+f])goals[6+f]=want;
#endif
 }
 working=0;
#ifdef DU_RETURNS
 for(u32 f=0;f<2;f++){du_fx_goal[f]=goals[6+f];if(du_fx_goal[f]!=65536||du_fx_gain[f]!=65536)working=1;}
#endif
 for(u32 t=0;t<6;t++){
  u32 before=gain[t],after=goals[t];if(after!=65536)working=1;
  if(before!=65536||after!=65536){
   s32 *mid=(s32*)(0x80001858+128*t),*side=br_side&&((u32*)br_side_on)[t]?(s32*)(br_side+128*t):0;
   s32 delta=(s32)after-(s32)before;
   for(u32 i=0;i<32;i++){u32 g=(u32)((s32)before+((delta*(s32)(i+1))>>5));mid[i]=multiply(mid[i],g);if(side)side[i]=multiply(side[i],g);}
  }gain[t]=after;
 }
}
