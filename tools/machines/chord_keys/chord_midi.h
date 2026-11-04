#ifndef CHORD_MIDI_H
#define CHORD_MIDI_H

/* Sortie par piste : ROOT=0 (OS), CHORD=1 ; sauvegardée avec le pattern. */
unsigned ck_ui_midi_get(unsigned track);
void ck_ui_midi_set(unsigned track, unsigned enabled);
unsigned ck_audio_midi_get(unsigned track);

#endif
