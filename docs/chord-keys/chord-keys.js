/* Silent examples: C major, DIATONIC palette, SHAPE BASE.
 * Match chord_voicing.c's four-voice choices and chord_name.c's harmonic names.
 * The diminished fifth replaces the third on extended half-diminished chords.
 */
(function () {
  "use strict";
  const host = document.getElementById("chord-device");
  if (!host || !window.MCDevice) return;
  const device = window.MCDevice.render(host, { lit: ["s1", "lcd"], lcd: "CHORD KEYS/>Cmaj9" });
  const notes = ["C", "D", "E", "F", "G", "A", "B"];
  const examples = {
    tri: { positions: [0, 2, 4], names: ["C", "Dm", "Em", "F", "G", "Am", "Bdim"] },
    7: { positions: [0, 2, 4, 6], names: ["Cmaj7", "Dm7", "Em7", "Fmaj7", "G7", "Am7", "Bm7♭5"] },
    9: { positions: [0, 2, 6, 8], names: ["Cmaj9", "Dm9", "Em7(♭9)", "Fmaj9", "G9", "Am9", "Bm7♭5(♭9)"] },
    11: { positions: [0, 2, 6, 10], names: ["Cmaj11", "Dm11", "Em11", "Fmaj7(♯11)", "G11", "Am11", "Bm11♭5"] },
    13: { positions: [0, 2, 6, 12], names: ["Cmaj13", "Dm13", "Em7(♭13)", "Fmaj13", "G13", "Am7(♭13)", "Bm7♭5(♭13)"] }
  };
  const buttons = Array.from(document.querySelectorAll("[data-trig]"));
  const types = Array.from(document.querySelectorAll("[data-extension]"));
  const outName = document.getElementById("chord-name");
  const outNotes = document.getElementById("chord-notes");
  let selected = 0;
  let extension = "9";

  function render() {
    const fr = document.documentElement.lang === "fr";
    const octave = Math.floor(selected / 7);
    const degree = selected % 7;
    const example = examples[extension];
    const positions = example.positions.slice();
    if (degree === 6 && Number(extension) >= 9) positions[1] = 4;
    outName.textContent = example.names[degree];
    outNotes.textContent = positions.map((offset) => notes[(degree + offset) % 7]).join(" · ");
    device.light(["s" + (selected + 1), "lcd"]);
    device.show("CHORD KEYS/>" + example.names[degree].replaceAll("♭", "b").replaceAll("♯", "#"));
    buttons.forEach((button, index) => {
      button.setAttribute("aria-pressed", String(index === selected));
      const position = Math.floor(index / 7);
      const register = position === 0 ? (fr ? "octave de base" : "base octave") : "octave +" + position;
      button.setAttribute("aria-label", "TRIG " + (index + 1) + ": " + example.names[index % 7] + ", " + register);
    });
    types.forEach((button) => button.setAttribute("aria-pressed", String(button.dataset.extension === extension)));
    const registerText = octave ? " · +" + octave + (octave === 1 ? " octave" : " octaves") : "";
    outNotes.textContent += registerText;
  }

  buttons.forEach((button, index) => {
    button.addEventListener("click", () => { selected = index; render(); });
  });
  types.forEach((button) => {
    button.addEventListener("click", () => { extension = button.dataset.extension; render(); });
  });
  document.querySelector(".chord-types").hidden = false;
  document.querySelector(".trig-keys").hidden = false;
  document.querySelector(".demo-hint").hidden = false;
  new MutationObserver(render).observe(document.documentElement, { attributes: true, attributeFilter: ["lang"] });
  render();
})();
