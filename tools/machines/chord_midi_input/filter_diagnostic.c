/* Profil filtre : conserver le repeat approuve et son ABI, puis afficher
 * les memes compteurs P/O/N que le profil sans filtre a la release du combo.
 * Lier mi_beat_popup a br_popup (entree complete), jamais br_popup_out :
 * cet epilogue seul depile le cadre de l'appelant et corrompt le retour.
 * Regression : tools/emu/test_filter_repeat_diagnostic.py. */
typedef unsigned int u32;
extern u32 mi_beat_key_original(const u32 *);
extern volatile u32 mi_beat_keys,mi_diag_peak,mi_diag_over,mi_diag_new;
extern void mi_beat_popup(const char *);
u32 mi_filter_diagnostic_key(const u32 *event){
 u32 before=mi_beat_keys,result=mi_beat_key_original(event);
 if(before==3 && mi_beat_keys!=3){
  char line[40];
  ((u32(*)())0x40000e6e)(line,"P%u O%u N%u",mi_diag_peak/901,mi_diag_over,mi_diag_new);
  mi_beat_popup(line);mi_diag_peak=0;mi_diag_over=0;mi_diag_new=0;
 }
 return result;
}
