package com.openlocal.office.core;

import java.nio.charset.StandardCharsets;
import java.util.*;
import org.w3c.dom.*;

/** Safe, rich DOCX read view. Never changes the existing editable DocxSession. */
public final class RichDocxPreview {
    private static final String W="http://schemas.openxmlformats.org/wordprocessingml/2006/main";
    private static final String R="http://schemas.openxmlformats.org/officeDocument/2006/relationships";
    private static final String A="http://schemas.openxmlformats.org/drawingml/2006/main";

    private final ZipPackage pkg;
    private final NodeList paragraphs;
    private final Map<String,String> images=new HashMap<>();

    private RichDocxPreview(byte[] bytes)throws Exception{
        pkg=ZipPackage.read(bytes);
        Document doc=XmlUtil.parse(pkg.get("word/document.xml"));
        paragraphs=doc.getElementsByTagNameNS(W,"p");
        byte[] rels=pkg.entries.get("word/_rels/document.xml.rels");
        if(rels!=null){
            Document relations=XmlUtil.parse(rels);
            NodeList items=relations.getElementsByTagName("Relationship");
            for(int i=0;i<items.getLength();i++){
                Element rel=(Element)items.item(i);
                if("External".equalsIgnoreCase(rel.getAttribute("TargetMode")))continue;
                String id=rel.getAttribute("Id"),target=rel.getAttribute("Target");
                if(id.isEmpty()||target.isEmpty())continue;
                String p=target.startsWith("/")?target.substring(1):"word/"+target;
                p=p.replace("word/../","").replace("word/./","word/");
                if(p.startsWith("word/media/") && !p.contains(".."))images.put(id,p);
            }
        }
    }

    public static String window(byte[] bytes,int start,int length)throws Exception{
        RichDocxPreview d=new RichDocxPreview(bytes);
        int begin=Math.max(0,start),end=Math.min(d.paragraphs.getLength(),begin+Math.max(0,Math.min(150,length)));
        StringBuilder s=new StringBuilder("[");
        for(int i=begin;i<end;i++){
            if(i>begin)s.append(',');
            String markup=d.paragraph((Element)d.paragraphs.item(i));
            s.append('[').append(i).append(',').append(UniversalReader.quote(markup)).append(']');
        }
        return s.append(']').toString();
    }

    private String paragraph(Element p){
        String style="";
        NodeList ps=p.getElementsByTagNameNS(W,"pStyle");
        if(ps.getLength()>0)style=((Element)ps.item(0)).getAttributeNS(W,"val");
        String lower=style.toLowerCase(Locale.ROOT);
        String tag=lower.equals("title")?"h1":lower.startsWith("heading1")?"h2":
            lower.startsWith("heading2")?"h3":lower.startsWith("heading")?"h4":"p";
        String cls=lower.contains("quote")?"fg-docx-quote":"fg-docx-block";
        StringBuilder out=new StringBuilder("<").append(tag).append(" class=\"").append(cls).append("\">");
        NodeList children=p.getChildNodes();
        for(int i=0;i<children.getLength();i++)node(children.item(i),out);
        out.append("</").append(tag).append(">");
        return out.toString();
    }

    private void node(Node n,StringBuilder out){
        if(!(n instanceof Element))return;
        Element e=(Element)n;
        String local=e.getLocalName(),ns=e.getNamespaceURI();
        if(W.equals(ns)&&("pPr".equals(local)||"rPr".equals(local)))return;
        if(W.equals(ns)&&"t".equals(local)){out.append(escape(e.getTextContent()));return;}
        if(W.equals(ns)&&"tab".equals(local)){out.append("&emsp;");return;}
        if(W.equals(ns)&&"br".equals(local)){out.append("<br>");return;}
        if(W.equals(ns)&&"r".equals(local)){
            Element rp=null;
            NodeList ch=e.getChildNodes();
            for(int i=0;i<ch.getLength();i++){
                Node c=ch.item(i);
                if(c instanceof Element&&W.equals(c.getNamespaceURI())&&"rPr".equals(c.getLocalName()))rp=(Element)c;
            }
            boolean bold=has(rp,"b"),italic=has(rp,"i"),underline=has(rp,"u"),strike=has(rp,"strike");
            if(bold)out.append("<strong>");
            if(italic)out.append("<em>");
            if(underline)out.append("<u>");
            if(strike)out.append("<s>");
            for(int i=0;i<ch.getLength();i++)node(ch.item(i),out);
            if(strike)out.append("</s>");
            if(underline)out.append("</u>");
            if(italic)out.append("</em>");
            if(bold)out.append("</strong>");
            return;
        }
        if(W.equals(ns)&&"drawing".equals(local)) {
            NodeList blips=e.getElementsByTagNameNS(A,"blip");
            for(int i=0;i<blips.getLength();i++){
                Element blip=(Element)blips.item(i);
                String id=blip.getAttributeNS(R,"embed"),name=images.get(id);
                if(name==null)continue;
                byte[] payload=pkg.entries.get(name);
                if(payload==null||payload.length>3_000_000){out.append("[embedded image]");continue;}
                String ext=name.substring(name.lastIndexOf('.')+1).toLowerCase(Locale.ROOT);
                String mime=ext.equals("jpg")||ext.equals("jpeg")?"image/jpeg":ext.equals("png")?"image/png":
                    ext.equals("gif")?"image/gif":ext.equals("webp")?"image/webp":"";
                if(mime.isEmpty()){out.append("[embedded image]");continue;}
                out.append("<img alt=\"Embedded image\" src=\"data:").append(mime).append(";base64,")
                    .append(java.util.Base64.getEncoder().encodeToString(payload)).append("\">");
            }
            return;
        }
        NodeList children=n.getChildNodes();
        for(int i=0;i<children.getLength();i++)node(children.item(i),out);
    }

    private boolean has(Element pr,String local){
        if(pr==null)return false;
        NodeList nodes=pr.getElementsByTagNameNS(W,local);
        if(nodes.getLength()==0)return false;
        String val=((Element)nodes.item(0)).getAttributeNS(W,"val");
        return !val.equals("0")&&!val.equalsIgnoreCase("false");
    }
    private String escape(String raw){
        return raw.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
            .replace("\"","&quot;").replace("'","&#39;");
    }
}
