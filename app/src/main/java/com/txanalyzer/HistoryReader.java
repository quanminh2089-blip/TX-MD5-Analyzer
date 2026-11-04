package com.txanalyzer;

import android.graphics.Bitmap;
import android.graphics.Color;
import android.graphics.Rect;
import com.google.mlkit.vision.text.Text;
import java.text.Normalizer;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/** Reads the *visible* history-board cells in the supplied game screenshot.
 * The position model is calibrated for the landscape history panel shown by the user.
 * Numbers are deliberately marked unknown unless OCR passes range and side checks. */
public final class HistoryReader {
    public static final class Entry {
        public final int col, row;
        public final boolean tai;
        public int value = -1;
        Entry(int c, int r, boolean t) { col=c; row=r; tai=t; }
        public String display() { return (tai ? "T" : "X") + (value < 0 ? "?" : value); }
    }
    public static final class Result {
        public final List<Entry> entries = new ArrayList<>();
        public int totalTai = -1, totalXiu = -1;
        public float gridLeft, gridTop, cellWidth, cellHeight;
        public int topRowCount = 0;
        public boolean gridDetected() { return topRowCount >= 12 && entries.size() >= 20; }
        public String signature() {
            StringBuilder b = new StringBuilder();
            b.append(totalTai).append('/').append(totalXiu).append(':');
            for (Entry e:entries) b.append(e.tai?'T':'X').append(e.col).append('.').append(e.row).append(';');
            return b.toString();
        }
        public String summary() {
            if (totalTai >= 0 && totalXiu >= 0) {
                int total = totalTai+totalXiu;
                String pct = total>0 ? String.format(Locale.US,"%.0f%%",100.0*totalTai/total) : "--";
                return "Tài " + totalTai + "  •  Xỉu " + totalXiu + "  •  Tài " + pct;
            }
            return "Chưa đọc chắc tổng Tài/Xỉu";
        }
        public String historyLine() {
            if(entries.isEmpty()) return "Không thấy ô lịch sử";
            StringBuilder s=new StringBuilder();
            int from=Math.max(0,entries.size()-22);
            for(int i=from;i<entries.size();i++) {
                if(i>from) s.append(' ');
                s.append(entries.get(i).display());
            }
            return s.toString();
        }
    }
    private static final Pattern TOTALS=Pattern.compile("\\b(TAI|XIU)\\s*[:：]?\\s*(\\d{1,3})\\b");
    private static final int COLS=20, ROWS=5;

    public static String plain(String original) {
        return Normalizer.normalize(original==null?"":original, Normalizer.Form.NFD)
                .replaceAll("\\p{M}+", "").toUpperCase(Locale.ROOT);
    }
    public static boolean isHistory(String text) {
        String p=plain(text).replaceAll("\\s+", " ");
        if ((p.contains("LICH") && p.contains("PHIEN")) ||
                (p.contains("SU PHIEN") && p.contains("TAI"))) return true;
        // Some game fonts defeat OCR on the heading, but its two small summary counters survive.
        Matcher m=TOTALS.matcher(p);
        boolean tai=false,xiu=false;
        while(m.find()) {
            int n=Integer.parseInt(m.group(2));
            if(n>200)continue; // reject large betting amounts
            if(m.group(1).equals("TAI"))tai=true;
            else xiu=true;
        }
        return tai&&xiu;
    }
    public static int orientationScore(String text) {
        String p=plain(text);
        int score=Math.min(p.length(),160)/12;
        if(p.contains("LICH")) score+=20;
        if(p.contains("PHIEN")) score+=25;
        if(p.contains("TAI")) score+=12;
        if(p.contains("XIU")) score+=12;
        if(p.contains("MD5")) score+=6;
        if(p.contains("CUOC")) score+=5;
        return score;
    }
    public Result analyze(Bitmap image,String recognizedText) {
        Result totals = new Result();
        String t=plain(recognizedText).replace('\n',' ');
        Matcher m=TOTALS.matcher(t);
        while(m.find()) {
            int number;
            try { number=Integer.parseInt(m.group(2)); } catch(Exception e) {continue;}
            if(m.group(1).equals("TAI")) totals.totalTai=number;
            else totals.totalXiu=number;
        }
        // Layout is normalized to the landscape game view, not the physical phone orientation.
        // Search a small neighborhood to tolerate device cutouts, viewport margins and scaling.
        final float w=image.getWidth(), h=image.getHeight();
        Result best = null;
        int bestScore=-1;
        float[] offsetsX={0f,-.012f,.012f,-.025f,.025f};
        float[] offsetsY={0f,-.012f,.012f,-.025f,.025f};
        float[] scales={1f,.965f,1.035f};
        for(float sc:scales) for(float ox:offsetsX) for(float oy:offsetsY) {
            float width=w*.468f*sc, height=h*.204f*sc;
            float left=w*(.2875f+ox)+(w*.468f-width)*.5f;
            float top=h*(.547f+oy)+(h*.204f-height)*.5f;
            Result r = measure(image,left,top,width/COLS,height/ROWS);
            int score=r.topRowCount*4+r.entries.size();
            if(score>bestScore) {bestScore=score; best=r;}
            if(r.topRowCount>=18 && r.entries.size()>=32) break;
        }
        if(best!=null && best.gridDetected()) {
            best.totalTai=totals.totalTai;
            best.totalXiu=totals.totalXiu;
            return best;
        }
        return totals; // do not hallucinate grid data when calibration is uncertain
    }
    private static Result measure(Bitmap b,float left,float top,float dx,float dy) {
        Result result=new Result();
        result.gridLeft=left;
        result.gridTop=top;
        result.cellWidth=dx;
        result.cellHeight=dy;
        for(int col=0;col<COLS;col++) for(int row=0;row<ROWS;row++) {
            float cx=left+(col+.5f)*dx,cy=top+(row+.5f)*dy;
            if(cx<10||cy<10||cx>=b.getWidth()-10||cy>=b.getHeight()-10) continue;
            boolean[] state=readChip(b,cx,cy,Math.min(dx,dy));
            if(!state[0])continue;
            result.entries.add(new Entry(col,row,state[1]));
            if(row==0)result.topRowCount++;
        }
        return result;
    }
    /** ring samples discriminate white disks, gold-rimmed black disks, and empty grid cells */
    private static boolean[] readChip(Bitmap b,float x,float y,float size) {
        int white=0,gold=0;
        for(int k=0;k<20;k++) {
            double a=2*Math.PI*k/20;
            for(float rr:new float[]{.21f,.29f}) {
                int px=Math.round(x+(float)Math.cos(a)*size*rr);
                int py=Math.round(y+(float)Math.sin(a)*size*rr);
                if(px<0||py<0||px>=b.getWidth()||py>=b.getHeight())continue;
                int c=b.getPixel(px,py),red=Color.red(c),green=Color.green(c),blue=Color.blue(c);
                if(red>=140 && green>=140 && blue>=125 && Math.max(red,Math.max(green,blue))-Math.min(red,Math.min(green,blue))<80)white++;
                if(red>100 && green>61 && blue<125 && red>green*1.07f && red>blue*1.42f)gold++;
            }
        }
        if(white>=11 && white>gold*1.4f)return new boolean[]{true,false}; // Xỉu
        if(gold>=7 && gold>white*.65f)return new boolean[]{true,true}; // Tài
        return new boolean[]{false,false};
    }
    /** Associates OCR numbers found in an upscaled grid crop with verified colored circles. */
    public static void setNumbers(Result r,Text recognized) {
        if(!r.gridDetected())return;
        for(Text.TextBlock block:recognized.getTextBlocks())for(Text.Line line:block.getLines())for(Text.Element el:line.getElements()) {
            String value=el.getText().trim().replace('O','0').replace('o','0').replace('I','1').replace('l','1');
            if(!value.matches("\\d{1,2}"))continue;
            int n;
            try {n=Integer.parseInt(value);}catch(Exception ignored){continue;}
            if(n<3||n>18)continue;
            Rect bounds=el.getBoundingBox();
            if(bounds==null)continue;
            float x=(bounds.exactCenterX()/3f)/r.cellWidth;
            float y=(bounds.exactCenterY()/3f)/r.cellHeight;
            int col=(int)Math.floor(x),row=(int)Math.floor(y);
            if(col<0||col>=COLS||row<0||row>=ROWS)continue;
            float fx=x-col-.5f, fy=y-row-.5f;
            if(Math.abs(fx)>.42f||Math.abs(fy)>.42f)continue;
            for(Entry e:r.entries)if(e.col==col&&e.row==row && ((n>=11)==e.tai)) {e.value=n;break;}
        }
    }
}
