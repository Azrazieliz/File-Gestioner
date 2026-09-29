from pathlib import Path

APP = Path("app/src/main/assets/app.js")
CSS = Path("app/src/main/assets/style.css")

app = APP.read_text()

old = """  let sdocxModulePromise=null;
  async function loadSdocxModule(){
    if(!sdocxModulePromise)sdocxModulePromise=(async()=>{
      const mod=await import('./sdocx/sdocx.js');
      const b64mod=await import('./sdocx/sdocx_wasm_b64.js');
      const wasm=b64ToBytes(b64mod.default);
      await mod.default({module_or_path:wasm});
      return mod;
    })();
    return sdocxModulePromise;
  }
"""

new = """  let sdocxModulePromise=null;
  function loadClassicScript(src){
    return new Promise((resolve,reject)=>{
      const existing=document.querySelector('script[data-olo-src="'+src+'"]');
      if(existing){
        if(existing.dataset.loaded==='1')return resolve();
        existing.addEventListener('load',()=>resolve(),{once:true});
        existing.addEventListener('error',()=>reject(new Error('Could not load '+src)),{once:true});
        return;
      }
      const s=document.createElement('script');
      s.src=src;
      s.async=true;
      s.dataset.oloSrc=src;
      s.onload=()=>{s.dataset.loaded='1';resolve();};
      s.onerror=()=>reject(new Error('Could not load '+src));
      document.head.appendChild(s);
    });
  }
  async function loadSdocxModule(){
    if(!sdocxModulePromise)sdocxModulePromise=(async()=>{
      await loadClassicScript('sdocx/sdocx.js');
      await loadClassicScript('sdocx/sdocx_wasm_b64.js');
      if(typeof wasm_bindgen==='undefined')throw new Error('SDOCX runtime did not initialize.');
      if(!window.SDOCX_WASM_B64)throw new Error('SDOCX WebAssembly payload is missing.');
      const mod=wasm_bindgen;
      await mod(b64ToBytes(window.SDOCX_WASM_B64));
      return mod;
    })();
    return sdocxModulePromise;
  }
"""

if old not in app:
    raise RuntimeError("Dynamic-import SDOCX loader block not found")
app = app.replace(old, new, 1)
APP.write_text(app)

css = CSS.read_text()
if ".notice{display:none!important}" not in css:
    css += "\n/* Informational notice bars intentionally disabled in all document modes. */\n.notice{display:none!important}\n"
CSS.write_text(css)
