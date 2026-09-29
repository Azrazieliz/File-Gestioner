package com.openlocal.office.core;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.*;
import java.util.zip.*;

/**
 * Editable Samsung Notes SDOCX text-flow session.
 *
 * The class edits document-level flowing text stored in note.note while
 * preserving the rest of the archive. Rich-text span and paragraph records are
 * retained and their UTF-16/paragraph ranges are shifted as text is edited.
 * Embedded text-flow objects are still opened for reading, but are kept
 * read-only because rewriting their anchors safely requires a fuller writer.
 */
public final class SdocxSession {
    private final byte[] sourceArchive;
    private final NoteTemplate template;
    private String text;

    private SdocxSession(byte[] sourceArchive, NoteTemplate template) {
        this.sourceArchive = sourceArchive;
        this.template = template;
        this.text = template.text;
    }

    public static SdocxSession open(byte[] archiveBytes) throws Exception {
        if (archiveBytes == null || archiveBytes.length < 4) throw new IOException("Empty SDOCX file.");
        byte[] note = readEntry(archiveBytes, "note.note");
        if (note == null) throw new IOException("SDOCX archive has no note.note entry.");
        byte[] manifest = readEntry(archiveBytes, "pageIdInfo.dat");
        if (manifest == null || manifest.length < 34) throw new IOException("SDOCX archive has no valid pageIdInfo.dat entry.");
        return new SdocxSession(Arrays.copyOf(archiveBytes, archiveBytes.length), NoteTemplate.parse(note));
    }

    public static void validate(byte[] archiveBytes) throws Exception {
        SdocxSession session = open(archiveBytes);
        byte[] note = readEntry(archiveBytes, "note.note");
        if (note == null || note.length < 32) throw new IOException("Invalid SDOCX note entry.");
        byte[] expected = Arrays.copyOfRange(note, note.length - 32, note.length);
        byte[] actual = sha256(Arrays.copyOf(note, note.length - 32));
        if (!Arrays.equals(expected, actual)) throw new IOException("SDOCX note checksum is invalid.");
        byte[] manifest = readEntry(archiveBytes, "pageIdInfo.dat");
        if (manifest == null || manifest.length < 32 || !Arrays.equals(expected, Arrays.copyOf(manifest, 32))) {
            throw new IOException("SDOCX manifest does not reference the current note checksum.");
        }
        session.text();
    }

    public String text() { return text; }
    public boolean editable() { return !template.hasEmbeddedObjects; }

    public void setText(String value) {
        String next = value == null ? "" : value;
        if (next.equals(text)) return;
        if (!editable()) throw new IllegalStateException("This SDOCX contains embedded rich-text objects and is read-only to avoid damaging them.");
        template.applyTextEdit(text, next);
        text = next;
    }

    public byte[] serialize() throws Exception {
        if (!editable() && !text.equals(template.text)) {
            throw new IOException("This SDOCX contains embedded rich-text objects and cannot be rewritten safely.");
        }
        if (!editable()) return Arrays.copyOf(sourceArchive, sourceArchive.length);
        byte[] originalNote = readEntry(sourceArchive, "note.note");
        if (originalNote == null) throw new IOException("SDOCX archive has no note.note entry.");
        RewriteResult rewritten = template.rewrite(originalNote, text);
        byte[] result = rewriteArchive(sourceArchive, rewritten.note, rewritten.digest);
        validate(result);
        return result;
    }

    private static byte[] rewriteArchive(byte[] archive, byte[] newNote, byte[] noteDigest) throws Exception {
        ByteArrayOutputStream out = new ByteArrayOutputStream(Math.max(archive.length, newNote.length / 2));
        boolean sawNote = false, sawManifest = false;
        try (ZipInputStream zin = new ZipInputStream(new ByteArrayInputStream(archive));
             ZipOutputStream zout = new ZipOutputStream(out)) {
            for (ZipEntry inEntry; (inEntry = zin.getNextEntry()) != null;) {
                byte[] bytes = readAll(zin);
                if ("note.note".equals(inEntry.getName())) {
                    bytes = newNote;
                    sawNote = true;
                } else if ("pageIdInfo.dat".equals(inEntry.getName())) {
                    if (bytes.length < 32) throw new IOException("Invalid SDOCX page manifest.");
                    bytes = Arrays.copyOf(bytes, bytes.length);
                    System.arraycopy(noteDigest, 0, bytes, 0, 32);
                    sawManifest = true;
                }
                ZipEntry e = new ZipEntry(inEntry.getName());
                if (inEntry.getTime() >= 0) e.setTime(inEntry.getTime());
                if (inEntry.getComment() != null) e.setComment(inEntry.getComment());
                if (inEntry.getExtra() != null) e.setExtra(inEntry.getExtra());
                int method = inEntry.getMethod();
                if (method == ZipEntry.STORED) {
                    CRC32 crc = new CRC32(); crc.update(bytes);
                    e.setMethod(ZipEntry.STORED);
                    e.setSize(bytes.length);
                    e.setCompressedSize(bytes.length);
                    e.setCrc(crc.getValue());
                } else {
                    e.setMethod(ZipEntry.DEFLATED);
                }
                zout.putNextEntry(e);
                zout.write(bytes);
                zout.closeEntry();
                zin.closeEntry();
            }
        }
        if (!sawNote || !sawManifest) throw new IOException("Incomplete SDOCX archive.");
        return out.toByteArray();
    }

    private static byte[] readEntry(byte[] archive, String wanted) throws IOException {
        try (ZipInputStream zin = new ZipInputStream(new ByteArrayInputStream(archive))) {
            for (ZipEntry e; (e = zin.getNextEntry()) != null;) {
                if (wanted.equals(e.getName())) return readAll(zin);
                zin.closeEntry();
            }
        }
        return null;
    }

    private static byte[] readAll(InputStream in) throws IOException {
        ByteArrayOutputStream out = new ByteArrayOutputStream();
        byte[] buf = new byte[64 * 1024];
        for (int n; (n = in.read(buf)) != -1;) out.write(buf, 0, n);
        return out.toByteArray();
    }

    private static byte[] sha256(byte[] bytes) throws Exception {
        return MessageDigest.getInstance("SHA-256").digest(bytes);
    }

    private static int u8(byte[] b, int o) throws IOException { need(b,o,1); return b[o]&0xff; }
    private static int u16(byte[] b, int o) throws IOException { need(b,o,2); return (b[o]&0xff)|((b[o+1]&0xff)<<8); }
    private static long u32(byte[] b, int o) throws IOException {
        need(b,o,4); return ((long)b[o]&0xff)|(((long)b[o+1]&0xff)<<8)|(((long)b[o+2]&0xff)<<16)|(((long)b[o+3]&0xff)<<24);
    }
    private static int i16(byte[] b, int o) throws IOException { return (short)u16(b,o); }
    private static void need(byte[] b,int o,int n)throws IOException{if(o<0||n<0||o>b.length-n)throw new IOException("Truncated SDOCX binary record.");}
    private static int checkedInt(long value,String field)throws IOException{if(value<0||value>Integer.MAX_VALUE)throw new IOException("SDOCX "+field+" is too large.");return(int)value;}
    private static int skipMask(byte[] b,int o)throws IOException{int n=u8(b,o);need(b,o+1,n);return o+1+n;}
    private static int skipUtf16U16(byte[] b,int o)throws IOException{int units=u16(b,o);if(units==0xffff)return o+2;return checkedInt((long)o+2L+(long)units*2L,"string");}
    private static void writeU16(ByteArrayOutputStream out,int v){out.write(v&0xff);out.write((v>>>8)&0xff);}
    private static void writeU32(ByteArrayOutputStream out,long v){out.write((int)v&0xff);out.write((int)(v>>>8)&0xff);out.write((int)(v>>>16)&0xff);out.write((int)(v>>>24)&0xff);}
    private static void putU32(byte[] b,int o,long v)throws IOException{need(b,o,4);b[o]=(byte)v;b[o+1]=(byte)(v>>>8);b[o+2]=(byte)(v>>>16);b[o+3]=(byte)(v>>>24);}

    private static final class FrameInfo {
        int start,size,kind,flexStart,end;
        FrameInfo(int start,int size,int kind,int flexStart,int end){this.start=start;this.size=size;this.kind=kind;this.flexStart=flexStart;this.end=end;}
    }
    private static FrameInfo frame(byte[] body,int start)throws IOException{
        int size=checkedInt(u32(body,start),"frame size");
        if(size<12||start>body.length-size)throw new IOException("Invalid SDOCX frame size.");
        int kind=i16(body,start+4), flexibleOffset=checkedInt(u32(body,start+6),"frame flexible offset");
        int p=start+10;int propCount=u8(body,p);p++;need(body,p,propCount);p+=propCount;int fieldCount=u8(body,p);p++;need(body,p,fieldCount);
        boolean fieldsEmpty=true;for(int i=0;i<fieldCount;i++)if(body[p+i]!=0){fieldsEmpty=false;break;}p+=fieldCount;
        int fixedEndRel=(flexibleOffset==0&&fieldsEmpty)?size:flexibleOffset;
        if(fixedEndRel<p-start||fixedEndRel>size)throw new IOException("Invalid SDOCX frame offset.");
        return new FrameInfo(start,size,kind,start+fixedEndRel,start+size);
    }

    private static final class RawRangeRecord {
        final byte[] bytes;
        final boolean paragraph;
        RawRangeRecord(byte[] bytes,boolean paragraph){this.bytes=bytes;this.paragraph=paragraph;}
        int start()throws IOException{return checkedInt(u32(bytes,4),"text range");}
        int end()throws IOException{return checkedInt(u32(bytes,8),"text range");}
        void shift(int editStart,int oldEnd,int newEnd)throws IOException{
            int s=start(),e=end();
            int ns=mapStart(s,editStart,oldEnd,newEnd),ne=mapEnd(e,editStart,oldEnd,newEnd);
            if(ne<ns)ne=ns;putU32(bytes,4,ns);putU32(bytes,8,ne);
        }
    }
    private static final class Section {
        int start,length;
        Section(int start,int length){this.start=start;this.length=length;}
        void shift(int editStart,int oldEnd,int newEnd){int e=start+length;int ns=mapStart(start,editStart,oldEnd,newEnd),ne=mapEnd(e,editStart,oldEnd,newEnd);if(ne<ns)ne=ns;start=ns;length=ne-ns;}
    }
    private static int mapStart(int p,int editStart,int oldEnd,int newEnd){if(p<=editStart)return p;if(p>=oldEnd)return p+(newEnd-oldEnd);return editStart;}
    private static int mapEnd(int p,int editStart,int oldEnd,int newEnd){if(p<=editStart)return p;if(p>=oldEnd)return p+(newEnd-oldEnd);return newEnd;}
    private static int countNewlines(String s,int from,int to){int n=0;for(int i=Math.max(0,from),e=Math.min(s.length(),to);i<e;i++)if(s.charAt(i)=='\n')n++;return n;}

    private static final class NoteTemplate {
        final String text;
        final int flexibleOffset,bodySizePos,bodyStart,bodyEnd,frameStart,frameFlexStart,frameEnd;
        final byte[] marginAndGravity,postSections,frameFlexSuffix;
        final ArrayList<RawRangeRecord> spans,paragraphs;
        final ArrayList<Section> sections;
        final boolean hasEmbeddedObjects;

        NoteTemplate(String text,int flexibleOffset,int bodySizePos,int bodyStart,int bodyEnd,int frameStart,int frameFlexStart,int frameEnd,
                     byte[] marginAndGravity,ArrayList<RawRangeRecord> spans,ArrayList<RawRangeRecord> paragraphs,ArrayList<Section> sections,
                     byte[] postSections,byte[] frameFlexSuffix,boolean hasEmbeddedObjects){
            this.text=text;this.flexibleOffset=flexibleOffset;this.bodySizePos=bodySizePos;this.bodyStart=bodyStart;this.bodyEnd=bodyEnd;
            this.frameStart=frameStart;this.frameFlexStart=frameFlexStart;this.frameEnd=frameEnd;this.marginAndGravity=marginAndGravity;
            this.spans=spans;this.paragraphs=paragraphs;this.sections=sections;this.postSections=postSections;this.frameFlexSuffix=frameFlexSuffix;
            this.hasEmbeddedObjects=hasEmbeddedObjects;
        }

        static NoteTemplate parse(byte[] note)throws Exception{
            if(note.length<64)throw new IOException("Invalid SDOCX note header.");
            int trailerStart=note.length-32;byte[] stored=Arrays.copyOfRange(note,trailerStart,note.length),computed=sha256(Arrays.copyOf(note,trailerStart));
            if(!Arrays.equals(stored,computed))throw new IOException("SDOCX note checksum is invalid.");
            int o=0,flex=checkedInt(u32(note,o),"note flexible offset");o+=4;o=skipMask(note,o);o=skipMask(note,o);need(note,o,4);o+=4;o=skipUtf16U16(note,o);
            need(note,o,4+8+8+4*5);o+=4+8+8+4*5;int titleSize=checkedInt(u32(note,o),"title size");o+=4;need(note,o,titleSize);o+=titleSize;
            int bodySizePos=o,bodySize=checkedInt(u32(note,o),"body size");o+=4;int bodyStart=o,bodyEnd=bodyStart+bodySize;need(note,bodyStart,bodySize);
            if(flex<bodyEnd||flex>trailerStart)throw new IOException("Invalid SDOCX note offsets.");
            byte[] body=Arrays.copyOfRange(note,bodyStart,bodyEnd);FrameInfo textFrame=null;int p=0;
            while(p<body.length){FrameInfo f=frame(body,p);if(f.kind==7){textFrame=f;break;}p=f.end;}
            if(textFrame==null)throw new IOException("SDOCX note body has no text frame.");
            int commonSize=checkedInt(u32(body,textFrame.flexStart),"text common size"),commonStart=textFrame.flexStart+4,commonEnd=commonStart+commonSize;need(body,commonStart,commonSize);
            int c=commonStart,textUnits=checkedInt(u32(body,c),"text length");c+=4;int textBytes=checkedInt((long)textUnits*2L,"text byte length");need(body,c,textBytes);
            String text=new String(body,c,textBytes,StandardCharsets.UTF_16LE);c+=textBytes;
            int spanCount=checkedInt(u32(body,c),"style span count");c+=4;ArrayList<RawRangeRecord> spans=new ArrayList<>(spanCount);
            for(int i=0;i<spanCount;i++){int n=u16(body,c);c+=2;need(body,c,n);byte[] rec=Arrays.copyOfRange(body,c,c+n);if(n<16)throw new IOException("Invalid SDOCX style span.");spans.add(new RawRangeRecord(rec,false));c+=n;}
            int paraCount=checkedInt(u32(body,c),"paragraph count");c+=4;ArrayList<RawRangeRecord> paras=new ArrayList<>(paraCount);
            for(int i=0;i<paraCount;i++){int n=u16(body,c);c+=2;need(body,c,n);byte[] rec=Arrays.copyOfRange(body,c,c+n);if(n<12)throw new IOException("Invalid SDOCX paragraph record.");paras.add(new RawRangeRecord(rec,true));c+=n;}
            need(body,c,17);byte[] mg=Arrays.copyOfRange(body,c,c+17);c+=17;ArrayList<Section> sections=new ArrayList<>();
            if(c+2<=commonEnd){int sc=u16(body,c);c+=2;for(int i=0;i<sc;i++){need(body,c,8);sections.add(new Section(checkedInt(u32(body,c),"section start"),checkedInt(u32(body,c+4),"section length")));c+=8;}}
            int postStart=c;boolean embedded=false;if(c+8<=commonEnd){long flags=u32(body,c);embedded=(flags&1L)!=0;}
            byte[] post=Arrays.copyOfRange(body,postStart,commonEnd);byte[] suffix=Arrays.copyOfRange(body,commonEnd,textFrame.end);
            return new NoteTemplate(text,flex,bodySizePos,bodyStart,bodyEnd,textFrame.start,textFrame.flexStart,textFrame.end,mg,spans,paras,sections,post,suffix,embedded);
        }

        void applyTextEdit(String oldText,String newText){
            int prefix=0,max=Math.min(oldText.length(),newText.length());while(prefix<max&&oldText.charAt(prefix)==newText.charAt(prefix))prefix++;
            if(prefix>0&&prefix<oldText.length()&&Character.isHighSurrogate(oldText.charAt(prefix-1))&&Character.isLowSurrogate(oldText.charAt(prefix)))prefix--;
            int oldEnd=oldText.length(),newEnd=newText.length();while(oldEnd>prefix&&newEnd>prefix&&oldText.charAt(oldEnd-1)==newText.charAt(newEnd-1)){oldEnd--;newEnd--;}
            if(oldEnd<oldText.length()&&oldEnd>0&&Character.isLowSurrogate(oldText.charAt(oldEnd))&&Character.isHighSurrogate(oldText.charAt(oldEnd-1)))oldEnd--;
            if(newEnd<newText.length()&&newEnd>0&&Character.isLowSurrogate(newText.charAt(newEnd))&&Character.isHighSurrogate(newText.charAt(newEnd-1)))newEnd--;
            try{for(RawRangeRecord r:spans)r.shift(prefix,oldEnd,newEnd);}catch(IOException e){throw new IllegalStateException(e);}
            int oldParaStart=countNewlines(oldText,0,prefix),oldParaEnd=oldParaStart+countNewlines(oldText,prefix,oldEnd),newParaEnd=oldParaStart+countNewlines(newText,prefix,newEnd);
            try{for(RawRangeRecord r:paragraphs)r.shift(oldParaStart,oldParaEnd,newParaEnd);}catch(IOException e){throw new IllegalStateException(e);}
            for(Section section:sections)section.shift(prefix,oldEnd,newEnd);
        }

        RewriteResult rewrite(byte[] note,String value)throws Exception{
            byte[] body=Arrays.copyOfRange(note,bodyStart,bodyEnd),utf16=value.getBytes(StandardCharsets.UTF_16LE);
            ByteArrayOutputStream common=new ByteArrayOutputStream(utf16.length+128+spans.size()*24+paragraphs.size()*24+sections.size()*8);
            writeU32(common,value.length());common.write(utf16);writeU32(common,spans.size());
            for(RawRangeRecord r:spans){writeU16(common,r.bytes.length);common.write(r.bytes);}writeU32(common,paragraphs.size());
            for(RawRangeRecord r:paragraphs){writeU16(common,r.bytes.length);common.write(r.bytes);}common.write(marginAndGravity);writeU16(common,sections.size());
            for(Section s:sections){writeU32(common,s.start);writeU32(common,s.length);}common.write(postSections);byte[] commonBytes=common.toByteArray();
            ByteArrayOutputStream flexOut=new ByteArrayOutputStream(commonBytes.length+frameFlexSuffix.length+4);writeU32(flexOut,commonBytes.length);flexOut.write(commonBytes);flexOut.write(frameFlexSuffix);byte[] flexBytes=flexOut.toByteArray();
            ByteArrayOutputStream f7=new ByteArrayOutputStream((frameFlexStart-frameStart)+flexBytes.length);f7.write(body,frameStart,frameFlexStart-frameStart);f7.write(flexBytes);byte[] f7Bytes=f7.toByteArray();putU32(f7Bytes,0,f7Bytes.length);
            ByteArrayOutputStream bodyOut=new ByteArrayOutputStream(body.length+Math.max(0,f7Bytes.length-(frameEnd-frameStart)));bodyOut.write(body,0,frameStart);bodyOut.write(f7Bytes);bodyOut.write(body,frameEnd,body.length-frameEnd);byte[] newBody=bodyOut.toByteArray();int delta=newBody.length-body.length;
            int trailerStart=note.length-32;ByteArrayOutputStream payloadOut=new ByteArrayOutputStream(note.length+delta);payloadOut.write(note,0,bodySizePos);writeU32(payloadOut,newBody.length);payloadOut.write(newBody);payloadOut.write(note,bodyEnd,trailerStart-bodyEnd);byte[] payload=payloadOut.toByteArray();putU32(payload,0,(long)flexibleOffset+delta);byte[] digest=sha256(payload);
            ByteArrayOutputStream finalNote=new ByteArrayOutputStream(payload.length+32);finalNote.write(payload);finalNote.write(digest);return new RewriteResult(finalNote.toByteArray(),digest);
        }
    }

    private static final class RewriteResult { final byte[] note,digest;RewriteResult(byte[] note,byte[] digest){this.note=note;this.digest=digest;} }
}
