/* Wizard158 : vue d accueil seulement. Aucun setter, fichier ou chemin audio.
 * Bitmap128x64 natif, colonnes min/max bornees et cachees par slot/hash/taille.
 * Les popups et fenetres natives gardent leur rendu et toutes leurs touches. */
typedef unsigned int u32;typedef int s32;typedef unsigned short u16;typedef signed short s16;typedef unsigned char u8;
#define N(a) ((u32(*)())(a))
extern u32 ws_previous_draw(u32,u32),sx_track(void);
extern const u16*ws_params(u32);
extern volatile u32 ws_slot_base[64],ws_slot_count[64],ws_slot_size[64],ws_slot_hash[64],ws_slot_side[64],ws_track_slot[6],ws_mode[6];
extern const char ws_names[];extern const u8 ws_pcm_top[];
static s32 low[122],high[122];
static u32 cache_base,cache_count,cache_hash,cache_side,cache_slot,cache_size,valid,peak;
static void pixel(u32*fb,u32 x,u32 y){if(x<128&&y<64){u32 yy=63-y;fb[x*2+(yy>>5)]|=1u<<(31-(yy&31));}}
static void line(u32*fb,u32 x,u32 y0,u32 y1){for(u32 y=y0;y<=y1&&y<64;y++)pixel(fb,x,y);}
static void text(u32 canvas,u32*font,u32 x,u32 top,const char*value){N(0x40071a04)(canvas,font,x,55-top,0,"%s",value);}

#ifdef WS_VOLUME159
/* Niveau de piste natif, pas un faux vu-metre. Le getter renvoie un octet. */
static void volume(u32*fb,u32 lane,u32 right){
 u32 root=N(0x400cf866)();if(!root)return;u32 kit=N(0x4000eb9c)(root);if(!kit)return;
 u32 value=N(0x40009c5a)(kit,lane)&255;if(value>127)value=127;
 u32 x0=24,x1=right>6?right-6:24;if(x1>88)x1=88;if(x1<=x0)return;u32 count=(x1-x0+2)/6,fill=value*count/127;
 for(u32 i=0;i<count;i++){
  u32 x=x0+i*6;
  for(u32 dx=0;dx<4;dx++)for(u32 y=57;y<=61;y++)
   if(i<fill||dx==0||dx==3||y==57||y==61)pixel(fb,x+dx,y);
 }
}
#endif

#ifdef WS_PAN371
/* Affichage seul : DATA alterne niveau/pan, sans modifier le son. */
extern u32 ws_previous_key(u32,u32);
extern u32 ws_previous_model_key(const u32*);
extern u32 ws_previous_controller_key(u32,const u32*);
extern volatile u32 ws_cpu_open,ws_mod_menu;
volatile u32 ws_pan_mode;
static u32 pan_press;
static u32 home_visible,home_view,home_lane;
#ifdef WS_PAN_DEBUG375
static volatile u32 key_code,key_flags,key_reason,key_lane,draw_count,draw_pan;
void ws_pan_snapshot(u8*d){d[0]='W';d[1]='P';d[2]=ws_pan_mode;d[3]=key_code;d[4]=key_flags;d[5]=key_reason;d[6]=key_lane;d[7]=pan_press;d[8]=draw_count;d[9]=draw_pan;}
#endif
static u32 pan_home(u32 view,u32 lane){
#ifdef WS_PAN_DEBUG375
 key_reason=2;if(view&&*(const u32*)view!=0x400ffe20)return 0;
 key_reason=3;if(view&&*(const u32*)(view+284))return 0;key_reason=4;if(lane>=6)return 0;
 key_reason=5;const u16*p=ws_params(lane);if(!p||(p[9]>>8)!=6)return 0;
 key_reason=6;u32 ui=N(0x400cf9a8)();
 if(ui&&((N(0x4006b704)(ui)&255)||(N(0x4006b736)(ui)&255)||(N(0x4006bb18)(ui)&255)))return 0;
 key_reason=0;return 1;
#else
 if((view&&(*(const u32*)view!=0x400ffe20||*(const u32*)(view+284)))||lane>=6)return 0;
 const u16*p=ws_params(lane);if(!p||(p[9]>>8)!=6)return 0;
 u32 ui=N(0x400cf9a8)();
 return !ui||!((N(0x4006b704)(ui)&255)||(N(0x4006b736)(ui)&255)||(N(0x4006bb18)(ui)&255));
#endif
}
static u32 try_pan_key(u32 view,u32 event){
 if(!event)return 0;
 const u32*e=(const u32*)event;
#ifdef WS_PAN_DEBUG375
 key_code=e[3];key_flags=e[4];
#endif
 if(e[3]==32){
  if((e[4]&16)&&pan_press){pan_press=0;return 1;}
  u32 lane=sx_track();
#ifdef WS_PAN_DEBUG375
  key_lane=lane;pan_home(view,lane);
#endif
  if((e[4]&1)&&!pan_press&&pan_home(view,lane)&&!(N(0x4007faf4)(1)&255)&&!(e[4]&14)){
   ws_pan_mode^=1u<<lane;pan_press=1;
   u32 app=*(volatile u32*)0x40fe4178;if(app)N(0x40076bee)(app+64);return 1;
  }
  if(pan_press)return 1;
 }
 return 0;
}
u32 ws_key(u32 view,u32 event){return try_pan_key(view,event)?1:ws_previous_key(view,event);}
static u32 pointer(u32 p){return p>=0x40000000u&&p<0x46a00000u&&!(p&1);}
static u32 contains(const char*p,const char*word){
 for(u32 i=0;i<64&&p[i];i++){u32 j=0;while(word[j]&&i+j<64&&p[i+j]==word[j])j++;if(!word[j])return 1;}return 0;
}
/* Les navigateurs et boites natives gardent DATA, meme si une image d accueil
 * reste en cache sous leur fenetre. Le RTTI est lu, jamais appele ni modifie. */
static u32 modal(void){
 u32 app=*(volatile u32*)0x40fe4178;if(!pointer(app))return 1;
 u32 head=app+84,node=*(u32*)head;
 for(u32 n=0;node!=head&&n<32;n++){
  if(!pointer(node))return 1;u32 view=*(u32*)(node+8);
  if(pointer(view)&&!*(const u8*)(view+48)){
   u32 vt=*(u32*)view;
   if(vt==0x40111104u||vt==0x40111544u||vt==0x40111054u)return 1;
   if(pointer(vt)&&vt>=0x40000404u){
    u32 ti=*(u32*)(vt-4);if(pointer(ti)){u32 name=*(u32*)(ti+4);
     if(name>=0x40000000u&&name<0x469fffc0u){const char*p=(const char*)name;if(contains(p,"Browser")||contains(p,"File")||contains(p,"Popup")||contains(p,"Dialog")||contains(p,"MenuView")||contains(p,"Picker"))return 1;}
    }
   }
  }
  node=*(u32*)node;
 }
 return node!=head;
}
u32 ws_model_key(const u32*e){
 if(e&&e[3]==32){
#ifdef WS_PAN_DEBUG375
  key_code=e[3];key_flags=e[4];key_reason=!home_visible?7:home_lane!=sx_track()?8:ws_cpu_open?9:ws_mod_menu?10:modal()?11:0;
#endif
  if(pan_press&&try_pan_key(home_view,(u32)e))return 1;
  if(home_visible&&home_lane==sx_track()&&!ws_cpu_open&&!ws_mod_menu&&!modal()&&try_pan_key(home_view,(u32)e))return 1;
 }
 return ws_previous_model_key(e);
}
u32 ws_controller_key(u32 controller,const u32*e){
 /* Le dessin d accueil reste en cache sous les fenetres natives. Invalider
  * AVANT leurs touches d ouverture, meme si le menu consomme ensuite la touche.
  * Le prochain vrai dessin de la waveform reactive DATA. */
 if(e&&(e[4]&1)&&!(e[4]&0x28)){
  u32 code=e[3];
  if(code==4||code==5||code==8||code==13||code==15||(code==2&&((e[4]&2)||(N(0x4007faf4)(1)&255))))home_visible=0;
 }
 return ws_previous_controller_key(controller,e);
}
static void pan(u32 canvas,u32*font,u32*fb,u32 lane,u32 right){
 const u16*p=ws_params(lane);if(!p)return;
 /* En lecture, afficher aussi le pan p-locke du bloc courant. */
 if(*(volatile u32*)0x40a7883c)p=(const u16*)(0x8000100c+14+66*lane);
 u32 value=p[22]>>8;if(value>127)value=127;
 u32 end=right>6?right-6:24;if(end>88)end=88;if(end<60)return;
 text(canvas,font,23,55,"L");text(canvas,font,end-5,55,"R");
 /* Blocs identiques au niveau : centre plein, extension vers L ou R. */
 u32 x0=32,x1=end-9,count=(x1-x0+2)/6;if(!(count&1))count--;if(!count)return;
 u32 middle=count/2;s32 delta=(s32)value-64;
 u32 amount=(u32)(delta<0?-delta:delta),maximum=delta<0?64:63;
 u32 fill=(amount*middle+maximum-1)/maximum;
 for(u32 i=0;i<count;i++){
  u32 distance=i<middle?middle-i:i-middle;
  u32 full=i==middle||(distance<=fill&&(delta<0?i<middle:i>middle));
  u32 x=x0+i*6;
  for(u32 dx=0;dx<4;dx++)for(u32 y=57;y<=61;y++)
   if(full||dx==0||dx==3||y==57||y==61)pixel(fb,x+dx,y);
 }
}
#endif

static u32 scan(u32 slot,u32 base,u32 count,u32 size,u32 hash,u32 side){
 if(valid&&cache_base==base&&cache_count==count&&cache_hash==hash&&cache_side==side&&cache_slot==slot&&cache_size==size)return 1;
 valid=0;peak=256;
 const s16*mid=(const s16*)(base+64);const s16*other=side?(const s16*)(base+64+side):0;
 for(u32 x=0;x<122;x++){
  u32 first=x*count/122,end=(x+1)*count/122;if(end<=first)end=first+1;if(end>count)end=count;
  u32 step=(end-first+31)/32;if(!step)step=1;s32 lo=32767,hi=-32768;
  for(u32 i=first;i<end;i+=step){s32 a=mid[i],b=a;if(other){s32 s=other[i];b=a-s;a+=s;}if(a<lo)lo=a;if(a>hi)hi=a;if(b<lo)lo=b;if(b>hi)hi=b;}
  low[x]=lo;high[x]=hi;u32 a=lo<0?(u32)-lo:(u32)lo,b=hi<0?(u32)-hi:(u32)hi;if(a>peak)peak=a;if(b>peak)peak=b;
 }
 if(ws_slot_base[slot]!=base||ws_slot_count[slot]!=count||ws_slot_hash[slot]!=hash||ws_slot_side[slot]!=side||ws_slot_size[slot]!=size)return 0;
 cache_base=base;cache_count=count;cache_hash=hash;cache_side=side;cache_slot=slot;cache_size=size;valid=1;return 1;
}
u32 ws_draw(u32 view,u32 canvas){
#ifdef WS_PAN371
 home_visible=0;
#endif
 u32 previous=ws_previous_draw(view,canvas);if(previous)return previous;
 if(view&&(*(const u32*)view!=0x400ffe20||*(const u32*)(view+284)))return 0;
 u32 lane=sx_track();if(lane>=6)return 0;const u16*p=ws_params(lane);if(!p||(p[9]>>8)!=6)return 0;
 /* Memes deux etats prioritaires que DrumSelect : note/potard et vue speciale.
  * Deleguer AVANT toute lecture PCM ou ecriture de pixels. */
 u32 ui=N(0x400cf9a8)();if(ui&&((N(0x4006b704)(ui)&255)||(N(0x4006b736)(ui)&255)||(N(0x4006bb18)(ui)&255)))return 0;
 if(!canvas||*(const u32*)(canvas+12)!=2)return 0;u32*fb=*(u32**)(canvas+16);if(!fb)return 0;
 u32 slot=ws_track_slot[lane],base=0,count=0,size=0,hash=0,side=0,loaded=0;
 if(slot<64){base=ws_slot_base[slot];count=ws_slot_count[slot];size=ws_slot_size[slot];hash=ws_slot_hash[slot];side=ws_slot_side[slot];
  u32 top=(u32)ws_pcm_top;
  loaded=hash&&base>=0x4a810000&&base<top&&size>=64&&size<=0x1800000&&size<=top-base&&count&&count<=0xc00000&&count<=(size-64)/2;
  if(loaded&&side&&(side>size-64||count>(size-64-side)/2||side<count*2))loaded=0;
  if(loaded)loaded=scan(slot,base,count,size,hash,side);
 }
 for(u32 i=0;i<256;i++)fb[i]=0;
 char title[18],label[24];u32 n=0;
 if(loaded){const char*name=ws_names+slot*32;while(n<16&&name[n]){title[n]=name[n];n++;}
  if(n==16&&name[16])title[15]='~';title[n]=0;
  /* Un nom court conserve les points internes ; retirer seulement .wav final. */
  if(n>=4&&title[n-4]=='.'&&(title[n-3]=='w'||title[n-3]=='W')&&(title[n-2]=='a'||title[n-2]=='A')&&(title[n-1]=='v'||title[n-1]=='V'))title[n-4]=0;
  if(!title[0])N(0x40000e6e)(title,"Sample %u",slot+1);
 }else{const char*s="Sample Wizard";while(*s)title[n++]=*s++;title[n]=0;valid=0;}
 u32 duration_x=91;u32 font[2];N(0x40072260)(font,0x40140ab0);
 text(canvas,font,3,2,title);
 if(loaded)N(0x40000e6e)(label,"S%02u",slot+1);else N(0x40000e6e)(label,"S--");text(canvas,font,107,2,label);
 /* Bandeau inverse ; les coords du framebuffer sont retournees dans pixel(). */
 for(u32 x=0;x<128;x++)for(u32 y=0;y<12;y++){u32 yy=63-y;fb[x*2+(yy>>5)]^=1u<<(31-(yy&31));}
 for(u32 x=2;x<126;x++)pixel(fb,x,53);
 N(0x40000e6e)(label,"T%u",lane+1);text(canvas,font,3,55,label);
 if(loaded){u32 centis=count/480;N(0x40000e6e)(label,"%u.%02us",centis/100,centis%100);u32 len=0;while(label[len])len++;duration_x=len<20?126-6*len:3;text(canvas,font,duration_x,55,label);
  for(u32 x=0;x<122;x++){
   s32 a=32-high[x]*17/(s32)peak,b=32-low[x]*17/(s32)peak;if(a<14)a=14;if(b>50)b=50;
   if(a>b){s32 t=a;a=b;b=t;}line(fb,x+3,(u32)a,(u32)b);
  }
  for(u32 x=3;x<125;x+=3)pixel(fb,x,32);
  /* Repere Start/Position, pas un faux curseur anime : Stretch utilise Speed. */
  u32 mode=ws_mode[lane];if(mode<=3||mode==5){s32 start=(s16)p[11];if(start<0)start=0;if(start>32512)start=32512;u32 x=3+(u32)start*121/32768;
   for(u32 y=14;y<51;y+=2)pixel(fb,x,y);for(s32 d=-2;d<=2;d++)pixel(fb,(u32)((s32)x+d),13);
  }
 }else{text(canvas,font,37,29,"No sample");text(canvas,font,91,55,"--.--s");}
 #ifdef WS_VOLUME159
#ifdef WS_PAN371
 home_visible=1;home_view=view;home_lane=lane;
#ifdef WS_PAN_DEBUG375
 draw_count++;draw_pan=!!(ws_pan_mode&(1u<<lane));
#endif
 if(ws_pan_mode&(1u<<lane))pan(canvas,font,fb,lane,duration_x);else
#endif
 volume(fb,lane,duration_x);
#else
 (void)duration_x;
#endif
 N(0x40072080)(font);return 1;
}
