package com.txanalyzer;

import android.content.Context;
import android.os.Handler;
import android.os.Looper;
import android.os.SystemClock;
import com.txanalyzer.bot.BotSession;

/** Arms on user tap, waits for Liên Quân, stops immediately on OFF.
 *  Training macro, not a fully autonomous bot. Never issues gestures in other apps. */
public final class AutoControl {
    private static final long MAX_SESSION_MS=15*60*1000L; // safety timeout
    private static final Handler H=new Handler(Looper.getMainLooper());
    private static final BotSession SESSION=new BotSession();
    private static boolean enabled=false;
    private static long started;
    private static int step;
    private static int failures;
    private static final Runnable LOOP=new Runnable(){
        @Override public void run(){
            if(!enabled)return;
            BotAccessibilityService s=BotAccessibilityService.current();
            if(s==null || SystemClock.elapsedRealtime()-started>MAX_SESSION_MS){stop();return;}
            if(!BotAccessibilityService.isGameForeground() || !s.isLandscape()){
                // Stay armed while switching from Android Settings into the game,
                // but do not touch anything until the actual game window is found.
                H.postDelayed(this,950);return;
            }
            // Conservative control test: attack regularly and move briefly once in a while.
            // BotCore is not supplied with fabricated observations.
            boolean ok=((++step%7)==0)?s.pulseMovement():s.tapAttack();
            if(!ok){
                if(++failures>=3){stop();return;}
            }else failures=0;
            H.postDelayed(this,1500);
        }
    };
    private AutoControl(){}
    public static boolean isEnabled(){return enabled;}
    /** Settings are needed only when the Accessibility Service is not connected. */
    public static boolean start(Context context){
        if(enabled)return true;
        if(!BotAccessibilityService.isAvailable())return false;
        enabled=true;step=0;failures=0;started=SystemClock.elapsedRealtime();
        SESSION.setEnabled(true);
        H.removeCallbacks(LOOP);H.post(LOOP);
        EspOverlayService.refresh();return true;
    }
    public static void stop(){
        enabled=false;SESSION.setEnabled(false);
        H.removeCallbacks(LOOP);EspOverlayService.refresh();
    }
}
