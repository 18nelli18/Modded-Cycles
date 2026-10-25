/* Image exacte v128 approuvee ; aucun repli vers une composition differente. */
window.MCFixedMainImageMeta={"mainOsSha":"c7fcbbae50ac86ed190cb3d50eea4755137cc546dcc603e26a3f66d2b747b8e2","syxSha256":"a3df9c7ca6e6f566e6747dab872223189e236a18567ba0163523b8b612a5ad0d"};
window.MCFixedMainImageReady=fetch(new URL("all-features-usb-2ch-default.syx?v=2026-10-24-sidechain-mute-main-241",window.location.href),{cache:"no-store"}).then(r=>{if(!r.ok)throw Error("Verified main firmware image could not be loaded");return r.arrayBuffer();}).then(b=>new Uint8Array(b));
