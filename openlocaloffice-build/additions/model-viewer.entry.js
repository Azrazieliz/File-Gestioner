/* File Gestioner 3D asset viewer. Bundled OFFLINE with three.js r186 (MIT).
   Read-only: model bytes stay in the local Android WebView. */
import * as T from './three-vendor/three.module.js';
import { OrbitControls } from './three-vendor/addons/controls/OrbitControls.js';
import { GLTFLoader } from './three-vendor/addons/loaders/GLTFLoader.js';
import { OBJLoader } from './three-vendor/addons/loaders/OBJLoader.js';
import { FBXLoader } from './three-vendor/addons/loaders/FBXLoader.js';
import { STLLoader } from './three-vendor/addons/loaders/STLLoader.js';
import { PLYLoader } from './three-vendor/addons/loaders/PLYLoader.js';
import { ColladaLoader } from './three-vendor/addons/loaders/ColladaLoader.js';
import { ThreeMFLoader } from './three-vendor/addons/loaders/3MFLoader.js';
import { TDSLoader } from './three-vendor/addons/loaders/TDSLoader.js';
import { AMFLoader } from './three-vendor/addons/loaders/AMFLoader.js';
import { USDLoader } from './three-vendor/addons/loaders/USDLoader.js';

const E=(tag,cls,txt)=>{const node=document.createElement(tag);if(cls)node.className=cls;if(txt!==undefined)node.textContent=txt;return node;};
const q=(name,fn)=>{const b=E('button','fg-3d-button',name);b.type='button';b.addEventListener('click',fn);return b;};
const decoder=new TextDecoder('utf-8');
let active=null;
function reset(){
  if(!active)return;
  const p=active; active=null;p.dead=true;
  if(p.frameId)cancelAnimationFrame(p.frameId);
  if(p.observer)p.observer.disconnect();
  if(p.controls)p.controls.dispose();
  if(p.renderer){p.renderer.dispose();p.renderer.forceContextLoss();p.renderer.domElement.remove();}
  if(p.root)p.root.traverse(obj=>{
    if(obj.geometry)obj.geometry.dispose();
    for(const mat of (Array.isArray(obj.material)?obj.material:[obj.material])){
      if(!mat)continue;
      for(const key of ['map','normalMap','emissiveMap','roughnessMap','metalnessMap','aoMap','alphaMap']){
        if(mat[key]&&mat[key].isTexture)mat[key].dispose();
      }
      mat.dispose();
    }
  });
  for(const url of p.urls||[])URL.revokeObjectURL(url);
}
function chunks(bridge,report,stale){
  const size=Number(bridge.getRawDocumentSize?.()||0);
  if(!Number.isSafeInteger(size)||size<=0||size>80*1024*1024)throw Error('Model is empty or exceeds the 80 MiB offline preview limit.');
  const buffer=new Uint8Array(size),step=96*1024;
  return (async()=>{
    for(let offset=0;offset<size;offset+=step){
      if(stale())throw Error('Model changed while loading.');
      const encoded=bridge.getRawDocumentChunk(offset,Math.min(step,size-offset));
      if(!encoded)throw Error('Cannot read the archived model bytes.');
      const raw=atob(encoded);
      if(raw.length>step||raw.length+offset>size)throw Error('Invalid model byte chunk.');
      for(let i=0;i<raw.length;i++)buffer[offset+i]=raw.charCodeAt(i);
      if((offset/step)%24===0){report('Reading file · '+Math.round(100*offset/size)+'%');await new Promise(resolve=>setTimeout(resolve,0));}
    }
    return buffer.buffer;
  })();
}
function manager(){
  const m=new T.LoadingManager();
  m.setURLModifier(url=>{
    if(/^(data:|blob:)/i.test(url))return url;
    throw new Error('This model references an external texture, .bin or material file. Open a self-contained GLB or embed its dependencies.');
  });
  return m;
}
function geometryGroup(geometry,name,points=false){
  const group=new T.Group();group.name=name;
  if(geometry.attributes.color&&geometry.attributes.color.itemSize>=3) {
    group.add(new T.Mesh(geometry,new T.MeshStandardMaterial({vertexColors:true,side:T.DoubleSide,metalness:.05,roughness:.85})));
  }else if(points){
    group.add(new T.Points(geometry,new T.PointsMaterial({color:0x76a6e6,size:.02,sizeAttenuation:true})));
  }else{
    if(!geometry.attributes.normal)geometry.computeVertexNormals();
    group.add(new T.Mesh(geometry,new T.MeshStandardMaterial({color:0xa5bde7,side:T.DoubleSide,metalness:.1,roughness:.75})));
  }
  return group;
}
function parse(format,buffer){
  const text=()=>decoder.decode(new Uint8Array(buffer));
  const m=manager();
  switch(format){
    case 'glb':case 'gltf':
      return new Promise((resolve,reject)=>{
        new GLTFLoader(m).parse(format==='glb'?buffer:text(),'',
          data=>resolve({root:data.scene||data.scenes?.[0],clips:data.animations||[]}),reject);
      });
    case 'obj':return Promise.resolve({root:new OBJLoader(m).parse(text()),clips:[]});
    case 'fbx':{
      const model=new FBXLoader(m).parse(buffer,'');
      return Promise.resolve({root:model,clips:model.animations||[]});
    }
    case 'stl':return Promise.resolve({root:geometryGroup(new STLLoader(m).parse(buffer),'STL'),clips:[]});
    case 'ply':{
      const g=new PLYLoader(m).parse(buffer);
      const points=!g.index&&!g.attributes.normal;
      return Promise.resolve({root:geometryGroup(g,'PLY',points),clips:[]});
    }
    case 'dae':{
      const model=new ColladaLoader(m).parse(text(),'');
      return Promise.resolve({root:model.scene,clips:model.animations||[]});
    }
    case '3mf':return Promise.resolve({root:new ThreeMFLoader(m).parse(buffer),clips:[]});
    case '3ds':return Promise.resolve({root:new TDSLoader(m).parse(buffer),clips:[]});
    case 'amf':return Promise.resolve({root:new AMFLoader(m).parse(buffer),clips:[]});
    case 'usdz':case 'usda':case 'usdc':{
      return new Promise((resolve,reject)=>{
        try{
          let called=false;
          const result=new USDLoader(m).parse(buffer,'',root=>{called=true;resolve({root,clips:[]})},reject);
          if(!called&&!result)reject(Error('USD file could not be parsed.'));
        }catch(e){reject(e);}
      });
    }
    default:throw Error('Unsupported model format: '+format+'. Native .blend/.max/.ma projects require an export to GLB or FBX.');
  }
}
function open(doc,host,bridge){
  reset();
  const rootUI=E('div','fg-3d-app');
  const top=E('div','fg-3d-toolbar');
  const headline=E('div','fg-3d-heading');
  headline.append(E('span','fg-3d-badge',(doc.format||'3D').toUpperCase()),E('strong','fg-3d-name',doc.name||'3D asset'));
  top.append(headline);
  const actions=E('div','fg-3d-tools');
  top.append(actions);
  const area=E('div','fg-3d-area');
  const viewport=E('div','fg-3d-canvas');
  const overlay=E('div','fg-3d-overlay','Preparing offline model preview…');
  area.append(viewport,overlay);
  const info=E('section','fg-3d-info','Read-only · Local 3D model · Drag to rotate · Pinch to zoom · Two-finger drag to pan');
  rootUI.append(top,area,info);
  host.classList.add('fg-reader-host');
  host.replaceChildren(rootUI);
  for(const id of ['sheetBar','spreadsheetTools','textFormat','notice'])document.getElementById(id)?.classList.add('hidden');
  document.querySelector('.searchbar')?.classList.add('hidden');
  document.getElementById('saveBtn').disabled=true;
  document.getElementById('copyBtn').disabled=true;

  const state={dead:false,root:null,renderer:null,controls:null,urls:[],frameId:null,observer:null};
  active=state;
  const isOld=()=>state.dead||active!==state;
  const status=t=>{if(!isOld())overlay.textContent=t;};
  const load=async()=>{
    try{
      if(!bridge)throw Error('Android file bridge is unavailable.');
      if(!window.WebGLRenderingContext)throw Error('This Android WebView does not support WebGL.');
      const buffer=await chunks(bridge,status,isOld);
      if(isOld())return;
      const parsed=await parse(String(doc.format||'').toLowerCase(),buffer);
      if(isOld())return;
      const model=parsed.root;
      if(!model)throw Error('The model has no visible scene.');
      state.root=model;
      const scene=new T.Scene();
      scene.background=new T.Color(0x141b28);
      scene.add(new T.HemisphereLight(0xffffff,0x445872,2.1));
      const key=new T.DirectionalLight(0xffffff,3);
      key.position.set(3,8,5);scene.add(key);
      const fill=new T.DirectionalLight(0xa5c4ff,1.1);
      fill.position.set(-5,2,-6);scene.add(fill);
      scene.add(model);
      const grid=new T.GridHelper(10,20,0x657997,0x263747);
      const axes=new T.AxesHelper(1);
      scene.add(grid,axes);
      axes.visible=false;
      const camera=new T.PerspectiveCamera(42,1,.001,100000);
      const renderer=new T.WebGLRenderer({antialias:true,alpha:false,powerPreference:'low-power',preserveDrawingBuffer:false});
      renderer.setPixelRatio(Math.min(2,window.devicePixelRatio||1));
      renderer.outputColorSpace=T.SRGBColorSpace;
      renderer.toneMapping=T.ACESFilmicToneMapping;
      renderer.toneMappingExposure=1.25;
      viewport.append(renderer.domElement);
      state.renderer=renderer;
      const controls=new OrbitControls(camera,renderer.domElement);
      state.controls=controls;
      controls.enableDamping=true;controls.dampingFactor=.12;
      controls.minDistance=.001;controls.maxDistance=1000000;
      controls.screenSpacePanning=true;
      function fit(){
        const bounds=new T.Box3().setFromObject(model);
        if(bounds.isEmpty())throw Error('This model has no renderable geometry.');
        const center=bounds.getCenter(new T.Vector3());
        const span=bounds.getSize(new T.Vector3()).length();
        const radius=Math.max(.001,span/2);
        const dist=radius/Math.sin(T.MathUtils.degToRad(camera.fov/2))*1.45;
        camera.position.copy(center).add(new T.Vector3(dist*.7,dist*.45,dist));
        camera.near=Math.max(.00001,radius/500);
        camera.far=Math.max(100,radius*1000);
        camera.updateProjectionMatrix();
        controls.target.copy(center);
        controls.minDistance=Math.max(.00001,radius*.015);
        controls.maxDistance=Math.max(100,radius*1000);
        controls.update();
        grid.position.y=bounds.min.y;
        grid.scale.setScalar(Math.max(.01,span/10));
        axes.position.copy(center);
        axes.scale.setScalar(Math.max(.01,radius*.5));
      }
      fit();
      let meshes=0,faces=0,vertices=0,materials=0;
      model.traverse(o=>{if(!o.isMesh&&!o.isPoints&&!o.isLine)return;meshes++;
        if(o.geometry){const g=o.geometry,qty=g.index?.count??g.attributes.position?.count??0;
          vertices+=g.attributes.position?.count??0;
          if(o.isMesh)faces+=Math.floor(qty/3);}
        materials+=Array.isArray(o.material)?o.material.length:Number(!!o.material);
      });
      if(!meshes)throw Error('The model loaded but has no displayable meshes.');
      info.textContent=`${meshes.toLocaleString()} objects · ${vertices.toLocaleString()} vertices · ${faces.toLocaleString()} triangles · ${materials} materials · ${(buffer.byteLength/1048576).toFixed(1)} MiB`;
      actions.append(q('Fit',fit));
      let wire=false;
      actions.append(q('Wireframe',()=>{
        wire=!wire;model.traverse(o=>{if(!o.material)return;
          for(const m of (Array.isArray(o.material)?o.material:[o.material]))if('wireframe' in m)m.wireframe=wire;
        });
      }));
      actions.append(q('Grid',()=>{grid.visible=!grid.visible;}));
      actions.append(q('Axes',()=>{axes.visible=!axes.visible;}));
      const clips=parsed.clips||[];
      const mixer=clips.length?new T.AnimationMixer(model):null;
      if(clips.length){
        const selector=E('select','fg-3d-select');
        selector.append(E('option','',`Animations (${clips.length}) · paused`));
        clips.forEach((clip,i)=>{const o=E('option','',clip.name||'Animation '+(i+1));o.value=String(i);selector.append(o);});
        selector.onchange=()=>{
          mixer.stopAllAction();
          if(selector.value!==''){const clip=clips[Number(selector.value)];mixer.clipAction(clip).reset().play();}
        };
        actions.append(selector);
      }
      overlay.remove();
      const clock=new T.Clock();
      const resize=()=>{
        if(isOld())return;
        const w=Math.max(1,viewport.clientWidth),h=Math.max(1,viewport.clientHeight);
        camera.aspect=w/h;camera.updateProjectionMatrix();renderer.setSize(w,h,false);
      };
      if(window.ResizeObserver){state.observer=new ResizeObserver(resize);state.observer.observe(viewport);}
      resize();
      const tick=()=>{
        if(isOld())return;
        state.frameId=requestAnimationFrame(tick);
        const delta=Math.min(clock.getDelta(),.1);
        if(mixer)mixer.update(delta);
        controls.update();
        renderer.render(scene,camera);
      };
      tick();
    }catch(error){
      if(isOld())return;
      status('Cannot preview this model: '+String(error?.message||error));
      info.textContent='3D previews are read-only. Use self-contained models (GLB recommended); complex CAD and native Blender project files need conversion.';
    }
  };
  load();
}
window.FileGestionerModelViewer={open,dispose:reset,formats:['glb','gltf','obj','fbx','stl','ply','dae','3mf','3ds','amf','usdz','usda','usdc']};
