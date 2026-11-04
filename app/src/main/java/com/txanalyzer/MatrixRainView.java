package com.txanalyzer;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.view.View;
import java.util.Random;

/** Decorative falling glyphs. It does not access the network or device information. */
public class MatrixRainView extends View {
    private final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Random random = new Random(21);
    private float[] heads = new float[0];
    private float[] speeds = new float[0];
    private int columns = 0;
    private float cell;
    private boolean running = true;
    private static final char[] GLYPHS = "0123456789ABCDEF<>/{}+-".toCharArray();

    public MatrixRainView(Context context) { super(context); }

    @Override protected void onSizeChanged(int width, int height, int oldWidth, int oldHeight) {
        super.onSizeChanged(width, height, oldWidth, oldHeight);
        cell = getResources().getDisplayMetrics().density * 17f;
        columns = Math.max(1, (int)Math.ceil(width / cell));
        heads = new float[columns];
        speeds = new float[columns];
        for (int i=0; i<columns; i++) {
            heads[i] = -(random.nextInt(Math.max(1, height / (int)cell + 5))) * cell;
            speeds[i] = cell * (0.16f + random.nextFloat() * 0.24f);
        }
    }

    @Override protected void onDraw(Canvas canvas) {
        super.onDraw(canvas);
        canvas.drawColor(0xff030b0c);
        paint.setTypeface(android.graphics.Typeface.MONOSPACE);
        paint.setTextSize(cell * .78f);
        for (int i=0; i<columns; i++) {
            for (int j=0; j<10; j++) {
                float y = heads[i] - j*cell;
                if (y < 0 || y > getHeight()+cell) continue;
                paint.setColor(j==0 ? Color.argb(125,152,255,196) : Color.argb(Math.max(12,73-j*6), 42,222,132));
                paint.setShadowLayer(j==0 ? 5f:0f,0,0,0xff00dd80);
                canvas.drawText(String.valueOf(GLYPHS[random.nextInt(GLYPHS.length)]), i*cell+3, y, paint);
            }
            heads[i] += speeds[i];
            if (heads[i] - 9*cell > getHeight()) heads[i] = -cell * random.nextInt(12);
        }
        paint.clearShadowLayer();
        if (running) postInvalidateDelayed(78);
    }
    public void stop() { running=false; }
    @Override protected void onDetachedFromWindow() { running=false; super.onDetachedFromWindow(); }
}
