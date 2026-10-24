/* Popup temporaire natif : duree/destruction stock, rendu natif et valeurs propres. */
typedef unsigned int u32;typedef int s32;
extern volatile u32 cr_mode,cr_rate,cr_bits;
extern u32 cr_native_popup(u32,u32,u32,s32,u32,u32);
static u32 table[22];
const u32 cr_obj[2]={0x400fd134,0};
extern u32 cr_object(void);
const u32 cr_view_vt[33]={[32]=(u32)cr_object};
const u32 cr_view[1]={(u32)cr_view_vt};
u32 cr_popup_render(u32 self,u32 canvas){
 u32 field=((const u32*)self)[39],value=field?cr_bits:cr_rate;
 u32 graphic=field?(value-2)*127/14:value;
 void (*rect)(u32,s32,s32,s32,s32,u32)=(void*)0x40070efc;
 void (*text)(u32,u32,s32,s32,u32,const char*,const char*)=(void*)0x40071a04;
 rect(canvas,0,0,127,63,0);
 cr_native_popup((u32)cr_view,canvas,field?38:37,graphic<<8,0,1);
 rect(canvas,0,33,63,63,0);rect(canvas,64,32,127,63,0);
 text(canvas,0x40ea14cc,32,52,2,"%s",cr_mode==4?"Both 2":cr_mode==3?"Both 1":cr_mode==2?"Crush 2":"Crush 1");
 text(canvas,0x40ea14cc,32,40,2,"%s",field?"Bits":"Rate");
 char line[12];u32 font[2];((u32(*)(char*,const char*,...))0x40000e6e)(line,"%u",value);
 ((void(*)(u32*,u32))0x40072260)(font,0x401429ec);text(canvas,(u32)font,96,34,2,"%s",line);((void(*)(u32*))0x40072080)(font);
 ((void(*)(u32,s32,s32,s32,s32,u32))0x40070f6e)(canvas,0,0,63,63,0xffffffffu);
 return 0;
}
void cr_popup_bind(u32 object,u32 field){
 if(!table[6]){const u32 *native=(const u32*)0x40111bc8;for(u32 i=0;i<22;i++)table[i]=native[i];table[6]=(u32)cr_popup_render;}
 *(u32*)object=(u32)(table+2);((u32*)object)[39]=!!field;
}
