/* Note121 : noms/assignation UI uniquement ; aucun appel depuis le DSP LFO. */
typedef unsigned int u32;
volatile u32 ld_api[4];
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
u32 ld_assign(u32 descriptor){
 u32 key=ld_map_native(descriptor);
 u32 sr;__asm__ volatile("move.w %%sr,%0":"=d"(sr));
 if(!(sr&0x700)&&descriptor<ld_api[3]&&((u32(*)(u32))0x4007faf4)(5)&&((u32(*)(u32))0x4007faf4)(8)){
  if(key==18&&(ld_api[1]&1)){ld_finish();return 23;}
  if(key==13&&(ld_api[1]&2)){ld_finish();return 24;}
  if(key==14&&(ld_api[1]&2)){ld_finish();return 25;}
 }
 return key;
}
