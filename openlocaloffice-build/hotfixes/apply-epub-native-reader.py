from pathlib import Path

root=Path("app/src/main")
main=root/"java/com/openlocal/office/MainActivity.java"
source=main.read_text()
anchor='    private byte[] rawDocument;'
assert source.count(anchor)==1
source=source.replace(anchor,anchor+'''
    private volatile BookArchive bookArchive;
''',1)
anchor='            @Override public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {'
assert source.count(anchor)==1
source=source.replace(anchor,'''            @Override public WebResourceResponse shouldInterceptRequest(
                    WebView view, WebResourceRequest request) {
                Uri u=request.getUrl();
                if("https".equals(u.getScheme())&&"fg-assets.invalid".equals(u.getHost())){
                    BookArchive active=bookArchive;
                    try {
                        if(active!=null){
                            WebResourceResponse response=active.response(u.getEncodedPath());
                            if(response!=null)return response;
                        }
                    }catch(Exception ignored){}
                    return new WebResourceResponse("text/plain","UTF-8",
                        new ByteArrayInputStream(new byte[0]));
                }
                return super.shouldInterceptRequest(view,request);
            }
'''+anchor,1)
anchor='    @Override public void onDestroy() {'
assert source.count(anchor)==1
source=source.replace(anchor,'''    private void closeBook() {
        BookArchive previous=bookArchive;
        bookArchive=null;
        if(previous!=null)try{previous.close();}catch(Exception ignored){}
    }
'''+anchor,1)
source=source.replace('''        io.shutdownNow();
        if (web != null) web.destroy();''','''        io.shutdownNow();
        closeBook();
        if (web != null) web.destroy();''',1)
anchor='''                if ("pdf".equals(quickType)) {'''
assert source.count(anchor)==1
source=source.replace(anchor,'''                // EPUB is a genuine spine-based ebook, not flattened ZIP text.
                // Read metadata and chapters from a seekable fd or bounded disk
                // spool. This path intentionally bypasses the editor's 80 MiB
                // heap limit, including for multi-GiB archives.
                if ("epub".equals(quickType)) {
                    closeBook();
                    BookArchive candidate=new BookArchive(this,uri,true);
                    android.util.Log.i("FG_BOOK","EPUB_READY chapters="+
                        candidate.chapterCount()+" illustrations="+candidate.imageCount());
                    bookArchive=candidate;
                    xlsx=null;csv=null;docx=null;sdocx=null;
                    textDocument=null;rawDocument=null;
                    currentUri=uri;currentName=name;currentType="epub";
                    currentMime="application/epub+zip";
                    remember(uri,name,currentMime);
                    org.json.JSONObject bookJson=candidate.metadata();
                    bookJson.put("name",name).put("readOnly",true);
                    String payload=bookJson.toString();
                    runOnUiThread(()->js("window.loadDocument("+payload+")"));
                    return;
                }
'''+anchor,1)
anchor='''        @JavascriptInterface public int getDocxRichBlockCount() {'''
assert source.count(anchor)==1
source=source.replace(anchor,r'''        @JavascriptInterface public String getBookContents(){
            BookArchive active=bookArchive;
            if(active==null)return "[]";
            try{return active.contents().toString();}
            catch(Exception ignored){return "[]";}
        }
        @JavascriptInterface public String getBookChapter(int index){
            BookArchive active=bookArchive;
            if(active==null)return "{}";
            try{return active.chapter(index).toString();}
            catch(Exception e){
                return "{\"error\":"+UniversalReader.quote(message(e))+"}";
            }
        }
        @JavascriptInterface public String getBookImages(){
            BookArchive active=bookArchive;
            if(active==null)return "[]";
            try{return active.images().toString();}
            catch(Exception ignored){return "[]";}
        }
        @JavascriptInterface public String getBookImageUrl(int index){
            BookArchive active=bookArchive;
            if(active==null)return "";
            try{return active.archiveEntry(index);}
            catch(Exception ignored){return "";}
        }
'''+anchor,1)
main.write_text(source)
print("EPUB streaming native route, image URL interception and spine/chapter bridge inserted")
