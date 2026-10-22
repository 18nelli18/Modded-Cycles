/* DX : diagnostic P/O/N optionnel, OFF par defaut. Le menu et les E/S
 * disque sont UI ; l'audio lit seulement le drapeau et ses compteurs. */
typedef unsigned int u32;typedef unsigned char u8;
extern volatile u32 row,menu,wf_stock,lm_enabled,dl_enabled;
extern volatile u32 wf_api[];
extern u32 wf_menu_edit(void),wf_usb_set(u32);
volatile u32 dx_enabled;
volatile u32 dx_peak,dx_over,dx_new,dx_before_mask;
/* Cle repeat, masque des touches et entree COMPLETE du popup selon variante. */
volatile u32 dx_beat_api[3] __attribute__((section(".data")))={0};
static void repaint(void){u32 app=*(volatile u32*)0x40fe4178;if(app)((void(*)(u32))0x40076bee)(app+64);}
void dx_set(u32 on){
 u32 sr;__asm__ volatile("move.w %%sr,%0\nmove.w #0x2700,%%sr":"=d"(sr)::"memory","cc");
 dx_enabled=0;dx_peak=dx_over=dx_new=dx_before_mask=0;dx_enabled=!!on;
 __asm__ volatile("move.w %0,%%sr"::"d"(sr):"memory","cc");
}
u32 dx_encoder(const u32 *e){
 if(!menu||!e||e[0]!=0x400fbebcu)return 0;
 if(e[3]!=1)return 1;
 int d=((int(*)(const u32*,u32,u32))0x4006f73a)(e,1,1);if(!d)return 1;
 if(!wf_menu_edit())row=(row+(d>0?1:5))%6;
 else if(row==5)dx_set(d>0);
 else if(row==4)dl_enabled=d>0;
 else if(row==3)lm_enabled=d>0;
 else if(row==2&&wf_api[8])*(volatile u8*)wf_api[8]=d>0?0:1;
 else if(row==1)wf_usb_set(d>0);
 else if(!row)wf_stock=d>0;
 repaint();return 1;
}
void dx_menu_value(u32 selected,u32 item,u32 canvas,u32 x,u32 y){
 (void)selected;(void)item;
 ((void(*)())0x40071a04)(canvas,0x40ea14cc,x+24,y,4,"%s",dx_enabled?"On":"Off");
 if(wf_menu_edit()&&row==5)((void(*)())0x40070efc)(canvas,x-13,y-2,x+25,y+10,0xffffffffu);
}
void dx_before(u32 now){
 if(!dx_enabled||*(volatile u32*)0x40a7883c!=1)return;
 u32 elapsed=now-*(volatile u32*)0x46732080;
 if(elapsed>dx_peak)dx_peak=elapsed;if(elapsed>90112&&dx_over<9999)dx_over++;
 u32 mask=0;for(u32 i=0;i<6;i++)if(((volatile u8*)0x46732058)[i])mask|=1u<<i;dx_before_mask=mask;
}
void dx_after(void){
 if(!dx_enabled||*(volatile u32*)0x40a7883c!=1)return;
 for(u32 i=0;i<6;i++)if(((volatile u8*)0x46732058)[i]&&!(dx_before_mask&(1u<<i))&&dx_new<9999)dx_new++;
}
u32 dx_beat_key(const u32 *e){
 u32 before=*(volatile u32*)dx_beat_api[1];
 u32 result=((u32(*)(const u32*))dx_beat_api[0])(e);
 if(dx_enabled&&before==3&&*(volatile u32*)dx_beat_api[1]!=3){
  char text[40];((u32(*)())0x40000e6e)(text,"P%u O%u N%u",dx_peak/901,dx_over,dx_new);
  ((void(*)(const char*))dx_beat_api[2])(text);dx_peak=dx_over=dx_new=0;
 }
 return result;
}
