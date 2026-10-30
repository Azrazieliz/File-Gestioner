/* File Gestioner reader navigation, typography, progress and EPUB image zoom. */
(()=>{'use strict';
let reading=null,scroller=null,controls=null,settings=null,lightbox=null,listener=null;
let mode='scroll',frame=0;
const by=s=>document.querySelector(s);
const el=(tag,cls,value)=>{const x=document.createElement(tag);if(cls)x.className=cls;if(value!==undefined)x.textContent=value;return x;};
const btn=(label,tip,fn)=>{const b=el('button','fg-control-button',label);b.type='button';b.title=tip;b.setAttribute('aria-label',tip);b.onclick=fn;return b;};
const saved=(k,f)=>{try{return localStorage.getItem('fg.controls.'+k)||f;}catch(_){return f;}};
const save=(k,v)=>{try{localStorage.setItem('fg.controls.'+k,v);}catch(_){}};
const prefs={bg:saved('bg','#101114'),ink:saved('ink','#e3e0dc'),size:Number(saved('size','19'))||19,font:saved('font','Georgia,serif')};
const validFonts=['Georgia,serif','Arial,sans-serif','system-ui','monospace'];
const findScroll=()=>by('.fg-progressive-scroll')||by('.fg-folder-scroll')||by('.fg-book-scroll')||by('.fg-pdf-scroll')||by('.fg-archive-scroll')||by('.fg-text-scroll')||by('.fg-reader-scroll');
function useStyle(){
 for(const target of [by('.fg-book'),by('.fg-folder-reader'),by('#editor'),by('.fg-progressive-comic')].filter(Boolean)){
   target.style.setProperty('--fg-book-bg',prefs.bg);target.style.setProperty('--fg-book-paper',prefs.bg);
   target.style.setProperty('--fg-book-text',prefs.ink);
   target.style.setProperty('--fg-book-font-size',prefs.size+'px');
   target.style.setProperty('--fg-book-font',validFonts.includes(prefs.font)?prefs.font:'Georgia,serif');
   target.style.setProperty('--fg-reader-paper',prefs.bg);
   target.style.setProperty('--fg-reader-ink',prefs.ink);
   target.style.setProperty('--fg-reader-size',prefs.size+'px');
   target.style.setProperty('--fg-reader-font',prefs.font);
 }
}
function progress(){return !scroller?0:Math.min(1,Math.max(0,scroller.scrollTop/Math.max(1,scroller.scrollHeight-scroller.clientHeight)));}
function move(delta){
 if(!scroller)return;
 const limit=Math.max(0,scroller.scrollHeight-scroller.clientHeight);
 const next=scroller.scrollTop+delta*Math.max(100,scroller.clientHeight*.95);
 if((delta<0&&scroller.scrollTop<12)||(delta>0&&scroller.scrollTop>=limit-12)){
   window.FileGestionerLibrary?.openSibling?.(delta);return;
 }
 scroller.scrollTo({top:Math.max(0,Math.min(limit,next)),behavior:'auto'});
}
function update(){
 if(!controls||!scroller)return;
 const p=progress(),bar=controls.querySelector('.fg-control-progress'),label=controls.querySelector('.fg-control-position');
 if(bar&&!bar.matches(':active'))bar.value=Math.round(p*1000);
 const nodes=scroller.querySelectorAll('.fg-folder-page,.fg-progressive-page,.fg-comic-section,.fg-pdf-section,.fg-book-chapter');
 const total=nodes.length;
 if(!total){label.textContent=Math.round(p*100)+'%';return;}
 const focus=scroller.getBoundingClientRect().top+scroller.clientHeight*.38;
 let best=0,distance=Infinity;
 const center=Math.floor(p*(total-1)),start=total>350?Math.max(0,center-100):0,end=total>350?Math.min(total,start+250):total;
 for(let i=start;i<end;i++){
   const r=nodes[i].getBoundingClientRect();
   const d=focus<r.top?r.top-focus:focus>r.bottom?focus-r.bottom:0;
   if(d<distance){best=i;distance=d;if(d===0)break;}
 }
 label.textContent=(best+1)+' / '+total;
}
function schedule(){if(frame)return;frame=requestAnimationFrame(()=>{frame=0;update();});}
function pageMode(next){
 mode=next;save('mode',mode);
 scroller?.classList.toggle('fg-control-pages',mode==='pages');
 const toggle=controls?.querySelector('.fg-control-mode');
 if(toggle)toggle.textContent=mode==='pages'?'Pages':'Scroll';
}
function closeSettings(){settings?.remove();settings=null;}
function appearance(){
 closeSettings();settings=el('section','fg-control-settings');settings.setAttribute('role','dialog');
 const head=el('div','fg-control-settings-row');
 head.append(el('strong',null,'Reading appearance'),btn('×','Close settings',closeSettings));settings.append(head);
 function field(name,input){const l=el('label','fg-control-field');l.append(el('span',null,name),input);settings.append(l);}
 const fonts=el('select','fg-control-font');
 for(const [value,name] of [['Georgia,serif','Serif'],['Arial,sans-serif','Sans serif'],['system-ui','System'],['monospace','Monospace']]){
  const opt=el('option',null,name);opt.value=value;fonts.append(opt);
 }
 fonts.value=prefs.font;
 fonts.onchange=()=>{prefs.font=fonts.value;save('font',prefs.font);useStyle();};
 field('Font',fonts);
 const size=el('input');size.type='range';size.min=12;size.max=36;size.value=prefs.size;
 size.oninput=()=>{prefs.size=Number(size.value);save('size',prefs.size);useStyle();};
 field('Text size',size);
 for(const [key,label] of [['bg','Background color'],['ink','Text color']]){
  const color=el('input');color.type='color';color.value=prefs[key];
  color.oninput=()=>{prefs[key]=color.value;save(key,prefs[key]);useStyle();};
  field(label,color);
 }
 const presets=el('div','fg-control-settings-row');
 for(const [name,bg,ink] of [['Dark','#101114','#e3e0dc'],['Paper','#f5f2ec','#242426'],['Sepia','#e9dec5','#483825'],['Black','#000000','#ffffff']]){
  presets.append(btn(name,name+' colors',()=>{prefs.bg=bg;prefs.ink=ink;save('bg',bg);save('ink',ink);useStyle();closeSettings();}));
 }
 settings.append(presets);document.body.append(settings);
}
function zoomImage(url){
 if(!url)return;
 closeImage();
 lightbox=el('section','fg-control-lightbox');lightbox.setAttribute('role','dialog');
 const image=el('img','fg-control-big-image');image.src=url;image.alt='Expanded illustration';image.draggable=false;
 const close=btn('×','Close image',closeImage);close.classList.add('fg-control-image-close');
 lightbox.append(image,close);document.body.append(lightbox);
 let scale=1,tx=0,ty=0,gesture=null;
 const distance=(a,b)=>Math.hypot(a.clientX-b.clientX,a.clientY-b.clientY);
 const draw=()=>image.style.transform='translate('+tx+'px,'+ty+'px) scale('+scale+')';
 image.addEventListener('touchstart',e=>{
  if(e.touches.length===2)gesture={span:distance(...e.touches),startScale:scale};
  else if(e.touches.length===1)gesture={x:e.touches[0].clientX,y:e.touches[0].clientY};
 },{passive:true});
 image.addEventListener('touchmove',e=>{
  if(e.touches.length===2&&gesture?.span){if(e.cancelable)e.preventDefault();
   scale=Math.max(1,Math.min(6,gesture.startScale*distance(...e.touches)/Math.max(1,gesture.span)));draw();
  }else if(e.touches.length===1&&gesture?.x!==undefined&&scale>1){
   if(e.cancelable)e.preventDefault();
   tx+=e.touches[0].clientX-gesture.x;ty+=e.touches[0].clientY-gesture.y;
   gesture={x:e.touches[0].clientX,y:e.touches[0].clientY};draw();
  }
 },{passive:false});
 image.addEventListener('touchend',()=>{gesture=null;},{passive:true});
 image.addEventListener('dblclick',()=>{scale=scale>1?1:2;if(scale===1)tx=ty=0;draw();});
}
function closeImage(){lightbox?.remove();lightbox=null;}
function remove(){
 closeSettings();closeImage();
 if(scroller&&listener)scroller.removeEventListener('scroll',listener);
 scroller=null;listener=null;controls?.remove();controls=null;
 if(frame)cancelAnimationFrame(frame);frame=0;
}
function attach(){
 if(window.FileGestionerLibrary?.isVisible?.()){remove();return;}
 const next=findScroll();
 if(!next)return;
 if(next===scroller&&controls){useStyle();update();return;}
 remove();scroller=next;
 controls=el('section','fg-controls');controls.setAttribute('aria-label','Reader navigation');
 const row=el('div','fg-control-row');
 row.append(
  btn('‹','Back to collection',()=>window.FileGestionerLibrary?.show?.()),
  btn('⇤','Previous book',()=>window.FileGestionerLibrary?.openSibling?.(-1)),
  btn('◀','Previous page',()=>move(-1)),
  btn('▶','Next page',()=>move(1)),
  btn('⇥','Next book',()=>window.FileGestionerLibrary?.openSibling?.(1)));
 const toggle=btn('Scroll','Switch between scrolling and page mode',()=>pageMode(mode==='pages'?'scroll':'pages'));
 toggle.classList.add('fg-control-mode');row.append(toggle,btn('Aa','Reader font and colors',appearance));
 row.append(btn('▾','Minimize controls',()=>controls.classList.toggle('fg-controls-mini')));
 controls.append(row);
 const scrub=el('div','fg-control-row fg-control-scrub');
 const slider=el('input','fg-control-progress');slider.type='range';slider.min=0;slider.max=1000;slider.step=1;
 slider.oninput=()=>{const limit=Math.max(0,scroller.scrollHeight-scroller.clientHeight);
  scroller.scrollTo({top:limit*Number(slider.value)/1000,behavior:'auto'});update();};
 const label=el('span','fg-control-position','0%');
 scrub.append(slider,label);controls.append(scrub);document.body.append(controls);
 listener=()=>schedule();scroller.addEventListener('scroll',listener,{passive:true});
 scroller.addEventListener('click',e=>{
  if(mode!=='pages'||e.target?.closest?.('button,input,a,textarea,[contenteditable]'))return;
  const rect=scroller.getBoundingClientRect(),x=e.clientX-rect.left;
  if(x<rect.width*.17)move(-1);else if(x>rect.width*.83)move(1);
 });
 pageMode(saved('mode','scroll'));useStyle();update();
}
document.addEventListener('click',e=>{
 const img=e.target?.closest?.('.fg-book img,.fg-document-sheet img,.fg-folder-page img');
 if(!img||lightbox)return;
 e.preventDefault();e.stopPropagation();zoomImage(img.currentSrc||img.src);
},true);
function renderImageFolder(data){
 const pages=Array.isArray(data.pages)?[...data.pages]:[];
 const editor=by('#editor');
 if(!editor){
   console.error('FG_FOLDER: missing document editor');
   window.FileGestionerLibrary?.show?.();
   return;
 }
 document.body.classList.add('fg-folder-reading');
 const host=el('div','fg-folder-reader');
 const view=el('div','fg-folder-scroll');
 view.setAttribute('role','document');view.setAttribute('aria-label','Folder image reader');
 const stack=el('div','fg-folder-stack');
 const sentinel=el('div','fg-folder-sentinel');
 sentinel.textContent='Loading next images…';
 stack.append(sentinel);view.append(stack);host.append(view);
 editor.replaceChildren(host);
 for(const id of ['sheetBar','spreadsheetTools','textFormat','notice'])
  by('#'+id)?.classList.add('hidden');
 let imageObserver=null,batchObserver=null,index=0,finished=false,busy=false;
 function appendBatch(){
  if(!host.isConnected){imageObserver?.disconnect();batchObserver?.disconnect();return;}
  if(busy||index>=pages.length)return;
  busy=true;
  const frag=document.createDocumentFragment();
  const end=Math.min(pages.length,index+48);
  while(index<end){
   const i=index++,page=pages[i];
   if(!page?.url)continue;
   const section=el('section','fg-folder-page');
   section.dataset.page=String(i+1);
   const image=el('img','fg-folder-image');
   image.alt=page.name||'Image '+i;image.loading='lazy';
   image.decoding='async';image.dataset.src=page.url;
   section.append(image);frag.append(section);
   if(imageObserver)imageObserver.observe(image);
   else image.src=page.url;
  }
  stack.insertBefore(frag,sentinel);
  busy=false;
  sentinel.textContent=finished?
   (index<pages.length?'Continue reading…':'End of folder'):
   (index<pages.length?'Continue reading…':'Receiving more images…');
  // The sentinel observer adds the next batch when it enters the viewport.
 }
 if(window.IntersectionObserver){
  imageObserver=new IntersectionObserver(records=>{
   for(const record of records){
    if(!record.isIntersecting)continue;
    const img=record.target;imageObserver.unobserve(img);
    if(img.dataset.src)img.src=img.dataset.src;
   }
  },{root:view,rootMargin:'120% 0px',threshold:0});
  batchObserver=new IntersectionObserver(records=>{
   for(const r of records)if(r.isIntersecting)appendBatch();
  },{root:view,rootMargin:'160% 0px',threshold:0});
  batchObserver.observe(sentinel);
 }
 const add=incoming=>{
  if(!host.isConnected)return;
  if(!Array.isArray(incoming))return;
  pages.push(...incoming);
  if(index<pages.length&&
     (index===0||sentinel.getBoundingClientRect().top<
       view.getBoundingClientRect().bottom+view.clientHeight))
    requestAnimationFrame(appendBatch);
  sentinel.textContent='Receiving '+pages.length+' images…';
 };
 window.FileGestionerFolder={
  append:payload=>add(payload?.pages),
  done:total=>{finished=true;sentinel.textContent=
   index<pages.length?'Continue reading…':'All '+total+' images received';},
  count:()=>pages.length
 };
 appendBatch();
}
const upstream=window.loadDocument;
window.loadDocument=function(data){
 reading=data;remove();
 if(data?.type==='folderImages'){
   // Existing generic loader has no "folderImages" type. Calling it first
   // can throw or replace the editor after the folder image view was made.
   document.getElementById('home')?.classList.add('hidden');
   document.getElementById('work')?.classList.remove('hidden');
   window.FileGestionerLibrary?.hideForReader?.();
   renderImageFolder(data);
   requestAnimationFrame(()=>requestAnimationFrame(attach));
   return;
 }
 const result=upstream.apply(this,arguments);
 requestAnimationFrame(()=>requestAnimationFrame(attach));
 return result;
};
window.FileGestionerReading={
 attach,close:remove,handleBack:()=>{if(lightbox){closeImage();return true;}
  if(settings){closeSettings();return true;}return false;},
 version:'0.14.0'
};
})();