/* Export SAMP des prises RSG1 : vue canonique seulement, aucun fichier modifie.
 * Aucun acces fichier depuis le parseur/serialiseur RPC. Un seul File natif,
 * lectures dans OPEN/READ uniquement et fermeture native seule. Aucun hook audio.
 * Le hash prive reproduit le code natif, sans toucher son etat global. */
typedef unsigned int u32;typedef int s32;typedef unsigned char u8;typedef short s16;
#define N(a) ((s32(*)())(a))
extern volatile u32 ex_id_mode;
extern u8 ex_hash_state[];extern void ex_hash_update(const void*,u32);extern u32 ex_hash_final(void);
static u32 active,sid,bytes,stereo,gain,open_pending,req_id,req_n,req_off,read_converting,hash_pos,hash_ok,cache_hash,cache_size,cache_tick,closing,closed_sid,closed_size;static u32 *borrowed;
static char path[256],directory[256],cached_path[256];static u8 header[64],mid[2048],side[2048],pcm[4096];
static u32 get(const u8*p){return ((u32)p[0]<<24)|((u32)p[1]<<16)|((u32)p[2]<<8)|p[3];}
static void put(u8*p,u32 x){p[0]=x>>24;p[1]=x>>16;p[2]=x>>8;p[3]=x;}
static void copy(u8*d,const u8*s,u32 n){while(n--)*d++=*s++;}
static u32 string(char*d,const u8*s,u32 n){u32 i=0;for(;i<255&&i<n;i++){d[i]=s[i];if(!s[i])return 1;}d[0]=0;return 0;}
static u32 same(const char*a,const char*b){while(*a&&*a==*b){a++;b++;}return *a==*b;}
static void close(void){active=0;borrowed=0;open_pending=0;read_converting=0;}
static void init_hash(void){for(u32 i=0;i<1216;i++)ex_hash_state[i]=0;put(ex_hash_state+1204,0x43fa243a);put(ex_hash_state+1208,0x43fa243a);put(ex_hash_state+1212,0x43fa243a);hash_pos=0;hash_ok=1;}
static s32 scaled(s32 v){if(gain>=4096){if(v>32767)return 32767;if(v< -32768)return -32768;}v=(v*(s32)gain)>>12;if(v>32767)v=32767;if(v< -32768)v=-32768;return v;}
static u32 disk(void*out,u32 at,u32 n){u32*fh=borrowed+2;if(!borrowed)return 0;fh[1]=at;return N(0x4007baaa)(out,n,fh)==(s32)n;}
u32 ex_read(u8*out,u32 off,u32 n){
 if(!active||off>bytes+64||n>bytes+64-off)return 0;
 while(n){
  if(off<64){u32 k=64-off;if(k>n)k=n;copy(out,header+off,k);out+=k;off+=k;n-=k;continue;}
  u32 width=stereo?4:2,pos=off-64,frame=pos/width,skip=pos%width,frames=(n+skip+width-1)/width;if(frames>1024)frames=1024;
  u32 available=bytes/width-frame;if(frames>available)frames=available;if(!frames)return 0;
  if(!disk(mid,64+frame*2,frames*2))return 0;
  if(stereo&&!disk(side,64+bytes/2+frame*2,frames*2))return 0;
  for(u32 i=0;i<frames;i++){s32 m=(s16)((mid[2*i]<<8)|mid[2*i+1]);if(stereo){s32 s=(s16)((side[2*i]<<8)|side[2*i+1]);s32 l=scaled(m+s),r=scaled(m-s);pcm[4*i]=l>>8;pcm[4*i+1]=l;pcm[4*i+2]=r>>8;pcm[4*i+3]=r;}else{s32 v=scaled(m);pcm[2*i]=v>>8;pcm[2*i+1]=v;}}
  u32 k=frames*width-skip;if(k>n)k=n;copy(out,pcm+skip,k);out+=k;off+=k;n-=k;
 }
 return 1;
}
/* Lecture de l en-tete dans le handler OPEN natif, sur son unique objet File.
 * Les deux positions sont restaurees ; aucun open/close supplementaire. */
void vx_open(u32*file){
 if(!open_pending)return;open_pending=0;active=0;borrowed=0;
 if(!file||file[1]!=0||!((u8*)file)[24])return;
 u32 position=file[10],physical=file[3];file[3]=0;
 s32 got=N(0x4007bf38)(file,header,64);file[3]=physical;file[10]=position;
 if(got!=64||get(header+24)!=0x52534731)return;
 bytes=get(header+4);stereo=get(header+32)&1;gain=get(header+28);if(!gain)gain=4096;
 if(!bytes||bytes>0x2000000||(bytes%(stereo?4:2))||gain>65536||get(header+8)!=48000)return;
 if((u32)N(0x4007c0f2)(file)!=bytes+80)return;
 header[1]=stereo;for(u32 i=24;i<64;i++)header[i]=0;
 borrowed=file;
 /* La compensation de lecture peut depasser le plein niveau WAV. Mesurer
  * le pic LR avant emission, puis reduire uniformement le gain si necessaire.
  * Aucun ecretage ni compression ; les PCM enregistres restent intacts. */
 u32 peak=0,width=stereo?4:2,total=bytes/width;
 for(u32 frame=0;frame<total;){u32 count=total-frame;if(count>1024)count=1024;
  if(!disk(mid,64+frame*2,count*2)||(stereo&&!disk(side,64+bytes/2+frame*2,count*2))){file[3]=physical;file[10]=position;borrowed=0;return;}
  for(u32 i=0;i<count;i++){s32 m=(s16)((mid[2*i]<<8)|mid[2*i+1]);s32 l=m,r=m;if(stereo){s32 s=(s16)((side[2*i]<<8)|side[2*i+1]);l=m+s;r=m-s;}u32 a=l<0?-l:l,b=r<0?-r:r;if(a>peak)peak=a;if(b>peak)peak=b;}
  frame+=count;
 }
 file[3]=physical;file[10]=position;
 if(peak){u32 safe=134213632u/peak;if(gain>safe)gain=safe;}
 sid=file[2];active=1;init_hash();
}
s32 vx_read(u32*file,u8*out,u32 count){
 if(!active||file!=borrowed||!read_converting||req_id!=sid)return N(0x4007bf38)(file,out,count);
 u32 position=file[10],physical=file[3];
 if(position!=req_off||count!=req_n||!ex_read(out,position,count)){file[3]=physical;file[10]=position;close();return -1;}
 file[3]=position+count;file[10]=position+count;return count;
}
void ex_request(const u8*msg){
 if(!ex_id_mode){close();cache_hash=0;return;}
 u32 type=msg[8];const u8*p=*(const u8*const*)(msg+12);const u8*end=*(const u8*const*)(msg+16);if(end<p||end-p<5)return;p+=5;u32 n=end-p;
 if(type==0x10){string(directory,p,n);return;}
 if(type==0x20||type==0x21||type==0x40||type==0x41||type==0x42||type==0x46){cache_hash=0;return;}
 if(type==0x30){close();closing=0;cache_hash=0;if(string(path,p,n))open_pending=1;return;}
 if(type==0x33||type==0x34){close();cache_hash=0;return;}
 if(type==0x35){read_converting=0;return;}
 if(type==0x31){if(active){closing=1;closed_sid=sid;closed_size=bytes+64;}close();return;}
 if((type==0x32||type==0x36)&&n>=12){req_id=get(p);req_n=get(p+4);req_off=get(p+8);read_converting=1;}
}
u32 ex_reply(const u8*msg,u8*p,u32 n){
  if(!ex_id_mode)return n;u32 type=msg[8];
 if((type==0xb0||type==0xb3)&&active&&n>=9){if(p[0]!=1){close();return n;}sid=get(p+1);put(p+5,bytes+64);return n;}
 if((type==0xb2||type==0xb5||type==0xb6||type==0xb7)&&active&&req_id==sid&&p[0]==1){
  u32 prefix=(type==0xb6||type==0xb7)?21:17;if(n<prefix||req_n>n-prefix||req_off>bytes+64){close();return n;}u32 count=req_n;if(count>bytes+64-req_off)count=bytes+64-req_off;
  if(req_off==0)init_hash();if(hash_ok&&req_off==hash_pos){ex_hash_update(p+prefix,count);hash_pos+=count;if(hash_pos==bytes+64){static const u32 zeros[4]={0,0,0,0};ex_hash_update(zeros,16);cache_hash=ex_hash_final()|1;cache_size=bytes+64;cache_tick=*(volatile u32*)0xfc07000c;string(cached_path,(const u8*)path,256);hash_ok=0;}}else hash_ok=0;
  return prefix+count;
 }
 if((type==0xb1||type==0xb4)&&closing&&n>=8&&get(p)==closed_sid){put(p+4,closed_size);closing=0;return n;}
 if((type==0x90||type==0x94)&&cache_hash&&(*(volatile u32*)0xfc07000c-cache_tick)<441000000u){
  u32 at=0;while(at+10<=n){u8*q=p+at;u32 j=at+10;while(j<n&&p[j])j++;if(j==n)break;
   const char*file=(const char*)q+10;u32 slash=0;for(u32 i=0;cached_path[i];i++)if(cached_path[i]=='/')slash=i;
   u32 len=0;while(directory[len])len++;while(len>1&&directory[len-1]=='/')len--;
   u32 parent=(len==slash);if(slash==0&&len==1&&directory[0]=='/')parent=1;for(u32 i=0;parent&&i<slash;i++)if(directory[i]!=cached_path[i])parent=0;
   if(parent&&same(file,cached_path+slash+1)){put(q,cache_hash);put(q+4,cache_size);}
   at=j+1;
  }
 }
 return n;
}

/* Le constructeur initialise seulement l en-tete ; corriger au send final. */
void ex_send(u8 *msg){u8 *p=*(u8**)(msg+12),*end=*(u8**)(msg+16);if(end>=p && (u32)(end-p)>=5){u32 n=ex_reply(msg,p+5,(u32)(end-p)-5);*(u8**)(msg+16)=p+5+n;}}

/* Conserver le cache natif alloue, invalider seulement sa cle au nouvel OPEN. */
void vx_invalidate(u32 *session){u32 *cached=(u32*)session[20];if(cached)cached[1]=0xffffffffu;}
