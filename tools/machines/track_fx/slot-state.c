/* MFT1 : choix par piste et reglages par type, banques de96patterns.
 * Les E/S restent dans le service UI/codec explicite, jamais dans l'audio.
 * Les sauvegardes natives du projet ne sont ni agrandies ni reutilisees.
 */
typedef unsigned int u32;typedef int s32;typedef unsigned char u8;
#define N(a) ((u32(*)())(a))
#define ROW 48u
#define PAYLOAD (ROW*96u)
#define SIZE (16u+PAYLOAD)
extern volatile u32 ch_mode,cr_mode;
extern u32 lt_config[8][4],lt_active;
extern u32 fx_speed,fx_depth,fx_crackle,fx_warble,fx_wspeed,fx_ring_freq,fx_ring_depth,fx_phase_rate,fx_phase_depth,fx_phase_feedback,cr_rate,cr_bits;
extern void mf_old_frame(void);
extern u32 mf_old_project_encode(u8*,const u8*,u32,u32,u32),mf_old_pattern_copy(u32,u32,u32),mf_old_pattern_init(u8*,u32),mf_crc(const u8*,u32);
volatile u32 mf_mode,mf_requested,mf_audio_ready;
volatile u8 mf_live[ROW] __attribute__((aligned(4)));
static u8 bank[96][ROW] __attribute__((aligned(4))),packet[SIZE];
static struct {u32 ptr;u8 data[ROW];} clips[8];
static u32 owner,generation,project,current=96,ready,pending=1,dirty,mode_dirty,mode_loaded,clip_cursor,touch;
static const u8 cfg[24]={42,64,0,0,42,64,0,0,24,24,32,0,80,127,0,0,48,112,64,0,96,12,0,0};
static u32 lock(void){u32 sr;__asm__ volatile("move.w %%sr,%0\nmove.w #0x2700,%%sr":"=d"(sr)::"memory","cc");return sr;}
static void unlock(u32 sr){__asm__ volatile("move.w %0,%%sr"::"d"(sr):"memory","cc");}
static void cp(u8*d,const u8*s,u32 n){while(n--)*d++=*s++;}
static void defaults(u8*p){for(u32 i=0;i<ROW;i++)p[i]=0;cp(p+12,cfg,24);}
static u32 raw(void){u32 p=*(volatile u32*)0x40fe4228;return p?*(volatile u32*)(p+16):0;}
static u32 gen(void){return *(volatile u32*)0x468f6e80;}
static u32 pattern(void){u32 p=*(volatile u32*)0x40a7887c;return p?*(const u32*)(p+30706):96;}
static u32 uuid(u32 r){return r>=0x40000400u&&r<0x42400000u-0x37615cu?*(const u32*)(r+8):0;}
static u32 rev_light(u32 m){return m==1?1:m==2?2:m==3?3:m==9?4:0;}
static u32 del_light(u32 m){return m==1?1:m==2?2:m==11?3:0;}
static u32 rev_ok(u32 m){return m==0||m==1||m==2||m==3||m==7||m==8||m==9||m==10||m==11;}
static u32 del_ok(u32 m){return m==0||m==1||m==2||m==5||m==9||m==10||m==11||m==12;}
static void retired_effects(void){
#ifdef MF_NO_VINYL
 if(ch_mode==3)ch_mode=0;
 for(u32 t=0;t<6;t++)if(mf_live[t]==3)mf_live[t]=0;
 if(mf_live[36]==3)mf_live[36]=0;if(mf_live[38]==3)mf_live[38]=0;
#endif
}
static void import_params(void){
 u32 r=rev_light(ch_mode),d=del_light(cr_mode);
 if(r==1||r==2){mf_live[12+(r-1)*4]=fx_speed;mf_live[13+(r-1)*4]=fx_depth;}
 if(r==3){mf_live[20]=fx_crackle;mf_live[21]=fx_warble;mf_live[22]=fx_wspeed;}
 if(r==4){mf_live[24]=fx_ring_freq;mf_live[25]=fx_ring_depth;}
 if(d==3){mf_live[28]=fx_phase_rate;mf_live[29]=fx_phase_depth;mf_live[30]=fx_phase_feedback;}
 if(d==1||d==2){mf_live[32]=cr_rate;mf_live[33]=cr_bits;}
}
static void runtime(void){
 retired_effects();
 for(u32 e=1;e<7;e++)for(u32 k=0;k<4;k++)lt_config[e][k]=mf_live[12+4*(e-1)+k];
 mf_requested=0;for(u32 t=0;t<12;t++)mf_requested|=mf_live[t];
 if(mf_live[40]){
  ch_mode=mf_live[mf_mode?38:36];cr_mode=mf_live[mf_mode?39:37];
  if(!mf_mode){u32 r=rev_light(ch_mode),d=del_light(cr_mode);
   if(r==1||r==2){fx_speed=mf_live[12+4*(r-1)];fx_depth=mf_live[13+4*(r-1)];}
   if(r==3){fx_crackle=mf_live[20];fx_warble=mf_live[21];fx_wspeed=mf_live[22];}
   if(r==4){fx_ring_freq=mf_live[24];fx_ring_depth=mf_live[25];}
   if(d==3){fx_phase_rate=mf_live[28];fx_phase_depth=mf_live[29];fx_phase_feedback=mf_live[30];}
   if(d==1||d==2){cr_rate=mf_live[32];cr_bits=mf_live[33];}
  }
 }
}
static void seed(void){
 if(mf_live[40])return;u32 r=rev_ok(ch_mode)?ch_mode:0,d=del_ok(cr_mode)?cr_mode:0;
 mf_live[36]=r;mf_live[37]=d;mf_live[38]=rev_light(r)?0:r;mf_live[39]=del_light(d)?0:d;
 for(u32 t=0;t<6;t++){mf_live[t]=rev_light(r);mf_live[6+t]=del_light(d);}import_params();mf_live[40]=1;dirty=1;
}
void mf_seed_pots(void){seed();}
/* Comparaison par mots seulement lorsque toutes les IRQ sont deja masquees.
 * Hors section critique, garder les lectures volatiles historiques par octet. */
typedef u32 capture_word __attribute__((may_alias));
static void capture(void){if(ready&&current<96&&!pending){u8*p=bank[current];u32 sr;__asm__ volatile("move.w %%sr,%0":"=d"(sr));
 if((sr&0x700)==0x700){capture_word*d=(capture_word*)p;const volatile capture_word*s=(const volatile capture_word*)mf_live;for(u32 i=0;i<ROW/4;i++){u32 v=s[i];if(d[i]!=v){d[i]=v;dirty=1;}}}
 else for(u32 i=0;i<ROW;i++)if(p[i]!=mf_live[i]){p[i]=mf_live[i];dirty=1;}}}
static void apply(u32 id){u8 d[ROW];defaults(d);const u8*p=id<96?bank[id]:d;u32 sr=lock();for(u32 i=0;i<ROW;i++)mf_live[i]=p[i];if(mf_mode)seed();runtime();unlock(sr);}
__attribute__((optimize("O2"))) void mf_sync_audio(void){
 retired_effects();
 u32 r=raw(),g=gen();if(!ready||r!=owner||g!=generation){pending=1;mf_requested=mf_audio_ready=0;return;}
 u32 id=pattern();if(id<96&&id!=current){capture();current=id;apply(id);}
}
void mf_touch(void){touch=*(volatile u32*)0xfc07000c;capture();dirty=1;}
void mf_legacy_capture(void){if(!ready||pending||current!=pattern())return;if(!mf_mode&&mf_live[40]){mf_live[36]=rev_ok(ch_mode)?ch_mode:0;mf_live[37]=del_ok(cr_mode)?cr_mode:0;if(!rev_light(ch_mode))mf_live[38]=ch_mode;if(!del_light(cr_mode))mf_live[39]=cr_mode;import_params();capture();}}
void mf_mode_set(u32 value){value=!!value;if(value==mf_mode)return;u32 sr=lock();mf_legacy_capture();if(value)seed();mf_mode=value;runtime();capture();unlock(sr);mode_dirty=1;mf_touch();}
u32 mf_choice(u32 slot,u32 track){retired_effects();if(track>5)return 0;if(!slot){u32 r=mf_live[track];return r==1?1:r==2?2:r==3?3:r==4?9:mf_live[38];}u32 d=mf_live[6+track];return d==1?1:d==2?2:d==3?11:mf_live[39];}
void mf_choose(u32 slot,u32 track,u32 value){
#ifdef MF_NO_VINYL
 if(!slot&&value==3)return;
#endif
 if(track>5||(!slot&&!rev_ok(value))||(slot&&!del_ok(value)))return;u32 sr=lock();seed();if(slot){mf_live[6+track]=del_light(value);if(!del_light(value))mf_live[39]=value;}else{mf_live[track]=rev_light(value);if(!rev_light(value))mf_live[38]=value;}runtime();capture();unlock(sr);mf_touch();}
void mf_config_set(u32 type,u32 index,u32 value){if(type<1||type>6||index>3||value>127||(type==6&&index==1&&(value<2||value>16)))return;u32 sr=lock();mf_live[12+4*(type-1)+index]=value;lt_config[type][index]=value;capture();unlock(sr);mf_touch();}
static void filename(char*p,u32 id){const char h[]="0123456789abcdef",pre[]="/MFX_";for(u32 i=0;i<5;i++)p[i]=pre[i];for(u32 i=0;i<8;i++)p[5+i]=h[(id>>(28-i*4))&15];p[13]='.';p[14]='c';p[15]='f';p[16]='g';p[17]=0;}
static u32 valid(const u8*p){for(u32 id=0;id<96;id++){const u8*v=p+id*ROW;for(u32 t=0;t<6;t++)if(v[t]>4||v[6+t]>3)return 0;for(u32 i=12;i<36;i++)if(v[i]>127)return 0;if(v[33]<2||v[33]>16||!rev_ok(v[36])||!del_ok(v[37])||!rev_ok(v[38])||rev_light(v[38])||!del_ok(v[39])||del_light(v[39])||v[40]>1)return 0;for(u32 i=41;i<ROW;i++)if(v[i])return 0;}return 1;}
static void load(void){
 ready=0;owner=raw();generation=gen();project=uuid(owner);for(u32 id=0;id<96;id++)defaults(bank[id]);for(u32 i=0;i<8;i++)clips[i].ptr=0;
 if(project){char path[20];filename(path,project);u32 h[4]={0};u8 extra;if(!N(0x4007bc5e)(path,"r",h)){u32 ok=N(0x4007baaa)(packet,SIZE,h)==SIZE&&!N(0x4007baaa)(&extra,1,h);N(0x4007bc1c)(h);u32*v=(u32*)packet;if(ok&&v[0]==0x4d465431&&v[1]==project&&v[2]==PAYLOAD&&v[3]==mf_crc(packet+16,PAYLOAD)&&valid(packet+16))cp((u8*)bank,packet+16,PAYLOAD);}}
 current=pattern();dirty=pending=0;ready=mf_audio_ready=1;apply(current);
}
static void save(void){
 u32 sr;__asm__ volatile("move.w %%sr,%0":"=d"(sr));if((sr&0x700)||!ready||pending||owner!=raw()||!dirty)return;capture();project=uuid(owner);if(!project)return;
 u32*head=(u32*)packet;head[0]=0x4d465431;head[1]=project;head[2]=PAYLOAD;cp(packet+16,(const u8*)bank,PAYLOAD);head[3]=mf_crc(packet+16,PAYLOAD);char path[20];filename(path,project);u32 h[4]={0};
 if(!N(0x4007bc5e)(path,"w",h)){u32 ok=!N(0x4007bb76)(h,0,SIZE)&&N(0x4007bb0a)(packet,SIZE,h)==SIZE&&!N(0x4007e2f6)(h);if(N(0x4007bc1c)(h))ok=0;if(ok)dirty=0;}
}
void mf_frame(void){
 mf_old_frame();u32 sr;__asm__ volatile("move.w %%sr,%0":"=d"(sr));if((sr&0x700)||!*(volatile u32*)0x40fe4178||!raw())return;
 if(!mode_loaded){mode_loaded=1;u8 b[8],extra;u32 h[4]={0};if(!N(0x4007bc5e)("/MFXGlobal.cfg","r",h)){u32 ok=N(0x4007baaa)(b,8,h)==8&&!N(0x4007baaa)(&extra,1,h);N(0x4007bc1c)(h);if(ok&&*(u32*)b==0x4d464731&&b[4]<2&&b[5]==(u8)~b[4]&&b[6]==165&&b[7]==90)mf_mode=b[4];}}
 mf_sync_audio();if(pending)load();
 if(mode_dirty&&!*(volatile u32*)0x40a78874&&*(volatile u32*)0xfc07000c-touch>=135168000u){u8 b[8]={77,70,71,49,mf_mode,(u8)~mf_mode,165,90};u32 h[4]={0};if(!N(0x4007bc5e)("/MFXGlobal.cfg","w",h)){u32 ok=!N(0x4007bb76)(h,0,8)&&N(0x4007bb0a)(b,8,h)==8&&!N(0x4007e2f6)(h);if(N(0x4007bc1c)(h))ok=0;if(ok)mode_dirty=0;}}
}
u32 mf_project_encode(u8*out,const u8*in,u32 limit,u32 flags,u32 cb){mf_sync_audio();if(pending&&raw())load();mf_legacy_capture();capture();u32 result=mf_old_project_encode(out,in,limit,flags,cb);if((result&255)&&(flags&16)&&(u32)in==owner)save();return result;}
static u32 at(u32 ptr){if(!owner||ptr<owner+28)return 96;u32 n=ptr-owner-28;return n<96*30710u&&n%30710u==0?n/30710u:96;}
static void get(u32 ptr,u8*out){capture();u32 id=at(ptr);if(id<96){cp(out,bank[id],ROW);return;}for(u32 i=0;i<8;i++)if(clips[i].ptr==ptr){cp(out,clips[i].data,ROW);return;}defaults(out);}
static void put(u32 ptr,const u8*in){u32 id=at(ptr);if(id<96){cp(bank[id],in,ROW);if(current==id)apply(id);dirty=1;return;}u32 n=8;for(u32 i=0;i<8;i++)if(clips[i].ptr==ptr){n=i;break;}if(n==8)n=clip_cursor++&7;clips[n].ptr=ptr;cp(clips[n].data,in,ROW);}
u32 mf_pattern_copy(u32 dst,u32 src,u32 bytes){u8 row[ROW];if(bytes==30710)get(src,row);u32 r=mf_old_pattern_copy(dst,src,bytes);if(bytes==30710)put(dst,row);return r;}
u32 mf_pattern_init(u8*ptr,u32 flags){u32 r=mf_old_pattern_init(ptr,flags);u8 row[ROW];defaults(row);if(ptr&&ready)put((u32)ptr,row);return r;}
