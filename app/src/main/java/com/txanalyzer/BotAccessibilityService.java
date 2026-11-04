package com.txanalyzer;

import android.accessibilityservice.AccessibilityService;
import android.accessibilityservice.GestureDescription;
import android.graphics.Path;
import android.graphics.Point;
import android.os.Handler;
import android.os.Looper;
import android.util.Log;
import android.view.Display;
import android.view.WindowManager;
import android.view.accessibility.AccessibilityEvent;
import android.view.accessibility.AccessibilityNodeInfo;
import android.view.accessibility.AccessibilityWindowInfo;
import java.util.List;

/** Opt-in gestures for the installed game; no root, memory access, or fake game observations. */
public final class BotAccessibilityService extends AccessibilityService {
    private static final String TAG="MinhQuanControl";
    private static final String GAME="com.garena.game.kgvn";
    private static BotAccessibilityService current;
    private final Handler handler=new Handler(Looper.getMainLooper());
    private String foreground="";

    public static boolean isAvailable(){return current!=null;}
    static BotAccessibilityService current(){return current;}
    public static boolean isGameForeground(){
        BotAccessibilityService s=current;
        return s!=null && GAME.equals(s.foregroundPackage());
    }
    @Override protected void onServiceConnected(){
        super.onServiceConnected();
        current=this;
        foreground=readVisibleApp();
        Log.i(TAG,"Accessibility service connected; visible="+foreground);
        EspOverlayService.refresh();
    }
    @Override public void onAccessibilityEvent(AccessibilityEvent event){
        if(event==null||event.getPackageName()==null)return;
        int t=event.getEventType();
        if(t!=AccessibilityEvent.TYPE_WINDOW_STATE_CHANGED &&
           t!=AccessibilityEvent.TYPE_WINDOWS_CHANGED)return;
        String pkg=event.getPackageName().toString();
        if(pkg.equals(getPackageName()))return; // Tapping our overlay is not leaving the game.
        if(!pkg.isEmpty())foreground=pkg;
    }
    /** Read the active window when possible; game engines may expose no accessible nodes. */
    private String readVisibleApp(){
        try{
            AccessibilityNodeInfo r=getRootInActiveWindow();
            if(r!=null){
                CharSequence p=r.getPackageName();
                String result=p==null?"":p.toString();r.recycle();
                if(!result.isEmpty()&&!result.equals(getPackageName()))return result;
            }
        }catch(Exception e){Log.w(TAG,"Cannot read active window",e);}
        try{
            List<AccessibilityWindowInfo> windows=getWindows();
            if(windows!=null){
                for(AccessibilityWindowInfo w:windows){
                    if(w.getType()!=AccessibilityWindowInfo.TYPE_APPLICATION)continue;
                    AccessibilityNodeInfo root=w.getRoot();
                    if(root==null)continue;
                    CharSequence pn=root.getPackageName();
                    String p=pn==null?"":pn.toString();root.recycle();
                    if(!p.isEmpty()&&!p.equals(getPackageName()))return p;
                }
            }
        }catch(Exception e){Log.w(TAG,"Cannot inspect windows",e);}
        return "";
    }
    private String foregroundPackage(){
        String visible=readVisibleApp();
        if(!visible.isEmpty())foreground=visible;
        return foreground;
    }
    @Override public void onInterrupt(){AutoControl.stop();}
    @Override public boolean onUnbind(android.content.Intent i){disconnect();return super.onUnbind(i);}
    @Override public void onDestroy(){disconnect();super.onDestroy();}
    private void disconnect(){if(current==this){current=null;AutoControl.stop();EspOverlayService.refresh();}}
    private Point screenSize(){
        WindowManager wm=(WindowManager)getSystemService(WINDOW_SERVICE);
        Display d=wm.getDefaultDisplay();Point p=new Point();d.getRealSize(p);return p;
    }
    boolean isLandscape(){Point s=screenSize();return s.x>s.y;}
    /** Basic attack input only while the real game is foreground in landscape. */
    boolean tapAttack(){
        if(!isGameForeground()||!isLandscape())return false;
        Point p=screenSize();return gesture(p.x*.894f,p.y*.795f,p.x*.894f,p.y*.795f,75);
    }
    /** Approximate movement pulse for testing; not navigation or decision-making. */
    boolean pulseMovement(){
        if(!isGameForeground()||!isLandscape())return false;
        Point p=screenSize();return gesture(p.x*.15f,p.y*.78f,p.x*.18f,p.y*.70f,350);
    }
    private boolean gesture(float x1,float y1,float x2,float y2,long duration){
        Path path=new Path();path.moveTo(x1,y1);
        if(x1!=x2||y1!=y2)path.lineTo(x2,y2);
        GestureDescription.Builder b=new GestureDescription.Builder();
        b.addStroke(new GestureDescription.StrokeDescription(path,0,duration));
        try{return dispatchGesture(b.build(),null,handler);}
        catch(Exception ex){Log.e(TAG,"Gesture dispatch error",ex);return false;}
    }
}
