from pathlib import Path

INDEX = Path('app/src/main/assets/index.html')
CSS = Path('app/src/main/assets/style.css')
APP = Path('app/src/main/assets/app.js')
MAIN = Path('app/src/main/java/com/openlocal/office/MainActivity.java')

HTML_MARKER = 'id="spreadsheetTools"'
CSS_MARKER = '/* File Gestioner spreadsheet interaction layer */'
JS_MARKER = '/* File Gestioner spreadsheet interaction layer */'
JAVA_MARKER = 'getClipboardText()'

html = INDEX.read_text()
if HTML_MARKER not in html:
    toolbar = r'''  <div id="spreadsheetTools" class="spreadsheetTools hidden" aria-label="Spreadsheet tools">
    <div class="cellRefBox" id="selectedCellRef" aria-live="polite">A1</div>
    <label class="formulaBox" aria-label="Cell value or formula">
      <span class="fxLabel">fx</span>
      <input id="formulaInput" type="text" autocomplete="off" autocapitalize="off" spellcheck="false" placeholder="Value or formula">
    </label>
    <div class="sheetQuickActions" aria-label="Edit actions">
      <button id="sheetUndo" type="button" aria-label="Undo" title="Undo">↶</button>
      <button id="sheetRedo" type="button" aria-label="Redo" title="Redo">↷</button>
      <button id="sheetCopy" type="button" aria-label="Copy selection" title="Copy">⧉</button>
      <button id="sheetCut" type="button" aria-label="Cut selection" title="Cut">✂</button>
      <buttton id="sheetPaste" type="button" aria-label="Paste" title="Paste">▃</button>
      <button id="sheetClear" type="button" aria-label="Clear selection" title="Clear">⌫</button>
    </div>
  </div>\n'''
    marker = '  <div id="textFormat" class="formatbar hidden">'
    if marker not in html:
        raise SystemExit('Could not locate text format bar for spreadsheet toolbar insertion')
    html = html.replace(marker, toolbar + marker, 1)
    INDEX.write_text(html)

css = CSS.read_text()
if CSS_MARKER not in css:
    css += r'''

/* File Gestioner spreadsheet interaction layer */
.spreadsheetTools{
  display:grid;
  grid-template-columns:auto minmax(180px,1fr) auto;
  gap:8px;
  align-items:center;
  width:100%;
  min-width:0;
  padding:8px 10px;
  background:var(--fg-card,var(--panel,#fff));
  border-bottom:1px solid var(--fg-border,var(--border,#d8dde7));
  position:relative;
  z-index:35;
}
.spreadsheetTools.hidden{display:none!important}
.cellRefBox{
  min-width:64px;
  height:40px;
  display:flex;
  align-items:center;
  justify-content:center;
  padding:0 10px;
  border:1px solid var(--fg-border,var(--border,#d8dde7));
  border-radius:10px;
  background:var(--fg-elevated,var(--bg,#fff));
  color:var(--fg-text,currentColor);
  font:700 13px/1 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
  font-variant-numeric:tabular-nums;
  white-space:nowrap;
}
.formulaBox{
  display:grid;
  grid-template-columns:auto minmax(0,1fr);
  align-items:center;
  min-width:0;
  height:40px;
  border:1px solid var(--fg-border,var(--border,#d8dde7));
  border-radius:10px;
  background:var(--fg-elevated,var(--bg,#fff));
  overflow:hidden;
}
.fxLabel{
  padding:0 9px;
  color:var(--fg-accent,#7187ff);
  font:800 13px/1 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
  user-select:none;
}
#formulaInput{
  width:100%;
  min-width:0;
  height:38px;
  padding:0 10px 0 0;
  border:0!important;
  outline:0!important;
  background:transparent!important;
  color:var(--fg-text,currentColor)!important;
  box-shadow:none!important;
  font-size:14px;
}
.sheetQuickActions{
  display:flex;
  gap:4px;
  min-width:0;
}
.sheetQuickActions button{
  width:38px;
  min-width:38px;
  height:38px;
  padding:0;
  display:grid;
  place-items:center;
  border:1px solid var(--fg-border,var(--border,#d8dde7));
  border-radius:10px;
  background:var(--fg-elevated,var(--bg,#fff));
  color:var(--fg-text,currentColor);
  font-size:17px;
  line-height:1;
}
.sheetQuickActions button:disabled{opacity:.38}
#editor table.sheet td{
  cursor:cell;
  user-select:none;
  -webkit-user-select:none;
  position:relative;
}
#editor table.sheet td.fg-selected{
  background:color-mix(in srgb,var(--fg-accent,#7187ff) 13%,transparent)!important;
}
#editor table.sheet td.fg-selection-edge::after{
  content:"";
  position:absolute;
  inset:-1px;
  border:2px solid var(--fg-accent,#7187ff);
  pointer-events:none;
  z-index:8;
}
#editor table.sheet td.fg-active-cell::after{
  content:"";
  position:absolute;
  inset:-1px;
  border:2px solid var(--fg-accent,#7187ff);
  pointer-events:none;
  z-index:9;
}
#editor table.sheet td[contenteditable="true"]{
  cursor:text;
  user-select:text;
  -webkit-user-select:text;
  background:var(--fg-card,#fff)!important;
  box-shadow:inset 0 0 0 2px var(--fg-accent,#7187ff);
  z-index:10;
}
#editor table.sheet th.fg-header-selected{
  color:var(--fg-accent,#7187ff)!important;
  background:color-mix(in srgb,var(--fg-accent,#7187ff) 12%,var(--fg-elevated,#fff))!important;
}
@media(max-width:700px){
  .spreadsheetTools{
    grid-template-columns:64px minmax(0,1fr);
    gap:6px;
    paddin:7px 10px 8px;
  }
  .cellRefBox,.formulaBox{height:38px}
  #formulaInput{height:36px;font-size:16px}
  .sheetQuickActions{
    grid-column:1/-1;
    display:grid;
    grid-template-columns:repeat(6,1fr);
    width:100%;
  }
  .sheetQuickActions button{
    width:100%;
    min-width:0;
    height:36px;
  }
}
'''
    CSS.write_text(css)

app = APP.read_text()
if JS_MARKER not in app:
    app += r'''

/* File Gestioner spreadsheet interaction layer */
(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const editor = $('editor');
  const sheetBar = $('sheetBar');
  const tools = $('spreadsheetTools');
  const formula = $('formulaInput');
  const refBox = $('selectedCellRef');
  if(!editor || !sheetBar || !tools || !formula || !refBox) return;

  const selection = {
    anchor:null,
    focus:null,
    active:null,
    lastSheet:-1,
    pending:null,
    dragging:false,
    touchTimer:null,
    touchStart:null,
    lastTapAt:0,
    lastTapKey:'',
    undo:[],
    redo:[],
    editBefore:null,
  };
  const MAX_HISTORY = 100;
  const bridge = () => window.AndroidBridge || null;

  function activeSheetIndex(){
    const children=Array.from($('tabs')?.children||[]);
    const active=children.findIndex(el=>el.classList.contains('active')||el.getAttribute('aria-selected')==='true');
    return Math.max(0,active);
  }
  function isSpreadsheet(){
    return !sheetBar.classList.contains('hidden') && !!editor.querySelector('table.sheet');
  }
  function coords(td){
    if(!td?.matches?.('td[data-r][data-c]'))return null;
    return {row:Number(td.dataset.r),col:Number(td.dataset.c)};
  }
  function keyOf(p){return p?`${p.row}:${p.col}`:'';}
  function alpha(n){let s='';for(n++;n>0;n=Math.floor((n-1)/26))s=String.fromCharCode(65+(n-1)%26)+s;return s;}
  function cellRef(p){return p?`${alpha(p.col)}${p.row+1}`:'';}
  function parseAlpha(s){let n=0;for(const ch of String(s||'').trim().toUpperCase()){if(ch<'A'||ch>'Z')return -1;n=n*26+(ch.charCodeAt(0)-64);}return n-1;}
  function cellAt(p){return p?editor.querySelector(`td[data-r="${p.row}"][data-c="${p.col}"]`):null;}
  function visibleCells(){return Array.from(editor.querySelectorAll('table.sheet td[data-r][data-c]'));}
  function visibleBounds(){
    const cells=visibleCells(); if(!cells.length)return null;
    const rows=cells.map(x=>Number(x.dataset.r)), cols=cells.map(x=>Number(x.dataset.c));
    return {r1:Math.min(...rows),r2:Math.max(...rows),c1:Math.min(...cols),c2:Math.max(...cols)};
  }
  function rangeBounds(){
    if(!selection.anchor||!selection.focus)return null;
    return {
      r1:Math.min(selection.anchor.row,selection.focus.row),
      r2:Math.max(selection.anchor.row,selection.focus.row),
      c1:Math.min(selection.anchor.col,selection.focus.col),
      c2:Math.max(selection.anchor.col,selection.focus.col),
    };
  }
  function inRange(p,b){return !!b&&p.row>=b.r1&&p.row<=b.r2&&p.col>=b.c1&&p.col<=b.c2;}
  function selectionLabel(){
    const b=rangeBounds();if(!b)return 'A1';
    const a=cellRef({row:b.r1,col:b.c1}),z=cellRef({row:b.r2,col:b.c2});
    return a===z?a:`${a}:$z{}`;
  }
  function updateToolbar(){
    const active=cellAt(selection.active||selection.focus||selection.anchor);
    refBox.textContent=selectionLabel();
    if(document.activeElement!==formula)formula.value=active?.textContent||'';
    $('sheetUndo').disabled=!selection.undo.length;
    $('sheetRedo').disabled=!selection.redo.length;
    const enabled=!!rangeBounds();
    for(const id of ['sheetCopy','sheetCut','sheetClear'])$(id).disabled=!enabled;
  }
  function paintSelection(){
    const b=rangeBounds();
    editor.querySelectorAll('.fg-selected,.fg-active-cell,.fg-selection-edge').forEach(el=>el.classList.remove('fg-selected','fg-active-cell','fg-selection-edge'));
    editor.querySelectorAll('.fg-header-selected').forEach(el=>el.classList.remove('fg-header-selected'));
    if(!b){updateToolbar();return;}
    for(const td of visibleCells(){
      const p=coords(td); if(!inRange(p,b))continue;
      td.classList.add('fg-selected');
      if(p.row===b.r1||p.row===b.r2||p.col===b.c1||p.col===b.c2)td.classList.add('fg-selection-edge');
    }
    const active=cellAt(selection.active||selection.focus);
    active?.classList.add('fg-active-cell');
    const table=editor.querySelector('table.sheet');
    if(table){
      const head=table.tHead?.rows?.[0];
      if(head){for(let i=1;i<head.cells.length;i++){const col=parseAlpha(head.cells[i].textContent);if(col>=b.c1&&col<=b.c2)head.cells[i].classList.add('fg-header-selected');}}
      for(const row of Array.from(table.tBodies?.[0]?.rows||[])){
        const th=row.cells?.[0]; if(!th)return;
        const r=Number(th.textContent)-1;if(r>=b.r1&&r<=b.r2)th.classList.add('fg-header-selected');
      }
    }
    updateToolbar();
  }
  function selectCell(p,extend=false,scroll=false){
    if(!p)return;
    if(!extend||!selection.anchor)selection.anchor={...p};
    selection.focus={...p};selection.active={...p};
    paintSelection();
    if(scroll)cellAt(p)?.scrollIntoView({block:'nearest',inline:'nearest'});
  }
  function selectRange(a,z,active=z){selection.anchor={...a};selection.focus={...z