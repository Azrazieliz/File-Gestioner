package com.openlocal.office.core;

import android.content.Context;
import android.net.Uri;
import android.os.SystemClock;
import android.util.Log;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.Locale;
import java.util.concurrent.ConcurrentHashMap;

/** Reusable disk cache for SAF pipes. Each remote archive is downloaded once.
 * Only explicit book-opening requests invoke this class. Library thumbnails
 * never invoke it. No source file is modified.
 */
public final class RemoteBookSpool {
    private static final ConcurrentHashMap<String,Object> LOCKS=
        new ConcurrentHashMap<>();
    private RemoteBookSpool(){}

    private static String identity(Uri uri,long length) {
        try{
            MessageDigest digest=MessageDigest.getInstance("SHA-256");
            byte[] hash=digest.digest((uri.toString()+"|"+length)
                .getBytes(StandardCharsets.UTF_8));
            StringBuilder sb=new StringBuilder();
            for(byte b:hash)sb.append(String.format(Locale.ROOT,"%02x",b&255));
            return sb.toString();
        }catch(Exception e){
            throw new IllegalStateException("Cannot hash archive cache identity",e);
        }
    }
    /** Blocks concurrent requests for this exact source until a single complete
     * copy is available. Retains successful copies across reader sessions.
     */
    public static File obtain(Context ctx,Uri uri,long expected) throws IOException {
        String key=identity(uri,expected);
        Object lock=LOCKS.computeIfAbsent(key,k->new Object());
        synchronized(lock){
            File dir=new File(ctx.getCacheDir(),"reading-v2");
            if(!dir.exists()&&!dir.mkdirs())
                throw new IOException("Cannot create remote book cache");
            File ready=new File(dir,key+".zip");
            if(ready.isFile()&&ready.length()>0&&
                (expected<0||ready.length()==expected)){
                Log.i("FG_PERF","CLOUD_SPOOL_CACHE_HIT bytes="+ready.length());
                ready.setLastModified(System.currentTimeMillis());
                return ready;
            }
            if(ready.exists()&&!ready.delete())
                throw new IOException("Cannot discard incomplete remote book cache");
            File pending=new File(dir,key+".part");
            if(pending.exists()&&!pending.delete())
                throw new IOException("Cannot discard unfinished remote download");
            long start=SystemClock.elapsedRealtime(),copied=0;
            try(InputStream in=ctx.getContentResolver().openInputStream(uri);
                OutputStream out=new BufferedOutputStream(
                    new FileOutputStream(pending),128*1024)){
                if(in==null)throw new IOException("Document provider returned no stream");
                byte[] buffer=new byte[128*1024];
                int n;
                while((n=in.read(buffer))!=-1){
                    out.write(buffer,0,n);
                    copied+=n;
                }
            }catch(IOException e){
                pending.delete();
                throw e;
            }
            if(copied==0||(expected>0&&copied!=expected)){
                pending.delete();
                throw new IOException("Incomplete cloud archive: received "+copied+
                    " bytes, expected "+expected);
            }
            if(!pending.renameTo(ready)){
                pending.delete();
                throw new IOException("Cannot finalize remote book cache");
            }
            Log.i("FG_PERF","CLOUD_SPOOL_ms="+
                (SystemClock.elapsedRealtime()-start)+" bytes="+copied);
            return ready;
        }
    }
}
