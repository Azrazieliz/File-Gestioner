package com.openlocal.office.core;

import java.io.*;
import java.util.Locale;
import org.apache.poi.hssf.usermodel.HSSFWorkbook;
import org.apache.poi.ss.usermodel.*;
import org.apache.poi.hwpf.extractor.WordExtractor;

/**
 * Offline legacy Microsoft Office readers. Does not alter the original file.
 * DOC uses the Word text model; XLS emits sheet/row/cell values as readable TSV.
 * Only editable OpenXML sessions (DOCX/XLSX) retain round-trip editing.
 */
public final class LegacyOfficeReader {
    private static final int MAX_CHARS=3_000_000;
    private LegacyOfficeReader(){}

    public static String read(byte[] original,String kind)throws Exception {
        if(original==null||original.length==0||original.length>60_000_000)
            throw new IOException("Legacy document is empty or beyond the supported size.");
        if("doc".equals(kind)){
            try(WordExtractor extractor=new WordExtractor(new ByteArrayInputStream(original))){
                String text=extractor.getText();
                if(text==null||text.isBlank())throw new IOException("Legacy DOC has no readable body text");
                if(text.length()>MAX_CHARS)throw new IOException("Word text exceeds safe preview limit");
                return text;
            }
        }
        if("xls".equals(kind)){
            StringBuilder out=new StringBuilder();
            try(HSSFWorkbook wb=new HSSFWorkbook(new ByteArrayInputStream(original))){
                DataFormatter fmt=new DataFormatter(Locale.ROOT);
                for(int s=0;s<wb.getNumberOfSheets();s++){
                    Sheet sheet=wb.getSheetAt(s);
                    out.append("\n\nSHEET: ").append(sheet.getSheetName()).append("\n");
                    int rows=0;
                    for(Row row:sheet){
                        if(++rows>100000)throw new IOException("Spreadsheet exceeds safe row limit");
                        int first=Math.max(0,row.getFirstCellNum());
                        int last=Math.min(1024,Math.max(first,row.getLastCellNum()));
                        for(int c=first;c<last;c++){
                            if(c>first)out.append('\t');
                            Cell cell=row.getCell(c);
                            if(cell!=null)out.append(fmt.formatCellValue(cell)
                                .replace("\t"," ").replace("\r"," ").replace("\n"," "));
                        }
                        out.append('\n');
                        if(out.length()>MAX_CHARS)throw new IOException("Workbook text exceeds safe preview limit");
                    }
                }
            }
            return out.length()==0?"The workbook contains no readable cells":out.toString().trim();
        }
        throw new IOException("Unsupported legacy document format");
    }
}
