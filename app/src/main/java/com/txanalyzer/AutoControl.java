package com.txanalyzer;

import android.content.Context;
import android.os.Handler;
import android.os.Looper;
import android.os.SystemClock;
import com.txanalyzer.bot.BotSession;

/** Conservative, time-limited real gesture test. NOT a full-match AI. */
public final class AutoControl {
    private static final long MAX_SESSION_MS=90_000;
    private static final Handler H=new Handler(Looper.getMainLooper());
    private static final BotSession SESSION=new BotSession();
    private static boolean enabled=false;
    private static long started;
    private static int step;
    private static final Runnable LOOP=new Runnable(){
        @Override public void run(){
            if(!enabled)return;
            BotAccessibilityService service=BotAccessibilityService.isAvailable()
                    ? currentService():null;
            if(service==null || !BotAccessibilityService.isGameForeground() ||
                    !service.isLandscape() || SystemClock.elapsedRealtime()-started>MAX_SESSION_MS) {
                stop();return;
            }
            // Minimal real interaction: alternate an attack tap and occasional joystick pulse.
            // No fabricated observations are provided to BotCore.
            boolean ok=((++step%5)==0) ? service.pulseMovement() : service.tapAttack();
            if(!ok){stop();return;}
            H.postDelayed(this,1600);
        }
    };
    private static BotAccessibilityService currentService(){return BotAccessibilityService.current();}
    private AutoControl(){}
    public static boolean isEnabled(){return enabled;}
    public static boolean start(Context context){
        BotAccessibilityService svc=currentService();
        if(enabled || svc==null || !BotAccessibilityService.isGameForeground() || !svc.isLandscape())return false;
        enabled=true;step=0;started=SystemClock.elapsedRealtime();
        SESSION.setEnabled(true);
        H.removeCallbacks(LOOP);H.postDelayed(LOOP,500);
        EspOverlayService.refresh();return true;
    }
    public static void stop(){
        if(!enabled)return;
        enabled=false;SESSION.setEnabled(false);
        H.removeCallbacks(LOOP);
        EspOverlayService.refresh();
    }
}
