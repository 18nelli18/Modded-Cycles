/* Banque215 chargee : le sync natif est integralement ecrase par restore.
 * Conserver son seul effet hors contexte (seen=epoch), puis restore natif.
 * Tout chargement, import ou changement de pattern reste sur le chemin215. */
typedef unsigned int u32;
extern volatile u32 ls_ready,ls_current,ls_import_pending,ls_epoch,ls_seen;
extern void ls_original(u32,u32),ls_restore(u32,u32);
void li_sync_fast(u32 ctx,u32 frame){
 u32 pattern=*(volatile u32*)0x40a7887c;
 u32 id=pattern?*(const u32*)(pattern+30706):96;
 if(ctx&&ls_ready&&id<96&&ls_current==id&&!ls_import_pending){
  ls_seen=ls_epoch;ls_restore(ctx,id);return;
 }
 ls_original(ctx,frame);
}
