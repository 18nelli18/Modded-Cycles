/* Note 98 : sidecars MPI1 pour le noyau RAM actuel, sans changer son ABI.
 * E/S uniquement UI/IPL0, transport arrete ; deux copies par pattern.
 * Les pointeurs et les phases ne sont jamais serialises.
 */
typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;
typedef signed int i32;
typedef u32 (*Fn)();
enum { CONTEXT,TABLE,EMPTY,PATTERN,PLAY,REPEAT_LOOKUP,REPEAT_PREPARE,
 REPEAT_RESET,REPEAT_PENDING,LOCKS_FOR,LOCKS_RESET,CC_STATE,LFO_SETTINGS,
 LFO_PREPARE,LFO_REFRESH,BANK_SYNC,CLIP_INVALIDATE,UI_DRAIN,POPUP,
 ACTIVE_PATTERN,RUNTIME,CLOCK,ACTIVATE,ASSIGN_CANCEL,OLD_LOAD,
 GENIE_QUEUE,GENIE_UNDO,SG_UNDO,HELD,REMOVE,CHANGED,CFG_INIT,LFO_CONTEXT };
/* Table reliee aux symboles de la recette selectionnee par le navigateur. */
volatile u32 mp_api[33];
#define V(n) (*(volatile u32 *)mp_api[n])
#define CALL(n) ((Fn)mp_api[n])
#define N(a) ((Fn)(a))
#define NOTES 1584u
#define REPEAT 3120u
#define LOCKS 9216u
#define GLOBAL 336u
#define PAYLOAD (NOTES+REPEAT+LOCKS+GLOBAL)
#define HEADER 48u
#define RECORD (HEADER+PAYLOAD)
u32 mp_busy,mp_poison,mp_error,mp_owner,mp_key,mp_slot,mp_serial,mp_loaded[96];
u32 mp_entry_table,mp_entry_serial,mp_entry_id,mp_saving;
static u8 *buffer,*verify;
static u32 seen_serial;
static u32 operation_serial;
static u32 held_table;
static u32 notice_id,notice_slot=0xffffffffu;
static u8 entry[276] __attribute__((aligned(4)));
static u32 retired[96];
static char path[64],name[48];
static u32 root;
static char feedback[20];
static u32 rd32(const u8 *p){return (u32)p[0]<<24|(u32)p[1]<<16|(u32)p[2]<<8|p[3];}
static void wr32(u8 *p,u32 v){p[0]=v>>24;p[1]=v>>16;p[2]=v>>8;p[3]=v;}
static void copy(u8 *d,const u8 *s,u32 n){while(n--)*d++=*s++;}
static void fill(u8 *d,u8 v,u32 n){while(n--)*d++=v;}
void *memcpy(void *d,const void *s,u32 n){copy(d,s,n);return d;}
void *memset(void *d,int v,u32 n){fill(d,(u8)v,n);return d;}
static int equal(const u8 *a,const u8 *b,u32 n){while(n--)if(*a++!=*b++)return 0;return 1;}
u32 mp_crc(const u8 *p,u32 n){u32 c=~0u;while(n--){c^=*p++;for(u32 k=0;k<8;k++)c=c>>1^((0u-(c&1))&0xedb88320u);}return ~c;}
static u32 ipl(void){u16 sr;__asm__ volatile("move.w %%sr,%0":"=d"(sr));return sr&0x700;}
static u32 stopped(void){return *(volatile u32 *)0x40a7883c!=1;}
static u32 identity(void){u32 p=N(0x400cf866)();return p?N(0x4000eae2)(p):0;}
/* L'identite live est renouvelee par Load : seule la fiche sauvegardee
 * fournit la cle disque. Ne jamais comparer cette cle a l'identite live. */
static u32 saved_key(u32 s){u32 p;if(s>95)return 0;p=N(0x400d0a10)();if(!p||N(0x4008c2c2)(p,s)!=6)return 0;return N(0x4008c324)(p,s);}
static int ready(void){
 if(ipl()||!stopped()||!V(CONTEXT)||(!V(TABLE)&&!held_table))return 0;
 if(!buffer)buffer=(u8 *)N(0x400802e0)(RECORD);
 if(!verify)verify=(u8 *)N(0x400802e0)(RECORD);
 return buffer&&verify;
}
static void popup(const char *s){if(mp_api[POPUP])CALL(POPUP)(s);}
static void error_popup(u32 load){
 const char *prefix=load?"MIDI LOAD E":"MIDI SAVE E";copy((u8 *)feedback,(const u8 *)prefix,11);
 feedback[11]='0'+mp_error/10;feedback[12]='0'+mp_error%10;feedback[13]=0;popup(feedback);
}
static int fail(u32 e){mp_error=e;return 0;}
/* Tous les champs musicaux sont controles avant publication. */
u32 mp_values(const u8 *p){
 static const u8 maxima[8]={1,16,127,255,5,4,63,165};
 static const u16 lfo_max[8]={32767,23,32767,128,6,32767,4,32767};
 for(u32 lane=0;lane<6;lane++){
  const u8 *a=p+264*lane;
  if(a[0]>1||a[1]>1||a[2]>15||a[3]<2||a[3]>4||a[4]<1||a[4]>64||a[5]>6)return 0;
  if((signed char)a[6]<-60||(signed char)a[6]>60||a[7]>127)return 0;
  for(u32 i=0;i<64;i++){const u8 *t=a+8+4*i;if(t[0]>127||t[1]>127||t[2]>64)return 0;if((t[3]&1)&&(!t[1]||!t[2]))return 0;}
 }
 p+=NOTES;
 for(u32 i=0;i<390;i++,p+=8){for(u32 k=0;k<8;k++)if(p[k]>maxima[k])return 0;if(!p[5])return 0;}
 for(u32 i=0;i<LOCKS;i+=2)if((p[i]!=255||p[i+1]!=255)&&(p[i]>127||p[i+1]>127))return 0;
 p+=LOCKS;
 for(u32 i=0;i<144;i+=2)if((p[i]!=255&&p[i]>127)||p[i+1]>127)return 0;
 p+=144;
 for(u32 i=0;i<96;i++){u32 v=(u32)p[2*i]<<8|p[2*i+1];if(v>lfo_max[i&7])return 0;}
 return 1;
}
u32 mp_encode(u8 *out,const u8 *payload,u32 id,u32 slot,u32 pattern,u32 generation){
 if(!out||!payload||!id||slot>95||pattern>95||!mp_values(payload))return 0;
 if(out!=payload-HEADER&&(u32)out<(u32)payload+PAYLOAD&&(u32)payload<(u32)out+RECORD)return 0;
 if(out!=payload-HEADER)copy(out+HEADER,payload,PAYLOAD);
 fill(out,0,HEADER);wr32(out,0x4d504931);wr32(out+4,1);wr32(out+8,RECORD);
 wr32(out+12,id);wr32(out+16,slot);wr32(out+20,pattern);wr32(out+24,generation);
 wr32(out+28,mp_crc(out+HEADER,PAYLOAD));wr32(out+44,mp_crc(out,44));return 1;
}
u32 mp_decode(const u8 *r,u32 id,u32 slot,u32 pattern){
 if(!r||!id||slot>95||pattern>95)return 0;
 if(rd32(r)!=0x4d504931||rd32(r+4)!=1||rd32(r+8)!=RECORD||rd32(r+12)!=id||rd32(r+16)!=slot||rd32(r+20)!=pattern)return 0;
 if(rd32(r+32)||rd32(r+36)||rd32(r+40)||rd32(r+44)!=mp_crc(r,44)||rd32(r+28)!=mp_crc(r+HEADER,PAYLOAD))return 0;
 return mp_values(r+HEADER);
}
/* 1=A,2=B,3=absent,0=aucune copie recuperable ou generations ambigues. */
u32 mp_choose(const u8 *a,u32 va,const u8 *b,u32 vb){
 if(!va&&!vb)return 0;if(!va)return 2;if(!vb)return 1;
 u32 delta=rd32(a+24)-rd32(b+24);if(delta==0x80000000u)return 0;
 return (i32)delta>=0?1:2;
}
static void hex8(char *out,u32 v){static const char h[]="0123456789ABCDEF";for(u32 i=0;i<8;i++)out[i]=h[v>>(28-4*i)&15];}
static void make_path(u32 id,u32 slot,u32 pattern,u32 which){
 const char prefix[]="/ModdedCycles/";copy((u8 *)path,(const u8 *)prefix,14);
 copy((u8 *)name,(const u8 *)"MPI1-",5);name[5]='0'+slot/10;name[6]='0'+slot%10;name[7]='-';hex8(name+8,id);
 name[16]='-';name[17]='0'+pattern/10;name[18]='0'+pattern%10;name[19]='-';name[20]='A'+which;name[21]=0;
 copy((u8 *)path+14,(const u8 *)name,22);
}
static int directory(u32 create){
 i32 found=(i32)N(0x4007ad86)(2,"ModdedCycles",entry);
 if(found<0||mp_poison)return -1;
 if(!found&&create){if(N(0x4007ac46)("/ModdedCycles")||mp_poison)return -1;found=(i32)N(0x4007ad86)(2,"ModdedCycles",entry);}
 if(!found)return 0;if(found!=1||((u16 *)entry)[2]!=1||(root=rd32(entry))<2)return -1;return 1;
}
static int presence(void){i32 v=(i32)N(0x4007ad86)(root,name,entry);if(mp_poison||v<0||v>1)return -1;return v;}
static int read_file(u8 *out){
 u32 h[4]={0,0,0,0};i32 n;u32 pos=0;int ok=0;u8 extra;
 if(N(0x4007bc5e)(path,"r",h))return fail(10);
 while(pos<RECORD){u32 count=RECORD-pos;if(mp_serial!=operation_serial||!stopped())goto close;if(count>512)count=512;n=(i32)N(0x4007baaa)(out+pos,count,h);if(n<=0||(u32)n>count)goto close;pos+=(u32)n;}
 n=(i32)N(0x4007baaa)(&extra,1,h);ok=n==0;
close:if(N(0x4007bc1c)(h))ok=0;return ok&&!mp_poison;
}
static int write_file(const u8 *data){
 u32 h[4]={0,0,0,0},pos=0;int ok=0;i32 n;
 if(mp_poison)return fail(11);
 if(N(0x4007bc5e)(path,"w",h))return fail(12);
 if(N(0x4007bb76)(h,0,RECORD))goto close;
 while(pos<RECORD){u32 count=RECORD-pos;if(mp_serial!=operation_serial||!stopped())goto close;if(count>512)count=512;n=(i32)N(0x4007bb0a)(data+pos,count,h);if(n<=0||(u32)n>count||mp_poison)goto close;pos+=(u32)n;}
 if(N(0x4007e2f6)(h)||mp_poison)goto close;ok=1;
close:if(N(0x4007bc1c)(h))ok=0;
 if(!ok||mp_poison)return fail(13);return 1;
}
/* Les fichiers presents mais invalides ne sont jamais traites comme absents. */
static int load_pair(u32 id,u32 slot,u32 pattern){
 u32 valid[2]={0,0},present[2]={0,0};int v;u8 *out[2]={buffer,verify};
 for(u32 i=0;i<2;i++){make_path(id,slot,pattern,i);v=presence();if(v<0)return fail(14);present[i]=v;if(v)valid[i]=read_file(out[i])&&mp_decode(out[i],id,slot,pattern);}
 if(!present[0]&&!present[1])return 3;
 int chosen=(int)mp_choose(buffer,valid[0],verify,valid[1]);if(chosen)mp_error=0;return chosen;
}
static int snapshot(u8 *out,u8 *bank){
 u8 *repeat=(u8 *)CALL(REPEAT_PREPARE)(bank),*locks=(u8 *)CALL(LOCKS_FOR)(bank,1);
 CALL(LFO_PREPARE)();u8 *lfo=(u8 *)V(LFO_SETTINGS);
 if(!repeat||!locks||!lfo)return fail(15);
 copy(out,bank,NOTES);copy(out+NOTES,repeat,REPEAT);copy(out+NOTES+REPEAT,locks,LOCKS);
 copy(out+NOTES+REPEAT+LOCKS,(u8 *)mp_api[CC_STATE],144);copy(out+NOTES+REPEAT+LOCKS+144,lfo,192);
 return mp_values(out);
}
u32 mp_save_pattern(u32 id,u32 slot,u32 pattern,u8 *bank){
 int chosen=load_pair(id,slot,pattern);u32 gen=0,target=0;
 if(!chosen)return fail(16);
 if(chosen!=3){u8 *old=chosen==1?buffer:verify;gen=rd32(old+24)+1;target=chosen==1?1:0;}
 if(mp_serial!=operation_serial||!stopped()||!snapshot(buffer+HEADER,bank)||!mp_encode(buffer,buffer+HEADER,id,slot,pattern,gen))return fail(17);
 make_path(id,slot,pattern,target);if(!write_file(buffer))return 0;
 if(!read_file(verify)||!equal(buffer,verify,RECORD)||!mp_decode(verify,id,slot,pattern)||mp_serial!=operation_serial)return fail(18);
 return 1;
}
/* Save natif : capture d'entree, puis seulement apres son succes. */
void mp_save_enter(void){mp_entry_table=0;mp_entry_id=0;if(ipl()||mp_busy||!V(CONTEXT))return;mp_saving=1;mp_entry_table=V(TABLE);mp_entry_serial=mp_serial;mp_entry_id=identity();}
void mp_save_finish(u32 self,u32 slot){
 mp_saving=0;
 if(ipl()||mp_busy||!V(CONTEXT))return;
 if(!stopped()){popup("STOP TO SAVE MIDI");return;}
 if(slot>95)return;
 if(!ready()){popup("MIDI: NO MEMORY");return;}
 if(!V(TABLE)||held_table){popup("MIDI: RELOAD FIRST");return;}
 if(!mp_entry_table||mp_entry_table!=V(TABLE)||mp_entry_serial!=mp_serial){popup("MIDI: PROJECT CHANGED");return;}
 u32 id=N(0x4000eae2)(self);if(!id||identity()!=id){popup("MIDI: OWNER");return;}
 mp_busy=1;mp_error=0;operation_serial=mp_serial;
 if(directory(1)!=1){fail(19);goto done;}
 CALL(ASSIGN_CANCEL)();CALL(BANK_SYNC)();
 for(u32 i=0;i<96;i++){if(!V(TABLE)||mp_serial!=operation_serial){fail(24);goto done;}u8 *bank=((u8 **)V(TABLE))[i];if(mp_loaded[i]==2){fail(23);goto done;}if(bank){if(!mp_save_pattern(id,slot,i,bank))goto done;mp_loaded[i]=1;}}
 mp_owner=id;mp_key=id;mp_slot=slot;notice_id=id;notice_slot=slot;seen_serial=mp_serial;
done:mp_busy=0;if(mp_error)error_popup(0);else popup("MIDI SAVED");
}
/* La sortie echec doit aussi lever la garde du drain UI. */
void mp_save_result(u32 self,u32 slot,u32 ok){
 mp_saving=0;if(ok&255)mp_save_finish(self,slot);
 else if(!ipl()&&!mp_busy&&V(CONTEXT)&&slot<96)popup("MIDI: SAVE A FAILED");
}
void mp_load_notice(u32 id,u32 slot){
 notice_id=id;notice_slot=slot;
 mp_serial++;
 /* Retirer la table avant le prochain tick ; aucune E/S ni allocation ici. */
 if(V(CONTEXT)&&V(TABLE)){
  held_table=V(TABLE);V(TABLE)=0;
  if(V(RUNTIME)&&V(CLOCK))CALL(ACTIVATE)(mp_api[PLAY],V(RUNTIME),V(CLOCK),V(EMPTY));
  V(PATTERN)=V(EMPTY);
 }
}
static void clear_project(void){
 u32 *table=(u32 *)(held_table?held_table:V(TABLE));u32 context=V(CONTEXT),empty=V(EMPTY);
 /* Lecture arretee, aucun pointeur IRQ vers les anciennes banques. */
 if(V(RUNTIME)&&V(CLOCK))CALL(ACTIVATE)(mp_api[PLAY],V(RUNTIME),V(CLOCK),empty);
 V(PATTERN)=empty;V(REPEAT_PENDING)=1;CALL(REPEAT_RESET)();CALL(LOCKS_RESET)();CALL(CLIP_INVALIDATE)();CALL(ASSIGN_CANCEL)();
 for(u32 i=GENIE_QUEUE;i<=CHANGED;i++)if(mp_api[i])V(i)=0;
 u8 *cc=(u8 *)mp_api[CC_STATE];for(u32 i=0;i<144;i+=2){cc[i]=255;cc[i+1]=64;}
 CALL(LFO_PREPARE)();if(V(LFO_SETTINGS))CALL(CFG_INIT)(V(LFO_SETTINGS));
 if(V(LFO_CONTEXT))fill((u8 *)V(LFO_CONTEXT)+2480,0,532);
 CALL(LFO_REFRESH)();
 for(u32 i=0;i<96;i++){u32 old=table[i];table[i]=0;mp_loaded[i]=0;if(old&&old!=context&&old!=empty)N(0x400802ec)(old);if(retired[i])N(0x400802ec)(retired[i]);retired[i]=0;}
 if(held_table){V(TABLE)=held_table;held_table=0;}
}
u32 mp_restore_pattern(u32 id,u32 slot,u32 pattern){
 int chosen=load_pair(id,slot,pattern);if(chosen==3){mp_loaded[pattern]=1;return 1;}if(!chosen)return fail(20);
 u8 *record=chosen==1?buffer:verify,*bank=(u8 *)N(0x400802e0)(NOTES);if(!bank)return fail(21);
 /* Banques et extensions restent candidates jusqu'a validation/allocation. */
 u8 *repeat=(u8 *)CALL(REPEAT_PREPARE)(bank),*locks=(u8 *)CALL(LOCKS_FOR)(bank,1);
 CALL(LFO_PREPARE)();u8 *lfo=(u8 *)V(LFO_SETTINGS);
 if(!repeat||!locks||!lfo||mp_serial!=operation_serial||!V(TABLE)||!stopped()){/* Les tables auxiliaires possedent deja bank : retrait au prochain changement de projet. */retired[pattern]=(u32)bank;return fail(22);}
 u8 *p=record+HEADER;copy(bank,p,NOTES);copy(repeat,p+NOTES,REPEAT);copy(locks,p+NOTES+REPEAT,LOCKS);
 copy((u8 *)mp_api[CC_STATE],p+NOTES+REPEAT+LOCKS,144);copy(lfo,p+NOTES+REPEAT+LOCKS+144,192);
 u32 old=((u32 *)V(TABLE))[pattern];((u32 *)V(TABLE))[pattern]=(u32)bank;mp_loaded[pattern]=1;
 /* Les index auxiliaires peuvent encore contenir old : retrait apres reset. */
 if(old&&old!=V(CONTEXT)&&old!=V(EMPTY))retired[pattern]=old;
 CALL(BANK_SYNC)();CALL(LFO_REFRESH)();return 1;
}
void mp_ui(void){
 if(ipl()||mp_busy||mp_saving||!stopped()||!V(CONTEXT)||(!V(TABLE)&&!held_table))return;
 u32 id=identity(),slot=N(0x40044d74)(),key=saved_key(slot);
 /* Une notification de Load nommee est prioritaire, meme avant le commit
  * du slot courant ; une working copy 96 utilise la fiche du slot courant. */
 if(seen_serial!=mp_serial&&notice_id&&notice_slot<96){slot=notice_slot;key=notice_id;}
 if(!id||!key||slot>95){
  mp_busy=1;if(held_table||mp_owner!=id||seen_serial!=mp_serial)clear_project();
  mp_owner=id;mp_key=0;mp_slot=0xffffffffu;seen_serial=mp_serial;mp_busy=0;return;
 }
 if(!ready())return;
 mp_busy=1;operation_serial=mp_serial;
 if(mp_owner!=id||mp_key!=key||mp_slot!=slot||seen_serial!=mp_serial||held_table){clear_project();mp_owner=id;mp_key=key;mp_slot=slot;seen_serial=mp_serial;}
 u32 pattern=CALL(ACTIVE_PATTERN)();
 if(pattern<96&&!mp_loaded[pattern]){
  mp_error=0;int found=directory(0);
  if(found==0)mp_loaded[pattern]=1;
  else if(found<0||!mp_restore_pattern(key,slot,pattern)){mp_loaded[pattern]=2;if(!mp_error)mp_error=14;error_popup(1);}
 }
 mp_busy=0;
}
