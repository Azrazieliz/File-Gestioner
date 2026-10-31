#!/usr/bin/env python3
"""Open massive SAF image directories progressively, without a 20k cap."""
from pathlib import Path
root=Path("app/src/main")
main=root/"java/com/openlocal/office/MainActivity.java"
s=main.read_text()
start=s.index("    private void openFolderImages(String uriText){")
end=s.index("    private void openUri(Uri uri) {",start)
assert 2800<end-start<11000
replacement=r'''    private final java.util.concurrent.ConcurrentHashMap<Integer,FolderPage>
        fgFolderPageMap=new java.util.concurrent.ConcurrentHashMap<>();
    private final java.util.concurrent.atomic.AtomicLong fgFolderVersion=
        new java.util.concurrent.atomic.AtomicLong();
    private void openFolderImages(String uriText){
        if(uriText==null||libraryTree==null)return;
        final Uri directory=Uri.parse(uriText);
        // Opening a subfolder must not depend on the current scan's transient
        // allowedLibraryUris set: it is cleared when the library refreshes.
        // Validate against the persistently granted SAF tree instead.
        try{
            if(!"content".equals(directory.getScheme())||
               !libraryTree.getAuthority().equals(directory.getAuthority())||
               !android.provider.DocumentsContract.getTreeDocumentId(libraryTree)
                   .equals(android.provider.DocumentsContract.getTreeDocumentId(directory))||
               !android.provider.DocumentsContract.isDocumentUri(this,directory))
                throw new SecurityException("Folder is outside the selected library");
        }catch(Exception invalid){
            runOnUiThread(()->js("window.FileGestionerLibrary?.error("+
                q("Cannot open image folder: "+message(invalid))+")"));
            return;
        }
        final long request=fgFolderVersion.incrementAndGet();
        final String token=java.util.UUID.randomUUID().toString();
        fgFolderToken=token;
        fgFolderPageMap.clear();
        fgDirectoryExecutor.execute(()->{
            final java.util.concurrent.atomic.AtomicInteger pageIndex=
                new java.util.concurrent.atomic.AtomicInteger();
            final java.util.concurrent.atomic.AtomicBoolean started=
                new java.util.concurrent.atomic.AtomicBoolean();
            final java.util.function.Consumer<java.util.List<FolderPage>> flush=(batch)->{
                if(request!=fgFolderVersion.get()||batch.isEmpty())return;
                try{
                    batch.sort((x,y)->com.openlocal.office.core.ReaderLibrary.naturalCompare(
                        x.name,y.name));
                    org.json.JSONArray images=new org.json.JSONArray();
                    for(FolderPage page:batch){
                        int i=pageIndex.getAndIncrement();
                        fgFolderPageMap.put(i,page);
                        images.put(new org.json.JSONObject().put("name",page.name)
                            .put("url","https://fg-assets.invalid/folder-img/"+
                                token+"/"+i));
                    }
                    if(!started.getAndSet(true)){
                        final String payload=new org.json.JSONObject()
                            .put("type","folderImages").put("name","Image folder")
                            .put("pages",images).toString();
                        runOnUiThread(()->{
                            if(request==fgFolderVersion.get())
                                js("window.loadDocument("+payload+")");
                        });
                    }else{
                        final String payload=new org.json.JSONObject()
                            .put("pages",images).toString();
                        runOnUiThread(()->{
                            if(request==fgFolderVersion.get())
                                js("window.FileGestionerFolder?.append("+payload+")");
                        });
                    }
                }catch(Exception e){android.util.Log.w("FG_FOLDER","Batch failed",e);}
            };
            try{
                Uri children=android.provider.DocumentsContract.buildChildDocumentsUriUsingTree(
                    directory,android.provider.DocumentsContract.getDocumentId(directory));
                String[] cols={
                    android.provider.DocumentsContract.Document.COLUMN_DOCUMENT_ID,
                    android.provider.DocumentsContract.Document.COLUMN_DISPLAY_NAME,
                    android.provider.DocumentsContract.Document.COLUMN_MIME_TYPE};
                // A cloud SAF provider can take time to enumerate 40k files.
                // Emit the first 64 rows immediately; do not wait for the end.
                java.util.List<FolderPage> batch=new java.util.ArrayList<>(64);
                long startMillis=android.os.SystemClock.elapsedRealtime();
                try(android.database.Cursor cursor=getContentResolver().query(
                    children,cols,null,null,null)){
                    if(cursor==null)throw new java.io.IOException("Folder unavailable");
                    while(cursor.moveToNext()){
                        if(request!=fgFolderVersion.get())return;
                        String id=cursor.getString(0),name=cursor.getString(1),
                            mime=cursor.getString(2);
                        if(id==null||name==null||name.startsWith("."))continue;
                        String lower=name.toLowerCase(java.util.Locale.ROOT);
                        if(!(lower.endsWith(".png")||lower.endsWith(".jpg")||
                             lower.endsWith(".jpeg")||lower.endsWith(".webp")||
                             lower.endsWith(".gif")||lower.endsWith(".avif")))continue;
                        if(android.provider.DocumentsContract.Document.MIME_TYPE_DIR
                            .equals(mime))continue;
                        batch.add(new FolderPage(
                            android.provider.DocumentsContract.buildDocumentUriUsingTree(
                                directory,id),name));
                        if(batch.size()>=64){
                            flush.accept(batch);
                            batch=new java.util.ArrayList<>(64);
                        }
                    }
                }
                flush.accept(batch);
                if(!started.get()){
                    runOnUiThread(()->{
                        if(request==fgFolderVersion.get())
                            js("window.FileGestionerLibrary?.enterFolder("+
                                q(android.provider.DocumentsContract.getDocumentId(directory))+")");
                    });
                }else{
                    final int total=pageIndex.get();
                    runOnUiThread(()->{
                        if(request==fgFolderVersion.get())
                            js("window.FileGestionerFolder?.done("+total+")");
                    });
                }
                android.util.Log.i("FG_FOLDER","FOLDER_STREAM_COMPLETE pages="+
                    pageIndex.get()+" millis="+
                    (android.os.SystemClock.elapsedRealtime()-startMillis));
            }catch(Exception e){
                android.util.Log.e("FG_FOLDER","FOLDER_STREAM_FAILED",e);
                if(request==fgFolderVersion.get())
                    runOnUiThread(()->js("window.FileGestionerLibrary?.error("+
                        q("Image folder error: "+message(e))+")"));
            }
        });
    }
'''
s=s[:start]+replacement+s[end:]
start=s.index('                    if(assetPath!=null&&assetPath.startsWith("/folder-img/")){')
end=s.index('                    if(assetPath!=null&&assetPath.startsWith("/cover/")){',start)
old=s[start:end]
assert 'fgFolderUris' in old
new=r'''                    if(assetPath!=null&&assetPath.startsWith("/folder-img/")){
                        String[] part=assetPath.split("/");
                        if(part.length==4&&part[2].equals(fgFolderToken)){
                            try{
                                int index=Integer.parseInt(part[3]);
                                FolderPage page=fgFolderPageMap.get(index);
                                if(page!=null){
                                    String lower=page.name.toLowerCase(java.util.Locale.ROOT);
                                    String mime=lower.endsWith(".png")?"image/png":
                                        lower.endsWith(".webp")?"image/webp":
                                        lower.endsWith(".gif")?"image/gif":
                                        lower.endsWith(".avif")?"image/avif":"image/jpeg";
                                    InputStream input=getContentResolver().openInputStream(page.uri);
                                    if(input!=null)return new WebResourceResponse(mime,null,input);
                                }
                            }catch(Exception e){
                                android.util.Log.w("FG_FOLDER","Failed image fetch",e);
                            }
                        }
                        return new WebResourceResponse("image/jpeg",null,
                            new ByteArrayInputStream(new byte[0]));
                    }
'''
s=s[:start]+new+s[end:]
main.write_text(s)
print("Image folder progressively streams batches of 64 pages, no 20k limit, concurrent demand decoding")
