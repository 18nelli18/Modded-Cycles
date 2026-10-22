/* SPDX-License-Identifier: MIT
 * Choix RLD par projet dans la marge du bloc natif de reglages (notes/58).
 */
#define PER_RAW_PROJECT_SETTINGS 0x40a700c0u
#define PER_PROJECT_OPTION_OFFSET 0x1f0u
extern u32 per_settings_encode_stock(void*,const void*);
extern u32 per_settings_decode_stock(void*,const void*);
extern void per_settings_clear_stock(void*);
u32 per_settings_encode(void *out,const void *settings){
 u32 result=per_settings_encode_stock(out,settings);
 if((result&255)&&out&&(u32)settings==PER_RAW_PROJECT_SETTINGS){
  u8 *record=(u8*)out+PER_PROJECT_OPTION_OFFSET;
  u32 value=0x01000000u|(per_reload_keep?1u:0u);
  write32(record,0x50524c44u);write32(record+4,~0x50524c44u);
  write32(record+8,value);write32(record+12,~value);
 }
 return result;
}
u32 per_settings_decode(void *settings,const void *in){
 u32 result=per_settings_decode_stock(settings,in);
 if((u32)settings==PER_RAW_PROJECT_SETTINGS){
  u32 keep=0;
  if((result&255)&&in){
   const u8 *record=(const u8*)in+PER_PROJECT_OPTION_OFFSET;
   u32 value=read32(record+8);
   if(read32(record)==0x50524c44u&&read32(record+4)==~0x50524c44u&&
      (value==0x01000000u||value==0x01000001u)&&read32(record+12)==~value)keep=value&1;
  }
  per_reload_keep=keep;
 }
 return result;
}
void per_settings_clear(void *settings){
 per_settings_clear_stock(settings);
 if((u32)settings==PER_RAW_PROJECT_SETTINGS)per_reload_keep=0;
}
