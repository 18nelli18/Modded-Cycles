/* Adaptation UI PPPCCC : aucun E/S ni changement des donnees du sequenceur. */
typedef unsigned int u32;typedef unsigned char u8;
#define N(a) ((u32(*)())(a))
extern volatile u32 ts_on;
extern u32 ui_header(void),pt_length(const u8*,u32);
extern void fx_notice(const char*);
/* Meme portee PTN/TRK que Page Len ; les trigs caches ne deviennent pas editables. */
u32 ts_page_length(void){
 u32 object=ui_header();if(!object)return 16;u32 vt=*(u32*)object;if(!vt)return 16;
 u8*h=(u8*)N(*(u32*)(vt+40))(object);if(!h)return 16;
 u32 root=N(0x400cf866)(),t=root?N(0x40012412)(N(0x4000eb90)(root)):0;return pt_length(h,t);
}
u32 ts_allowed(u32 step){return step<64&&(step&15)<ts_page_length();}
u32 ts_has_note(u32 track,u32 step){return ts_allowed(step)?N(0x40015c20)(track,step):0;}
u32 ts_has_lock(u32 track,u32 step){return ts_allowed(step)?N(0x40015c7c)(track,step):0;}
u32 ts_has_plock(u32 track,u32 step){return ts_allowed(step)?N(0x400158ca)(track,step):0;}
void ts_notice(const char*value){
 const char*text=value&&value[0]=='A'?"Trig Select All":value&&value[0]=='N'?"Trig Select None":value&&value[1]=='n'?"Trig Select ON":"Trig Select OFF";fx_notice(text);
}
u32 ts_led_value(u32 step){
 if(ts_on!=0x5453454c||step>=64)return 0;
 u32 ui=N(0x400cf9a8)();if(!ui||!N(0x4006b7a0)(ui,step)||!ts_allowed(step))return 0;
 return (*(volatile u32*)0xfc07000c&(1u<<24))?2:1;
}
