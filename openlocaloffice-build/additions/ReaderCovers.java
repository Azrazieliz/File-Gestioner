package com.openlocal.office.core;

import android.content.Context;
import android.net.Uri;
import android.os.ParcelFileDescriptor;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.pdf.PdfRenderer;
import android.system.Os;
import android.system.OsConstants;
import java.io.*;
import java.security.MessageDigest;
import java.util.*;
import java.util.concurrent.Semaphore;

/** Bounded, disk-cached cover extraction. Large cloud ZIPs never get
 * downloaded just to populate an attractive bookshelf.
 */
public final class ReaderCovers {
    private static final Semaphore WORKERS=new Semaphore(2);
    private ReaderCovers(){}
    public static InputStream open(Context ctx,Uri source,String name,
                                   long size,long lastModified) throws IOException {
        File dir=new File(ctx.getCacheDir(),"covers-v2");
        if(!dir.exists()&&!dir.mkdirs())throw new IOException("Cover cache unavailable");
        String key=hash(source.toString()+"|"+size+"|"+lastModified);
        File cached=new File(dir,key+".jpg");
        if(cached.exists()&&cached.length()>0)return new FileInputStream(cached);
        boolean acquired=false;
        try {
            WORKERS.acquire();
            acquired=true;
            if(cached.exists()&&cached.length()>0)return new FileInputStream(cached);
            // For pipe-only TeraBox streams, extracting a thumbnail from a
            // 2GiB remote ZIP would copy the *entire* file. Skip it instead.
            if(isArchive(name)&&size>64L*1024*1024&&!seekable(ctx,source))
                throw new IOException("Cloud archive needs a local/seekable copy before cover preview");
            Bitmap bitmap=decode(ctx,source,name);
            if(bitmap==null)throw new IOException("No supported illustration/cover");
            File temp=new File(dir,key+".tmp");
            try(FileOutputStream out=new FileOutputStream(temp)){
                if(!bitmap.compress(Bitmap.CompressFormat.JPEG,84,out))
                    throw new IOException("Cannot encode thumbnail");
            }finally{bitmap.recycle();}
            if(!temp.renameTo(cached)){
                if(!cached.exists())throw new IOException("Unable to write cover cache");
                temp.delete();
            }
            return new FileInputStream(cached);
        }catch(IOException e){
            // Missing art must not crash the library, but never silently hide
            // why all covers failed (e.g. an unsupported EPUB XML parser).
            android.util.Log.w("FG_COVERS","Thumbnail extraction failed: "+name,e);
            throw e;
        }        }catch(InterruptedException error){
            Thread.currentThread().interrupt();
            throw new IOException("Cover loading interrupted",error);
        }finally {
            if(acquired)WORKERS.release();
        }
    }
    private static boolean isArchive(String filename){
        String s=filename.toLowerCase(Locale.ROOT);
        return s.endsWith(".zip")||s.endsWith(".cbz")||s.endsWith(".epub");
    }
    private static boolean seekable(Context ctx,Uri uri){
        try(ParcelFileDescriptor fd=ctx.getContentResolver().openFileDescriptor(uri,"r")){
            if(fd==null)return false;
            Os.lseek(fd.getFileDescriptor(),0,OsConstants.SEEK_CUR);
            return true;
        }catch(Exception e){return false;}
    }
    private static Bitmap decode(Context ctx,Uri uri,String name) throws IOException{
        String lower=name.toLowerCase(Locale.ROOT);
        if(lower.endsWith(".pdf")){
            try(ParcelFileDescriptor fd=ctx.getContentResolver().openFileDescriptor(uri,"r")){
                if(fd==null)return null;
                try(PdfRenderer renderer=new PdfRenderer(fd)){
                    if(renderer.getPageCount()==0)return null;
                    try(PdfRenderer.Page page=renderer.openPage(0)){
                        int w=360,h=Math.min(660,Math.max(1,360*page.getHeight()/Math.max(1,page.getWidth())));
                        Bitmap bitmap=Bitmap.createBitmap(w,h,Bitmap.Config.ARGB_8888);
                        bitmap.eraseColor(android.graphics.Color.WHITE);
                        page.render(bitmap,null,null,PdfRenderer.Page.RENDER_MODE_FOR_DISPLAY);
                        return bitmap;
                    }
                }
            }
        }
        if(isArchive(name)){
            try(BookArchive book=new BookArchive(ctx,uri,lower.endsWith(".epub"))){
                if(book.imageCount()==0)return null;
                // Comics: the FIRST page is the cover, never an arbitrary later
                // filename containing "title" or "front". EPUB: prefer its
                // explicitly named cover image when available.
                String candidate=book.imageName(0);
                if(lower.endsWith(".epub")){
                    for(int i=0;i<Math.min(book.imageCount(),40);i++){
                        String n=book.imageName(i).toLowerCase(Locale.ROOT);
                        if(n.matches(".*(?:^|[/_-])(?:cover|frontcover)(?:[_.-]|$).*")){
                            candidate=book.imageName(i);break;
                        }
                    }
                }
                try(InputStream bounds=book.coverStream(candidate)){
                    BitmapFactory.Options meta=new BitmapFactory.Options();
                    meta.inJustDecodeBounds=true;BitmapFactory.decodeStream(bounds,null,meta);
                    if(meta.outWidth<=0||meta.outHeight<=0)return null;
                    int ratio=1;
                    while(meta.outWidth/ratio>380*2||meta.outHeight/ratio>620*2)ratio*=2;
                    BitmapFactory.Options opts=new BitmapFactory.Options();
                    opts.inSampleSize=ratio;opts.inPreferredConfig=Bitmap.Config.RGB_565;
                    try(InputStream image=book.coverStream(candidate)){
                        return BitmapFactory.decodeStream(image,null,opts);
                    }
                }
            }catch(Exception e){throw new IOException("Cover not available: "+e.getMessage(),e);}
        }
        try(InputStream bounds=ctx.getContentResolver().openInputStream(uri)){
            if(bounds==null)return null;
            BitmapFactory.Options meta=new BitmapFactory.Options();
            meta.inJustDecodeBounds=true;BitmapFactory.decodeStream(bounds,null,meta);
            if(meta.outWidth<=0||meta.outHeight<=0)return null;
            int ratio=1;
            while(meta.outWidth/ratio>380*2||meta.outHeight/ratio>620*2)ratio*=2;
            BitmapFactory.Options opts=new BitmapFactory.Options();
            opts.inSampleSize=ratio;opts.inPreferredConfig=Bitmap.Config.RGB_565;
            try(InputStream input=ctx.getContentResolver().openInputStream(uri)){
                return input==null?null:BitmapFactory.decodeStream(input,null,opts);
            }
        }
    }
    private static String hash(String input){
        try{
            byte[] digest=MessageDigest.getInstance("SHA-256").digest(
                input.getBytes(java.nio.charset.StandardCharsets.UTF_8));
            StringBuilder s=new StringBuilder();
            for(byte b:digest)s.append(String.format(Locale.ROOT,"%02x",b&0xff));
            return s.toString();
        }catch(Exception e){return Integer.toHexString(input.hashCode());}
    }
}
