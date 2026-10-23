from pathlib import Path
import re

root=Path("app/src/main")
p=root/"java/com/openlocal/office/MainActivity.java"
s=p.read_text()
anchor='''                    BookArchive candidate=new BookArchive(this,uri,true);
                    bookArchive=candidate;'''
assert s.count(anchor)==1
s=s.replace(anchor,'''                    BookArchive candidate=new BookArchive(this,uri,true);
                    android.util.Log.i("FG_EPUB","EPUB_READY chapters="+
                        candidate.chapterCount()+" images="+candidate.imageCount());
                    bookArchive=candidate;''',1)
p.write_text(s)
css=root/"assets/style.css"
css.write_text(css.read_text()+r"""

/* EPUB fix / library cover polish: no redundant error overlays in the book UI */
.fg-lib-cover-image{object-fit:cover;object-position:50% 20%;display:block;
 background:transparent;image-rendering:auto}
.fg-lib-cover.fg-lib-has-image .fg-lib-fallback{display:none!important}
.fg-book .fg-book-article{overflow-wrap:break-word;word-break:normal}
""")
gradle=Path("app/build.gradle.kts")
s=gradle.read_text()
s,n=re.subn(r'versionCode\s*=\s*(\d+)',
    lambda m:'versionCode = '+str(int(m.group(1))+1),s,count=1)
assert n==1
s,n=re.subn(r'versionName\s*=\s*"[^"]+"',
    'versionName = "0.13.1"',s,count=1)
assert n==1
gradle.write_text(s)
print("v0.13.1 EPUB instrumentation, preview UI and safe upgrade version assigned")
