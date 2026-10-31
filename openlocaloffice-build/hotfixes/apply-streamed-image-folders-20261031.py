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
        openFolderImages(uriText,null);
    }
    private void openImageInFolder(String folderId,String selectedUri){
        if(libraryTree==null||selectedUri==null)return;
        // File URI must have been exposed by our selected collection.
        if(!allowedLibraryUris.contains(selectedUri)){
            runOnUiThread(()->js("window.FileGestionerLibrary?.error("+
                q("This image is no longer in the current collection")+")"));
            return;
        }
        String id=(folderId==null||folderId.isEmpty())?
            android.provider.DocumentsContract.getTreeDocumentId(libraryTree):folderId;
        Uri parent=android.provider.DocumentsContract.buildDocumentUriUsingTree(libraryTree,id);
        openFolderImages(parent.toString(),selectedUri);
    }
    private void openFolderImages(String uriText,String selectedUri){
        if(uriText==null||libraryTree==null)return;
        final Uri directory=Uri.parse(uriText);
        // Opening a subfolder must not depend on the current scan's transient
        // allowedLibraryUris set: it is cleared when the library refreshes.
        // Validate against the persistently granted SAF tree instead.
        try{
            if(!"content".equals(directory.getScheme())||
               !libraryTree.getAuthority().equals(directory.getAuthority())||
               !android.provider.DocumentsContract.getTreeDocumentId(libraryTree)
                   .equals(android.provider.DocumentsContract.getTreeDocumentId(directory)))
                throw new SecurityException("Folder is outside the selected library");
        }catch(Exception invalid){
            runOnUiThread(()->js("window.FileGestionerLibrary?.error("+
                q("Cannot open image folder: "+message(invalid))+")"));
            return;
        }
        final long request=fgFolderVersion.incrementAndGet();
        final String token=java.util.UUID.randomUUID().toString();
        fgFolderToken=token;
        // Selected file opens immediately even if remote listing takes time.
        final Uri selected=selectedUri==null?null:Uri.parse(selectedUri);
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
                                token+"/"+i)
                            .put("selected",selected!=null&&selected.equals(page.uri)));
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
                final String folderId=android.provider.DocumentsContract.getDocumentId(directory);
                // Build children through the actual persisted tree grant, not
                // a child URI that some cloud providers cannot authorize.
                Uri children=android.provider.DocumentsContract.buildChildDocumentsUriUsingTree(
                    libraryTree,folderId);
                String[] cols={
                    android.provider.DocumentsContract.Document.COLUMN_DOCUMENT_ID,
                    android.provider.DocumentsContract.Document.COLUMN_DISPLAY_NAME,
                    android.provider.DocumentsContract.Document.COLUMN_MIME_TYPE};
                // A cloud SAF provider can take time to enumerate 40k files.
                // Emit the first 64 rows immediately; do not wait for the end.
                java.util.List<FolderPage> batch=new java.util.ArrayList<>(64);
                long startMillis=android.os.SystemClock.elapsedRealtime();
                android.database.Cursor result=null;
                try{
                    try{
                        result=getContentResolver().query(children,cols,null,null,null);
                    }catch(Exception treeError){
                        android.util.Log.w("FG_FOLDER","Cloud tree query failed; trying document URI",treeError);
                    }
                    if(result==null){
                        Uri fallback=android.provider.DocumentsContract.buildChildDocumentsUri(
                            directory.getAuthority(),folderId);
                        result=getContentResolver().query(fallback,cols,null,null,null);
                    }
                    if(result==null)throw new java.io.IOException("Folder provider did not return images");
                    try(android.database.Cursor cursor=result){
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
                        Uri file=android.provider.DocumentsContract.buildDocumentUriUsingTree(
                            libraryTree,id);
                        batch.add(new FolderPage(file,name));
                        if(batch.size()>=64){
                            flush.accept(batch);
                            batch=new java.util.ArrayList<>(64);
                        }
                    }
                    }
                }catch(SecurityException permission){
                    throw new java.io.IOException("Round Sync folder permission denied: "+
                        permission.getMessage(),permission);
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
                android.util.Log.e("FG_FOLDER","FOLDER_STREAM_FAILED provider="+
                    directory.getAuthority(),e);
                if(request==fgFolderVersion.get())
                    runOnUiThread(()->{
                        js("window.FileGestionerFolder?.failed("+q(message(e))+")");
                        js("window.FileGestionerLibrary?.error("+
                            q("Cannot browse image folder: "+message(e))+")");
                    });
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
                                    InputStream input=null;
                                    try{
                                        input=getContentResolver().openInputStream(page.uri);
                                    }catch(Exception first){
                                        android.util.Log.w("FG_FOLDER",
                                            "SAF openInputStream failed; retrying file descriptor",first);
                                        android.os.ParcelFileDescriptor descriptor=
                                            getContentResolver().openFileDescriptor(page.uri,"r");
                                        if(descriptor!=null)
                                            input=new android.os.ParcelFileDescriptor.AutoCloseInputStream(descriptor);
                                    }
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
# Add a bridge method without breaking older openImageFolder callers.
bridge='''        @JavascriptInterface public void openImageFolder(String uri){
             MainActivity.this.openFolderImages(uri);
        }
'''
assert s.count(bridge)==1
s=s.replace(bridge,bridge+'''        @JavascriptInterface public void openImageInFolder(String folder,String selected){
            MainActivity.this.openImageInFolder(folder,selected);
        }
''',1)
main.write_text(s)
print("SAF image folders: Round Sync tree access, sequential navigation and resilient image streams")
