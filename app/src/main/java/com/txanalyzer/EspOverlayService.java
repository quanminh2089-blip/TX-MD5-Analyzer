package com.txanalyzer;

import android.app.Service;
import android.content.Intent;
import android.graphics.Color;
import android.graphics.PixelFormat;
import android.graphics.drawable.GradientDrawable;
import android.os.IBinder;
import android.provider.Settings;
import android.view.Gravity;
import android.view.MotionEvent;
import android.view.View;
import android.view.WindowManager;
import android.widget.LinearLayout;
import android.widget.TextView;

/** Overlay compatibility test only. No game memory access or enemy detection. */
public class EspOverlayService extends Service {
    private static boolean running;
    private WindowManager wm;
    private View panel;
    private WindowManager.LayoutParams params;
    public static boolean isRunning() { return running; }
    private int dp(float v) { return (int)(v * getResources().getDisplayMetrics().density + .5f); }
    @Override public IBinder onBind(Intent i) { return null; }
    @Override public void onCreate() {
        super.onCreate();
        if (!Settings.canDrawOverlays(this)) { stopSelf(); return; }
        wm = (WindowManager)getSystemService(WINDOW_SERVICE);
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(dp(12),dp(10),dp(12),dp(10));
        GradientDrawable bg = new GradientDrawable();
        bg.setColor(0xe6081819); bg.setCornerRadius(dp(14)); bg.setStroke(dp(1),0xff27d89b);
        root.setBackground(bg);
        TextView title = new TextView(this);
        title.setText("◈ MINHQUAN · OVERLAY TEST"); title.setTextColor(0xff48f6b1);
        title.setTextSize(12); title.setGravity(Gravity.CENTER);
        root.addView(title);
        TextView status = new TextView(this);
        status.setText("LỚP PHỦ HOẠT ĐỘNG\nESP TƯỚNG ẨN: CHƯA CÓ DỮ LIỆU\nChạm giữ để di chuyển");
        status.setTextColor(Color.WHITE); status.setTextSize(11);
        status.setGravity(Gravity.CENTER); status.setPadding(0,dp(9),0,dp(9));
        root.addView(status);
        TextView close = new TextView(this);
        close.setText("✕ ĐÓNG"); close.setTextColor(0xfff9b4b4);
        close.setGravity(Gravity.CENTER); close.setPadding(0,dp(5),0,dp(4));
        root.addView(close); close.setOnClickListener(v -> stopSelf());
        params = new WindowManager.LayoutParams(dp(246),WindowManager.LayoutParams.WRAP_CONTENT,
                WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY,
                WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE | WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN,
                PixelFormat.TRANSLUCENT);
        params.gravity = Gravity.TOP | Gravity.START;
        params.x = dp(20); params.y = dp(130);
        root.setOnTouchListener(new View.OnTouchListener() {
            float startX,startY; int initialX,initialY;
            @Override public boolean onTouch(View v, MotionEvent event) {
                switch(event.getActionMasked()) {
                    case MotionEvent.ACTION_DOWN:
                        startX=event.getRawX();startY=event.getRawY();initialX=params.x;initialY=params.y;return true;
                    case MotionEvent.ACTION_MOVE:
                        params.x=initialX+(int)(event.getRawX()-startX);
                        params.y=initialY+(int)(event.getRawY()-startY);
                        if(wm!=null)wm.updateViewLayout(panel,params);
                        return true;
                    default:return true;
                }
            }
        });
        panel=root;
        try { wm.addView(panel,params); running=true; }
        catch(Exception ex) { panel=null;stopSelf(); }
    }
    @Override public void onDestroy() {
        running=false;
        if(panel!=null && wm!=null) { try { wm.removeView(panel); } catch(Exception ignored) {} }
        panel=null;super.onDestroy();
    }
}
