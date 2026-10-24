#include "fx.h"
#ifdef FX_CPU_OPT
/* Geste DX optionnel : tap FUNC (<250ms), second appui sous350ms,
 * maintien500ms puis relachement. Toute autre touche/rotation annule.
 * UI seulement ; le toggle DX sauvegarde reste l unique autorisation. */
static u32 dx_func_stage,dx_func_down,dx_func_stamp,dx_func_release,dx_other_keys;
static void show_diag(void){
 char text[40];u32 average=gr_diag_blocks?(gr_diag_sum/gr_diag_blocks)*100/256:0;
 N(0x40000e6e)(text,"A%u P%u O%u N%u",average,dx_peak/901,dx_over,dx_new);
 N(dx_beat_api[2])(text);dx_peak=dx_over=dx_new=gr_diag_sum=gr_diag_blocks=0;
}
void fx_diag_cancel(void){dx_func_stage=0;}
void fx_diag_gesture(const u32*e){
 u32 code=e[3],flags=e[4],down=flags&1,now=*(volatile u32*)0xfc07000c;
 if(code!=1){
  if(code>1&&code<32&&!(flags&32)){u32 bit=1u<<code;if(down)dx_other_keys|=bit;else dx_other_keys&=~bit;}
  dx_func_stage=0;return;
 }
 u32 prior=dx_func_down;dx_func_down=down;
 /* 0x20 est le maintien long natif, pas une touche synthetique. */
 if(!dx_enabled||menu||fx_menu_open||dx_other_keys||fx_tap_force
#ifndef FX_DX_FUNC_FIX
 ||(flags&32)
#endif
 ){dx_func_stage=0;return;}
 if(down){
  if(!prior&&!(flags&8)){
   dx_func_stage=dx_func_stage==2&&now-dx_func_release<=47308800u?3:1;
   dx_func_stamp=now;
  }
 }else if(prior){
  if(dx_func_stage==1&&now-dx_func_stamp<=33792000u){dx_func_stage=2;dx_func_release=now;}
  else{u32 show=dx_func_stage==3&&now-dx_func_stamp>=67584000u;dx_func_stage=0;if(show)show_diag();}
 }
}
/* Ancien geste reserve au retrig, aucun diagnostic au relachement. */
u32 fx_diag_key(const u32*e){return N(dx_beat_api[0])(e);}
#else
static u32 physical,hold_start,hold_armed,suppressed;
/* Seul un maintien physique de350ms rend le diagnostic eligibile. Aucun
 * changement du diagnostic enable ni des compteurs depuis un geste synthetique. */
u32 fx_diag_key(const u32*e){u32 code=e[3],down=e[4]&1,before_physical=physical,before=*(volatile u32*)dx_beat_api[1];
 if((code==2||code==4)&&!fx_tap_force){u32 bit=code==2?1:2;if(down)physical|=bit;else physical&=~bit;}
 if(physical==3&&before_physical!=3){hold_start=*(volatile u32*)0xfc07000c;hold_armed=1;suppressed=0;}
 u32 result=N(dx_beat_api[0])(e);if(bl_latched)suppressed=1;
 if(dx_enabled&&before==3&&*(volatile u32*)dx_beat_api[1]!=3&&before_physical==3&&physical!=3&&hold_armed&&!suppressed&&!bl_latched&&*(volatile u32*)0xfc07000c-hold_start>=47308800u){
  char text[40];u32 average=gr_diag_blocks?(gr_diag_sum/gr_diag_blocks)*100/256:0;N(0x40000e6e)(text,"A%u P%u O%u N%u",average,dx_peak/901,dx_over,dx_new);N(dx_beat_api[2])(text);dx_peak=dx_over=dx_new=gr_diag_sum=gr_diag_blocks=0;
 }
 if(before_physical==3&&physical!=3)hold_armed=0;return result;
}
#endif
/* Un cran accepte par40ms et par evenement, pas de saut de Wizard. */
static u32 machine_stamp,machine_valid,machine_result;
#ifdef FX_RETROSYN_PRIVATE
#define MACHINE_COUNT 23
#elif defined(FX_LEGACY)
#define MACHINE_COUNT 22
#elif defined(FX_SPEAK)
#define MACHINE_COUNT 21
#else
#define MACHINE_COUNT 20
#endif
u32 fx_machine_step(u32 machine,s32 delta){
#ifdef FX_RETROSYN_PRIVATE
static const u8 order[MACHINE_COUNT]={0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,18,19,20,21,22,17};
#elif defined(FX_LEGACY)
static const u8 order[MACHINE_COUNT]={0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,18,19,20,21,17};
#elif defined(FX_SPEAK)
static const u8 order[MACHINE_COUNT]={0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,18,19,20,17};
#else
static const u8 order[20]={0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,18,19,17};
#endif
u32 pos=0;
 for(u32 i=0;i<MACHINE_COUNT;i++)if(order[i]==machine)pos=i;
 if(!delta)return machine;u32 now=*(volatile u32*)0xfc07000c;
 if(machine_valid&&machine==machine_result&&now-machine_stamp<5406720u)return machine;
 if(delta>0&&pos<MACHINE_COUNT-1)pos++;if(delta<0&&pos)pos--;machine_valid=1;machine_stamp=now;machine_result=order[pos];return machine_result;
}
