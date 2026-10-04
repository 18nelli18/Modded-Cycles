/* Flasher versions, newest first. Shown on the home page and in the flasher.
 * New version: add an entry at the top, with what changed since the previous one:
 *   { version: "1.1", date: "2026-10-15", changes: [{ en: "…", fr: "…" }] }
 */
window.MC_RELEASES = [
  { version: "1.14", date: "2026-10-04", changes: [
    { en: "USB audio: no more dropouts when the processor load changes (Model-TG, muted tracks, effects turning off). The stock OS sends each block to the computer right after computing it, so the moment moved with the load, and the 6-channel mod's buffer only tolerated 0.2 ms of it; each block now leaves at the start of the next one, always at the same moment (0.67 ms more latency), and the 6-channel buffer gains a slot",
      fr: "Audio USB : plus de trous quand la charge du processeur change (Model-TG, pistes mutées, effets qui s'éteignent). L'OS d'origine envoie chaque bloc à l'ordinateur juste après l'avoir calculé, donc à un instant qui bougeait avec la charge, et le tampon du mod 6 canaux n'en tolérait que 0,2 ms ; chaque bloc part maintenant au début du suivant, toujours au même instant (0,67 ms de latence en plus), et le tampon du 6 canaux gagne une case" },
    { en: "6-channel audio with Model-TG: a muted track's stem is no longer cut off (its note rings out, as without Model-TG) and no longer restarts frozen when unmuted",
      fr: "Audio 6 canaux avec Model-TG : la piste USB d'une piste mutée n'est plus coupée net (sa note sonne jusqu'au bout, comme sans Model-TG) et ne repart plus figée au démute" },
    { en: "6-channel audio: the copy of the six tracks to USB is lighter on the processor (same bytes)",
      fr: "Audio 6 canaux : la copie des six pistes vers l'USB est plus légère pour le processeur (mêmes octets)" },
    { en: "Checked in the emulator, with the original OS's USB driver; to be confirmed on the hardware",
      fr: "Vérifié en émulation, avec le pilote USB de l'OS d'origine ; à confirmer sur la machine" },
  ] },
  { version: "1.13", date: "2026-10-03", changes: [
    { en: "New: easier trig removal. On the stock OS, a press on a trig longer than 0.2 s counts as a hold and the trig stays, so the soft keys often needed a second press; with this mod, letting go within half a second removes it",
      fr: "Nouveau : effacer un trig plus facilement. Avec l'OS d'origine, un appui sur un trig de plus de 0,2 s compte comme un maintien et le trig reste, si bien que les touches souples demandaient souvent un second appui ; avec ce mod, relâcher en moins d'une demi-seconde l'efface" },
    { en: "Tested on a real Model:Cycles, with Model-TG, the 5 Syntakt engines, 6-channel audio and the arpeggiator",
      fr: "Testé sur un vrai Model:Cycles, avec Model-TG, les 5 moteurs du Syntakt, l'audio 6 canaux et l'arpégiateur" },
    { en: "Guide: a Removing trigs section, with a key to try the delay",
      fr: "Guide : une section Effacer un trig, avec une touche pour essayer le délai" },
  ] },
  { version: "1.12", date: "2026-10-03", changes: [
    { en: "New: an arpeggiator in place of the retrig. Hold several notes with RETRIG (or A.On) and they play one after another; FUNC + RETRIG gains Arp (direction) and Oct (1 to 4 octaves), saved with the pattern",
      fr: "Nouveau : un arpégiateur à la place du retrig. Tenez plusieurs notes avec RETRIG (ou A.On) et elles se jouent l'une après l'autre ; FUNC + RETRIG gagne Arp (le sens) et Oct (1 à 4 octaves), enregistrés avec le pattern" },
    { en: "Tested on a real Model:Cycles: the arpeggiator, and Model-TG 1.1 with the 5 Syntakt engines and 6-channel audio",
      fr: "Testés sur un vrai Model:Cycles : l'arpégiateur, et Model-TG 1.1 avec les 5 moteurs du Syntakt et l'audio 6 canaux" },
    { en: "Model-TG: in mute mode (held or latched), each track key mutes at once, as with the latching mute alone; Model-TG queued them until you left the mode",
      fr: "Model-TG : en mode mute (tenu ou verrouillé), chaque touche de piste mute tout de suite, comme avec le mute verrouillé seul ; Model-TG les mettait en attente jusqu'à la sortie du mode" },
    { en: "Guide: an Arpeggiator section",
      fr: "Guide : une section Arpégiateur" },
  ] },
  { version: "1.11", date: "2026-10-03", changes: [
    { en: "Model-TG updated to its version 1.1: slide trigs (hold SETTINGS and press a trig key) glide the parameters from one trig to the next, on every machine, the Syntakt engines included",
      fr: "Model-TG passe à sa version 1.1 : les slide trigs (maintenir SETTINGS et appuyer sur une touche de pas) font glisser les paramètres d'un trig au suivant, sur toutes les machines, moteurs du Syntakt compris" },
    { en: "Model-TG 1.1 with the 5 Syntakt engines worked on a real Model:Cycles; its choices stay marked experimental until a firmware built by this page is tried",
      fr: "Model-TG 1.1 avec les 5 moteurs du Syntakt a fonctionné sur un vrai Model:Cycles ; ses choix restent marqués expérimentaux jusqu'à l'essai d'un firmware construit par cette page" },
    { en: "Guide: how to use slide trigs, in the Model-TG section",
      fr: "Guide : l'utilisation des slide trigs, dans la section Model-TG" },
  ] },
  { version: "1.10", date: "2026-10-03", changes: [
    { en: "Guide: a Model-TG section (loading samples, playback modes, Attack and Filter, shortcuts)",
      fr: "Guide : une section Model-TG (charger des échantillons, modes de lecture, Attack et filtre, raccourcis)" },
  ] },
  { version: "1.9", date: "2026-10-02", changes: [
    { en: "Model-TG with the 5 Syntakt engines is now tested on a real Model:Cycles",
      fr: "Model-TG avec les 5 moteurs du Syntakt est maintenant testé sur un vrai Model:Cycles" },
  ] },
  { version: "1.8", date: "2026-10-02", changes: [
    { en: "MACHINES screen: with more than 7 machines, the position dots go on two rows instead of running over the machine picture",
      fr: "Écran MACHINES : au-delà de 7 machines, les points de position passent sur deux lignes au lieu de déborder sur l'image de la machine" },
  ] },
  { version: "1.8", date: "2026-10-02", changes: [
    { en: "Syntakt engines: the flasher takes Syntakt OS 1.42, the version now on elektron.se (1.41 still works: same engines, same firmware)",
      fr: "Moteurs du Syntakt : le flasher accepte l'OS Syntakt 1.42, la version désormais sur elektron.se (la 1.41 marche toujours : mêmes moteurs, même firmware)" },
  ] },
  { version: "1.7", date: "2026-10-02", changes: [
    { en: "Model-TG with the Syntakt engines: a little lighter on the CPU (our busiest code in the fast internal memory, silent tails of the original machines stopped sooner under heavy load)",
      fr: "Model-TG avec les moteurs du Syntakt : un peu plus léger pour le processeur (notre code le plus appelé en mémoire interne rapide, fins de notes inaudibles des machines d'origine arrêtées plus tôt sous forte charge)" },
  ] },
  { version: "1.6", date: "2026-10-01", changes: [
    { en: "Model-TG together with the Syntakt engines: the Sampler stays the 7th machine, the engines follow it (checked in the emulator)",
      fr: "Model-TG avec les moteurs du Syntakt : le Sampler reste la 7e machine, les moteurs le suivent (vérifié en émulation)" },
  ] },
  { version: "1.5", date: "2026-10-01", changes: [
    { en: "Model-TG by TinyGregAudio: a Sampler machine, resampling, retrig and master FX (on its own for now)",
      fr: "Model-TG de TinyGregAudio : machine Sampler, rééchantillonnage, retrig et effets master (seul pour l'instant)" },
  ] },
  { version: "1.4", date: "2026-10-01", changes: [
    { en: "Fewer cut notes when Syntakt voices play together: only sustained load or a really long block cuts a voice",
      fr: "Moins de notes coupées quand les voix du Syntakt jouent ensemble : seule une charge soutenue ou un bloc vraiment trop long coupe une voix" },
  ] },
  { version: "1.3", date: "2026-10-01", changes: [
    { en: "Syntakt voices keep their state in the fast internal memory too",
      fr: "Les voix du Syntakt gardent aussi leur état en mémoire interne rapide" },
  ] },
  { version: "1.2", date: "2026-10-01", changes: [
    { en: "Syntakt engines even lighter: their code now runs from the fast internal memory",
      fr: "Moteurs du Syntakt encore plus légers : leur code s'exécute en mémoire interne rapide" },
  ] },
  { version: "1.1", date: "2026-10-01", changes: [
    { en: "Syntakt engines lighter on the CPU: their work buffers now use the fast internal memory",
      fr: "Moteurs du Syntakt plus légers pour le processeur : leurs tampons de calcul passent en mémoire interne rapide" },
  ] },
  { version: "1.0", date: "2026-10-01", changes: [] },
];
