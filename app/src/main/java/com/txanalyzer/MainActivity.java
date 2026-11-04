package com.txanalyzer;

import android.app.Activity;
import android.content.Intent;
import android.graphics.Color;
import android.graphics.drawable.GradientDrawable;
import android.media.projection.MediaProjectionManager;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.provider.Settings;
import android.view.Gravity;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;

public class MainActivity extends Activity {
    private static final int CAPTURE_REQUEST=222;
    private static final int NOTIFICATION_REQUEST=223;
    private TextView status;
    private MediaProjectionManager manager;
    private int dp(float v){return Math.round(getResources().getDisplayMetrics().density*v);}
    private TextView label(String text,int size,int color) {
        TextView v=new TextView(this);v.setText(text);v.setTextSize(size);v.setTextColor(color);return v;
    }
    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        manager=(MediaProjectionManager)getSystemService(MEDIA_PROJECTION_SERVICE);
        LinearLayout layout=new LinearLayout(this);
        layout.setOrientation(LinearLayout.VERTICAL);
        layout.setPadding(dp(22),dp(45),dp(22),dp(20));
        layout.setBackgroundColor(Color.rgb(13,21,37));
        TextView title=label("TX MD5 ANALYZER",25,Color.WHITE);title.setTypeface(null,1);
        layout.addView(title);
        TextView subtitle=label("LIVE • Tự nhận diện lịch sử trên màn hình",14,Color.rgb(112,190,255));
        subtitle.setPadding(0,dp(8),0,dp(20));layout.addView(subtitle);
        TextView description=label("1. Cho phép hiện cửa sổ nổi.\n2. Đồng ý chia sẻ màn hình.\n3. Mở game và mở LỊCH SỬ PHIÊN.\n4. Bong bóng TX tự đọc Tài/Xỉu và các ô nhìn thấy.\n5. Chạm bong bóng để mở rộng thống kê.",15,Color.rgb(225,231,240));
        description.setLineSpacing(dp(4),1f);layout.addView(description);
        Button start=new Button(this);start.setText("BẮT ĐẦU TỰ ĐỘNG NHẬN DIỆN");
        LinearLayout.LayoutParams sp=new LinearLayout.LayoutParams(-1,dp(55));sp.topMargin=dp(25);
        layout.addView(start,sp);start.setOnClickListener(v->begin());
        Button stop=new Button(this);stop.setText("DỪNG VÀ THU HỒI CHIA SẺ");
        LinearLayout.LayoutParams st=new LinearLayout.LayoutParams(-1,dp(54));st.topMargin=dp(10);
        layout.addView(stop,st);stop.setOnClickListener(v->{
            Intent cmd=new Intent(this,CaptureService.class);cmd.setAction(CaptureService.STOP_ACTION);
            startService(cmd);status.setText("Đã yêu cầu dừng chia sẻ màn hình.");
        });
        status=label("Chưa cấp quyền ghi màn hình",13,Color.rgb(128,226,175));
        status.setPadding(0,dp(20),0,dp(20));layout.addView(status);
        TextView privacy=label("Dữ liệu được xử lý trên thiết bị, không gửi lên máy chủ. Chỉ đọc kết quả đã hiển thị; không thể biết chắc kết quả ngẫu nhiên trong tương lai.",12,Color.rgb(162,175,194));
        layout.addView(privacy);
        setContentView(layout);
        if(Build.VERSION.SDK_INT>=33 && checkSelfPermission("android.permission.POST_NOTIFICATIONS")!=getPackageManager().PERMISSION_GRANTED) {
            requestPermissions(new String[]{"android.permission.POST_NOTIFICATIONS"},NOTIFICATION_REQUEST);
        }
    }
    private void begin() {
        if(!Settings.canDrawOverlays(this)){
            status.setText("Vui lòng bật quyền 'Hiển thị trên ứng dụng khác' rồi quay lại.");
            startActivity(new Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION,Uri.parse("package:"+getPackageName())));
            return;
        }
        status.setText("Đang yêu cầu quyền chia sẻ màn hình...");
        startActivityForResult(manager.createScreenCaptureIntent(),CAPTURE_REQUEST);
    }
    @Override protected void onActivityResult(int request,int code,Intent data) {
        super.onActivityResult(request,code,data);
        if(request!=CAPTURE_REQUEST)return;
        if(code==RESULT_OK && data!=null) {
            Intent service=new Intent(this,CaptureService.class);
            service.putExtra("result",code);service.putExtra("data",data);
            if(Build.VERSION.SDK_INT>=26)startForegroundService(service);else startService(service);
            status.setText("Đã cấp quyền. Hãy mở bảng LỊCH SỬ PHIÊN trong game.");
        }else status.setText("Bạn đã từ chối chia sẻ màn hình.");
    }
}
