/* Banque LFO2 complete par pattern/piste. Le frame natif peut conserver les
 * cinq anciens champs : il ne doit plus reimposer le son sortant au contexte.
 * Ancien L2x conserve et migre ; les sons MIDI ne sont jamais reecrits. */
typedef unsigned int u32;typedef unsigned short u16;typedef unsigned char u8;
#define N(a) ((u32(*)())(a))
#define ROW 116u
#define PAYLOAD (96u*ROW)
#define SIZE (16u+PAYLOAD)
extern volatile u32 lf2_context,lf2n_epoch,lf2n_seen,xp_polarity[12],xp_lp_one[6],xp_lp_two[6],xp_project_decoding;
extern void xp_old_sync(u32,u32),xp_old_frame(void),xp_old_change(u32),xp_old_dispatch(u32,u32,u32),xp_pattern(u32),xp_old_redraw(u32);
extern u32 xp_old_clear(u32,u32,u32,u32,u32,u32),xp_old_command(u32,u32,u32,u32,u32),xp_old_open(u32),xp_copy_prepare(void),xp_quiet(void),xp_crc(const u8*,u32);
extern u32 xp_old_edit(u32,u32,u32,u32),xp_old_unpack(u8*,u32);
extern void xp_old_pol_set(u32,u32,u32);
extern u32 xp_old_clip(u8*,const u8*,u32);
static u8 *storage;static u32 ready,project,project_owner,project_gen,native_pending,current=96,dirty,import_pending;
static char path[20];
static u32 pattern(void){u32 p=*(volatile u32*)0x40a7887c;return p?*(const u32*)(p+30706):96;}
static u32 owner(void){u32 p=*(volatile u32*)0x40fe4228;return p?*(const u32*)(p+16):0;}
static u8 *rows(void){return storage+SIZE;}
static u8 *row(u32 id){return rows()+id*ROW;}
static u8 *sound(u32 t){u32 p=*(volatile u32*)0x40a78888;return p?(u8*)(p+28+t*100):0;}
static u32 lock(void){u32 sr;__asm__ volatile("move.w %%sr,%0\n\tmove.w #0x2700,%%sr":"=d"(sr)::"memory","cc");return sr;}
static void unlock(u32 sr){__asm__ volatile("move.w %0,%%sr"::"d"(sr):"memory","cc");}
static void defaults(u8*p){for(u32 i=0;i<ROW;i++)p[i]=0;for(u32 t=0;t<6;t++){u16*v=(u16*)(p+t*16);v[0]=0x7000;v[1]=0x400;v[2]=0x4000;v[3]=0x7f00;v[7]=0x4000;}}
static u32 values_ok(const u16*v){return v[0]<32768&&!(v[1]&255)&&(v[1]>>8)<24&&v[2]<32768&&!(v[3]&255)&&((v[3]>>8)<33||(v[3]>>8)==127)&&!(v[4]&255)&&(v[4]>>8)<7&&v[5]<32768&&!(v[6]&255)&&(v[6]>>8)<5&&v[7]<32768;}
static u32 native_values(u16*v,const u8*p){
 if(!p||p[38]==17)return 0;v[0]=*(const u16*)(p+76);v[1]=*(const u16*)(p+78)&0xff00;v[4]=*(const u16*)(p+80);v[3]=*(const u16*)(p+82);if(!v[3])v[3]=0x7f00;v[7]=*(const u16*)(p+84);return values_ok(v);
}
static void capture_track(u32 t){
 if(!ready||current>=96||!lf2_context||t>=6)return;u16*p=(u16*)(row(current)+t*16);const volatile u16*v=(const volatile u16*)(lf2_context+192+t*16);
 for(u32 i=0;i<8;i++){u16 n=v[i];if(i==1)n&=0xff00;if(i==3&&!n)n=0x7f00;if(p[i]!=n){p[i]=n;dirty=1;}}
 u8*raw=sound(t);u32 pol=native_pending?row(current)[96+t]:raw&&(raw[79]&0xfc)==0xa0?(raw[79]>>1)&1:xp_lp_two[t]&1;
 if(row(current)[96+t]!=pol){row(current)[96+t]=pol;dirty=1;}
}
static void capture(void){if(!ready||current>=96)return;for(u32 t=0;t<6;t++)capture_track(t);u8*p=row(current)+102;for(u32 i=0;i<12;i++)if(p[i]!=(xp_polarity[i]&1)){p[i]=xp_polarity[i]&1;dirty=1;}}
static void restore(u32 ctx,u32 id){
 if(!ready||id>=96||!ctx)return;const u16*p=(const u16*)row(id);volatile u16*v=(volatile u16*)(ctx+192);u32 sr=lock();
 for(u32 t=0;t<6;t++){for(u32 i=0;i<8;i++)v[t*8+i]=p[t*8+i];u8*raw=sound(t);u32 one=raw&&(raw[79]&0xfc)==0xa0?raw[79]&1:xp_lp_one[t]&1;v[t*8+1]|=0xa0|one|((u32)row(id)[96+t]<<1);}
 for(u32 i=0;i<12;i++)xp_polarity[i]=row(id)[102+i];unlock(sr);
}
/* Publication UI pour copie/export du son, sans notifier ni toucher LFO1.
 * L'audio lit sa banque complete restauree, jamais ces cinq champs caches. */
static void native_ui(void){
 if(!ready||current>=96||current!=pattern())return;const u16*v=(const u16*)row(current);
 for(u32 t=0;t<6;t++){u8*p=sound(t);if(!p||p[38]==17)continue;u32 one=(p[79]&0xfc)==0xa0?p[79]&1:xp_lp_one[t]&1;
  *(u16*)(p+76)=v[t*8];*(u16*)(p+78)=v[t*8+1]|0xa0|one|((u32)row(current)[96+t]<<1);*(u16*)(p+80)=v[t*8+4];*(u16*)(p+82)=v[t*8+3]==0x7f00?0:v[t*8+3];*(u16*)(p+84)=v[t*8+7];
 }
}
u32 xp_edit(u32 ctx,u32 t,u32 field,u32 value){u32 sr=lock();if(ctx==lf2_context&&native_pending&&ready){native_ui();native_pending=0;}u32 ok=xp_old_edit(ctx,t,field,value);if(ok&&ctx==lf2_context)capture_track(t);unlock(sr);return ok;}
void xp_pol_set(u32 t,u32 bank,u32 uni){if(ready&&native_pending){native_ui();native_pending=0;}xp_old_pol_set(t,bank,uni);if(bank==1)capture_track(t);}
u32 xp_clip(u8*dst,const u8*src,u32 bytes){if(ready){capture();native_ui();native_pending=0;}return xp_old_clip(dst,src,bytes);}
static void import_sound(u32 t){
 if(!ready||current>=96||t>=6)return;u8*p=sound(t);u16*v=(u16*)(row(current)+t*16);if(p&&p[38]!=17){v[2]=0x4000;v[5]=v[6]=0;if(native_values(v,p)){row(current)[96+t]=(p[79]&0xfc)==0xa0?(p[79]>>1)&1:0;dirty=1;}}
}
u32 xp_unpack(u8*p,u32 word){
 u32 ok=xp_old_unpack(p,word);u32 table=*(volatile u32*)0x40a78888,at=(u32)p;
 if(ready&&!xp_project_decoding&&table&&at>=table+28&&at<table+628&&(at-table-28)%100==0){u32 t=(at-table-28)/100;
  if(ok){import_sound(t);restore(lf2_context,current);}else if((word&0xc0000000u)==0x80000000u)import_pending|=1u<<t;
 }return ok;
}
void xp_redraw(u32 track){capture();native_ui();xp_old_redraw(track);}
u32 xp_command(u32 object,u32 machine,u32 flags,u32 undo,u32 preset){u32 result=xp_old_command(object,machine,flags,undo,preset);if(result&255){capture();native_ui();}return result;}
void xp_sync(u32 ctx,u32 frame){
 u32 id=pattern(),transition=ready&&id<96&&current!=id;if(transition)capture();xp_old_sync(ctx,frame);
 if(!ready||id>=96)return;if(transition){current=id;native_pending=1;}
 if(import_pending){for(u32 t=0;t<6;t++)if(import_pending&(1u<<t))import_sound(t);import_pending=0;}
 restore(ctx,id);
}
void xp_change(u32 ptr){capture();xp_old_change(ptr);if(ready&&ptr){u32 id=*(const u32*)(ptr+30706);if(id<96&&id!=current){current=id;native_pending=1;restore(lf2_context,id);}}}
void xp_dispatch(u32 frame,u32 ticks,u32 trig){xp_pattern(*(volatile u32*)0x40a7887c);xp_old_dispatch(frame,ticks,trig);}
u32 xp_clear(u32 root,u32 id,u32 seq,u32 sound_clear,u32 undo,u32 quiet){u32 result=xp_old_clear(root,id,seq,sound_clear,undo,quiet);if((result&255)&&sound_clear&&ready){if(id>95)id=95;defaults(row(id));dirty=1;}return result;}
static void filename(u32 id){const char hex[]="0123456789abcdef";const char pre[]="/L2p_";for(u32 i=0;i<5;i++)path[i]=pre[i];for(u32 i=0;i<8;i++)path[5+i]=hex[(id>>(28-i*4))&15];path[13]='.';path[14]='c';path[15]='f';path[16]='g';path[17]=0;}
static u32 valid(const u8*p){for(u32 id=0;id<96;id++){const u8*r=p+id*ROW;for(u32 t=0;t<6;t++)if(!values_ok((const u16*)(r+t*16)))return 0;for(u32 i=96;i<114;i++)if(r[i]>1)return 0;if(r[114]||r[115])return 0;}return 1;}
static void save(void){
 if(!ready||!dirty||!project)return;u32*h=(u32*)storage;h[0]=0x4c325031;h[1]=project;h[2]=PAYLOAD;h[3]=xp_crc(rows(),PAYLOAD);for(u32 i=0;i<PAYLOAD;i++)storage[16+i]=rows()[i];u32 handle[4]={0};
 if(!N(0x4007bc5e)(path,"w",handle)){u32 ok=!N(0x4007bb76)(handle,0,SIZE)&&N(0x4007bb0a)(storage,SIZE,handle)==SIZE&&!N(0x4007e2f6)(handle);if(N(0x4007bc1c)(handle))ok=0;if(ok)dirty=0;}
}
/* 96 kits natifs : copie du template7094 par 40061738 ; sons a kit+28.
 * Lire chaque kit enregistre, pas le cache sonore global encore sortant. */
static void seed_native(void){
 u32 raw=owner();if(raw<0x40000400u||raw>0x42400000u-0x37615cu)return;
 for(u32 id=0;id<96;id++){u32 kit=*(const u8*)(raw+28+id*30710+30670);if(kit>=96)kit=id;
  for(u32 t=0;t<6;t++){const u8*p=(const u8*)(raw+0x2d1812u+kit*7094+28+t*100);u16 v[8];for(u32 i=0;i<8;i++)v[i]=((u16*)row(id))[t*8+i];if(native_values(v,p)){for(u32 i=0;i<8;i++)((u16*)row(id))[t*8+i]=v[i];row(id)[96+t]=(p[79]&0xfc)==0xa0?(p[79]>>1)&1:0;}}
 }
}
static void legacy(u32 id){
 u32 h[4]={0};u8 extra;path[3]='x';if(!N(0x4007bc5e)(path,"r",h)){
  u32 ok=N(0x4007baaa)(storage,4624,h)==4624&&!N(0x4007baaa)(&extra,1,h);N(0x4007bc1c)(h);u32*head=(u32*)storage;
  if(ok&&head[0]==0x4c325831&&head[1]==id&&head[2]==4608&&head[3]==xp_crc(storage+16,4608)){
   for(u32 k=0;k<96;k++){const u8*p=storage+16+k*48;for(u32 t=0;t<6;t++){const u16*v=(const u16*)(p+t*6);if(v[0]<32768&&v[1]<32768&&!(v[2]&255)&&(v[2]>>8)<5){u16*d=(u16*)(row(k)+t*16);d[2]=v[0];d[5]=v[1];d[6]=v[2];}}
    for(u32 i=0;i<12;i++)if(p[36+i]<2)row(k)[102+i]=p[36+i];
   }
  }
 }path[3]='p';
}
static void load(u32 id){
 ready=0;for(u32 i=0;i<96;i++)defaults(row(i));seed_native();u32 active=pattern();if(active<96)for(u32 i=0;i<12;i++)row(active)[102+i]=xp_polarity[i]&1;filename(id);u32 h[4]={0},loaded=0;u8 extra;
 if(id&&!N(0x4007bc5e)(path,"r",h)){u32 ok=N(0x4007baaa)(storage,SIZE,h)==SIZE&&!N(0x4007baaa)(&extra,1,h);N(0x4007bc1c)(h);u32*head=(u32*)storage;
  if(ok&&head[0]==0x4c325031&&head[1]==id&&head[2]==PAYLOAD&&head[3]==xp_crc(storage+16,PAYLOAD)&&valid(storage+16)){for(u32 i=0;i<PAYLOAD;i++)rows()[i]=storage[16+i];loaded=1;}
 }if(id&&!loaded)legacy(id);project=id;current=active;ready=1;dirty=id&&!loaded;native_pending=1;import_pending=0;restore(lf2_context,current);
}
void xp_frame(void){
 xp_old_frame();u32 sr;__asm__ volatile("move.w %%sr,%0":"=d"(sr));
 if((sr&0x700)||!*(volatile u32*)0x40fe4178||*(volatile u32*)0x40a7883c||!lf2_context||!N(0x400d0a10)())return;
 u32 kit=N(0x400cf866)();if(!kit)return;u32 id=N(0x4000eae2)(kit),raw=*(const u32*)(kit+16);if(!raw)raw=kit;u32 generation=*(volatile u32*)0x468f6e80;
 if(!storage){storage=(u8*)N(0x400802e0)(SIZE+PAYLOAD);if(!storage)return;}
 if(ready&&raw==project_owner&&generation==project_gen&&!project&&id){project=id;filename(id);dirty=1;}
 if(!ready||project!=id||project_owner!=raw||project_gen!=generation){if(ready&&project&&dirty){if(*(volatile u32*)0x40a78874||!xp_quiet())return;save();if(dirty)return;}load(id);project_owner=raw;project_gen=generation;}
 u32 pat=pattern();if(pat<96&&pat!=current){capture();current=pat;native_pending=1;restore(lf2_context,pat);}if(native_pending&&pat==current){native_ui();native_pending=0;}capture();
 if(!*(volatile u32*)0x40a78874&&xp_quiet())save();
}
u32 xp_open(u32 view){xp_copy_prepare();xp_pattern(*(volatile u32*)0x40a7887c);xp_frame();native_ui();return xp_old_open(view);}
