from pathlib import Path

INDEX=Path("app/src/main/assets/index.html")
CSS=Path("app/src/main/assets/style.css")
JS=Path("app/src/main/assets/app.js")

html=INDEX.read_text()
html=html.replace(
    '<script src="app.js"></script>',
    '<script src="app.js"></script>\n<script src="universal-reader.js"></script>'
)
html=html.replace(
    'Open, inspect and edit spreadsheets and documents with a fast, local-first workflow.',
    'A private, beautifully readable space for documents, ebooks, PDFs, spreadsheets and image archives.'
)
html=html.replace(
    'XLSX · CSV · DOCX · TXT · MD · SDOCX',
    'PDF · DOCX · XLSX · PPTX · EPUB · ODT · ODS · ODP · SDOCX · RTF · HTML · TXT · MD · CBZ · ZIP · IMAGES'
)
html=html.replace(
    '<div class="card small"><strong>Private by design</strong>',
    '<div class="fg-home-intro"><div><strong>Read naturally.</strong><span>Document pages, slide text, ebook chapters, image and comic previews.</span></div><div><strong>Edit deliberately.</strong><span>Keep the original spreadsheet, DOCX, text and Samsung Notes editors.</span></div></div>\n'
    '<div class="card small"><strong>Private by design</strong>'
)
INDEX.write_text(html)

js=JS.read_text()
# Drop the destructive "each paragraph is a heading" presentation on DOCX read pages.
reader=Path("app/src/main/assets/universal-reader.js")
source=reader.read_text()
source=source.replace("for(const [i,txt] of docxEntries())addLines(p,txt,'docx');",
                      "for(const [i,txt] of docxEntries())addLines(p,txt,i===0?'docx':'paragraph');")
reader.write_text(source)

marker="/* File Gestioner immersive reader + unified document UI */"
css=CSS.read_text()
if marker not in css:
    css += r'''

/* File Gestioner immersive reader + unified document UI */
:root {
  --fg-app-bg:#eef1f6;
  --fg-paper:#fff;
  --fg-paper-text:#253044;
  --fg-reader-muted:#68758b;
  --fg-reader-border:#dbe1eb;
  --fg-reader-accent:#526cd6;
}
@media (prefers-color-scheme:dark) {
  :root {
    --fg-app-bg:#10141b;
    --fg-paper:#1c2330;
    --fg-paper-text:#e9edf5;
    --fg-reader-muted:#a6b1c3;
    --fg-reader-border:#374255;
    --fg-reader-accent:#9badff;
  }
}
html,body{background:var(--fg-app-bg);font-family:system-ui,-apple-system,Roboto,sans-serif}
.home{width:min(100%,900px);max-width:900px;padding:30px 20px calc(35px + env(safe-area-inset-bottom))}
.hero{
  position:relative;overflow:hidden;text-align:left;
  padding:clamp(26px,5vw,48px);
  background:linear-gradient(138deg,#1b2851 0%,#27396b 48%,#18243e 100%);
  border:1px solid #465681;
  box-shadow:0 24px 60px #14234422;
  color:#fff;
}
.hero::after{
  content:"";position:absolute;pointer-events:none;
  width:230px;height:230px;right:-100px;top:-110px;
  border:45px solid #ffffff0a;border-radius:42px;transform:rotate(25deg)
}
.hero h1{font-size:clamp(34px,7vw,52px);max-width:16ch;line-height:1.05;letter-spacing:-.045em}
.hero p{color:#d2dcf4;max-width:55ch;line-height:1.6}
.hero .formats{margin-top:22px;font-size:11px;font-weight:650;letter-spacing:.05em;line-height:1.8;color:#d2dcf4!important}
.hero button{background:#a1b4ff!important;color:#111b35!important;border:none!important;min-height:48px;font-weight:750}
.fg-home-intro{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;margin-bottom:14px}
.fg-home-intro>div{display:flex;flex-direction:column;gap:8px;min-width:0;padding:18px;
  background:var(--fg-card);border:1px solid var(--fg-border);border-radius:18px}
.fg-home-intro strong{color:var(--fg-text);font-size:15px}
.fg-home-intro span{color:var(--fg-muted);line-height:1.45;font-size:12px}
.recent{text-align:left;box-shadow:none;border:1px solid var(--fg-border);border-radius:14px}
.bar{min-height:62px}
.brand #status{font-weight:450}
.work{height:calc(100dvh - 64px);background:var(--fg-app-bg);min-height:0}
#editor.fg-reader-host{
  display:flex!important;flex-direction:column;
  overflow:hidden!important;min-width:0;min-height:0;
  width:100%;max-width:100%;flex:1;background:var(--fg-app-bg)
}
.fg-reader-toolbar{
  display:flex;flex-wrap:wrap;align-items:center;column-gap:10px;row-gap:7px;
  flex:0 0 auto;padding:9px 15px;
  background:var(--fg-card);border-bottom:1px solid var(--fg-border);min-width:0;
}
.fg-reader-kind{
  color:#fff;background:#586bd5;border-radius:6px;padding:4px 7px;
  letter-spacing:.07em;font-size:10px;font-weight:850;white-space:nowrap;
}
.fg-reader-title{
  min-width:0;max-width:min(50vw,440px);font-size:13px;font-weight:750;
  color:var(--fg-text);overflow:hidden;text-overflow:ellipsis;white-space:nowrap
}
.fg-reader-desc{flex:1 1 160px;min-width:0;font-size:11px;color:var(--fg-muted)}
.fg-reader-tools{display:flex;align-items:center;gap:5px;flex:0 0 auto;max-width:100%;flex-wrap:wrap}
.fg-reader-button{
  display:inline-grid;place-items:center;min-height:37px;min-width:37px;
  border:1px solid var(--fg-border);border-radius:9px;padding:7px 11px;
  background:var(--fg-elevated);color:var(--fg-text);font-size:13px;font-weight:650;
}
.fg-reader-button:disabled{opacity:.3}
.fg-reader-counter{font-size:11px;color:var(--fg-muted);font-variant-numeric:tabular-nums;padding:0 5px}
.fg-reader-scroll{
  flex:1;min-height:0;min-width:0;width:100%;max-width:100%;overflow:auto;
  padding:clamp(12px,3vw,28px) 10px calc(60px + env(safe-area-inset-bottom));
  overscroll-behavior:contain;-webkit-overflow-scrolling:touch;
}
.fg-page{
  color:var(--fg-paper-text);width:min(100%,840px);
  margin:0 auto 24px;padding:clamp(24px,5vw,60px);
  border:1px solid var(--fg-reader-border);border-radius:3px;
  background:var(--fg-paper);box-shadow:0 12px 40px rgba(16,25,45,.11);
}
.fg-document-sheet{
  min-height:min(76vh,920px);line-height:1.75;
  font-size:calc(16px * var(--fg-size,1));overflow-wrap:anywhere;
  -webkit-hyphens:auto;hyphens:auto
}
.fg-document-h1{
  font-size:1.7em;font-weight:800;line-height:1.22;letter-spacing:-.026em;
  margin:0 0 1.3em;color:var(--fg-paper-text)
}
.fg-document-h2{
  margin:1.4em 0 .75em;font-size:1.23em;line-height:1.38;letter-spacing:-.017em;
  color:var(--fg-paper-text);font-weight:770
}
.fg-document-p{margin:0 0 .65em;white-space:pre-wrap;line-height:1.7}
.fg-document-bullet{margin:0 0 .55em;padding-left:1.4em;text-indent:-1em;line-height:1.65}
.fg-paragraph-break{height:.55em}
.fg-document-code{
  background:color-mix(in srgb,var(--fg-paper-text) 5%,var(--fg-paper));
  color:var(--fg-paper-text);border:1px solid var(--fg-reader-border);
  border-radius:12px;padding:16px;max-width:100%;overflow:auto;
  font:400 .84em/1.65 ui-monospace,SFMono-Regular,Consolas,monospace;
  white-space:pre-wrap;tab-size:4;word-break:break-word
}
.fg-pdf-sheet{padding:0;overflow:hidden;width:fit-content;max-width:100%;border:0;background:#fff}
.fg-pdf-img{display:block;max-width:100%;height:auto}
.fg-image-surface{display:flex;justify-content:center}
.fg-display-image{height:max-content;max-height:none;object-fit:contain;border-radius:4px;box-shadow:0 10px 34px #0002}
.fg-archive-sheet{min-height:55vh}
.fg-archive-img{max-width:100%;display:block;margin:20px auto;height:auto;object-fit:contain}
.fg-entry-select{
  max-width:min(75vw,250px);min-height:37px;padding:6px 8px;
  border:1px solid var(--fg-reader-border);border-radius:9px;
  background:var(--fg-elevated);color:var(--fg-text);
  white-space:nowrap;text-overflow:ellipsis;overflow:hidden
}
.fg-reader-empty{
  margin:35px auto;padding:22px 24px;max-width:650px;
  background:var(--fg-paper);border:1px dashed var(--fg-reader-border);
  border-radius:13px;color:var(--fg-reader-muted);line-height:1.6
}
@media(max-width:680px){
  .fg-home-intro{grid-template-columns:1fr}
  .home{padding:18px 12px 42px}
  .hero{border-radius:16px;padding:27px 23px}
  .hero h1{font-size:35px}
  .fg-reader-toolbar{padding:8px 10px;row-gap:8px}
  .fg-reader-desc{flex:1 0 100%}
  .fg-reader-tools{justify-content:flex-start}
  .fg-reader-scroll{padding:10px 6px calc(54px + env(safe-area-inset-bottom))}
  .fg-page{padding:25px 20px;box-shadow:0 6px 20px #0001;border-radius:2px}
  .fg-document-sheet{font-size:calc(15.5px * var(--fg-size,1));line-height:1.7}
  .bar .actions{gap:4px}
  .bar .actions button{padding:7px 8px;font-size:11.5px}
}
'''
    CSS.write_text(css)
CSS.write_text(CSS.read_text()+'''
.fg-docx-rich-block{line-height:1.7;color:var(--fg-paper-text)}
.fg-docx-rich-block p{margin:0 0 .75em;min-height:.35em;white-space:pre-wrap}
.fg-docx-rich-block h1{font-size:1.9em;margin:0 0 1em;line-height:1.26}
.fg-docx-rich-block h2{font-size:1.45em;margin:1.3em 0 .65em;line-height:1.3}
.fg-docx-rich-block h3{font-size:1.2em;margin:1.1em 0 .6em}
.fg-docx-rich-block h4{font-size:1.1em;margin:1em 0 .6em}
.fg-docx-rich-block img{display:block;max-width:100%;height:auto;margin:1em auto}
.fg-docx-rich-block .fg-docx-quote{border-left:3px solid var(--fg-reader-accent);padding-left:1em;font-style:italic}
''')
print("Universal reader web UI installed")
