package com.openlocal.office.core;

import android.content.Context;
import android.database.Cursor;
import android.net.Uri;
import android.provider.DocumentsContract;
import android.provider.OpenableColumns;
import org.json.JSONArray;
import org.json.JSONObject;
import java.util.*;

/** Read-only SAF bookshelf: no whole-book copies, no source modifications,
 * no network/third-party service. Enumerate only the selected folder and page.
 */
public final class ReaderLibrary {
    public static final int PAGE_SIZE=500;
    public static final class Listing {
        public final JSONArray items;
        public final String folder;
        Listing(String folder,JSONArray items){this.folder=folder;this.items=items;}
    }
    private ReaderLibrary(){}
    public static Listing list(Context ctx,Uri tree,String folderId) throws Exception{
        String root=DocumentsContract.getTreeDocumentId(tree);
        String id=folderId==null||folderId.isBlank()?root:folderId;
        Uri children=DocumentsContract.buildChildDocumentsUriUsingTree(tree,id);
        String[] cols={
            DocumentsContract.Document.COLUMN_DOCUMENT_ID,
            DocumentsContract.Document.COLUMN_DISPLAY_NAME,
            DocumentsContract.Document.COLUMN_MIME_TYPE,
            DocumentsContract.Document.COLUMN_SIZE,
            DocumentsContract.Document.COLUMN_LAST_MODIFIED
        };
        JSONArray array=new JSONArray();
        try(Cursor cursor=ctx.getContentResolver().query(children,cols,null,null,null)){
            if(cursor==null)throw new java.io.IOException("The folder provider did not return files");
            int total=0;
            while(cursor.moveToNext()){
                String did=cursor.getString(0),name=cursor.getString(1),mime=cursor.getString(2);
                if(name==null||did==null||mime==null)continue;
                boolean folder=DocumentsContract.Document.MIME_TYPE_DIR.equals(mime);
                String lower=name.toLowerCase(Locale.ROOT);
                if(!folder&&!supported(lower))continue;
                JSONObject item=new JSONObject();
                item.put("id",did).put("title",stripExtension(name))
                    .put("name",name).put("mime",mime)
                    .put("folder",folder)
                    .put("size",cursor.isNull(3)?-1L:cursor.getLong(3))
                    .put("modified",cursor.isNull(4)?0L:cursor.getLong(4));
                item.put("uri",DocumentsContract.buildDocumentUriUsingTree(tree,did).toString());
                array.put(item);
                if(++total>=PAGE_SIZE)break;
            }
        }
        return new Listing(id,array);
    }
    /** First actual image or supported book in a folder. Metadata only:
     * do not download any book while listing a collection.
     */
    public static final class CoverCandidate {
        public final Uri uri;
        public final String name;
        public final long size;
        public final long modified;
        CoverCandidate(Uri uri,String name,long size,long modified){
            this.uri=uri;this.name=name;this.size=size;this.modified=modified;
        }
    }
    public static CoverCandidate firstCover(Context ctx,Uri directory) throws Exception {
        Uri children=DocumentsContract.buildChildDocumentsUriUsingTree(
            directory,DocumentsContract.getDocumentId(directory));
        String[] cols={DocumentsContract.Document.COLUMN_DOCUMENT_ID,
            DocumentsContract.Document.COLUMN_DISPLAY_NAME,
            DocumentsContract.Document.COLUMN_MIME_TYPE,
            DocumentsContract.Document.COLUMN_SIZE,
            DocumentsContract.Document.COLUMN_LAST_MODIFIED};
        String bestId=null,bestName=null;
        long bestSize=-1,bestModified=0;
        try(Cursor cursor=ctx.getContentResolver().query(children,cols,null,null,null)){
            if(cursor==null)return null;
            int scanned=0;
            while(cursor.moveToNext()&&scanned++<2000){
                String id=cursor.getString(0),name=cursor.getString(1),mime=cursor.getString(2);
                if(id==null||name==null||mime==null)continue;
                String low=name.toLowerCase(Locale.ROOT);
                if(name.startsWith(".")||low.startsWith("._")||
                   !(low.endsWith(".jpg")||low.endsWith(".jpeg")||
                     low.endsWith(".png")||low.endsWith(".webp")||
                     low.endsWith(".epub")||low.endsWith(".cbz")||
                     low.endsWith(".zip")||low.endsWith(".pdf")))continue;
                if(bestName==null||naturalCompare(name,bestName)<0){
                    bestName=name;bestId=id;
                    bestSize=cursor.isNull(3)?-1:cursor.getLong(3);
                    bestModified=cursor.isNull(4)?0:cursor.getLong(4);
                }
            }
        }
        return bestId==null?null:new CoverCandidate(
            DocumentsContract.buildDocumentUriUsingTree(directory,bestId),
            bestName,bestSize,bestModified);
    }
    private static int naturalCompare(String a,String b){
        int i=0,j=0;
        while(i<a.length()&&j<b.length()){
            char x=a.charAt(i),y=b.charAt(j);
            if(Character.isDigit(x)&&Character.isDigit(y)){
                int startI=i,startJ=j;
                while(i<a.length()&&Character.isDigit(a.charAt(i)))i++;
                while(j<b.length()&&Character.isDigit(b.charAt(j)))j++;
                String n=a.substring(startI,i).replaceFirst("^0+(?!$)","");
                String m=b.substring(startJ,j).replaceFirst("^0+(?!$)","");
                if(n.length()!=m.length())return Integer.compare(n.length(),m.length());
                int c=n.compareTo(m);if(c!=0)return c;
            }else{
                int c=Character.compare(Character.toLowerCase(x),Character.toLowerCase(y));
                if(c!=0)return c;i++;j++;
            }
        }
        return Integer.compare(a.length(),b.length());
    }
    private static boolean supported(String filename){
        for(String suffix:new String[]{
            ".zip",".cbz",".cbr",".epub",".pdf",".docx",".doc",
            ".xlsx",".xls",".csv",".txt",".md",".rtf",".odt",".ods",
            ".sdocx",".jpg",".jpeg",".png",".webp",".avif",".gif",
            ".glb",".gltf",".fbx",".obj",".blend",".vrm",".pmx",".pmd"
        })if(filename.endsWith(suffix))return true;
        return false;
    }
    private static String stripExtension(String text){
        int index=text.lastIndexOf('.');
        return index>0?text.substring(0,index):text;
    }
}
