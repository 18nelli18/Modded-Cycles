/* Note121 : noms/assignation UI uniquement ; aucun appel depuis le DSP LFO. */
typedef unsigned int u32;
volatile u32 ld_api[9];
static u32 ld_map_native(u32 descriptor){return ((u32(*)(u32))0x4005a4e8)(descriptor);}
static u32 context_for(u32 secondary){
 u32 kit=((u32(*)(void))0x400cf866)();
 if(!kit)return 0;
 u32 track=secondary&&ld_api[7]?*(volatile u32 *)ld_api[7]:((u32(*)(u32))0x40012412)(kit+48);
 if(track>5)return 0;
 return ((u32(*)(u32,u32))0x400097f0)(kit+116,track);
}
static u32 wizard(u32 context){
 if(!ld_api[8]||!context||*(volatile u32 *)context!=0x400fd134)return 0;
 u32 handle=*(volatile u32 *)(context+4);
 if(!handle)return 0;
 u32 vt=*(volatile u32 *)handle;
 if(!vt)return 0;
 u32 raw=((u32(*)(u32))*(volatile u32 *)(vt+40))(handle);
 return raw&&*(volatile unsigned char *)(raw+38)==6;
}
/* Les noms partages sont reecrits pendant les recherches de potards d'autres machines.
   Resoudre le nom avec le vrai contexte de son, y compris pendant le popup encodeur. */
static u32 parameter_name(u32 context,u32 descriptor,u32 offset){
 u32 index=descriptor<ld_api[3]?descriptor:0;
 u32 record=*(volatile u32 *)0x4005a4f4+56*index;
 if(wizard(context)){
  u32 key=*(volatile u32 *)(record+4);
  if(key==13)return offset==52?(u32)"FLT":(u32)"Filter";
  if(key==14)return offset==52?(u32)"RES":(u32)"Resonance";
 }
 return *(volatile u32 *)(record+offset);
}
u32 ld_short(u32 context,u32 descriptor){return parameter_name(context,descriptor,52);}
u32 ld_long(u32 context,u32 descriptor){return parameter_name(context,descriptor,44);}

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
 if(wizard(context)){
  if(dest==13)return (u32)"FLT";
  if(dest==14)return (u32)"RES";
  if(dest==24||dest==25)return (u32)"ERR";
 }
 u32 name=text(dest);return name?name:((u32(*)(u32,u32))0x4000b208)(context,descriptor);
}
u32 ld_second(u32 dest){
 if(wizard(context_for(1))){
  if(dest==13)return (u32)"FLT";
  if(dest==14)return (u32)"RES";
  if(dest==24||dest==25)return (u32)"ERR";
 }
 u32 name=text(dest);return name?name:((u32(*)(u32))ld_api[0])(dest);
}
/* Une cible par evenement encodeur ; aucune substitution dans les lectures UI ordinaires. */
volatile u32 ld_target_override;
static u32 quick_target(u32 index,u32 secondary){
 u32 machines=((u32(*)(u32))0x4007faf4)(5);
 if(!machines&&((u32(*)(u32))0x4007faf4)(1))return 0xffffffffu;
 if(index==1)return machines&&(ld_api[1]&1)?23:18;
 /* Wizard possede deja son filtre sur les cles natives13/14. */
 if((index==4||index==5)&&wizard(context_for(secondary)))return index==4?13:14;
 if(index==4)return machines&&(ld_api[1]&2)?24:13;
 if(index==5)return machines&&(ld_api[1]&2)?25:14;
 return 0xffffffffu;
}
extern u32 ld_primary_quick_native(u32 view,u32 index,u32 delta);
extern u32 ld_secondary_quick_native(u32 index,u32 delta);
u32 ld_primary_quick(u32 view,u32 index,u32 delta){
 u32 saved=ld_target_override,target=quick_target(index,0);
 ld_target_override=target==0xffffffffu?0:target+1;
 u32 result=ld_primary_quick_native(view,index,delta);
 ld_target_override=saved;return result;
}
u32 ld_secondary_quick(u32 index,u32 delta){
 u32 saved=ld_target_override,target=quick_target(index,1);
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

