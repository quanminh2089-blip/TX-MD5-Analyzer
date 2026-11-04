package com.txanalyzer;

import android.accessibilityservice.AccessibilityService;
import android.accessibilityservice.GestureDescription;
import android.graphics.Path;
import android.graphics.Point;
import android.os.Handler;
import android.os.Looper;
import android.view.Display;
import android.view.WindowManager;
import android.view.accessibility.AccessibilityEvent;

/** Opt-in local gesture injector; does not read the game process or memory. */
public final class BotAccessibilityService extends AccessibilityService {
    private static final String GAME_PACKAGE="com.garena.game.kgvn";
    private static BotAccessibilityService instance;
    private String foregroundPackage="";
    private final Handler handler=new Handler(Looper.getMainLooper());
    public static boolean isAvailable(){return instance!=null;}
    static BotAccessibilityService current(){return instance;}
    public static boolean isGameForeground(){
        return instance!=null && GAME_PACKAGE.equals(instance.foregroundPackage);
    }
    @Override protected void onServiceConnected(){super.onServiceConnected();instance=this;}
    @Override public void onAccessibilityEvent(AccessibilityEvent event){
        if(event==null||event.getPackageName()==null)return;
        int t=event.getEventType();
        if(t!=AccessibilityEvent.TYPE_WINDOW_STATE_CHANGED && t!=AccessibilityEvent.TYPE_WINDOWS_CHANGED)return;
        String pkg=event.getPackageName().toString();
        // Floating overlay interactions can generate this app's events; do not misclassify them.
        if(getPackageName().equals(pkg))return;
        foregroundPackage=pkg;
        if(!GAME_PACKAGE.equals(pkg))AutoControl.stop();
    }
    @Override public void onInterrupt(){AutoControl.stop();}
    @Override public boolean onUnbind(android.content.Intent intent){disconnect();return super.onUnbind(intent);}
    @Override public void onDestroy(){disconnect();super.onDestroy();}
    private void disconnect(){if(instance==this){instance=null;AutoControl.stop();}}
    private Point screenSize(){
        WindowManager wm=(WindowManager)getSystemService(WINDOW_SERVICE);
        Display display=wm.getDefaultDisplay();
        Point p=new Point();display.getRealSize(p);
        return p;
    }
    boolean isLandscape(){Point p=screenSize();return p.x>p.y;}
    /** Approximate attack button tap for testing in training mode only. */
    boolean tapAttack(){
        if(!isGameForeground() || !isLandscape())return false;
        Point p=screenSize();
        return gesture(p.x*.894f,p.y*.795f,p.x*.894f,p.y*.795f,75);
    }
    /** A short joystick pulse for control testing; NOT lane navigation. */
    boolean pulseMovement(){
        if(!isGameForeground() || !isLandscape())return false;
        Point p=screenSize();
        return gesture(p.x*.15f,p.y*.78f,p.x*.18f,p.y*.70f,400);
    }
    private boolean gesture(float x1,float y1,float x2,float y2,long duration){
        Path path=new Path();path.moveTo(x1,y1);
        if(x1!=x2||y1!=y2)path.lineTo(x2,y2);
        GestureDescription.Builder builder=new GestureDescription.Builder();
        builder.addStroke(new GestureDescription.StrokeDescription(path,0,duration));
        try {return dispatchGesture(builder.build(),null,handler);}catch(Exception ex){return false;}
    }
}
