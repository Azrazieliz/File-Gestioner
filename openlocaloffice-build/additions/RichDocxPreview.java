package com.openlocal.office.core;

import java.util.*;
import org.w3c.dom.*;

/**
 * Faithful, read-only DOCX flow: renders Word body blocks in their actual order.
 * A table is ONE structural block, not its paragraphs scattered into the text.
 * Uses bounded windows and escaped, internally generated HTML; preserves the
 * existing editable DocxSession without modifying or rewriting its source.
 */
public final class RichDocxPreview {
    private static final String W="http://schemas.openxmlformats.org/wordprocessingml/2006/main";
    private static final String R="http://schemas.openxmlformats.org/officeDocument/2006/relationships";
    private static final String A="http://schemas.openxmlformats.org/drawingml/2006/main";
    private final ZipPackage pkg;
    private final ArrayList<Element> blocks=new ArrayList<>();
    private final Map<String,String> images=new HashMap<>();
    private final Map<String,String> numberFormats=new HashMap<>();

    private RichDocxPreview(byte[] bytes)throws Exception{
        pkg=ZipPackage.read(bytes);
        byte[] data=pkg.entries.get("word/document.xml");
        if(data==null)throw new IllegalArgumentException("DOCX has no document body");
        Document document=XmlUtil.parse(data);
        NodeList bodies=document.getElementsByTagNameNS(W,"body");
        if(bodies.getLength()==0)throw new IllegalArgumentException("DOCX has no Word body");
        gather((Element)bodies.item(0));
        if(blocks.size()>75000)throw new IllegalArgumentException("DOCX exceeds paragraph preview limit");
        byte[] rels=pkg.entries.get("word/_rels/document.xml.rels");
        if(rels!=null){
            Document relations=XmlUtil.parse(rels);
            NodeList items=relations.getElementsByTagName("Relationship");
            for(int i=0;i<items.getLength();i++){
                Element rel=(Element)items.item(i);
                if("External".equalsIgnoreCase(rel.getAttribute("TargetMode")))continue;
                String id=rel.getAttribute("Id"),target=rel.getAttribute("Target");
                if(id.isEmpty()||target.isEmpty())continue;
                String path=target.startsWith("/")?target.substring(1):"word/"+target;
                path=path.replace("word/../","").replace("word/./","word/");
                if(path.startsWith("word/media/")&&!path.contains(".."))images.put(id,path);
            }
        }
        byte[] numbering=pkg.entries.get("word/numbering.xml");
        if(numbering!=null){
            Document numberingDoc=XmlUtil.parse(numbering);
            Map<String,String> abstractFormats=new HashMap<>(),numAbstract=new HashMap<>();
            NodeList abstractNodes=numberingDoc.getElementsByTagNameNS(W,"abstractNum");
            for(int i=0;i<abstractNodes.getLength();i++){
                Element abstractNode=(Element)abstractNodes.item(i);
                String id=abstractNode.getAttributeNS(W,"abstractNumId");
                for(Element lvl:direct(abstractNode,"lvl")){
                    String index=lvl.getAttributeNS(W,"ilvl");
                    Element fmt=first(lvl,"numFmt");
                    if(fmt!=null)abstractFormats.put(id+":"+index,fmt.getAttributeNS(W,"val"));
                }
            }
            NodeList nums=numberingDoc.getElementsByTagNameNS(W,"num");
            for(int i=0;i<nums.getLength();i++){
                Element num=(Element)nums.item(i);
                Element aid=first(num,"abstractNumId");
                if(aid!=null)numAbstract.put(num.getAttributeNS(W,"numId"),aid.getAttributeNS(W,"val"));
            }
            for(Map.Entry<String,String> n:numAbstract.entrySet())
                for(int lvl=0;lvl<9;lvl++)
                    numberFormats.put(n.getKey()+":"+lvl,
                        abstractFormats.getOrDefault(n.getValue()+":"+lvl,"bullet"));
        }
    }

    /** Total top-level paragraphs/tables in true document order, not nested p count. */
    public static int blockCount(byte[] bytes)throws Exception{
        return new RichDocxPreview(bytes).blocks.size();
    }

    /** Stable bounded ordered blocks. Each item is [blockIndex,safeMarkup]. */
    public static String window(byte[] bytes,int start,int count)throws Exception{
        RichDocxPreview doc=new RichDocxPreview(bytes);
        int from=Math.max(0,start),to=Math.min(doc.blocks.size(),from+Math.max(0,Math.min(36,count)));
        Map<String,Integer> numbers=new HashMap<>();
        for(int i=0;i<from&&i<doc.blocks.size();i++)doc.accumulateListCounters(doc.blocks.get(i),numbers);
        StringBuilder output=new StringBuilder("[");
        for(int i=from;i<to;i++){
            if(i>from)output.append(',');
            String html=doc.block(doc.blocks.get(i),numbers);
            output.append('[').append(i).append(',')
                .append(UniversalReader.quote(html)).append(']');
        }
        return output.append(']').toString();
    }

    private void gather(Element parent){
        for(Node n=parent.getFirstChild();n!=null;n=n.getNextSibling()){
            if(!(n instanceof Element))continue;
            Element e=(Element)n;
            if(W.equals(e.getNamespaceURI())&&
               ("p".equals(e.getLocalName())||"tbl".equals(e.getLocalName()))) {
                blocks.add(e);
            } else if(W.equals(e.getNamespaceURI())&&
                      ("sdt".equals(e.getLocalName())||"sdtContent".equals(e.getLocalName())||
                       "customXml".equals(e.getLocalName())||"ins".equals(e.getLocalName()))) {
                gather(e);
            }
        }
    }

    private String block(Element e,Map<String,Integer> counters){
        if("tbl".equals(e.getLocalName()))return table(e,0);
        return paragraph(e,counters,false);
    }

    private void accumulateListCounters(Element element,Map<String,Integer> counts){
        if(!"p".equals(element.getLocalName()))return;
        String key=listKey(element);
        if(key!=null)counts.put(key,counts.getOrDefault(key,0)+1);
    }

    private String listKey(Element p){
        Element pr=first(p,"pPr");
        if(pr==null)return null;
        Element numPr=first(pr,"numPr");
        if(numPr==null)return null;
        Element id=first(numPr,"numId");
        if(id==null)return null;
        Element level=first(numPr,"ilvl");
        String val=id.getAttributeNS(W,"val");
        if(val.isEmpty()||"0".equals(val))return null;
        int depth=Math.max(0,Math.min(8,intAttr(level,"val",0)));
        return val+":"+depth;
    }

    private String paragraph(Element p,Map<String,Integer> counters,boolean inCell){
        Element pr=first(p,"pPr"),ps=pr==null?null:first(pr,"pStyle");
        String style=ps==null?"":ps.getAttributeNS(W,"val").toLowerCase(Locale.ROOT);
        String kind="p";
        if(style.contains("title")||style.equals("titre"))kind="h1";
        else if(style.matches(".*(?:heading|titre)[ _-]*1$"))kind="h2";
        else if(style.matches(".*(?:heading|titre)[ _-]*2$"))kind="h3";
        else if(style.matches(".*(?:heading|titre)[ _-]*[3-9]$"))kind="h4";
        Element outline=pr==null?null:first(pr,"outlineLvl");
        int level=intAttr(outline,"val",-1);
        if(level>=0&&level<=2)kind=level==0?"h2":level==1?"h3":"h4";
        String key=listKey(p);
        StringBuilder out=new StringBuilder();
        String cls=key==null?"fg-docx-p":"fg-docx-listitem";
        if(style.contains("quote")||style.contains("citation"))cls+=" fg-docx-quote";
        if(inCell)cls+=" fg-docx-cell-p";
        StringBuilder body=new StringBuilder();
        for(Node n=p.getFirstChild();n!=null;n=n.getNextSibling())inline(n,body);
        if(body.toString().trim().isEmpty()){
            // Keep real deliberate blank lines, but make them small and unobtrusive.
            return "<p class=\"fg-docx-blank\" aria-hidden=\"true\"></p>";
        }
        out.append('<').append(kind).append(" class=\"").append(cls).append("\"");
        StringBuilder css=new StringBuilder();
        if(pr!=null){
            Element jc=first(pr,"jc");
            String align=jc==null?"":jc.getAttributeNS(W,"val");
            if(align.equals("center")||align.equals("right")||align.equals("both"))
                css.append("text-align:").append(align.equals("both")?"justify":align).append(';');
            Element spacing=first(pr,"spacing");
            if(spacing!=null){
                int before=intAttr(spacing,"before",-1),after=intAttr(spacing,"after",-1);
                if(before>=0)css.append("margin-top:").append(Math.min(36,before/15)).append("px;");
                if(after>=0)css.append("margin-bottom:").append(Math.min(32,after/15)).append("px;");
            }
        }
        if(key!=null){
            int depth=Integer.parseInt(key.substring(key.indexOf(':')+1));
            css.append("margin-left:").append(Math.min(96,depth*16+12)).append("px;");
        }
        if(css.length()>0)out.append(" style=\"").append(css).append("\"");
        out.append('>');
        if(key!=null){
            int value=counters.getOrDefault(key,0)+1;
            counters.put(key,value);
            String format=numberFormats.getOrDefault(key,style.contains("number")?"decimal":"bullet");
            String marker=numberLabel(format,value);
            out.append("<span class=\"fg-docx-marker\" aria-hidden=\"true\">").append(escape(marker)).append("</span>");
        }
        out.append(body);
        out.append("</").append(kind).append('>');
        return out.toString();
    }

    private String numberLabel(String format,int value){
        switch(format){
            case "decimal":return value+".";
            case "lowerLetter":return String.valueOf((char)('a'+(value-1)%26))+".";
            case "upperLetter":return String.valueOf((char)('A'+(value-1)%26))+".";
            case "lowerRoman":return roman(value).toLowerCase(Locale.ROOT)+".";
            case "upperRoman":return roman(value)+".";
            default:return "•";
        }
    }

    private static String roman(int n){
        int[] values={1000,900,500,400,100,90,50,40,10,9,5,4,1};
        String[] labels={"M","CM","D","CD","C","XC","L","XL","X","IX","V","IV","I"};
        StringBuilder s=new StringBuilder();
        int remaining=Math.min(n,9999);
        for(int i=0;i<values.length;i++)while(remaining>=values[i]){
            remaining-=values[i];s.append(labels[i]);
        }
        return s.toString();
    }

    private String table(Element t,int depth){
        if(depth>5)return "<p>[Nested table exceeds preview depth]</p>";
        StringBuilder out=new StringBuilder("<div class=\"fg-docx-table-scroll\"><table class=\"fg-docx-table\"><tbody>");
        for(Element row:direct(t,"tr")){
            out.append("<tr>");
            for(Element cell:direct(row,"tc")){
                Element properties=first(cell,"tcPr"),span=properties==null?null:first(properties,"gridSpan");
                int colspan=Math.max(1,Math.min(24,intAttr(span,"val",1)));
                out.append("<td");
                if(colspan>1)out.append(" colspan=\"").append(colspan).append('"');
                out.append('>');
                boolean any=false;
                for(Node n=cell.getFirstChild();n!=null;n=n.getNextSibling()){
                    if(!(n instanceof Element)||!W.equals(n.getNamespaceURI()))continue;
                    Element e=(Element)n;
                    if("p".equals(e.getLocalName())){
                        out.append(paragraph(e,new HashMap<>(),true));any=true;
                    } else if("tbl".equals(e.getLocalName())){
                        out.append(table(e,depth+1));any=true;
                    }
                }
                if(!any)out.append("&nbsp;");
                out.append("</td>");
            }
            out.append("</tr>");
        }
        return out.append("</tbody></table></div>").toString();
    }

    private void inline(Node node,StringBuilder out){
        if(!(node instanceof Element))return;
        Element e=(Element)node;
        String local=e.getLocalName(),ns=e.getNamespaceURI();
        if(W.equals(ns)){
            if("pPr".equals(local)||"rPr".equals(local)||"instrText".equals(local)||
               "delText".equals(local)||"del".equals(local)||"fldChar".equals(local))return;
            if("t".equals(local)){out.append(escape(e.getTextContent()));return;}
            if("tab".equals(local)){out.append("&#9;");return;}
            if("br".equals(local)||"cr".equals(local)){out.append("<br>");return;}
            if("noBreakHyphen".equals(local)){out.append("&#8209;");return;}
            if("softHyphen".equals(local)){out.append("&shy;");return;}
            if("r".equals(local)){
                Element pr=first(e,"rPr");
                boolean bold=enabled(pr,"b"),italic=enabled(pr,"i"),
                    under=enabled(pr,"u"),strike=enabled(pr,"strike");
                Element sup=pr==null?null:first(pr,"vertAlign");
                String vertical=sup==null?"":sup.getAttributeNS(W,"val");
                if(bold)out.append("<strong>");
                if(italic)out.append("<em>");
                if(under)out.append("<u>");
                if(strike)out.append("<s>");
                if(vertical.equals("superscript"))out.append("<sup>");
                if(vertical.equals("subscript"))out.append("<sub>");
                for(Node n=e.getFirstChild();n!=null;n=n.getNextSibling())inline(n,out);
                if(vertical.equals("subscript"))out.append("</sub>");
                if(vertical.equals("superscript"))out.append("</sup>");
                if(strike)out.append("</s>");
                if(under)out.append("</u>");
                if(italic)out.append("</em>");
                if(bold)out.append("</strong>");
                return;
            }
            if("hyperlink".equals(local)){
                out.append("<span class=\"fg-docx-link\">");
                for(Node n=e.getFirstChild();n!=null;n=n.getNextSibling())inline(n,out);
                out.append("</span>");
                return;
            }
            if("drawing".equals(local)){embeddedImages(e,out);return;}
        }
        for(Node n=e.getFirstChild();n!=null;n=n.getNextSibling())inline(n,out);
    }

    private void embeddedImages(Element e,StringBuilder out){
        NodeList blips=e.getElementsByTagNameNS(A,"blip");
        for(int i=0;i<blips.getLength();i++){
            Element blip=(Element)blips.item(i);
            String path=images.get(blip.getAttributeNS(R,"embed"));
            if(path==null)continue;
            byte[] image=pkg.entries.get(path);
            if(image==null||image.length>2_000_000){
                out.append("<span class=\"fg-docx-image-fallback\">[Embedded image too large to preview]</span>");
                continue;
            }
            String ext=path.substring(path.lastIndexOf('.')+1).toLowerCase(Locale.ROOT);
            String mime=ext.equals("jpg")||ext.equals("jpeg")?"image/jpeg":
                ext.equals("png")?"image/png":ext.equals("gif")?"image/gif":
                ext.equals("webp")?"image/webp":"";
            if(mime.isEmpty())continue;
            out.append("<img loading=\"lazy\" alt=\"Document image\" src=\"data:")
                .append(mime).append(";base64,")
                .append(java.util.Base64.getEncoder().encodeToString(image)).append("\">");
        }
    }

    private static boolean enabled(Element parent,String local){
        Element element=parent==null?null:first(parent,local);
        if(element==null)return false;
        String value=element.getAttributeNS(W,"val");
        return !value.equals("0")&&!value.equalsIgnoreCase("false")&&
            !value.equalsIgnoreCase("none");
    }

    private static int intAttr(Element element,String local,int fallback){
        if(element==null)return fallback;
        try{return Integer.parseInt(element.getAttributeNS(W,local));}
        catch(Exception ignored){return fallback;}
    }

    private static Element first(Element parent,String local){
        if(parent==null)return null;
        for(Node n=parent.getFirstChild();n!=null;n=n.getNextSibling())
            if(n instanceof Element && W.equals(n.getNamespaceURI()) && local.equals(n.getLocalName()))
                return (Element)n;
        return null;
    }

    private static List<Element> direct(Element parent,String local){
        List<Element> out=new ArrayList<>();
        for(Node n=parent.getFirstChild();n!=null;n=n.getNextSibling())
            if(n instanceof Element && W.equals(n.getNamespaceURI()) && local.equals(n.getLocalName()))
                out.add((Element)n);
        return out;
    }

    private static String escape(String raw){
        return raw.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
            .replace("\"","&quot;").replace("'","&#39;");
    }
}
