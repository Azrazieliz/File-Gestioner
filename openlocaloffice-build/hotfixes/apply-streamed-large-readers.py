from pathlib import Path

root=Path("app/src/main")
main=root/"java/com/openlocal/office/MainActivity.java"
source=main.read_text()
def once(old,new):
    global source
    assert source.count(old)==1,"Missing unique MainActivity anchor: "+old[:90]
    source=source.replace(old,new,1)

once('    private volatile BookArchive bookArchive;',
'''    private volatile BookArchive bookArchive;
    private StreamedText textStream;
    private String imageStreamToken;''')
once('    private void closeBook() {',
'''    private void closeTextStream() {
        StreamedText previous=textStream;
        textStream=null;
        if(previous!=null)try{previous.close();}catch(Exception ignored){}
    }
    private void closeBook() {''')
once('''        closeBook();
        if (web != null) web.destroy();''',
'''        closeBook();
        closeTextStream();
        if (web != null) web.destroy();''')
once('''                String quickType = detectType(uri, name);''',
'''                String quickType = detectType(uri, name);
                closeBook();
                closeTextStream();
                imageStreamToken=null;''')
once('''                    BookArchive active=bookArchive;
                    try {''',
'''                    String assetPath=u.getPath();
                    if(assetPath!=null&&imageStreamToken!=null&&
                        assetPath.equals("/raw/"+imageStreamToken+"/image")&&
                        currentUri!=null) {
                        try {
                            InputStream image=getContentResolver().openInputStream(currentUri);
                            if(image!=null)return new WebResourceResponse(currentMime,null,image);
                        }catch(Exception ignored){}
                        return new WebResourceResponse("text/plain","UTF-8",
                            new ByteArrayInputStream(new byte[0]));
                    }
                    BookArchive active=bookArchive;
                    try {''')
once('''                if ("epub".equals(quickType)) {''',r'''                if ("cbz".equals(quickType)||"zip".equals(quickType)) {
                    BookArchive candidate=new BookArchive(this,uri,false);
                    bookArchive=candidate;
                    xlsx=null;csv=null;docx=null;sdocx=null;
                    textDocument=null;rawDocument=null;
                    currentUri=uri;currentName=name;currentType=quickType;
                    currentMime="application/zip";
                    remember(uri,name,currentMime);
                    String payload="{\"type\":\"archive\",\"name\":"+q(name)+
                        ",\"format\":"+q(quickType)+
                        ",\"streamed\":true,\"comicMode\":"+candidate.comicLike()+
                        ",\"readOnly\":true}";
                    runOnUiThread(()->js("window.loadDocument("+payload+")"));
                    return;
                }
                if(isImageType(quickType)) {
                    xlsx=null;csv=null;docx=null;sdocx=null;
                    textDocument=null;rawDocument=null;
                    currentUri=uri;currentName=name;currentType=quickType;
                    currentMime=mimeForPreview(quickType);
                    imageStreamToken=java.util.UUID.randomUUID().toString();
                    remember(uri,name,currentMime);
                    String url="https://fg-assets.invalid/raw/"+imageStreamToken+"/image";
                    String payload="{\"type\":\"image\",\"name\":"+q(name)+
                        ",\"format\":"+q(quickType)+
                        ",\"url\":"+q(url)+",\"streamed\":true,\"readOnly\":true}";
                    runOnUiThread(()->js("window.loadDocument("+payload+")"));
                    return;
                }
                long quickSize=displaySize(uri);
                if ((quickSize>MAX_FILE_BYTES||quickSize<0) &&
                    (isTextType(quickType)||Arrays.asList("txt","md","markdown").contains(quickType))) {
                    textStream=new StreamedText(this,uri);
                    xlsx=null;csv=null;docx=null;sdocx=null;
                    textDocument=null;rawDocument=null;
                    currentUri=uri;currentName=name;currentType=quickType;
                    currentMime="text/plain";
                    remember(uri,name,currentMime);
                    String payload="{\"type\":\"streamText\",\"name\":"+q(name)+
                        ",\"format\":"+q(quickType)+
                        ",\"streamed\":true,\"readOnly\":true}";
                    runOnUiThread(()->js("window.loadDocument("+payload+")"));
                    return;
                }
                if ("epub".equals(quickType)) {''')
once('''        @JavascriptInterface public String getBookContents(){''',r'''        @JavascriptInterface public String nextTextChunk(int chars){
            StreamedText active=textStream;
            if(active==null)return "{\"text\":\"\",\"end\":true}";
            try{return active.nextJson(chars);}
            catch(Exception ignored){return "{\"text\":\"\",\"end\":true}";}
        }
        @JavascriptInterface public String getArchiveImageUrl(String name){
            BookArchive active=bookArchive;
            if(active==null||!("zip".equals(currentType)||"cbz".equals(currentType)))return "";
            return active.urlForEntry(name);
        }
        @JavascriptInterface public String getBookContents(){''')
once('''            try {return rawDocument==null?"[]":UniversalReader.archiveListJson(rawDocument);}''',
'''            try {
                if(bookArchive!=null&&("zip".equals(currentType)||"cbz".equals(currentType)))
                    return bookArchive.fileList().toString();
                return rawDocument==null?"[]":UniversalReader.archiveListJson(rawDocument);
            }''')
once('''            try {return rawDocument==null?"":UniversalReader.entryBase64(rawDocument,name);}''',
'''            try {
                if(bookArchive!=null&&("zip".equals(currentType)||"cbz".equals(currentType)))
                    return bookArchive.entryBase64(name);
                return rawDocument==null?"":UniversalReader.entryBase64(rawDocument,name);
            }''')
main.write_text(source)
print("Seekable large EPUB/CBZ/ZIP, direct image streams and chunked long text wired")
