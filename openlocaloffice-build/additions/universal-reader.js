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
function controls(bar,count,render){
 const prev=button('‹',()=>{page=Math.max(0,page-1);render();});prev.disabled=page<=0;
 const next=button('›',()=>{page=Math.min(count-1,page+1);render();});next.disabled=page>=count-1;
 bar.append(prev,E('span','fg-reader-counter',(page+1)+' / '+count),next);
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
function pdf(){
 const [bar,tools]=toolbar('Native PDF page · offline');
 controls(tools,doc.pages,pdf);zoomer(tools,pdf);
 const body=E('div','fg-reader-scroll'),p=paper('fg-pdf-sheet'),image=E('img','fg-pdf-img');
 image.alt='PDF page '+(page+1);
 const data=bridge()?.getPdfPage?.(page,Math.round(960*zoom));
 if(data){image.src='data:image/jpeg;base64,'+data;p.appendChild(image);}
 else p.appendChild(E('p','fg-reader-empty','Cannot display page. The PDF may be password-protected or unsupported.'));
 body.appendChild(p);stage(bar,body);
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
function addLines(p,text,format){
 const code=/^(json|xml|yaml|yml|toml|log|sql|tsv|java|kt|kts|js|ts|css|scss|py|sh|ini|conf|svg|gradle|c|cpp|h|hpp|go|rs|php|gitignore)$/.test(format||'');
 if(code){p.appendChild(E('pre','fg-document-code',text));return;}
 let first=true;
 for(const line of String(text).replace(/\r\n/g,'\n').split('\n')){
   let value=line.trim();
   if(!value){p.appendChild(E('div','fg-paragraph-break'));continue;}
   const md=/^(#{1,6})\s+(.+)/.exec(value);
   const heading=md||/^(?:SLIDE|CHAPTER)\s+\d+/i.test(value)||/^\d+(?:\.\d+)*\s+\S/.test(value)&&value.length<100;
   if(first&&format==='docx'&&value.length<120){p.appendChild(E('h1','fg-document-h1',value));}
   else if(heading){p.appendChild(E('h2','fg-document-h2',md?md[2]:value));}
   else if(format==='md'&&/^[-*+]\s+/.test(value)){p.appendChild(E('p','fg-document-bullet','• '+value.slice(2)));}
   else p.appendChild(E('p','fg-document-p',line));
   first=false;
 }
}
function textView(){
 const text=String(bridge()?.getText?.()||''),chunk=18000,pages=Math.max(1,Math.ceil(text.length/chunk));
 page=Math.min(page,pages-1);
 const desc=/^(pptx|odp)$/.test(doc.format)?'Slide text extraction · graphics/layout may differ':'Document reading view · offline';
 const [bar,tools]=toolbar(desc);
 controls(tools,pages,textView);zoomer(tools,textView);
 const body=E('div','fg-reader-scroll'),p=paper('fg-document-sheet');
 addLines(p,text.slice(page*chunk,(page+1)*chunk),doc.format);
 body.appendChild(p);stage(bar,body);
}
function docxEntries(){
 const count=doc.paragraphCount||0;
 try{return JSON.parse(bridge()?.getParagraphWindow?.(page*150,Math.max(0,Math.min(150,count-page*150)))||'[]');}
 catch(_){return [];}
}
function docx(){
 const pages=Math.max(1,Math.ceil((doc.paragraphCount||0)/150));page=Math.min(page,pages-1);
 const [bar,tools]=toolbar('Continuous reading layout · text-edit option');
 controls(tools,pages,docx);zoomer(tools,docx);
 tools.appendChild(button('Edit text',()=>{
   editing=true;original(doc);$('editor').classList.remove('fg-reader-host');
   $('fgBackToReader').classList.remove('hidden');
 }));
 const body=E('div','fg-reader-scroll'),p=paper('fg-document-sheet');
 for(const [i,txt] of docxEntries())addLines(p,txt,'docx');
 body.appendChild(p);stage(bar,body,true);
}
function archive(){
 let entries=[];try{entries=JSON.parse(bridge()?.getArchiveEntries?.()||'[]');}catch(_){}
 if(doc.format==='cbz')entries=entries.filter(e=>/\.(png|jpe?g|gif|webp|bmp|avif)$/i.test(e.name));
 archiveIndex=Math.min(archiveIndex,Math.max(0,entries.length-1));
 const [bar,tools]=toolbar(doc.format==='cbz'?'Comic / sequential images':'Archive explorer');
 if(!entries.length){const body=E('div','fg-reader-scroll');body.appendChild(E('p','fg-reader-empty','Archive has no previewable entries.'));stage(bar,body);return;}
 const prev=button('‹',()=>{archiveIndex=Math.max(0,archiveIndex-1);archive();});prev.disabled=archiveIndex===0;
 const next=button('›',()=>{archiveIndex=Math.min(entries.length-1,archiveIndex+1);archive();});next.disabled=archiveIndex===entries.length-1;
 tools.append(prev,E('span','fg-reader-counter',(archiveIndex+1)+' / '+entries.length),next);
 if(doc.format!=='cbz'){
   const chooser=E('select','fg-entry-select');chooser.setAttribute('aria-label','Select archive entry');
   entries.forEach((entry,index)=>{const option=document.createElement('option');option.value=index;option.textContent=entry.name;chooser.appendChild(option);});
   chooser.value=archiveIndex;chooser.onchange=()=>{archiveIndex=+chooser.value;archive();};tools.appendChild(chooser);
 }
 const body=E('div','fg-reader-scroll'),p=paper('fg-archive-sheet'),entry=entries[archiveIndex];
 p.appendChild(E('h2','fg-document-h2',entry.name));
 if(entry.preview){
   let data='';try{data=bridge()?.getArchiveEntryBase64?.(entry.name)||'';}catch(_){}
   if(data&&/\.(png|jpe?g|gif|webp|bmp|avif)$/i.test(entry.name)){
     const im=E('img','fg-archive-img');im.alt=entry.name;
     const ext=entry.name.substring(entry.name.lastIndexOf('.')+1).toLowerCase();
     im.src='data:image/'+(ext==='jpg'?'jpeg':ext)+';base64,'+data;p.appendChild(im);
   }else if(data){try{p.appendChild(E('pre','fg-document-code',new TextDecoder().decode(decode(data))));}
     catch(_){p.appendChild(E('p','fg-reader-empty','Cannot decode this entry.'));}}
   else p.appendChild(E('p','fg-reader-empty','Entry is too large or unsupported for inline preview.'));
 }else p.appendChild(E('p','fg-reader-empty','This item can be listed, but not previewed safely.'));
 body.appendChild(p);stage(bar,body);
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