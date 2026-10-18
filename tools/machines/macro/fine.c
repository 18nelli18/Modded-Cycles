/* FINE17 reste lo-fi. Reglage fin dans la fraction native de PITCH10 :
 * deux unites8.8 =1/128demi-ton, resolution utilisee par Braids.
 * UI seule ; aucun changement de synthese ou du format de son.
 */
typedef unsigned int u32;
typedef signed int i32;
volatile u32 mf_api[5] __attribute__((section(".data")))={0,0,0,0,0};
static u32 saved[4] __attribute__((section(".data")))={0,0,0,0};
static u32 settings_raw __attribute__((section(".data")))=0;
static u32 used __attribute__((section(".data")))=0;
extern void mf_draw(void);
u32 mf_active(void){
 u32 root=((u32 (*)(void))0x400cf866)();if(!root)return 0;
 u32 lane=((u32 (*)(u32))0x40012412)(root+48);
 return lane<6&&((u32 (*)(u32,u32))0x4001e318)(0,lane)==mf_api[0];
}
static u32 fine_held(void){return (settings_raw||(mf_api[4]?*(volatile u32 *)mf_api[4]:((u32 (*)(u32))0x4007faf4)(13)))&&!((u32 (*)(u32))0x4007faf4)(1);}
static u32 step(u32 context,i32 value,i32 delta,i32 lo,i32 hi,u32 which){
 if(!mf_active())return ((u32 (*)(u32,i32,i32,i32,i32))saved[which])(context,value,delta,lo,hi);
 i32 result;
 if(fine_held()){
  if(delta>32767)delta=32767;
  if(delta < -32767)delta=-32767;
  i32 turns=delta<0?-((-delta+255)>>8):(delta+255)>>8;
  result=value+2*turns;used=1;
  if(mf_api[1])*(volatile u32 *)mf_api[1]=1;
 }else{
  result=(i32)((u32 (*)(u32,i32,i32,i32,i32))saved[which])(context,value&~255,delta,lo,hi)+(value&255);
 }
 if(result<lo)result=lo;
 if(result>hi)result=hi;
 return (u32)result;
}
u32 mf_step(u32 context,i32 value,i32 delta,i32 lo,i32 hi){return step(context,value,delta,lo,hi,0);}
u32 mf_step_fine(u32 context,i32 value,i32 delta,i32 lo,i32 hi){return step(context,value,delta,lo,hi,1);}
u32 mf_fmt(u32 context,u32 value,char *out){
 if(!mf_active())return ((u32 (*)(u32,u32,char *))saved[2])(context,value,out);
 i32 offset=(i32)value-16384;u32 magnitude=offset<0?(u32)-offset:(u32)offset;
 return ((u32 (*)(char *,const char *,...))0x40000e6e)(out,"%s%d.%03d",offset<0?"-":"+",magnitude>>8,((magnitude&255)*1000+128)>>8);
}
u32 mf_original_draw(void){return saved[3];}
void mf_prepare(u32 machine,u32 knob,u32 func){
 if(machine!=mf_api[0]||knob!=2||func)return;
 volatile u32 *record=(volatile u32 *)(0x40a71754+42*100);
 if(!saved[0]){saved[0]=record[19];saved[1]=record[20];saved[2]=record[8];saved[3]=record[12];}
 record[19]=(u32)mf_step;record[20]=(u32)mf_step_fine;record[8]=(u32)mf_fmt;record[12]=(u32)mf_draw;
}
u32 mf_key(const u32 *event){
 if(!event||event[3]!=13)return 0;
 settings_raw=(event[4]&1)!=0;
 if(event[4]&1){if(!(event[4]&8))used=0;return 0;}
 if(!used)return 0;
 used=0;return mf_api[1]?0:1;
}

/* Le potard ordinaire passe par vt[20], pas par le callback fine du descripteur.
 * Intercepter seulement PITCH MACRO sous SETTINGS ; deleguer tout le reste. */
u32 mf_edit_native(u32 object,u32 descriptor,i32 value,i32 delta,u32 original){
 if(descriptor!=42||!mf_active()||!fine_held())
  return ((u32 (*)(u32,u32,i32,i32))original)(object,descriptor,value,delta);
 i32 turns=delta<0?-((-delta+255)>>8):(delta+255)>>8;
 i32 result=value+2*turns;
 if(result<(40<<8))result=40<<8;
 if(result>(88<<8))result=88<<8;
 used=1;if(mf_api[1])*(volatile u32 *)mf_api[1]=1;
 return (u32)result;
}
