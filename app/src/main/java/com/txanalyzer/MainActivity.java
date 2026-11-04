package com.txanalyzer;

import android.animation.ObjectAnimator;
import android.app.Activity;
import android.app.Dialog;
import android.content.Intent;
import android.content.res.ColorStateList;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.ColorDrawable;
import android.graphics.drawable.GradientDrawable;
import android.media.projection.MediaProjectionManager;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.provider.Settings;
import android.text.InputType;
import android.view.Gravity;
import android.view.Window;
import android.view.WindowManager;
import android.widget.Button;
import android.widget.EditText;
import android.widget.FrameLayout;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;

/** Native startup splash + small centered key dialog; the key is an offline DEMO gate,
 * not a remote license or security system. Screen capture always requires user consent. */
public class MainActivity extends Activity {
    private static final int CAPTURE_REQUEST=222;
    private static final int NOTIFICATION_REQUEST=223;
    private static final long SPLASH_DURATION_MS=3000L;
    private static final String DEMO_KEY="FreeKey_MinhQuan";
    private static final int NAVY=Color.rgb(10,18,32);
    private static final int LIGHT=Color.rgb(236,242,250);
    private static final int SUBTLE=Color.rgb(161,177,199);
    private static final int GOLD=Color.rgb(226,178,97);
    private final Handler ui=new Handler(Looper.getMainLooper());
    private final Runnable openLogin=()->{if(!isFinishing()&&!isDestroyed()){renderDashboard();showKeyDialog();}};
    private ObjectAnimator spin;
    private Dialog keyDialog;
    private TextView status;
    private MediaProjectionManager manager;
    private boolean authenticated=false;

    private int dp(float value){return Math.round(getResources().getDisplayMetrics().density*value);}
    private GradientDrawable rounded(int fill,int radius){
        GradientDrawable d=new GradientDrawable();d.setColor(fill);d.setCornerRadius(dp(radius));return d;
    }
    private GradientDrawable outlined(int fill,int stroke,int radius){
        GradientDrawable d=rounded(fill,radius);d.setStroke(dp(1),stroke);return d;
    }
    private TextView text(String content,float sp,int color){
        TextView v=new TextView(this);v.setText(content);v.setTextSize(sp);v.setTextColor(color);return v;
    }
    private ImageView avatar(int sizeDp){
        ImageView picture=new ImageView(this);
        picture.setImageResource(R.drawable.minhquan_avatar);
        picture.setScaleType(ImageView.ScaleType.FIT_CENTER);
        picture.setContentDescription("Avatar MinhQuan - mặt nạ xanh");
        picture.setLayoutParams(new LinearLayout.LayoutParams(dp(sizeDp),dp(sizeDp)));
        return picture;
    }
    @Override public void onCreate(Bundle state){
        super.onCreate(state);
        manager=(MediaProjectionManager)getSystemService(MEDIA_PROJECTION_SERVICE);
        if(state!=null && state.getBoolean("authenticated",false)){
            authenticated=true;renderDashboard();return;
        }
        showSplash();
        ui.postDelayed(openLogin,SPLASH_DURATION_MS);
    }
    /** Small floating loading card matching the user's reference (within app, not over game).
     * The 3-second timer is an intro animation, not a real network request. */
    private void showSplash(){
        FrameLayout root=new FrameLayout(this);
        root.setBackgroundColor(Color.BLACK);

        // Warm bronze logo behind the compact centered loading popup, like the reference layout.
        LinearLayout brand=new LinearLayout(this);
        brand.setGravity(Gravity.CENTER);
        brand.setOrientation(LinearLayout.VERTICAL);
        TextView word=text("MINHQUAN",34,0xffb98865);
        word.setGravity(Gravity.CENTER);
        word.setTypeface(Typeface.DEFAULT,Typeface.BOLD);
        word.setLetterSpacing(.12f);
        brand.addView(word,new LinearLayout.LayoutParams(-2,-2));
        TextView caption=text("MD5 ANALYZER",11,0xffb99c84);
        caption.setGravity(Gravity.CENTER);
        caption.setTypeface(Typeface.DEFAULT,Typeface.BOLD);
        caption.setLetterSpacing(.25f);
        LinearLayout.LayoutParams cp=new LinearLayout.LayoutParams(-2,-2);
        cp.topMargin=dp(2);
        brand.addView(caption,cp);
        root.addView(brand,new FrameLayout.LayoutParams(-1,-2,Gravity.CENTER));

        // The entire progress box is deliberately small: 174 x 100 dp.
        LinearLayout loading=new LinearLayout(this);
        loading.setOrientation(LinearLayout.VERTICAL);
        loading.setGravity(Gravity.CENTER_HORIZONTAL);
        loading.setPadding(dp(8),dp(11),dp(8),dp(9));
        loading.setBackground(rounded(0xff302a29,10));
        loading.setElevation(dp(10));
        FrameLayout.LayoutParams card=new FrameLayout.LayoutParams(dp(174),dp(100),Gravity.CENTER);
        root.addView(loading,card);

        FrameLayout avatarHolder=new FrameLayout(this);
        LinearLayout.LayoutParams holderParams=new LinearLayout.LayoutParams(dp(46),dp(46));
        loading.addView(avatarHolder,holderParams);
        ImageView rotating=new ImageView(this);
        rotating.setImageResource(R.drawable.minhquan_avatar);
        rotating.setScaleType(ImageView.ScaleType.FIT_CENTER);
        rotating.setContentDescription("Ảnh mặt nạ xanh MinhQuan đang xoay");
        avatarHolder.addView(rotating,new FrameLayout.LayoutParams(-1,-1,Gravity.CENTER));

        TextView message=text("Loading data from Server...",10.5f,0xfff0e8e4);
        message.setSingleLine(true);
        message.setGravity(Gravity.CENTER);
        message.setTypeface(Typeface.DEFAULT,Typeface.BOLD);
        message.setIncludeFontPadding(false);
        LinearLayout.LayoutParams label=new LinearLayout.LayoutParams(-1,dp(20));
        label.topMargin=dp(8);
        loading.addView(message,label);
        // Text imitates reference presentation only; the app does not contact a server.
        setContentView(root);
        spin=ObjectAnimator.ofFloat(rotating,"rotation",0f,360f);
        spin.setDuration(1450);
        spin.setRepeatCount(ObjectAnimator.INFINITE);
        spin.setInterpolator(new android.view.animation.LinearInterpolator());
        spin.start();
    }
    private void renderDashboard(){
        if(spin!=null){spin.cancel();spin=null;}
        ScrollView scroll=new ScrollView(this);
        scroll.setFillViewport(true);scroll.setBackgroundColor(NAVY);
        LinearLayout content=new LinearLayout(this);content.setPadding(dp(22),dp(32),dp(22),dp(28));
        content.setOrientation(LinearLayout.VERTICAL);content.setGravity(Gravity.CENTER_HORIZONTAL);
        scroll.addView(content);
        ImageView pic=avatar(102);content.addView(pic);
        TextView header=text("MINHQUAN",26,Color.WHITE);header.setTypeface(Typeface.DEFAULT,Typeface.BOLD);
        header.setLetterSpacing(.1f);header.setGravity(Gravity.CENTER);
        LinearLayout.LayoutParams h=new LinearLayout.LayoutParams(-1,-2);h.topMargin=dp(14);content.addView(header,h);
        TextView line=text("TX MD5  •  TRÌNH ĐỌC LỊCH SỬ",12,GOLD);line.setGravity(Gravity.CENTER);
        LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(-1,-2);lp.topMargin=dp(7);content.addView(line,lp);
        LinearLayout card=new LinearLayout(this);card.setOrientation(LinearLayout.VERTICAL);card.setPadding(dp(18),dp(20),dp(18),dp(18));
        card.setBackground(outlined(0xff17243a,0xff2d4057,18));
        LinearLayout.LayoutParams cp=new LinearLayout.LayoutParams(-1,-2);cp.topMargin=dp(27);content.addView(card,cp);
        TextView sub=text("NHẬN DIỆN TỰ ĐỘNG",16,LIGHT);sub.setTypeface(Typeface.DEFAULT,Typeface.BOLD);card.addView(sub);
        TextView instructions=text("Cấp quyền hiển thị nổi và ghi màn hình, sau đó mở bảng LỊCH SỬ PHIÊN trong game. Bong bóng MinhQuan sẽ cập nhật kết quả đã hiển thị.",14,SUBTLE);
        instructions.setLineSpacing(dp(4),1.06f);
        LinearLayout.LayoutParams ip=new LinearLayout.LayoutParams(-1,-2);ip.topMargin=dp(12);card.addView(instructions,ip);
        Button start=new Button(this);start.setText("BẮT ĐẦU NHẬN DIỆN");start.setAllCaps(false);
        start.setTextColor(NAVY);start.setBackgroundTintList(ColorStateList.valueOf(GOLD));
        LinearLayout.LayoutParams bp=new LinearLayout.LayoutParams(-1,dp(52));bp.topMargin=dp(22);card.addView(start,bp);
        start.setOnClickListener(v->{if(authenticated)begin();else showKeyDialog();});
        Button stop=new Button(this);stop.setText("DỪNG CHỤP MÀN HÌNH");stop.setAllCaps(false);
        stop.setTextColor(LIGHT);stop.setBackgroundTintList(ColorStateList.valueOf(0xff34445d));
        LinearLayout.LayoutParams sp=new LinearLayout.LayoutParams(-1,dp(50));sp.topMargin=dp(9);card.addView(stop,sp);
        stop.setOnClickListener(v->{if(!authenticated){showKeyDialog();return;}
            Intent command=new Intent(this,CaptureService.class);command.setAction(CaptureService.STOP_ACTION);
            startService(command);status.setText("Đã yêu cầu dừng chia sẻ màn hình.");});
        status=text("Chưa bắt đầu phiên nhận diện",13,0xff9dd2b0);
        LinearLayout.LayoutParams statusP=new LinearLayout.LayoutParams(-1,-2);statusP.topMargin=dp(16);content.addView(status,statusP);
        TextView note=text("Chỉ đọc kết quả đã xuất hiện; không đảm bảo dự đoán kết quả tương lai. Ứng dụng không gửi ảnh màn hình lên máy chủ.",12,SUBTLE);
        note.setLineSpacing(dp(3),1f);LinearLayout.LayoutParams noteP=new LinearLayout.LayoutParams(-1,-2);noteP.topMargin=dp(17);content.addView(note,noteP);
        setContentView(scroll);
    }
    /** A compact, native, centered key dialog styled after the reference screenshot.
     * This is a window inside MinhQuan, not a system-wide popup on top of other apps.
     */
    private void showKeyDialog(){
        if(isFinishing()||isDestroyed())return;
        if(keyDialog!=null&&keyDialog.isShowing())return;

        final Dialog dialog=new Dialog(this);
        keyDialog=dialog;
        dialog.requestWindowFeature(Window.FEATURE_NO_TITLE);

        final int dialogColor=Color.rgb(57,52,47);
        final int rule=0xff58524b;
        final LinearLayout panel=new LinearLayout(this);
        panel.setOrientation(LinearLayout.VERTICAL);
        panel.setBackground(rounded(dialogColor,12));
        panel.setClipToOutline(true);

        TextView title=text("MinhQuan'z",17,Color.WHITE);
        title.setTypeface(Typeface.DEFAULT,Typeface.BOLD);
        title.setGravity(Gravity.CENTER);
        LinearLayout.LayoutParams titleLayout=new LinearLayout.LayoutParams(-1,dp(25));
        titleLayout.topMargin=dp(15);
        titleLayout.leftMargin=dp(9);
        titleLayout.rightMargin=dp(9);
        panel.addView(title,titleLayout);

        TextView instructions=text("Bấm Vào Nút Get Key Để Lấy Key Free",11.5f,0xfff1ece7);
        instructions.setTypeface(Typeface.DEFAULT,Typeface.BOLD);
        instructions.setGravity(Gravity.CENTER);
        instructions.setSingleLine(false);
        LinearLayout.LayoutParams instructionsLayout=new LinearLayout.LayoutParams(-1,-2);
        instructionsLayout.leftMargin=dp(10);
        instructionsLayout.rightMargin=dp(10);
        instructionsLayout.topMargin=dp(1);
        panel.addView(instructions,instructionsLayout);

        // The reference's '- 18s' is reproduced as a static visual label.
        // No fictitious key expiry or countdown is implied.
        TextView referenceLabel=text("- 18s",11,0xfff1ece7);
        referenceLabel.setGravity(Gravity.CENTER);
        LinearLayout.LayoutParams labelLayout=new LinearLayout.LayoutParams(-1,dp(20));
        panel.addView(referenceLabel,labelLayout);

        final EditText input=new EditText(this);
        input.setSingleLine(true);
        input.setTextColor(Color.WHITE);
        input.setHintTextColor(0xff93939c);
        input.setTextSize(12.5f);
        input.setInputType(InputType.TYPE_CLASS_TEXT|InputType.TYPE_TEXT_VARIATION_VISIBLE_PASSWORD);
        input.setHint("Nhập key MinhQuan");
        input.setPadding(dp(10),0,dp(9),0);
        input.setSelectAllOnFocus(false);
        input.setBackground(rounded(0xff1c1c23,6));
        LinearLayout.LayoutParams inputLayout=new LinearLayout.LayoutParams(-1,dp(36));
        inputLayout.leftMargin=dp(14);
        inputLayout.rightMargin=dp(14);
        inputLayout.topMargin=dp(14);
        inputLayout.bottomMargin=dp(15);
        panel.addView(input,inputLayout);

        android.view.View horizontalRule=new android.view.View(this);
        horizontalRule.setBackgroundColor(rule);
        panel.addView(horizontalRule,new LinearLayout.LayoutParams(-1,dp(1)));

        LinearLayout buttons=new LinearLayout(this);
        buttons.setOrientation(LinearLayout.HORIZONTAL);
        buttons.setGravity(Gravity.CENTER);
        panel.addView(buttons,new LinearLayout.LayoutParams(-1,dp(45)));

        TextView getKey=text("Get Key",14,0xffd32129);
        getKey.setTypeface(Typeface.DEFAULT,Typeface.BOLD);
        getKey.setGravity(Gravity.CENTER);
        getKey.setClickable(true);
        getKey.setFocusable(true);
        getKey.setContentDescription("Get Key - điền key miễn phí");
        buttons.addView(getKey,new LinearLayout.LayoutParams(0,-1,1f));

        android.view.View verticalRule=new android.view.View(this);
        verticalRule.setBackgroundColor(rule);
        buttons.addView(verticalRule,new LinearLayout.LayoutParams(dp(1),-1));

        TextView ok=text("OK",14,0xff85bffe);
        ok.setTypeface(Typeface.DEFAULT,Typeface.BOLD);
        ok.setGravity(Gravity.CENTER);
        ok.setClickable(true);
        ok.setFocusable(true);
        buttons.addView(ok,new LinearLayout.LayoutParams(0,-1,1f));

        getKey.setOnClickListener(v->{
            input.setText(DEMO_KEY);
            input.setSelection(input.length());
            Toast.makeText(this,"Đã điền key miễn phí",Toast.LENGTH_SHORT).show();
        });
        ok.setOnClickListener(v->{
            if(DEMO_KEY.equals(input.getText().toString().trim())){
                authenticated=true;
                dialog.dismiss();
                if(status!=null)status.setText("Đã mở công cụ. Nhấn Bắt đầu để cấp quyền.");
            }else{
                input.setError("Key không hợp lệ. Bấm Get Key để lấy key miễn phí.");
            }
        });

        dialog.setContentView(panel);
        dialog.setCanceledOnTouchOutside(false);
        dialog.setCancelable(false);
        Window window=dialog.getWindow();
        if(window!=null){
            window.setBackgroundDrawable(new ColorDrawable(Color.TRANSPARENT));
            window.addFlags(WindowManager.LayoutParams.FLAG_DIM_BEHIND);
            WindowManager.LayoutParams attributes=window.getAttributes();
            attributes.dimAmount=.58f;
            window.setAttributes(attributes);
            window.setSoftInputMode(WindowManager.LayoutParams.SOFT_INPUT_STATE_ALWAYS_HIDDEN);
        }
        dialog.show();
        window=dialog.getWindow();
        if(window!=null){
            int width=Math.min(dp(278),getResources().getDisplayMetrics().widthPixels-dp(32));
            window.setLayout(width,WindowManager.LayoutParams.WRAP_CONTENT);
            window.setGravity(Gravity.CENTER);
        }
    }
    private void begin(){
        if(Build.VERSION.SDK_INT>=33 &&
                checkSelfPermission("android.permission.POST_NOTIFICATIONS")!=getPackageManager().PERMISSION_GRANTED){
            requestPermissions(new String[]{"android.permission.POST_NOTIFICATIONS"},NOTIFICATION_REQUEST);
            return;
        }
        beginCaptureConsent();
    }
    @Override public void onRequestPermissionsResult(int request,String[] permissions,int[] grantResults){
        super.onRequestPermissionsResult(request,permissions,grantResults);
        if(request==NOTIFICATION_REQUEST && authenticated)beginCaptureConsent();
    }
    private void beginCaptureConsent(){
        if(!Settings.canDrawOverlays(this)){
            status.setText("Cấp quyền 'Hiển thị trên ứng dụng khác', sau đó quay lại bấm Bắt đầu.");
            startActivity(new Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION,Uri.parse("package:"+getPackageName())));
            return;
        }
        status.setText("Đang yêu cầu quyền chia sẻ màn hình...");
        startActivityForResult(manager.createScreenCaptureIntent(),CAPTURE_REQUEST);
    }
    @Override protected void onActivityResult(int request,int code,Intent data){
        super.onActivityResult(request,code,data);
        if(request!=CAPTURE_REQUEST)return;
        if(code==RESULT_OK && data!=null){
            Intent service=new Intent(this,CaptureService.class);
            service.putExtra("result",code);service.putExtra("data",data);
            if(Build.VERSION.SDK_INT>=26)startForegroundService(service);else startService(service);
            if(status!=null)status.setText("Đã cấp quyền. Hãy mở bảng LỊCH SỬ PHIÊN trong game.");
        }else if(status!=null)status.setText("Bạn đã từ chối chia sẻ màn hình.");
    }
    @Override protected void onSaveInstanceState(Bundle state){super.onSaveInstanceState(state);state.putBoolean("authenticated",authenticated);}
    @Override protected void onDestroy(){ui.removeCallbacks(openLogin);if(spin!=null)spin.cancel();if(keyDialog!=null){keyDialog.dismiss();keyDialog=null;}super.onDestroy();}
}
