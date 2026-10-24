typedef unsigned int u32;typedef int s32;typedef unsigned short u16;typedef short s16;typedef unsigned char u8;
#define N(a) ((u32(*)())(a))
extern volatile u32 cr_mode,cr_rate,cr_bits,cr_send[6],ch_mode;
extern volatile u32 menu,bl_latched,bl_physical,bl_function;
extern volatile u32 dx_enabled,dx_peak,dx_over,dx_new,dx_beat_api[3],gr_diag_sum,gr_diag_blocks;
extern volatile u32 br_keys,br_cancel;
extern u32 fx_previous_encoder(u32,const u32*),fx_native_encoder(u32,const u32*),fx_previous_draw(u32,u32),fx_native_keys(u32*),fx_query_original(u32);
extern u32 fx_previous_popup(u32,u32,u32,s32,u32,u32);
extern void fx_notice(const char*),fx_show(u32),cr_service(void);
extern void ch_native(s32*,const s32*,const s16*),ch_chorus(s32*,const s32*,const s16*,u32,u32),cr_post(s32*);
#ifdef FX_POLISH
u32 fx_overlay(u32,u32);void dx7_service(void);
#endif
extern u32 fx_menu_open,fx_menu_slot,fx_menu_cursor,fx_force_active,fx_force_func,fx_force_track,fx_tap_force;
extern u32 fx_speed,fx_depth,fx_crackle,fx_warble,fx_wspeed,fx_aux_ch[6],fx_aux_vi[6],fx_dirty;
#ifdef FX_CHEAP
#ifdef FX_DUCK
#ifdef FX_EXTRA
#define FX_DEL_COUNT 12
#else
#define FX_DEL_COUNT 11
#endif
extern u32 fx_duck_amount,fx_duck_release;
#else
#define FX_DEL_COUNT 10
#endif
void fx_room_reset(void);void fx_room(s32*,const s32*,const s16*);
#elif defined(FX_CLOUD)
#define FX_DEL_COUNT 9
extern u32 fx_cloud_density,fx_cloud_pitch;
void fx_cloud_reset(void);void fx_cloud(s32*);
#elif defined(FX_OCTAVE_POLISH)
#define FX_DEL_COUNT 8
#elif defined(FX_NEW_DELAYS)
#define FX_DEL_COUNT 7
#else
#define FX_DEL_COUNT 5
#endif
#ifdef FX_CHEAP
#ifdef FX_DUCK
#ifdef FX_EXTRA
#define FX_SPECIAL_DELAY(m) ((m)==5||(m)==9||(m)==10||(m)==11)
#else
#define FX_SPECIAL_DELAY(m) ((m)==5||(m)==9||(m)==10)
#endif
#else
#define FX_SPECIAL_DELAY(m) ((m)==5||(m)==9)
#endif
#elif defined(FX_NO_SHIMMER)
#define FX_SPECIAL_DELAY(m) ((m)==5)
#elif defined(FX_LEAN_FX)
#define FX_SPECIAL_DELAY(m) ((m)==5||(m)==6)
#else
#define FX_SPECIAL_DELAY(m) ((m)>=5&&(m)<FX_DEL_COUNT)
#endif
#ifdef FX_PS1
#ifdef FX_CHEAP
#ifdef FX_EXTRA
#ifdef FX_REVERB101
#define FX_REV_COUNT 12
#elif defined(FX_GATED)
#define FX_REV_COUNT 11
#else
#define FX_REV_COUNT 10
#endif
#else
#define FX_REV_COUNT 9
#endif
#else
#define FX_REV_COUNT 8
#endif
void fx_ps1_reset(void);void fx_ps1(s32*,const s32*,const s16*);
#else
#define FX_REV_COUNT 7
#endif
#ifdef FX_LEAN_FX
#ifdef FX_CHEAP
#ifdef FX_EXTRA
#ifdef FX_REVERB101
#define FX_REV_MENU_COUNT 9
#elif defined(FX_GATED)
#define FX_REV_MENU_COUNT 8
#else
#define FX_REV_MENU_COUNT 7
#endif
#else
#define FX_REV_MENU_COUNT 6
#endif
#else
#define FX_REV_MENU_COUNT 5
#endif
#ifdef FX_NO_SHIMMER
#ifdef FX_CHEAP
#ifdef FX_DUCK
#ifdef FX_EXTRA
#define FX_DEL_MENU_COUNT 7
#else
#define FX_DEL_MENU_COUNT 6
#endif
#else
#define FX_DEL_MENU_COUNT 5
#endif
#else
#define FX_DEL_MENU_COUNT 4
#endif
#else
#ifdef FX_DUCK
#ifdef FX_EXTRA
#define FX_DEL_MENU_COUNT 7
#else
#define FX_DEL_MENU_COUNT 6
#endif
#else
#define FX_DEL_MENU_COUNT 5
#endif
#endif
static inline u32 fx_clean_rev(u32 m){return m==4?3:m==5?1:m==6?2:(m<4||m==7
#ifdef FX_CHEAP
||m==8
#ifdef FX_EXTRA
||m==9
#ifdef FX_GATED
||m==10
#ifdef FX_REVERB101
||m==11
#endif
#endif
#endif
#endif
)?m:0;}
#ifdef FX_NO_SHIMMER
static inline u32 fx_clean_del(u32 m){return (m<3||m==5
#ifdef FX_CHEAP
||m==9
#ifdef FX_DUCK
||m==10
#ifdef FX_EXTRA
||m==11
#endif
#endif
#endif
)?m:0;}
#else
static inline u32 fx_clean_del(u32 m){return m==7?6:(m<3||m==5||m==6)?m:0;}
#endif
#else
#define FX_REV_MENU_COUNT FX_REV_COUNT
#define FX_DEL_MENU_COUNT FX_DEL_COUNT
#endif
#ifdef FX_EXTRA
extern u32 fx_ring_freq,fx_ring_depth,fx_phase_rate,fx_phase_depth,fx_phase_feedback;
void fx_ring(s32*,const s32*);void fx_phaser(s32*,const s32*);void fx_extra_reset(u32);
#endif
#ifdef FX_GATED
#ifdef FX_GATED96
#define FX_GATED_LABEL "GATED"
#else
#define FX_GATED_LABEL "Gated"
#endif
extern u32 fx_gate_time;
#ifdef FX_GATE_PREDELAY
extern u32 fx_gate_predelay;
#ifdef FX_REVERB101
u32 fx_gate_delay_ms(u32);void fx_hall_reset(void);void fx_hall(s32*,const s32*,const s16*);
#endif
#endif
void fx_gated(s32*,const s32*,const s16*);void fx_gate_reset(void);void fx_gate_settings(void);u32 fx_input_quiet(void);
#endif
extern const char *const fx_rev_names[FX_REV_COUNT],*const fx_del_names[FX_DEL_COUNT];
extern const u32 fx_rev_order[FX_REV_MENU_COUNT],fx_del_order[FX_DEL_MENU_COUNT];
u32 fx_selected(void);void fx_redraw(void);void fx_service(void);void fx_commit(void);void fx_value(u32,u32*,const char**,const char**);void fx_parameter(u32,int);void fx_vinyl_reset(void);

#ifdef FX_CPU_OPT
void fx_diag_cancel(void);void fx_diag_gesture(const u32*);
#endif
