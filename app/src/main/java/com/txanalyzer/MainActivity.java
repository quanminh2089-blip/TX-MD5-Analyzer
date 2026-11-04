package com.txanalyzer;

import android.animation.ObjectAnimator;
import android.app.Activity;
import android.app.Dialog;
import android.content.Intent;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.net.Uri;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.os.SystemClock;
import android.provider.Settings;
import android.text.InputType;
import android.view.Gravity;
import android.view.Window;
import android.view.WindowManager;
import android.view.animation.LinearInterpolator;
import android.widget.Button;
import android.widget.EditText;
import android.widget.FrameLayout;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Toast;
import android.webkit.WebView;
import android.webkit.WebSettings;
import android.webkit.WebChromeClient;
import android.webkit.WebViewClient;

/** Restore the v0.7 rotating intro and small MinhQuan'z key dialog.
 *  Never expose the previous Matrix/account screen. */
public final class MainActivity extends Activity {
    private static final String KEY = "FreeKey_MinhQuan";
    private static final long INTRO_MS = 3000;
    private final Handler handler = new Handler(Looper.getMainLooper());
    private ObjectAnimator avatarSpin;
    private Dialog keyDialog;
    private Runnable counterTask;
    private boolean accepted = false;
    private boolean launched = false;
    private boolean destroyed = false;

    private int dp(float v){return (int)(v*getResources().getDisplayMetrics().density+.5f);}
    private GradientDrawable shape(int color,int radius){
        GradientDrawable d=new GradientDrawable(); d.setColor(color); d.setCornerRadius(dp(radius));return d;
    }
    private TextView txt(String s,float size,int color){
        TextView t=new TextView(this);t.setText(s);t.setTextSize(size);t.setTextColor(color);return t;
    }
    private ImageView avatar(int size){
        ImageView a=new ImageView(this);a.setImageResource(R.drawable.minhquan_avatar);
        a.setScaleType(ImageView.ScaleType.FIT_CENTER);
        a.setContentDescription("Avatar MinhQuan");
        a.setLayoutParams(new LinearLayout.LayoutParams(dp(size),dp(size)));return a;
    }
    @Override public void onCreate(Bundle state){
        super.onCreate(state);
        getWindow().setStatusBarColor(Color.BLACK);
        getWindow().setNavigationBarColor(Color.BLACK);
        // A key is requested on each fresh launch, like the original v0.7 screen.
        accepted=state!=null && state.getBoolean("accepted",false);
        if(accepted){afterKey();return;}
        showIntro();
        handler.postDelayed(()->{
            if(destroyed||isFinishing())return;
            stopSpin();showKeyHost();showKeyDialog();
        }, INTRO_MS);
    }
    private void showIntro(){
        FrameLayout root=new FrameLayout(this);root.setBackgroundColor(Color.BLACK);
        LinearLayout card=new LinearLayout(this);card.setOrientation(LinearLayout.VERTICAL);
        card.setGravity(Gravity.CENTER_HORIZONTAL);
        card.setPadding(dp(8),dp(11),dp(8),dp(8));
        card.setBackground(shape(0xff302c2b,10));card.setElevation(dp(10));
        root.addView(card,new FrameLayout.LayoutParams(dp(174),dp(100),Gravity.CENTER));
        ImageView image=avatar(46);card.addView(image);
        TextView loading=txt("Loading data from Server...",10.2f,0xffeeeae8);
        loading.setTypeface(Typeface.DEFAULT,Typeface.BOLD);
        loading.setSingleLine(true);loading.setGravity(Gravity.CENTER);
        LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(-1,dp(20));lp.topMargin=dp(8);
        card.addView(loading,lp);setContentView(root);
        avatarSpin=ObjectAnimator.ofFloat(image,"rotation",0f,360f);
        avatarSpin.setDuration(1350);avatarSpin.setRepeatCount(ObjectAnimator.INFINITE);
        avatarSpin.setInterpolator(new LinearInterpolator());avatarSpin.start();
    }
    private void stopSpin(){if(avatarSpin!=null){avatarSpin.cancel();avatarSpin=null;}}
    private void showKeyHost(){
        FrameLayout root=new FrameLayout(this);root.setBackgroundColor(0xff080e19);
        LinearLayout body=new LinearLayout(this);body.setOrientation(LinearLayout.VERTICAL);
        body.setGravity(Gravity.CENTER);body.addView(avatar(104));
        TextView name=txt("MINHQUAN",22,0xff42e6b2);
        name.setGravity(Gravity.CENTER);name.setTypeface(Typeface.DEFAULT,Typeface.BOLD);
        LinearLayout.LayoutParams np=new LinearLayout.LayoutParams(-1,-2);np.topMargin=dp(14);
        body.addView(name,np);root.addView(body,new FrameLayout.LayoutParams(-1,-1));
        setContentView(root);
    }
    private void showKeyDialog(){
        if(destroyed||accepted||isFinishing())return;
        if(keyDialog!=null&&keyDialog.isShowing())return;
        Dialog dialog=new Dialog(this);keyDialog=dialog;
        dialog.requestWindowFeature(Window.FEATURE_NO_TITLE);dialog.setCancelable(false);
        LinearLayout panel=new LinearLayout(this);panel.setOrientation(LinearLayout.VERTICAL);
        panel.setBackground(shape(0xff36312f,11));panel.setClipToOutline(true);
        TextView title=txt("MinhQuan'z",17,Color.WHITE);
        title.setTypeface(Typeface.DEFAULT,Typeface.BOLD);title.setGravity(Gravity.CENTER);
        LinearLayout.LayoutParams tp=new LinearLayout.LayoutParams(-1,dp(27));tp.topMargin=dp(14);panel.addView(title,tp);
        TextView hint=txt("Bấm Vào Nút Get Key Để Lấy Key Free",11.2f,Color.WHITE);
        hint.setGravity(Gravity.CENTER);
        LinearLayout.LayoutParams hp=new LinearLayout.LayoutParams(-1,dp(20));hp.leftMargin=dp(8);hp.rightMargin=dp(8);
        panel.addView(hint,hp);
        TextView counter=txt("-1s",12,Color.WHITE);counter.setGravity(Gravity.CENTER);
        panel.addView(counter,new LinearLayout.LayoutParams(-1,dp(19)));
        EditText key=new EditText(this);key.setSingleLine(true);key.setTextSize(12.3f);
        key.setHint("Nhập key MinhQuan");key.setTextColor(Color.WHITE);
        key.setHintTextColor(0xff9c9da8);
        key.setInputType(InputType.TYPE_CLASS_TEXT|InputType.TYPE_TEXT_FLAG_NO_SUGGESTIONS);
        key.setPadding(dp(12),0,dp(12),0);key.setBackground(shape(0xff1d1e26,7));
        LinearLayout.LayoutParams kp=new LinearLayout.LayoutParams(-1,dp(38));
        kp.topMargin=dp(16);kp.leftMargin=dp(14);kp.rightMargin=dp(14);kp.bottomMargin=dp(16);
        panel.addView(key,kp);
        TextView line=txt("",1,Color.TRANSPARENT);line.setBackgroundColor(0xff615853);
        panel.addView(line,new LinearLayout.LayoutParams(-1,dp(1)));
        LinearLayout actions=new LinearLayout(this);actions.setGravity(Gravity.CENTER);
        panel.addView(actions,new LinearLayout.LayoutParams(-1,dp(45)));
        TextView getKey=txt("Get Key",13.5f,0xffef4b4b);
        getKey.setTypeface(Typeface.DEFAULT,Typeface.BOLD);getKey.setGravity(Gravity.CENTER);
        actions.addView(getKey,new LinearLayout.LayoutParams(0,-1,1));
        getKey.setOnClickListener(v->{key.setText(KEY);key.setSelection(key.getText().length());});
        TextView sep=txt("",1,Color.TRANSPARENT);sep.setBackgroundColor(0xff615853);
        actions.addView(sep,new LinearLayout.LayoutParams(dp(1),-1));
        TextView ok=txt("OK",13.5f,0xff81bcf7);
        ok.setTypeface(Typeface.DEFAULT,Typeface.BOLD);ok.setGravity(Gravity.CENTER);
        actions.addView(ok,new LinearLayout.LayoutParams(0,-1,1));
        ok.setOnClickListener(v->{
            if(!KEY.equals(key.getText().toString().trim())){
                key.setError("Key chưa đúng");Toast.makeText(this,"Key không hợp lệ",Toast.LENGTH_SHORT).show();return;
            }
            accepted=true;stopCounter();dialog.dismiss();keyDialog=null;
            handler.postDelayed(this::afterKey,120);
        });
        dialog.setContentView(panel);
        Window w=dialog.getWindow();
        if(w!=null){
            w.setBackgroundDrawableResource(android.R.color.transparent);
            w.addFlags(WindowManager.LayoutParams.FLAG_DIM_BEHIND);
            WindowManager.LayoutParams p=w.getAttributes();p.dimAmount=.58f;
            p.width=dp(274);p.height=-2;p.gravity=Gravity.CENTER;w.setAttributes(p);
            w.setSoftInputMode(WindowManager.LayoutParams.SOFT_INPUT_STATE_ALWAYS_HIDDEN);
        }
        dialog.setOnDismissListener(d->stopCounter());dialog.show();
        if(dialog.getWindow()!=null)dialog.getWindow().setLayout(dp(274),-2);
        long since=SystemClock.elapsedRealtime();
        counterTask=new Runnable(){@Override public void run(){
            if(destroyed||!dialog.isShowing())return;
            long s=1+(SystemClock.elapsedRealtime()-since)/1000L;
            counter.setText("-"+s+"s");handler.postDelayed(this,200);
        }};
        handler.post(counterTask);
    }
    private void stopCounter(){if(counterTask!=null){handler.removeCallbacks(counterTask);counterTask=null;}}
    private WebView magicWeb;
    private void afterKey(){
        if(!accepted||destroyed||isFinishing()||launched)return;
        launched=true;
        magicWeb=new WebView(this);
        magicWeb.setBackgroundColor(Color.BLACK);
        magicWeb.setWebViewClient(new WebViewClient());
        magicWeb.setWebChromeClient(new WebChromeClient());
        WebSettings ws=magicWeb.getSettings();
        ws.setJavaScriptEnabled(true);
        ws.setDomStorageEnabled(true);
        ws.setAllowFileAccess(true);
        ws.setMediaPlaybackRequiresUserGesture(true);
        ws.setBuiltInZoomControls(false);
        ws.setDisplayZoomControls(false);
        magicWeb.setLayerType(android.view.View.LAYER_TYPE_HARDWARE,null);
        setContentView(magicWeb);
        magicWeb.loadUrl("file:///android_asset/index.html");
    }
    @Override public void onBackPressed(){
        if(magicWeb!=null&&magicWeb.canGoBack())magicWeb.goBack();
        else super.onBackPressed();
    }
    @Override protected void onSaveInstanceState(Bundle state){state.putBoolean("accepted",accepted);super.onSaveInstanceState(state);}
    @Override protected void onDestroy(){
        destroyed=true;handler.removeCallbacksAndMessages(null);stopSpin();stopCounter();
        if(keyDialog!=null){keyDialog.setOnDismissListener(null);keyDialog.dismiss();keyDialog=null;}
        super.onDestroy();
    }
}
