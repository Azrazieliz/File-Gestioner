/* File Gestioner · One mobile interaction system for every supported file type.
   Offline only; does not modify data, conversion or native editor protocols.
   PDF retains its native lazy raster/pinch handler. 3D retains OrbitControls.
*/
(()=>{'use strict';
const $=id=>document.getElementById(id);
const upstream=window.loadDocument;
let generation=0,active=null,observer=null,scheduled=false;
const minScale=.65,maxScale=4;
const clamp=n=>Math.max(minScale,Math.min(maxScale,Math.round(n*1000)/1000));
const element=(tag,className,label)=>{
  const e=document.createElement(tag);e.className=className;
  if(label!==undefined)e.textContent=label;
  return e;
};
function restore(){
  if(active){active.dispose();active=null;}
  observer?.disconnect();observer=null;
  document.getElementById('fg-unified-dock')?.remove();
  document.body.classList.remove('fg-unified-reading','fg-unified-editor');
}
function locate(doc){
  const editor=$('editor');if(!editor)return null;
  const find=query=>editor.querySelector(query);
  if(doc.type==='spreadsheet'){
    const scroller=find('.editorGridWrap'),target=find('table.sheet');
    return scroller&&target?{mode:'layout',scroller,target,kind:'spreadsheet'}:null;
  }
  if(doc.type==='sdocx'){
    const target=find('#sdocxEditor');
    return target?{mode:'text-size',scroller:target,target,kind:'sdocx'}:null;
  }
  if(doc.type==='docx'){
    const target=find('.fg-docx-sheet')||find('.fg-docx-edit-sheet');
    const scroller=find('.fg-docx-scroll')||find('.fg-docx-edit-scroll');
    return target&&scroller?{mode:target.classList.contains('fg-docx-sheet')?'reflow':'text-size',
      scroller,target,kind:'docx'}:null;
  }
  if(doc.type==='reader'||doc.type==='binary'){
    const target=find('.fg-continuous-text')||find('.fg-document-sheet');
    const scroller=find('.fg-text-scroll')||find('.fg-reader-scroll');
    return target&&scroller?{mode:'reflow',scroller,target,kind:'document'}:null;
  }
  if(doc.type==='text'){
    const target=find('#plainTextEditor');
    const scroller=find('.textDoc')||editor;
    return target?{mode:'text-size',scroller,target,kind:'text'}:null;
  }
  if(doc.type==='image'){
    const target=find('.fg-display-image'),scroller=find('.fg-image-surface');
    return target&&scroller?{mode:'image',scroller,target,kind:'image'}:null;
  }
  if(doc.type==='archive'){
    const scroller=find('.fg-archive-scroll');
    const comic=doc.format==='cbz'||doc.readerMode==='comic'||doc.archiveMode==='comic';
    const target=find(comic?'.fg-comic-stack':'.fg-archive-list');
    return target&&scroller?{mode:comic?'width':'layout',
      scroller,target,kind:comic?'comic':'archive'}:null;
  }
  return null;
}
function createController(doc,config){
  const {scroller,target,mode,kind}=config;
  const dock=element('div','fg-unified-dock');
  dock.id='fg-unified-dock';
  dock.setAttribute('role','toolbar');
  dock.setAttribute('aria-label','Reader zoom controls');
  const label=element('button','fg-unified-scale','100%');
  const click=(name,description,act)=>{
    const b=element('button','fg-unified-control',name);
    b.type='button';b.setAttribute('aria-label',description);
    b.addEventListener('click',act);return b;
  };
  let scale=1,disposed=false,pinch=null,lastTap=0,lastPosition=null;
  const settingsKey='fg.view.scale.v1.'+
    String(doc.type||'reader')+':'+String(doc.name||'');
  let savedScale=1;
  try {
    const value=Number(localStorage.getItem(settingsKey));
    if(Number.isFinite(value)&&value>=minScale&&value<=maxScale)savedScale=value;
  }catch(_){} 
  const applyScale=(value)=>{
    if(mode==='reflow')target.style.setProperty('--fg-size',String(value));
    else if(mode==='width'||mode==='image'){
      target.style.width=Math.round(value*100)+'%';
      target.style.maxWidth='none';
      if(mode==='image'){
        target.style.height='auto';
        target.style.display='block';
      }
    }else if(mode==='layout'){
      target.style.zoom=String(value);
    }else if(mode==='text-size'){
      target.style.fontSize=(Math.round(160*value)/10)+'px';
      if(kind==='sdocx')target.style.lineHeight=String(1.55);
    }
  };
  const zoomTo=(next,fx=scroller.clientWidth*.5,fy=scroller.clientHeight*.5)=>{
    if(disposed)return;
    const value=clamp(next);
    if(!Number.isFinite(value)||Math.abs(value-scale)<.002)return;
    const old=scale;
    const anchorX=(scroller.scrollLeft+fx)/old;
    const anchorY=(scroller.scrollTop+fy)/old;
    scale=value;
    applyScale(value);
    label.textContent=Math.round(value*100)+'%';
    try{localStorage.setItem(settingsKey,String(scale));}catch(_){} 
    scroller.scrollLeft=Math.max(0,anchorX*value-fx);
    scroller.scrollTop=Math.max(0,anchorY*value-fy);
  };
  label.addEventListener('click',()=>zoomTo(1));
  label.setAttribute('aria-label','Reset document zoom to 100 percent');
  const zoomOut=click('−','Zoom out',()=>zoomTo(scale/1.25));
  const zoomIn=click('+','Zoom in',()=>zoomTo(scale*1.25));
  const fit=click('Fit','Fit document to screen width',()=>zoomTo(1));
  dock.append(zoomOut,label,zoomIn,fit);
  $('work')?.appendChild(dock);
  document.body.classList.add('fg-unified-reading');
  if(['spreadsheet','sdocx','text'].includes(kind))document.body.classList.add('fg-unified-editor');
  else document.body.classList.remove('fg-unified-editor');
  scroller.classList.add('fg-unified-scroll');
  if(mode==='image')scroller.classList.add('fg-unified-image-scroll');
  const span=(a,b)=>Math.hypot(a.clientX-b.clientX,a.clientY-b.clientY);
  const center=(a,b)=>{
    const r=scroller.getBoundingClientRect();
    return [(a.clientX+b.clientX)*.5-r.left,(a.clientY+b.clientY)*.5-r.top];
  };
  const begin=e=>{
    if(e.touches.length!==2)return;
    const p=center(e.touches[0],e.touches[1]);
    pinch={distance:Math.max(1,span(e.touches[0],e.touches[1])),
      initial:scale,point:p,moved:false};
  };
  const move=e=>{
    if(!pinch||e.touches.length!==2)return;
    if(e.cancelable!==false)e.preventDefault();
    pinch.moved=true;
    const p=center(e.touches[0],e.touches[1]);
    zoomTo(pinch.initial*span(e.touches[0],e.touches[1])/pinch.distance,p[0],p[1]);
  };
  const end=e=>{
    if(pinch){if(e.touches.length<2)pinch=null;return;}
    // Double tap zoom is supported on non-editable image/CBZ/document reader
    // surfaces only, so it never hijacks editing or spreadsheet selection.
    if(['spreadsheet','sdocx','text'].includes(kind)||e.touches.length||
       e.changedTouches.length!==1)return;
    if(e.target?.closest?.('input,textarea,[contenteditable=true],button,select'))return;
    const point=e.changedTouches[0],time=Date.now();
    const coords=[point.clientX,point.clientY];
    if(lastPosition&&time-lastTap<320&&span(
       {clientX:coords[0],clientY:coords[1]},
       {clientX:lastPosition[0],clientY:lastPosition[1]})<30){
      if(e.cancelable!==false)e.preventDefault();
      const rect=scroller.getBoundingClientRect();
      zoomTo(scale>=1.7?1:2,coords[0]-rect.left,coords[1]-rect.top);
      lastTap=0;lastPosition=null;
    }else{lastTap=time;lastPosition=coords;}
  };
  const wheel=e=>{
    if(!e.ctrlKey&&!e.metaKey)return;
    e.preventDefault();
    const rect=scroller.getBoundingClientRect();
    zoomTo(scale*Math.exp(-e.deltaY*.008),e.clientX-rect.left,e.clientY-rect.top);
  };
  scroller.addEventListener('touchstart',begin,{passive:true});
  scroller.addEventListener('touchmove',move,{passive:false});
  scroller.addEventListener('touchend',end,{passive:false});
  scroller.addEventListener('touchcancel',()=>{pinch=null;},{passive:true});
  scroller.addEventListener('wheel',wheel,{passive:false});
  const cleanup=()=>{
    disposed=true;
    scroller.removeEventListener('touchstart',begin);
    scroller.removeEventListener('touchmove',move);
    scroller.removeEventListener('touchend',end);
    scroller.removeEventListener('wheel',wheel);
    scroller.classList.remove('fg-unified-scroll','fg-unified-image-scroll');
    dock.remove();
  };
  if(Math.abs(savedScale-1)>.005)requestAnimationFrame(()=>zoomTo(savedScale));
  return {doc,scroller,target,kind,zoomTo,dispose:cleanup};
}
function scan(doc,nonce){
  if(nonce!==generation)return;
  if(doc.type==='pdf'||doc.type==='model3d'){
    document.body.classList.add('fg-unified-reading');
    return;
  }
  const config=locate(doc);
  if(!config){
    if(active){active.dispose();active=null;}
    return;
  }
  if(active?.target===config.target&&active.scroller===config.scroller)return;
  if(active){active.dispose();active=null;}
  active=createController(doc,config);
}
window.loadDocument=function(doc){
  restore();
  const nonce=++generation;
  upstream(doc);
  scan(doc,nonce);
  // Some editors schedule their DOM after the source picker callback.
  requestAnimationFrame(()=>scan(doc,nonce));
  const editor=$('editor');
  if(window.MutationObserver&&editor){
    observer=new MutationObserver(()=>{
      if(scheduled)return;
      scheduled=true;
      requestAnimationFrame(()=>{scheduled=false;scan(doc,nonce);});
    });
    observer.observe(editor,{childList:true,subtree:false});
  }
};
window.FileGestionerUnifiedReader={
  current:()=>active,
  formats:['pdf','docx','doc','txt','md','epub','odt','ods','odp','rtf','html',
    'json','xml','yaml','csv','tsv','xlsx','xls','sdocx','cbz','zip',
    'png','jpeg','webp','gif','3d'],
  version:'0.11.0'
};
})();
