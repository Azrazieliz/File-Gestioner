package com.openlocal.office.core;

import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.Color;
import android.graphics.Matrix;
import android.graphics.pdf.PdfRenderer;
import android.net.Uri;
import android.os.ParcelFileDescriptor;
import android.text.Html;
import android.util.Base64;

import org.w3c.dom.*;
import javax.xml.parsers.DocumentBuilderFactory;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import java.util.regex.*;
import java.util.zip.*;

/** Bounded, offline-only readers for documents not served by native editable sessions. */
public final class UniversalReader {
    private UniversalReader() {}
    private static final int MAX_ENTRIES = 3000;
    private static final int MAX_TEXT_ENTRY = 3 * 1024 * 1024;
    private static final int MAX_IMAGE_ENTRY = 12 * 1024 * 1024;
    private static final long MAX_TOTAL_EXTRACT = 40L * 1024L * 1024L;
    private static final Pattern IMAGE = Pattern.compile("(?i).+\\.(png|jpe?g|gif|webp|bmp|avif)$");
    private static final Pattern TEXT = Pattern.compile("(?i).+\\.(txt|md|markdown|csv|tsv|json|xml|yaml|yml|html?|xhtml|css|js|java|kt|py|ini|log|sql|rtf)$");
    private static final Pattern EPUB_CHAPTER = Pattern.compile("(?i).+\\.(html?|xhtml)$");
    private static final Pattern PPT_SLIDE = Pattern.compile("ppt/slides/slide([0-9]+)\\.xml");
    private static final Pattern LIST_LIMIT = Pattern.compile(".*"); // all entries processed under explicit size limits

    public static int pdfPages(Context ctx, Uri uri) throws IOException {
        try (ParcelFileDescriptor fd=ctx.getContentResolver().openFileDescriptor(uri, "r")) {
            if(fd==null)throw new IOException("The PDF provider did not open the file.");
            try(PdfRenderer pdf=new PdfRenderer(fd)){return pdf.getPageCount();}
        }
    }

    public static String pdfPage(Context ctx, Uri uri, int pageIndex, int targetWidth) throws IOException {
        try(ParcelFileDescriptor fd=ctx.getContentResolver().openFileDescriptor(uri, "r")) {
            if(fd==null)throw new IOException("Cannot read PDF.");
            try(PdfRenderer pdf=new PdfRenderer(fd)) {
                if(pageIndex<0||pageIndex>=pdf.getPageCount()) throw new IOException("PDF page out of bounds");
                try(PdfRenderer.Page page=pdf.openPage(pageIndex)) {
                    int width=Math.max(360,Math.min(1500,targetWidth));
                    int height=Math.max(1,Math.round(width*(page.getHeight()/(float)page.getWidth())));
                    if(height>4000){width=Math.round(width*(4000f/height));height=4000;}
                    Bitmap bitmap=Bitmap.createBitmap(width,height,Bitmap.Config.ARGB_8888);
                    try {
                        bitmap.eraseColor(Color.WHITE);
                        page.render(bitmap,null,null,PdfRenderer.Page.RENDER_MODE_FOR_DISPLAY);
                        ByteArrayOutputStream out=new ByteArrayOutputStream();
                        bitmap.compress(Bitmap.CompressFormat.JPEG,84,out);
                        return Base64.encodeToString(out.toByteArray(), Base64.NO_WRAP);
                    } finally {bitmap.recycle();}
                }
            }
        }
    }

    public static final class Entry {
        public final String name;
        public final long size;
        public Entry(String name,long size){this.name=name;this.size=size;}
    }

    public static List<Entry> list(byte[] data) throws IOException {
        ArrayList<Entry> out=new ArrayList<>();
        try(ZipInputStream zip=new ZipInputStream(new ByteArrayInputStream(data))) {
            ZipEntry e; int count=0;
            while((e=zip.getNextEntry())!=null) {
                if(++count>MAX_ENTRIES) throw new IOException("Archive exceeds 3,000 entries.");
                if(!e.isDirectory()&&!e.getName().startsWith("__MACOSX/"))
                    out.add(new Entry(e.getName(),e.getSize()));
                zip.closeEntry();
            }
        }
        out.sort(Comparator.comparing(a->a.name, String.CASE_INSENSITIVE_ORDER));
        return out;
    }

    private static byte[] entryBytes(byte[] data,String name,int limit) throws IOException {
        try(ZipInputStream zip=new ZipInputStream(new ByteArrayInputStream(data))) {
            ZipEntry e; int seen=0;
            while((e=zip.getNextEntry())!=null) {
                if(++seen>MAX_ENTRIES)throw new IOException("Archive has too many entries.");
                if(name.equals(e.getName())) {
                    if(e.getSize()>limit)throw new IOException("Entry exceeds preview size limit.");
                    ByteArrayOutputStream out=new ByteArrayOutputStream();
                    byte[] buffer=new byte[16384];int n,total=0;
                    while((n=zip.read(buffer))!=-1){
                        total+=n;
                        if(total>limit)throw new IOException("Archive entry expands beyond safe limit.");
                        out.write(buffer,0,n);
                    }
                    return out.toByteArray();
                }
            }
        }
        return null;
    }

    public static String entryBase64(byte[] data,String name) throws IOException {
        if(data==null||name==null)return "";
        if(!IMAGE.matcher(name).matches()&&!TEXT.matcher(name).matches())
            throw new IOException("This archive entry has no safe inline preview.");
        byte[] content=entryBytes(data,name,IMAGE.matcher(name).matches()?MAX_IMAGE_ENTRY:MAX_TEXT_ENTRY);
        if(content==null)throw new IOException("Archive entry not found.");
        return Base64.encodeToString(content,Base64.NO_WRAP);
    }

    public static String archiveListJson(byte[] bytes) throws IOException {
        List<Entry> entries=list(bytes);
        StringBuilder s=new StringBuilder("[");
        for(Entry e:entries){
            if(s.length()>1)s.append(',');
            s.append("{\"name\":").append(quote(e.name)).append(",\"size\":").append(e.size)
                .append(",\"preview\":").append(IMAGE.matcher(e.name).matches()||TEXT.matcher(e.name).matches()).append('}');
        }
        return s.append(']').toString();
    }

    public static String extractDocument(byte[] archive,String kind) throws Exception {
        List<Entry> entries=list(archive);
        StringBuilder result=new StringBuilder();
        long total=0;
        int slides=0;
        for(Entry e:entries) {
            String path=e.name;
            boolean accept;
            if("pptx".equals(kind)) accept=PPT_SLIDE.matcher(path).matches();
            else if("epub".equals(kind)) accept=EPUB_CHAPTER.matcher(path).matches() &&
                !path.toLowerCase(Locale.ROOT).contains("nav.") &&
                !path.toLowerCase(Locale.ROOT).contains("toc.");
            else accept=path.equals("content.xml"); // ODT, ODS, ODP
            if(!accept)continue;
            byte[] part=entryBytes(archive,path,MAX_TEXT_ENTRY);
            if(part==null)continue;
            total+=part.length;
            if(total>MAX_TOTAL_EXTRACT)throw new IOException("Document expands beyond safe limit");
            String text;
            if("epub".equals(kind)) {
                String html=new String(part,StandardCharsets.UTF_8);
                text=Html.fromHtml(html, Html.FROM_HTML_MODE_COMPACT).toString();
            } else {
                text=xmlText(part, "pptx".equals(kind));
            }
            if(text.isBlank())continue;
            if("pptx".equals(kind)) {
                slides++;
                Matcher m=PPT_SLIDE.matcher(path);
                String label=m.matches()?m.group(1):String.valueOf(slides);
                result.append("\n\nSLIDE ").append(label).append("\n\n");
            } else if("epub".equals(kind)) {
                result.append("\n\n").append(path.replaceAll(".*/","")).append("\n\n");
            }
            result.append(text.trim()).append("\n");
            if(result.length()>3_000_000)throw new IOException("Extracted document text exceeds preview limit");
        }
        if(result.length()==0)throw new IOException("No readable content was found inside this document.");
        return result.toString().trim();
    }

    private static String xmlText(byte[] content, boolean slideMode) throws Exception {
        DocumentBuilderFactory factory=DocumentBuilderFactory.newInstance();
        factory.setNamespaceAware(true);
        factory.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);
        factory.setFeature("http://xml.org/sax/features/external-general-entities", false);
        factory.setFeature("http://xml.org/sax/features/external-parameter-entities", false);
        org.w3c.dom.Document doc=factory.newDocumentBuilder().parse(new ByteArrayInputStream(content));
        NodeList nodes=doc.getElementsByTagName("*");
        StringBuilder out=new StringBuilder();
        for(int i=0;i<nodes.getLength();i++) {
            Element e=(Element)nodes.item(i);
            String n=e.getLocalName();
            if(slideMode) {
                if("t".equals(n)&&e.getNamespaceURI()!=null)out.append(e.getTextContent()).append(' ');
                if("p".equals(n)&&out.length()>0)out.append('\n');
            } else {
                if("p".equals(n)||"h".equals(n)) {
                    String text=e.getTextContent().trim();
                    if(!text.isEmpty())out.append(text).append("\n\n");
                } else if("table-row".equals(n)) {
                    out.append('\n');
                }
            }
        }
        return out.toString();
    }

    public static String plainRtf(String raw) {
        // Safe text approximation; never executes objects/macros.
        return raw.replaceAll("(?s)\\{\\\\\\*[^{}]*\\}","")
            .replaceAll("\\\\par\\b","\\n")
            .replaceAll("\\\\tab\\b","\\t")
            .replaceAll("\\\\'[a-fA-F0-9]{2}","")
            .replaceAll("\\\\[a-zA-Z]+-?\\d* ?","")
            .replaceAll("[{}]","").trim();
    }

    public static String quote(String s){
        if(s==null)return "null";
        StringBuilder o=new StringBuilder("\"");
        for(int i=0;i<s.length();i++){
            char c=s.charAt(i);
            if(c=='\\'||c=='"')o.append('\\').append(c);
            else if(c=='\n')o.append("\\n");
            else if(c=='\r')o.append("\\r");
            else if(c=='\t')o.append("\\t");
            else if(c<32)o.append(String.format("\\u%04x",(int)c));
            else o.append(c);
        }
        return o.append('"').toString();
    }
}
