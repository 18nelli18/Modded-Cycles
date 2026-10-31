/* Parcours silencieux : aucune ecriture sonore avant clic DATA.
 * Le commit utilise le meme chemin natif que Stk, snapshots inclus. */
typedef unsigned int u32;typedef int s32;typedef unsigned char u8;
#define N(a) ((u32(*)())(a))
extern const u8 rm_order[];extern const u32 rm_count;
extern u32 mb_native_rotate(u32,s32,u32,u32),mb_native_key(u32,const u32*);
extern u32 rm_machine_valid,rm_machine_stamp,rm_machine_result;
extern void fx_notice(const char*);
volatile u32 mb_silent=1,mb_pending,mb_candidate,mb_lane,mb_all,mb_view;
static u32 committing,owned;
static void redraw(void){u32 app=*(volatile u32*)0x40fe4178;if(app)N(0x40076bee)(app+64);}
void mb_cancel(void){mb_pending=committing=0;}
u32 mb_step(u32 machine,s32 delta){
 if(committing)return mb_candidate;
 if(machine==21)machine=4;u32 pos=0;for(u32 i=0;i<rm_count;i++)if(rm_order[i]==machine)pos=i;
 if(!delta)return rm_order[pos];u32 now=*(volatile u32*)0xfc07000c;
 if(rm_machine_valid&&machine==rm_machine_result&&now-rm_machine_stamp<5406720u)return machine;
 if(delta>0&&pos+1<rm_count)pos++;if(delta<0&&pos)pos--;
 rm_machine_valid=1;rm_machine_stamp=now;return rm_machine_result=rm_order[pos];
}
u32 mb_rotate(u32 view,s32 delta,u32 all,u32 arg){
 if(!mb_silent){mb_cancel();return mb_native_rotate(view,delta,all,arg);}
 if(!delta)return 0;u32 root=N(0x400cf866)(),track=root?N(0x40012412)(root+48):6;if(track>=6)return 0;
 if(!mb_pending||mb_lane!=track||mb_view!=view){mb_candidate=N(0x4001e318)(0,track);mb_lane=track;mb_view=view;}
 u32 pos=0;for(u32 i=0;i<rm_count;i++)if(rm_order[i]==mb_candidate)pos=i;
 if(delta>0&&pos+1<rm_count)pos++;if(delta<0&&pos)pos--;mb_candidate=rm_order[pos];mb_all=all;mb_pending=1;redraw();
 return 0;
}
u32 mb_key(u32 view,const u32*e){
 if(!e)return mb_native_key(view,e);u32 code=N(0x4007240c)(e),flags=e[4];
 if(code==32&&(mb_pending||owned)){
  if((flags&9)==1){owned=1;if(mb_pending&&view==mb_view){u32 root=N(0x400cf866)(),track=root?N(0x40012412)(root+48):6;if(track==mb_lane){committing=1;mb_native_rotate(view,1,mb_all,0);committing=0;}mb_pending=0;redraw();}}
  if(!(flags&1))owned=0;return 1;
 }
 if((flags&9)==1&&(code==12||code==5||(code>=16&&code<22)))mb_cancel();
 return mb_native_key(view,e);
}

/* Le dessinateur natif recoit seulement l ID a afficher ; aucun son ecrit. */
u32 mb_display_machine(u32 machine,u32 view){return mb_pending&&view==mb_view?mb_candidate:machine;}
