from pathlib import Path

JS=Path("app/src/main/assets/app.js")
CSS=Path("app/src/main/assets/style.css")
code=JS.read_text()
start=code.index("  function renderDocx(focusIndex=null){")
end=code.index("  function persistText(){",start)
replacement=r'''
  /* DOCX text editing: one scrollable document, not 200 disconnected textareas.
     Each editable block maps exactly to the existing paragraph edit interface.
     Rich formatting is retained for unmodified blocks; edited blocks are text-only. */
  function renderDocx(focusIndex=null){
    clearModeBars();
    const total=state.doc.paragraphCount||0;
    let cursor=clamp(focusIndex!==null?focusIndex:state.docStart,0,Math.max(0,total-1));
    const shell=document.createElement('div');shell.className='fg-docx-edit-shell';
    const top=document.createElement('div');top.className='fg-docx-edit-top';
    const start=document.createElement('button');start.textContent='↑ Start';
    const current=document.createElement('span');current.className='fg-docx-edit-counter';
    const help=document.createElement('span');help.className='fg-docx-edit-notice';
    help.textContent='Edit paragraph text · Enter moves to next paragraph · Changes save when you leave a paragraph';
    top.append(start,current,help);shell.appendChild(top);
    const scroll=document.createElement('div');scroll.className='fg-docx-edit-scroll';
    const sheet=document.createElement('article');sheet.className='fg-docx-edit-sheet';
    scroll.appendChild(sheet);shell.appendChild(scroll);
    let loading=false,failed=false,focused=false;
    const batch=48;
    function persist(n){
      if(!n||!n.isConnected)return;
      const next=n.innerText.replace(/\r/g,'').replace(/\u00a0/g,' ');
      if(next!==n.dataset.before){
        try{bridge()?.setParagraph(Number(n.dataset.index),next);n.dataset.before=next;setDirty(true);}
        catch(e){showError(String(e));}
      }
    }
    function append(){
      if(loading||failed||cursor>=total)return;
      loading=true;
      try{
        const raw=bridge()?.getParagraphWindow(cursor,Math.min(batch,total-cursor));
        const items=raw?JSON.parse(raw):[];
        if(!Array.isArray(items)||items.length===0)throw Error('No paragraphs returned by editor');
        const fragment=document.createDocumentFragment();
        for(const [i,text] of items){
          const p=document.createElement('div');
          p.className='fg-docx-edit-paragraph';
          p.contentEditable='true';p.spellcheck=true;
          p.setAttribute('role','textbox');
          p.setAttribute('aria-label','Edit paragraph '+(i+1));
          p.setAttribute('aria-multiline','false');
          p.dataset.index=i;p.dataset.before=text;
          p.textContent=text||'';
          let debounce=null;
          p.oninput=()=>{clearTimeout(debounce);debounce=setTimeout(()=>persist(p),500);};
          p.onblur=()=>{clearTimeout(debounce);persist(p);};
          p.onkeydown=e=>{
            if(e.key==='Enter'){
              e.preventDefault();persist(p);
              const next=p.nextElementSibling;
              if(next?.matches('.fg-docx-edit-paragraph'))next.focus();
              else {append();p.nextElementSibling?.focus();}
            }
          };
          fragment.appendChild(p);
        }
        sheet.appendChild(fragment);
        cursor=Number(items[items.length-1][0])+1;
        current.textContent=cursor+' / '+total+' paragraphs';
        if(focusIndex!==null&&!focused){
          const p=sheet.querySelector('[data-index="'+focusIndex+'"]');
          if(p){focused=true;p.focus();p.scrollIntoView({block:'center'});}
        }
      }catch(e){failed=true;help.textContent='Cannot load more paragraphs: '+String(e.message||e);}
      finally{loading=false;}
    }
    start.onclick=()=>{state.docStart=0;renderDocx();};
    if(total)append();
    else sheet.textContent='This DOCX contains no text paragraphs.';
    let pending=false;
    scroll.addEventListener('scroll',()=>{
      if(pending)return;
      pending=true;
      requestAnimationFrame(()=>{
        pending=false;
        if(scroll.scrollTop+scroll.clientHeight>=scroll.scrollHeight-900)append();
      });
    },{passive:true});
    $('editor').replaceChildren(shell);
    requestAnimationFrame(()=>{
      if(scroll.scrollHeight<=scroll.clientHeight+300)append();
    });
  }
'''
code=code[:start]+replacement+code[end:]
JS.write_text(code)
CSS.write_text(CSS.read_text()+r'''

/* Seamless editable DOCX paragraph flow. Save protocol remains paragraph-indexed. */
.fg-docx-edit-shell{height:100%;display:flex;flex-direction:column;min-height:0;
  background:var(--fg-app-bg);overflow:hidden}
.fg-docx-edit-top{display:flex;align-items:center;gap:12px;flex-wrap:wrap;min-height:52px;
  background:var(--fg-card);border-bottom:1px solid var(--fg-border);padding:8px 14px}
.fg-docx-edit-counter{font:600 12px system-ui;color:var(--fg-text)}
.fg-docx-edit-notice{color:var(--fg-muted);font-size:11px;line-height:1.45;flex:1 1 180px}
.fg-docx-edit-scroll{flex:1;min-height:0;overflow:auto;overscroll-behavior:contain;
  padding:clamp(10px,3vw,24px) 8px 60px}
.fg-docx-edit-sheet{max-width:850px;min-height:78vh;margin:auto;
  padding:clamp(24px,5vw,58px);background:var(--fg-paper);
  color:var(--fg-paper-text);font:400 16px/1.7 Georgia,"Noto Serif",serif;
  box-shadow:0 8px 28px #00000012;border:1px solid var(--fg-reader-border)}
.fg-docx-edit-paragraph{padding:2px 3px;margin:0 0 .65em;min-height:1.4em;
  white-space:pre-wrap;overflow-wrap:anywhere;border:0;border-radius:3px;outline:none;
  caret-color:var(--fg-reader-accent);cursor:text}
.fg-docx-edit-paragraph:focus{background:color-mix(in srgb,var(--fg-reader-accent) 6%,var(--fg-paper));
  box-shadow:inset 3px 0 var(--fg-reader-accent)}
@media(max-width:680px){
  .fg-docx-edit-scroll{padding:8px 6px 60px}
  .fg-docx-edit-sheet{padding:22px 18px;font-size:15px}
}
''')
print("Seamless DOCX text editor installed")
