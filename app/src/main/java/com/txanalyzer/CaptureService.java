package com.txanalyzer;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.Service;
import android.content.Context;
import android.content.Intent;
import android.content.pm.ServiceInfo;
import android.content.res.Configuration;
import android.graphics.Bitmap;
import android.graphics.Color;
import android.graphics.Matrix;
import android.graphics.PixelFormat;
import android.graphics.Rect;
import android.graphics.drawable.GradientDrawable;
import android.hardware.display.DisplayManager;
import android.hardware.display.VirtualDisplay;
import android.media.Image;
import android.media.ImageReader;
import android.media.projection.MediaProjection;
import android.media.projection.MediaProjectionManager;
import android.os.Build;
import android.os.Handler;
import android.os.IBinder;
import android.os.Looper;
import android.util.DisplayMetrics;
import android.view.Gravity;
import android.view.MotionEvent;
import android.view.View;
import android.view.WindowManager;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.TextView;
import com.google.android.gms.tasks.OnCompleteListener;
import com.google.mlkit.vision.common.InputImage;
import com.google.mlkit.vision.text.Text;
import com.google.mlkit.vision.text.TextRecognition;
import com.google.mlkit.vision.text.TextRecognizer;
import com.google.mlkit.vision.text.latin.TextRecognizerOptions;
import java.nio.ByteBuffer;
import java.util.Locale;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/** On-device screen OCR; no requests, website access, auto-bets or claimed RNG predictions. */
public class CaptureService extends Service {
    public static final String STOP_ACTION="com.txanalyzer.STOP";
    private static final long FRAME_MS=1700;
    private final Handler main=new Handler(Looper.getMainLooper());
    private final HistoryReader historyReader=new HistoryReader();
    private final TextRecognizer recognizer=TextRecognition.getClient(TextRecognizerOptions.DEFAULT_OPTIONS);
    private WindowManager wm;
    private MediaProjection projection;
    private VirtualDisplay virtualDisplay;
    private ImageReader reader;
    private FrameLayout root;
    private WindowManager.LayoutParams overlayParams;
    private LinearLayout bubble,panel;
    private TextView status,stats,recent,details;
    private volatile boolean busy=false,ending=false;
    private long lastFrame=0;
    private int preferredRotation=-90;
    private String lastSignature="",lastSession="";
    private HistoryReader.Result latest;
    private boolean expanded=false;

    @Override public IBinder onBind(Intent intent){return null;}

    @Override public int onStartCommand(Intent intent,int flags,int startId) {
        if(intent!=null && STOP_ACTION.equals(intent.getAction())) {stopSelf();return START_NOT_STICKY;}
        if(projection!=null || ending)return START_NOT_STICKY;
        if(intent==null)return START_NOT_STICKY;
        try {
            NotificationManager nm=(NotificationManager)getSystemService(NOTIFICATION_SERVICE);
            nm.createNotificationChannel(new NotificationChannel("capture","Phân tích màn hình",NotificationManager.IMPORTANCE_LOW));
            Notification note=new Notification.Builder(this,"capture")
                    .setSmallIcon(android.R.drawable.ic_menu_view)
                    .setContentTitle("TX MD5 Analyzer đang nhận diện")
                    .setContentText("Phân tích trên thiết bị • Mở ứng dụng để dừng")
                    .setOngoing(true).build();
            if(Build.VERSION.SDK_INT>=29)startForeground(100,note,ServiceInfo.FOREGROUND_SERVICE_TYPE_MEDIA_PROJECTION);
            else startForeground(100,note);
            wm=(WindowManager)getSystemService(WINDOW_SERVICE);
            showOverlay();
            MediaProjectionManager mgr=(MediaProjectionManager)getSystemService(MEDIA_PROJECTION_SERVICE);
            @SuppressWarnings("deprecation") Intent permission=intent.getParcelableExtra("data");
            int code=intent.getIntExtra("result",0);
            if(permission==null||code==0)throw new IllegalArgumentException("Thiếu quyền ghi màn hình");
            projection=mgr.getMediaProjection(code,permission);
            if(projection==null)throw new IllegalStateException("Không khởi tạo được MediaProjection");
            projection.registerCallback(new MediaProjection.Callback(){
                @Override public void onStop(){main.post(()->stopSelf());}
            },main);
            createDisplay();
            setState("Đang quét • Mở bảng LỊCH SỬ PHIÊN để đọc tự động");
        }catch(Exception e) {
            setState("Lỗi cấp quyền: "+e.getMessage());
            stopSelf();
        }
        return START_NOT_STICKY;
    }

    @SuppressWarnings("deprecation")
    private void createDisplay() {
        DisplayMetrics m=new DisplayMetrics();
        wm.getDefaultDisplay().getRealMetrics(m);
        reader=ImageReader.newInstance(m.widthPixels,m.heightPixels,PixelFormat.RGBA_8888,2);
        reader.setOnImageAvailableListener(this::takeFrame,main);
        virtualDisplay=projection.createVirtualDisplay("TX-MD5-Local",m.widthPixels,m.heightPixels,m.densityDpi,
                DisplayManager.VIRTUAL_DISPLAY_FLAG_AUTO_MIRROR,reader.getSurface(),null,main);
    }

    @Override public void onConfigurationChanged(Configuration config) {
        super.onConfigurationChanged(config);
        if(virtualDisplay==null||wm==null||ending)return;
        // Android 14+: resize existing virtual display (one createVirtualDisplay per capture token).
        main.postDelayed(()->{
            if(virtualDisplay==null||wm==null||ending)return;
            try {
                DisplayMetrics m=new DisplayMetrics();
                wm.getDefaultDisplay().getRealMetrics(m);
                if(reader!=null&&reader.getWidth()==m.widthPixels&&reader.getHeight()==m.heightPixels)return;
                ImageReader old=reader;
                reader=ImageReader.newInstance(m.widthPixels,m.heightPixels,PixelFormat.RGBA_8888,2);
                reader.setOnImageAvailableListener(this::takeFrame,main);
                virtualDisplay.resize(m.widthPixels,m.heightPixels,m.densityDpi);
                virtualDisplay.setSurface(reader.getSurface());
                if(old!=null)old.close();
                preferredRotation=m.widthPixels<m.heightPixels?-90:0;
            }catch(Exception e){setState("Không đổi được vùng chụp: "+e.getMessage());}
        },350);
    }

    private void takeFrame(ImageReader source) {
        Image image=null;
        try {
            image=source.acquireLatestImage();
            if(image==null)return;
            long now=System.currentTimeMillis();
            if(busy || now-lastFrame<FRAME_MS)return;
            lastFrame=now;
            Image.Plane plane=image.getPlanes()[0];
            ByteBuffer bytes=plane.getBuffer();
            int width=image.getWidth(),height=image.getHeight();
            int pixelStride=plane.getPixelStride(),rowStride=plane.getRowStride();
            int paddedWidth=width+(rowStride-pixelStride*width)/pixelStride;
            if(paddedWidth<width || paddedWidth>width+1000)return;
            Bitmap padded=Bitmap.createBitmap(paddedWidth,height,Bitmap.Config.ARGB_8888);
            padded.copyPixelsFromBuffer(bytes);
            Bitmap screen=Bitmap.createBitmap(padded,0,0,width,height);
            padded.recycle();
            busy=true;
            int angle=width<height?(preferredRotation==90?90:-90):(preferredRotation==180?180:0);
            recognize(screen,angle,true);
        }catch(Exception ex){busy=false;setState("Lỗi lấy ảnh: "+ex.getMessage());}
        finally{if(image!=null)image.close();}
    }

    private static Bitmap oriented(Bitmap src,int angle) {
        if(angle==0)return src;
        Matrix matrix=new Matrix();matrix.postRotate(angle);
        return Bitmap.createBitmap(src,0,0,src.getWidth(),src.getHeight(),matrix,true);
    }

    private void recognize(Bitmap original,int angle,boolean tryAlternate) {
        final Bitmap upright;
        try{upright=oriented(original,angle);}catch(Exception e){original.recycle();busy=false;return;}
        recognizer.process(InputImage.fromBitmap(upright,0))
                .addOnSuccessListener(text->{
                    if(ending){free(original,upright);return;}
                    String parsed=text.getText();
                    boolean board=HistoryReader.isHistory(parsed);
                    int score=HistoryReader.orientationScore(parsed);
                    if(!board && tryAlternate && (score<55 || latest==null)) {
                        if(upright!=original)upright.recycle();
                        int alternate=original.getHeight()>original.getWidth()?-angle:180;
                        recognize(original,alternate,false);
                        return;
                    }
                    preferredRotation=angle;
                    if(board)analyzeHistory(original,upright,parsed);
                    else {
                        updateNonHistory(parsed);
                        free(original,upright);
                    }
                })
                .addOnFailureListener(err->{setState("Không đọc được ảnh: "+err.getMessage());free(original,upright);});
    }

    private void analyzeHistory(Bitmap original,Bitmap upright,String txt) {
        final HistoryReader.Result result=historyReader.analyze(upright,txt);
        if(result.gridDetected()) {
            // Second OCR pass on a 3x enlarged crop of the verified grid to read tiny numbers.
            // The color/shape classification remains useful even when number OCR fails.
            int x=Math.max(0,Math.round(result.gridLeft));
            int y=Math.max(0,Math.round(result.gridTop));
            int w=Math.min(upright.getWidth()-x,Math.round(result.cellWidth*20));
            int h=Math.min(upright.getHeight()-y,Math.round(result.cellHeight*5));
            if(w>50&&h>30) {
                Bitmap crop=Bitmap.createBitmap(upright,x,y,w,h);
                Bitmap enlarged=Bitmap.createScaledBitmap(crop,w*3,h*3,true);
                crop.recycle();
                recognizer.process(InputImage.fromBitmap(enlarged,0))
                        .addOnSuccessListener(numbers->{
                            // Crop origin can be fractional; cell coordinates are local to crop.
                            HistoryReader.setNumbers(result,numbers);
                            showHistory(result);
                        })
                        .addOnFailureListener(e->showHistory(result))
                        .addOnCompleteListener(task->{enlarged.recycle();free(original,upright);});
                return;
            }
        }
        showHistory(result);
        free(original,upright);
    }

    private void updateNonHistory(String text) {
        Matcher id=Pattern.compile("#\\s*(\\d{5,10})").matcher(text);
        if(id.find())lastSession=id.group(1);
        if(latest==null) {
            setState("Đang quét màn hình • Mở LỊCH SỬ PHIÊN để nhập lịch sử");
            main.post(()->{
                if(details!=null)details.setText(lastSession.isEmpty()?"Chưa có phiên được xác nhận":"Phiên trên màn hình: #"+lastSession);
            });
        }else setState("Đang theo dõi • Đã lưu ảnh chụp lịch sử gần nhất");
    }

    private void showHistory(HistoryReader.Result data) {
        if(ending)return;
        String signature=data.signature();
        // Retain most recent valid grid if a subsequent frame contains only unreadable cells.
        if(!data.gridDetected() && latest!=null && latest.gridDetected()) {
            setState("Có bảng lịch sử • Đang chờ nhận diện rõ hơn");
            return;
        }
        latest=data;
        if(signature.equals(lastSignature)) {setState("Đã đồng bộ lịch sử • Tự động quét");return;}
        lastSignature=signature;
        String mostRecent="Chưa xác định";
        if(!data.entries.isEmpty()) {
            HistoryReader.Entry last=data.entries.get(data.entries.size()-1);
            mostRecent=(last.tai?"TÀI":"XỈU")+(last.value>=0?" ("+last.value+")":" (chưa đọc rõ điểm)");
        }
        final String newMostRecent=mostRecent;
        main.post(()->{
            if(stats==null)return;
            status.setText(data.gridDetected()?"● ĐÃ NHẬN DIỆN BẢNG LỊCH SỬ":"● THẤY BẢNG • CHƯA ĐỌC ĐỦ Ô");
            stats.setText(data.summary()+"\nÔ nhìn thấy: "+data.entries.size()+" • Gần nhất: "+newMostRecent);
            recent.setText(data.historyLine());
            details.setText("Chỉ các ô đang hiển thị được ghi nhận. '?' = chưa xác nhận số điểm.\nKhông dự đoán kết quả phiên chưa mở.");
        });
    }

    private void free(Bitmap source,Bitmap rotated) {
        try{if(rotated!=source && !rotated.isRecycled())rotated.recycle();}catch(Exception ignored){}
        try{if(!source.isRecycled())source.recycle();}catch(Exception ignored){}
        busy=false;
    }

    private int dp(float value) {return Math.round(getResources().getDisplayMetrics().density*value);}
    private GradientDrawable bg(int color,int radiusDp) {
        GradientDrawable d=new GradientDrawable();d.setColor(color);d.setCornerRadius(dp(radiusDp));return d;
    }
    private TextView tv(String text,int size,int color) {
        TextView t=new TextView(this);t.setText(text);t.setTextSize(size);t.setTextColor(color);return t;
    }
    private void showOverlay() {
        root=new FrameLayout(this);
        bubble=new LinearLayout(this);bubble.setGravity(Gravity.CENTER);
        bubble.setBackground(bg(Color.rgb(25,57,99),40));bubble.setElevation(dp(8));
        TextView logo=tv("TX",16,Color.WHITE);logo.setGravity(Gravity.CENTER);logo.setTypeface(null,1);
        bubble.addView(logo);
        FrameLayout.LayoutParams bp=new FrameLayout.LayoutParams(dp(54),dp(54));
        root.addView(bubble,bp);
        panel=new LinearLayout(this);panel.setPadding(dp(15),dp(13),dp(15),dp(14));panel.setOrientation(LinearLayout.VERTICAL);
        panel.setBackground(bg(Color.argb(247,18,28,48),18));panel.setElevation(dp(10));
        TextView title=tv("TX MD5   •   LIVE     −",16,Color.WHITE);title.setTypeface(null,1);
        title.setPadding(0,0,0,dp(10));panel.addView(title);
        status=tv("● Đang chờ cấp quyền màn hình",12,Color.rgb(105,226,165));
        panel.addView(status);
        stats=tv("Tài —  •  Xỉu —",16,Color.WHITE);stats.setPadding(0,dp(12),0,dp(10));
        panel.addView(stats);
        TextView historyTitle=tv("LỊCH SỬ NHẬN DIỆN",12,Color.rgb(120,184,255));
        panel.addView(historyTitle);
        recent=tv("Mở bảng Lịch sử phiên trong game",13,Color.WHITE);recent.setPadding(0,dp(8),0,dp(10));
        panel.addView(recent);
        details=tv("Quét trên máy • Không đặt cược tự động",11,Color.rgb(185,196,214));
        panel.addView(details);
        TextView exit=tv("DỪNG CHỤP MÀN HÌNH",12,Color.rgb(255,142,142));
        exit.setPadding(0,dp(16),0,0);exit.setGravity(Gravity.END);
        exit.setOnClickListener(v->stopSelf());panel.addView(exit);
        panel.setVisibility(View.GONE);
        FrameLayout.LayoutParams pp=new FrameLayout.LayoutParams(dp(294),-2);root.addView(panel,pp);
        title.setOnClickListener(v->setExpanded(false));
        attachDrag(bubble);
        int type=Build.VERSION.SDK_INT>=26?WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY:WindowManager.LayoutParams.TYPE_PHONE;
        overlayParams=new WindowManager.LayoutParams(dp(54),dp(54),type,
                WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE|WindowManager.LayoutParams.FLAG_NOT_TOUCH_MODAL,PixelFormat.TRANSLUCENT);
        overlayParams.gravity=Gravity.TOP|Gravity.LEFT;
        overlayParams.x=dp(12);overlayParams.y=dp(110);
        wm.addView(root,overlayParams);
    }
    private void attachDrag(View bubbleView) {
        bubbleView.setOnTouchListener(new View.OnTouchListener(){
            private float downX,downY;private int left,top;
            @Override public boolean onTouch(View v,MotionEvent e) {
                switch(e.getActionMasked()) {
                    case MotionEvent.ACTION_DOWN: downX=e.getRawX();downY=e.getRawY();left=overlayParams.x;top=overlayParams.y;return true;
                    case MotionEvent.ACTION_MOVE:
                        overlayParams.x=Math.max(0,left+Math.round(e.getRawX()-downX));
                        overlayParams.y=Math.max(0,top+Math.round(e.getRawY()-downY));
                        if(wm!=null&&root!=null)wm.updateViewLayout(root,overlayParams);
                        return true;
                    case MotionEvent.ACTION_UP:
                        if(Math.abs(e.getRawX()-downX)<dp(9)&&Math.abs(e.getRawY()-downY)<dp(9))setExpanded(true);
                        return true;
                }
                return false;
            }
        });
    }
    private void setExpanded(boolean value) {
        if(root==null||wm==null)return;
        expanded=value;
        bubble.setVisibility(value?View.GONE:View.VISIBLE);
        panel.setVisibility(value?View.VISIBLE:View.GONE);
        int screenWidth=getResources().getDisplayMetrics().widthPixels;
        overlayParams.width=value?Math.min(dp(294),Math.round(screenWidth*.86f)):dp(54);
        overlayParams.height=value?WindowManager.LayoutParams.WRAP_CONTENT:dp(54);
        if(value)overlayParams.x=Math.min(overlayParams.x,Math.max(0,screenWidth-overlayParams.width));
        wm.updateViewLayout(root,overlayParams);
    }
    private void setState(String message) {
        main.post(()->{if(status!=null&&!ending)status.setText(message);});
    }
    @Override public void onDestroy() {
        ending=true;
        if(reader!=null){reader.setOnImageAvailableListener(null,null);reader.close();reader=null;}
        if(virtualDisplay!=null){virtualDisplay.release();virtualDisplay=null;}
        if(projection!=null){projection.stop();projection=null;}
        if(wm!=null && root!=null){try{wm.removeView(root);}catch(Exception ignored){}root=null;}
        recognizer.close();
        super.onDestroy();
    }
}
