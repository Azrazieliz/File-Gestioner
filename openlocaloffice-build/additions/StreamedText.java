package com.openlocal.office.core;

import android.content.Context;
import android.net.Uri;
import java.io.*;
import java.nio.charset.*;
/** Forward-only bounded text stream; file size can exceed Integer.MAX_VALUE.
 * Content is never loaded in a single byte[] or JavaScript string.
 */
public final class StreamedText implements Closeable {
    private final BufferedReader reader;
    private long characters;
    private boolean ended;
    public StreamedText(Context context,Uri uri) throws IOException {
        InputStream input=context.getContentResolver().openInputStream(uri);
        if(input==null)throw new IOException("The document provider cannot stream this text");
        reader=new BufferedReader(new InputStreamReader(input,StandardCharsets.UTF_8),64*1024);
    }
    public synchronized String nextJson(int requested) throws Exception{
        if(ended)return "{\"text\":\"\",\"end\":true}";
        int count=Math.max(1024,Math.min(65536,requested));
        char[] chars=new char[count];
        int n=reader.read(chars,0,count);
        if(n<0){ended=true;return "{\"text\":\"\",\"end\":true}";}
        characters+=n;
        return new org.json.JSONObject()
            .put("text",new String(chars,0,n))
            .put("end",false)
            .put("characters",characters).toString();
    }
    @Override public synchronized void close() throws IOException{reader.close();}
}
