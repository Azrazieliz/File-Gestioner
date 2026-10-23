from pathlib import Path
import re

main=Path("app/src/main/java/com/openlocal/office/MainActivity.java")
java=main.read_text()
# The app uses a WebView. Predictive/system Back cannot simply finish the
# Activity while a document, book drawer or collection child is visible.
method='''    @Override public void onBackPressed() {
        if(web==null){
            super.onBackPressed();
            return;
        }
        web.evaluateJavascript(
            "(function(){try{return !!(window.FileGestionerLibrary && " +
            "window.FileGestionerLibrary.handleBack && " +
            "window.FileGestionerLibrary.handleBack());}catch(e){return false;}})()",
            handled -> {
                if(!"true".equals(handled)){
                    // At the library root, Android may perform its normal Back.
                    finish();
                }
            });
    }
'''
if re.search(r'\bvoid\s+onBackPressed\s*\(',java):
    match=re.search(r'(?m)^[ \t]*@Override\s+public\s+void\s+onBackPressed\s*\([^)]*\)\s*\{',java)
    if not match:
        match=re.search(r'(?m)^[ \t]*public\s+void\s+onBackPressed\s*\([^)]*\)\s*\{',java)
    assert match is not None,"Existing Back override could not be found safely"
    idx=match.end();level=1
    while idx<len(java) and level:
        if java[idx]=='{':level+=1
        elif java[idx]=='}':level-=1
        idx+=1
    java=java[:match.start()]+method+java[idx:]
else:
    anchor="    @Override public void onDestroy() {"
    assert java.count(anchor)==1,"Could not locate Activity lifetime anchor"
    java=java.replace(anchor,method+anchor,1)
main.write_text(java)
gradle=Path("app/build.gradle.kts")
version=gradle.read_text()
version,n=re.subn(r'versionCode\s*=\s*(\d+)',
    lambda match:"versionCode = "+str(int(match.group(1))+1),version,count=1)
assert n==1,"Missing Android versionCode"
version,n=re.subn(r'versionName\s*=\s*"[^"]+"',
    'versionName = "0.13.1"',version,count=1)
assert n==1,"Missing Android versionName"
gradle.write_text(version)
print("File Gestioner v0.13.1 — fixed EPUB, covers and Android Back")

