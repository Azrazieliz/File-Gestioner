/* Show the first page while remote ZIP/CBZ streams into one on-device cache. */
(()=>{
'use strict';
let panel=null,progressLabel=null;
function hide(){panel?.remove();panel=null;progressLabel=null;}
function show(source,filename){
  if(typeof source!=='string'||!source.startsWith('https://fg-assets.invalid/early/'))return;
  hide();
  panel=document.createElement('div');panel.className='fg-early-overlay';
  const info=document.createElement('div');info.className='fg-early-info';
  const label=document.createElement('strong');label.textContent='First page ready';
  progressLabel=document.createElement('span');
  progressLabel.textContent='Downloading remaining pages from cloud…';
  info.append(label,progressLabel);panel.append(info);
  const frame=document.createElement('div');frame.className='fg-early-image-container';
  const image=document.createElement('img');image.src=source;
  image.alt=filename||'First image';image.className='fg-early-image';
  frame.append(image);panel.append(frame);document.body.append(panel);
}
function progress(value,total){
  if(!progressLabel)return;
  const mb=(Number(value)/1048576).toFixed(1),denom=Number(total);
  progressLabel.textContent=denom>0?
    'Reading '+mb+' / '+(denom/1048576).toFixed(1)+' MB from cloud…':
    'Reading '+mb+' MB from cloud…';
}
window.FileGestionerEarly={show,progress,hide};
const previous=window.loadDocument;
if(typeof previous==='function')window.loadDocument=function(info){
  hide();return previous.apply(this,arguments);
};
window.addEventListener('pagehide',hide);
const style=document.createElement('style');
style.textContent=
  '.fg-early-overlay{position:fixed;z-index:9950;inset:0;display:flex;flex-direction:column;background:#0c121c;color:#eef5ff;padding:calc(5px + env(safe-area-inset-top)) 0 calc(5px + env(safe-area-inset-bottom))}'+
  '.fg-early-info{display:flex;gap:4px;flex-direction:column;align-items:center;font:12px/1.5 system-ui;padding:8px}'+
  '.fg-early-info span{color:#bdcee4;font-size:11px}'+
  '.fg-early-image-container{flex:1;min-height:0;display:grid;place-items:center;overflow:hidden}'+
  '.fg-early-image{max-width:100%;max-height:100%;object-fit:contain;display:block}';
document.head.append(style);
})();