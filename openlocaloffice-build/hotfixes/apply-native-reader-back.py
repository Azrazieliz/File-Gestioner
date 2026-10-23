from pathlib import Path
p=Path("app/src/main/java/com/openlocal/office/MainActivity.java")
s=p.read_text()
anchor="    private boolean pageReady;"
assert s.count(anchor)==1
s=s.replace(anchor,'''    private volatile long lastBackAt=0L;
    private android.window.OnBackInvokedCallback predictiveBackCallback;
'''+anchor,1)
anchor='''        setContentView(web);
        String libraryValue='''
assert s.count(anchor)==1
s=s.replace(anchor,'''        setContentView(web);
        if(android.os.Build.VERSION.SDK_INT>=33){
            predictiveBackCallback=()->navigateBackToReader();
            getOnBackInvokedDispatcher().registerOnBackInvokedCallback(
                android.window.OnBackInvokedDispatcher.PRIORITY_DEFAULT,
                predictiveBackCallback);
        }
        String libraryValue=''',1)
anchor="    @Override public void onDestroy() {"
assert s.count(anchor)==1
s=s.replace(anchor,'''    private void navigateBackToReader(){
        if(web!=null&&pageReady){
            web.evaluateJavascript(
                "window.FileGestionerNavigation?.back()",null);
        }else{
            exitAfterBack();
        }
    }
    private void exitAfterBack(){
        long now=android.os.SystemClock.elapsedRealtime();
        if(now-lastBackAt<2100L) {
            finish();
            return;
        }
        lastBackAt=now;
        android.widget.Toast.makeText(this,
            "Press Back again to exit",android.widget.Toast.LENGTH_SHORT).show();
    }
    @Override public void onBackPressed(){navigateBackToReader();}
'''+anchor,1)
anchor='''        io.shutdownNow();
        closeBook();'''
assert s.count(anchor)==1
s=s.replace(anchor,'''        if(android.os.Build.VERSION.SDK_INT>=33&&predictiveBackCallback!=null){
            getOnBackInvokedDispatcher().unregisterOnBackInvokedCallback(predictiveBackCallback);
        }
        io.shutdownNow();
        closeBook();''',1)
anchor='''        @JavascriptInterface public void pickLibraryFolder(){'''
assert s.count(anchor)==1
s=s.replace(anchor,'''        @JavascriptInterface public void exitFromLibraryRoot(){
            runOnUiThread(()->exitAfterBack());
        }
'''+anchor,1)
p.write_text(s)
print("Android system Back and predictive back now navigate in-app, only root double-back exits")
