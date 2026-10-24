#include "fx.h"
static u32 popup_table[22];
const u32 fx_obj[2]={0x400fd134,0};
extern u32 fx_object(void);
const u32 fx_view_vt[33]={[32]=(u32)fx_object};
const u32 fx_view[1]={(u32)fx_view_vt};
#ifdef FX_CLOUD_REPAIR
/* Lire les vrais accesseurs OS : Time/Feedback globaux et Send de la piste.
 * Aucun miroir partage avec Density, aucune valeur issue du dessin precedent. */
u32 fx_cloud_native_value(u32 field,u32 lane){
 u32 root=N(0x400cf866)(),bank=N(0x4000eb9c)(root);
 u32 obj=field==14?N(0x400097f0)(bank,lane):N(0x40009810)(bank);
 u32 desc=field==14?26:field==13?38:37;
 return N(*(u32*)(*(u32*)obj+28))(obj,desc,lane)>>8;
}
#endif
void fx_value(u32 field,u32*value,const char**type,const char**label){u32 lane=fx_selected();if(lane>=6)lane=0;
 *type=(field<3
#ifdef FX_CLOUD
 ||field==10||field==11
#ifdef FX_CLOUD_REPAIR
 ||field==12||field==13||field==14
#endif
#endif
 ?fx_del_names[cr_mode<FX_DEL_COUNT?cr_mode:0]:fx_rev_names[ch_mode<FX_REV_COUNT?ch_mode:0]);
 switch(field){case 0:*value=cr_rate;*label="Rate";break;case 1:*value=cr_bits;*label="Bits";break;case 2:*value=cr_send[lane];*label="Crush Send";break;case 3:*value=fx_speed;*label="Speed";break;case 4:*value=fx_depth;*label="Depth";break;case 5:*value=fx_aux_ch[lane];*label="Chorus Send";break;case 6:*value=fx_crackle;*label="Crackle";break;case 7:*value=fx_warble;*label="Warble Amt";break;case 8:*value=fx_wspeed;*label="Warble Spd";break;
#ifdef FX_CLOUD
#ifdef FX_CLOUD_REPAIR
case 12:case 13:case 14:*value=fx_cloud_native_value(field,lane);*label=field==12?"Window":field==13?"Feedback":"Cloud Send";break;
#endif
case 10:*value=fx_cloud_density;*label="Density";break;case 11:*value=fx_cloud_pitch;*label="Pitch";break;
#endif
default:*value=fx_aux_vi[lane];*label="Vinyl Send";break;}
}
static void title(u32 canvas,const char*type,const char*label){N(0x40070efc)(canvas,0,33,63,63,0);N(0x40071a04)(canvas,0x40ea14cc,32,52,2,"%s",type);N(0x40071a04)(canvas,0x40ea14cc,32,40,2,"%s",label);}
u32 fx_popup_render(u32 self,u32 canvas){u32 field=((const u32*)self)[39],value;const char*type,*label;fx_value(field,&value,&type,&label);
 u32 graphic=field==1?(value-2)*127/14:value;
#ifdef FX_CLOUD
 if(field==11)graphic=value*127/24;
#endif
N(0x40070efc)(canvas,0,0,127,63,0);
 fx_previous_popup((u32)fx_view,canvas,37,graphic<<8,0,1);title(canvas,type,label);N(0x40070efc)(canvas,64,32,127,63,0);
 char line[12];u32 font[2];
#ifdef FX_CLOUD
 if(field==11)N(0x40000e6e)(line,"%+d",(s32)value-12);else
#endif
 N(0x40000e6e)(line,"%u",value);N(0x40072260)(font,0x401429ec);N(0x40071a04)(canvas,font,96,34,2,"%s",line);N(0x40072080)(font);N(0x40070f6e)(canvas,0,0,63,63,0xffffffffu);return 0;
}
void fx_popup_bind(u32 object,u32 field){if(!popup_table[6]){const u32*n=(const u32*)0x40111bc8;for(u32 i=0;i<22;i++)popup_table[i]=n[i];popup_table[6]=(u32)fx_popup_render;}*(u32*)object=(u32)(popup_table+2);((u32*)object)[39]=field<
#ifdef FX_CLOUD_REPAIR
15
#elif defined(FX_CLOUD)
12
#else
10
#endif
?field:0;}
u32 fx_popup(u32 view,u32 canvas,u32 desc,s32 value,u32 flags,u32 last){u32 result=fx_previous_popup(view,canvas,desc,value,flags,last);
 #ifdef FX_NEW_DELAYS
 if(FX_SPECIAL_DELAY(cr_mode)){
#ifdef FX_CLOUD
 if(cr_mode==8){if(desc==26)title(canvas,"CLOUD","Cloud Send");if(desc==37||desc==38)title(canvas,"CLOUD",desc==37?"Window":"Feedback");}
 else
#endif
 {if(desc==26)title(canvas,fx_del_names[cr_mode],"Delay Send");if(desc==37||desc==38)title(canvas,fx_del_names[cr_mode],desc==37?"Time":"Feedback");}}
#endif
#ifdef FX_PS1
 if(ch_mode==7){if(desc==27)title(canvas,"PS1","PS1 Send");if(desc==39||desc==40)title(canvas,"PS1",desc==39?"Decay":"Tone");}
#endif
 #ifdef FX_CHEAP
 if(ch_mode==8){if(desc==27)title(canvas,"ROOM","Room Send");if(desc==39||desc==40)title(canvas,"ROOM",desc==39?"Decay":"Tone");}
#endif
 if(desc==26&&(cr_mode==1||cr_mode==2))title(canvas,fx_del_names[cr_mode],"Crush Send");
 if(desc==27&&(ch_mode==1||ch_mode==2||ch_mode==3))title(canvas,fx_rev_names[ch_mode],ch_mode==3?"Vinyl Send":"Chorus Send");
 return result;
}
