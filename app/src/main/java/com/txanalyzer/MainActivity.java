package com.txanalyzer;

import android.app.Activity;
import android.content.Intent;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.net.Uri;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.provider.Settings;
import android.text.InputType;
import android.view.Gravity;
import android.view.View;
import android.view.inputmethod.EditorInfo;
import android.widget.Button;
import android.widget.EditText;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Toast;

/** Only the local key screen. After consent, leave the app and show the small overlay. */
public final class MainActivity extends Activity {
    private static final String KEY = "FreeKey_MinhQuan"; // local-only key, NOT server authentication
    private static final String GAME_PACKAGE = "com.garena.game.kgvn";
    private static final int REQ_OVERLAY = 401;
    private final Handler handler = new Handler(Looper.getMainLooper());
    private boolean opened = false;
    private int dp(float v) { return (int)(v * getResources().getDisplayMetrics().density + .5f); }

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        getWindow().setStatusBarColor(Color.BLACK);
        getWindow().setNavigationBarColor(Color.BLACK);
        if (keyPassed()) {
            if (Settings.canDrawOverlays(this)) {
                handler.post(this::openOverlayAndGame);
            } else {
                showOverlayPermission();
            }
        } else {
            showKeyOnly();
        }
    }

    private boolean keyPassed() {
        return getSharedPreferences("minhquan_local", MODE_PRIVATE).getBoolean("key_accepted",false);
    }

    private GradientDrawable bg(int fill, int border, int radius) {
        GradientDrawable d=new GradientDrawable();
        d.setColor(fill); d.setCornerRadius(dp(radius));
        d.setStroke(dp(1), border);
        return d;
    }

    private LinearLayout screen() {
        LinearLayout root=new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setGravity(Gravity.CENTER);
        root.setPadding(dp(26),dp(22),dp(26),dp(22));
        root.setBackgroundColor(0xff070d10);
        setContentView(root);
        return root;
    }

    private TextView label(String s, int size, int color) {
        TextView t=new TextView(this); t.setText(s); t.setTextSize(size);
        t.setTextColor(color); t.setGravity(Gravity.CENTER);
        return t;
    }

    private Button button(String s) {
        Button b=new Button(this); b.setText(s); b.setAllCaps(false);
        b.setTextSize(15); b.setTextColor(0xff041511);
        b.setBackground(bg(0xff4ce0ae,0xff4ce0ae,12));
        return b;
    }

    private void showKeyOnly() {
        LinearLayout root=screen();
        ImageView img=new ImageView(this);
        img.setImageResource(R.drawable.minhquan_avatar);
        img.setScaleType(ImageView.ScaleType.FIT_CENTER);
        root.addView(img,new LinearLayout.LayoutParams(dp(112),dp(112)));

        TextView name=label("MINHQUAN",23,0xff65e7b9);
        name.setTypeface(Typeface.DEFAULT,Typeface.BOLD);
        LinearLayout.LayoutParams np=new LinearLayout.LayoutParams(-1,-2);np.topMargin=dp(10);
        root.addView(name,np);

        EditText entry=new EditText(this);
        entry.setSingleLine(true);
        entry.setHint("Nhập key để tiếp tục");
        entry.setTextColor(Color.WHITE);
        entry.setHintTextColor(0xff83968d);
        entry.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_FLAG_NO_SUGGESTIONS);
        entry.setImeOptions(EditorInfo.IME_ACTION_DONE);
        entry.setPadding(dp(16),0,dp(16),0);
        entry.setBackground(bg(0xff132320,0xff3e8c71,12));
        LinearLayout.LayoutParams ep=new LinearLayout.LayoutParams(-1,dp(52)); ep.topMargin=dp(28);
        root.addView(entry,ep);

        Button enter=button("Xác nhận key");
        LinearLayout.LayoutParams bp=new LinearLayout.LayoutParams(-1,dp(52)); bp.topMargin=dp(14);
        root.addView(enter,bp);
        View.OnClickListener submit=v -> {
            if (!KEY.equals(entry.getText().toString().trim())) {
                entry.setError("Key không đúng"); return;
            }
            getSharedPreferences("minhquan_local",MODE_PRIVATE).edit()
                    .putBoolean("key_accepted",true).apply();
            if (Settings.canDrawOverlays(this)) openOverlayAndGame();
            else { showOverlayPermission(); askOverlayPermission(); }
        };
        enter.setOnClickListener(submit);
        entry.setOnEditorActionListener((v,action,event) -> { submit.onClick(v); return true; });
    }

    private void showOverlayPermission() {
        LinearLayout root=screen();
        root.addView(label("MINHQUAN",24,0xff4ce0ae));
        TextView hint=label("Cho phép 'Hiển thị trên ứng dụng khác' để mở nút AUTO CHƠI trên game.",15,Color.WHITE);
        LinearLayout.LayoutParams hp=new LinearLayout.LayoutParams(-1,-2);hp.topMargin=dp(24);
        root.addView(hint,hp);
        Button allow=button("Cấp quyền hiển thị");
        LinearLayout.LayoutParams ap=new LinearLayout.LayoutParams(-1,dp(52));ap.topMargin=dp(26);
        root.addView(allow,ap);
        allow.setOnClickListener(v->askOverlayPermission());
    }

    private void askOverlayPermission() {
        if (Settings.canDrawOverlays(this)) {openOverlayAndGame();return;}
        try {
            Intent i=new Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION,
                    Uri.parse("package:"+getPackageName()));
            startActivityForResult(i, REQ_OVERLAY);
        } catch (Exception ex) {
            Toast.makeText(this,"Không mở được trang cấp quyền: "+ex.getMessage(),Toast.LENGTH_LONG).show();
        }
    }

    @Override protected void onActivityResult(int requestCode,int resultCode,Intent data) {
        super.onActivityResult(requestCode,resultCode,data);
        if(requestCode==REQ_OVERLAY && keyPassed() && Settings.canDrawOverlays(this)) {
            openOverlayAndGame();
        }
    }

    @Override protected void onResume() {
        super.onResume();
        if(keyPassed() && Settings.canDrawOverlays(this)) {
            handler.postDelayed(this::openOverlayAndGame,220);
        }
    }

    private void openOverlayAndGame() {
        if(opened || isFinishing() || !keyPassed() || !Settings.canDrawOverlays(this)) return;
        opened=true;
        try { startService(new Intent(this,EspOverlayService.class)); }
        catch(Exception ex) { opened=false;Toast.makeText(this,"Không mở được menu nổi",Toast.LENGTH_LONG).show();return; }
        // Launch the existing Vietnamese Liên Quân app when installed; otherwise return Home.
        Intent game=getPackageManager().getLaunchIntentForPackage(GAME_PACKAGE);
        try {
            if(game!=null) { game.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);startActivity(game); }
            else {
                Intent home=new Intent(Intent.ACTION_MAIN);
                home.addCategory(Intent.CATEGORY_HOME);
                home.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                startActivity(home);
            }
        } catch(Exception ignored) { /* The overlay still works; user can open game manually. */ }
        finish();
    }

    @Override protected void onDestroy(){handler.removeCallbacksAndMessages(null);super.onDestroy();}
}
