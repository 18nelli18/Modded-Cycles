/* FXS1 : 36 valeurs par pattern, codecs/UI seulement pour le CRC et les E/S.
 * Le raccord au changement natif ne fait que des copies bornees en RAM. */
typedef unsigned int u32;typedef unsigned char u8;
#include "fields.h"
extern void fxp_capture(u8*),fxp_apply(const u8*),fxp_sync(void);
extern u32 fxp_crc(const u8*,u32),fxp_values_ok(const u8*),fxp_record_valid(const u8*);
extern u32 fxs_native_encode(u8*,const u8*,u32),fxs_native_decode(u8*,const u8*,u32);
extern u32 fxs_native_init(u8*,u32),fxs_native_load(u32,u32,u32),fxs_native_new_project(u32,u32);
extern u32 fxs_native_copy(u32,u32,u32);
struct bank {u8 value[96][36],valid[96];};
struct clip {u32 ptr;u8 value[36],valid;};
static struct bank live,waiting,exported;
static struct clip clips[8];
static volatile u32 revision;
static u32 project,waiting_project,current,current_ptr,ready,legacy,waiting_legacy,busy,decoding,encoding,export_project,clip_cursor;
static u8 legacy_value[36];
#define STRIDE 30710u
#define PAD 0x39d0u
static u32 rd(const u8*p){return (u32)p[0]<<24|(u32)p[1]<<16|(u32)p[2]<<8|p[3];}
static void wr(u8*p,u32 v){p[0]=v>>24;p[1]=v>>16;p[2]=v>>8;p[3]=v;}
static void cp(u8*d,const u8*s,u32 n){while(n--)*d++=*s++;}
static void zero(u8*d,u32 n){while(n--)*d++=0;}
static u32 lock(void){u32 sr;__asm__ volatile("move.w %%sr,%0\n\tmove.w #0x2700,%%sr":"=d"(sr)::"memory","cc");return sr;}
static void unlock(u32 sr){__asm__ volatile("move.w %0,%%sr"::"d"(sr):"memory","cc");}
static u32 raw_now(void){u32 p=*(volatile u32*)0x40fe4228;return p?*(volatile u32*)(p+16):0;}
static u32 index_at(u32 ptr,u32 raw){
 if(!raw||ptr<raw+28)return 96;u32 offset=ptr-raw-28;
 return offset<96*STRIDE&&offset%STRIDE==0?offset/STRIDE:96;
}
static u32 same(const u8*a,const u8*b){for(u32 i=0;i<36;i++)if(a[i]!=b[i])return 0;return 1;}
static void store_current(void){
 if(!ready||current>95||project!=raw_now())return;
 u8 v[36];fxp_capture(v);cp(live.value[current],v,36);
 live.valid[current]=live.valid[current]||!same(v,fxp_defaults);
}
static u32 record(const u8*p){return rd(p)==0x46585331&&p[4]==1&&p[5]==36&&!p[6]&&!p[7]&&rd(p+44)==fxp_crc(p,44)&&fxp_values_ok(p+8);}
static void emit(u8*p,const u8*v,u32 valid){
 zero(p,48);if(!valid)return;wr(p,0x46585331);p[4]=1;p[5]=36;cp(p+8,v,36);wr(p+44,fxp_crc(p,44));
}
static void get_value(u32 ptr,u8*v,u32*valid){
 u32 id=index_at(ptr,project);
 if(ready&&id<96){store_current();*valid=live.valid[id];cp(v,*valid?live.value[id]:fxp_defaults,36);return;}
 for(u32 i=0;i<8;i++)if(clips[i].ptr==ptr){*valid=clips[i].valid;cp(v,*valid?clips[i].value:fxp_defaults,36);return;}
 *valid=0;cp(v,fxp_defaults,36);
}
static void put_value(u32 ptr,const u8*v,u32 valid){
 u32 id=index_at(ptr,project);
 if(ready&&id<96){cp(live.value[id],v,36);live.valid[id]=valid;if(current==id)fxp_apply(valid?v:fxp_defaults);return;}
 u32 slot=8;for(u32 i=0;i<8;i++)if(clips[i].ptr==ptr){slot=i;break;}
 if(slot==8){slot=clip_cursor++&7;clips[slot].ptr=ptr;}
 cp(clips[slot].value,v,36);clips[slot].valid=valid;
}
u32 fxs_revision(void){return revision;}
void fxs_restore(u32 seen,const u8*v){u32 sr=lock();if(revision==seen)fxp_apply(v);unlock(sr);}
void fxs_change(u32 ptr){
 if(!ready||!ptr||project!=raw_now())return;
 u32 id=*(const u32*)(ptr+30706);if(id>95)return;
 u32 sr=lock();
 if(current!=id){
  revision++;store_current();current=id;current_ptr=ptr;
  if(legacy){cp(live.value[id],legacy_value,36);live.valid[id]=!same(legacy_value,fxp_defaults);legacy=0;}
  fxp_apply(live.valid[id]?live.value[id]:fxp_defaults);
  *(volatile u32*)FXP_MENU_ADDRESS=0;revision++;
 }else current_ptr=ptr;
 unlock(sr);
}
void fxs_ui(void){if(!busy&&ready)fxs_change(*(volatile u32*)0x40a7887c);}
void fxs_project_decode_begin(void){decoding++;}
void fxs_project_decode_end(u32 raw,const u8*in,u32 ok){
 if(decoding)decoding--;if(!ok||!raw||!in)return;
 for(u32 i=0;i<96;i++){
  const u8*p=in+512+14848*i+PAD;waiting.valid[i]=rd(in+4)==6&&record(p);
  cp(waiting.value[i],waiting.valid[i]?p+8:fxp_defaults,36);
 }
 waiting_project=raw;
 waiting_legacy=fxp_record_valid(in+0x1c0)&&in[0x1c0+4]==1;
}
void fxs_project_new(u32 raw){zero((u8*)&waiting,sizeof(waiting));waiting_project=raw;waiting_legacy=0;}
void fxs_adopt(u32 raw,const u8*v){
 ready=0;project=0;current=96;current_ptr=0;revision++;
 if(waiting_project==raw){cp((u8*)&live,(const u8*)&waiting,sizeof(live));legacy=waiting_legacy;waiting_project=0;}
 else{zero((u8*)&live,sizeof(live));legacy=0;}
 zero((u8*)clips,sizeof(clips));cp(legacy_value,v,36);project=raw;revision++;ready=1;
}
u32 fxs_project_encode_begin(u32 raw){
 const struct bank*src=0;export_project=raw;
 if(ready&&project==raw){u32 sr=lock();revision++;store_current();revision++;unlock(sr);src=&live;}
 else if(waiting_project==raw)src=&waiting;
 if(src){
  u32 ok=0;for(u32 k=0;k<4;k++){u32 seen=revision;cp((u8*)&exported,(const u8*)src,sizeof(exported));if(seen==revision&&!(seen&1)){ok=1;break;}}
  if(!ok)return 0;
 }else zero((u8*)&exported,sizeof(exported));
 encoding++;return 1;
}
void fxs_project_encode_end(void){if(encoding)encoding--;}
u32 fxs_encode(u8*out,const u8*raw,u32 limit){
 u8 v[36];u32 valid=0;
 if(raw){
  u32 id=index_at((u32)raw,export_project);
  if(encoding&&id<96){valid=exported.valid[id];cp(v,valid?exported.value[id]:fxp_defaults,36);}
  else if(!encoding){u32 sr=lock();get_value((u32)raw,v,&valid);unlock(sr);}
 }
 u32 result=fxs_native_encode(out,raw,limit);
 if((result&255)&&out&&raw&&rd(out)==4)emit(out+PAD,v,valid);
 return result;
}
u32 fxs_decode(u8*raw,const u8*in,u32 id){
 u32 result=fxs_native_decode(raw,in,id);
 if((result&255)&&raw&&in&&!decoding){u32 valid=rd(in)==4&&record(in+PAD);u32 sr=lock();revision++;put_value((u32)raw,valid?in+PAD+8:fxp_defaults,valid);revision++;unlock(sr);}
 return result;
}
u32 fxs_init(u8*raw,u32 flags){
 u32 result=fxs_native_init(raw,flags);
 if(raw&&!decoding&&!busy){u32 sr=lock();revision++;put_value((u32)raw,fxp_defaults,0);revision++;unlock(sr);}
 return result;
}
u32 fxs_copy(u32 dst,u32 src,u32 n){
 u8 v[36];u32 valid=0;
 if(n==STRIDE){u32 sr=lock();get_value(src,v,&valid);unlock(sr);}
 u32 result=fxs_native_copy(dst,src,n);
 if(n==STRIDE){u32 sr=lock();revision++;put_value(dst,v,valid);revision++;unlock(sr);}
 return result;
}
u32 fxs_load(u32 self,u32 slot,u32 cb){busy++;u32 result=fxs_native_load(self,slot,cb);busy--;if(result&255){fxp_sync();fxs_ui();}return result;}
u32 fxs_new_project(u32 self,u32 flags){busy++;u32 result=fxs_native_new_project(self,flags);busy--;fxp_sync();fxs_ui();return result;}
