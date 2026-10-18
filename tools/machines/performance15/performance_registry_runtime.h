/* SPDX-License-Identifier: MIT
 * Mode Performance : quinze macros, quatre destinations chacune.
 * Sources autonomes de la contribution experimentale (notes/58).
 */
s32 per_param_index(u32 track,u32 id){
 if(track>6||id>255)return -1;
 const PerParameter *p=track==6?per_fx_params:per_track_params;
 u32 count=track==6?PER_FX_COUNT:PER_TRACK_COUNT;
 for(u32 i=0;i<count;i++)if(p[i].id==id)return i;
 return -1;
}
u32 per_param_key(u32 track,u32 id){
 s32 index=per_param_index(track,id);if(index<0)return 0;
 return (track==6?per_fx_params:per_track_params)[index].key;
}
u32 per_param_from_key(u32 track,u32 identity){
 if(track>6)return 0xffffffffu;
 const PerParameter *p=track==6?per_fx_params:per_track_params;
 u32 count=track==6?PER_FX_COUNT:PER_TRACK_COUNT;
 for(u32 i=0;i<count;i++)if(p[i].key==identity)return p[i].id;
 return 0xffffffffu;
}

u32 per_profile_for_track(u32 track){return 0;}
u32 per_param_next_for(u32 profile,u32 track,u32 id,s32 change){
 if(profile>=PER_PROFILE_COUNT)profile=0;
 const PerProfile *p=&per_profiles[profile];
 const u8 *menu=track==6?p->fx:p->track;u32 count=track==6?p->fx_count:p->track_count,index=0;
 for(u32 i=0;i<count;i++)if(menu[i]==id){index=i;break;}
 s32 next=(s32)index+change;if(next<0)next=0;if(next>=(s32)count)next=count-1;
 return menu[next];
}
const char *per_param_name_for(u32 profile,u32 track,u32 id){
 if(track>6)return "INVALID";
 if(profile>=PER_PROFILE_COUNT)profile=0;
 const PerProfile *p=&per_profiles[profile];const u8 *menu=track==6?p->fx:p->track;
 const char *const *names=track==6?p->fx_names:p->track_names;u32 count=track==6?p->fx_count:p->track_count;
 for(u32 i=0;i<count;i++)if(menu[i]==id)return names[i];
 return "INVALID";
}
static s32 per_param_value(const PerParameter *p,s32 value){
 if(value<p->minimum)value=p->minimum;if(value>p->maximum)value=p->maximum;
 if(p->step==256){value=(value+128)&~255;if(value>p->maximum)value=p->maximum;}
 return value;
}
