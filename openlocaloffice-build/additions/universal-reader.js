/* File Gestioner universal offline reader */
(()=>{'use strict';
const $=id=>document.getElementById(id), original=window.loadDocument;
let doc=null, page=0, zoom=1, archiveIndex=0, assetUrl=null, editing=false;
const bridge=()=>window.AndroidBridge||null;
const ro=d=>['pdf','image','reader','archive','binary'].includes(d?.type)||d?.readOnly===true;
function E(tag,cls,text){const n=document.createElement(tag);if(cls)n.className=cls;if(text!==undefined)n.textContent=text;return n;}
function button(label,click){const b=E('button','fg-reader-button',label);b.onclick=click;return b;}
function toolbar(description){
 const t=E('div','fg-reader-toolbar');
 t.append(E('span','fg-reader-kind',(doc.format||doc.type||'file').toUpperCase()),
  E('span','fg-reader-title',doc.name||'Document'),E('span','fg-reader-desc',description));
 const tools=E('div','fg-reader-tools');t.appendChild(tools);return [t,tools];
}
function paper(tag){const p=E('article','fg-page '+(tag||''));p.style.setProperty('--fg-size',String(zoom));return p;}
function stage(t,content,hasTextSearch=false){
 const host=$('editor');host.classList.add('fg-reader-host');host.replaceChildren(t,content);
 for(const id of ['sheetBar','spreadsheetTools','textFormat','notice'])$(id)?.classList.add('hidden');
 document.querySelector('.searchbar')?.classList.toggle('hidden',!hasTextSearch);
 if(ro(doc)){$('saveBtn').disabled=true;$('copyBtn').disabled=true;}
}
function zoomer(bar,render){
 bar.append(button('−',()=>{zoom=Math.max(.7,zoom-.15);render();}),
  E('span','fg-reader-counter',Math.round(zoom*100)+'%'),
  button('+',()=>{zoom=Math.min(2.3,zoom+.15);render();}));
}
function decode(encoded){
 const bin=atob(encoded),out=new Uint8Array(bin.length);
 for(let i=0;i<bin.length;i++)out[i]=bin.charCodeAt(i);
 return out;
}
function localBytes(){
 const b=bridge(),length=Number(b?.getRawDocumentSize?.()||0);
 if(!length||length>80*1024*1024)throw Error('File exceeds safe preview size.');
 const chunks=[],size=120*1024;
 for(let off=0;off<length;off+=size)chunks.push(decode(b.getRawDocumentChunk(off,Math.min(size,length-off))));
 const out=new Uint8Array(length);let pos=0;
 for(const c of chunks){out.set(c,pos);pos+=c.length;}
 return out;
}
/* Continuous PDFs: one vertical document, native aspect-ratio placeholders,
   render only pages approaching the viewport and free distant bitmaps. */
let activeReaderCleanup=null;
function pdf(){
 const b=bridge();
 const count=Math.max(0,Number(doc.pages)||0);
 const [bar,tools]=toolbar('Continuous PDF · swipe vertically');
 const body=E('div','fg-reader-scroll fg-pdf-scroll');
 body.setAttribute('role','document');
 body.setAttribute('aria-label',(doc.name||'PDF')+' · '+count+' pages');
 const stack=E('div','fg-pdf-stack');
 const refs=[],loaded=new Map(),waiting=new Set();
 let metrics=[],observer=null,disposed=false,scheduled=false,readingPage=0,zoomValue=1;
 try{metrics=JSON.parse(b?.getPdfPageMetrics?.()||'[]');}catch(_){}
 if(!Array.isArray(metrics))metrics=[];
 const progress=E('span','fg-reader-counter fg-pdf-progress',
   count?'Page 1 of '+count:'Empty PDF');
 progress.setAttribute('aria-live','off');
 const zoomLabel=E('span','fg-reader-counter','Fit width');
 const container=E('div','fg-pdf-container');
 stack.appendChild(container);
 body.appendChild(stack);
 function widthPx(){return Math.max(360,Math.min(1500,
     Math.round(Math.max(360,body.clientWidth-20)*(window.devicePixelRatio||1)*zoomValue)));}
 function put(index){
   if(disposed||loaded.has(index)||waiting.has(index)||index<0||index>=count)return;
   waiting.add(index);
   if(!scheduled){scheduled=true;requestAnimationFrame(drawNext);}
 }
 function drawNext(){
   scheduled=false;
   if(disposed)return;
   const iterator=waiting.values(),next=iterator.next();
   if(next.done)return;
   const index=next.value;waiting.delete(index);
   const cell=refs[index];
   if(!cell)return;
   // Never do expensive bridge PDF rendering for pages now far from view.
   const viewport=body.getBoundingClientRect(),bounds=cell.getBoundingClientRect();
   if(bounds.bottom<viewport.top-2*body.clientHeight ||
      bounds.top>viewport.bottom+2*body.clientHeight){
     if(waiting.size){scheduled=true;requestAnimationFrame(drawNext);}return;
   }
   try{
     const data=b?.getPdfPage?.(index,widthPx());
     if(!data)throw Error('The page could not be rendered.');
     const img=E('img','fg-pdf-img');
     img.alt='Page '+(index+1)+' of '+count;
     img.decoding='async';
     img.src='data:image/jpeg;base64,'+data;
     img.onerror=()=>{if(!disposed)cell.replaceChildren(
       E('div','fg-reader-empty','Page '+(index+1)+' could not be displayed.'));};
     cell.replaceChildren(img);
     loaded.set(index,{img,pixels:widthPx()});
   }catch(error){
     cell.replaceChildren(E('div','fg-reader-empty',
       'Cannot display page '+(index+1)+': '+String(error.message||error)));
   }
   trim();
   if(waiting.size){scheduled=true;requestAnimationFrame(drawNext);}
 }
 function trim(){
   const viewport=body.getBoundingClientRect();
   for(const [i,item] of loaded){
     const box=refs[i].getBoundingClientRect();
     if(box.bottom<viewport.top-2.5*body.clientHeight ||
        box.top>viewport.bottom+2.5*body.clientHeight){
       item.img.removeAttribute('src');
       loaded.delete(i);
       refs[i].replaceChildren(E('div','fg-pdf-skeleton','Page '+(i+1)));
     }
   }
 }
 function updateCurrent(){
   if(disposed)return;
   const center=body.getBoundingClientRect().top+Math.max(20,body.clientHeight*.3);
   let best=readingPage,dist=Infinity;
   for(let i=0;i<count;i++){
     const rect=refs[i].getBoundingClientRect();
     const d=rect.top>center?rect.top-center:rect.bottom<center?center-rect.bottom:0;
     if(d<dist){dist=d;best=i;if(d===0)break;}
   }
   readingPage=best;progress.textContent='Page '+(best+1)+' of '+count;
   trim();
   // Fallback if WebView lacks IntersectionObserver.
   if(!observer)for(let i=Math.max(0,best-1);i<=Math.min(count-1,best+2);i++)put(i);
 }
 function resizeZoom(delta,fit=false){
   zoomValue=fit?1:Math.max(.7,Math.min(2.5,Math.round((zoomValue+delta)*100)/100));
   stack.style.width=Math.round(zoomValue*100)+'%';
   zoomLabel.textContent=zoomValue===1?'Fit width':Math.round(zoomValue*100)+'%';
   for(const [i,item] of loaded){
     item.img.removeAttribute('src');
     loaded.delete(i);
     refs[i].replaceChildren(E('div','fg-pdf-skeleton','Page '+(i+1)));
   }
   updateCurrent();
   for(let i=Math.max(0,readingPage-1);i<=Math.min(count-1,readingPage+1);i++)put(i);
 }
 tools.append(progress,
   button('−',()=>resizeZoom(-.15)),
   zoomLabel,button('+',()=>resizeZoom(.15)),
   button('Fit width',()=>resizeZoom(0,true)));
 for(let i=0;i<count;i++){
   const metricsEntry=metrics[i];
   const w=Number(metricsEntry?.[0]),h=Number(metricsEntry?.[1]);
   const aspect=w>0&&h>0?w/h:.707;
   const cell=E('section','fg-pdf-section');
   cell.dataset.page=String(i+1);
   cell.style.aspectRatio=String(aspect);
   cell.setAttribute('aria-label','PDF page '+(i+1));
   cell.appendChild(E('div','fg-pdf-skeleton','Page '+(i+1)));
   container.appendChild(cell);refs.push(cell);
 }
 if(!count)container.appendChild(E('p','fg-reader-empty','The PDF contains no pages.'));
 stage(bar,body);
 if(window.IntersectionObserver){
   observer=new IntersectionObserver(items=>{
     if(disposed)return;
     for(const item of items)if(item.isIntersecting){
       const i=Number(item.target.dataset.page)-1;put(i);
     }
   },{root:body,rootMargin:'90% 0px',threshold:0});
   for(const cell of refs)observer.observe(cell);
 }
 let raf=0;
 const onScroll=()=>{
   if(raf)return;
   raf=requestAnimationFrame(()=>{raf=0;updateCurrent();});
 };
 body.addEventListener('scroll',onScroll,{passive:true});
 if(count){put(0);if(count>1)put(1);}
 activeReaderCleanup=()=>{
   disposed=true;observer?.disconnect();waiting.clear();
   if(raf)cancelAnimationFrame(raf);
   for(const item of loaded.values())item.img.removeAttribute('src');
   loaded.clear();
 };
}
function imageView(){
 const [bar,tools]=toolbar('Image preview · pinch/scroll to inspect');
 zoomer(tools,imageView);
 const body=E('div','fg-reader-scroll fg-image-surface'),img=E('img','fg-display-image');
 const formats={jpg:'jpeg',jpeg:'jpeg',png:'png',webp:'webp',gif:'gif',avif:'avif',bmp:'bmp',heic:'heic',heif:'heif'};
 try{
  if(!assetUrl)assetUrl=URL.createObjectURL(new Blob([localBytes()],{type:'image/'+(formats[doc.format]||'jpeg')}));
  img.src=assetUrl;img.alt=doc.name;img.style.width='min(100%, '+Math.round(850*zoom)+'px)';
  img.onerror=()=>{body.replaceChildren(E('p','fg-reader-empty','This image codec is unsupported by the installed Android WebView.'));};
  body.appendChild(img);
 }catch(e){body.appendChild(E('p','fg-reader-empty',String(e.message||e)));}
 stage(bar,body);
}
function addLines(host,raw,format){
 const code=/^(json|xml|yaml|yml|toml|log|sql|tsv|java|kt|kts|js|ts|css|scss|py|sh|ini|conf|svg|gradle|c|cpp|h|hpp|go|rs|php|gitignore)$/.test(format||'');
 if(code){host.appendChild(E('pre','fg-document-code',raw));return;}
 const markdown=['md','markdown'].includes(format);
 const lines=String(raw).replace(/\r\n?/g,'\n').split('\n');
 let buffer=[],codeBlock=null;
 function flush(){
   if(!buffer.length)return;
   const p=E('p','fg-document-p',buffer.join('\n'));
   host.appendChild(p);buffer=[];
 }
 for(const line of lines){
   const trimmed=line.trim();
   if(markdown&&/^ {0,3}~~~/.test(line)){
     flush();
     if(codeBlock){host.appendChild(E('pre','fg-document-code',codeBlock.join('\n')));codeBlock=null;}
     else codeBlock=[];
     continue;
   }
   if(markdown&&line.trimStart().startsWith(String.fromCharCode(96,96,96))){
     flush();
     if(codeBlock){host.appendChild(E('pre','fg-document-code',codeBlock.join('\n')));codeBlock=null;}
     else codeBlock=[];
     continue;
   }
   if(codeBlock){codeBlock.push(line);continue;}
   if(!trimmed){flush();continue;}
   const md=markdown?/^(#{1,6})\s+(.+)$/.exec(trimmed):null;
   if(md){flush();host.appendChild(E(md[1].length<=1?'h1':'h2',md[1].length<=1?'fg-document-h1':'fg-document-h2',md[2]));continue;}
   if(markdown&&/^[-*+]\s+/.test(trimmed)){flush();host.appendChild(E('p','fg-document-bullet','• '+trimmed.slice(2)));continue;}
   if(markdown&&/^\d+[.)]\s+/.test(trimmed)){flush();host.appendChild(E('p','fg-document-bullet',trimmed));continue;}
   if(markdown&&/^>\s*/.test(trimmed)){flush();host.appendChild(E('blockquote','fg-docx-quote',trimmed.replace(/^>\s*/,'')));continue;}
   // Plain-text line breaks remain in the same logical paragraph; separate
   // only at blank lines, not at every wrapped or hard-broken source line.
   buffer.push(line);
 }
 flush();
 if(codeBlock)host.appendChild(E('pre','fg-document-code',codeBlock.join('\n')));
}
/* TXT, Markdown, EPUB, ODT/ODS text and code all scroll in ONE document.
   Large sources append source-preserving blocks rather than artificial pages. */
function textView(){
 const text=String(bridge()?.getText?.()||'');
 const [bar,tools]=toolbar('Continuous document · vertical scrolling');
 const body=E('div','fg-reader-scroll fg-text-scroll');
 const sheet=paper('fg-document-sheet fg-continuous-text');
 sheet.setAttribute('role','document');
 sheet.setAttribute('aria-label',doc.name||'Document');
 let size=1;
 const setSize=delta=>{
   size=Math.max(.75,Math.min(2,Math.round((size+delta)*100)/100));
   sheet.style.setProperty('--fg-size',String(size));
 };
 tools.append(button('A−',()=>setSize(-.1)),button('A+',()=>setSize(.1)));
 if(text.length<=2_000_000) {
   addLines(sheet,text,doc.format);
 } else {
   // Very large files: preserve every character, including whitespace and
   // original line breaks, while avoiding a monolithic UI-thread DOM build.
   let offset=0,loading=false;
   function append(){
     if(loading||offset>=text.length)return;
     loading=true;
     const frag=document.createDocumentFragment();
     for(let n=0;n<3&&offset<text.length;n++){
       let end=Math.min(text.length,offset+64_000);
       if(end<text.length){
         const cut=text.lastIndexOf('\n',end);
         if(cut>offset+32_000)end=cut+1;
       }
       const part=E('pre','fg-document-code fg-raw-text',text.slice(offset,end));
       frag.appendChild(part);offset=end;
     }
     sheet.appendChild(frag);loading=false;
   }
   append();
   let ticking=false;
   body.addEventListener('scroll',()=>{
     if(ticking)return;ticking=true;
     requestAnimationFrame(()=>{
       ticking=false;
       if(body.scrollTop+body.clientHeight>body.scrollHeight-1000)append();
     });
   },{passive:true});
 }
 body.appendChild(sheet);stage(bar,body);
}
/* DOCX reads body blocks in order, keeps tables together, and scrolls without
   manufacturing pages every 150 paragraphs. Windows are lazily appended. */
function docx(){
 const b=bridge();
 let count=0;
 try{count=Number(b?.getDocxRichBlockCount?.()||0);}catch(_){}
 const [bar,tools]=toolbar('Faithful document flow · original tables, headings and lists');
 const body=E('div','fg-reader-scroll fg-docx-scroll');
 const sheet=paper('fg-document-sheet fg-docx-sheet');
 sheet.setAttribute('role','document');
 sheet.setAttribute('aria-label',doc.name||'Word document');
 const progress=E('span','fg-reader-counter','');
 const message=E('div','fg-docx-message','');
 const foot=E('div','fg-docx-foot');
 foot.append(progress);
 body.append(sheet,foot);
 let next=0,start=0,loading=false,lastSearch=0;
 const chunk=24;
 function updateProgress(){
   const done=Math.min(count,next);
   progress.textContent=count?done+' / '+count+' blocks':'Empty document';
 }
 function appendNext(){
   if(loading||next>=count)return;
   loading=true;
   try{
     const rows=JSON.parse(b?.getDocxRichWindow?.(next,chunk)||'[]');
     if(!Array.isArray(rows)||!rows.length)throw Error('Reader returned no document blocks.');
     const f=document.createDocumentFragment();
     for(const item of rows){
       if(!Array.isArray(item)||item.length!==2)continue;
       const n=E('div','fg-docx-flow-block');
       n.dataset.index=String(item[0]);
       // Only our native parser produces HTML, with escaped user text.
       n.innerHTML=item[1];
       f.appendChild(n);
     }
     sheet.appendChild(f);
     next=Math.min(count,next+rows.length);
     message.textContent=start?'Showing from document block '+(start+1):'';
   }catch(e){
     message.textContent='Cannot render this section: '+String(e.message||e);
   }finally{loading=false;updateProgress();}
 }
 function showFrom(index){
   start=Math.max(0,Math.min(count-1,index));next=start;
   sheet.replaceChildren();body.scrollTop=0;
   appendNext();
 }
 const begin=button('↑ Start',()=>{lastSearch=0;showFrom(0);});
 begin.title='Return to the beginning of the document';
 tools.appendChild(begin);
 tools.appendChild(button('A−',()=>{
   zoom=Math.max(.78,Math.round((zoom-.1)*100)/100);
   sheet.style.setProperty('--fg-size',String(zoom));
 }));
 tools.appendChild(button('A+',()=>{
   zoom=Math.min(1.8,Math.round((zoom+.1)*100)/100);
   sheet.style.setProperty('--fg-size',String(zoom));
 }));
 const searchInput=E('input','fg-reader-find');
 searchInput.type='search';searchInput.placeholder='Find in document';
 searchInput.setAttribute('aria-label','Find in entire Word document');
 const findAction=()=>{
   const term=searchInput.value.trim();
   if(!term)return;
   const target=Number(b?.findDocxBlock?.(term,lastSearch)??-1);
   if(target<0){message.textContent='No matching text found';return;}
   lastSearch=target+1;
   let node=sheet.querySelector('[data-index="'+target+'"]');
   if(!node){showFrom(target);node=sheet.querySelector('[data-index="'+target+'"]');}
   if(node)node.scrollIntoView({block:'start',behavior:'auto'});
   message.textContent='Match at block '+(target+1)+' of '+count;
 };
 searchInput.addEventListener('keydown',event=>{
   if(event.key==='Enter'){event.preventDefault();findAction();}
 });
 tools.append(searchInput,button('Find',findAction));
 tools.appendChild(button('Edit text',()=>{
   editing=true;original(doc);
   $('editor').classList.remove('fg-reader-host');
   $('fgBackToReader').classList.remove('hidden');
 }));
 foot.prepend(message);
 updateProgress();
 if(count)appendNext();
 else sheet.appendChild(E('p','fg-reader-empty','No Word body content was found.'));
 let scheduled=false;
 body.addEventListener('scroll',()=>{
   if(scheduled)return;
   scheduled=true;
   requestAnimationFrame(()=>{
     scheduled=false;
     if(body.scrollTop+body.clientHeight>=body.scrollHeight-850){
       appendNext();
       requestAnimationFrame(fillViewport);
     }
   });
 },{passive:true});
 stage(bar,body);
 // DOCX editing exists, but accidental Save in reader mode is not offered.
 if($('saveBtn'))$('saveBtn').disabled=true;
 if($('copyBtn'))$('copyBtn').disabled=true;
 function fillViewport(){
   if(next>=count||loading)return;
   if(body.scrollHeight<=body.clientHeight+400){
     const before=next;
     appendNext();
     if(next>before)requestAnimationFrame(fillViewport);
   }
 }
 requestAnimationFrame(fillViewport);
}
/* Comics and archives are content streams, not one-entry slide decks. */
function archive(){
 let entries=[];
 try{entries=JSON.parse(bridge()?.getArchiveEntries?.()||'[]');}catch(_){}
 if(doc.format==='cbz')entries=entries.filter(e=>/\.(png|jpe?g|gif|webp|bmp|avif)$/i.test(e.name));
 const [bar,tools]=toolbar(doc.format==='cbz'?
    'Continuous comic · scroll down through every image':
    'Archive contents · scroll and expand entries');
 const body=E('div','fg-reader-scroll fg-archive-scroll');
 body.setAttribute('role','document');
 tools.appendChild(E('span','fg-reader-counter',entries.length+' entries'));
 if(!entries.length){
   body.appendChild(E('p','fg-reader-empty','Archive has no previewable entries.'));
   stage(bar,body);return;
 }
 function content(entry,dest){
   dest.replaceChildren();
   if(!entry.preview){
     dest.appendChild(E('p','fg-reader-empty','This entry cannot be previewed safely.'));
     return;
   }
   try{
     const data=bridge()?.getArchiveEntryBase64?.(entry.name)||'';
     if(!data)throw Error('Entry exceeds preview limit or is not readable.');
     if(/\.(png|jpe?g|gif|webp|bmp|avif)$/i.test(entry.name)){
       const ext=entry.name.split('.').pop().toLowerCase();
       const im=E('img','fg-archive-img');im.alt=entry.name;
       im.loading='lazy';
       im.src='data:image/'+(ext==='jpg'?'jpeg':ext)+';base64,'+data;
       dest.appendChild(im);
     }else{
       dest.appendChild(E('pre','fg-document-code',
         new TextDecoder().decode(decode(data))));
     }
   }catch(error){
     dest.appendChild(E('p','fg-reader-empty',
       'Cannot preview '+entry.name+': '+String(error.message||error)));
   }
 }
 if(doc.format==='cbz'){
   const stack=E('div','fg-pdf-stack fg-comic-stack'),cells=[],loaded=new Map();
   let disposed=false,observer=null,scheduled=false;
   const queue=new Set();
   const root=E('div','fg-pdf-container');
   function enqueue(i){
     if(disposed||loaded.has(i)||queue.has(i))return;
     queue.add(i);
     if(!scheduled){scheduled=true;requestAnimationFrame(draw);}
   }
   function draw(){
     scheduled=false;
     if(disposed||!queue.size)return;
     const i=queue.values().next().value;queue.delete(i);
     const frame=cells[i],rect=frame.getBoundingClientRect(),view=body.getBoundingClientRect();
     if(rect.bottom>=view.top-2*body.clientHeight&&rect.top<=view.bottom+2*body.clientHeight){
       const target=E('div','fg-comic-page');
       content(entries[i],target);
       frame.replaceChildren(target);loaded.set(i,target);
     }
     trim();
     if(queue.size){scheduled=true;requestAnimationFrame(draw);}
   }
   function trim(){
     const view=body.getBoundingClientRect();
     for(const [i,target] of loaded){
       const rect=cells[i].getBoundingClientRect();
       if(rect.bottom<view.top-3*body.clientHeight||
          rect.top>view.bottom+3*body.clientHeight){
         target.querySelectorAll('img').forEach(img=>img.removeAttribute('src'));
         loaded.delete(i);
         cells[i].replaceChildren(E('div','fg-pdf-skeleton','Image '+(i+1)));
       }
     }
   }
   entries.forEach((entry,i)=>{
     const frame=E('section','fg-comic-section');
     frame.dataset.page=String(i+1);
     frame.setAttribute('aria-label','Comic image '+(i+1)+' '+entry.name);
     frame.appendChild(E('div','fg-pdf-skeleton','Image '+(i+1)));
     root.appendChild(frame);cells.push(frame);
   });
   stack.appendChild(root);body.appendChild(stack);stage(bar,body);
   if(window.IntersectionObserver){
     observer=new IntersectionObserver(items=>{
       for(const item of items)if(item.isIntersecting)
         enqueue(Number(item.target.dataset.page)-1);
     },{root:body,rootMargin:'90% 0px'});
     cells.forEach(c=>observer.observe(c));
   }
   let raf=0;
   body.addEventListener('scroll',()=>{
     if(raf)return;
     raf=requestAnimationFrame(()=>{
       raf=0;trim();
       if(!observer){
         const top=body.getBoundingClientRect().top;
         cells.forEach((c,i)=>{
           const rect=c.getBoundingClientRect();
           if(rect.bottom>=top-body.clientHeight&&rect.top<=top+2*body.clientHeight)enqueue(i);
         });
       }
     });
   },{passive:true});
   enqueue(0);if(entries.length>1)enqueue(1);
   activeReaderCleanup=()=>{
     disposed=true;observer?.disconnect();queue.clear();
     if(raf)cancelAnimationFrame(raf);
     for(const cell of loaded.values())
       cell.querySelectorAll('img').forEach(img=>img.removeAttribute('src'));
     loaded.clear();
   };
 }else{
   const list=E('div','fg-archive-list');
   entries.forEach((entry,i)=>{
     const row=E('details','fg-archive-entry');
     const summary=E('summary','fg-archive-summary',
       (entry.name||'Entry '+(i+1))+
       (entry.size>=0?' · '+(Math.round(entry.size/1024))+' KiB':''));
     const dest=E('div','fg-archive-preview');
     row.append(summary,dest);
     row.addEventListener('toggle',()=>{
       if(row.open)content(entry,dest);
       else {dest.querySelectorAll('img').forEach(im=>im.removeAttribute('src'));dest.replaceChildren();}
     });
     list.appendChild(row);
   });
   body.appendChild(list);stage(bar,body);
 }
}
function binary(){
 const [bar]=toolbar('Unknown or legacy binary document · inspection only');
 const body=E('div','fg-reader-scroll'),p=paper('fg-document-sheet');
 p.appendChild(E('h2','fg-document-h2','A dedicated renderer is required'));
 p.appendChild(E('p','fg-document-p','The original bytes are untouched. This is not a faithful document preview. Legacy DOC, XLS and PPT need specific decoders.'));
 try{
  const size=Math.min(1024,Number(bridge()?.getRawDocumentSize?.()||0)),data=decode(bridge()?.getRawDocumentChunk?.(0,size)||''),rows=[];
  for(let i=0;i<data.length;i+=16){
   const a=data.slice(i,i+16);
   rows.push(i.toString(16).padStart(6,'0')+'  '+[...a].map(v=>v.toString(16).padStart(2,'0')).join(' ').padEnd(47,' ')+'  '+[...a].map(v=>v>=32&&v<127?String.fromCharCode(v):'.').join(''));
  }
  p.appendChild(E('pre','fg-document-code',rows.join('\n')));
 }catch(e){p.appendChild(E('p','fg-reader-empty',String(e)));}
 body.appendChild(p);stage(bar,body);
}
function backButton(){
 let b=$('fgBackToReader');if(!b){b=button('Read',()=>{editing=false;page=0;docx();b.classList.add('hidden');});b.id='fgBackToReader';b.classList.add('hidden');document.querySelector('.actions')?.prepend(b);}
 return b;
}
window.loadDocument=function(d){
 if(assetUrl){URL.revokeObjectURL(assetUrl);assetUrl=null;}
 if(activeReaderCleanup){activeReaderCleanup();activeReaderCleanup=null;}
 doc=d;page=0;zoom=1;archiveIndex=0;editing=false;
 $('editor')?.classList.remove('fg-reader-host');backButton().classList.add('hidden');
 original(d);
 if(d.type==='pdf')pdf();
 else if(d.type==='image')imageView();
 else if(d.type==='reader')textView();
 else if(d.type==='archive')archive();
 else if(d.type==='binary')binary();
 else if(d.type==='docx')docx();
 if(ro(d)){$('saveBtn').disabled=true;$('copyBtn').disabled=true;}
};
})();