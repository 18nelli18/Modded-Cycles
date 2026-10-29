/* Machine-specific, note-triggered parameter transients. The sound and locks
 * are never rewritten: only two words in the private audio frame are changed
 * around the native voice call, then restored. No extra oscillators or voices. */
typedef unsigned int u32;typedef int s32;typedef unsigned short u16;
#ifndef PP_UNIQUE
#define PP_UNIQUE 0
#endif
#ifndef PP_REMOVE_LEGACY
#define PP_REMOVE_LEGACY 0
#endif
extern void mf_old_voice_playability(s32*,u16*,u32,u32);
struct recipe {unsigned char a,b,ticks; signed char da,db;};
/* Fields are native parameter slots. Never morph a machine/model selector. */
static const struct recipe recipes[25]={
 {10,11,12,16,20},   /* Kick: pitch knock */
 {11,14,27,24,40},   /* Snare: noise snap */
 {11,13,14,45,18},   /* Metal: bright strike */
 {14,13,21,64,24},   /* Perc: FM thwack */
 {10,14,39,12,-32},  /* Tone: octave pluck */
 {13,11,53,48,24},   /* Chord: chime bloom */
 {10,18,18,-5,-12},  /* Wizard: tape start */
 {13,14,17,36,48},   /* SD Vintage: wire crack */
 {11,13,30,-25,52},  /* Clap Vintage: burst snap */
 {10,11,33,7,64},    /* Toy: fifth chirp */
 {13,11,13,70,-32},  /* Bits: digital snap */
 {10,11,61,-12,38},  /* Swarm: detune burst with a low pitch scoop */
 {11,13,26,60,35},   /* Macro: timbre strike */
 {14,13,83,50,25},   /* Acid: resonant accent */
 {11,13,45,55,25},   /* Wave: scanning pluck */
 {13,11,20,45,-35},  /* Feral: digital bark */
 {10,14,24,24,50},   /* Elder: chip sweep */
 {0,0,0,0,0},       /* MIDI Out: native MIDI controls */
 {11,13,36,38,-25},  /* Tiny: texture nip */
 {11,13,29,-45,65},  /* Shadow: grain snap */
 {11,14,180,50,47},  /* Speak: formant/consonant bite through its leading pause */
 {0,0,0,0,0},       /* Removed Legacy */
 {10,13,22,-12,80},  /* Retrosyn: arcade hit */
 {11,14,9,45,45},    /* Punch: FM hammer */
 {13,11,11,60,35}   /* Estus: transient snap */
};
struct phase {u32 machine,age,on;};static struct phase phase[6];
struct saved {u16 *where,value;};
static void change(struct saved*s,u32*n,u16*p,u32 field,s32 amount,u32 env){
 u16*at=p+field;s32 v=(s32)*at+((amount*256*(s32)env)>>16);
 if(v<0)v=0;if(v>32512)v=32512;
 if(v!=*at){s[*n].where=at;s[*n].value=*at;(*n)++;*at=(u16)v;}
}
void pp_voice_loop(s32*out,u16*frame,u32 trig,u32 release){
 struct saved saved[18];u32 count=0;
 for(u32 t=0;t<6;t++){
  u16*p=frame+7+t*33;u32 machine=p[9]>>8;
  if(PP_REMOVE_LEGACY&&machine==21){saved[count].where=p+9;saved[count++].value=p[9];p[9]=4<<8;machine=4;}
  if(!PP_UNIQUE)continue;
  struct phase*s=&phase[t];u32 on=p[15]!=0;
  if(!on||machine>=25||!recipes[machine].ticks){s->on=0;s->machine=machine;s->age=255;continue;}
  if(!s->on||s->machine!=machine||(trig&(1u<<t)))s->age=0;
  s->on=1;s->machine=machine;const struct recipe*r=recipes+machine;
  if(s->age<r->ticks){u32 env=65536u-(s->age*65536u)/r->ticks;change(saved,&count,p,r->a,r->da,env);change(saved,&count,p,r->b,r->db,env);s->age++;}
 }
 mf_old_voice_playability(out,frame,trig,release);
 while(count){count--;*saved[count].where=saved[count].value;}
}
