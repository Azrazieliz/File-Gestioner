from pathlib import Path

INDEX = Path("app/src/main/assets/index.html")
CSS = Path("app/src/main/assets/style.css")

MARKER = "/* OpenLocalOffice mobile spreadsheet UI hotfix */"

css = CSS.read_text()
if MARKER not in css:
    css += r'''

/* OpenLocalOffice mobile spreadsheet UI hotfix */
html,body{
  width:100%;
  max-width:100%;
  overflow-x:hidden;
}
*,*::before,*::after{box-sizing:border-box}
body{margin:0}
.work,.searchbar,.sheetbar,.rangeNav,#editor{
  min-width:0;
  max-width:100%;
}
.work{
  width:100%;
  overflow-x:hidden;
}
.searchbar{
  width:100%;
  display:grid;
  grid-template-columns:minmax(0,1fr) auto;
  gap:8px;
  align-items:center;
}
.searchbar input{
  width:100%;
  min-width:0;
}
#searchResults{
  grid-column:1/-1;
  min-width:0;
  max-width:100%;
}
.sheetbar{
  width:100%;
  overflow:hidden;
}
.tabs{
  display:flex;
  width:100%;
  min-width:0;
  max-width:100%;
  gap:8px;
  overflow-x:auto;
  overflow-y:hidden;
  overscroll-behavior-x:contain;
  -webkit-overflow-scrolling:touch;
  scrollbar-width:none;
  padding-bottom:2px;
}
.tabs::-webkit-scrollbar{display:none}
.tabs>button,.tabs>[role="tab"]{
  flex:0 0 auto;
  max-width:min(72vw,280px);
  overflow:hidden;
  text-overflow:ellipsis;
  white-space:nowrap;
}
.rangeNav{
  width:100%;
  display:grid;
  grid-template-columns:repeat(4,minmax(0,1fr));
  gap:6px;
  align-items:center;
}
.rangeNav button{
  width:100%;
  min-width:0;
  white-space:nowrap;
  overflow:hidden;
  text-overflow:ellipsis;
}
#rangeInfo{
  grid-column:1/-1;
  min-width:0;
  text-align:center;
  white-space:nowrap;
  overflow:hidden;
  text-overflow:ellipsis;
}
#goCell{
  grid-column:1/4;
  width:100%;
  min-width:0;
}
#goCellBtn{
  grid-column:4;
}
#editor{
  width:100%;
  overflow:auto;
  overscroll-behavior:contain;
  -webkit-overflow-scrolling:touch;
  touch-action:pan-x pan-y;
}

/* The spreadsheet, not the page, owns horizontal scrolling. */
#sheetBar:not(.hidden) ~ #editor{
  width:100%;
  min-width:0;
  max-width:100%;
  overflow:auto!important;
}
#sheetBar:not(.hidden) ~ #editor table{
  width:max-content;
  min-width:100%;
  max-width:none;
  border-collapse:separate;
  border-spacing:0;
}
#sheetBar:not(.hidden) ~ #editor table thead th{
  position:sticky;
  top:0;
  z-index:5;
}
#sheetBar:not(.hidden) ~ #editor table tr>th:first-child,
#sheetBar:not(.hidden) ~ #editor table tr>td:first-child{
  position:sticky;
  left:0;
  z-index:4;
}
#sheetBar:not(.hidden) ~ #editor table thead tr>th:first-child{
  z-index:6;
}

@media(max-width:700px){
  .bar{
    width:100%;
    max-width:100%;
    padding:8px 10px;
    gap:8px;
  }
  .brand{min-width:0}
  .brand strong,
  .brand span{
    min-width:0;
    overflow:hidden;
    text-overflow:ellipsis;
    white-space:nowrap;
  }
  .actions{
    flex:0 0 auto;
    gap:6px;
  }
  .actions button{
    min-width:0;
    padding:8px 10px;
  }
  .searchbar{
    padding:8px 10px;
    gap:6px;
  }
  .searchbar input,
  .searchbar button{
    min-height:44px;
  }
  .searchbar button{
    padding-inline:14px;
  }
  .sheetbar{
    padding:0 10px 8px;
  }
  .tabs{
    gap:6px;
    padding:2px 0 6px;
  }
  .tabs>button,.tabs>[role="tab"]{
    min-height:40px;
    max-width:68vw;
    padding:7px 13px;
    font-size:14px;
  }
  .rangeNav{
    gap:6px;
  }
  .rangeNav button{
    min-height:40px;
    padding:7px 5px;
    font-size:13px;
  }
  #rangeInfo{
    padding:2px 4px;
    font-size:12px;
    opacity:.82;
  }
  #goCell,
  #goCellBtn{
    min-height:40px;
  }
  #sheetBar:not(.hidden) ~ #editor table th,
  #sheetBar:not(.hidden) ~ #editor table td{
    min-width:116px;
    max-width:220px;
  }
  #sheetBar:not(.hidden) ~ #editor table tr>th:first-child,
  #sheetBar:not(.hidden) ~ #editor table tr>td:first-child{
    width:46px;
    min-width:46px;
    max-width:46px;
  }
}
'''
    CSS.write_text(css)

html = INDEX.read_text()
# Allow users to zoom while keeping the layout device-width bound.
html = html.replace(",maximum-scale=1", "")
INDEX.write_text(html)
