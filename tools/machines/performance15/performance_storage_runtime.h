/* SPDX-License-Identifier: MIT
 * Persistance native des macros ; rechargement TEMP selectif et metadonnees sans reset audio.
 * Contribution source autonome experimentale (notes/58).
 */
#define PER_PROJECT_KITS 0x409c9c80u
#define PER_KIT_BYTES 0x1bb6u
#define PER_RECORD_OFFSET 0x1d00u
#define PER_RECORD_BYTES 256u
#define PER_EXTRA_KITS 8u
#define PER_STORAGE_SLOTS (96u+PER_EXTRA_KITS)
#define PER_STORAGE_BYTES (PER_STORAGE_SLOTS*(512u+4u)+PER_EXTRA_KITS*4u)
volatile u8 *per_storage_memory DATA=0;
volatile u8 (*per_saved)[256] DATA=0;
volatile u8 (*per_saved_other)[256] DATA=0;
volatile u32 *per_saved_generation DATA=0;
volatile u32 *per_saved_extra DATA=0;

u32 per_storage_initialize(void){
 if(per_storage_memory)return 1;
 u8 *memory=CALL(0x40080064,u8*(*)(u32))(PER_STORAGE_BYTES);
 if(!memory)return 0;
 memset(memory,0,PER_STORAGE_BYTES);
 per_saved=(volatile u8(*)[256])memory;
 per_saved_other=(volatile u8(*)[256])(memory+PER_STORAGE_SLOTS*256u);
 per_saved_generation=(volatile u32*)(memory+PER_STORAGE_SLOTS*512u);
 per_saved_extra=(volatile u32*)(memory+PER_STORAGE_SLOTS*516u);
 __asm__ volatile("":::"memory");per_storage_memory=memory;return 1;
}
extern void per_project_ctor_stock(void*,void*);
void per_project_ctor(void *object,void *project){per_storage_initialize();per_project_ctor_stock(object,project);}
volatile u32 per_edit_epoch DATA=0,per_amount_cache_valid DATA=0,per_amount_cache_slot DATA=0,per_amount_cache_generation DATA=0,per_amount_cache_epoch DATA=0;
volatile u32 per_active_pattern DATA=0,per_active_kit DATA=0,per_storage_reload DATA=0,per_storage_fault DATA=0;
extern u32 per_encode_stock(void*,const void*,u32),per_decode_stock(void*,const void*,u32);

volatile u32 per_temp_decode_kit DATA=0,per_temp_decode_index DATA=0;
const u8 *volatile per_temp_decode_record DATA=0;

volatile u32 per_reload_keep DATA=0;
volatile u32 per_reload_context DATA=0;
u32 per_reload_amounts[3] DATA={0};
static void reload_patch_record(u8 *record);
extern void per_clear_kit_stock(void*),per_commit_stock(void*,void*);
static u16 read16(const u8 *p){return ((u16)p[0]<<8)|p[1];}
static u32 read32(const u8 *p){return ((u32)p[0]<<24)|((u32)p[1]<<16)|((u32)p[2]<<8)|p[3];}
static void write16(u8 *p,u32 v){p[0]=v>>8;p[1]=v;}
static void write32(u8 *p,u32 v){p[0]=v>>24;p[1]=v>>16;p[2]=v>>8;p[3]=v;}
const u32 per_crc_nibbles[16]={0x0u,0x1db71064u,0x3b6e20c8u,0x26d930acu,0x76dc4190u,0x6b6b51f4u,0x4db26158u,0x5005713cu,0xedb88320u,0xf00f9344u,0xd6d6a3e8u,0xcb61b38cu,0x9b64c2b0u,0x86d3d2d4u,0xa00ae278u,0xbdbdf21cu};
static u32 record_crc(const u8 *p){u32 c=0xffffffffu;for(u32 i=0;i<240;i++){c^=p[i];c=(c>>4)^per_crc_nibbles[c&15];c=(c>>4)^per_crc_nibbles[c&15];}return ~c;}
s32 per_storage_slot(const void *kit,u32 create){
 u32 at=(u32)kit,offset=at-PER_PROJECT_KITS;if(!at||!per_storage_memory)return -1;
 if(offset<96u*PER_KIT_BYTES){u32 address=PER_PROJECT_KITS;for(u32 i=0;i<96;i++,address+=PER_KIT_BYTES)if(at==address)return i;}
 for(u32 i=0;i<PER_EXTRA_KITS;i++)if(per_saved_extra[i]==at)return 96+i;
 if(create){for(u32 i=0;i<PER_EXTRA_KITS;i++)if(!per_saved_extra[i]){per_saved_extra[i]=at;return 96+i;}per_storage_fault++;}
 return -1;
}
static volatile u8 *storage_bank(u32 slot,u32 generation){return generation&1?per_saved_other[slot]:per_saved[slot];}
static volatile u8 *storage_pending(u32 slot){return storage_bank(slot,per_saved_generation[slot]+1);}
static void storage_publish(u32 slot){__asm__ volatile("":::"memory");per_saved_generation[slot]++;}
void per_storage_snapshot(u32 slot,u8 *out){
 if(slot>=96+PER_EXTRA_KITS||!per_storage_memory){memset(out,0,256);return;}
 u32 generation;
 do{generation=per_saved_generation[slot];volatile u8 *from=storage_bank(slot,generation);for(u32 i=0;i<256;i++)out[i]=from[i];__asm__ volatile("":::"memory");}while(generation!=per_saved_generation[slot]);
}
static void record_initialize(u8 *record){
 memset(record,0,256);write32(record,0x50455246u);record[4]=3;record[5]=15;record[6]=4;write16(record+8,240);
 for(u32 i=0;i<60;i++)write16(record+16+i*4+2,0x100);
}
static void record_defaults(u8 *record){record_initialize(record);write32(record+12,record_crc(record+16));}
u32 per_record_valid(const u8 *r){
 if(!r||read32(r)!=0x50455246u||(r[4]!=2&&r[4]!=3)||r[5]!=15||r[6]!=4||r[7]||read16(r+8)!=240||read16(r+10)||read32(r+12)!=record_crc(r+16))return 0;
 for(u32 i=0;i<60;i++){const u8 *p=r+16+i*4;if((r[4]==2?p[0]:(p[0]&7))>6||p[1]==128||!read16(p+2))return 0;
  if(r[4]==3&&((p[0]&8)||(i%4==1&&(p[0]&128))||(i%4>=2&&(p[0]&240))))return 0;}
 return 1;
}

/* Modifier une copie ; conserver le record TEMP et les schemas futurs opaques. */
static void reload_patch_record(u8 *record){
 if(!per_record_valid(record)){

  if(read32(record)==0x50455246u&&record[4]>3)return;
  record_defaults(record);
 }
 record[4]=3;
 for(u32 i=0;i<3;i++){
  u32 m=4+i*5,amount=per_reload_amounts[i];
  record[16+m*16]=(record[16+m*16]&7)|((amount&15)<<4);
  record[20+m*16]=(record[20+m*16]&7)|((amount>>4)<<4);
 }
 write32(record+12,record_crc(record+16));
}
static u32 storage_irq_lock(void){
 u32 saved;__asm__ volatile("move.w %%sr,%0":"=d"(saved)::"memory");
 u32 masked=saved|0x700u;__asm__ volatile("move.w %0,%%sr"::"d"(masked):"memory","cc");return saved;
}
static void storage_irq_restore(u32 saved){__asm__ volatile("move.w %0,%%sr"::"d"(saved):"memory","cc");}
static void storage_clear_offsets(void){
 per_edit_epoch++;per_amount_cache_valid=0;
 for(u32 m=0;m<15;m++)per_amounts[m]=0;
 per_level_mask=per_fx_mask=0;
 for(u32 t=0;t<6;t++){per_sound_mask[t]=0;per_level_sums[t]=0;for(u32 d=0;d<PER_SOUND_COUNT;d++)per_sound_sums[t][d]=0;}
 for(u32 d=0;d<PER_FX_COUNT;d++)per_fx_sums[d]=0;
}
void per_storage_load(const void *kit){
 u32 irq=storage_irq_lock();
 s32 slot=per_storage_slot(kit,0);u8 snapshot[256];if(slot>=0)per_storage_snapshot(slot,snapshot);const u8 *record=slot<0?0:snapshot;u32 valid=per_record_valid(record);
 storage_clear_offsets();
 for(u32 i=0;i<60;i++){
  volatile Route *r=&per_routes[i/4][i%4];r->track=r->dest=r->on=r->pad=0;r->depth=0;r->reserved=0;
  if(valid){const u8 *p=record+16+i*4;r->track=record[4]==3?(p[0]&7):p[0];r->depth=(signed char)p[1];r->reserved=read16(p+2);u32 id=per_param_from_key(r->track,r->reserved);r->dest=id==0xffffffffu?255:id;r->pad=id==0xffffffffu;}
 }
 if(valid&&record[4]==3)for(u32 m=0;m<15;m++)per_amounts[m]=(record[16+m*16]>>4)|((record[20+m*16]>>4)<<4);
 per_initialized=1;per_storage_reload=0;

 for(u32 t=0;t<7;t++)per_apply(t,(const u16*)(0x800015aeu+t*66u));
 storage_irq_restore(irq);

 if(per_mode&&per_main_view)CALL(0x40076082,void(*)(void*))((void*)per_main_view);
}

u32 per_encode(void *out,const void *kit,u32 options){
 u32 result=per_encode_stock(out,kit,options);
 if((result&255)&&out&&kit){s32 slot=per_storage_slot(kit,0);u8 *tail=(u8*)out+PER_RECORD_OFFSET;
  if(slot>=0)per_storage_snapshot(slot,tail);
  if(slot<0||read32(tail)!=0x50455246u)record_defaults(tail);
 }
 return result;
}
u32 per_decode(void *kit,const void *in,u32 index){
 per_storage_initialize();
 u32 result=per_decode_stock(kit,in,index);s32 slot=per_storage_slot(kit,1);
 if(slot>=0){volatile u8 *pending=storage_pending(slot);for(u32 i=0;i<256;i++)pending[i]=0;
  if(result&255){
   const u8 *record=per_temp_decode_record;
   if(!record||(u32)kit!=per_temp_decode_kit||index!=per_temp_decode_index)record=in?(const u8*)in+PER_RECORD_OFFSET:0;
   if(record&&read32(record)==0x50455246u)for(u32 i=0;i<256;i++)pending[i]=record[i];
  }
  if((result&255)&&per_reload_context&&(u32)kit==per_temp_decode_kit&&index==per_temp_decode_index)
   reload_patch_record((u8*)pending);
  storage_publish(slot);
 }
 if(kit&&(u32)kit==per_active_kit)per_storage_load(kit);
 return result;
}
void per_clear_kit(void *kit){
 per_clear_kit_stock(kit);s32 slot=per_storage_slot(kit,0);if(slot>=0){volatile u8 *pending=storage_pending(slot);for(u32 i=0;i<256;i++)pending[i]=0;storage_publish(slot);}
 if(kit&&(u32)kit==per_active_kit)per_storage_load(kit);
}

void *per_kit_copy(void *out,const void *in,u32 count){
 void *result=CALL(0x4008f1f0,void*(*)(void*,const void*,u32))(out,in,count);
 if(count==PER_KIT_BYTES&&out&&in){s32 from=per_storage_slot(in,0),to=per_storage_slot(out,from>=0);
  if(to>=0){volatile u8 *pending=storage_pending(to);if(from<0){for(u32 i=0;i<256;i++)pending[i]=0;}else per_storage_snapshot(from,(u8*)pending);storage_publish(to);}
  if((u32)out==per_active_kit)per_storage_load(out);
 }
 return result;
}
static void storage_release(void *object){if(!per_storage_memory)return;u32 kit=(u32)object+0x77fa;for(u32 i=0;i<PER_EXTRA_KITS;i++)if(per_saved_extra[i]==kit){if(per_amount_cache_slot==96+i)per_amount_cache_valid=0;per_saved_extra[i]=0;for(u32 j=0;j<256;j++)per_saved[96+i][j]=per_saved_other[96+i][j]=0;}}
void per_clip_destroy(void *object){storage_release(object);CALL(0x400d3b3c,void(*)(void*))(object);}
void per_clip_delete(void *object){storage_release(object);CALL(0x400d3bd6,void(*)(void*))(object);}
extern volatile u8 *per_temp_memory;
extern volatile u32 per_temp_owner,per_temp_owner_valid;
void per_commit(void *pattern,void *kit){
 per_commit_stock(pattern,kit);if(pattern&&kit)per_storage_observe();
}

void per_storage_observe(void){
 if(per_clip_valid&&per_clip_owner!=*(volatile u32*)0x406fa02cu)per_clip_valid=0;
 u32 pattern=*(volatile u32*)0x40a7887cu,kit=*(volatile u32*)0x40a78888u;
 if(!pattern||!kit)return;
 if(per_temp_memory&&per_temp_owner_valid&&per_temp_owner!=*(volatile u32*)0x406fa02cu)per_temp_owner_valid=0;
 if(pattern==per_active_pattern&&kit==per_active_kit&&!per_storage_reload)return;
 u32 irq=storage_irq_lock();
 pattern=*(volatile u32*)0x40a7887cu;kit=*(volatile u32*)0x40a78888u;
 if(pattern&&kit&&(pattern!=per_active_pattern||kit!=per_active_kit||per_storage_reload)){
  per_active_pattern=pattern;per_active_kit=kit;per_storage_load((void*)kit);
 }
 storage_irq_restore(irq);
}

static void per_record_routes(u8 *r){
 record_initialize(r);
 for(u32 i=0;i<60;i++){volatile Route *route=&per_routes[i/4][i%4];u8 *p=r+16+i*4;
  u32 identity=route->reserved?route->reserved:per_param_key(route->track,route->dest);
  p[0]=route->track;p[1]=route->depth;write16(p+2,identity?identity:0x100);
 }
 for(u32 m=0;m<15;m++){u32 amount=per_amounts[m];if(amount>127)amount=127;r[16+m*16]|=(amount&15)<<4;r[20+m*16]|=(amount>>4)<<4;}
 write32(r+12,record_crc(r+16));
}
static void per_storage_notice(u32 slot){
 if(slot<96){void *manager=CALL(0x400cf866,void*(*)(void))();if(manager)CALL(0x400d1f98,void(*)(void*,u32,void*))((u8*)manager+0x74,slot,0);}
}

extern void per_mirror_notify(void*,u32,u32,u32);
/* Jobs natifs de miroirs puis notification du parent, sans remplacement du kit audio. */
static void per_storage_edit_notice(u32 slot){
 if(slot>=96)return;
 u32 *manager=CALL(0x400cf866,u32*(*)(void))();if(!manager)return;
 u32 *model=(u32*)((u8*)manager+0x74);
 u32 *begin=(u32*)model[8],*end=(u32*)model[9];
 for(u32 *p=begin;p<end;p++)if(*p&&model[4])
  per_mirror_notify(model,slot,*p,0);
 if(model[17]==slot){
  begin=(u32*)model[11];end=(u32*)model[12];
  for(u32 *p=begin;p<end;p++)if(*p&&model[4])
   per_mirror_notify(model,slot,*p,1);
 }
 CALL(0x400d0f6c,void(*)(void*,void*))(model,0);
}
/* Linearite du CRC : contribution de chaque bit du montant a position fixe. */
const u32 per_amount_crc[15][7]={{0x77f00d0u,0xefe01a0u,0x1dfc0340u,0x3bf80680u,0xfb52fb5bu,0x2dd4f0f7u,0x5ba9e1eeu},{0x79adc1b6u,0xf35b836cu,0x3dc60099u,0x7b8c0132u,0xecf54eau,0x1d9ea9d4u,0x3b3d53a8u},{0x3408cbb5u,0x6811976au,0xd0232ed4u,0x7b375be9u,0x23839f87u,0x47073f0eu,0x8e0e7e1cu},{0x969fcbd7u,0xf64e91efu,0x37ec259fu,0x6fd84b3eu,0xe0c271abu,0x1af5e517u,0x35ebca2eu},{0xa1ec1617u,0x98a92a6fu,0xea23529fu,0xf37a37fu,0x95c7e89u,0x12b8fd12u,0x2571fa24u},{0xeecb8c08u,0x6e61e51u,0xdcc3ca2u,0x1b987944u,0xeade201u,0x1d5bc402u,0x3ab78804u},{0x6e3c913u,0xdc79226u,0x1b8f244cu,0x371e4898u,0x6b3552d5u,0xd66aa5aau,0x77a44d15u},{0x891d5fb2u,0xc94bb925u,0x49e6740bu,0x93cce816u,0x2dabb054u,0x5b5760a8u,0xb6aec150u},{0xa9610f72u,0x89b318a5u,0xc817370bu,0x4b5f6857u,0xd2b7334bu,0x7e1f60d7u,0xfc3ec1aeu},{0x9d02e2aau,0xe174c315u,0x1998806bu,0x333100d6u,0xdad33551u,0x6ed76ce3u,0xddaed9c6u},{0x19088711u,0x32110e22u,0x64221c44u,0xc8443888u,0x89163eadu,0xc95d7b1bu,0x49cbf077u},{0x9e6ff41du,0xe7aeee7bu,0x142cdab7u,0x2859b56eu,0x1b23d03bu,0x3647a076u,0x6c8f40ecu},{0x6dfcc142u,0xdbf98284u,0x6c820349u,0xd9040692u,0xcf108ce3u,0x45501f87u,0x8aa03f0eu},{0x1d596ee9u,0x3ab2ddd2u,0x7565bba4u,0xeacb7748u,0x1b5fd1d0u,0x36bfa3a0u,0x6d7f4740u},{0xe6273e9eu,0x173f7b7du,0x2e7ef6fau,0x5cfdedf4u,0xc18edfcu,0x1831dbf8u,0x3063b7f0u}};
void per_record_amount(u8 *r,u32 m,u32 amount){
 if(m>=15)return;if(amount>127)amount=127;
 u32 old=(r[16+m*16]>>4)|((r[20+m*16]>>4)<<4),delta=old^amount;
 u32 crc=read32(r+12);
 for(u32 bit=0;bit<7;bit++)if(delta&(1u<<bit))crc^=per_amount_crc[m][bit];
 r[16+m*16]=(r[16+m*16]&15)|((amount&15)<<4);
 r[20+m*16]=(r[20+m*16]&15)|((amount>>4)<<4);
 write32(r+12,crc);
}
static u32 per_edit_publish(u32 slot,u32 pattern,u32 kit,u32 epoch){
 u32 irq=storage_irq_lock();
 if(pattern!=per_active_pattern||kit!=per_active_kit||epoch!=per_edit_epoch){storage_irq_restore(irq);return 0;}
 storage_publish(slot);per_amount_cache_slot=slot;per_amount_cache_generation=per_saved_generation[slot];per_amount_cache_epoch=epoch;per_amount_cache_valid=1;
 storage_irq_restore(irq);return 1;
}
static void per_storage_edit(void){
 s32 slot=per_storage_slot((void*)per_active_kit,1);if(slot<0)return;
 u32 pattern=per_active_pattern,kit=per_active_kit,epoch=per_edit_epoch;
 per_record_routes((u8*)storage_pending(slot));
 if(per_edit_publish(slot,pattern,kit,epoch))per_storage_edit_notice(slot);
}
void per_storage_amount_edit(u32 m){
 s32 slot=per_storage_slot((void*)per_active_kit,1);if(slot<0)return;
 if(m>=15||!per_amount_cache_valid||per_amount_cache_slot!=(u32)slot||per_amount_cache_generation!=per_saved_generation[slot]||per_amount_cache_epoch!=per_edit_epoch){per_storage_edit();return;}
 u32 pattern=per_active_pattern,kit=per_active_kit,epoch=per_edit_epoch;
 u8 *pending=(u8*)storage_pending(slot);per_storage_snapshot(slot,pending);
 per_record_amount(pending,m,per_amounts[m]);
 if(per_edit_publish(slot,pattern,kit,epoch))per_storage_edit_notice(slot);
}

#define PER_TEMP_BYTES (96u*524u)
volatile u8 *per_temp_memory DATA=0;
volatile u32 per_temp_owner DATA=0,per_temp_owner_valid DATA=0;
u32 per_temp_initialize(void){
 if(per_temp_memory)return 1;
 u8 *memory=CALL(0x40080064,u8*(*)(u32))(PER_TEMP_BYTES);
 if(!memory)return 0;
 memset(memory,0,PER_TEMP_BYTES);__asm__ volatile("":::"memory");per_temp_memory=memory;return 1;
}
static volatile u32 *temp_generations(void){return (volatile u32*)(per_temp_memory+96u*512u);}
static volatile u8 *temp_record(u32 index,u32 generation){return per_temp_memory+((generation&1)*96u+index)*256u;}
static volatile u32 *temp_project(u32 index,u32 generation){return (volatile u32*)(per_temp_memory+96u*516u)+((generation&1)*96u+index);}
static u32 temp_current(u32 index){return index<96&&per_active_pattern&&per_active_kit&&*(volatile u32*)(per_active_pattern+0x77f2)==index;}
static void temp_publish(u32 index,u32 project,const u8 *record){
 u32 generation=temp_generations()[index]+1;volatile u8 *to=temp_record(index,generation);
 for(u32 i=0;i<256;i++)to[i]=record[i];*temp_project(index,generation)=project;
 __asm__ volatile("":::"memory");temp_generations()[index]=generation;
}
static void temp_session(u32 project){
 if(!per_temp_owner_valid||per_temp_owner!=project){for(u32 i=0;i<96;i++)temp_generations()[i]=0;per_temp_owner=project;per_temp_owner_valid=1;}
}
u32 per_temp_snapshot(u32 index,u32 project,u8 *out){
 if(!per_temp_memory||!per_temp_owner_valid||per_temp_owner!=project||index>=96)return 0;
 u32 generation,identity;
 do{generation=temp_generations()[index];if(!generation)return 0;identity=*temp_project(index,generation);volatile u8 *from=temp_record(index,generation);for(u32 i=0;i<256;i++)out[i]=from[i];__asm__ volatile("":::"memory");}while(generation!=temp_generations()[index]);
 return identity==project;
}
extern u32 per_temp_save_stock(void*,u32,u32,u32,u32),per_temp_reload_stock(void*,u32,u32,u32,u32);
u32 per_temp_save(void *manager,u32 temp,u32 index,u32 sequence,u32 kit){
 per_storage_observe();
 u8 record[256];u32 capture=(temp&255)&&(kit&255)&&temp_current(index)&&per_temp_initialize();
 u32 project=0,pattern=per_active_pattern;
 if(capture){project=CALL(0x4000eae2,u32(*)(void*))(manager);temp_session(project);s32 slot=per_storage_slot((void*)per_active_kit,0);
  if(slot>=0)per_storage_snapshot(slot,record);else memset(record,0,256);

  if(read32(record)!=0x50455246u||(record[4]==2||record[4]==3))per_record_routes(record);
 }
 u32 result=per_temp_save_stock(manager,temp,index,sequence,kit);
 if((result&255)&&capture&&pattern==per_active_pattern&&temp_current(index)&&project==CALL(0x4000eae2,u32(*)(void*))(manager))temp_publish(index,project,record);
 return result;
}
u32 per_temp_reload(void *manager,u32 temp,u32 index,u32 sequence,u32 kit){
 per_storage_observe();
 u8 record[256];u32 project=0,restore=0;
 u32 keep=per_reload_keep&&(temp&255)&&(kit&255)&&temp_current(index);
 if(keep){
  for(u32 i=0;i<3;i++)per_reload_amounts[i]=per_amounts[4+i*5];
  per_temp_decode_kit=per_active_kit;per_temp_decode_index=index;
  per_reload_context=1;
 }
 if((temp&255)&&(kit&255)&&temp_current(index)&&per_temp_memory){project=CALL(0x4000eae2,u32(*)(void*))(manager);temp_session(project);restore=per_temp_snapshot(index,project,record);}

 if(restore){if(keep)reload_patch_record(record);per_temp_decode_kit=per_active_kit;per_temp_decode_index=index;per_temp_decode_record=record;}
 u32 result=per_temp_reload_stock(manager,temp,index,sequence,kit);
 per_reload_context=0;per_temp_decode_record=0;per_temp_decode_kit=per_temp_decode_index=0;
 if((result&255)&&restore&&temp_current(index)&&project==CALL(0x4000eae2,u32(*)(void*))(manager)){
  s32 slot=per_storage_slot((void*)per_active_kit,1);
  if(slot>=0){volatile u8 *to=storage_pending(slot);for(u32 i=0;i<256;i++)to[i]=record[i];storage_publish(slot);per_storage_load((void*)per_active_kit);per_storage_notice(slot);}
 }
 return result;
}

u32 per_storage_key(u32 id,u32 flags){
 if(!(flags&16))return 1;
 per_storage_observe();
 if(!per_active_pattern)return 0;
 u32 slot=*(volatile u32*)(per_active_pattern+0x77f2);
 if(slot>=96)return 0;
 void *manager=CALL(0x400cf866,void*(*)(void))();
 if(manager){
  if(id==13)CALL(0x4001040e,u32(*)(void*,u32,u32,u32,u32))(manager,1,slot,1,1);
  else CALL(0x400107d8,u32(*)(void*,u32,u32,u32,u32))(manager,1,slot,1,1);
 }
 return 1;
}
