/* Note121 : noms/assignation UI uniquement ; aucun appel depuis le DSP LFO. */
typedef unsigned int u32;
volatile u32 ld_api[7];
static u32 ld_map_native(u32 descriptor){return ((u32(*)(u32))0x4005a4e8)(descriptor);}

/* Fermeture differee native : ne detruit pas la vue pendant le dispatch. */
void ld_finish(void){
 if(!*(volatile u32 *)0x40fe4178)return;
 u32 app=((u32(*)(void))0x400d0974)();
 u32 manager=((u32(*)(u32))0x400060d8)(app);
 if(!manager)return;
 u32 head=manager+20,node=*(volatile u32 *)(head+4);
 for(u32 count=0;node&&node!=head&&count<32;count++){
  u32 view=*(volatile u32 *)(node+8);
  if(view&&*(volatile u32 *)view==0x40117920&&!*(volatile unsigned char *)(view+48))
   ((void(*)(u32))0x40076126)(view);
  node=*(volatile u32 *)(node+4);
 }
}
u32 ld_knob(u32 view,u32 knob,u32 func,u32 track){
 u32 result=((u32(*)(u32,u32,u32,u32))ld_api[2])(view,knob,func,track);
 if(((knob==3&&(ld_api[1]&1))||(knob>=4&&knob<=7&&(ld_api[1]&2)))&&((u32(*)(u32))0x4007faf4)(5))ld_finish();
 return result;
}
extern u32 ld_present_native(u32 manager,u32 pair,u32 modal);
u32 ld_present(u32 manager,u32 pair,u32 modal){
 u32 view=pair?*(volatile u32 *)pair:0;
 if(view&&*(volatile u32 *)view!=0x40117920&&((u32(*)(u32))0x4007faf4)(5))ld_finish();
 return ld_present_native(manager,pair,modal);
}
static u32 text(u32 dest){
 if(dest==23&&(ld_api[1]&1))return (u32)"ATK";
 if(dest==24&&(ld_api[1]&2))return (u32)"FLT";
 if(dest==25&&(ld_api[1]&2))return (u32)"RES";
 return 0;
}
u32 ld_first(u32 context,u32 descriptor,u32 unused,u32 dest){
 u32 name=text(dest);return name?name:((u32(*)(u32,u32))0x4000b208)(context,descriptor);
}
u32 ld_second(u32 dest){
 u32 name=text(dest);return name?name:((u32(*)(u32))ld_api[0])(dest);
}
/* Une cible par evenement encodeur ; aucune substitution dans les lectures UI ordinaires. */
volatile u32 ld_target_override;
static u32 quick_target(u32 index){
 u32 machines=((u32(*)(u32))0x4007faf4)(5);
 if(!machines&&((u32(*)(u32))0x4007faf4)(1))return 0xffffffffu;
 if(index==1)return machines&&(ld_api[1]&1)?23:18;
 if(index==4)return machines&&(ld_api[1]&2)?24:13;
 if(index==5)return machines&&(ld_api[1]&2)?25:14;
 return 0xffffffffu;
}
extern u32 ld_primary_quick_native(u32 view,u32 index,u32 delta);
extern u32 ld_secondary_quick_native(u32 index,u32 delta);
u32 ld_primary_quick(u32 view,u32 index,u32 delta){
 u32 saved=ld_target_override,target=quick_target(index);
 ld_target_override=target==0xffffffffu?0:target+1;
 u32 result=ld_primary_quick_native(view,index,delta);
 ld_target_override=saved;return result;
}
u32 ld_secondary_quick(u32 index,u32 delta){
 u32 saved=ld_target_override,target=quick_target(index);
 ld_target_override=target==0xffffffffu?0:target+1;
 u32 result=ld_secondary_quick_native(index,delta);
 ld_target_override=saved;return result;
}
u32 ld_assign(u32 descriptor){
 return ld_target_override?ld_target_override-1:ld_map_native(descriptor);
}

/* Note121 : libelles de RETROSYN seulement ; descripteurs audio conserves. */
const char ld_rs_timbre[]="Timbre",ld_rs_osc[]="Oscillator",ld_rs_sweep[]="Pitch Sweep",ld_rs_arp[]="Chord Arp";
const char ld_rs_timbre_short[]="TIMB",ld_rs_osc_short[]="OSC",ld_rs_sweep_short[]="PSWP",ld_rs_arp_short[]="ARP";

