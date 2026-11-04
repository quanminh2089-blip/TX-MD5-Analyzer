package com.txanalyzer;

import android.Manifest;
import android.animation.ObjectAnimator;
import android.app.Activity;
import android.net.Uri;
import android.provider.Settings;
import android.app.Dialog;
import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.content.res.ColorStateList;
import android.graphics.Color;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.widget.RemoteViews;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.os.Build;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.os.SystemClock;
import android.text.InputType;
import android.view.Gravity;
import android.view.View;
import android.view.Window;
import android.view.WindowManager;
import android.view.animation.LinearInterpolator;
import android.widget.Button;
import android.widget.EditText;
import android.widget.FrameLayout;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;

/**
 * MinhQuan v0.7 — native Android UI prototype.
 * Offline key and account are for local demonstration only. No account server,
 * network port scans, screen capture, prediction, or remote session is used.
 * The Matrix panel is explicitly a VISUAL SIMULATION.
 */
public class MainActivity extends Activity {
    private static final String DEMO_KEY = "FreeKey_MinhQuan";
    private static final String DEMO_USER = "MinhQuan08";
    private static final String DEMO_HASH = "ef7fdfa1d814267f512e139b442628a00072953caa0f04b4f041229c446be3a2";
    private static final String DEMO_SALT = "MinhQuan-local-demo-v0.7|";
    private static final String CHANNEL_ID = "minhquan_login_v2";
    private static final int REQUEST_NOTIFICATIONS = 40;
    private static final long INTRO_MILLIS = 3000;
    private static final int BG = 0xff080e19;
    private static final int PANEL = 0xff142035;
    private static final int BORDER = 0xff2a4152;
    private static final int WHITE = 0xfff4f8fd;
    private static final int MUTED = 0xff96abc2;
    private static final int GREEN = 0xff42e6b2;
    private static final int INPUT = 0xff0d1624;
    private static final int DIALOG_BG = 0xff36312f;

    private final Handler handler = new Handler(Looper.getMainLooper());
    private Dialog keyDialog;
    private ObjectAnimator avatarSpin;
    private Runnable timerRunnable;
    private Runnable introRunnable;
    private long counterStarted;
    private boolean keyAccepted = false;
    private boolean consoleOpen = false;
    private MatrixRainView rainView;
    private Runnable consoleRunnable;
    private boolean notifyAfterPermission = false;
    private boolean isDestroyedNow = false;

    private int dp(float v) {
        return (int) (getResources().getDisplayMetrics().density * v + 0.5f);
    }

    private GradientDrawable shape(int color, float radius) {
        GradientDrawable d = new GradientDrawable();
        d.setColor(color);
        d.setCornerRadius(dp(radius));
        return d;
    }

    private GradientDrawable outlined(int color, int stroke, float radius) {
        GradientDrawable d = shape(color, radius);
        d.setStroke(dp(1), stroke);
        return d;
    }

    private TextView text(String value, float size, int color) {
        TextView t = new TextView(this);
        t.setText(value);
        t.setTextSize(size);
        t.setTextColor(color);
        return t;
    }

    private ImageView avatar(int size) {
        ImageView image = new ImageView(this);
        image.setImageResource(R.drawable.minhquan_avatar);
        image.setScaleType(ImageView.ScaleType.FIT_CENTER);
        image.setContentDescription("Avatar mặt nạ xanh MinhQuan");
        image.setLayoutParams(new LinearLayout.LayoutParams(dp(size), dp(size)));
        return image;
    }

    @Override
    public void onCreate(Bundle state) {
        super.onCreate(state);
        getWindow().setStatusBarColor(Color.BLACK);
        getWindow().setNavigationBarColor(Color.BLACK);
        createNotificationChannel();
        if (state != null && state.getBoolean("keyAccepted", false)) {
            keyAccepted = true;
            consoleOpen = state.getBoolean("consoleOpen", false);
            if (consoleOpen) showMatrixScreen();
            else showAccountScreen();
        } else {
            showIntro();
            introRunnable = () -> {
                if (!isDestroyedNow && !isFinishing()) {
                    stopAvatarSpin();
                    showAccountScreen();
                    showKeyDialog();
                }
            };
            handler.postDelayed(introRunnable, INTRO_MILLIS);
        }
    }

    /** Black background only: no golden brand text behind loading card. */
    private void showIntro() {
        FrameLayout root = new FrameLayout(this);
        root.setBackgroundColor(Color.BLACK);

        LinearLayout card = new LinearLayout(this);
        card.setOrientation(LinearLayout.VERTICAL);
        card.setGravity(Gravity.CENTER_HORIZONTAL);
        card.setPadding(dp(8), dp(11), dp(8), dp(8));
        card.setBackground(shape(0xff302c2b, 10));
        card.setElevation(dp(10));
        root.addView(card, new FrameLayout.LayoutParams(dp(174), dp(100), Gravity.CENTER));

        ImageView image = avatar(46);
        card.addView(image);

        TextView loading = text("Loading data from Server...", 10.2f, 0xffeeeae8);
        loading.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        loading.setSingleLine(true);
        loading.setGravity(Gravity.CENTER);
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(-1, dp(20));
        lp.topMargin = dp(8);
        card.addView(loading, lp);

        setContentView(root);
        avatarSpin = ObjectAnimator.ofFloat(image, "rotation", 0f, 360f);
        avatarSpin.setDuration(1350);
        avatarSpin.setRepeatCount(ObjectAnimator.INFINITE);
        avatarSpin.setInterpolator(new LinearInterpolator());
        avatarSpin.start();
    }

    private void stopAvatarSpin() {
        if (avatarSpin != null) {
            avatarSpin.cancel();
            avatarSpin = null;
        }
    }

    private void showAccountScreen() {
        ScrollView scroll = new ScrollView(this);
        scroll.setFillViewport(true);
        scroll.setBackgroundColor(BG);
        scroll.setClipToPadding(false);

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setGravity(Gravity.CENTER_HORIZONTAL);
        root.setPadding(dp(23), dp(38), dp(23), dp(34));
        scroll.addView(root, new ScrollView.LayoutParams(-1, -1));

        root.addView(avatar(112));
        TextView name = text("MINHQUAN", 29, WHITE);
        name.setTypeface(Typeface.create("sans-serif-medium", Typeface.BOLD));
        name.setLetterSpacing(0.12f);
        name.setGravity(Gravity.CENTER);
        LinearLayout.LayoutParams nameParams = new LinearLayout.LayoutParams(-1, -2);
        nameParams.topMargin = dp(13);
        root.addView(name, nameParams);

        LinearLayout form = new LinearLayout(this);
        form.setOrientation(LinearLayout.VERTICAL);
        form.setPadding(dp(20), dp(24), dp(20), dp(24));
        form.setBackground(outlined(PANEL, BORDER, 20));
        LinearLayout.LayoutParams formParams = new LinearLayout.LayoutParams(-1, -2);
        formParams.topMargin = dp(35);
        root.addView(form, formParams);

        TextView heading = text("Đăng nhập tài khoản", 20, WHITE);
        heading.setTypeface(Typeface.create("sans-serif-medium", Typeface.BOLD));
        form.addView(heading);
        TextView userLabel = text("TÊN NGƯỜI DÙNG", 11.5f, MUTED);
        userLabel.setLetterSpacing(0.08f);
        LinearLayout.LayoutParams ulp = new LinearLayout.LayoutParams(-1, -2);
        ulp.topMargin = dp(21);
        form.addView(userLabel, ulp);

        EditText username = new EditText(this);
        username.setSingleLine(true);
        username.setTextSize(14.5f);
        username.setTextColor(WHITE);
        username.setHintTextColor(0xff61748a);
        username.setHint("Nhập tên người dùng");
        username.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_FLAG_NO_SUGGESTIONS);
        username.setPadding(dp(15), 0, dp(15), 0);
        username.setBackground(outlined(INPUT, BORDER, 11));
        LinearLayout.LayoutParams uep = new LinearLayout.LayoutParams(-1, dp(51));
        uep.topMargin = dp(9);
        form.addView(username, uep);

        TextView passwordLabel = text("MẬT KHẨU", 11.5f, MUTED);
        passwordLabel.setLetterSpacing(0.08f);
        LinearLayout.LayoutParams plp = new LinearLayout.LayoutParams(-1, -2);
        plp.topMargin = dp(20);
        form.addView(passwordLabel, plp);

        LinearLayout passwordRow = new LinearLayout(this);
        passwordRow.setGravity(Gravity.CENTER_VERTICAL);
        passwordRow.setOrientation(LinearLayout.HORIZONTAL);
        passwordRow.setBackground(outlined(INPUT, BORDER, 11));
        LinearLayout.LayoutParams prp = new LinearLayout.LayoutParams(-1, dp(51));
        prp.topMargin = dp(9);
        form.addView(passwordRow, prp);

        EditText password = new EditText(this);
        password.setSingleLine(true);
        password.setTextSize(14.5f);
        password.setTextColor(WHITE);
        password.setHintTextColor(0xff61748a);
        password.setHint("Nhập mật khẩu");
        password.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_VARIATION_PASSWORD);
        password.setPadding(dp(15), 0, dp(4), 0);
        password.setBackgroundColor(Color.TRANSPARENT);
        passwordRow.addView(password, new LinearLayout.LayoutParams(0, -1, 1));

        TextView showHide = text("Hiện", 12, GREEN);
        showHide.setGravity(Gravity.CENTER);
        showHide.setContentDescription("Hiện hoặc ẩn mật khẩu");
        showHide.setPadding(dp(5), 0, dp(13), 0);
        passwordRow.addView(showHide, new LinearLayout.LayoutParams(-2, -1));
        final boolean[] passwordVisible = {false};
        showHide.setOnClickListener(v -> {
            passwordVisible[0] = !passwordVisible[0];
            password.setInputType(InputType.TYPE_CLASS_TEXT |
                    (passwordVisible[0] ? InputType.TYPE_TEXT_VARIATION_VISIBLE_PASSWORD
                            : InputType.TYPE_TEXT_VARIATION_PASSWORD));
            password.setSelection(password.getText().length());
            showHide.setText(passwordVisible[0] ? "Ẩn" : "Hiện");
        });

        Button login = new Button(this);
        login.setText("ĐĂNG NHẬP");
        login.setTextSize(14);
        login.setAllCaps(false);
        login.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        login.setTextColor(0xff0b1b20);
        login.setBackgroundTintList(ColorStateList.valueOf(GREEN));
        LinearLayout.LayoutParams loginParams = new LinearLayout.LayoutParams(-1, dp(52));
        loginParams.topMargin = dp(28);
        form.addView(login, loginParams);
        login.setOnClickListener(v -> {
            String enteredUser = username.getText().toString().trim();
            String enteredPassword = password.getText().toString();
            if (enteredUser.isEmpty()) {
                username.setError("Nhập tên người dùng");
                username.requestFocus();
                return;
            }
            if (enteredPassword.isEmpty()) {
                password.setError("Nhập mật khẩu");
                password.requestFocus();
                return;
            }
            if (verifyDemoAccount(enteredUser, enteredPassword)) {
                hideKeyboard();
                consoleOpen = true;
                showMatrixScreen();
            } else {
                password.setText("");
                password.setError("Thông tin đăng nhập không đúng");
                Toast.makeText(this, "Tên người dùng hoặc mật khẩu không đúng", Toast.LENGTH_LONG).show();
            }
        });

        LinearLayout contact = new LinearLayout(this);
        contact.setOrientation(LinearLayout.VERTICAL);
        contact.setGravity(Gravity.CENTER);
        contact.setPadding(dp(12), dp(14), dp(12), dp(14));
        LinearLayout.LayoutParams contactParams = new LinearLayout.LayoutParams(-1, -2);
        contactParams.topMargin = dp(20);
        root.addView(contact, contactParams);
        String[] contacts = {
                "Admin: Nguyễn Minh Quân",
                "Zalo: 0899174526",
                "Telegram: @mquan08"
        };
        for (String line : contacts) {
            TextView item = text(line, 12.3f, MUTED);
            item.setGravity(Gravity.CENTER);
            item.setPadding(0, dp(3), 0, dp(3));
            contact.addView(item, new LinearLayout.LayoutParams(-1, -2));
        }

        setContentView(scroll);
    }

    /** Offline demonstration credential check; NOT a secure production login. */
    private boolean verifyDemoAccount(String username, String password) {
        if (!DEMO_USER.equals(username)) return false;
        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            byte[] bytes = digest.digest((DEMO_SALT + username + "|" + password)
                    .getBytes(StandardCharsets.UTF_8));
            StringBuilder result = new StringBuilder();
            for (byte b : bytes) result.append(String.format(java.util.Locale.ROOT, "%02x", b & 255));
            return MessageDigest.isEqual(result.toString().getBytes(StandardCharsets.UTF_8),
                    DEMO_HASH.getBytes(StandardCharsets.UTF_8));
        } catch (NoSuchAlgorithmException ex) {
            return false;
        }
    }

    private void hideKeyboard() {
        android.view.inputmethod.InputMethodManager keyboard =
                (android.view.inputmethod.InputMethodManager) getSystemService(INPUT_METHOD_SERVICE);
        if (keyboard != null && getCurrentFocus() != null)
            keyboard.hideSoftInputFromWindow(getCurrentFocus().getWindowToken(), 0);
    }

    /** Terminal aesthetic only — all ports and handshakes below are simulated. */
    private void showMatrixScreen() {
        if (consoleRunnable != null) handler.removeCallbacks(consoleRunnable);
        if (rainView != null) rainView.stop();
        FrameLayout screen = new FrameLayout(this);
        screen.setBackgroundColor(0xff030b0c);
        rainView = new MatrixRainView(this);
        screen.addView(rainView, new FrameLayout.LayoutParams(-1, -1));
        ScrollView scroll = new ScrollView(this);
        scroll.setFillViewport(true);
        screen.addView(scroll, new FrameLayout.LayoutParams(-1, -1));
        LinearLayout layout = new LinearLayout(this);
        layout.setOrientation(LinearLayout.VERTICAL);
        layout.setGravity(Gravity.CENTER_HORIZONTAL);
        layout.setPadding(dp(19), dp(23), dp(19), dp(25));
        scroll.addView(layout);

        ImageView logo = avatar(76);
        layout.addView(logo);
        TextView head = text("MINHQUAN // TERMINAL", 19, 0xffd7fff0);
        head.setTypeface(Typeface.create("monospace", Typeface.BOLD));
        head.setGravity(Gravity.CENTER);
        LinearLayout.LayoutParams hlp = new LinearLayout.LayoutParams(-1,-2);
        hlp.topMargin = dp(10);
        layout.addView(head,hlp);
        TextView sub = text("SYSTEM VISUALIZATION • LOCAL DEMO", 10.5f, GREEN);
        sub.setTypeface(Typeface.MONOSPACE);
        sub.setGravity(Gravity.CENTER);
        LinearLayout.LayoutParams slp = new LinearLayout.LayoutParams(-1,-2);
        slp.topMargin=dp(5);
        layout.addView(sub,slp);

        LinearLayout terminal = new LinearLayout(this);
        terminal.setOrientation(LinearLayout.VERTICAL);
        terminal.setPadding(dp(15),dp(15),dp(15),dp(16));
        terminal.setBackground(outlined(0xed061b18,0xff176d54,15));
        LinearLayout.LayoutParams tLp = new LinearLayout.LayoutParams(-1,-2);
        tLp.topMargin = dp(24);
        layout.addView(terminal,tLp);
        LinearLayout toolbar = new LinearLayout(this);
        toolbar.setOrientation(LinearLayout.HORIZONTAL);
        toolbar.setGravity(Gravity.CENTER_VERTICAL);
        terminal.addView(toolbar,new LinearLayout.LayoutParams(-1,dp(28)));
        for (int c : new int[]{0xfff36e62,0xffefbd50,0xff3eeaa5}) {
            TextView dot = text("●",14,c);
            dot.setPadding(0,0,dp(7),0);
            toolbar.addView(dot);
        }
        TextView label=text("  minhquan@local  ~  demo",11,0xff89eecb);
        label.setTypeface(Typeface.MONOSPACE);
        toolbar.addView(label);
        View separator = new View(this);
        separator.setBackgroundColor(0xff1d664f);
        LinearLayout.LayoutParams sepLp = new LinearLayout.LayoutParams(-1,dp(1));
        sepLp.topMargin=dp(4);sepLp.bottomMargin=dp(11);
        terminal.addView(separator,sepLp);
        TextView log = text("",11.5f,0xffb0ffd8);
        log.setTypeface(Typeface.MONOSPACE);
        log.setLineSpacing(dp(4),1.0f);
        log.setMinHeight(dp(218));
        terminal.addView(log,new LinearLayout.LayoutParams(-1,-2));

        TextView state = text("● ĐANG KHỞI TẠO MÔ PHỎNG",11.5f,0xffffd18f);
        state.setGravity(Gravity.CENTER);
        state.setTypeface(Typeface.MONOSPACE);
        LinearLayout.LayoutParams stateLp = new LinearLayout.LayoutParams(-1,-2);
        stateLp.topMargin=dp(19);
        layout.addView(state,stateLp);
        TextView hint = text("Các cổng và trạng thái chỉ là hiệu ứng hiển thị. Ứng dụng không thực hiện kết nối hoặc quét mạng.",11,MUTED);
        hint.setGravity(Gravity.CENTER);
        LinearLayout.LayoutParams hintLp = new LinearLayout.LayoutParams(-1,-2);
        hintLp.topMargin=dp(12);
        layout.addView(hint,hintLp);

        Button overlay = new Button(this);
        overlay.setText("BẬT / TẮT MENU NỔI TRÊN GAME");
        overlay.setAllCaps(false);
        overlay.setTextColor(0xff09231b);
        overlay.setBackgroundTintList(ColorStateList.valueOf(GREEN));
        LinearLayout.LayoutParams overlayLp = new LinearLayout.LayoutParams(-1, dp(52));
        overlayLp.topMargin = dp(20);
        layout.addView(overlay, overlayLp);
        overlay.setOnClickListener(v -> {
            if (!Settings.canDrawOverlays(this)) {
                Toast.makeText(this, "Cấp quyền hiển thị trên ứng dụng khác rồi quay lại", Toast.LENGTH_LONG).show();
                Intent settings = new Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION,
                        Uri.parse("package:" + getPackageName()));
                startActivity(settings);
                return;
            }
            Intent service = new Intent(this, EspOverlayService.class);
            if (EspOverlayService.isRunning()) stopService(service);
            else startService(service);
        });
        TextView overlayNote = text("Kiểm tra lớp phủ trên game thật; chưa đọc vị trí tướng, không hiển thị kẻ địch ẩn.", 11, MUTED);
        overlayNote.setGravity(Gravity.CENTER);
        layout.addView(overlayNote);

        Button exit = new Button(this);
        exit.setAllCaps(false);
        exit.setText("Trở về đăng nhập");
        exit.setTextSize(13);
        exit.setTextColor(0xffdbfff0);
        exit.setBackgroundTintList(ColorStateList.valueOf(0xff174b3f));
        LinearLayout.LayoutParams backLp = new LinearLayout.LayoutParams(-1,dp(46));
        backLp.topMargin=dp(24);
        layout.addView(exit,backLp);
        exit.setOnClickListener(v -> {
            consoleOpen=false;
            if (consoleRunnable != null) handler.removeCallbacks(consoleRunnable);
            if (rainView != null) rainView.stop();
            rainView=null;
            showAccountScreen();
        });
        setContentView(screen);
        String[] messages = new String[]{
                "$ minhquan --init --visual",
                "[00] AUTH TOKEN ... VALID (LOCAL)",
                "[01] RENDER ENGINE ... READY",
                "[02] MATRIX STREAM ... ONLINE (DEMO)",
                "[03] PORT 443/TCP ... OPEN (SIMULATED)",
                "[04] PORT 8080/TCP ... OPEN (SIMULATED)",
                "[05] PORT 9001/TCP ... OPEN (SIMULATED)",
                "[06] UI CHANNEL ... SYNCHRONIZED",
                "[07] SESSION ... GRANTED (LOCAL DEMO)",
                ">> MINHQUAN VISUAL CONSOLE READY  _"
        };
        StringBuilder buffer = new StringBuilder();
        final int[] step = {0};
        consoleRunnable = new Runnable() {
            @Override public void run() {
                if (isDestroyedNow || !consoleOpen || step[0] >= messages.length) return;
                buffer.append(messages[step[0]++]).append("\n");
                log.setText(buffer.toString());
                if (step[0] < messages.length) {
                    handler.postDelayed(this, 430);
                } else {
                    state.setText("● MÔ PHỎNG HOÀN TẤT • HỆ THỐNG SẴN SÀNG");
                    state.setTextColor(GREEN);
                }
            }
        };
        handler.postDelayed(consoleRunnable, 200);
    }

    /** Small central key dialog. Counter starts at -1s then -2s, -3s, ... */
    private void showKeyDialog() {
        if (isFinishing() || isDestroyedNow || keyAccepted) return;
        if (keyDialog != null && keyDialog.isShowing()) return;

        final Dialog dialog = new Dialog(this);
        keyDialog = dialog;
        dialog.requestWindowFeature(Window.FEATURE_NO_TITLE);
        dialog.setCancelable(false);

        LinearLayout panel = new LinearLayout(this);
        panel.setOrientation(LinearLayout.VERTICAL);
        panel.setBackground(shape(DIALOG_BG, 11));
        panel.setClipToOutline(true);

        TextView title = text("MinhQuan'z", 17, WHITE);
        title.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        title.setGravity(Gravity.CENTER);
        LinearLayout.LayoutParams titleLp = new LinearLayout.LayoutParams(-1, dp(27));
        titleLp.topMargin = dp(14);
        panel.addView(title, titleLp);

        TextView help = text("Bấm Vào Nút Get Key Để Lấy Key Free", 11.2f, WHITE);
        help.setGravity(Gravity.CENTER);
        LinearLayout.LayoutParams helpLp = new LinearLayout.LayoutParams(-1, dp(20));
        helpLp.leftMargin = dp(8);
        helpLp.rightMargin = dp(8);
        panel.addView(help, helpLp);

        TextView counter = text("-1s", 12, WHITE);
        counter.setGravity(Gravity.CENTER);
        LinearLayout.LayoutParams countLp = new LinearLayout.LayoutParams(-1, dp(19));
        panel.addView(counter, countLp);

        EditText key = new EditText(this);
        key.setSingleLine(true);
        key.setTextSize(12.3f);
        key.setHint("Nhập key MinhQuan");
        key.setTextColor(WHITE);
        key.setHintTextColor(0xff9c9da8);
        key.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_FLAG_NO_SUGGESTIONS);
        key.setPadding(dp(12), 0, dp(12), 0);
        key.setBackground(shape(0xff1d1e26, 7));
        LinearLayout.LayoutParams keyLp = new LinearLayout.LayoutParams(-1, dp(38));
        keyLp.topMargin = dp(16);
        keyLp.leftMargin = dp(14);
        keyLp.rightMargin = dp(14);
        keyLp.bottomMargin = dp(16);
        panel.addView(key, keyLp);

        TextView line = new TextView(this);
        line.setBackgroundColor(0xff615853);
        panel.addView(line, new LinearLayout.LayoutParams(-1, dp(1)));

        LinearLayout buttons = new LinearLayout(this);
        buttons.setOrientation(LinearLayout.HORIZONTAL);
        buttons.setGravity(Gravity.CENTER);
        panel.addView(buttons, new LinearLayout.LayoutParams(-1, dp(45)));

        TextView getKey = text("Get Key", 13.5f, 0xffef4b4b);
        getKey.setGravity(Gravity.CENTER);
        getKey.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        buttons.addView(getKey, new LinearLayout.LayoutParams(0, -1, 1));
        getKey.setOnClickListener(v -> {
            key.setText(DEMO_KEY);
            key.setSelection(key.getText().length());
        });

        TextView divider = new TextView(this);
        divider.setBackgroundColor(0xff615853);
        buttons.addView(divider, new LinearLayout.LayoutParams(dp(1), -1));

        TextView confirm = text("OK", 13.5f, 0xff81bcf7);
        confirm.setGravity(Gravity.CENTER);
        confirm.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        buttons.addView(confirm, new LinearLayout.LayoutParams(0, -1, 1));
        confirm.setOnClickListener(v -> {
            if (!DEMO_KEY.equals(key.getText().toString().trim())) {
                key.setError("Key chưa đúng");
                Toast.makeText(this, "Key không hợp lệ", Toast.LENGTH_SHORT).show();
                return;
            }
            keyAccepted = true;
            stopKeyCounter();
            dialog.dismiss();
            sendLoginNotification();
        });

        dialog.setContentView(panel);
        Window w = dialog.getWindow();
        if (w != null) {
            w.setBackgroundDrawableResource(android.R.color.transparent);
            w.addFlags(WindowManager.LayoutParams.FLAG_DIM_BEHIND);
            WindowManager.LayoutParams p = w.getAttributes();
            p.dimAmount = 0.58f;
            p.width = dp(274);
            p.height = WindowManager.LayoutParams.WRAP_CONTENT;
            p.gravity = Gravity.CENTER;
            w.setAttributes(p);
            w.setSoftInputMode(WindowManager.LayoutParams.SOFT_INPUT_STATE_ALWAYS_HIDDEN);
        }
        dialog.setOnDismissListener(d -> stopKeyCounter());
        dialog.show();
        // Dialog parameters must also be set after show() on some Android versions.
        if (dialog.getWindow() != null) dialog.getWindow().setLayout(dp(274), -2);

        counterStarted = SystemClock.elapsedRealtime();
        timerRunnable = new Runnable() {
            @Override public void run() {
                if (isDestroyedNow || !dialog.isShowing()) return;
                long seconds = 1 + (SystemClock.elapsedRealtime() - counterStarted) / 1000L;
                counter.setText("-" + seconds + "s");
                handler.postDelayed(this, 200);
            }
        };
        handler.post(timerRunnable);
    }

    private void stopKeyCounter() {
        if (timerRunnable != null) handler.removeCallbacks(timerRunnable);
        timerRunnable = null;
    }

    private void createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            NotificationManager manager = (NotificationManager) getSystemService(NOTIFICATION_SERVICE);
            NotificationChannel c = new NotificationChannel(CHANNEL_ID, "MinhQuan • Đăng nhập", NotificationManager.IMPORTANCE_DEFAULT);
            c.setDescription("Xác nhận đăng nhập key trong ứng dụng MinhQuan");
            manager.createNotificationChannel(c);
        }
    }

    private void sendLoginNotification() {
        if (Build.VERSION.SDK_INT >= 33 &&
                checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) {
            notifyAfterPermission = true;
            requestPermissions(new String[]{Manifest.permission.POST_NOTIFICATIONS}, REQUEST_NOTIFICATIONS);
            return;
        }
        postLoginNotification();
    }

    private void postLoginNotification() {
        if (Build.VERSION.SDK_INT >= 33 &&
                checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) return;
        NotificationManager manager = (NotificationManager) getSystemService(NOTIFICATION_SERVICE);
        Intent open = new Intent(this, MainActivity.class);
        open.addFlags(Intent.FLAG_ACTIVITY_SINGLE_TOP | Intent.FLAG_ACTIVITY_CLEAR_TOP);
        PendingIntent pending = PendingIntent.getActivity(this, 0, open,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
        Bitmap logo = BitmapFactory.decodeResource(getResources(), R.drawable.minhquan_avatar);
        RemoteViews compact = new RemoteViews(getPackageName(), R.layout.notification_login);
        compact.setImageViewResource(R.id.notification_avatar, R.drawable.minhquan_avatar);
        compact.setTextViewText(R.id.notification_title, "MinhQuan");
        compact.setTextViewText(R.id.notification_message, "ĐĂNG NHẬP APP THÀNH CÔNG✅");
        Notification notification = new Notification.Builder(this, CHANNEL_ID)
                .setSmallIcon(R.drawable.ic_notification)
                .setLargeIcon(logo)
                .setContentTitle("MinhQuan")
                .setContentText("ĐĂNG NHẬP APP THÀNH CÔNG✅")
                .setStyle(new Notification.DecoratedCustomViewStyle())
                .setCustomContentView(compact)
                .setCustomBigContentView(compact)
                .setColor(GREEN)
                .setAutoCancel(true)
                .setContentIntent(pending)
                .build();
        manager.notify(1006, notification);
    }

    @Override
    public void onRequestPermissionsResult(int requestCode, String[] permissions, int[] results) {
        super.onRequestPermissionsResult(requestCode, permissions, results);
        if (requestCode == REQUEST_NOTIFICATIONS && notifyAfterPermission) {
            notifyAfterPermission = false;
            if (results.length > 0 && results[0] == PackageManager.PERMISSION_GRANTED) {
                postLoginNotification();
            } else {
                Toast.makeText(this, "Cần cấp quyền thông báo để hiển thị xác nhận.", Toast.LENGTH_LONG).show();
            }
        }
    }

    @Override
    protected void onSaveInstanceState(Bundle state) {
        state.putBoolean("keyAccepted", keyAccepted);
        state.putBoolean("consoleOpen", consoleOpen);
        super.onSaveInstanceState(state);
    }

    @Override
    protected void onDestroy() {
        isDestroyedNow = true;
        if (introRunnable != null) handler.removeCallbacks(introRunnable);
        stopAvatarSpin();
        stopKeyCounter();
        if (consoleRunnable != null) handler.removeCallbacks(consoleRunnable);
        if (rainView != null) rainView.stop();
        if (keyDialog != null) {
            keyDialog.setOnDismissListener(null);
            if (keyDialog.isShowing()) keyDialog.dismiss();
        }
        super.onDestroy();
    }
}
