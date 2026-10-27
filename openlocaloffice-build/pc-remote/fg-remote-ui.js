/* File Gestioner native PC viewer. Independent Koikatsu and Blender sessions.
   This displays frames rendered by PC-native applications, NEVER a fake GLB.
   The PC server is authenticated and reachable through the USB ADB loopback.
*/
(()=>{
'use strict';
const URL_ROOT='http://127.0.0.1:39273';
const bridge=()=>window.AndroidBridge||null;
let overlay=null,status=null,viewport=null,frame=null,active=null,kind='cube',busy=false,scheduled=false;
let yaw=.4,pitch=.2,distance=2.5,contacts=new Map(),lastSpan=0,serial=0,dead=false;
const el=(tag,cls,text)=>{
  const x=document.createElement(tag);
  if(cls)x.className=cls;
  if(text!==undefined)x.textContent=text;
  return x;
};
const setStatus=t=>{if(status)status.textContent=t;};
const token=()=>String(bridge()?.getRemoteToken?.()||'').trim();
async function api(path,opts={}){
  const auth=token();if(!auth)throw Error('Pair this phone with the PC first.');
  const resp=await fetch(URL_ROOT+path,{...opts,headers:{...(opts.headers||{}),'X-FG-Token':auth},cache:'no-store'});
  if(!resp.ok){
    let details='';try{details=(await resp.json()).error||''}catch(_){}
    throw Error(details||'PC bridge HTTP '+resp.status);
  }
  return resp;
}
async function render(){
  if(!active||dead||busy)return;
  busy=true;const at=++serial;
  try{
    setStatus(kind==='cube'||kind==='blend'?'Blender rendering in background…':'Koikatsu rendering in background…');
    const url='/api/frame?session='+encodeURIComponent(active)+
      '&yaw='+encodeURIComponent(yaw)+'&pitch='+encodeURIComponent(pitch)+
      '&distance='+encodeURIComponent(distance);
    const data=await (await api(url)).blob();
    if(dead||at!==serial)return;
    const objectUrl=URL.createObjectURL(data);
    const previous=frame.dataset.objectUrl;
    frame.src=objectUrl;frame.dataset.objectUrl=objectUrl;
    if(previous)URL.revokeObjectURL(previous);
    setStatus('PC-rendered 3D · drag to orbit · pinch to zoom');
  }catch(e){setStatus(String(e.message||e));}
  finally{
    busy=false;
    if(scheduled&&!dead){scheduled=false;render();}
  }
}
function requestFrame(){if(!active||dead)return;if(busy)scheduled=true;else render();}
function onOpen(response){
  try{
    const data=typeof response==='string'?JSON.parse(response):response;
    if(data.error){setStatus(data.error);return;}
    active=data.session||null;
    setStatus(data.ready?'Connected · preparing native 3D…':
      (data.error||'Native renderer is not yet online'));
    if(data.ready)requestFrame();
  }catch(e){setStatus('Invalid native PC response: '+e.message);}
}
function close(){
  dead=true;active=null;contacts.clear();serial++;
  if(frame?.dataset?.objectUrl)URL.revokeObjectURL(frame.dataset.objectUrl);
  if(overlay)overlay.remove();overlay=null;frame=null;status=null;
}
function open(nextKind='cube'){
  close();dead=false;kind=nextKind;active=null;busy=false;scheduled=false;
  yaw=.4;pitch=.2;distance=2.5;
  overlay=el('section','fg-pc-overlay');overlay.setAttribute('role','dialog');
  overlay.setAttribute('aria-label','Native PC 3D Viewer');
  const head=el('div','fg-pc-head');
  head.append(el('strong',null,kind==='koikatsu'?'Koikatsu · PC Native 3D':
    kind==='blend'?'Blender · PC Native Scene':'Blender · Independent Cube'));
  const closeButton=el('button','fg-pc-close','Close');
  closeButton.onclick=close;head.append(closeButton);overlay.append(head);
  const pair=el('div','fg-pc-pair');
  const input=el('input','fg-pc-token');
  input.type='password';input.placeholder='PC pairing token (first connection)';
  input.value=token();
  const save=el('button','fg-pc-action','Pair');
  save.onclick=()=>{bridge()?.setRemoteToken?.(input.value.trim());setStatus('Pairing saved only on this phone.');};
  pair.append(input,save);overlay.append(pair);
  viewport=el('div','fg-pc-viewport');
  frame=el('img','fg-pc-frame');frame.alt='Remote native 3D scene';
  frame.draggable=false;viewport.append(frame);overlay.append(viewport);
  status=el('div','fg-pc-status','Not connected');
  overlay.append(status);
  const actions=el('div','fg-pc-actions');
  const connect=el('button','fg-pc-action','Open on PC');
  connect.onclick=()=>{
    if(input.value.trim()!==token())bridge()?.setRemoteToken?.(input.value.trim());
    setStatus('Connecting to PC…');
    try{bridge()?.remoteOpen3D?.(kind);}catch(e){setStatus(String(e));}
  };
  const reset=el('button','fg-pc-action','Reset view');
  reset.onclick=()=>{yaw=.4;pitch=.2;distance=2.5;requestFrame();};
  actions.append(connect,reset);overlay.append(actions);
  let center=null;
  viewport.addEventListener('pointerdown',e=>{
    viewport.setPointerCapture(e.pointerId);
    contacts.set(e.pointerId,{x:e.clientX,y:e.clientY});
    center=null;
  });
  viewport.addEventListener('pointermove',e=>{
    if(!contacts.has(e.pointerId))return;
    const old=contacts.get(e.pointerId);
    contacts.set(e.pointerId,{x:e.clientX,y:e.clientY});
    if(contacts.size===1){
      yaw+=(e.clientX-old.x)*.012;
      pitch=Math.max(-1.25,Math.min(1.25,pitch+(e.clientY-old.y)*.008));
    }else if(contacts.size===2){
      const points=[...contacts.values()];
      const span=Math.hypot(points[0].x-points[1].x,points[0].y-points[1].y);
      if(lastSpan)distance=Math.max(1.05,Math.min(15,distance*lastSpan/Math.max(span,1)));
      lastSpan=span;
    }
  });
  const end=e=>{
    contacts.delete(e.pointerId);lastSpan=0;
    if(contacts.size===0)requestFrame();
  };
  viewport.addEventListener('pointerup',end);viewport.addEventListener('pointercancel',end);
  document.body.append(overlay);
}
window.FileGestionerRemoteViewer={open,onOpen,close};
const entry=el('button','fg-pc-entry','PC 3D');
entry.type='button';entry.setAttribute('aria-label','Open independent native Blender cube on PC');
let entryKind=null;
entry.hidden=true;
entry.onclick=()=>{if(entryKind)open(entryKind);};
const originalLoad=window.loadDocument;
if(typeof originalLoad==='function'){
  window.loadDocument=function(documentInfo){
    entryKind=documentInfo?.koikatsuCard===true?'koikatsu':
      documentInfo?.type==='model3d'&&['blend','blend1'].includes(documentInfo?.format)?'blend':null;
    entry.hidden=!entryKind;
    if(entryKind)entry.textContent=entryKind==='koikatsu'?'Open Koikatsu 3D':'Open in Blender';
    close();
    return originalLoad.apply(this,arguments);
  };
}
document.body.append(entry);
// Independent cube entry belongs to the Library's 3D tools, never on PDFs,
// books, spreadsheets or ordinary images. No permanent floating 3D control.
const cubeEntry=el('button','fg-lib-secondary fg-pc-cube','Blender cube');
cubeEntry.type='button';cubeEntry.title='Render independent Blender cube on PC';
cubeEntry.onclick=()=>open('cube');
document.querySelector('#fg-library .fg-lib-actions')?.append(cubeEntry);

})();