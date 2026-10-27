#!/usr/bin/env python3
"""Progressive comic pages: each decoded ZIP entry becomes readable immediately."""
from pathlib import Path
root=Path("app/src/main")
main=root/"java/com/openlocal/office/MainActivity.java"
s=main.read_text()
a="""    private volatile byte[] fgEarlyPage;
    private volatile String fgEarlyToken;
    private volatile String fgEarlyMime="image/jpeg";
"""
assert s.count(a)==1, "Old one-page state changed"
s=s.replace(a,"""    private volatile String fgEarlyToken;
    private final java.util.concurrent.ConcurrentHashMap<Integer,java.io.File>
        fgEarlyPages=new java.util.concurrent.ConcurrentHashMap<>();
    private final java.util.concurrent.ConcurrentHashMap<Integer,String>
        fgEarlyMimes=new java.util.concurrent.ConcurrentHashMap<>();
""",1)
a="""                    if(assetPath!=null&&assetPath.startsWith("/early/")&&
                       assetPath.substring("/early/".length()).equals(fgEarlyToken)&&
                       fgEarlyPage!=null){
                        return new WebResourceResponse(fgEarlyMime,null,
                            new ByteArrayInputStream(fgEarlyPage));
                    }"""
assert s.count(a)==1, "Old one-page WebView resource changed"
s=s.replace(a,"""                    if(assetPath!=null&&assetPath.startsWith("/early/")){
                        String suffix=assetPath.substring("/early/".length());
                        int split=suffix.indexOf('/');
                        if(split>0&&suffix.substring(0,split).equals(fgEarlyToken)){
                            try {
                                int index=Integer.parseInt(suffix.substring(split+1));
                                java.io.File page=fgEarlyPages.get(index);
                                if(page!=null&&page.isFile()){
                                    return new WebResourceResponse(
                                        fgEarlyMimes.getOrDefault(index,"image/jpeg"),null,
                                        new FileInputStream(page));
                                }
                            }catch(Exception ignored){}
                        }
                        return new WebResourceResponse("image/jpeg",null,
                            new ByteArrayInputStream(new byte[0]));
                    }""",1)
a="""BookArchive candidate=new BookArchive(this,uri,false,
                        new RemoteBookSpool.PreviewListener(){
                            public void onFirstPage(String filename,byte[] image){
                                if(image==null||image.length==0)return;
                                fgEarlyPage=image;
                                fgEarlyToken=java.util.UUID.randomUUID().toString();
                                String l=filename.toLowerCase(java.util.Locale.ROOT);
                                fgEarlyMime=l.endsWith(".webp")?"image/webp":
                                    l.endsWith(".png")?"image/png":"image/jpeg";
                                String u="https://fg-assets.invalid/early/"+fgEarlyToken;
                                runOnUiThread(()->js("window.FileGestionerEarly?.show("+
                                    q(u)+","+q(filename)+")"));
                                android.util.Log.i("FG_PERF","EARLY_PAGE_READY bytes="+image.length);
                            }
                            public void onProgress(long downloaded,long expected){
                                runOnUiThread(()->js("window.FileGestionerEarly?.progress("+
                                    downloaded+","+expected+")"));
                            }
                        });"""
assert s.count(a)==1, "Old preview listener changed"
new="""final String progressiveSession=java.util.UUID.randomUUID().toString();
                    fgEarlyToken=progressiveSession;
                    fgEarlyPages.clear();
                    fgEarlyMimes.clear();
                    final java.util.concurrent.atomic.AtomicInteger progressiveIndex=
                        new java.util.concurrent.atomic.AtomicInteger();
                    final java.io.File progressDir=new java.io.File(getCacheDir(),
                        "progress-"+progressiveSession);
                    BookArchive candidate=new BookArchive(this,uri,false,
                        new RemoteBookSpool.PreviewListener(){
                            public void onFirstPage(String filename,byte[] image){
                                onPage(filename,image);
                            }
                            public void onPage(String filename,byte[] image){
                                if(image==null||image.length<100||
                                   !progressiveSession.equals(fgEarlyToken))return;
                                try {
                                    if(!progressDir.exists()&&!progressDir.mkdirs())
                                        return;
                                    int index=progressiveIndex.getAndIncrement();
                                    java.io.File file=new java.io.File(progressDir,index+".image");
                                    try(FileOutputStream out=new FileOutputStream(file)){
                                        out.write(image);
                                    }
                                    fgEarlyPages.put(index,file);
                                    String lower=filename.toLowerCase(java.util.Locale.ROOT);
                                    fgEarlyMimes.put(index,lower.endsWith(".png")?"image/png":
                                        lower.endsWith(".webp")?"image/webp":"image/jpeg");
                                    String url="https://fg-assets.invalid/early/"+
                                        progressiveSession+"/"+index;
                                    runOnUiThread(()->{
                                        if(progressiveSession.equals(fgEarlyToken))
                                            js("window.FileGestionerEarly?.append("+
                                                q(url)+","+q(filename)+","+index+")");
                                    });
                                    android.util.Log.i("FG_PERF","PAGE_READABLE index="+
                                        (index+1)+" bytes="+image.length);
                                }catch(Exception e){
                                    android.util.Log.w("FG_PERF","Progress page not saved",e);
                                }
                            }
                            public void onProgress(long downloaded,long expected){
                                runOnUiThread(()->{
                                    if(progressiveSession.equals(fgEarlyToken))
                                        js("window.FileGestionerEarly?.progress("+
                                            downloaded+","+expected+")");
                                });
                            }
                        });"""
s=s.replace(a,new,1)
main.write_text(s)
html=root/"assets/index.html"
s=html.read_text()
assert "</body>" in s
s=s.replace("</body>",'<script src="fg-early-page.js"></script>\n</body>')
html.write_text(s)
print("Progressive ZIP reading: one provider stream, pages 1..N available as completed")
