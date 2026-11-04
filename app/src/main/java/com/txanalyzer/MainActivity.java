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
        picture.setContentDescription("Avatar MinhQuan - mặt nạ chiến binh");
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
    private void showSplash(){
        FrameLayout root=new FrameLayout(this);
        root.setBackgroundColor(NAVY);
        LinearLayout group=new LinearLayout(this);group.setGravity(Gravity.CENTER);group.setOrientation(LinearLayout.VERTICAL);
        FrameLayout.LayoutParams place=new FrameLayout.LayoutParams(-1,-2,Gravity.CENTER);
        root.addView(group,place);
        FrameLayout halo=new FrameLayout(this);
        GradientDrawable glow=new GradientDrawable(GradientDrawable.Orientation.TL_BR,new int[]{0xff234865,0xff0d182a,0xff332718});
        glow.setShape(GradientDrawable.OVAL);halo.setBackground(glow);
        group.addView(halo,new LinearLayout.LayoutParams(dp(190),dp(190)));
        ImageView rotating=new ImageView(this);rotating.setImageResource(R.drawable.minhquan_avatar);
        rotating.setScaleType(ImageView.ScaleType.FIT_CENTER);
        rotating.setContentDescription("Biểu tượng MinhQuan đang xoay");
        FrameLayout.LayoutParams pic=new FrameLayout.LayoutParams(dp(158),dp(158),Gravity.CENTER);
        halo.addView(rotating,pic);
        TextView name=text("MINHQUAN",29,Color.WHITE);name.setGravity(Gravity.CENTER);name.setLetterSpacing(.13f);
        name.setTypeface(Typeface.DEFAULT,Typeface.BOLD);
        LinearLayout.LayoutParams np=new LinearLayout.LayoutParams(-1,-2);np.topMargin=dp(26);group.addView(name,np);
        TextView message=text("ĐANG KHỞI ĐỘNG",11,GOLD);message.setLetterSpacing(.18f);message.setGravity(Gravity.CENTER);
        LinearLayout.LayoutParams mp=new LinearLayout.LayoutParams(-1,-2);mp.topMargin=dp(9);group.addView(message,mp);
        TextView privacy=text("Trình đọc lịch sử • Phân tích trên thiết bị",12,SUBTLE);
        privacy.setGravity(Gravity.CENTER);LinearLayout.LayoutParams pp=new LinearLayout.LayoutParams(-1,-2);pp.topMargin=dp(15);group.addView(privacy,pp);
        setContentView(root);
        spin=ObjectAnimator.ofFloat(rotating,"rotation",0f,360f);
        spin.setDuration(1200);
        spin.setRepeatCount(ObjectAnimator.INFINITE);
        spin.setInterpolator(new android.view.animation.LinearInterpolator());spin.start();
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
    /** Centered floating-style dialog within the app, deliberately NOT a system overlay. */
    private void showKeyDialog(){
        if(isFinishing()||isDestroyed())return;
        if(keyDialog!=null&&keyDialog.isShowing())return;
        Dialog dialog=new Dialog(this);keyDialog=dialog;
        dialog.requestWindowFeature(Window.FEATURE_NO_TITLE);
        LinearLayout body=new LinearLayout(this);body.setOrientation(LinearLayout.VERTICAL);
        body.setPadding(dp(20),dp(19),dp(20),dp(17));
        body.setBackground(outlined(0xff20283a,0xff647083,17));
        TextView heading=text("MINHQUAN",19,Color.WHITE);heading.setTypeface(Typeface.DEFAULT,Typeface.BOLD);
        heading.setGravity(Gravity.CENTER);body.addView(heading);
        TextView hint=text("Nhập key để mở công cụ",13,0xffd2d9e6);hint.setGravity(Gravity.CENTER);
        LinearLayout.LayoutParams hintP=new LinearLayout.LayoutParams(-1,-2);hintP.topMargin=dp(7);body.addView(hint,hintP);
        TextView demo=text("Key miễn phí • Không cần tài khoản",11,GOLD);demo.setGravity(Gravity.CENTER);
        LinearLayout.LayoutParams demoP=new LinearLayout.LayoutParams(-1,-2);demoP.topMargin=dp(6);body.addView(demo,demoP);
        EditText input=new EditText(this);
        input.setSingleLine(true);input.setTextColor(Color.WHITE);input.setHintTextColor(0xff8a98ac);
        input.setTextSize(14);input.setInputType(InputType.TYPE_CLASS_TEXT|InputType.TYPE_TEXT_VARIATION_VISIBLE_PASSWORD);
        input.setHint("Nhập key MinhQuan");input.setPadding(dp(11),0,dp(11),0);
        input.setBackground(outlined(0xff0d1726,0xff46536c,9));
        LinearLayout.LayoutParams inP=new LinearLayout.LayoutParams(-1,dp(46));inP.topMargin=dp(17);body.addView(input,inP);
        TextView error=text("",12,0xfff5a4a4);error.setGravity(Gravity.CENTER);
        LinearLayout.LayoutParams errP=new LinearLayout.LayoutParams(-1,-2);errP.topMargin=dp(7);body.addView(error,errP);
        LinearLayout controls=new LinearLayout(this);controls.setOrientation(LinearLayout.HORIZONTAL);
        LinearLayout.LayoutParams rowP=new LinearLayout.LayoutParams(-1,dp(46));rowP.topMargin=dp(10);body.addView(controls,rowP);
        Button get=new Button(this);get.setText("Lấy key");get.setAllCaps(false);get.setTextColor(GOLD);
        get.setBackgroundTintList(ColorStateList.valueOf(0xff323b50));
        LinearLayout.LayoutParams left=new LinearLayout.LayoutParams(0,-1,1);left.rightMargin=dp(7);controls.addView(get,left);
        Button accept=new Button(this);accept.setText("XÁC NHẬN");accept.setAllCaps(false);accept.setTextColor(NAVY);
        accept.setBackgroundTintList(ColorStateList.valueOf(GOLD));controls.addView(accept,new LinearLayout.LayoutParams(0,-1,1));
        get.setOnClickListener(v->{input.setText(DEMO_KEY);input.setSelection(input.length());error.setText("Key miễn phí đã được điền.");});
        accept.setOnClickListener(v->{
            if(DEMO_KEY.equals(input.getText().toString().trim())){
                authenticated=true;dialog.dismiss();if(status!=null)status.setText("Đã mở công cụ. Nhấn Bắt đầu để cấp quyền.");
            }else{error.setText("Key không hợp lệ. Nhấn 'Lấy key' để nhận key miễn phí.");}
        });
        dialog.setContentView(body);
        dialog.setCanceledOnTouchOutside(false);
        dialog.setCancelable(false);
        Window window=dialog.getWindow();
        if(window!=null){window.setBackgroundDrawable(new ColorDrawable(Color.TRANSPARENT));
            window.addFlags(WindowManager.LayoutParams.FLAG_DIM_BEHIND);
            WindowManager.LayoutParams p=window.getAttributes();p.dimAmount=.68f;window.setAttributes(p);
            window.setSoftInputMode(WindowManager.LayoutParams.SOFT_INPUT_STATE_ALWAYS_HIDDEN);
        }
        dialog.show();
        window=dialog.getWindow();if(window!=null){
            int width=Math.min(dp(330),getResources().getDisplayMetrics().widthPixels-dp(34));
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
