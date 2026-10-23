from pathlib import Path
import re

MAIN=Path("app/src/main/java/com/openlocal/office/MainActivity.java")
MANIFEST=Path("app/src/main/AndroidManifest.xml")
s=MAIN.read_text()

def replace_once(old,new):
    global s
    assert old in s, f"Missing backend anchor: {old[:80]}"
    s=s.replace(old,new,1)

replace_once('private static final long MAX_FILE_BYTES = 40L * 1024L * 1024L;',
             'private static final long MAX_FILE_BYTES = 80L * 1024L * 1024L;')
replace_once('                long size = displaySize(uri);',
'''                String quickType = detectType(uri, name);
                if ("mp3".equals(quickType) || "mp4".equals(quickType) || "pptx".equals(quickType)) {
                    throw new IOException("MP3, MP4 and PPTX are excluded from File Gestioner reading.");
                }
                if ("pdf".equals(quickType)) {
                    int pages = UniversalReader.pdfPages(this, uri);
                    if (pages <= 0) throw new IOException("This PDF has no pages.");
                    xlsx = null; csv = null; docx = null; sdocx = null;
                    textDocument = null; rawDocument = null;
                    currentUri = uri; currentName = name; currentType = "pdf";
                    currentMime = "application/pdf";
                    remember(uri,name,currentMime);
                    String payload = "{\\"type\\":\\"pdf\\",\\"name\\":"+q(name)+
                        ",\\"format\\":\\"pdf\\",\\"readOnly\\":true,\\"pages\\":"+pages+"}";
                    runOnUiThread(() -> js("window.loadDocument(" + payload + ")"));
                    return;
                }
                long size = displaySize(uri);''')
replace_once('                } else if ("xls".equals(type)) {',
'''                } else if ("epub".equals(type) ||
                           "odt".equals(type) || "ods".equals(type) || "odp".equals(type)) {
                    textDocument = UniversalReader.extractDocument(bytes,type);
                    currentType = type; currentMime = mimeForPreview(type);
                    json = readerJson(name,type,textDocument.length());
                } else if ("zip".equals(type) || "cbz".equals(type)) {
                    rawDocument = bytes; currentType = type; currentMime = "application/zip";
                    json = "{\\"type\\":\\"archive\\",\\"name\\":"+q(name)+
                        ",\\"format\\":"+q(type)+",\\"readOnly\\":true}";
                } else if (isImageType(type)) {
                    rawDocument=bytes; currentType=type; currentMime=mimeForPreview(type);
                    json = "{\\"type\\":\\"image\\",\\"name\\":"+q(name)+
                        ",\\"format\\":"+q(type)+",\\"readOnly\\":true}";
                } else if ("rtf".equals(type) || "html".equals(type) || "htm".equals(type)) {
                    String source = new String(bytes,StandardCharsets.UTF_8);
                    textDocument = "rtf".equals(type) ? UniversalReader.plainRtf(source)
                        : android.text.Html.fromHtml(source,android.text.Html.FROM_HTML_MODE_COMPACT).toString();
                    currentType=type; currentMime=mimeForPreview(type);
                    json=readerJson(name,type,textDocument.length());
                } else if (isTextType(type)) {
                    textDocument = new String(bytes,StandardCharsets.UTF_8);
                    if ("json".equals(type)) {
                        try { textDocument = new org.json.JSONObject(textDocument).toString(2); }
                        catch(Exception notObject) {
                            try { textDocument = new org.json.JSONArray(textDocument).toString(2); }
                            catch(Exception ignored) {}
                        }
                    }
                    currentType=type; currentMime=mimeForPreview(type);
                    json=readerJson(name,type,textDocument.length());
                } else if ("doc".equals(type)) {
                    textDocument=LegacyOfficeReader.read(bytes,"doc");
                    currentType="doc"; currentMime=mimeForPreview(type);
                    json = readerJson(name,type,textDocument.length());
                } else if ("xls".equals(type)) {''')
replace_once('                    throw new IOException("Legacy .xls is not included in this offline build. Save it as .xlsx first.");',
'''                    textDocument=LegacyOfficeReader.read(bytes,"xls");
                    currentType="xls"; currentMime=mimeForPreview(type);
                    json = readerJson(name,type,textDocument.length());''')
replace_once('                    throw new IOException("Unsupported file. Open an .xlsx, .csv, .docx, .txt, .md or .sdocx file.");',
'''                    rawDocument=bytes; currentType=type.isEmpty()?"unknown":type;
                    currentMime=mimeForPreview(type); json=binaryJson(name,currentType,bytes.length);''')

replace_once('    private byte[] serializeCurrent() throws Exception {',
'''    private static boolean isImageType(String type) {
        return Arrays.asList("jpg","jpeg","png","webp","gif","bmp","avif","heic","heif").contains(type);
    }
    private static boolean isTextType(String type) {
        return Arrays.asList("tsv","json","xml","yaml","yml","toml","log","ini","conf",
            "properties","sql","svg","tex","bib","java","kt","kts","py","js","ts","css",
            "scss","sh","bat","ps1","c","cpp","h","hpp","rs","go","rb","php","swift",
            "gradle","gitignore","dockerfile").contains(type);
    }
    private static String mimeForPreview(String type) {
        if ("doc".equals(type))return "application/msword";
        if ("xls".equals(type))return "application/vnd.ms-excel";
        if ("pdf".equals(type))return "application/pdf";
        if ("epub".equals(type))return "application/epub+zip";
        if ("odt".equals(type))return "application/vnd.oasis.opendocument.text";
        if ("ods".equals(type))return "application/vnd.oasis.opendocument.spreadsheet";
        if ("odp".equals(type))return "application/vnd.oasis.opendocument.presentation";
        if ("png".equals(type))return "image/png";
        if ("jpg".equals(type)||"jpeg".equals(type))return "image/jpeg";
        if ("webp".equals(type))return "image/webp";
        if ("gif".equals(type))return "image/gif";
        if ("bmp".equals(type))return "image/bmp";
        if ("avif".equals(type))return "image/avif";
        if ("heif".equals(type)||"heic".equals(type))return "image/heif";
        return "text/plain";
    }
    private static String readerJson(String name,String type,int length) {
        return "{\\"type\\":\\"reader\\",\\"name\\":"+q(name)+",\\"format\\":"+q(type)+
            ",\\"characters\\":"+length+",\\"readOnly\\":true}";
    }
    private static String binaryJson(String name,String type,int length) {
        return "{\\"type\\":\\"binary\\",\\"name\\":"+q(name)+",\\"format\\":"+q(type)+
            ",\\"bytes\\":"+length+",\\"readOnly\\":true}";
    }

    private byte[] serializeCurrent() throws Exception {''')
replace_once('        if (xlsx != null) return xlsx.serialize();',
'''        if (Arrays.asList("pdf","pptx","doc","epub","odt","ods","odp","zip","cbz",
              "image","rtf","html","htm","xls","unknown").contains(currentType) ||
              isImageType(currentType) || isTextType(currentType)) {
            throw new IOException("This format is available for reading only; editing the original is disabled.");
        }
        if (xlsx != null) return xlsx.serialize();''')
replace_once('    private String detectType(Uri uri,String name){',
'''    private String detectType(Uri uri,String name){''')
replace_once('        if("xlsx".equals(ext)||"csv".equals(ext)||"docx".equals(ext)||"txt".equals(ext)||"md".equals(ext)||"markdown".equals(ext)||"sdocx".equals(ext)||"xls".equals(ext))return ext;',
'''        if(!ext.isEmpty() &&
           (Arrays.asList("xlsx","csv","docx","txt","md","markdown","sdocx","xls",
              "pdf","pptx","epub","odt","ods","odp","zip","cbz","rtf","html","htm","doc","mp3","mp4").contains(ext) ||
             isImageType(ext) || isTextType(ext)))return ext;''')
replace_once('        if("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet".equals(m))return "xlsx";',
'''        if("application/msword".equals(m))return "doc";
        if("application/vnd.ms-excel".equals(m))return "xls";
        if("application/pdf".equals(m))return "pdf";
        if("application/epub+zip".equals(m))return "epub";
        if(m!=null && m.startsWith("image/"))return m.substring(6).replace("svg+xml","svg");
        if("application/vnd.openxmlformats-officedocument.presentationml.presentation".equals(m))return "pptx";
        if("application/vnd.oasis.opendocument.text".equals(m))return "odt";
        if("application/vnd.oasis.opendocument.spreadsheet".equals(m))return "ods";
        if("application/vnd.oasis.opendocument.presentation".equals(m))return "odp";
        if("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet".equals(m))return "xlsx";''')
replace_once('        return "";\n    }\n    private long displaySize',
'''        if("audio/mpeg".equals(m))return "mp3";
        if("video/mp4".equals(m))return "mp4";
        if(m!=null && m.startsWith("text/"))return "txt";
        return "";
    }
    private long displaySize''')

replace_once('        @JavascriptInterface public void saveCopy(){',
'''        @JavascriptInterface public int getDocxRichBlockCount() {
            try {return docx==null?0:RichDocxPreview.blockCount(docx.serialize());}
            catch(Exception e){return 0;}
        }
        @JavascriptInterface public int findDocxBlock(String needle,int start) {
            try {return docx==null?-1:RichDocxPreview.find(docx.serialize(),needle,start);}
            catch(Exception e){return -1;}
        }
        @JavascriptInterface public String getDocxRichWindow(int start,int count) {
            try {return docx==null?"[]":RichDocxPreview.window(docx.serialize(),start,count);}
            catch(Exception e){return "[]";}
        }
        @JavascriptInterface public String getPdfPage(int index,int width) {
            try { return currentUri==null||!"pdf".equals(currentType)?"":UniversalReader.pdfPage(
                MainActivity.this,currentUri,index,width); }
            catch(Exception e){return "";}
        }
        @JavascriptInterface public String getArchiveEntries() {
            try {return rawDocument==null?"[]":UniversalReader.archiveListJson(rawDocument);}
            catch(Exception e){return "[]";}
        }
        @JavascriptInterface public String getArchiveEntryBase64(String name) {
            try {return rawDocument==null?"":UniversalReader.entryBase64(rawDocument,name);}
            catch(Exception e){return "";}
        }
        @JavascriptInterface public void saveCopy(){''')
MAIN.write_text(s)

manifest=MANIFEST.read_text()
anchor='<data android:mimeType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" />'
assert anchor in manifest
manifest=manifest.replace(anchor,anchor+'''
                <data android:mimeType="application/msword" />
                <data android:mimeType="application/vnd.ms-excel" />
                <data android:mimeType="application/pdf" />
                <data android:mimeType="application/epub+zip" />
                <data android:mimeType="application/vnd.oasis.opendocument.text" />
                <data android:mimeType="application/vnd.oasis.opendocument.spreadsheet" />
                <data android:mimeType="application/vnd.oasis.opendocument.presentation" />
                <data android:mimeType="image/*" />
                <data android:mimeType="text/*" />''')
MANIFEST.write_text(manifest)

gradle=Path("app/build.gradle.kts")
if gradle.exists():
    build=gradle.read_text()
    if "org.apache.poi:poi-scratchpad:" not in build:
        if "dependencies {" in build:
            build=build.replace("dependencies {", "dependencies {\n    implementation(\"org.apache.poi:poi-scratchpad:5.4.1\")",1)
        else:
            build += "\ndependencies {\n    implementation(\"org.apache.poi:poi-scratchpad:5.4.1\")\n}\n"
    build=re.sub(r'versionCode\s*=\s*(\d+)',lambda m:'versionCode = '+str(int(m.group(1))+1),build,count=1)
    build=re.sub(r'versionName\s*=\s*"[^"]+"','versionName = "0.9.0"',build,count=1)
    gradle.write_text(build)
print("Universal document reader backend installed")
