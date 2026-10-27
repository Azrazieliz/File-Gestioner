/* Progressive zero-gap comic reading, one provider stream, pages available immediately. */
(()=>{
'use strict';
let surface=null,scroll=null,stack=null,status=null,readFull=null;
let pages=0,scale=1,complete=false,points=new Map(),pinchStart=0;
let lastTap=0,lastPos=null;
function setStatus(value){if(status)status.textContent=value;}
function hide(){
 if(surface)surface.remove();
 surface=null;scroll=null;stack=null;status=null;readFull=null;
 pages=0;scale=1;complete=false;points.clear();pinchStart=0;
}
function readFullBook(){
 if(!complete)return;
 const view=scroll,sections=[...stack.children];
 const firstVisible=sections.findIndex(el=>
   el.getBoundingClientRect().bottom>view.getBoundingClientRect().top+10);
 hide();
 const reader=document.querySelector('.fg-archive-scroll');
 const cells=reader?.querySelectorAll('.fg-comic-section');
 if(reader&&cells?.length){
   const n=Math.max(0,Math.min(firstVisible,cells.length-1));
   requestAnimationFrame(()=>requestAnimationFrame(()=>{
     reader.scrollTop=cells[n].offsetTop-cells[0].offsetTop;
   }));
 }
}
function initialize(){
 if(surface)return;
 surface=document.createElement('section');
 surface.className='fg-progressive-comic';
 surface.setAttribute('role','region');
 surface.setAttribute('aria-label','Progressive comic reading');
 scroll=document.createElement('div');scroll.className='fg-progressive-scroll';
 stack=document.createElement('div');stack.className='fg-progressive-pages';
 scroll.append(stack);surface.append(scroll);
 const foot=document.createElement('div');foot.className='fg-progressive-foot';
 status=document.createElement('span');status.textContent='Receiving comic pages…';
 const library=document.createElement('button');library.textContent='Library';
 library.type='button';
 library.addEventListener('click',()=>{
   hide();window.FileGestionerLibrary?.show?.();
   window.AndroidBridge?.setReadingImmersive?.(false);
 });
 readFull=document.createElement('button');readFull.textContent='Full reader';
 readFull.type='button';readFull.hidden=true;
 readFull.addEventListener('click',readFullBook);
 foot.append(status,readFull,library);surface.append(foot);
 scroll.addEventListener('pointerdown',e=>{
   scroll.setPointerCapture(e.pointerId);
   points.set(e.pointerId,{x:e.clientX,y:e.clientY});
   if(points.size===2){
     const a=[...points.values()];
     pinchStart=Math.hypot(a[0].x-a[1].x,a[0].y-a[1].y);
   }
 });
 scroll.addEventListener('pointermove',e=>{
   if(!points.has(e.pointerId))return;
   const before=points.get(e.pointerId);
   points.set(e.pointerId,{x:e.clientX,y:e.clientY});
   if(points.size===2){
     const a=[...points.values()];
     const span=Math.hypot(a[0].x-a[1].x,a[0].y-a[1].y);
     if(pinchStart>0){
       scale=Math.max(1,Math.min(4,scale*span/pinchStart));
       stack.style.width=Math.round(scale*100)+'%';
     }
     pinchStart=span;
   }else{
     scroll.scrollTop+=before.y-e.clientY;
     if(scale>1)scroll.scrollLeft+=before.x-e.clientX;
   }
 });
 const up=e=>{
   const pos=points.get(e.pointerId);
   points.delete(e.pointerId);
   if(points.size<2)pinchStart=0;
   if(!pos)return;
   const dist=Math.hypot(pos.x-e.clientX,pos.y-e.clientY);
   const now=Date.now();
   if(dist<18&&now-lastTap<350&&lastPos&&
       Math.hypot(lastPos.x-e.clientX,lastPos.y-e.clientY)<52){
     scale=1;stack.style.width='100%';scroll.scrollLeft=0;lastTap=0;
   }else if(dist<18){lastTap=now;lastPos={x:e.clientX,y:e.clientY};}
 };
 scroll.addEventListener('pointerup',up);
 scroll.addEventListener('pointercancel',up);
 document.body.append(surface);
 window.AndroidBridge?.setReadingImmersive?.(true);
}
function append(url,name,index){
 if(typeof url!=='string'||!url.startsWith('https://fg-assets.invalid/early/'))return;
 if(!Number.isInteger(index)||index<0||index>150000)return;
 initialize();
 if(index<pages)return;
 const img=document.createElement('img');img.src=url;
 img.alt='Page '+(index+1)+' · '+name;
 img.loading='eager';img.decoding='async';
 const section=document.createElement('section');
 section.className='fg-progressive-page';section.dataset.page=String(index+1);
 section.append(img);stack.append(section);
 pages++;
 setStatus(pages+' page'+(pages===1?'':'s')+' ready · downloading next…');
}
function progress(bytes,total){
 if(!surface)return;
 const mb=(Number(bytes)/1048576).toFixed(1);
 if(!complete)setStatus(pages+' pages available · '+mb+
   (Number(total)>0?' / '+(Number(total)/1048576).toFixed(1):'')+' MB received');
}
function finish(){
 if(!surface)return;
 complete=true;
 setStatus('All '+pages+' pages are available');
 readFull.hidden=false;
}
window.FileGestionerEarly={append,show:()=>{},progress,hide,finish};
const oldLoad=window.loadDocument;
if(typeof oldLoad==='function'){
 window.loadDocument=function(payload){
   const hadPages=pages>0;
   const result=oldLoad.apply(this,arguments);
   if(hadPages)finish();
   return result;
 };
}
window.addEventListener('pagehide',hide);
const style=document.createElement('style');
style.textContent=[
'.fg-progressive-comic{position:fixed;inset:0;z-index:9900;background:#090c12;color:#dfeaff;display:flex;flex-direction:column;padding-top:env(safe-area-inset-top,0px)}',
'.fg-progressive-scroll{flex:1;min-height:0;overflow:auto;touch-action:none;overscroll-behavior:contain}',
'.fg-progressive-pages{width:100%;margin:0;padding:0;line-height:0}',
'.fg-progressive-page{display:block;width:100%;margin:0;padding:0;border:0;line-height:0;min-height:0}',
'.fg-progressive-page img{display:block;width:100%;height:auto;margin:0;padding:0;border:0;box-shadow:none;vertical-align:top}',
'.fg-progressive-foot{display:flex;align-items:center;gap:7px;padding:4px 8px calc(4px + env(safe-area-inset-bottom,0px));font:11px system-ui;background:#141b29e8}',
'.fg-progressive-foot span{flex:1;color:#b7c5dc;overflow:hidden;text-overflow:ellipsis}',
'.fg-progressive-foot button{color:#f2f6ff;background:#273b61;border:1px solid #405b87;font:12px system-ui;border-radius:7px;padding:6px 9px}',
'.fg-progressive-foot button[hidden]{display:none}'
].join('\n');
document.head.append(style);
})();