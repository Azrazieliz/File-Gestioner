#!/usr/bin/env python3
"""Create a synthetic, public-domain-free EPUB smoke fixture >80 MiB.
Not shipped in the APK. No source book or copyrighted assets used.
"""
from pathlib import Path
from zipfile import ZipFile,ZIP_STORED,ZIP_DEFLATED
import struct,zlib,sys

output=Path(sys.argv[1]) if len(sys.argv)>1 else Path("epub-fixture.epub")
output.parent.mkdir(parents=True,exist_ok=True)
def illustration(width=480,height=600):
    # Synthetic test illustration using only Python's standard library.
    raw=bytearray()
    for y in range(height):
        raw.append(0)
        r=round(36+55*y/height);g=round(52+15*y/height);b=round(102+31*y/height)
        raw.extend(bytes((r,g,b))*width)
    def chunk(t,data):
        return struct.pack(">I",len(data))+t+data+struct.pack(">I",zlib.crc32(t+data)&0xffffffff)
    return b"\x89PNG\r\n\x1a\n"+chunk(b"IHDR",struct.pack(">IIBBBBB",width,height,8,2,0,0,0))+chunk(b"IDAT",zlib.compress(bytes(raw),6))+chunk(b"IEND",b"")

container='''<?xml version="1.0" encoding="UTF-8"?>
<container xmlns="urn:oasis:names:tc:opendocument:xmlns:container" version="1.0">
<rootfiles><rootfile full-path="OPS/package.opf" media-type="application/oebps-package+xml"/></rootfiles>
</container>'''
opf='''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE package PUBLIC "-//IDPF//DTD OPF 2.0//EN" "http://www.idpf.org/dtds/2007/opf.dtd">
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="id">
<metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
<dc:identifier id="id">urn:uuid:fixture-professional-reader</dc:identifier>
<dc:title>Sample Book · Premium Reader Test</dc:title>
<dc:creator>File Gestioner CI</dc:creator><dc:language>en</dc:language>
</metadata>
<manifest>
<item id="cover" href="Text/cover.xhtml" media-type="application/xhtml+xml"/>
<item id="chapter" href="Text/chapter.xhtml" media-type="application/xhtml+xml"/>
<item id="image" href="Images/cover.png" media-type="image/png"/>
<item id="blob" href="Unused/large.bin" media-type="application/octet-stream"/>
</manifest>
<spine><itemref idref="cover"/><itemref idref="chapter"/></spine>
</package>'''
cover='''<html xmlns="http://www.w3.org/1999/xhtml"><head><title>Illustrations</title></head>
<body><h1>Illustrations</h1><figure><img src="../Images/cover.png" alt="Synthetic illustration"/></figure></body></html>'''
chapter='''<html xmlns="http://www.w3.org/1999/xhtml"><head><title>The First Chapter</title></head>
<body><h1>The First Chapter</h1><p>The reader should preserve the original paragraph structure,
rather than inserting XHTML filenames or showing a developer-oriented file dump.</p>
<p>Choose a comfortable theme, font, size, spacing and margins, then read continuously.</p>
<p>Images remain local and load on demand as you scroll through the book.</p></body></html>'''
with ZipFile(output,'w',allowZip64=True) as z:
    z.writestr('mimetype','application/epub+zip',compress_type=ZIP_STORED)
    z.writestr('META-INF/container.xml',container,compress_type=ZIP_DEFLATED)
    z.writestr('OPS/package.opf',opf,compress_type=ZIP_DEFLATED)
    z.writestr('OPS/Text/cover.xhtml',cover,compress_type=ZIP_DEFLATED)
    z.writestr('OPS/Text/chapter.xhtml',chapter,compress_type=ZIP_DEFLATED)
    z.writestr('OPS/Images/cover.png',illustration(),compress_type=ZIP_STORED)
    with z.open('OPS/Unused/large.bin','w',force_zip64=True) as out:
        chunk=b'\0'*(1024*1024)
        for _ in range(86):out.write(chunk)
assert output.stat().st_size>80*1024*1024
print("Synthetic EPUB smoke fixture:",output.stat().st_size,"bytes")
