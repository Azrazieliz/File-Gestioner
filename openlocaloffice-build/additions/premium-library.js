/* File Gestioner Library — visual-first offline bookshelf. */
(()=>{'use strict';
const bridge=()=>window.AndroidBridge;
const E=(tag,cls,content)=>{const n=document.createElement(tag);if(cls)n.className=cls;
  if(content!==undefined)n.textContent=content;return n;};
const b=(label,cls,fn)=>{const n=E('button',cls,label);n.type='button';
  n.addEventListener('click',fn);return n;};
const root=E('section','fg-library-root fg-lib-hidden');
root.id='fg-library';
const header=E('header','fg-lib-header'),body=E('main','fg-lib-body');
const brand=E('div','fg-lib-brand');
const monogram=E('div','fg-lib-monogram','FG');
const titleGroup=E('div','fg-lib-title-group');
titleGroup.append(E('strong','fg-lib-brand-title','File Gestioner'),
                  E('span','fg-lib-brand-subtitle','YOUR PRIVATE LIBRARY'));
brand.append(monogram,titleGroup);
const actions=E('div','fg-lib-actions');
const openBtn=b('Open file','fg-lib-primary',()=>bridge()?.pickFile?.());
const collectionBtn=b('Collection','fg-lib-secondary',()=>bridge()?.pickLibraryFolder?.());
actions.append(openBtn,collectionBtn);header.append(brand,actions);
const welcome=E('section','fg-lib-welcome');
const kicker=E('p','fg-lib-kicker','OFFLINE READING');
const hero=E('h1','fg-lib-hero','Your library, beautifully organized.');
const subtitle=E('p','fg-lib-subtitle',
  'Illustrated books, webtoons, documents and 3D assets. Your files stay on your device.');
welcome.append(kicker,hero,subtitle);
const toolbar=E('section','fg-lib-toolbar');
const back=b('‹','fg-lib-nav-back',()=>navigateBack());
back.setAttribute('aria-label','Return to parent folder');
const heading=E('div','fg-lib-collection-title','Library');
const count=E('span','fg-lib-count','');
const headBox=E('div','fg-lib-head-info');headBox.append(heading,count);
const search=E('input','fg-lib-search');
search.type='search';search.placeholder='Search your books';search.autocomplete='off';
search.setAttribute('aria-label','Search your library');
const layout=b('▦','fg-lib-icon',()=>{list=!list;layout.textContent=list?'☷':'▦';render();});
layout.setAttribute('aria-label','Toggle grid and list');
toolbar.append(back,headBox,search,layout);
const filters=E('div','fg-lib-filters');
const deck=E('div','fg-lib-grid');
const empty=E('div','fg-lib-empty');
const loading=E('div','fg-lib-loading','Loading your collection…');
const footer=E('div','fg-lib-footer',
  'PRIVATE · OFFLINE · ORIGINAL FILES UNCHANGED');
body.append(welcome,toolbar,filters,loading,deck,empty,footer);
root.append(header,body);
document.body.insertBefore(root,document.getElementById('busy')||null);
const categories=[
 ['all','All'],['comic','Comics'],['book','Books'],
 ['document','Documents'],['model','3D assets']
];
let entries=[],list=false,currentFolder='',stack=[],filter='all',phrase='',loaded=false,visible=false,activeUri='';
function classify(entry){
 if(entry.folder)return 'folder';
 const x=entry.name.toLowerCase();
 if(/\.(cbz|zip|cbr)$/.test(x))return 'comic';
 if(/\.(epub)$/.test(x))return 'book';
 if(/\.(glb|gltf|fbx|obj|vrm|blend|pmx|pmd)$/.test(x))return 'model';
 return 'document';
}
function formatSize(n){
 if(n==null||n<0)return '';
 if(n>=1024**3)return (n/(1024**3)).toFixed(n>=10*1024**3?0:1)+' GB';
 if(n>=1024**2)return (n/(1024**2)).toFixed(n>=10*1024**2?0:1)+' MB';
 return Math.round(n/1024)+' KB';
}
function label(e){
 const c=classify(e);
 return {comic:'WEBTOON',book:'EBOOK',document:'DOCUMENT',model:'3D ASSET',
   folder:'COLLECTION'}[c];
}
function icon(c){return {comic:'▧',book:'▤',document:'▤',model:'◇',folder:'▣'}[c];}
function tint(name){
 let h=42;for(const ch of name)h=(h*33+ch.charCodeAt(0))>>>0;
 return (h%260)+30;
}
function openBook(item){
 if(item.folder){
   bridge()?.openImageFolder?.(item.uri);
   return;
 }
 activeUri=item.uri;
 root.classList.add('fg-lib-hidden');
 visible=false;
 document.getElementById('home')?.classList.add('hidden');
 document.getElementById('work')?.classList.remove('hidden');
 bridge()?.openLibraryFile?.(item.uri);
}
// Never start five remote archive transfers at once. Image requests run only
// after the corresponding tile intersects the viewport; each finishes before
// the next starts. Opening a book cancels the pending (not-yet-started) work.
let coverQueue=Promise.resolve();
const queuedCovers=new WeakSet();
const coverObserver=window.IntersectionObserver?new IntersectionObserver(changes=>{
 for(const item of changes){
   if(!item.isIntersecting)continue;
   coverObserver.unobserve(item.target);
   item.target._fgStartCover?.();
 }
},{root:body,rootMargin:'0px'}):null;
function loadRemoteCover(image,url,cover){
 if(queuedCovers.has(image))return;
 queuedCovers.add(image);
 coverQueue=coverQueue.catch(()=>{}).then(()=>new Promise(resolve=>{
   if(!image.isConnected||!visible){resolve();return;}
   const indicator=E('span','fg-lib-cover-loading','Loading cover…');
   cover.appendChild(indicator);
   const finish=()=>{indicator.remove();resolve();};
   image.addEventListener('load',finish,{once:true});
   image.addEventListener('error',finish,{once:true});
   image.src=url;
 }));
}
function card(item,i){
 const c=classify(item),tile=E('article','fg-lib-tile fg-lib-'+c);
 tile.setAttribute('role','button');tile.setAttribute('tabindex','0');
 const cover=E('div','fg-lib-cover');
 cover.style.setProperty('--fg-hue',String(tint(item.name)));
 const fallback=E('div','fg-lib-fallback');
 fallback.append(E('span','fg-lib-fallback-glyph',icon(c)),
                 E('strong','fg-lib-fallback-title',item.title));
 cover.appendChild(fallback);
 if(item.cover){
   const image=E('img','fg-lib-cover-image');
   image.loading='lazy';image.decoding='async';
   image.alt='Cover · '+item.title;
   image.addEventListener('load',()=>{cover.classList.add('fg-lib-has-image');});
   image.addEventListener('error',()=>{if(!item.remoteCover)image.remove();});
   cover.appendChild(image);
   if(item.remoteCover){
     // Automatic, sequential, visibility-prioritized cloud thumbnail loading.
     cover._fgStartCover=()=>loadRemoteCover(image,item.cover,cover);
     if(coverObserver)coverObserver.observe(cover);
     else cover._fgStartCover();
   }else image.src=item.cover;
 }
 const badge=E('span','fg-lib-type',label(item));
 cover.appendChild(badge);
 const meta=E('div','fg-lib-tile-meta');
 meta.append(E('strong','fg-lib-item-title',item.title),
             E('span','fg-lib-item-detail',formatSize(item.size)||
               (item.folder?'Open collection':'')));
 tile.append(cover,meta);
 tile.addEventListener('click',()=>openBook(item));
 tile.addEventListener('keydown',e=>{
   if(e.key==='Enter'||e.key===' '){e.preventDefault();openBook(item);}
 });
 return tile;
}
function render(){
 deck.className='fg-lib-grid'+(list?' fg-lib-list':'');
 deck.replaceChildren();empty.replaceChildren();
 const needle=phrase.trim().toLocaleLowerCase();
 const shown=entries.filter(e=>{
   const c=classify(e);
   return (filter==='all'||c===filter||c==='folder')&&
     (!needle||e.title.toLocaleLowerCase().includes(needle));
 }).sort((a,b)=>{
   if(a.folder!==b.folder)return a.folder?-1:1;
   return a.title.localeCompare(b.title,undefined,{numeric:true,sensitivity:'base'});
 });
 const fragment=document.createDocumentFragment();
 shown.forEach((entry,i)=>fragment.appendChild(card(entry,i)));
 deck.appendChild(fragment);
 count.textContent=entries.length+' items';
 if(!shown.length){
   empty.append(E('div','fg-lib-empty-icon',entries.length?'⌕':'▤'),
     E('strong','',entries.length?'No matching titles':'Nothing in this collection yet'),
     E('p','',entries.length?'Try another title or category.':
       'Choose a folder containing books, documents or models.'));
 }
}
function createFilters(){
 filters.replaceChildren();
 for(const [key,name] of categories){
   const control=b(name,'fg-lib-filter'+(filter===key?' fg-lib-selected':''),
     ()=>{filter=key;createFilters();render();});
   filters.append(control);
 }
}
function request(){
 if(!bridge()?.getLibraryRoot?.()){showEmpty();return;}
 loading.classList.remove('fg-lib-hidden');deck.classList.add('fg-lib-hidden');
 empty.classList.add('fg-lib-hidden');
 bridge()?.listLibrary?.(currentFolder);
}
function showEmpty(){
 loaded=false;entries=[];deck.replaceChildren();loading.classList.add('fg-lib-hidden');
 welcome.classList.remove('fg-lib-hidden');toolbar.classList.add('fg-lib-hidden');
 filters.classList.add('fg-lib-hidden');empty.classList.remove('fg-lib-hidden');
 empty.replaceChildren();
 const add=b('Add a collection','fg-lib-large-action',
   ()=>bridge()?.pickLibraryFolder?.());
 empty.append(E('div','fg-lib-empty-icon','▧'),
   E('strong','','Build your personal library'),
   E('p','','Select a folder to see the actual covers of your books and image archives.'),
   add);
}
function enterFolder(id){
 const entry=entries.find(x=>x.folder&&x.id===id);
 if(!entry)return;
 stack.push(currentFolder);currentFolder=id;request();
}
function openSibling(direction){
 const sorted=entries.filter(e=>!e.folder&&
   /\.(epub|pdf|zip|cbz|cbr|jpe?g|png|webp|gif|avif)$/i.test(e.name||''))
   .sort((a,b)=>a.name.localeCompare(b.name,undefined,{numeric:true,sensitivity:'base'}));
 const i=sorted.findIndex(e=>e.uri===activeUri);
 if(i<0||!sorted.length)return false;
 const next=sorted[i+Math.sign(direction)];
 if(!next)return false;
 openBook(next);
 return true;
}
function navigateBack(){
 if(stack.length){currentFolder=stack.pop();request();return;}
 show();
}
function show(){
 window.FileGestionerReading?.close?.();
 document.body.classList.remove('fg-folder-reading');
 visible=true;root.classList.remove('fg-lib-hidden');
 document.getElementById('home')?.classList.add('hidden');
 document.getElementById('work')?.classList.add('hidden');
 document.body.classList.remove('fg-book-mode','fg-pdf-reading','fg-unified-reading');
 if(!bridge()?.getLibraryRoot?.()){showEmpty();return;}
 welcome.classList.add('fg-lib-hidden');toolbar.classList.remove('fg-lib-hidden');
 filters.classList.remove('fg-lib-hidden');
 createFilters();
 request();
}
function receive(payload){
 loaded=true;
 entries=Array.isArray(payload.items)?payload.items:[];
 currentFolder=payload.folder||currentFolder;
 loading.classList.add('fg-lib-hidden');deck.classList.remove('fg-lib-hidden');
 empty.classList.remove('fg-lib-hidden');
 heading.textContent=stack.length?'Collection':'Your library';
 welcome.classList.add('fg-lib-hidden');toolbar.classList.remove('fg-lib-hidden');
 filters.classList.remove('fg-lib-hidden');render();
}
function error(message){
 loading.classList.add('fg-lib-hidden');deck.classList.add('fg-lib-hidden');
 empty.classList.remove('fg-lib-hidden');
 empty.replaceChildren(E('strong','','This folder could not be read'),
                      E('p','',message||'Check cloud availability and file permissions'),
                      b('Try again','fg-lib-large-action',request));
}
search.addEventListener('input',()=>{phrase=search.value;render();});
const homeNav=b('Library','fg-lib-top-link',show);
homeNav.title='Open your library';
document.querySelector('.bar .actions')?.prepend(homeNav);
// Document opens from the Files picker, Round Sync and direct share intents
// must enter the same reader state as a library-card click.
const upstreamLoad=window.loadDocument;
window.loadDocument=function(payload){
 visible=false;
 root.classList.add('fg-lib-hidden');
 document.getElementById('home')?.classList.add('hidden');
 document.getElementById('work')?.classList.remove('hidden');
 return upstreamLoad(payload);
};
function handleAndroidBack(){
 if(window.FileGestionerReading?.handleBack?.())return true;
 // Reading settings are a modal surface, not an exit command.
 const drawer=document.querySelector('.fg-book-drawer:not(.fg-book-hidden)');
 if(drawer){drawer.classList.add('fg-book-hidden');return true;}
 if(visible){
   // Also tolerate older reader states in which the library flag remained
   // true after a document was opened from an external Android provider.
   if(!document.getElementById('work')?.classList.contains('hidden')){
     show();bridge()?.readerDiagnostic?.('BACK_TO_LIBRARY');return true;
   }
   if(stack.length){navigateBack();return true;}
   // Root collection is the app's top-level destination.
   return false;
 }
 // Return to the actual library, regardless of whether the source was
 // opened through Round Sync, Files, or a collection tile.
 show();
 bridge()?.readerDiagnostic?.('BACK_TO_LIBRARY');
 return true;
}
window.FileGestionerLibrary={
 show,receive,error,handleBack:handleAndroidBack,enterFolder,openSibling,
 isVisible:()=>visible,
 openCollection:()=>{
   currentFolder='';stack=[];show();
 },missingCollection:showEmpty
};
const initializeLibrary=()=>{
 // Handle both early page loads and scripts loaded after DOMContentLoaded.
 if(window.__fgLibraryInitialized)return;
 window.__fgLibraryInitialized=true;
 show();
 bridge()?.readerDiagnostic?.('LIBRARY_READY');
};
if(document.readyState==='loading')
 document.addEventListener('DOMContentLoaded',initializeLibrary,{once:true});
else initializeLibrary();
})();
