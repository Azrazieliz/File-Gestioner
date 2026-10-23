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
