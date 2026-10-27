#!/usr/bin/env python3
"""Display first comic page before slow Round Sync ZIP spool completes."""
from pathlib import Path
root=Path("app/src/main")
main=root/"java/com/openlocal/office/MainActivity.java"
s=main.read_text()
a="    private volatile Uri libraryTree;"
assert s.count(a)==1
s=s.replace(a,'''    private volatile byte[] fgEarlyPage;
    private volatile String fgEarlyToken;
    private volatile String fgEarlyMime="image/jpeg";
'''+a,1)
a="                    String assetPath=u.getPath();"
assert s.count(a)==1
s=s.replace(a,'''                    String assetPath=u.getPath();
                    if(assetPath!=null&&assetPath.startsWith("/early/")&&
                       assetPath.substring("/early/".length()).equals(fgEarlyToken)&&
                       fgEarlyPage!=null){
                        return new WebResourceResponse(fgEarlyMime,null,
                            new ByteArrayInputStream(fgEarlyPage));
                    }''',1)
a="BookArchive candidate=new BookArchive(this,uri,false);"
assert s.count(a)==1
s=s.replace(a,'''BookArchive candidate=new BookArchive(this,uri,false,
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
                        });''',1)
main.write_text(s)
html=root/"assets/index.html"
s=html.read_text()
assert "</body>" in s
s=s.replace("</body>",'<script src="fg-early-page.js"></script>\n</body>')
html.write_text(s)
print("Progressive first comic image integrated: exact same remote stream, no duplicate downloads")
