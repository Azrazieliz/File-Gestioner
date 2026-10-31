/* Build gate: image folders must reach their actual renderer; cloud videos
 * must start playback before the entire copy has completed.
 */
const fs=require('fs'),assert=require('assert'),vm=require('vm');
const js=fs.readFileSync('app/src/main/assets/reader-controls.js','utf8');
const lib=fs.readFileSync('app/src/main/assets/premium-library.js','utf8');
const main=fs.readFileSync('app/src/main/java/com/openlocal/office/MainActivity.java','utf8');
const media=fs.readFileSync('app/src/main/java/com/openlocal/office/core/FgMediaPlayer.java','utf8');
const growing=fs.readFileSync('app/src/main/java/com/openlocal/office/core/FgGrowingMediaDataSource.java','utf8');
assert(!lib.includes("if(item.folder){\n   bridge()?.openImageFolder"),'Folder overlay is still blocking image pages');
assert(lib.includes("root.classList.add('fg-lib-hidden');\n   visible=false;"),'Folder must hide library before loading');
assert(js.includes("if(data?.type==='folderImages'){"),'Special folder route absent');
const block=js.slice(js.indexOf("window.loadDocument=function(data){"));
assert(block.indexOf("renderImageFolder(data);")<block.indexOf("upstream.apply(this,arguments)"),
  'Generic loader must not run before folder image reader');
assert(js.includes('window.FileGestionerFolder='),'Dynamic image batches missing');
assert(js.includes("stack.insertBefore(frag,sentinel)"),'On-screen pages not appended');
assert(main.includes('fgFolderPageMap'),'Native folder images route missing');
assert(main.includes('fgFolderToken'),'Native folder token missing');
assert(main.includes('FgMediaPlayer'),'Media3 playback missing');
assert(media.includes('player.setMediaSource(new ProgressiveMediaSource.Factory(factory)'),
  'Growing cache is not connected to playback');
assert(media.indexOf('play(original)')<media.indexOf('private void copyThenPlay'),
  'Direct playback should be attempted first');
assert(media.includes('state.available=written;')&&media.includes('state.wake()'),
  'DataSource cannot see downloaded video bytes');
assert(growing.includes('state.available-position')&&growing.includes('state.finished'),
  'Growing file reader cannot return pages while receiving file');
const lower=main.indexOf('String lowerMediaName=name.toLowerCase(java.util.Locale.ROOT);');
const sniff=main.indexOf('String quickType = detectType(uri, name);');
assert(lower!==-1&&sniff!==-1&&lower<sniff,
  'MP4 must be opened without slow image/content sniffing');
const libFile=fs.readFileSync('app/src/main/java/com/openlocal/office/core/ReaderLibrary.java','utf8');
assert(libFile.includes('public static Listing stream('),'Incremental folder enumeration missing');
assert(libFile.includes('if(batch.length()>=96)'),'Directory chunking missing');
assert(!libFile.includes('if(++total>=PAGE_SIZE)break;') ||
       main.includes('ReaderLibrary.stream(this,root,folder'),
       'Library still truncates folders at 500 files');
// The native folder reader is not the generic loader: it must reveal #editor.
assert(js.includes("editor.classList.remove('hidden');"),'Image folder editor stays hidden');
const folderPatch=fs.readFileSync('../hotfixes/apply-streamed-image-folders-20261031.py','utf8');
assert(folderPatch.includes("DocumentsContract.getTreeDocumentId(libraryTree)"),
  'Folder access still depends on transient listing state');
const style=fs.readFileSync('app/src/main/assets/style.css','utf8');
assert(style.includes('display:block!important;height:100%!important;min-height:0!important'),
  'Folder editor does not fill the reading viewport');
assert(media.includes('SCREEN_ORIENTATION_SENSOR_LANDSCAPE'),'Video must rotate to landscape');
assert(media.includes('SYSTEM_UI_FLAG_IMMERSIVE_STICKY'),'Video must hide system bars');
assert(media.includes('direction*10000L'),'Left/right double tap must skip ten seconds');
assert(media.includes('setShowRewindButton(false)')&&media.includes('setShowFastForwardButton(false)'),
  'Video must remove old ten-second buttons');
assert(media.includes('if(video)leaveVideoFullscreen()'),'Video must restore normal orientation');
console.log('PASS: image folder visible, streamed pages, direct MP4 and growing cache byte reads.');
