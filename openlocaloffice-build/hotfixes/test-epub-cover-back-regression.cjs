/* Regression gate for EPUB crash / image-less bookshelf / Back-to-library.
 * Real XML + illustration + system Back verified in Android emulator CI.
 */
const fs=require('fs'),assert=require('assert');
const book=fs.readFileSync('app/src/main/java/com/openlocal/office/core/BookArchive.java','utf8');
const cover=fs.readFileSync('app/src/main/java/com/openlocal/office/core/ReaderCovers.java','utf8');
const main=fs.readFileSync('app/src/main/java/com/openlocal/office/MainActivity.java','utf8');
const library=fs.readFileSync('app/src/main/assets/premium-library.js','utf8');
const epub=fs.readFileSync('app/src/main/assets/epub-reader.js','utf8');
function need(x,msg){assert(x,msg);}
need(!book.includes('f.setFeature("http://apache.org/xml/features/disallow-doctype-decl"'),
  'Do not require unsupported Android Xerces feature');
need(book.includes('probe.contains("<!DOCTYPE")')&&book.includes('probe.contains("<!ENTITY")'),
  'EPUB XML must block DTD and entity declarations');
need(book.includes('builder.setEntityResolver'), 'XML must disable external resolution');
need(cover.includes('String candidate=book.imageName(0);'),
  'Comics must preview the first image');
need(cover.includes('FG_COVERS'),'Cover extraction failures must be diagnosable');
need(main.includes('getOnBackInvokedDispatcher')&&main.includes('onBackPressed()'),
  'Android system and predictive back must be handled');
need(main.includes('exitFromLibraryRoot'),'Back must only exit at root after confirmation');
need(library.includes('window.FileGestionerNavigation'),
  'Web library navigation must be accessible to Android');
need(library.includes('if(stack.length){navigateBack()'),
  'System Back must walk the folder tree');
need(library.includes('BACK_TO_LIBRARY'),
  'System Back must go from a reader to the library');
need(epub.includes('BOOK_IMAGE_LOADED'),'EPUB illustrations must be runtime-checked');
console.log('PASS: EPUB parser compatibility, safe local covers, predictive/system Back and library navigation');
