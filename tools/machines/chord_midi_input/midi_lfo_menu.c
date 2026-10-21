/* Pages LFO MIDI : vrai MenuView stock et edition via publication native.
 * L'etat reste celui du module MIDI existant ; aucune valeur LFO audio ecrite.
 */
typedef unsigned int u32;typedef unsigned short u16;
extern volatile u32 mi_mm_page,mi_mm_lane,mi_mm_row,mi_mm_edit;
extern const u16 *mi_mm_params(u32);
extern u32 mi_mm_lfo_read(const u16 *,u32,u32),mi_mm_lfo_edit(u16 *,u32,u32,int);
extern u32 mi_mm_draw_original(u32,u32),mi_mm_key_original(const u32 *);
extern u32 mi_mm_encoder_original(const u32 *),mi_mm_cc_read(const u16 *,u32);
extern int mi_mm_cc_number(u32);
extern void mi_mm_poll(void),mi_lfo_menu_draw(u32,u32);
extern void mx_latch_event(const u32 *);
extern void mm_lfo_live_speed(u32,u32,u32);
static u32 selected(void){u32 p=((u32(*)(void))0x400cf866)();return ((u32(*)(u32))0x40012412)(p+48);}
static u32 active(u32 t){return t<6 && mi_mm_lane==t && (mi_mm_page==1 || mi_mm_page==2) && ((u32(*)(u32,u32))0x4001e318)(0,t)==17;}
static void redraw(void){u32 app=*(volatile u32*)0x40fe4178;if(app)((void(*)(u32))0x40076bee)(app+64);}
static u32 quick_track=6,quick_page,quick_knob=12;
static int quick_cc=-1;
/* Ordre visible independant du format des huit champs sauvegardes. */
static const u32 row_fields[8]={4,1,3,7,0,2,5,6};
static void quick_reset(void){quick_track=6;quick_knob=12;quick_cc=-1;}
u32 mi_lfo_scroll(void){u32 row=mi_mm_row;return row<4?0:row>5?4:row-1;}
u32 mi_lfo_relative(void){return mi_mm_row-mi_lfo_scroll();}
u32 mi_lfo_number(void){return mi_mm_page;}
u32 mi_mm_key(const u32 *event){
 mx_latch_event(event);
 if(event && ((event[3]==8 && !(event[4]&1)) || (event[3]==8 && (event[4]&9)==1) || event[3]==12))quick_reset();
 if(event && event[3]==8 && (event[4]&9)==1 && ((u32(*)(u32,u32))0x4001e318)(0,selected())==17){
  /* Une TrackMenuView native encore ouverte ne doit pas restaurer le setup
   * par-dessus la page LFO au prochain refresh ou evenement DATA. */
  u32 app=*(volatile u32*)0x40fe4178;
  if(app){u32 head=app+84,node=*(u32*)(head+4);
   for(u32 i=0;node && node!=head && i<32;i++){
    u32 next=*(u32*)(node+4),view=*(u32*)(node+8);
    if(view && *(u32*)view==0x40108128 && !*(unsigned char*)(view+48))((void(*)(u32))0x40076126)(view);
    node=next;
   }
  }
 }
 return mi_mm_key_original(event);
}
u32 mi_lfo_encoder(const u32 *event){
 if(!event || event[0]!=0x400fbebc || event[3]<1 || event[3]>13)return 0;
 u32 t=selected();if(t>=6 || ((u32(*)(u32,u32))0x4001e318)(0,t)!=17)return 0;
 if(!((u32(*)(u32))0x4007faf4)(8))quick_reset();
 /* Meme table physique que le LFO audio : identifiant natif 29 = Speed. */
 u32 speed=0;
 if(event[3]!=1 && !((u32(*)(u32))0x4007faf4)(13)){
  const u32 *layout=(const u32*)((u32(*)(u32))0x4004df5c)(1);
  speed=layout && layout[2+event[3]-2]==29;
 }
 /* Speed reste un controle LFO hors page ; Swing et Chance passent au natif. */
 if(event[3]==12 || event[3]==13)return 0;
 if(!active(t)){
  if(!speed)return 0;
  mi_mm_lane=t;mi_mm_page=1;mi_mm_row=4;mi_mm_edit=0;
 }
 /* Les potards restent des CC, meme devant le menu LFO. Le raccourci
  * LFO+potard reprend uniquement son numero CC deja assigne. */
 if(event[3]!=1 && !speed){
  if(((u32(*)(u32))0x4007faf4)(8) && !((u32(*)(u32))0x4007faf4)(13)){
   const u16 *before=mi_mm_params(t);int cc=mi_mm_cc_number(mi_mm_cc_read(before,event[3]-2));
   if(cc>=0){
    u16 after[33];for(u32 i=0;i<33;i++)after[i]=before[i];
    u32 knob=event[3]-2;
    if(quick_track==t && quick_page==mi_mm_page && quick_knob==knob && quick_cc==cc && mi_mm_lfo_read(before,mi_mm_page-1,3)==(u32)cc){
     int delta=((int(*)(const u32*,u32,u32))0x4006f73a)(event,1,1);
     mi_mm_lfo_edit(after,mi_mm_page-1,7,delta*128);
     mi_mm_row=3;
    }else{
     mi_mm_lfo_edit(after,mi_mm_page-1,3,cc-(int)mi_mm_lfo_read(before,mi_mm_page-1,3));
     quick_track=t;quick_page=mi_mm_page;quick_knob=knob;quick_cc=cc;
     mi_mm_row=2;
    }
    u32 records[64],count=0;
    for(u32 i=1;i<33;i++)if(i!=9 && i!=10 && after[i]!=before[i]){records[2*count]=i;records[2*count+1]=(u32)after[i]<<16;count++;}
    if(count){u32 root=((u32(*)(void))0x400cf866)(),bank=((u32(*)(u32))0x4000eb9c)(root),object=((u32(*)(u32,u32))0x40009c1a)(bank,t);
     u32 pair[2]={(u32)records,(u32)(records+2*count)};((void(*)(u32,const u32*))0x4001416c)(object,pair);
    }
   }
   redraw();return 1;
  }
  u32 page=mi_mm_page;mi_mm_page=0;
  u32 result=mi_mm_encoder_original(event);mi_mm_page=page;
  redraw();return result;
 }
 if(((u32(*)(u32))0x4007faf4)(13))return 0;
 int delta=((int(*)(const u32*,u32,u32))0x4006f73a)(event,1,speed?8:1);
 if(event[3]==1 && !mi_mm_edit){int row=(int)mi_mm_row+delta;mi_mm_row=row<0?0:row>7?7:(u32)row;redraw();return 1;}
 if(mi_mm_row>7)return 1;
 u32 field=speed?0:row_fields[mi_mm_row];
 if(speed)mi_mm_row=4;
 const u16 *before=mi_mm_params(t);if(!before)return 1;
 u16 after[33];for(u32 i=0;i<33;i++)after[i]=before[i];
 if(field!=1 && field!=3 && field!=4 && field!=6)delta*=speed?256:128;
 mi_mm_lfo_edit(after,mi_mm_page-1,field,delta);
 u32 records[64],count=0;
 for(u32 i=1;i<33;i++)if(i!=9 && i!=10 && after[i]!=before[i]){records[2*count]=i;records[2*count+1]=(u32)after[i]<<16;count++;}
 if(count){u32 root=((u32(*)(void))0x400cf866)(),bank=((u32(*)(u32))0x4000eb9c)(root),object=((u32(*)(u32,u32))0x40009c1a)(bank,t);
  u32 pair[2]={(u32)records,(u32)(records+2*count)};((void(*)(u32,const u32*))0x4001416c)(object,pair);
  if(field==0)mm_lfo_live_speed(t,mi_mm_page-1,mi_mm_lfo_read(after,mi_mm_page-1,0));
 }
 redraw();return 1;
}
u32 mi_mm_draw(u32 view,u32 canvas){
 mi_mm_poll();u32 t=selected();if(!active(t))return mi_mm_draw_original(view,canvas);
 mi_lfo_menu_draw(view,canvas);return 1;
}
void mi_lfo_value(u32 self,u32 item,u32 canvas,u32 x,u32 y,u32 flags){
 (void)self;(void)flags;u32 field=*(u32*)(item+80)&255;
 const u16 *params=mi_mm_params(selected());u32 value=mi_mm_lfo_read(params,mi_mm_page-1,field);char line[32];
 if(field==3){if(value==128)((u32(*)())0x40000e6e)(line,"OFF");else ((u32(*)())0x40000e6e)(line,"CC%u",value);}
 else if(field==4 || field==6){const char *label=((const char *const*)(field==4?0x40108f24:0x40108f40))[value];((u32(*)())0x40000e6e)(line,"%s",label);}
 else if(field==1){u32 index=value%12,n=1u<<index;((u32(*)())0x40000e6e)(line,index>=10?"%s%uk":"%s%u",value<12?"*":"",index>=10?n>>10:n);}
 else ((u32(*)())0x40000e6e)(line,"%d",field==5?(int)(value>>8):((int)value-16384)>>8);
 ((void(*)())0x40071a04)(canvas,0x40ea14cc,x+24,y,4,"%s",line);
 if(mi_mm_edit && mi_mm_row<8 && field==row_fields[mi_mm_row])((void(*)())0x40070efc)(canvas,x-5,y-2,x+25,y+10,0xffffffffu);
}
