/* L'ABI des trois sites natifs est (piste, pattern, kit, pas, ...).
 * Le quatrieme argument est un index de pas, jamais une note MIDI.
 * Publier la vraie note avant le builder : l'IRQ peut rendre la voix avant
 * que le wrapper Wizard ne fasse sa seconde publication apres son retour.
 */
typedef unsigned int u32;
extern u32 mi_mm_sequence_original(u32,const u32 *,u32,u32);
/* La table UI peut deja contenir le pas suivant quand l'audio retire celui-ci
 * de sa file. Le note-on accepte, apres application des locks, est le seul
 * proprietaire de la note qui sera consommee par le prochain rendu Slice.
 * Aucun getter UI ni aucune E/S dans ce chemin d'interruption audio. */
u32 mi_slice_audio(u32 track,const u32 *event,u32 time,u32 notes){
 if(track<6 && notes && event && event[1]==1 && event[7]<128){
  const volatile unsigned short *params=(const volatile unsigned short *)(0x800015aeu+66*track);
  if(params[9]==(6u<<8))((volatile unsigned char *)0x401ac062)[track]=(unsigned char)event[7];
 }
 return mi_mm_sequence_original(track,event,time,notes);
}
static void capture(u32 track,u32 pattern,u32 step){
 if(track>=6 || step>=64 || !pattern)return;
 const unsigned char *raw=(const unsigned char *)(pattern+722*track);
 u32 note=raw[580+step];
 if(note>127)note=raw[712];
 ((volatile unsigned char *)0x401ac062)[track]=(unsigned char)note;
}
u32 mi_slice_sequence(u32 track,u32 pattern,u32 kit,u32 step,u32 flags,u32 time){
 capture(track,pattern,step);
 return ((u32(*)(u32,u32,u32,u32,u32,u32))0x401bf458)(track,pattern,kit,step,flags,time);
}
u32 mi_slice_preview(u32 track,u32 pattern,u32 kit,u32 step,u32 flags,u32 time){
 capture(track,pattern,step);
 return ((u32(*)(u32,u32,u32,u32,u32,u32))0x400548ce)(track,pattern,kit,step,flags,time);
}
