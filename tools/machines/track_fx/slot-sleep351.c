/* Activation independante : ne pas reveiller un slot jamais alimente.
 * Les queues natives restent intactes apres leur premiere entree, jusqu au
 * panic. L Eco HALL a sa propre politique de queue courte avec fondu.
 * Les modulations/aux non verifies restent toujours deleguees.
 */
typedef unsigned int u32;typedef int s32;typedef short s16;typedef unsigned short u16;
extern volatile u32 sf_rev,sf_del,sf_panic;
extern void sf_old_reverb(s32*,const s32*,const s16*,const u16*,const s32*,const s32*);
extern void sf_old_delay(s32*,const s32*,const s16*,const s32*,const s32*);
struct state{u32 epoch,mode,warm,alive;};
static struct state slots[2];
#ifdef SF_ECO_DELAY
extern void sf_eco_delay(s32*,const s32*,const s16*,u32),sf_eco_leave(void);
#endif
static u32 asleep(u32 slot,u32 mode,const s32*in){
 struct state*s=&slots[slot];
 if(s->epoch!=sf_panic){s->epoch=sf_panic;s->alive=s->warm=0;s->mode=mode;}
 if(s->mode!=mode){s->mode=mode;s->warm=64;}
 if(slot?(mode!=0&&mode!=5):(mode!=0&&mode!=8&&mode!=11)){s->alive=1;return 0;}
 if(s->alive)return 0;
 u32 energy=0;for(u32 i=0;i<64;i++)energy|=(u32)in[i];
 if(energy){s->alive=1;return 0;}
 if(s->warm){s->warm--;return 0;}
 return 1;
}
void sf_reverb(s32*out,const s32*in,const s16*params,const u16*mix,const s32*dl,const s32*dr){
 if(asleep(0,sf_rev,in)){for(u32 i=0;i<64;i++)out[i]=0;return;}
 sf_old_reverb(out,in,params,mix,dl,dr);
}
void sf_delay(s32*out,const s32*in,const s16*params,const s32*dl,const s32*dr){
#ifdef SF_ECO_DELAY
 if(sf_del==0||sf_del==5){sf_eco_delay(out,in,params,sf_del);return;}
 sf_eco_leave();
#endif
 if(asleep(1,sf_del,in)){for(u32 i=0;i<64;i++)out[i]=0;return;}
 sf_old_delay(out,in,params,dl,dr);
}
