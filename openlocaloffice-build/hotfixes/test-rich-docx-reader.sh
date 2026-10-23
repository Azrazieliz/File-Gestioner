#!/usr/bin/env bash
set -euo pipefail
# Run after source assembly. This test is real DOCX ZIP -> XML -> renderer,
# with a JVM-only quote stub to avoid loading Android graphics classes.
TEMP="$(mktemp -d)"
trap 'rm -rf "$TEMP"' EXIT
PKG="$TEMP/com/openlocal/office/core"
mkdir -p "$PKG" "$TEMP/classes"
cat > "$PKG/UniversalReader.java" <<'JAVA'
package com.openlocal.office.core;
public final class UniversalReader {
  public static String quote(String s) {
    return "\"" + s.replace("\\","\\\\").replace("\"","\\\"")
      .replace("\n","\\n").replace("\r","\\r") + "\"";
  }
}
JAVA
cat > "$PKG/ReaderStructureCheck.java" <<'JAVA'
package com.openlocal.office.core;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.zip.*;

public final class ReaderStructureCheck {
  static void check(boolean value,String message) {
    if(!value)throw new AssertionError(message);
  }
  public static void main(String[] args)throws Exception {
    String xml="<w:document xmlns:w=\"http://schemas.openxmlformats.org/wordprocessingml/2006/main\">"
      +"<w:body>"
      +"<w:p><w:pPr><w:pStyle w:val=\"Title\"/></w:pPr><w:r><w:t>Title A</w:t></w:r></w:p>"
      +"<w:p><w:r><w:t>First paragraph. Next sentence.</w:t></w:r></w:p>"
      +"<w:tbl><w:tr><w:tc><w:p><w:r><w:t>Left cell</w:t></w:r></w:p></w:tc>"
      +"<w:tc><w:p><w:r><w:t>Right cell</w:t></w:r></w:p></w:tc></w:tr></w:tbl>"
      +"<w:p><w:pPr><w:numPr><w:ilvl w:val=\"0\"/><w:numId w:val=\"4\"/></w:numPr></w:pPr>"
      +"<w:r><w:t>Numbered item</w:t></w:r></w:p>"
      +"<w:p><w:r><w:rPr><w:b/></w:rPr><w:t>&lt;script&gt;safe&lt;/script&gt;</w:t></w:r></w:p>"
      +"</w:body></w:document>";
    ByteArrayOutputStream out=new ByteArrayOutputStream();
    try(ZipOutputStream zip=new ZipOutputStream(out)) {
      zip.putNextEntry(new ZipEntry("word/document.xml"));
      zip.write(xml.getBytes(StandardCharsets.UTF_8));
      zip.closeEntry();
    }
    byte[] docx=out.toByteArray();
    check(RichDocxPreview.blockCount(docx)==5,"Top-level block count must exclude nested table paragraphs");
    String full=RichDocxPreview.window(docx,0,5);
    check(full.contains("<table"),"Table markup missing");
    check(full.contains("Left cell")&&full.contains("Right cell"),"Table cell text missing");
    check(full.indexOf("First paragraph")<full.indexOf("<table"),"Table moved ahead of paragraph");
    check(full.indexOf("Right cell")<full.indexOf("Numbered item"),"Table flattened out of order");
    check(full.contains("<h1"),"Word title style ignored");
    check(full.contains("fg-docx-marker"),"List marker missing");
    check(!full.contains("<script>"),"Untrusted Word content executed as HTML");
    check(full.contains("&lt;script&gt;safe&lt;/script&gt;"),"Escaping corrupted");
    check(RichDocxPreview.find(docx,"right cell",0)==2,"Whole-document search missed a table cell");
    check(RichDocxPreview.find(docx,"title a",0)==0,"Zero-index search is broken");
    check(RichDocxPreview.find(docx,"something absent",0)==-1,"Missing text falsely matched");
    String middle=RichDocxPreview.window(docx,2,1);
    check(middle.contains("<table"),"Window clipped structural block");
    check(!middle.contains("First paragraph"),"Window includes earlier block");
    System.out.println("DOCX structure/regression checks: OK (tables, order, semantics, escape, search, windows)");
  }
}
JAVA
BASE="app/src/main/java/com/openlocal/office/core"
javac -encoding UTF-8 -sourcepath "$TEMP" -d "$TEMP/classes" \
  "$PKG/UniversalReader.java" \
  "$BASE/ZipPackage.java" \
  "$BASE/XmlUtil.java" \
  "$BASE/RichDocxPreview.java" \
  "$PKG/ReaderStructureCheck.java"
java -cp "$TEMP/classes" com.openlocal.office.core.ReaderStructureCheck
