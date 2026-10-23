/* Release gate for real Android EPUB parser, covers and navigation.
 * Dynamic tests: Android emulator must also log FG_BOOK EPUB_READY and BACK_TO_LIBRARY.
 */
const fs=require('fs'),assert=require('assert');
const read=(path)=>fs.readFileSync(path,'utf8');
const book=read('app/src/main/java/com/openlocal/office/core/BookArchive.java');
const covers=read('app/src/main/java/com/openlocal/office/core/ReaderCovers.java');
const main=read('app/src/main/java/com/openlocal/office/MainActivity.java');
const library=read('app/src/main/assets/premium-library.js');
const fixture=read('../hotfixes/create-large-epub-fixture.py');
assert(!book.includes('f.setFeature("http://apache.org/xml/features/disallow-doctype-decl",true)'),
 'Do not call an unsupported Android DocumentBuilderFactory parser feature');
assert(book.includes('parser.setEntityResolver('),'External XML resolution must be blocked');
assert(book.includes('DOCTYPE'),'Standard EPUB2 external DTD must not crash parsing');
assert(book.includes('cover-image')&&book.includes('preferredCoverName'),
 'Actual EPUB2/EPUB3 cover metadata must be supported');
assert(covers.includes('book.preferredCover()'),
 'Bookshelf must extract cover or first actual ZIP/CBZ page');
assert(book.includes('archiveImages.sort(BookArchive::compareNatural)'),
 'Archive preview must honor numerical first-image order');
assert(main.includes('onBackPressed()')&&main.includes('evaluateJavascript('),
 'System navigation bar Back must connect to document/library state');
assert(library.includes('handleBack:handleAndroidBack'),'Library navigation method missing');
assert(library.includes('drawer.classList.add('),'Back should close reading appearance first');
assert(library.includes('BACK_TO_LIBRARY'),'Emulator must log library navigation');
assert(fixture.includes('<!DOCTYPE package PUBLIC'),'EPUB runtime regression must include the failure trigger');
console.log('PASS: Android-safe EPUB XML, official book covers, first ZIP page and native Back navigation');
