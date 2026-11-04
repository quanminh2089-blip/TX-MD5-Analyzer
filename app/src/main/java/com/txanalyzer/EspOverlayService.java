package com.txanalyzer;

import android.accessibilityservice.AccessibilityServiceInfo;
import android.app.Service;
import android.content.Intent;
import android.graphics.PixelFormat;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.os.IBinder;
import android.provider.Settings;
import android.view.Gravity;
import android.view.accessibility.AccessibilityManager;
import android.view.MotionEvent;
import android.view.View;
import android.view.WindowManager;
import android.widget.TextView;
import android.widget.Toast;
import java.util.List;

/** A single circular OFF/ON bubble. Tap to arm/stop; drag to reposition. */
public final class EspOverlayService extends Service {
    private static EspOverlayService current;
    private WindowManager wm;
    private TextView bubble;
    private WindowManager.LayoutParams params;
    private boolean dragging;
    private float downX,downY;
    private int initialX,initialY;
    private int dp(float v){return (int)(v*getResources().getDisplayMetrics().density+.5f);}
    @Override public IBinder onBind(Intent i){return null;}
    @Override public void onCreate(){
        super.onCreate();
        if(!Settings.canDrawOverlays(this)){stopSelf();return;}
        wm=(WindowManager)getSystemService(WINDOW_SERVICE);
        if(current!=null && current!=this)current.stopSelf();
        bubble=new TextView(this);
        bubble.setGravity(Gravity.CENTER);bubble.setTextSize(15);
        bubble.setTypeface(Typeface.DEFAULT,Typeface.BOLD);
        bubble.setTextColor(0xffffffff);
        bubble.setElevation(dp(9));
        bubble.setContentDescription("Chạm để bật hoặc tắt tự động chơi; giữ và kéo để di chuyển");
        params=new WindowManager.LayoutParams(dp(68),dp(68),
            WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY,
            WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE|
            WindowManager.LayoutParams.FLAG_NOT_TOUCH_MODAL|
            WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN,
            PixelFormat.TRANSLUCENT);
        params.gravity=Gravity.TOP|Gravity.START;
        params.x=dp(14);params.y=dp(120);
        bubble.setOnTouchListener((v,e)->{
            switch(e.getActionMasked()){
                case MotionEvent.ACTION_DOWN:
                    downX=e.getRawX();downY=e.getRawY();
                    initialX=params.x;initialY=params.y;dragging=false;return true;
                case MotionEvent.ACTION_MOVE:
                    float dx=e.getRawX()-downX,dy=e.getRawY()-downY;
                    if(Math.abs(dx)>dp(10)||Math.abs(dy)>dp(10))dragging=true;
                    if(dragging&&wm!=null){
                        params.x=Math.max(0,Math.min(getResources().getDisplayMetrics().widthPixels-dp(68),initialX+(int)dx));
                        params.y=Math.max(0,Math.min(getResources().getDisplayMetrics().heightPixels-dp(68),initialY+(int)dy));
                        try{wm.updateViewLayout(bubble,params);}catch(Exception ignored){}
                    }
                    return true;
                case MotionEvent.ACTION_UP:
                    if(!dragging)toggle();return true;
                case MotionEvent.ACTION_CANCEL:return true;
                default:return true;
            }
        });
        render();
        try{wm.addView(bubble,params);current=this;}
        catch(Exception ex){bubble=null;stopSelf();}
    }
    private void toggle(){
        if(AutoControl.isEnabled()){
            AutoControl.stop();toast("AUTO đã tắt");
        }else if(!BotAccessibilityService.isAvailable()){
            toast(accessibilityEnabledInSettings()
                ? "Trợ năng đang bật nhưng dịch vụ chưa kết nối. Tắt rồi bật lại MinhQuan điều khiển."
                : "Cấp quyền Trợ năng MinhQuan một lần, rồi quay lại Liên Quân");
            try{
                Intent i=new Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS);
                i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);startActivity(i);
            }catch(Exception ex){toast("Không thể mở cài đặt Trợ năng");}
        }else if(AutoControl.start(this)){
            toast(BotAccessibilityService.isGameForeground()
                ? "AUTO đã bật. Thử nghiệm điều khiển cơ bản."
                : "AUTO đã bật; đang chờ màn hình Liên Quân");
        }else{
            toast("Không kích hoạt được. Hãy kiểm tra quyền Trợ năng.");
        }
        render();
    }
    private boolean accessibilityEnabledInSettings(){
        try{
            AccessibilityManager manager=(AccessibilityManager)getSystemService(ACCESSIBILITY_SERVICE);
            if(manager==null)return false;
            List<AccessibilityServiceInfo> services=manager.getEnabledAccessibilityServiceList(
                AccessibilityServiceInfo.FEEDBACK_ALL_MASK);
            for(AccessibilityServiceInfo info:services){
                if(info.getResolveInfo()!=null&&info.getResolveInfo().serviceInfo!=null
                    &&getPackageName().equals(info.getResolveInfo().serviceInfo.packageName)
                    &&BotAccessibilityService.class.getName().equals(
                        info.getResolveInfo().serviceInfo.name))return true;
            }
        }catch(Exception ignored){}
        return false;
    }
    private void toast(String message){Toast.makeText(this,message,Toast.LENGTH_LONG).show();}
    private void render(){
        if(bubble==null)return;
        boolean enabled=AutoControl.isEnabled();
        bubble.setText(enabled?"ON":"OFF");
        GradientDrawable d=new GradientDrawable();
        d.setShape(GradientDrawable.OVAL);
        d.setColor(enabled?0xff00a85c:0xffd53240);
        d.setStroke(dp(2),enabled?0xffa3ffd1:0xffffb2bc);
        bubble.setBackground(d);
        bubble.setContentDescription("AUTO "+(enabled?"ON":"OFF")+". Chạm để đổi trạng thái");
    }
    public static void refresh(){
        EspOverlayService s=current;
        if(s!=null && s.bubble!=null)s.bubble.post(s::render);
    }
    @Override public void onDestroy(){
        if(current==this)current=null;
        AutoControl.stop();
        if(wm!=null&&bubble!=null){try{wm.removeView(bubble);}catch(Exception ignored){}}
        bubble=null;super.onDestroy();
    }
}
