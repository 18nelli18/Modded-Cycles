/* Master seul : conserver les banques par pattern, ignorer l'ancien choix TRK.
 * La ligne FX reste un indicateur MST sans edition, pour garder l'arbre natif. */
typedef unsigned int u32;
extern volatile u32 mo_mode,mo_loaded,mo_dirty;
extern volatile u32 menu,gc_level,gc_tree_cursor,gc_page,sx_submenu,du_page,mq_page;
extern void mo_old_frame(void);
extern u32 mo_old_key(const u32*),mo_tree_delegate(void);
static u32 global(void){return menu&&gc_level==1&&!gc_page&&!sx_submenu&&!du_page&&!mq_page;}
void mo_frame(void){mo_mode=0;mo_loaded=1;mo_dirty=0;mo_old_frame();}
void mo_set(u32 value){(void)value;mo_mode=0;}
u32 mo_edit(void){return global()&&gc_tree_cursor==9?0:mo_tree_delegate();}
u32 mo_key(const u32*e){if(global()&&gc_tree_cursor==9&&e&&e[3]==32)return 1;return mo_old_key(e);}
