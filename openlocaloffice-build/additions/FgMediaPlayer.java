package com.openlocal.office.core;

import android.app.Activity;
import android.net.Uri;
import android.os.StatFs;
import android.util.Log;
import android.view.Gravity;
import android.view.View;
import android.widget.Button;
import android.widget.FrameLayout;
import android.widget.TextView;
import androidx.media3.common.MediaItem;
import androidx.media3.common.PlaybackException;
import androidx.media3.common.Player;
import androidx.media3.exoplayer.ExoPlayer;
import androidx.media3.ui.PlayerView;
import java.io.*;
import java.security.MessageDigest;
import java.util.Locale;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/** Android media playback for SAF content, including provider streams.
 * Never blocks the UI on a cloud download. ExoPlayer streams when possible;
 * if a provider cannot seek, a single cached copy is tried automatically.
 */
@androidx.media3.common.util.UnstableApi
public final class FgMediaPlayer implements AutoCloseable {
    private final Activity activity;
    private final FrameLayout root;
    private final TextView status;
    private final ExoPlayer player;
    private final ExecutorService io=Executors.newSingleThreadExecutor();
    private volatile boolean closed;
    private volatile boolean fallbackStarted;
    private volatile int session=1;
    private Uri original;
    private String filename;
    private boolean video;
    private final Runnable onExit;

    public FgMediaPlayer(Activity activity,Uri original,String filename,
                         boolean video,Runnable onExit){
        this.activity=activity;this.original=original;this.filename=filename;
        this.video=video;this.onExit=onExit;
        root=new FrameLayout(activity);
        root.setBackgroundColor(0xff090c13);
        PlayerView display=new PlayerView(activity);
        display.setUseController(true);
        FrameLayout.LayoutParams videoLayout=new FrameLayout.LayoutParams(-1,-1);
        videoLayout.gravity=Gravity.CENTER;
        root.addView(display,videoLayout);
        player=new ExoPlayer.Builder(activity).build();
        display.setPlayer(player);
        TextView title=new TextView(activity);
        title.setText((video?"Video · ":"Audio · ")+filename);
        title.setTextColor(0xffffffff);
        title.setBackgroundColor(0xcc152039);
        title.setPadding(20,16,150,16);
        title.setTextSize(14);
        root.addView(title,new FrameLayout.LayoutParams(-1,-2,Gravity.TOP));
        Button back=new Button(activity);
        back.setText("Back");
        back.setOnClickListener(v->onExit.run());
        root.addView(back,new FrameLayout.LayoutParams(-2,-2,Gravity.TOP|Gravity.RIGHT));
        status=new TextView(activity);
        status.setTextColor(0xffcbd9ed);
        status.setTextSize(13);
        status.setBackgroundColor(0xbb101827);
        status.setPadding(14,12,14,12);
        root.addView(status,new FrameLayout.LayoutParams(-1,-2,Gravity.BOTTOM));
        player.addListener(new Player.Listener(){
            @Override public void onPlaybackStateChanged(int state){
                if(closed)return;
                if(state==Player.STATE_READY){
                    showMessage("");
                    Log.i("FG_MEDIA","MEDIA_READY "+filename+
                        " duration_ms="+player.getDuration());
                }else if(state==Player.STATE_BUFFERING)
                    showMessage("Buffering from "+original.getAuthority()+"…");
                else if(state==Player.STATE_ENDED)showMessage("Playback finished");
            }
            @Override public void onRenderedFirstFrame(){
                Log.i("FG_MEDIA","VIDEO_FIRST_FRAME "+filename);
            }
            @Override public void onPlayerError(PlaybackException error){
                Log.e("FG_MEDIA","PLAYBACK_ERROR code="+error.getErrorCodeName(),error);
                if(!fallbackStarted){
                    fallbackStarted=true;
                    copyThenPlay();
                }else showMessage("Unable to decode or play this file: "+error.getMessage());
            }
        });
        play(original);
    }
    public View getView(){return root;}
    private void showMessage(String message){
        activity.runOnUiThread(()->{
            if(closed)return;
            status.setText(message);
            status.setVisibility(message.isEmpty()?View.GONE:View.VISIBLE);
        });
    }
    private void play(Uri uri){
        if(closed)return;
        try{
            Log.i("FG_MEDIA","PLAY_START "+uri.getScheme()+" "+uri.getAuthority());
            player.setMediaItem(MediaItem.fromUri(uri));
            player.prepare();
            player.play();
        }catch(Exception e){
            Log.e("FG_MEDIA","MEDIA_PREPARE_FAILED",e);
            if(!fallbackStarted){fallbackStarted=true;copyThenPlay();}
            else showMessage("Playback failed: "+e.getMessage());
        }
    }
    private static String digest(Uri uri){
        try{
            byte[] bytes=MessageDigest.getInstance("SHA-256")
                .digest(uri.toString().getBytes(java.nio.charset.StandardCharsets.UTF_8));
            StringBuilder text=new StringBuilder();
            for(int i=0;i<16;i++)text.append(String.format(Locale.ROOT,"%02x",bytes[i]&255));
            return text.toString();
        }catch(Exception e){throw new IllegalStateException(e);}
    }
    private void copyThenPlay(){
        final int version=session;
        showMessage("This file provider cannot stream the video. Caching for playback…");
        io.execute(()->{
            File pending=null;
            try{
                File cacheDir=new File(activity.getExternalCacheDir()!=null?
                    activity.getExternalCacheDir():activity.getCacheDir(),"fg-media-v1");
                if(!cacheDir.exists()&&!cacheDir.mkdirs())
                    throw new IOException("No media cache directory");
                String low=filename.toLowerCase(Locale.ROOT);
                String extension=low.endsWith(".webm")?".webm":
                    low.endsWith(".m4a")?".m4a":low.endsWith(".mp3")?".mp3":".mp4";
                File ready=new File(cacheDir,digest(original)+extension);
                if(ready.isFile()&&ready.length()>0){
                    if(!closed&&version==session)
                        activity.runOnUiThread(()->play(Uri.fromFile(ready)));
                    return;
                }
                pending=new File(cacheDir,digest(original)+".part");
                long written=0,lastDisplay=0;
                try(InputStream in=activity.getContentResolver().openInputStream(original);
                    OutputStream out=new BufferedOutputStream(new FileOutputStream(pending))){
                    if(in==null)throw new IOException("Media provider returned no stream");
                    byte[] buffer=new byte[256*1024];
                    int n;
                    while((n=in.read(buffer))!=-1){
                        if(closed||version!=session)throw new IOException("Playback cancelled");
                        out.write(buffer,0,n);
                        written+=n;
                        if(written-lastDisplay>=4L*1024*1024){
                            lastDisplay=written;
                            final long copied=written;
                            showMessage("Caching "+(copied/1048576)+" MB for playback…");
                            StatFs fs=new StatFs(cacheDir.getAbsolutePath());
                            if(fs.getAvailableBytes()<64L*1024*1024)
                                throw new IOException("Insufficient storage for media cache");
                        }
                    }
                }
                if(written==0)throw new IOException("Media file is empty");
                if(!pending.renameTo(ready))throw new IOException("Cache rename failed");
                Log.i("FG_MEDIA","CACHED_MEDIA_READY bytes="+written);
                if(!closed&&version==session)
                    activity.runOnUiThread(()->play(Uri.fromFile(ready)));
            }catch(Exception e){
                Log.e("FG_MEDIA","CACHE_FALLBACK_ERROR",e);
                if(!closed&&version==session)
                    showMessage("Playback unavailable: "+e.getMessage());
                if(pending!=null)pending.delete();
            }
        });
    }
    @Override public void close(){
        closed=true;session++;
        player.stop();player.release();
        io.shutdownNow();
    }
}