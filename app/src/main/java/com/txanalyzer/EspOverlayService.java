package com.txanalyzer;

import android.app.Service;
import android.content.Intent;
import android.graphics.PixelFormat;
import android.graphics.drawable.GradientDrawable;
import android.os.IBinder;
import android.provider.Settings;
import android.view.Gravity;
import android.view.MotionEvent;
import android.view.View;
import android.view.WindowManager;
import android.widget.TextView;
import android.widget.Toast;

/** Minimal one-switch overlay. Touch to toggle; drag to reposition. */
public final class EspOverlayService extends Service {
    private static EspOverlayService current;
    private WindowManager wm;
    private TextView switchButton;
    private WindowManager.LayoutParams params;
    private boolean dragging;
    private int dp(float v){return (int)(v * getResources().getDisplayMetrics().density + .5f);}
    @Override public IBinder onBind(Intent i){return null;}
    @Override public void onCreate(){
        super.onCreate();
        if(!Settings.canDrawOverlays(this)){stopSelf();return;}
        wm=(WindowManager)getSystemService(WINDOW_SERVICE);
        switchButton=new TextView(this);
        switchButton.setGravity(Gravity.CENTER);
        switchButton.setTextSize(14);
        switchButton.setTypeface(android.graphics.Typeface.DEFAULT, android.graphics.Typeface.BOLD);
        switchButton.setPadding(dp(14),dp(9),dp(14),dp(9));
        switchButton.setElevation(dp(3));
        updateButton();
        params=new WindowManager.LayoutParams(dp(172),dp(52),
                WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY,
                WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE |
                WindowManager.LayoutParams.FLAG_NOT_TOUCH_MODAL |
                WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN,
                PixelFormat.TRANSLUCENT);
        params.gravity=Gravity.TOP|Gravity.START;
        params.x=dp(18);params.y=dp(112);
        switchButton.setOnTouchListener(new View.OnTouchListener(){
            float downX,downY; int x,y;
            @Override public boolean onTouch(View v,MotionEvent e){
                switch(e.getActionMasked()) {
                    case MotionEvent.ACTION_DOWN:
                        downX=e.getRawX();downY=e.getRawY();x=params.x;y=params.y;dragging=false;return true;
                    case MotionEvent.ACTION_MOVE:
                        float dx=e.getRawX()-downX,dy=e.getRawY()-downY;
                        if(Math.abs(dx)>dp(9)||Math.abs(dy)>dp(9))dragging=true;
                        if(dragging && wm!=null){
                            params.x=x+(int)dx;params.y=y+(int)dy;
                            try{wm.updateViewLayout(switchButton,params);}catch(Exception ignored){}
                        }
                        return true;
                    case MotionEvent.ACTION_UP:
                        if(!dragging)onToggle();return true;
                    default:return true;
                }
            }
        });
        try {wm.addView(switchButton,params);current=this;}
        catch(Exception ex){switchButton=null;stopSelf();}
    }
    private void onToggle(){
        if (AutoControl.isEnabled()) {
            AutoControl.stop();
        } else if (!BotAccessibilityService.isAvailable()) {
            Toast.makeText(this,"Bật dịch vụ 'MinhQuan điều khiển' trong Trợ năng",Toast.LENGTH_LONG).show();
            try {
                Intent i=new Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS);
                i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                startActivity(i);
            } catch(Exception ex){Toast.makeText(this,"Không mở được Trợ năng",Toast.LENGTH_LONG).show();}
        } else if (!BotAccessibilityService.isGameForeground()) {
            Toast.makeText(this,"Vào trận luyện tập Liên Quân rồi bật AUTO CHƠI",Toast.LENGTH_LONG).show();
        } else if (!AutoControl.start(this)) {
            Toast.makeText(this,"Chưa thể khởi động bộ điều khiển",Toast.LENGTH_LONG).show();
        }
        updateButton();
    }
    private void updateButton(){
        if(switchButton==null)return;
        boolean on=AutoControl.isEnabled();
        switchButton.setText(on ? "AUTO CHƠI  •  BẬT" : "AUTO CHƠI  •  TẮT");
        switchButton.setTextColor(on?0xff061a15:0xff52ebbd);
        GradientDrawable d=new GradientDrawable();
        d.setCornerRadius(dp(15));
        d.setColor(on?0xff47e2ac:0xe8091917);
        d.setStroke(dp(1),0xff32cfa1);
        switchButton.setBackground(d);
    }
    public static void refresh(){
        EspOverlayService s=current;
        if(s!=null && s.switchButton!=null)s.switchButton.post(s::updateButton);
    }
    @Override public void onDestroy(){
        if(current==this)current=null;
        AutoControl.stop();
        if(wm!=null && switchButton!=null){try{wm.removeView(switchButton);}catch(Exception ignored){}}
        switchButton=null;
        super.onDestroy();
    }
}
