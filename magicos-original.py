# ============================================================
# MAGICQN — mo phong dien thoai chay he dieu hanh MAZIUS.
# Day la san pham/thuong hieu doc lap, khong lien quan hay
# duoc cap phep boi Apple Inc. Moi tham chieu "iPhone"/"iOS"
# con sot lai trong code chi la ten bien/class noi bo, khong
# hien thi cho nguoi dung.
# ============================================================
import http.server
import socketserver
import threading
import webbrowser
import os
import glob
import json
import mimetypes
import socket
import secrets
import time

# Shared maintenance state survives application restarts.
SERVER_STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "magicos_server_state.json")
try:
    with open(SERVER_STATE_FILE, encoding="utf-8") as state_file:
        SERVER_OPEN = json.load(state_file).get("open", True) is True
except FileNotFoundError:
    SERVER_OPEN = True
except (OSError, ValueError, AttributeError):
    SERVER_OPEN = False
ADMIN_SESSIONS = {}

PORT = 8888
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WALLPAPER_URL_PATH = "/wallpaper-img"

def find_wallpaper():
    exts = (".jpg", ".jpeg", ".png", ".webp")
    found = []
    for ext in exts:
        found += glob.glob(os.path.join(SCRIPT_DIR, "*" + ext))
        found += glob.glob(os.path.join(SCRIPT_DIR, "*" + ext.upper()))
    return sorted(found)[0] if found else None

WALLPAPER_PATH = find_wallpaper()
WALLPAPER_CSS = (
    f"<style>#phone-container, #home-screen {{ background-image: url('{WALLPAPER_URL_PATH}'); }}</style>"
    if WALLPAPER_PATH else ""
)


# ============================================================
# APP "PENALTY" — nhung nguyen ma nguon Flask tu app.py, chay
# o mot cong rieng va duoc nhung vao man hinh MAGICQN qua iframe.
# ============================================================
PENALTY_APP_ID = "app-penalty"
PENALTY_PORT_START = 5091

PENALTY_APP_SOURCE = '# -*- coding: utf-8 -*-\nimport os\nimport json\nimport subprocess\nfrom werkzeug.security import generate_password_hash, check_password_hash\nfrom flask import Flask, render_template_string, send_file, request, jsonify, session\n\napp = Flask(__name__)\napp.secret_key = os.environ.get("SECRET_KEY", "goalkeeper-dev-secret-change-me")\n\n# ==========================================\n# 0. LƯU TRỮ TÀI KHOẢN NGƯỜI DÙNG (file JSON đơn giản)\n# ==========================================\nUSERS_FILE = "users.json"\n\ndef load_users():\n    if os.path.exists(USERS_FILE):\n        try:\n            with open(USERS_FILE, "r", encoding="utf-8") as f:\n                return json.load(f)\n        except Exception:\n            return {}\n    return {}\n\ndef save_users(users):\n    with open(USERS_FILE, "w", encoding="utf-8") as f:\n        json.dump(users, f, ensure_ascii=False, indent=2)\n\n# ==========================================\n# 1. HÀM TÁCH ÂM THANH TỪ VIDEO (MP4 -> MP3)\n# ==========================================\ndef extract_audio_from_video():\n    video_file = "nhacnen.mp4"\n    audio_file = "nhacnen.mp3"\n    \n    if os.path.exists(video_file) and not os.path.exists(audio_file):\n        print(f"🔄 Đang trích xuất âm thanh từ {video_file} sang {audio_file}...")\n        try:\n            # Lệnh ffmpeg tách audio, giữ chất lượng tốt, tắt video stream (-vn)\n            subprocess.run([\n                "ffmpeg", "-i", video_file, "-vn", \n                "-acodec", "libmp3lame", "-q:a", "2", \n                audio_file, "-y"\n            ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)\n            print("✅ Trích xuất âm thanh thành công!")\n        except FileNotFoundError:\n            print("❌ LỖI: Không tìm thấy \'ffmpeg\'. Vui lòng cài đặt FFmpeg hoặc tự chuyển đổi thủ công.")\n        except subprocess.CalledProcessError:\n            print("❌ LỖI: FFmpeg chạy thất bại. Kiểm tra lại file nhacnen.mp4")\n    elif os.path.exists(audio_file):\n        print("✅ File nhạc nền nhacnen.mp3 đã tồn tại, bỏ qua bước trích xuất.")\n    else:\n        print("⚠️ Không tìm thấy file nhacnen.mp4. Game sẽ chạy không có nhạc nền.")\n\n# ==========================================\n# 2. NỘI DUNG HTML/JS/CSS CỦA GAME\n# (Đã được thêm thẻ <audio> và script tự động phát nhạc)\n# ==========================================\nHTML_CONTENT = """\n<!DOCTYPE html>\n<html lang="vi" translate="no">\n<head>\n<meta charset="UTF-8">\n<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no, viewport-fit=cover">\n<meta name="google" content="notranslate">\n<meta name="format-detection" content="telephone=no, email=no, address=no">\n<title>Goalkeeper Ready</title>\n<style>\n  *{margin:0;padding:0;box-sizing:border-box;-webkit-tap-highlight-color:transparent;user-select:none}\n  html,body{width:100%;height:100%;overflow:hidden;background:#050608;font-family:\'Segoe UI\',Roboto,Arial,sans-serif}\n  #loading-screen{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;background:radial-gradient(circle at 50% 35%,#123a20 0%,#08140c 55%,#020402 100%);background-size:180% 180%;animation:bgDrift 9s ease-in-out infinite;z-index:50;overflow:hidden;transition:opacity .6s cubic-bezier(.4,0,.2,1)}\n  #loading-screen.hide{opacity:0;pointer-events:none;transform:scale(1.03)}\n  @keyframes bgDrift{0%,100%{background-position:50% 40%}50%{background-position:52% 60%}}\n  #loading-screen::before{content:"";position:absolute;inset:-20%;background:conic-gradient(from 0deg at 50% 30%,transparent 0deg,rgba(255,255,255,.05) 8deg,transparent 20deg,transparent 360deg);animation:sweep 6s linear infinite;pointer-events:none}\n  @keyframes sweep{to{transform:rotate(360deg)}}\n  .particles{position:absolute;inset:0;pointer-events:none;overflow:hidden}\n  .particle{position:absolute;bottom:-10px;border-radius:50%;background:rgba(143,242,156,.55);box-shadow:0 0 6px rgba(143,242,156,.6);animation-name:floatUp;animation-timing-function:ease-in;animation-iteration-count:infinite}\n  @keyframes floatUp{0%{transform:translateY(0);opacity:0}10%{opacity:.9}90%{opacity:.4}100%{transform:translateY(-115vh) translateX(var(--drift,12px));opacity:0}}\n  .logo-wrap{position:relative;display:flex;flex-direction:column;align-items:center;margin-bottom:46px;z-index:2}\n  .ball-halo{position:absolute;top:50%;left:50%;width:110px;height:110px;transform:translate(-50%,-52%);border-radius:50%;background:radial-gradient(circle,rgba(61,220,107,.35) 0%,rgba(61,220,107,0) 70%);animation:haloPulse 1.4s ease-in-out infinite;z-index:0}\n  @keyframes haloPulse{0%,100%{transform:translate(-50%,-52%) scale(.85);opacity:.6}50%{transform:translate(-50%,-52%) scale(1.15);opacity:1}}\n  .ball{position:relative;z-index:1;width:64px;height:64px;border-radius:50%;background:radial-gradient(circle at 32% 28%,#fff 0 18%,transparent 19%),radial-gradient(circle at 68% 28%,#fff 0 18%,transparent 19%),radial-gradient(circle at 50% 62%,#fff 0 20%,transparent 21%),#1a1a1a;box-shadow:0 0 26px rgba(143,242,156,.35),inset -6px -6px 10px rgba(0,0,0,.5),inset 4px 4px 8px rgba(255,255,255,.25);background-color:#e9e9e9;animation:spin 1.4s linear infinite,bounce 1.1s ease-in-out infinite}\n  .ball::before{content:"";position:absolute;inset:0;border-radius:50%;background:radial-gradient(circle at 50% 20%,transparent 30%,rgba(0,0,0,.55) 31%,transparent 33%),radial-gradient(circle at 22% 55%,transparent 30%,rgba(0,0,0,.55) 31%,transparent 33%),radial-gradient(circle at 78% 55%,transparent 30%,rgba(0,0,0,.55) 31%,transparent 33%)}\n  @keyframes spin{to{transform:rotate(360deg)}}\n  @keyframes bounce{0%,100%{transform:translateY(0)}50%{transform:translateY(-14px)}}\n  .ball-shadow{width:46px;height:9px;margin-top:8px;border-radius:50%;background:radial-gradient(ellipse,rgba(0,0,0,.55) 0%,transparent 72%);animation:shadowPulse 1.1s ease-in-out infinite;z-index:1}\n  @keyframes shadowPulse{0%,100%{transform:scale(1);opacity:.55}50%{transform:scale(.6);opacity:.25}}\n  .game-title{margin-top:22px;color:#f5f5f5;font-size:24px;font-weight:800;letter-spacing:4px;text-transform:uppercase;z-index:2;text-shadow:0 0 12px rgba(143,242,156,.35);animation:titleGlow 2.2s ease-in-out infinite}\n  @keyframes titleGlow{0%,100%{text-shadow:0 0 10px rgba(143,242,156,.25)}50%{text-shadow:0 0 22px rgba(143,242,156,.6)}}\n  .bar-track{position:relative;width:230px;height:9px;margin-top:36px;border-radius:6px;background:rgba(255,255,255,.08);overflow:hidden;box-shadow:inset 0 1px 3px rgba(0,0,0,.6);z-index:2}\n  .bar-fill{position:relative;height:100%;width:0%;border-radius:6px;background:linear-gradient(90deg,#2fb85a,#8ef29c,#3ddc6b);background-size:220% 100%;animation:barGradient 1.4s linear infinite;transition:width .18s cubic-bezier(.3,.6,.3,1);box-shadow:0 0 10px rgba(143,242,156,.55)}\n  @keyframes barGradient{0%{background-position:0% 0}100%{background-position:-220% 0}}\n  .bar-fill::after{content:"";position:absolute;inset:0;background:linear-gradient(110deg,transparent 30%,rgba(255,255,255,.55) 48%,transparent 66%);background-size:200% 100%;animation:shimmer 1.1s linear infinite}\n  @keyframes shimmer{0%{background-position:150% 0}100%{background-position:-50% 0}}\n  .pct{margin-top:12px;color:#bdbdbd;font-size:12px;letter-spacing:1px;z-index:2}\n  .pct.ready{color:#8ef29c;font-weight:700;letter-spacing:2px}\n  #game-screen{position:absolute;inset:0;display:none;background:#000;opacity:0;transform:scale(1.04);transition:opacity .6s cubic-bezier(.2,.8,.2,1),transform .6s cubic-bezier(.2,.8,.2,1)}\n  #game-screen.show{opacity:1;transform:scale(1)}\n  #gameCanvas{display:block;width:100%;height:100%}\n  #rotate-warning{display:none;position:absolute;inset:0;z-index:100;background:#050608;flex-direction:column;align-items:center;justify-content:center;color:#eaeaea;text-align:center;padding:24px}\n  .rotate-icon{font-size:44px;margin-bottom:14px;animation:rotateHint 1.6s ease-in-out infinite}\n  @keyframes rotateHint{0%,100%{transform:rotate(0)}50%{transform:rotate(90deg)}}\n  @media(orientation:landscape){ #rotate-warning.active{display:flex}}\n  #shot-controls{position:absolute;left:50%;bottom:calc(env(safe-area-inset-bottom,0px) + 30px + 18vh);transform:translateX(-50%);display:flex;align-items:flex-end;justify-content:center;gap:-6px;z-index:20;padding:0;background:none;border:none;box-shadow:none;opacity:0;pointer-events:none;transition:opacity .25s ease}\n  #shot-controls.reveal,#shot-controls.exiting{opacity:1}\n  .shot-btn{-webkit-tap-highlight-color:transparent;touch-action:manipulation;position:relative;width:78px;height:132px;margin:0 -10px;border:none;background:transparent;padding:0;display:flex;align-items:flex-end;justify-content:center;cursor:pointer;opacity:0;pointer-events:none;transform:translateY(14px) scale(.4);transition:filter .3s ease}\n  .shot-btn svg{width:100%;height:100%;display:block;position:relative;z-index:1;filter:drop-shadow(0 8px 12px rgba(0,0,0,.5));transition:transform .16s cubic-bezier(.34,1.56,.64,1),filter .3s ease}\n  #shot-controls.reveal .shot-btn{pointer-events:auto;animation:btnPop .55s cubic-bezier(.34,1.56,.64,1) forwards}\n  #shot-controls.reveal .shot-btn:nth-child(1){animation-delay:.06s}\n  #shot-controls.reveal .shot-btn:nth-child(2){animation-delay:.16s}\n  #shot-controls.reveal .shot-btn:nth-child(3){animation-delay:.26s}\n  @keyframes btnPop{0%{opacity:0;transform:translateY(20px) scale(.4)}60%{opacity:1;transform:translateY(-6px) scale(1.08)}100%{opacity:1;transform:translateY(0) scale(1)}}\n  #shot-controls.exiting .shot-btn{pointer-events:none;animation:btnHide .3s cubic-bezier(.4,0,.6,1) forwards}\n  #shot-controls.exiting .shot-btn:nth-child(1){animation-delay:.06s}\n  #shot-controls.exiting .shot-btn:nth-child(2){animation-delay:0s}\n  #shot-controls.exiting .shot-btn:nth-child(3){animation-delay:.06s}\n  @keyframes btnHide{to{opacity:0;transform:translateY(14px) scale(.5)}}\n  .shot-btn.pressed svg{transform:translateY(6px) scale(.92)}\n  .shot-btn.center{width:82px;height:140px}\n  .shot-btn:active:not(.disabled) svg,.shot-btn.pressed svg{filter:brightness(1.2) drop-shadow(0 4px 8px rgba(0,0,0,.55))}\n  .shot-btn.disabled{pointer-events:none}\n  .shot-btn.disabled svg{filter:grayscale(1) brightness(.55) drop-shadow(0 4px 6px rgba(0,0,0,.35))}\n  .shot-btn.reenable svg{animation:arrowPulse .5s ease-out}\n  @keyframes arrowPulse{0%{filter:brightness(1.5) drop-shadow(0 0 14px rgba(255,205,60,.9))}100%{filter:brightness(1) drop-shadow(0 8px 12px rgba(0,0,0,.5))}}\n  .spark{position:absolute;z-index:22;border-radius:50%;pointer-events:none;will-change:transform,opacity}\n  #cashout-bar{position:absolute;left:50%;bottom:calc(env(safe-area-inset-bottom,0px) + 26px + 26px);transform:translateX(-50%);width:min(84vw,340px);z-index:19;opacity:0;pointer-events:none}\n  #cashout-bar.reveal,#cashout-bar.exiting{opacity:1}\n  #cashout-bar .co-glow{position:absolute;left:50%;top:50%;width:150%;height:260%;transform:translate(-50%,-50%) scale(.3);border-radius:50%;background:radial-gradient(circle,rgba(120,255,150,.55) 0%,rgba(120,255,150,0) 68%);opacity:0;pointer-events:none;z-index:0}\n  #cashout-bar.reveal .co-glow{animation:coGlowBurst .8s cubic-bezier(.16,.84,.32,1) forwards}\n  @keyframes coGlowBurst{0%{opacity:.75;transform:translate(-50%,-50%) scale(.3)}100%{opacity:0;transform:translate(-50%,-50%) scale(1.75)}}\n  .cashout-btn{-webkit-tap-highlight-color:transparent;touch-action:manipulation;position:relative;width:100%;height:58px;border:2px solid rgba(255,255,255,.35);border-radius:14px;background:linear-gradient(180deg,#379c58 0%,#1f6636 48%,#0c331a 100%);box-shadow:0 12px 24px rgba(0,0,0,.5),inset 0 2px 3px rgba(255,255,255,.4),inset 0 -9px 13px rgba(0,0,0,.4);display:flex;align-items:center;justify-content:center;gap:10px;cursor:pointer;overflow:visible;z-index:1;opacity:0;pointer-events:none;transform:scale(.3) translateY(30px);transform-origin:50% 100%;filter:none;transition:filter .25s ease}\n  .cashout-btn::after{content:"";position:absolute;inset:-2px;border-radius:16px;border:3px solid rgba(160,255,180,.8);opacity:0;pointer-events:none;z-index:2}\n  #cashout-bar.reveal .cashout-btn::after{animation:coRingBurst .7s cubic-bezier(.16,.84,.32,1) .06s forwards}\n  @keyframes coRingBurst{0%{opacity:.8;transform:scale(.9)}100%{opacity:0;transform:scale(1.22)}}\n  #cashout-bar.reveal .cashout-btn{pointer-events:auto;animation:coPop .68s cubic-bezier(.22,1.2,.36,1) forwards}\n  @keyframes coPop{0%{opacity:0;transform:scale(.3) translateY(30px)}45%{opacity:1;transform:scale(1.08) translateY(-6px)}68%{transform:scale(.97) translateY(1px)}86%{transform:scale(1.02) translateY(0)}100%{opacity:1;transform:scale(1) translateY(0)}}\n  #cashout-bar.exiting .cashout-btn{pointer-events:none;animation:coHide .28s cubic-bezier(.4,0,.6,1) forwards!important}\n  @keyframes coHide{to{opacity:0;transform:scale(.4) translateY(16px)}}\n  .cashout-shine{position:absolute;inset:0;border-radius:12px;overflow:hidden;z-index:0}\n  .cashout-shine::before{content:"";position:absolute;inset:-30% -60%;background:linear-gradient(100deg,transparent 30%,rgba(255,255,255,.4) 48%,transparent 66%);background-size:220% 100%;animation:coShine 2.3s linear infinite}\n  @keyframes coShine{0%{background-position:150% 0}100%{background-position:-50% 0}}\n  .cashout-label{position:relative;z-index:2;color:#fff;font-weight:900;font-size:17px;letter-spacing:2px;text-shadow:0 2px 3px rgba(0,0,0,.5);display:inline-block}\n  #cashout-bar.reveal .cashout-label{animation:coLabelPop .4s cubic-bezier(.3,1.2,.4,1) .18s backwards}\n  @keyframes coLabelPop{0%{opacity:0;transform:translateY(4px)}100%{opacity:1;transform:translateY(0)}}\n  .cashout-amount{position:relative;z-index:2;color:#eaffee;font-weight:800;font-size:13.5px;letter-spacing:.2px;padding:3px 10px;border-radius:9px;background:rgba(0,0,0,.28);box-shadow:inset 0 1px 2px rgba(0,0,0,.4);font-variant-numeric:tabular-nums;transition:color .2s ease;display:inline-block}\n  #cashout-bar.reveal .cashout-amount{animation:coLabelPop .4s cubic-bezier(.3,1.2,.4,1) .26s backwards}\n  .cashout-amount.co-rolling{animation:coAmountRoll .5s cubic-bezier(.34,1.56,.64,1)}\n  @keyframes coAmountRoll{0%{transform:scale(1)}30%{transform:scale(1.3);color:#fff}100%{transform:scale(1)}}\n  .cashout-btn.disabled{filter:grayscale(.75) brightness(.6);cursor:default}\n  .cashout-btn.disabled .cashout-shine::before{animation:none;opacity:0}\n  .cashout-btn.unlocked{animation:coUnlock .55s ease-out}\n  @keyframes coUnlock{0%{filter:brightness(1.7) drop-shadow(0 0 18px rgba(143,242,156,.95))}100%{filter:brightness(1)}}\n  .cashout-coins{position:absolute;bottom:-10px;width:36px;height:24px;pointer-events:none;z-index:3;opacity:0;transform:translateY(-18px) scale(.4) rotate(-30deg)}\n  #cashout-bar.reveal .cashout-coins-left{animation:coCoinDrop .5s cubic-bezier(.34,1.56,.64,1) .2s forwards}\n  #cashout-bar.reveal .cashout-coins-right{animation:coCoinDrop .5s cubic-bezier(.34,1.56,.64,1) .3s forwards}\n  @keyframes coCoinDrop{0%{opacity:0;transform:translateY(-18px) scale(.4) rotate(-30deg)}70%{opacity:1;transform:translateY(2px) scale(1.12) rotate(6deg)}100%{opacity:1;transform:translateY(0) scale(1) rotate(0)}}\n  .cashout-coins-left{left:-9px}\n  .cashout-coins-right{right:-9px}\n  .cashout-coins i{position:absolute;display:block;width:17px;height:17px;border-radius:50%;background:radial-gradient(circle at 34% 26%,#ffe66d,#c99a00 72%);box-shadow:0 1px 2px rgba(0,0,0,.5),inset 0 1px 1px rgba(255,255,255,.6),inset 0 -2px 2px rgba(120,80,0,.5);border:.8px solid rgba(255,255,255,.3)}\n  .cashout-coins-left i:nth-child(1){left:15px;bottom:0;z-index:3}\n  .cashout-coins-left i:nth-child(2){left:7px;bottom:2px;z-index:2}\n  .cashout-coins-left i:nth-child(3){left:0;bottom:3px;z-index:1}\n  .cashout-coins-right i:nth-child(1){right:15px;bottom:0;z-index:3}\n  .cashout-coins-right i:nth-child(2){right:7px;bottom:2px;z-index:2}\n  .cashout-coins-right i:nth-child(3){right:0;bottom:3px;z-index:1}\n  #goal-notify{position:absolute;z-index:70;left:0;top:0;transform:translate(-50%,-100%);pointer-events:none;text-align:center}\n  #goal-notify .gn-ring{display:none}\n  #goal-notify .gn-burst{display:none}\n  #goal-notify .gn-text{position:relative;z-index:2;display:inline-block;font-family:\'Arial Black\',Arial,sans-serif;font-weight:900;letter-spacing:3px;font-size:clamp(28px,8vw,46px);opacity:0;white-space:nowrap}\n  #goal-notify .gn-text::before{display:none}\n  #goal-notify.show.goal .gn-text{color:#ffb020;animation:gnFade 1s ease-out forwards}\n  #goal-notify.show.miss .gn-text{color:#c21f14;animation:gnFade 1s ease-out forwards}\n  @keyframes gnFade{0%{opacity:0}15%{opacity:1}80%{opacity:1}100%{opacity:0}}\n  .gn-spark{position:absolute;z-index:69;border-radius:50%;pointer-events:none;will-change:transform,opacity}\n  #bet-controls{position:absolute;left:50%;bottom:calc(env(safe-area-inset-bottom,0px) + 26px);transform:translateX(-50%);display:flex;align-items:center;justify-content:center;gap:14px;z-index:20}\n  .bet-tri{-webkit-tap-highlight-color:transparent;touch-action:manipulation;position:relative;width:48px;height:88px;border:none;cursor:pointer;opacity:0;pointer-events:none;display:flex;transition:filter .2s ease}\n  .bet-tri-left{clip-path:polygon(100% 4%,100% 96%,4% 50%)}\n  .bet-tri-right{clip-path:polygon(0% 4%,0% 96%,96% 50%)}\n  .bet-tri-left .bet-tri-face{position:absolute;inset:0;background:radial-gradient(circle at 75% 30%,#3a3a3a,#0a0a0a 78%);box-shadow:inset 0 1px 2px rgba(255,255,255,.18)}\n  .bet-tri-right .bet-tri-face{position:absolute;inset:0;background:radial-gradient(circle at 25% 30%,#3a3a3a,#0a0a0a 78%);box-shadow:inset 0 1px 2px rgba(255,255,255,.18)}\n  .bet-tri-inner{position:relative;z-index:1;color:#fff;font-size:22px;font-weight:900;display:flex;align-items:center;justify-content:center;width:100%;height:100%;text-shadow:0 1px 2px rgba(0,0,0,.4)}\n  .bet-tri-left .bet-tri-inner{justify-content:flex-end;padding-right:14px}\n  .bet-tri-right .bet-tri-inner{justify-content:flex-start;padding-left:14px}\n  .bet-tri:active:not(.disabled){filter:brightness(1.25)}\n  .bet-square{position:relative;width:92px;height:92px;border-radius:20px;border:1.5px solid rgba(255,255,255,.3);background:linear-gradient(145deg,#3ddc6b,#1f8f43 60%,#136a30);box-shadow:0 10px 24px rgba(0,0,0,.5),0 0 26px rgba(61,220,107,.35),inset 0 2px 3px rgba(255,255,255,.45),inset 0 -6px 10px rgba(0,0,0,.35);display:flex;flex-direction:column;align-items:center;justify-content:center;gap:4px;cursor:pointer;z-index:1;opacity:0;pointer-events:none;overflow:hidden;animation:squareBreathe 2.2s ease-in-out infinite;transition:filter .15s ease}\n  @keyframes squareBreathe{0%,100%{transform:scale(1)}50%{transform:scale(1.035)}}\n  .bet-square::before{content:"";position:absolute;inset:-30% -30%;background:conic-gradient(rgba(255,255,255,0) 0%,rgba(255,255,255,.22) 8%,rgba(255,255,255,0) 18%);animation:squareSweep 2.6s linear infinite}\n  @keyframes squareSweep{to{transform:rotate(360deg)}}\n  .bet-play-text{position:relative;z-index:1;color:#fff;font-size:18px;font-weight:900;letter-spacing:2.5px;text-shadow:0 2px 3px rgba(0,0,0,.4)}\n  .bet-amount{position:relative;z-index:1;color:#eaffee;font-size:13px;font-weight:700;letter-spacing:.5px;padding:2px 10px;border-radius:10px;background:rgba(0,0,0,.22);box-shadow:inset 0 1px 2px rgba(0,0,0,.3)}\n  .bet-square:active:not(.disabled){filter:brightness(1.1)}\n  .bet-square.bump{animation:squareBreathe 2.2s ease-in-out infinite,betBump .32s ease}\n  @keyframes betBump{0%{transform:scale(1)}35%{transform:scale(1.18)}100%{transform:scale(1)}}\n  .bet-square.shake{animation:betShake .45s ease}\n  @keyframes betShake{0%,100%{transform:translateX(0)}20%{transform:translateX(-9px) rotate(-2deg)}40%{transform:translateX(8px) rotate(2deg)}60%{transform:translateX(-6px)}80%{transform:translateX(3px)}}\n  .bet-square.disabled{filter:grayscale(.6) brightness(.6);animation:none}\n  #bet-controls.reveal .bet-tri,#bet-controls.reveal .bet-square{pointer-events:auto;animation-name:betPop;animation-duration:.55s;animation-timing-function:cubic-bezier(.34,1.56,.64,1);animation-fill-mode:forwards}\n  #bet-controls.reveal .bet-square{animation-name:betPopSquare,squareBreathe;animation-duration:.55s,2.2s;animation-timing-function:cubic-bezier(.34,1.56,.64,1),ease-in-out;animation-fill-mode:forwards,none;animation-delay:.1s,.65s;animation-iteration-count:1,infinite}\n  #bet-controls.reveal .bet-tri-left{animation-delay:0s}\n  #bet-controls.reveal .bet-tri-right{animation-delay:.16s}\n  @keyframes betPop{0%{opacity:0;transform:scale(.3)}60%{opacity:1}100%{opacity:1;transform:scale(1)}}\n  @keyframes betPopSquare{0%{opacity:0;transform:scale(.2) rotate(-25deg)}55%{opacity:1;transform:scale(1.12) rotate(4deg)}100%{opacity:1;transform:scale(1) rotate(0)}}\n  #bet-controls.exiting .bet-tri,#bet-controls.exiting .bet-square{pointer-events:none;animation:betHide .28s cubic-bezier(.4,0,.6,1) forwards!important}\n  #bet-controls.exiting .bet-square{animation-delay:.06s!important}\n  @keyframes betHide{to{opacity:0;transform:scale(.4)}}\n  #balance-display{position:absolute;left:calc(env(safe-area-inset-left,0px) + 16px);top:calc(env(safe-area-inset-top,0px) + 54px);z-index:20;display:flex;align-items:center;gap:8px;padding:7px 14px 7px 7px;border-radius:22px;background:rgba(16,19,17,.7);backdrop-filter:blur(8px);-webkit-backdrop-filter:blur(8px);border:1px solid rgba(255,255,255,.12);box-shadow:0 6px 16px rgba(0,0,0,.4);opacity:0;transform:translateY(-14px);transition:opacity .45s ease .1s,transform .5s cubic-bezier(.2,.8,.2,1) .1s}\n  body.hud-show #balance-display{opacity:1;transform:translateY(0)}\n  #balance-coin{width:23px;height:23px;border-radius:50%;flex:none;display:flex;align-items:center;justify-content:center;background:linear-gradient(155deg,#ffe066,#d9a300);color:#4a3300;font-size:12.5px;font-weight:900;font-family:Arial,sans-serif;box-shadow:0 1px 3px rgba(0,0,0,.35),inset 0 1px 1px rgba(255,255,255,.5)}\n  #balance-amount{position:relative;display:inline-block;color:#f5f5f5;font-size:16px;font-weight:800;letter-spacing:.2px;font-variant-numeric:tabular-nums;text-shadow:0 1px 2px rgba(0,0,0,.5);transition:color .3s ease}\n  #balance-amount .cents{opacity:.6;font-size:12px;font-weight:700}\n  #balance-amount.flash-gain{color:#8ef29c}\n  #balance-amount.flash-loss{color:#ff8577}\n  #balance-display.bump{animation:balanceBump .4s cubic-bezier(.3,1.4,.4,1)}\n  @keyframes balanceBump{0%{transform:scale(1)}40%{transform:scale(1.1)}100%{transform:scale(1)}}\n  #balance-display.deny{animation:balanceDeny .4s ease}\n  @keyframes balanceDeny{0%,100%{transform:scale(1)}25%{transform:scale(.96) translateX(-3px)}50%{transform:scale(.96) translateX(3px)}75%{transform:scale(.98) translateX(-2px)}}\n  .balance-float{position:absolute;left:50%;top:-2px;font-size:13px;font-weight:800;letter-spacing:.2px;pointer-events:none;white-space:nowrap;font-variant-numeric:tabular-nums;animation:balanceFloatUp .9s cubic-bezier(.2,.7,.3,1) forwards}\n  .balance-float.gain{color:#8ef29c;text-shadow:0 2px 5px rgba(0,0,0,.55),0 0 10px rgba(143,242,156,.6)}\n  .balance-float.loss{color:#ff8577;text-shadow:0 2px 5px rgba(0,0,0,.55),0 0 10px rgba(255,110,90,.5)}\n  @keyframes balanceFloatUp{0%{opacity:0;transform:translate(-50%,4px) scale(.75)}16%{opacity:1;transform:translate(-50%,-4px) scale(1.1)}32%{transform:translate(-50%,-9px) scale(1)}75%{opacity:1;transform:translate(-50%,-27px) scale(1)}100%{opacity:0;transform:translate(-50%,-42px) scale(.94)}}\n  #jackpot-ladder{position:absolute;right:env(safe-area-inset-right,0px);top:calc(env(safe-area-inset-top,0px) + 54px);width:176px;z-index:15;opacity:0;transform:translateY(-14px);transition:opacity .45s ease .15s,transform .5s cubic-bezier(.2,.8,.2,1) .15s;pointer-events:none;filter:drop-shadow(0 10px 18px rgba(0,0,0,.55))}\n  body.hud-show #jackpot-ladder{opacity:1;transform:translateY(0)}\n  #jackpot-ladder svg{width:100%;height:auto;display:block;overflow:visible}\n  #jackpot-ladder .jp-row-text{font-family:\'Arial Black\',Arial,sans-serif;font-weight:900}\n  #jackpot-ladder .jp-row-lit{transition:filter .25s ease}\n  #jackpot-ladder.levelup{animation:jpLevelUp .5s ease}\n  @keyframes jpLevelUp{0%{transform:translateY(0) scale(1)}35%{transform:translateY(0) scale(1.08)}100%{transform:translateY(0) scale(1)}}\n  #jackpot-ladder .jp-row-text.jp-rolling{transform-box:fill-box;transform-origin:center;animation:jpValueRoll .55s cubic-bezier(.34,1.56,.64,1)}\n  @keyframes jpValueRoll{0%{transform:scale(1) translateY(0);filter:brightness(1) drop-shadow(0 0 0 rgba(255,214,90,0))}30%{transform:scale(1.22) translateY(-2px);filter:brightness(2) drop-shadow(0 0 8px rgba(255,214,90,.95))}100%{transform:scale(1) translateY(0);filter:brightness(1) drop-shadow(0 0 0 rgba(255,214,90,0))}}\n  #tier-select{position:absolute;right:calc(env(safe-area-inset-right,0px) + 176px - 72px);top:calc(env(safe-area-inset-top,0px) + 165px);width:120px;display:flex;flex-direction:column;gap:10px;z-index:20;pointer-events:none}\n  #tier-hand{position:absolute;left:-28px;top:0;font-size:20px;line-height:1;pointer-events:none;z-index:6;filter:drop-shadow(0 3px 4px rgba(0,0,0,.55));transform-origin:70% 50%;opacity:0;transition:opacity .3s ease,top .38s cubic-bezier(.34,1.56,.64,1),left .38s cubic-bezier(.34,1.56,.64,1),filter .3s ease}\n  #tier-select.reveal #tier-hand{opacity:1;animation:handPoke 1.15s ease-in-out .6s infinite}\n  #tier-select.locked #tier-hand{opacity:0}\n  @keyframes handPoke{0%,100%{transform:translateX(0) rotate(0deg) scale(1)}45%{transform:translateX(6px) rotate(-10deg) scale(1.08)}62%{transform:translateX(6px) rotate(-10deg) scale(.96)}}\n  .tier-btn{-webkit-tap-highlight-color:transparent;touch-action:manipulation;position:relative;height:31px;border-radius:7px;display:flex;flex-direction:column;align-items:center;justify-content:center;line-height:1;font-size:9.5px;font-weight:900;letter-spacing:.8px;color:#fff;text-shadow:0 1px 2px rgba(0,0,0,.55);cursor:pointer;border:2.2px solid;opacity:0;pointer-events:none;transform:translateX(-22px) scale(.82);transition:filter .35s ease,transform .22s cubic-bezier(.22,.61,.36,1);box-shadow:0 5px 10px rgba(0,0,0,.5),inset 0 1px 0 rgba(255,255,255,.2);overflow:visible}\n  .tier-btn::after{content:"";position:absolute;inset:-5px;border-radius:12px;box-shadow:0 0 0 rgba(0,0,0,0);opacity:0;pointer-events:none;transition:opacity .25s ease}\n  #tier-select.reveal .tier-amateur{animation-name:tierPop;animation-duration:.5s;animation-timing-function:cubic-bezier(.34,1.56,.64,1);animation-fill-mode:forwards;animation-delay:.08s}\n  #tier-select.reveal .tier-club{animation-name:tierPop;animation-duration:.5s;animation-timing-function:cubic-bezier(.34,1.56,.64,1);animation-fill-mode:forwards;animation-delay:.2s}\n  #tier-select.reveal .tier-premier{animation-name:tierPop;animation-duration:.5s;animation-timing-function:cubic-bezier(.34,1.56,.64,1);animation-fill-mode:forwards;animation-delay:.32s}\n  #tier-select.reveal .tier-btn{opacity:1;pointer-events:auto}\n  @keyframes tierPop{0%{opacity:0;transform:translateX(-22px) scale(.82)}60%{opacity:1;transform:translateX(3px) scale(1.05)}100%{opacity:1;transform:translateX(0) scale(1)}}\n  .tier-amateur{--glow:rgba(61,220,107,.9);width:68px;align-self:flex-start;border-color:#3ddc6b;background:linear-gradient(160deg,#1a4d28,#0a1f10 75%)}\n  .tier-club{--glow:rgba(255,176,32,.9);width:84px;align-self:flex-start;margin-left:8px;border-color:#ffb020;background:linear-gradient(160deg,#7a4a06,#2c1c02 75%)}\n  .tier-premier{--glow:rgba(255,65,54,.9);width:94px;align-self:flex-start;margin-left:15px;border-color:#ff4136;background:linear-gradient(160deg,#6e1210,#220505 75%)}\n  .tier-btn.selected{filter:brightness(1.1)}\n  .tier-btn.selected::after{opacity:1;box-shadow:0 0 14px var(--glow);animation:tierGlowPulse 1.4s ease-in-out infinite}\n  @keyframes tierGlowPulse{0%,100%{opacity:.65}50%{opacity:1}}\n  .tier-btn:active{filter:brightness(1.3)}\n  .tier-coins{position:absolute;left:-5px;bottom:-6px;width:22px;height:14px;pointer-events:none;z-index:2;transition:filter .35s ease}\n  .tier-coins i{position:absolute;display:block;width:11px;height:11px;border-radius:50%;background:radial-gradient(circle at 34% 26%,#ffe66d,#c99a00 72%);box-shadow:0 1px 2px rgba(0,0,0,.5),inset 0 1px 1px rgba(255,255,255,.6),inset 0 -2px 2px rgba(120,80,0,.5);border:.7px solid rgba(255,255,255,.3)}\n  .tier-coins i:nth-child(1){left:0;bottom:0;z-index:3}\n  #tier-select.locked .tier-btn{pointer-events:none;filter:grayscale(1) brightness(.5);animation-play-state:paused;transform:translateX(0) scale(1)!important}\n  #tier-select.locked .tier-btn::after{animation-play-state:paused;opacity:.3!important}\n  #tier-select.locked .tier-coins{filter:grayscale(1) brightness(.6)}\n  .tier-btn.reenable{animation:tierReenable .55s ease-out!important}\n  @keyframes tierReenable{0%{filter:grayscale(1) brightness(.5)}45%{filter:grayscale(0) brightness(1.55)}100%{filter:grayscale(0) brightness(1)}}\n  .tier-coins i:nth-child(2){left:5px;bottom:1.5px;z-index:2}\n  .tier-coins i:nth-child(3){left:10px;bottom:3px;z-index:1}\n\n  /* ================= AUTH SCREEN ================= */\n  #auth-screen{position:absolute;inset:0;z-index:60;display:flex;align-items:center;justify-content:center;overflow:hidden;background:radial-gradient(circle at 50% 20%,#134026 0%,#081a10 48%,#020402 100%);background-size:180% 180%;animation:bgDrift 10s ease-in-out infinite;transition:opacity .55s cubic-bezier(.4,0,.2,1),transform .55s cubic-bezier(.4,0,.2,1);padding:24px}\n  #auth-screen.hide{opacity:0;pointer-events:none;transform:scale(1.05)}\n  .auth-orb{position:absolute;border-radius:50%;filter:blur(2px);pointer-events:none;background:radial-gradient(circle,rgba(143,242,156,.35) 0%,rgba(143,242,156,0) 70%);animation:orbFloat 7s ease-in-out infinite}\n  @keyframes orbFloat{0%,100%{transform:translate(0,0) scale(1)}50%{transform:translate(14px,-22px) scale(1.12)}}\n  .auth-card{position:relative;z-index:2;width:100%;max-width:360px;border-radius:22px;padding:30px 26px 26px;background:linear-gradient(180deg,rgba(20,38,26,.72) 0%,rgba(8,18,12,.82) 100%);backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px);border:1px solid rgba(143,242,156,.18);box-shadow:0 24px 60px rgba(0,0,0,.55),inset 0 1px 0 rgba(255,255,255,.06);opacity:0;transform:translateY(24px) scale(.96);animation:cardIn .7s cubic-bezier(.2,.85,.3,1) .1s forwards}\n  @keyframes cardIn{to{opacity:1;transform:translateY(0) scale(1)}}\n  .auth-logo{display:flex;flex-direction:column;align-items:center;margin-bottom:20px}\n  .auth-ball{width:44px;height:44px;border-radius:50%;background:radial-gradient(circle at 32% 28%,#fff 0 18%,transparent 19%),radial-gradient(circle at 68% 28%,#fff 0 18%,transparent 19%),radial-gradient(circle at 50% 62%,#fff 0 20%,transparent 21%),#1a1a1a;background-color:#e9e9e9;box-shadow:0 0 18px rgba(143,242,156,.4);animation:authBallSpin 3.2s linear infinite}\n  @keyframes authBallSpin{to{transform:rotate(360deg)}}\n  .auth-title{margin-top:10px;color:#f2f2f2;font-size:19px;font-weight:800;letter-spacing:2.5px;text-transform:uppercase;text-shadow:0 0 14px rgba(143,242,156,.3)}\n  .auth-tabs{position:relative;display:flex;background:rgba(255,255,255,.06);border-radius:12px;padding:4px;margin-bottom:22px;border:1px solid rgba(255,255,255,.08)}\n  .auth-tab{flex:1;position:relative;z-index:2;text-align:center;padding:10px 0;font-size:13px;font-weight:700;letter-spacing:1px;color:#9aa79f;background:none;border:none;cursor:pointer;transition:color .3s ease}\n  .auth-tab.active{color:#08130b}\n  .auth-tab-slider{position:absolute;top:4px;left:4px;width:calc(50% - 4px);height:calc(100% - 8px);border-radius:9px;background:linear-gradient(135deg,#8ef29c,#3ddc6b);box-shadow:0 4px 14px rgba(61,220,107,.45);transition:transform .38s cubic-bezier(.34,1.56,.64,1);z-index:1}\n  .auth-tab-slider.right{transform:translateX(100%)}\n  .auth-form{display:none;flex-direction:column;gap:14px;animation:formIn .4s cubic-bezier(.2,.85,.3,1)}\n  .auth-form.active{display:flex}\n  @keyframes formIn{from{opacity:0;transform:translateX(10px)}to{opacity:1;transform:translateX(0)}}\n  .auth-field{position:relative}\n  .auth-field input{width:100%;padding:14px 14px 14px 42px;border-radius:11px;border:1.5px solid rgba(255,255,255,.12);background:rgba(255,255,255,.05);color:#f0f0f0;font-size:14px;outline:none;transition:border-color .25s ease,box-shadow .25s ease,background .25s ease}\n  .auth-field input::placeholder{color:#7c8a80}\n  .auth-field input:focus{border-color:#8ef29c;box-shadow:0 0 0 3px rgba(143,242,156,.15),0 0 16px rgba(143,242,156,.25);background:rgba(255,255,255,.08)}\n  .auth-field .fic{position:absolute;left:14px;top:50%;transform:translateY(-50%);font-size:15px;opacity:.7;pointer-events:none}\n  .auth-field.shake{animation:fieldShake .4s ease}\n  @keyframes fieldShake{0%,100%{transform:translateX(0)}20%{transform:translateX(-7px)}40%{transform:translateX(6px)}60%{transform:translateX(-4px)}80%{transform:translateX(3px)}}\n  .auth-field.err input{border-color:#ff6b6b;box-shadow:0 0 0 3px rgba(255,107,107,.15)}\n  .auth-msg{min-height:16px;font-size:12px;letter-spacing:.3px;text-align:center;color:#ff8a8a;transition:opacity .2s ease}\n  .auth-msg.ok{color:#8ef29c}\n  .auth-submit{position:relative;margin-top:4px;height:48px;border:none;border-radius:12px;background:linear-gradient(135deg,#3ddc6b,#2fb85a 55%,#1f8a43);color:#06120a;font-size:14px;font-weight:800;letter-spacing:1.5px;text-transform:uppercase;cursor:pointer;overflow:hidden;box-shadow:0 10px 24px rgba(47,184,90,.35),inset 0 1px 0 rgba(255,255,255,.35);transition:transform .15s ease,box-shadow .15s ease}\n  .auth-submit:active{transform:scale(.97)}\n  .auth-submit::after{content:"";position:absolute;inset:0;background:linear-gradient(110deg,transparent 30%,rgba(255,255,255,.55) 48%,transparent 66%);background-size:220% 100%;animation:shimmer 2.6s linear infinite}\n  .auth-submit .spin{display:none;width:18px;height:18px;border:2.5px solid rgba(6,18,10,.25);border-top-color:#06120a;border-radius:50%;animation:spin .7s linear infinite;margin:0 auto}\n  .auth-submit.loading .lbl{display:none}\n  .auth-submit.loading .spin{display:block}\n  .auth-submit.success{background:linear-gradient(135deg,#8ef29c,#3ddc6b)}\n  .auth-switch{margin-top:16px;text-align:center;font-size:12.5px;color:#9aa79f}\n  .auth-switch b{color:#8ef29c;cursor:pointer;font-weight:700}\n  .auth-check{position:absolute;inset:0;z-index:70;display:none;align-items:center;justify-content:center;background:rgba(2,6,3,.55);backdrop-filter:blur(6px)}\n  .auth-check.show{display:flex}\n  .auth-check-circle{width:88px;height:88px;border-radius:50%;background:radial-gradient(circle,#8ef29c,#2fb85a 70%);display:flex;align-items:center;justify-content:center;box-shadow:0 0 40px rgba(143,242,156,.6);transform:scale(0);animation:checkPop .5s cubic-bezier(.34,1.56,.64,1) forwards}\n  @keyframes checkPop{to{transform:scale(1)}}\n  .auth-check-circle svg{width:42px;height:42px}\n  .auth-check-circle path{stroke:#06120a;stroke-width:4;fill:none;stroke-linecap:round;stroke-linejoin:round;stroke-dasharray:40;stroke-dashoffset:40;animation:checkDraw .35s ease .35s forwards}\n  @keyframes checkDraw{to{stroke-dashoffset:0}}\n\n  /* ===== KICKOFF FLASH khi vào giao diện game ===== */\n  #kickoff-flash{position:absolute;inset:0;z-index:45;pointer-events:none;display:flex;align-items:center;justify-content:center;opacity:0}\n  #kickoff-flash.play{animation:kfFade 1s ease forwards}\n  #kickoff-flash::before{content:"";position:absolute;inset:0;background:radial-gradient(circle at 50% 45%,rgba(255,255,255,.9) 0%,rgba(143,242,156,.35) 30%,transparent 62%);transform:scale(.2);opacity:0}\n  #kickoff-flash.play::before{animation:kfRing .8s cubic-bezier(.16,.84,.32,1) forwards}\n  @keyframes kfRing{0%{transform:scale(.2);opacity:.95}100%{transform:scale(2.4);opacity:0}}\n  @keyframes kfFade{0%{opacity:1}70%{opacity:1}100%{opacity:0}}\n  .kickoff-text{position:relative;color:#fff;font-size:26px;font-weight:900;letter-spacing:6px;text-transform:uppercase;text-shadow:0 0 22px rgba(143,242,156,.85),0 2px 6px rgba(0,0,0,.6);opacity:0;transform:scale(.6)}\n  #kickoff-flash.play .kickoff-text{animation:kfText .8s cubic-bezier(.2,.9,.25,1.2) forwards}\n  @keyframes kfText{0%{opacity:0;transform:scale(.5)}45%{opacity:1;transform:scale(1.12)}65%{transform:scale(.97)}100%{opacity:0;transform:scale(1.02)}}\n</style>\n</head>\n<body>\n<!-- THÊM THẺ AUDIO ĐỂ PHÁT NHẠC NỀN -->\n<audio id="bgm" loop preload="auto">\n    <source src="/nhacnen.mp3" type="audio/mpeg">\n</audio>\n\n<div id="rotate-warning"><div class="rotate-icon">📱</div><div style="font-size:15px;letter-spacing:1px;">Vui lòng xoay điện thoại về chế độ dọc</div></div>\n\n<div id="kickoff-flash"><span class="kickoff-text">Vào sân!</span></div>\n\n<div id="loading-screen" style="display:none;"><div class="particles" id="particles"></div><div class="logo-wrap"><div class="ball-halo"></div><div class="ball"></div><div class="ball-shadow"></div><div class="game-title">Goal Keeper</div></div><div class="bar-track"><div class="bar-fill" id="barFill"></div></div><div class="pct" id="pctText">Đang tải... 0%</div></div>\n<div id="game-screen"><canvas id="gameCanvas"></canvas><div id="goal-notify"><span class="gn-ring"></span><span class="gn-burst"></span><span class="gn-text"></span></div><div id="bet-controls"><button type="button" class="bet-tri bet-tri-left" id="betMinus" aria-label="Giảm cược"><span class="bet-tri-face"></span><span class="bet-tri-inner">−</span></button><button type="button" class="bet-square" id="playBtn" aria-label="Chơi"><span class="bet-play-text">PLAY</span><span class="bet-amount" id="betAmountText">1 Token</span></button><button type="button" class="bet-tri bet-tri-right" id="betPlus" aria-label="Tăng cược"><span class="bet-tri-face"></span><span class="bet-tri-inner">+</span></button></div><div id="tier-select"><div id="tier-hand">👉</div><button type="button" class="tier-btn tier-amateur selected" data-mult="1.7" data-tier="amateur" aria-label="Hạng Amateur"><span class="tier-coins"><i></i><i></i><i></i></span><span class="tier-label">AMATEUR</span></button><button type="button" class="tier-btn tier-club" data-mult="2.4" data-tier="club" aria-label="Hạng Club"><span class="tier-coins"><i></i><i></i><i></i></span><span class="tier-label">CLUB</span></button><button type="button" class="tier-btn tier-premier" data-mult="3.4" data-tier="premier" aria-label="Hạng Premier"><span class="tier-coins"><i></i><i></i><i></i></span><span class="tier-label">PREMIER</span></button></div><div id="shot-controls">\n<button type="button" class="shot-btn" data-dir="left" aria-label="Sút trái"><svg viewBox="0 0 200 220" xmlns="http://www.w3.org/2000/svg"><defs><linearGradient id="goldGradL" x1="10%" y1="0%" x2="90%" y2="100%"><stop offset="0%" stop-color="#fffdc8"/><stop offset="22%" stop-color="#ffe45c"/><stop offset="50%" stop-color="#ffc200"/><stop offset="78%" stop-color="#f08a00"/><stop offset="100%" stop-color="#a85f00"/></linearGradient><linearGradient id="hiGradL" x1="0%" y1="0%" x2="100%" y2="60%"><stop offset="0%" stop-color="#ffffff" stop-opacity="0.9"/><stop offset="100%" stop-color="#ffffff" stop-opacity="0"/></linearGradient><filter id="dropShadowL" x="-40%" y="-40%" width="180%" height="180%"><feDropShadow dx="3" dy="6" stdDeviation="4" flood-color="#2a4200" flood-opacity="0.5"/></filter></defs><path fill="url(#goldGradL)" stroke="#7a4a00" stroke-width="2" stroke-linejoin="round" filter="url(#dropShadowL)" d="M 151.3,209.3 L 147.3,207.2 L 143.3,205.0 L 139.4,202.8 L 135.5,200.5 L 131.6,198.1 L 127.8,195.6 L 124.1,193.1 L 120.4,190.5 L 116.9,187.9 L 113.3,185.2 L 109.9,182.4 L 106.6,179.6 L 103.4,176.7 L 100.3,173.8 L 97.3,170.9 L 94.4,167.9 L 91.7,164.8 L 89.1,161.7 L 86.7,158.6 L 84.4,155.4 L 82.3,152.3 L 80.4,149.0 L 78.6,145.8 L 77.0,142.6 L 75.6,139.3 L 74.4,136.0 L 73.3,132.7 L 72.5,129.4 L 71.8,126.1 L 71.3,122.8 L 71.0,119.5 L 70.9,116.2 L 71.0,112.9 L 71.3,109.5 L 71.8,106.1 L 72.5,102.7 L 73.4,99.2 L 74.5,95.7 L 75.8,92.1 L 77.4,88.5 L 103.4,108.1 L 75.6,47.7 L 16.5,78.0 L 49.0,78.7 L 47.7,84.0 L 46.8,89.3 L 46.1,94.4 L 45.7,99.5 L 45.7,104.5 L 45.9,109.4 L 46.4,114.2 L 47.1,118.8 L 48.1,123.4 L 49.4,127.8 L 50.8,132.1 L 52.5,136.3 L 54.4,140.3 L 56.5,144.3 L 58.7,148.1 L 61.1,151.8 L 63.7,155.4 L 66.4,158.8 L 69.3,162.2 L 72.3,165.4 L 75.4,168.6 L 78.6,171.7 L 81.9,174.7 L 85.3,177.6 L 88.9,180.4 L 92.5,183.1 L 96.2,185.8 L 99.9,188.4 L 103.8,190.9 L 107.7,193.3 L 111.6,195.7 L 115.6,198.1 L 119.7,200.3 L 123.7,202.5 L 127.9,204.7 L 132.0,206.8 L 136.2,208.8 L 140.4,210.8 L 144.5,212.8 L 148.7,214.7 Z"/><path fill="url(#hiGradL)" opacity="0.55" d="M 151.3,209.3 L 147.3,207.2 L 143.3,205.0 L 139.4,202.8 L 135.5,200.5 L 131.6,198.1 L 127.8,195.6 L 124.1,193.1 L 120.4,190.5 L 116.9,187.9 L 113.3,185.2 L 109.9,182.4 L 106.6,179.6 L 103.4,176.7 L 100.3,173.8 L 97.3,170.9 L 94.4,167.9 L 91.7,164.8 L 89.1,161.7 L 86.7,158.6 L 84.4,155.4 L 82.3,152.3 L 80.4,149.0 L 78.6,145.8 L 77.0,142.6 L 75.6,139.3 L 74.4,136.0 L 73.3,132.7 L 72.5,129.4 L 71.8,126.1 L 71.3,122.8 L 71.0,119.5 L 70.9,116.2 L 71.0,112.9 L 71.3,109.5 L 71.8,106.1 L 72.5,102.7 L 73.4,99.2 L 74.5,95.7 L 75.8,92.1 L 77.4,88.5 L 60.9,82.8 L 59.5,87.4 L 58.4,92.0 L 57.6,96.4 L 57.0,100.8 L 56.6,105.2 L 56.6,109.4 L 56.7,113.6 L 57.1,117.7 L 57.7,121.8 L 58.6,125.7 L 59.6,129.6 L 60.9,133.4 L 62.3,137.1 L 64.0,140.8 L 65.8,144.4 L 67.8,147.9 L 70.0,151.3 L 72.3,154.7 L 74.8,158.0 L 77.4,161.2 L 80.1,164.4 L 83.0,167.5 L 86.0,170.5 L 89.2,173.5 L 92.4,176.4 L 95.8,179.2 L 99.2,182.0 L 102.7,184.7 L 106.3,187.3 L 110.0,189.9 L 113.8,192.4 L 117.6,194.9 L 121.5,197.3 L 125.5,199.6 L 129.5,201.9 L 133.5,204.1 L 137.5,206.3 L 141.6,208.4 L 145.7,210.4 L 149.8,212.4 Z"/></svg></button>\n<button type="button" class="shot-btn center" data-dir="mid" aria-label="Sút thẳng"><svg viewBox="0 0 200 220" xmlns="http://www.w3.org/2000/svg"><defs><linearGradient id="goldGradM" x1="10%" y1="0%" x2="90%" y2="100%"><stop offset="0%" stop-color="#fffdc8"/><stop offset="22%" stop-color="#ffe45c"/><stop offset="50%" stop-color="#ffc200"/><stop offset="78%" stop-color="#f08a00"/><stop offset="100%" stop-color="#a85f00"/></linearGradient><linearGradient id="hiGradM" x1="0%" y1="0%" x2="100%" y2="60%"><stop offset="0%" stop-color="#ffffff" stop-opacity="0.9"/><stop offset="100%" stop-color="#ffffff" stop-opacity="0"/></linearGradient><filter id="dropShadowM" x="-40%" y="-40%" width="180%" height="180%"><feDropShadow dx="3" dy="6" stdDeviation="4" flood-color="#2a4200" flood-opacity="0.5"/></filter></defs><path fill="url(#goldGradM)" stroke="#7a4a00" stroke-width="2" stroke-linejoin="round" filter="url(#dropShadowM)" d="M 101.0,214.0 L 101.1,209.6 L 101.3,205.3 L 101.4,201.1 L 101.7,196.9 L 101.9,192.8 L 102.1,188.8 L 102.3,184.8 L 102.6,180.9 L 102.9,177.0 L 103.1,173.2 L 103.4,169.5 L 103.7,165.8 L 104.0,162.1 L 104.3,158.5 L 104.6,154.9 L 105.0,151.4 L 105.3,147.9 L 105.6,144.4 L 105.9,141.0 L 106.3,137.6 L 106.6,134.2 L 107.0,130.9 L 107.3,127.5 L 107.7,124.2 L 108.1,120.9 L 108.4,117.7 L 108.8,114.4 L 109.2,111.1 L 109.6,107.9 L 109.9,104.6 L 110.3,101.4 L 110.7,98.1 L 111.1,94.9 L 111.5,91.6 L 111.9,88.4 L 112.3,85.1 L 112.7,81.8 L 113.2,78.5 L 113.6,75.2 L 114.0,71.8 L 148.0,81.8 L 100.0,31.8 L 52.0,81.8 L 86.0,71.8 L 86.4,75.2 L 86.8,78.5 L 87.3,81.8 L 87.7,85.1 L 88.1,88.4 L 88.5,91.6 L 88.9,94.9 L 89.3,98.1 L 89.7,101.4 L 90.1,104.6 L 90.4,107.9 L 90.8,111.1 L 91.2,114.4 L 91.6,117.7 L 91.9,120.9 L 92.3,124.2 L 92.7,127.5 L 93.0,130.9 L 93.4,134.2 L 93.7,137.6 L 94.1,141.0 L 94.4,144.4 L 94.7,147.9 L 95.0,151.4 L 95.4,154.9 L 95.7,158.5 L 96.0,162.1 L 96.3,165.8 L 96.6,169.5 L 96.9,173.2 L 97.1,177.0 L 97.4,180.9 L 97.7,184.8 L 97.9,188.8 L 98.1,192.8 L 98.3,196.9 L 98.6,201.1 L 98.7,205.3 L 98.9,209.6 L 99.0,214.0 Z"/><path fill="url(#hiGradM)" opacity="0.55" d="M 101.0,214.0 L 101.1,209.6 L 101.3,205.3 L 101.4,201.1 L 101.7,196.9 L 101.9,192.8 L 102.1,188.8 L 102.3,184.8 L 102.6,180.9 L 102.9,177.0 L 103.1,173.2 L 103.4,169.5 L 103.7,165.8 L 104.0,162.1 L 104.3,158.5 L 104.6,154.9 L 105.0,151.4 L 105.3,147.9 L 105.6,144.4 L 105.9,141.0 L 106.3,137.6 L 106.6,134.2 L 107.0,130.9 L 107.3,127.5 L 107.7,124.2 L 108.1,120.9 L 108.4,117.7 L 108.8,114.4 L 109.2,111.1 L 109.6,107.9 L 109.9,104.6 L 110.3,101.4 L 110.7,98.1 L 111.1,94.9 L 111.5,91.6 L 111.9,88.4 L 112.3,85.1 L 112.7,81.8 L 113.2,78.5 L 113.6,75.2 L 114.0,71.8 L 98.6,71.8 L 98.6,75.2 L 98.7,78.5 L 98.7,81.8 L 98.8,85.1 L 98.8,88.4 L 98.8,91.6 L 98.9,94.9 L 98.9,98.1 L 99.0,101.4 L 99.0,104.6 L 99.0,107.9 L 99.1,111.1 L 99.1,114.4 L 99.2,117.7 L 99.2,120.9 L 99.2,124.2 L 99.3,127.5 L 99.3,130.9 L 99.3,134.2 L 99.4,137.6 L 99.4,141.0 L 99.4,144.4 L 99.5,147.9 L 99.5,151.4 L 99.5,154.9 L 99.6,158.5 L 99.6,162.1 L 99.6,165.8 L 99.7,169.5 L 99.7,173.2 L 99.7,177.0 L 99.7,180.9 L 99.8,184.8 L 99.8,188.8 L 99.8,192.8 L 99.8,196.9 L 99.9,201.1 L 99.9,205.3 L 99.9,209.6 L 99.9,214.0 Z"/></svg></button>\n<button type="button" class="shot-btn" data-dir="right" aria-label="Sút phải"><svg viewBox="0 0 200 220" xmlns="http://www.w3.org/2000/svg"><defs><linearGradient id="goldGradR" x1="10%" y1="0%" x2="90%" y2="100%"><stop offset="0%" stop-color="#fffdc8"/><stop offset="22%" stop-color="#ffe45c"/><stop offset="50%" stop-color="#ffc200"/><stop offset="78%" stop-color="#f08a00"/><stop offset="100%" stop-color="#a85f00"/></linearGradient><linearGradient id="hiGradR" x1="0%" y1="0%" x2="100%" y2="60%"><stop offset="0%" stop-color="#ffffff" stop-opacity="0.9"/><stop offset="100%" stop-color="#ffffff" stop-opacity="0"/></linearGradient><filter id="dropShadowR" x="-40%" y="-40%" width="180%" height="180%"><feDropShadow dx="3" dy="6" stdDeviation="4" flood-color="#2a4200" flood-opacity="0.5"/></filter></defs><path fill="url(#goldGradR)" stroke="#7a4a00" stroke-width="2" stroke-linejoin="round" filter="url(#dropShadowR)" d="M 51.3,214.7 L 55.5,212.8 L 59.6,210.8 L 63.8,208.8 L 68.0,206.8 L 72.1,204.7 L 76.3,202.5 L 80.3,200.3 L 84.4,198.1 L 88.4,195.7 L 92.3,193.3 L 96.2,190.9 L 100.1,188.4 L 103.8,185.8 L 107.5,183.1 L 111.1,180.4 L 114.7,177.6 L 118.1,174.7 L 121.4,171.7 L 124.6,168.6 L 127.7,165.4 L 130.7,162.2 L 133.6,158.8 L 136.3,155.4 L 138.9,151.8 L 141.3,148.1 L 143.5,144.3 L 145.6,140.3 L 147.5,136.3 L 149.2,132.1 L 150.6,127.8 L 151.9,123.4 L 152.9,118.8 L 153.6,114.2 L 154.1,109.4 L 154.3,104.5 L 154.3,99.5 L 153.9,94.4 L 153.2,89.3 L 152.3,84.0 L 151.0,78.7 L 183.5,78.0 L 124.4,47.7 L 96.6,108.1 L 122.6,88.5 L 124.2,92.1 L 125.5,95.7 L 126.6,99.2 L 127.5,102.7 L 128.2,106.1 L 128.7,109.5 L 129.0,112.9 L 129.1,116.2 L 129.0,119.5 L 128.7,122.8 L 128.2,126.1 L 127.5,129.4 L 126.7,132.7 L 125.6,136.0 L 124.4,139.3 L 123.0,142.6 L 121.4,145.8 L 119.6,149.0 L 117.7,152.3 L 115.6,155.4 L 113.3,158.6 L 110.9,161.7 L 108.3,164.8 L 105.6,167.9 L 102.7,170.9 L 99.7,173.8 L 96.6,176.7 L 93.4,179.6 L 90.1,182.4 L 86.7,185.2 L 83.1,187.9 L 79.6,190.5 L 75.9,193.1 L 72.2,195.6 L 68.4,198.1 L 64.5,200.5 L 60.6,202.8 L 56.7,205.0 L 52.7,207.2 L 48.7,209.3 Z"/><path fill="url(#hiGradR)" opacity="0.55" d="M 51.3,214.7 L 55.5,212.8 L 59.6,210.8 L 63.8,208.8 L 68.0,206.8 L 72.1,204.7 L 76.3,202.5 L 80.3,200.3 L 84.4,198.1 L 88.4,195.7 L 92.3,193.3 L 96.2,190.9 L 100.1,188.4 L 103.8,185.8 L 107.5,183.1 L 111.1,180.4 L 114.7,177.6 L 118.1,174.7 L 121.4,171.7 L 124.6,168.6 L 127.7,165.4 L 130.7,162.2 L 133.6,158.8 L 136.3,155.4 L 138.9,151.8 L 141.3,148.1 L 143.5,144.3 L 145.6,140.3 L 147.5,136.3 L 149.2,132.1 L 150.6,127.8 L 151.9,123.4 L 152.9,118.8 L 153.6,114.2 L 154.1,109.4 L 154.3,104.5 L 154.3,99.5 L 153.9,94.4 L 153.2,89.3 L 152.3,84.0 L 151.0,78.7 L 139.1,82.8 L 140.5,87.4 L 141.6,92.0 L 142.4,96.4 L 143.0,100.8 L 143.4,105.2 L 143.4,109.4 L 143.3,113.6 L 142.9,117.7 L 142.3,121.8 L 141.4,125.7 L 140.4,129.6 L 139.1,133.4 L 137.7,137.1 L 136.0,140.8 L 134.2,144.4 L 132.2,147.9 L 130.0,151.3 L 127.7,154.7 L 125.2,158.0 L 122.6,161.2 L 119.9,164.4 L 117.0,167.5 L 114.0,170.5 L 110.8,173.5 L 107.6,176.4 L 104.2,179.2 L 100.8,182.0 L 97.3,184.7 L 93.7,187.3 L 90.0,189.9 L 86.2,192.4 L 82.4,194.9 L 78.5,197.3 L 74.5,199.6 L 70.5,201.9 L 66.5,204.1 L 62.5,206.3 L 58.4,208.4 L 54.3,210.4 L 50.2,212.4 Z"/></svg></button>\n</div></div><div id="cashout-bar" aria-label="Rút tiền"><div class="co-glow"></div><button type="button" class="cashout-btn disabled" id="cashoutBtn"><span class="cashout-shine"></span><span class="cashout-coins cashout-coins-left"><i></i><i></i><i></i></span><span class="cashout-label">CASH OUT</span><span class="cashout-amount" id="cashoutAmount">0 Token</span><span class="cashout-coins cashout-coins-right"><i></i><i></i><i></i></span></button></div><div id="balance-display"><span id="balance-coin">🪙</span><span id="balance-amount">100</span></div><div id="jackpot-ladder"><svg viewBox="0 0 445 610" xmlns="http://www.w3.org/2000/svg">\n  <defs>\n    <radialGradient id="jpFire" cx="50%" cy="35%" r="75%">\n      <stop offset="0%" stop-color="#ffdd88"/><stop offset="30%" stop-color="#ff8a00"/><stop offset="65%" stop-color="#8a1500"/><stop offset="100%" stop-color="#210500"/>\n    </radialGradient>\n    <linearGradient id="jpNavy" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#123663"/><stop offset="100%" stop-color="#081b36"/></linearGradient>\n    <linearGradient id="jpGold" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#fff2a8"/><stop offset="35%" stop-color="#ffcf3f"/><stop offset="70%" stop-color="#ff8a12"/><stop offset="100%" stop-color="#c94c00"/></linearGradient>\n    <linearGradient id="jpTitleFill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#fff7d6"/><stop offset="45%" stop-color="#ffcf3f"/><stop offset="100%" stop-color="#d98a00"/></linearGradient>\n  </defs>\n  <polygon id="jpRow9" class="jp-row-lit" points="55.6,100 430,100 430,154.44 71.1,154.44" fill="url(#jpGold)" stroke="#f2c14e" stroke-width="2.5"/>\n  <polygon id="jpRow8" class="jp-row-lit" points="71.1,154.44 430,154.44 430,208.89 86.6,208.89" fill="url(#jpNavy)" stroke="#f2c14e" stroke-width="2.5"/>\n  <polygon id="jpRow7" class="jp-row-lit" points="86.6,208.89 430,208.89 430,263.33 102.1,263.33" fill="url(#jpNavy)" stroke="#f2c14e" stroke-width="2.5"/>\n  <polygon id="jpRow6" class="jp-row-lit" points="102.1,263.33 430,263.33 430,317.78 117.6,317.78" fill="url(#jpNavy)" stroke="#f2c14e" stroke-width="2.5"/>\n  <polygon id="jpRow5" class="jp-row-lit" points="117.6,317.78 430,317.78 430,372.22 133.0,372.22" fill="url(#jpNavy)" stroke="#f2c14e" stroke-width="2.5"/>\n  <polygon id="jpRow4" class="jp-row-lit" points="133.0,372.22 430,372.22 430,426.67 148.5,426.67" fill="url(#jpNavy)" stroke="#f2c14e" stroke-width="2.5"/>\n  <polygon id="jpRow3" class="jp-row-lit" points="148.5,426.67 430,426.67 430,481.11 164.0,481.11" fill="url(#jpNavy)" stroke="#f2c14e" stroke-width="2.5"/>\n  <polygon id="jpRow2" class="jp-row-lit" points="164.0,481.11 430,481.11 430,535.56 179.5,535.56" fill="url(#jpNavy)" stroke="#f2c14e" stroke-width="2.5"/>\n  <polygon id="jpRow1" class="jp-row-lit" points="179.5,535.56 430,535.56 430,590 195,590" fill="url(#jpNavy)" stroke="#f2c14e" stroke-width="2.5"/>\n  <polygon points="30,10 430,10 430,100 55.6,100" fill="url(#jpFire)" stroke="#f2c14e" stroke-width="3"/>\n  <text x="230" y="70" text-anchor="middle" font-size="46" class="jp-row-text" fill="url(#jpTitleFill)" stroke="#7a3d00" stroke-width="2" paint-order="stroke">JACKPOT</text>\n  <polygon points="30,10 430,10 430,590 195,590" fill="none" stroke="#2ecc40" stroke-width="7" stroke-linejoin="round"/>\n  <polygon points="30,10 430,10 430,590 195,590" fill="none" stroke="#a8ffb0" stroke-width="1.5" stroke-linejoin="round" opacity="0.7"/>\n  <text id="jpNum9" x="83" y="135" class="jp-row-text" font-size="30" fill="#ffffff" stroke="#5a2200" stroke-width="1.5" paint-order="stroke">9</text>\n  <text id="jpVal9" x="418" y="135" text-anchor="end" class="jp-row-text" font-size="30" fill="#ffffff" stroke="#5a2200" stroke-width="1.2" paint-order="stroke">512 Token</text>\n  <text id="jpNum8" x="98" y="189" class="jp-row-text" font-size="28" fill="#f4f4f4" stroke="#0a1a30" stroke-width="1.5" paint-order="stroke">8</text>\n  <text id="jpVal8" x="418" y="189" text-anchor="end" class="jp-row-text" font-size="28" fill="#f2c14e" stroke="#3a1c00" stroke-width="1.2" paint-order="stroke">256 Token</text>\n  <text id="jpNum7" x="114" y="244" class="jp-row-text" font-size="28" fill="#f4f4f4" stroke="#0a1a30" stroke-width="1.5" paint-order="stroke">7</text>\n  <text id="jpVal7" x="418" y="244" text-anchor="end" class="jp-row-text" font-size="28" fill="#f2c14e" stroke="#3a1c00" stroke-width="1.2" paint-order="stroke">128 Token</text>\n  <text id="jpNum6" x="130" y="298" class="jp-row-text" font-size="28" fill="#f4f4f4" stroke="#0a1a30" stroke-width="1.5" paint-order="stroke">6</text>\n  <text id="jpVal6" x="418" y="298" text-anchor="end" class="jp-row-text" font-size="28" fill="#f2c14e" stroke="#3a1c00" stroke-width="1.2" paint-order="stroke">64 Token</text>\n  <text id="jpNum5" x="145" y="352" class="jp-row-text" font-size="28" fill="#f4f4f4" stroke="#0a1a30" stroke-width="1.5" paint-order="stroke">5</text>\n  <text id="jpVal5" x="418" y="352" text-anchor="end" class="jp-row-text" font-size="28" fill="#f2c14e" stroke="#3a1c00" stroke-width="1.2" paint-order="stroke">32 Token</text>\n  <text id="jpNum4" x="161" y="407" class="jp-row-text" font-size="28" fill="#f4f4f4" stroke="#0a1a30" stroke-width="1.5" paint-order="stroke">4</text>\n  <text id="jpVal4" x="418" y="407" text-anchor="end" class="jp-row-text" font-size="28" fill="#f2c14e" stroke="#3a1c00" stroke-width="1.2" paint-order="stroke">16 Token</text>\n  <text id="jpNum3" x="176" y="461" class="jp-row-text" font-size="28" fill="#f4f4f4" stroke="#0a1a30" stroke-width="1.5" paint-order="stroke">3</text>\n  <text id="jpVal3" x="418" y="461" text-anchor="end" class="jp-row-text" font-size="28" fill="#f2c14e" stroke="#3a1c00" stroke-width="1.2" paint-order="stroke">8 Token</text>\n  <text id="jpNum2" x="192" y="516" class="jp-row-text" font-size="28" fill="#f4f4f4" stroke="#0a1a30" stroke-width="1.5" paint-order="stroke">2</text>\n  <text id="jpVal2" x="418" y="516" text-anchor="end" class="jp-row-text" font-size="28" fill="#f2c14e" stroke="#3a1c00" stroke-width="1.2" paint-order="stroke">4 Token</text>\n  <text id="jpNum1" x="207" y="570" class="jp-row-text" font-size="28" fill="#f4f4f4" stroke="#0a1a30" stroke-width="1.5" paint-order="stroke">1</text>\n  <text id="jpVal1" x="418" y="570" text-anchor="end" class="jp-row-text" font-size="28" fill="#f2c14e" stroke="#3a1c00" stroke-width="1.2" paint-order="stroke">2 Token</text>\n</svg></div>\n\n<script>\n(function(){\n  // Da vo hieu hoa hoan toan Fullscreen API cho app nay: game luon\n  // chay vua khit trong khung man hinh MAGICQN, khong tran ra ngoai nua.\n  try {\n    var noop = function(){ return { catch: function(){}, then: function(){} }; };\n    ["requestFullscreen","webkitRequestFullscreen","mozRequestFullScreen","msRequestFullscreen"]\n      .forEach(function(m){ if (Element.prototype[m]) Element.prototype[m] = noop; });\n    if (window.screen && screen.orientation && screen.orientation.lock) {\n      screen.orientation.lock = function(){ return { catch: function(){} }; };\n    }\n  } catch (e) {}\n})();\n(function(){\n"use strict";\n// ===== XỬ LÝ ÂM THANH NỀN =====\nfunction playBGM() {\n    var bgm = document.getElementById(\'bgm\');\n    if (bgm && bgm.paused) {\n        bgm.volume = 0.4; // Âm lượng 40% để không quá ồn\n        bgm.play().catch(function(e) {\n            console.log("Trình duyệt chặn tự động phát nhạc, cần tương tác người dùng.");\n        });\n    }\n}\n// Kích hoạt nhạc khi người dùng chạm/click vào màn hình lần đầu (để tuân thủ chính sách autoplay của trình duyệt)\ndocument.addEventListener(\'click\', playBGM, { once: true });\ndocument.addEventListener(\'touchstart\', playBGM, { once: true });\n\n/* ===== LOADING ===== */\nvar barFill=document.getElementById(\'barFill\'),pctText=document.getElementById(\'pctText\'),loadingScreen=document.getElementById(\'loading-screen\'),gameScreen=document.getElementById(\'game-screen\'),loaded=false,progress=0;\n(function(){var w=document.getElementById(\'particles\');for(var i=0;i<16;i++){var p=document.createElement(\'div\');p.className=\'particle\';var s=2+Math.random()*3;p.style.width=s+\'px\';p.style.height=s+\'px\';p.style.left=(Math.random()*100)+\'%\';p.style.setProperty(\'--drift\',(Math.random()*40-20)+\'px\');p.style.animationDuration=(3.5+Math.random()*3)+\'s\';p.style.animationDelay=(Math.random()*4)+\'s\';w.appendChild(p)}})();\nstartLoading();\nfunction startLoading(){\n  loaded=true;\n  startGame();\n}\nfunction requestFS(el){/* da tat: chay vua trong man hinh app, khong doi fullscreen nua */}\nvar gameStarted=false;\nfunction startGame(){if(!loaded||gameStarted)return;gameStarted=true;requestFS(document.documentElement);loadingScreen.classList.add(\'hide\');setTimeout(function(){loadingScreen.style.display=\'none\';gameScreen.style.display=\'block\';document.getElementById(\'rotate-warning\').classList.add(\'active\');resizeCanvas();void gameScreen.offsetWidth;gameScreen.classList.add(\'show\');document.body.classList.add(\'hud-show\');var kf=document.getElementById(\'kickoff-flash\');kf.classList.add(\'play\');setTimeout(function(){kf.classList.remove(\'play\')},1050);refreshJackpotY();setTimeout(refreshJackpotY,700);gameActive=true;requestAnimationFrame(loop);showBetControls();showTierSelect();playBGM()},480)}\ndocument.getElementById(\'game-screen\').addEventListener(\'click\',function(){if(!document.fullscreenElement&&!document.webkitFullscreenElement){requestFS(document.documentElement)}});\n\n/* ===== BALANCE (hiển thị số dư, mặc định $100) ===== */\nvar playerBalance=(function(){try{var p=new URLSearchParams(window.location.search);var b=parseFloat(p.get("balance"));if(isFinite(b)&&b>=0)return b}catch(e){}return 100})();\nvar balanceDisplayEl=document.getElementById(\'balance-display\');\nvar balanceAmountEl=document.getElementById(\'balance-amount\');\nfunction formatBalance(v){var n=Math.max(0,v);return Math.round(n)}\nfunction renderBalance(v){if(balanceAmountEl)balanceAmountEl.innerHTML=formatBalance(v)}\nfunction pulseBalance(cls){if(!balanceDisplayEl)return;balanceDisplayEl.classList.remove(\'bump\',\'deny\');void balanceDisplayEl.offsetWidth;balanceDisplayEl.classList.add(cls)}\nvar balanceAnimId=null,balanceShown=playerBalance;\nfunction countBalanceTo(fromV,toV,gain){\n  if(balanceAnimId)cancelAnimationFrame(balanceAnimId);\n  var dur=gain?800:420,start=performance.now();\n  function step(now){\n    var t=Math.min((now-start)/dur,1);\n    var ease=1-Math.pow(1-t,3);\n    balanceShown=fromV+(toV-fromV)*ease;\n    renderBalance(balanceShown);\n    if(t<1){balanceAnimId=requestAnimationFrame(step)}else{balanceShown=toV;renderBalance(toV);balanceAnimId=null}\n  }\n  balanceAnimId=requestAnimationFrame(step);\n}\nfunction flashBalanceAmount(gain){\n  if(!balanceAmountEl)return;\n  balanceAmountEl.classList.remove(\'flash-gain\',\'flash-loss\');\n  void balanceAmountEl.offsetWidth;\n  balanceAmountEl.classList.add(gain?\'flash-gain\':\'flash-loss\');\n  setTimeout(function(){balanceAmountEl.classList.remove(\'flash-gain\',\'flash-loss\')},gain?800:420);\n}\nfunction spawnBalanceFloat(delta){\n  if(!balanceDisplayEl)return;\n  var el=document.createElement(\'div\');\n  el.className=\'balance-float \'+(delta>=0?\'gain\':\'loss\');\n  var amt=Math.round(Math.abs(delta)*100)/100;\n  el.textContent=(delta>=0?\'+\':\'−\')+(amt%1===0?amt:amt.toFixed(2))+\' Token\';\n  balanceDisplayEl.appendChild(el);\n  setTimeout(function(){el.remove()},900);\n}\nfunction notifyBalanceToParent(){try{window.parent.postMessage({source:"penalty-game",type:"balance",value:playerBalance},"*")}catch(e){}}function setBalance(v){playerBalance=v;balanceShown=v;renderBalance(v);notifyBalanceToParent()}\nfunction addBalance(delta){\n  var from=playerBalance;\n  playerBalance+=delta;\n  countBalanceTo(from,playerBalance,delta>0);\n  flashBalanceAmount(delta>0);\n  spawnBalanceFloat(delta);\n  pulseBalance(delta<0?\'deny\':\'bump\');\nnotifyBalanceToParent();}\nrenderBalance(playerBalance);\n\n/* ===== BET / PLAY CONTROLS ===== */\nvar betControlsEl=document.getElementById(\'bet-controls\'),shotControlsEl=document.getElementById(\'shot-controls\');\nvar playBtn=document.getElementById(\'playBtn\'),betMinusBtn=document.getElementById(\'betMinus\'),betPlusBtn=document.getElementById(\'betPlus\'),betAmountEl=document.getElementById(\'betAmountText\');\nvar betAmount=1,BET_MIN=1,BET_MAX=100;\nfunction renderBet(){betAmountEl.textContent=betAmount+\' Token\';updateJackpotValues()}\n\n/* ===== JACKPOT LADDER (multiplier board, x2 mỗi bậc, theo hệ số hạng đã chọn) ===== */\nvar jpLadderEl=document.getElementById(\'jackpot-ladder\');\nvar winStreak=0; // số lượt thắng liên tiếp hiện tại\nvar winMultiplier=1.7; // hệ số nhân của hạng đang chọn (AMATEUR/CLUB/PREMIER)\nfunction jpFormat(v){return (v>=100?Math.round(v):(Math.round(v*100)/100))+\' Token\'}\nvar jpCurrentValues=[0,0,0,0,0,0,0,0,0]; // giá trị đang hiển thị của mỗi bậc (index 0 = bậc 1)\nvar jpInitialized=false;\nfunction jpAnimateRow(el,lvl,fromV,toV){\n  var dur=520,start=performance.now();\n  el.classList.remove(\'jp-rolling\');void el.offsetWidth;el.classList.add(\'jp-rolling\');\n  function step(now){\n    var t=Math.min((now-start)/dur,1);\n    var ease=1-Math.pow(1-t,3);\n    var val=fromV+(toV-fromV)*ease;\n    el.textContent=jpFormat(val);\n    if(t<1){requestAnimationFrame(step)}else{\n      el.textContent=jpFormat(toV);\n      jpCurrentValues[lvl-1]=toV;\n      el.classList.remove(\'jp-rolling\');\n    }\n  }\n  requestAnimationFrame(step);\n}\nfunction updateJackpotValues(){\n  for(var lvl=1;lvl<=9;lvl++){\n    var amount=betAmount*winMultiplier*Math.pow(2,lvl-1);\n    var el=document.getElementById(\'jpVal\'+lvl);\n    if(!el)continue;\n    if(!jpInitialized){\n      el.textContent=jpFormat(amount);\n      jpCurrentValues[lvl-1]=amount;\n      continue;\n    }\n    var fromV=jpCurrentValues[lvl-1];\n    if(Math.abs(fromV-amount)<0.005)continue;\n    jpAnimateRow(el,lvl,fromV,amount);\n  }\n  jpInitialized=true;\n}\nfunction setJackpotHighlight(level){\n  for(var lvl=1;lvl<=9;lvl++){\n    var row=document.getElementById(\'jpRow\'+lvl);\n    var num=document.getElementById(\'jpNum\'+lvl);\n    var val=document.getElementById(\'jpVal\'+lvl);\n    if(!row)continue;\n    if(lvl===level){\n      row.setAttribute(\'fill\',\'url(#jpGold)\');\n      if(num){num.setAttribute(\'fill\',\'#ffffff\');num.setAttribute(\'stroke\',\'#5a2200\')}\n      if(val){val.setAttribute(\'fill\',\'#ffffff\');val.setAttribute(\'stroke\',\'#5a2200\')}\n    }else{\n      row.setAttribute(\'fill\',\'url(#jpNavy)\');\n      if(num){num.setAttribute(\'fill\',\'#f4f4f4\');num.setAttribute(\'stroke\',\'#0a1a30\')}\n      if(val){val.setAttribute(\'fill\',\'#f2c14e\');val.setAttribute(\'stroke\',\'#3a1c00\')}\n    }\n  }\n}\nfunction jpBumpLevelUp(){jpLadderEl.classList.remove(\'levelup\');void jpLadderEl.offsetWidth;jpLadderEl.classList.add(\'levelup\');setTimeout(refreshJackpotY,550)}\nfunction jpRegisterResult(won){\n  if(won){\n    winStreak=Math.min(winStreak+1,9);\n    setJackpotHighlight(Math.min(winStreak+1,9));\n    jpBumpLevelUp();\n  }else{\n    winStreak=0;\n    setJackpotHighlight(1);\n  }\n}\n\n/* ===== GOAL RESULT NOTIFY (VÀO!! / HỤT!! trên đầu khung thành) ===== */\nvar goalNotifyEl=document.getElementById(\'goal-notify\');\nvar goalNotifyTextEl=goalNotifyEl?goalNotifyEl.querySelector(\'.gn-text\'):null;\nvar goalNotifyTimer=null;\nfunction getGoalTopPos(){\n  var w=window.innerWidth,h=window.innerHeight;\n  var gw=Math.min(w*0.62,520),gh=gw*0.42,gx=(w-gw)/2,gy=h*0.58-gh*0.92;\n  return{x:gx+gw/2,y:gy};\n}\nfunction spawnGoalSparks(cx,cy){\n  var colors=[\'#ffe45c\',\'#ffb020\',\'#fff7d6\'];\n  for(var i=0;i<12;i++){\n    (function(i){\n      var el=document.createElement(\'div\');\n      el.className=\'gn-spark\';\n      var s=3+Math.random()*4,color=colors[i%colors.length];\n      el.style.width=s+\'px\';el.style.height=s+\'px\';\n      el.style.left=(cx-s/2)+\'px\';el.style.top=(cy-s/2)+\'px\';\n      el.style.background=color;el.style.boxShadow=\'0 0 8px \'+color;\n      document.body.appendChild(el);\n      var ang=Math.random()*Math.PI*2,dist=40+Math.random()*60;\n      var tx=Math.cos(ang)*dist,ty=Math.sin(ang)*dist-20;\n      var anim=el.animate([\n        {transform:\'translate(0,0) scale(1)\',opacity:1},\n        {transform:\'translate(\'+tx+\'px,\'+ty+\'px) scale(.2)\',opacity:0}\n      ],{duration:600+Math.random()*260,easing:\'cubic-bezier(.2,.7,.3,1)\'});\n      anim.onfinish=function(){el.remove()};\n    })(i);\n  }\n}\nfunction showGoalNotify(type){\n  try{\n    var amt=jpFormat(sessionAmount(winStreak));\n    var text=type===\'goal\'?(\'Ghi bàn! Tiền thưởng hiện tại: \'+amt):\'Không ghi bàn - phiên kết thúc\';\n    window.parent.postMessage({source:\'penalty-game\',type:\'notify\',kind:type,text:text},\'*\');\n  }catch(e){}\n}\nfunction bumpPlaySquare(){playBtn.classList.remove(\'bump\');void playBtn.offsetWidth;playBtn.classList.add(\'bump\')}\nfunction shakePlaySquare(){playBtn.classList.remove(\'shake\');void playBtn.offsetWidth;playBtn.classList.add(\'shake\')}\nfunction changeBet(delta){\n  var next=betAmount+delta;\n  if(next<BET_MIN||next>BET_MAX){shakePlaySquare();return;}\n  betAmount=next;renderBet();bumpPlaySquare();\n  if(navigator.vibrate){try{navigator.vibrate(7)}catch(e){}}\n}\nfunction bindHold(el,fn){\n  var delayT=null,repeatT=null;\n  function start(e){if(e.cancelable)e.preventDefault();fn();clearTimeout(delayT);clearInterval(repeatT);delayT=setTimeout(function(){repeatT=setInterval(fn,90)},380)}\n  function stop(){clearTimeout(delayT);clearInterval(repeatT)}\n  el.addEventListener(\'pointerdown\',start);\n  el.addEventListener(\'pointerup\',stop);\n  el.addEventListener(\'pointerleave\',stop);\n  el.addEventListener(\'pointercancel\',stop);\n}\nbindHold(betMinusBtn,function(){changeBet(-1)});\nbindHold(betPlusBtn,function(){changeBet(1)});\nrenderBet();\nsetJackpotHighlight(1);\nrefreshJackpotY();\n\n/* ===== TIER SELECT (AMATEUR x1.7 / CLUB x2.4 / PREMIER x3.4) ===== */\nvar tierSelectEl=document.getElementById(\'tier-select\');\nvar tierHandEl=document.getElementById(\'tier-hand\');\nvar tierBtns=Array.prototype.slice.call(document.querySelectorAll(\'.tier-btn\'));\nvar selectedTierBtn=tierBtns[0];\nfunction positionHandAt(btn){\n  if(!tierHandEl||!btn||!tierSelectEl)return;\n  var contRect=tierSelectEl.getBoundingClientRect();\n  var btnRect=btn.getBoundingClientRect();\n  var handW=tierHandEl.offsetWidth||22,handH=tierHandEl.offsetHeight||22;\n  var top=(btnRect.top-contRect.top)+(btnRect.height/2)-(handH/2);\n  var left=(btnRect.left-contRect.left)-handW-4;\n  tierHandEl.style.top=top+\'px\';\n  tierHandEl.style.left=left+\'px\';\n}\nfunction selectTier(btn){\n  selectedTierBtn=btn;\n  tierBtns.forEach(function(b){b.classList.remove(\'selected\')});\n  btn.classList.add(\'selected\');\n  winMultiplier=parseFloat(btn.getAttribute(\'data-mult\'))||1.7;\n  updateJackpotValues();\n  positionHandAt(btn);\n  if(navigator.vibrate){try{navigator.vibrate(10)}catch(e){}}\n}\ntierBtns.forEach(function(btn){btn.addEventListener(\'click\',function(){selectTier(btn)})});\nfunction showTierSelect(){\n  tierSelectEl.classList.remove(\'reveal\');\n  void tierSelectEl.offsetWidth;\n  tierSelectEl.classList.add(\'reveal\');\n  positionHandAt(selectedTierBtn);\n  setTimeout(function(){positionHandAt(selectedTierBtn)},900);\n}\nfunction lockTierSelect(){\n  tierSelectEl.classList.add(\'locked\');\n}\nfunction unlockTierSelect(){\n  var wasLocked=tierSelectEl.classList.contains(\'locked\');\n  tierSelectEl.classList.remove(\'locked\');\n  positionHandAt(selectedTierBtn);\n  if(wasLocked){\n    tierBtns.forEach(function(b){\n      b.classList.remove(\'reenable\');\n      void b.offsetWidth;\n      b.classList.add(\'reenable\');\n      setTimeout(function(){b.classList.remove(\'reenable\')},550);\n    });\n  }\n}\nwindow.addEventListener(\'resize\',function(){positionHandAt(selectedTierBtn)});\n\nfunction showBetControls(){\n  betControlsEl.classList.remove(\'exiting\');\n  betControlsEl.classList.remove(\'reveal\');\n  void betControlsEl.offsetWidth;\n  betControlsEl.classList.add(\'reveal\');\n  unlockTierSelect();\n}\nfunction hideBetControls(cb){\n  betControlsEl.classList.remove(\'reveal\');\n  betControlsEl.classList.add(\'exiting\');\n  lockTierSelect();\n  setTimeout(function(){betControlsEl.classList.remove(\'exiting\');if(cb)cb()},300);\n}\nfunction showShotControls(){\n  shotBtns.forEach(function(b){b.classList.remove(\'disabled\',\'pressed\')});\n  shotControlsEl.classList.remove(\'exiting\');\n  shotControlsEl.classList.remove(\'reveal\');\n  void shotControlsEl.offsetWidth;\n  shotControlsEl.classList.add(\'reveal\');\n}\nfunction hideShotControls(cb){\n  shotControlsEl.classList.remove(\'reveal\');\n  shotControlsEl.classList.add(\'exiting\');\n  setTimeout(function(){shotControlsEl.classList.remove(\'exiting\');if(cb)cb()},300);\n}\n/* ===== ROUND PLAN: mỗi ván random gán 3 kết quả cho 3 hướng =====\n   Luôn có đúng: 1 hướng VÀO LƯỚI (goal), 1 hướng bị THỦ MÔN BẮT (save), 1 hướng DỘI CỘT (post)\n   ROUND_PERMS liệt kê đủ 6 hoán vị có thể có của (goal,save,post) cho (left,mid,right).\n   Thứ tự trong mảng này phải khớp CHÍNH XÁC với PERMS trong tool.py để giải mã đúng. */\nvar roundPlan=null;\nvar ROUND_PERMS=[\n  [\'goal\',\'save\',\'post\'],\n  [\'goal\',\'post\',\'save\'],\n  [\'save\',\'goal\',\'post\'],\n  [\'save\',\'post\',\'goal\'],\n  [\'post\',\'goal\',\'save\'],\n  [\'post\',\'save\',\'goal\']\n];\nvar currentPermIndex=0;\nfunction planRound(){\n  var dirs=[\'left\',\'mid\',\'right\'];\n  currentPermIndex=Math.floor(Math.random()*ROUND_PERMS.length);\n  var outs=ROUND_PERMS[currentPermIndex];\n  roundPlan={};\n  dirs.forEach(function(d,i){roundPlan[d]=outs[i]});\n  return currentPermIndex;\n}\n\n/* ===== CASH OUT (rút tiền giữa chừng, tối đa 9 lượt sút mỗi phiên) ===== */\nvar cashoutBarEl=document.getElementById(\'cashout-bar\');\nvar cashoutBtn=document.getElementById(\'cashoutBtn\');\nvar cashoutAmountEl=document.getElementById(\'cashoutAmount\');\nvar inSession=false,sessionStake=0;\nfunction sessionAmount(level){return level<=0?sessionStake:Math.round(sessionStake*winMultiplier*Math.pow(2,level-1)*100)/100}\nfunction renderCashoutAmount(animate){\n  var val=sessionAmount(winStreak);\n  cashoutAmountEl.textContent=jpFormat(val);\n  if(animate){cashoutAmountEl.classList.remove(\'co-rolling\');void cashoutAmountEl.offsetWidth;cashoutAmountEl.classList.add(\'co-rolling\')}\n}\nfunction showCashoutBar(){\n  renderCashoutAmount(false);\n  cashoutBtn.classList.remove(\'disabled\');\n  cashoutBtn.classList.remove(\'unlocked\');\n  cashoutBarEl.classList.remove(\'exiting\');\n  cashoutBarEl.classList.remove(\'reveal\');\n  void cashoutBarEl.offsetWidth;\n  cashoutBarEl.classList.add(\'reveal\');\n}\nfunction hideCashoutBar(cb){\n  cashoutBarEl.classList.remove(\'reveal\');\n  cashoutBarEl.classList.add(\'exiting\');\n  setTimeout(function(){cashoutBarEl.classList.remove(\'exiting\');if(cb)cb()},300);\n}\nfunction unlockCashout(){\n  renderCashoutAmount(true);\n  cashoutBtn.classList.remove(\'disabled\');\n  cashoutBtn.classList.remove(\'unlocked\');\n  void cashoutBtn.offsetWidth;\n  cashoutBtn.classList.add(\'unlocked\');\n}\nfunction lockCashout(){cashoutBtn.classList.add(\'disabled\')}\nfunction spawnCoinFly(fromEl,toEl,count,onDone){\n  var fr=fromEl.getBoundingClientRect(),tr=toEl.getBoundingClientRect();\n  var fx=fr.left+fr.width/2,fy=fr.top+fr.height/2,tx=tr.left+tr.width/2,ty=tr.top+tr.height/2;\n  var done=0;\n  for(var i=0;i<count;i++){\n    (function(i){\n      var el=document.createElement(\'div\');\n      el.style.cssText=\'position:absolute;z-index:75;width:14px;height:14px;border-radius:50%;pointer-events:none;background:radial-gradient(circle at 34% 26%,#ffe66d,#c99a00 72%);box-shadow:0 1px 3px rgba(0,0,0,.5),inset 0 1px 1px rgba(255,255,255,.6)\';\n      var jitter=(Math.random()*40-20);\n      el.style.left=(fx-7+jitter)+\'px\';el.style.top=(fy-7)+\'px\';\n      document.body.appendChild(el);\n      setTimeout(function(){\n        var midX=(fx+tx)/2+(Math.random()*70-35),midY=Math.min(fy,ty)-70-Math.random()*50;\n        var anim=el.animate([\n          {transform:\'translate(0,0) scale(1) rotate(0deg)\',opacity:1,offset:0},\n          {transform:\'translate(\'+(midX-fx)+\'px,\'+(midY-fy)+\'px) scale(1.15) rotate(180deg)\',opacity:1,offset:.55},\n          {transform:\'translate(\'+(tx-fx)+\'px,\'+(ty-fy)+\'px) scale(.25) rotate(320deg)\',opacity:0,offset:1}\n        ],{duration:640,easing:\'cubic-bezier(.3,.6,.2,1)\'});\n        anim.onfinish=function(){el.remove();done++;if(done>=count&&onDone)onDone()};\n      },i*40);\n    })(i);\n  }\n}\nfunction endSession(){\n  inSession=false;sessionStake=0;\n  winStreak=0;setJackpotHighlight(1);\n  hideShotControls(function(){});\n  hideCashoutBar(function(){showBetControls()});\n}\nfunction doCashOut(){\n  if(!inSession||isShooting)return;\n  var amount=sessionAmount(winStreak);\n  inSession=false;\n  disableButtons();\n  lockCashout();\n  lockTierSelect();\n  if(navigator.vibrate){try{navigator.vibrate([25,20,25,20,50])}catch(e){}}\n  spawnCoinFly(cashoutBtn,balanceDisplayEl,12,function(){addBalance(amount)});\n  setTimeout(function(){endSession()},700);\n}\ncashoutBtn.addEventListener(\'click\',function(e){e.stopPropagation();doCashOut()});\n\nplayBtn.addEventListener(\'click\',function(){\n  if(isShooting)return;\n  if(playerBalance<betAmount){\n    shakePlaySquare();\n    if(navigator.vibrate){try{navigator.vibrate([15,40,15])}catch(e){}}\n    return;\n  }\n  addBalance(-betAmount);\n  sessionStake=betAmount;\n  inSession=true;\n  winStreak=0;setJackpotHighlight(1);\n  var permIndex=planRound();\n  hideBetControls(function(){showShotControls();showCashoutBar()});\n});\n\n/* ===== CANVAS ===== */\nvar canvas=document.getElementById(\'gameCanvas\'),ctx=canvas.getContext(\'2d\'),gameActive=false;\nfunction resizeCanvas(){var d=window.devicePixelRatio||1;canvas.width=window.innerWidth*d;canvas.height=window.innerHeight*d;canvas.style.width=window.innerWidth+\'px\';canvas.style.height=window.innerHeight+\'px\';ctx.setTransform(d,0,0,d,0,0)}\nwindow.addEventListener(\'resize\',function(){resizeCanvas();refreshJackpotY()});\n\n/* ===== PALETTE ===== */\nvar C={outline:\'#141414\',skin:\'#f2c199\',skinSh:\'#d9a678\',hair:\'#3b2415\',jersey:\'#f6cf00\',jerseySh:\'#d9a600\',collar:\'#b8860b\',shorts:\'#1c1c1c\',sockW:\'#f2f2f2\',sockSh:\'#d5d5d5\',boot:\'#161616\',lace:\'#eeeeee\',glove:\'#ff7518\',gloveSh:\'#cc5a10\',white:\'#ffffff\',mouth:\'#c98a68\',eye:\'#181818\'};\nvar GRID_W=24,GRID_H=32;\n\n/* ===== PIXEL ART DATA ===== */\nvar baseParts=[\n  {x:8,y:1,w:8,h:3,c:C.hair},{x:8,y:4,w:1,h:2,c:C.hair},{x:15,y:4,w:1,h:2,c:C.hair},{x:9,y:3,w:6,h:6,c:C.skin},{x:11,y:8,w:2,h:1,c:C.skin},\n  {x:7,y:9,w:10,h:8,c:C.jersey},\n  {x:3,y:11,w:4,h:4,c:C.jersey},{x:17,y:11,w:4,h:4,c:C.jersey},\n  {x:3,y:8,w:4,h:4,c:C.skin},{x:17,y:8,w:4,h:4,c:C.skin},\n  {x:2,y:6,w:5,h:3,c:C.glove},{x:17,y:6,w:5,h:3,c:C.glove},\n  {x:7,y:17,w:10,h:4,c:C.shorts},\n  {x:8,y:21,w:3,h:6,c:C.sockW},{x:13,y:21,w:3,h:6,c:C.sockW},\n  {x:7,y:27,w:5,h:3,c:C.boot},{x:12,y:27,w:5,h:3,c:C.boot}\n];\nvar detailParts=[\n  {x:14,y:9,w:3,h:8,c:C.jerseySh},{x:10,y:9,w:4,h:1,c:C.collar},{x:11,y:11,w:1,h:4,c:C.white},{x:10,y:11,w:1,h:1,c:C.white},{x:10,y:15,w:3,h:1,c:C.white},{x:7,y:17,w:10,h:1,c:\'#2b2b2b\'},\n  {x:2,y:8,w:5,h:1,c:C.gloveSh},{x:17,y:8,w:5,h:1,c:C.gloveSh},{x:4,y:6,w:1,h:2,c:C.gloveSh},{x:6,y:6,w:1,h:2,c:C.gloveSh},{x:19,y:6,w:1,h:2,c:C.gloveSh},{x:21,y:6,w:1,h:2,c:C.gloveSh},\n  {x:10,y:21,w:1,h:6,c:C.sockSh},{x:15,y:21,w:1,h:6,c:C.sockSh},{x:8,y:28,w:3,h:1,c:C.lace},{x:13,y:28,w:3,h:1,c:C.lace},\n  {x:10,y:5,w:1,h:1,c:C.eye},{x:13,y:5,w:1,h:1,c:C.eye},{x:11,y:7,w:2,h:1,c:C.mouth},{x:9,y:6,w:1,h:2,c:C.skinSh},{x:14,y:6,w:1,h:2,c:C.skinSh}\n];\nvar BODY_IDX=[0,1,2,3,4,5,12,13,14,15,16];\nvar ARM_IDX=[6,7,8,9,10,11];\nvar BODY_DET_IDX=[0,1,2,3,4,5,12,13,14,15];\nvar ARM_DET_IDX=[6,7,8,9,10,11];\nvar EYE_IDX=[16,17];\n\n/* ===== EASING ===== */\nfunction easeOutCubic(t){return 1-Math.pow(1-t,3)}\nfunction easeOutQuart(t){return 1-Math.pow(1-t,4)}\nfunction easeInCubic(t){return t*t*t}\nfunction easeInOutCubic(t){return t<.5?4*t*t*t:1-Math.pow(-2*t+2,3)/2}\nfunction easeOutBack(t){var c1=1.70158,c3=c1+1;return 1+c3*Math.pow(t-1,3)+c1*Math.pow(t-1,2)}\nfunction lerp(a,b,t){return a+(b-a)*t}\n\n/* ===== GOALKEEPER ===== */\nvar GK={\n  state:\'idle\',stateTime:0,stateDur:0,\n  pose:\'idle\',prevPose:\'idle\',poseT:0,poseDur:200,\n  screenX:0,screenY:0,\n  targetScreenX:0,targetScreenY:0,\n  diveDir:null,diveDist:0,diveArc:0,\n  diveProgress:0,\n  setPose:function(name,dur){this.prevPose=this.pose;this.pose=name;this.poseT=0;this.poseDur=dur||200},\n  setState:function(state,dur){this.state=state;this.stateTime=0;this.stateDur=dur},\n  anticipate:function(predictedDir){\n    this.setState(\'anticipate\',450);\n    this.setPose(\'anticipate\',250);\n    this.targetScreenX=0;this.targetScreenY=0;\n  },\n  dive:function(dir,goalInfo){\n    this.diveDir=dir;\n    this.setState(\'dive\',750);\n    this.diveProgress=0;\n    if(dir===\'left\'){\n      this.diveDist=goalInfo.gw*0.30;\n      this.diveArc=goalInfo.gh*0.22;\n      this.setPose(\'diveLeft\',300);\n    }else if(dir===\'right\'){\n      this.diveDist=goalInfo.gw*0.30;\n      this.diveArc=goalInfo.gh*0.22;\n      this.setPose(\'diveRight\',300);\n    }else{\n      this.diveDist=0;\n      this.diveArc=goalInfo.gh*0.15;\n      this.setPose(\'diveCenter\',300);\n    }\n  },\n  hold:function(){this.setState(\'hold\',1100);this.setPose(\'catch\',200)},\n  miss:function(){this.setState(\'dejected\',1000);this.setPose(\'dejected\',350)},\n  recover:function(){\n    this.recoverFromX=this.screenX;this.recoverFromY=this.screenY;\n    this.setState(\'recover\',650);this.setPose(\'idle\',450);\n    this.targetScreenX=0;this.targetScreenY=0;\n  },\n  update:function(dt){\n    this.stateTime+=dt;\n    this.poseT+=dt;\n    if(this.state===\'dive\'){\n      this.diveProgress=Math.min(this.stateTime/this.stateDur,1);\n      var t=easeOutCubic(this.diveProgress);\n      var dirSign=this.diveDir===\'left\'?-1:(this.diveDir===\'right\'?1:0);\n      this.screenX=dirSign*this.diveDist*t;\n      this.screenY=-this.diveArc*Math.sin(t*Math.PI);\n    }else if(this.state===\'recover\'){\n      var rt=Math.min(this.stateTime/this.stateDur,1);\n      var re=easeOutBack(rt);\n      this.screenX=lerp(this.recoverFromX,0,re);\n      this.screenY=lerp(this.recoverFromY,0,re);\n    }else if(this.state===\'hold\'||this.state===\'dejected\'){\n    }else{\n      this.screenX+=(this.targetScreenX-this.screenX)*Math.min(dt*0.006,1);\n      this.screenY+=(this.targetScreenY-this.screenY)*Math.min(dt*0.006,1);\n    }\n    if(this.stateDur>0&&this.stateTime>=this.stateDur){\n      if(this.state===\'anticipate\'){}\n      else if(this.state===\'dive\'){\n        if(BALL.outcome===\'save\')this.hold();\n        else this.miss();\n      }\n      else if(this.state===\'hold\'||this.state===\'dejected\'){this.recover()}\n      else if(this.state===\'recover\'){this.screenX=0;this.screenY=0;this.setState(\'idle\',0);this.setPose(\'idle\',100)}\n    }\n  },\n  getPoseOffsets:function(){\n    var t=Math.min(this.poseT/this.poseDur,1);\n    var e=easeOutCubic(t);\n    var prev=POSES[this.prevPose]||POSES.idle;\n    var next=POSES[this.pose]||POSES.idle;\n    return{\n      bodyDx:lerp(prev.bodyDx,next.bodyDx,e),\n      bodyDy:lerp(prev.bodyDy,next.bodyDy,e),\n      armDx:lerp(prev.armDx,next.armDx,e),\n      armDy:lerp(prev.armDy,next.armDy,e)\n    };\n  },\n  draw:function(originX,originY,px,t){\n    var blinkPhase=t%3600,blinking=blinkPhase<120;\n    var off=this.getPoseOffsets();\n    var rx=originX+this.screenX;\n    var ry=originY+this.screenY;\n    ctx.save();\n    ctx.translate(rx,ry);\n    ctx.scale(px,px);\n    ctx.fillStyle=\'rgba(0,0,0,0.35)\';\n    ctx.beginPath();\n    ctx.ellipse(GRID_W/2,GRID_H-0.5-(this.screenY/px),7.5,1.6,0,0,Math.PI*2);\n    ctx.fill();\n    var bdx=off.bodyDx,bdy=off.bodyDy;\n    ctx.fillStyle=C.outline;\n    BODY_IDX.forEach(function(i){var p=baseParts[i];ctx.fillRect(p.x+bdx-1,p.y+bdy-1,p.w+2,p.h+2)});\n    BODY_IDX.forEach(function(i){var p=baseParts[i];ctx.fillStyle=p.c;ctx.fillRect(p.x+bdx,p.y+bdy,p.w,p.h)});\n    BODY_DET_IDX.forEach(function(i){var p=detailParts[i];ctx.fillStyle=p.c;ctx.fillRect(p.x+bdx,p.y+bdy,p.w,p.h)});\n    var adx=off.bodyDx+off.armDx,ady=off.bodyDy+off.armDy;\n    ctx.fillStyle=C.outline;\n    ARM_IDX.forEach(function(i){var p=baseParts[i];ctx.fillRect(p.x+adx-1,p.y+ady-1,p.w+2,p.h+2)});\n    ARM_IDX.forEach(function(i){var p=baseParts[i];ctx.fillStyle=p.c;ctx.fillRect(p.x+adx,p.y+ady,p.w,p.h)});\n    ARM_DET_IDX.forEach(function(i){var p=detailParts[i];ctx.fillStyle=p.c;ctx.fillRect(p.x+adx,p.y+ady,p.w,p.h)});\n    EYE_IDX.forEach(function(i){var p=detailParts[i];ctx.fillStyle=blinking?C.skin:p.c;ctx.fillRect(p.x+bdx,p.y+bdy,p.w,p.h)});\n    ctx.restore();\n  },\n  getGlovePos:function(originX,originY,px){\n    var off=this.getPoseOffsets();\n    var adx=off.bodyDx+off.armDx,ady=off.bodyDy+off.armDy;\n    var gx=originX+this.screenX+(12+adx)*px;\n    var gy=originY+this.screenY+(7+ady)*px;\n    return{x:gx,y:gy};\n  }\n};\n\n/* ===== POSES ===== */\nvar POSES={\n  idle:      {bodyDx:0,bodyDy:0,armDx:0,armDy:0},\n  anticipate:{bodyDx:0,bodyDy:1,armDx:0,armDy:0},\n  diveLeft:  {bodyDx:0,bodyDy:0,armDx:0,armDy:-5},\n  diveRight: {bodyDx:0,bodyDy:0,armDx:0,armDy:-5},\n  diveCenter:{bodyDx:0,bodyDy:1,armDx:0,armDy:-5},\n  catch:     {bodyDx:0,bodyDy:0,armDx:0,armDy:-5},\n  dejected:  {bodyDx:0,bodyDy:2,armDx:0,armDy:2}\n};\n\n/* ===== BALL ===== */\nvar BALL_FLY_SAVE=700,BALL_FLY_GOAL=900,BALL_FLY_POST=520;\nvar BALL_BOUNCE_DUR=1150,BALL_POST_DUR=680,BALL_SETTLE_PAUSE=280,BALL_RETURN_DUR=850;\nfunction easeOutElastic(t){var c4=(2*Math.PI)/3.2;return t===0?0:t===1?1:Math.pow(2,-8*t)*Math.sin((t*8-0.75)*c4)+1}\nvar BALL={\n  state:\'idle\',time:0,\n  startX:0,startY:0,targetX:0,targetY:0,\n  catchX:0,catchY:0,\n  postX:0,postY:0,\n  deflectX:0,deflectY:0,\n  bounceBaseX:0,bounceBaseY:0,rollX:0,\n  returnFromX:0,returnFromY:0,\n  direction:null,predictedDir:null,outcome:null,result:null,\n  rotation:0,scale:1,trail:[],spinSpeed:0.012,\n  reset:function(x,y){\n    this.state=\'idle\';this.startX=x;this.startY=y;\n    this.rotation=0;this.scale=1;this.trail=[];\n    this.outcome=null;this.result=null;this.direction=null;this.predictedDir=null;\n  },\n  startSpin:function(dir){\n    this.state=\'spin\';this.time=0;this.direction=dir;\n    this.outcome=(roundPlan&&roundPlan[dir])||\'goal\';\n    this.result=this.outcome===\'save\'?\'saved\':(this.outcome===\'post\'?\'post\':\'goal\');\n    if(this.outcome===\'save\'){\n      this.predictedDir=dir;\n    }else{\n      var o=[\'left\',\'mid\',\'right\'].filter(function(d){return d!==dir});\n      this.predictedDir=o[Math.floor(Math.random()*o.length)];\n    }\n  },\n  update:function(dt,goalInfo){\n    this.time+=dt;\n    if(this.state===\'spin\'){\n      var t=Math.min(this.time/400,1);\n      this.rotation=t*Math.PI*2;\n      this.scale=1+Math.sin(t*Math.PI)*0.12;\n      if(t>=1){\n        this.state=\'fly\';this.time=0;\n        if(this.outcome===\'save\'){\n          this.targetX=goalInfo.targets[this.direction].x;\n          this.targetY=goalInfo.targets[this.direction].y;\n          var ce=easeOutQuart(0.62);\n          this.catchX=lerp(this.startX,this.targetX,ce);\n          this.catchY=lerp(this.startY,this.targetY,ce)+Math.sin(ce*Math.PI)*-55;\n        }else if(this.outcome===\'post\'){\n          var pp=goalInfo.postPoints[this.direction];\n          this.postX=pp.x;this.postY=pp.y;\n        }else{\n          this.targetX=goalInfo.targets[this.direction].x;\n          this.targetY=goalInfo.targets[this.direction].y;\n        }\n        GK.anticipate(this.predictedDir);\n      }\n    }\n    else if(this.state===\'fly\'){\n      var dur=this.outcome===\'save\'?BALL_FLY_SAVE:(this.outcome===\'post\'?BALL_FLY_POST:BALL_FLY_GOAL);\n      var t2=Math.min(this.time/dur,1);\n      var e=easeOutQuart(t2);\n      this.scale=1-e*0.35;\n      this.rotation+=dt*this.spinSpeed;\n      var pos=this.getPos();\n      if(pos&&Math.random()>0.4)this.trail.push({x:pos.x,y:pos.y,s:this.scale,life:1});\n      for(var i=this.trail.length-1;i>=0;i--){this.trail[i].life-=dt*0.003;if(this.trail[i].life<=0)this.trail.splice(i,1)}\n      if(t2>=0.15&&GK.state===\'anticipate\'){GK.dive(this.predictedDir,goalInfo)}\n      if(t2>=1){\n        if(this.outcome===\'save\'){\n          this.state=\'held\';this.time=0;\n        }else if(this.outcome===\'post\'){\n          this.state=\'postImpact\';this.time=0;\n          var dx=this.postX-goalInfo.gx-goalInfo.gw/2;\n          var side=this.direction===\'mid\'?(Math.random()<0.5?-1:1):(dx<0?-1:1);\n          if(this.direction===\'mid\'){\n            this.deflectX=this.postX+side*goalInfo.gw*0.55;\n            this.deflectY=this.postY-goalInfo.gh*0.85;\n          }else{\n            this.deflectX=this.postX+side*goalInfo.gw*0.62;\n            this.deflectY=this.postY+goalInfo.gh*0.30;\n          }\n          this.spinSpeed=0.03;\n          spawnPostFlash(this.postX,this.postY);\n        }else{\n          this.state=\'bounceGoal\';this.time=0;\n          this.bounceBaseX=this.targetX;this.bounceBaseY=this.targetY;\n          this.rollX=this.targetX+(Math.random()*2-1)*goalInfo.gw*0.10;\n          NET.triggerImpact(this.targetX,this.targetY);\n        }\n      }\n    }\n    else if(this.state===\'held\'){\n      for(var i=this.trail.length-1;i>=0;i--){this.trail[i].life-=dt*0.006;if(this.trail[i].life<=0)this.trail.splice(i,1)}\n      if(GK.state===\'idle\'){\n        var gp=GK.getGlovePos(goalInfo.originX,goalInfo.originY,goalInfo.px);\n        this.returnFromX=gp.x;this.returnFromY=gp.y;\n        this.startReturn();\n      }\n    }\n    else if(this.state===\'bounceGoal\'){\n      var bt=Math.min(this.time/BALL_BOUNCE_DUR,1);\n      this.rotation+=dt*0.018;\n      if(pos_trailTick(this,dt,0.5))this.trail.push({x:this.getPos().x,y:this.getPos().y,s:this.scale,life:1});\n      trimTrail(this,dt*0.0032);\n      if(bt>=1){\n        this.state=\'idle_pause\';this.time=0;\n        this.returnFromX=this.bounceGroundX;this.returnFromY=this.bounceGroundY;\n      }\n    }\n    else if(this.state===\'postImpact\'){\n      var pt=Math.min(this.time/BALL_POST_DUR,1);\n      this.rotation+=dt*this.spinSpeed;\n      this.scale=Math.max(0.15,this.scale-dt*0.0009);\n      if(pos_trailTick(this,dt,0.35))this.trail.push({x:this.getPos().x,y:this.getPos().y,s:this.scale,life:1});\n      trimTrail(this,dt*0.0035);\n      if(pt>=1){\n        this.state=\'idle_pause\';this.time=0;\n        this.returnFromX=this.deflectX;this.returnFromY=this.deflectY;\n      }\n    }\n    else if(this.state===\'idle_pause\'){\n      trimTrail(this,dt*0.004);\n      if(this.time>=BALL_SETTLE_PAUSE)this.startReturn();\n    }\n    else if(this.state===\'returning\'){\n      var rdur=BALL_RETURN_DUR,rt=Math.min(this.time/rdur,1);\n      var re=easeInOutCubic(rt);\n      this.rotation+=dt*0.01;\n      this.scale=0.55+re*0.45;\n      var rp=this.getPos();\n      if(rp&&Math.random()>0.5)this.trail.push({x:rp.x,y:rp.y,s:this.scale,life:1});\n      trimTrail(this,dt*0.003);\n      if(rt>=1){this.state=\'idle\';this.trail=[];this.rotation=0;this.scale=1}\n    }\n  },\n  startReturn:function(){\n    this.state=\'returning\';this.time=0;\n  },\n  getPos:function(){\n    if(this.state===\'idle\'||this.state===\'spin\')return{x:this.startX,y:this.startY};\n    if(this.state===\'fly\'){\n      if(this.outcome===\'save\'){\n        var dur=BALL_FLY_SAVE,t=Math.min(this.time/dur,1),e=easeOutQuart(t);\n        return{x:lerp(this.startX,this.catchX,e),y:lerp(this.startY,this.catchY,e)};\n      }else if(this.outcome===\'post\'){\n        var dur3=BALL_FLY_POST,t3=Math.min(this.time/dur3,1),e3=easeOutQuart(t3);\n        var x3=lerp(this.startX,this.postX,e3),y3=lerp(this.startY,this.postY,e3)+Math.sin(e3*Math.PI)*-45;\n        return{x:x3,y:y3};\n      }else{\n        var dur2=BALL_FLY_GOAL,t2=Math.min(this.time/dur2,1),e2=easeOutQuart(t2);\n        var x2=lerp(this.startX,this.targetX,e2),by2=lerp(this.startY,this.targetY,e2);\n        var arc=Math.sin(e2*Math.PI)*-55;\n        return{x:x2,y:by2+arc};\n      }\n    }\n    if(this.state===\'held\')return null;\n    if(this.state===\'bounceGoal\'){\n      var bt=Math.min(this.time/BALL_BOUNCE_DUR,1);\n      var floorY=this.bounceBaseY+90;\n      var rollT=easeOutCubic(bt);\n      var x=lerp(this.bounceBaseX,this.rollX,rollT);\n      var bounces=3,amp0=60;\n      var phase=bt*bounces;\n      var bounceIdx=Math.min(Math.floor(phase),bounces-1);\n      var localT=phase-bounceIdx;\n      var amp=amp0*Math.pow(0.42,bounceIdx);\n      var arcY=-Math.sin(localT*Math.PI)*amp;\n      var fall=lerp(this.bounceBaseY,floorY,easeOutCubic(Math.min(bt*1.4,1)));\n      var y=fall+arcY;\n      this.bounceGroundX=x;this.bounceGroundY=floorY;\n      this.scale=0.55+bt*0.55;\n      return{x:x,y:y};\n    }\n    if(this.state===\'postImpact\'){\n      var pt=Math.min(this.time/BALL_POST_DUR,1),pe=easeOutCubic(pt);\n      var arc=-Math.sin(pt*Math.PI)*40;\n      return{x:lerp(this.postX,this.deflectX,pe),y:lerp(this.postY,this.deflectY,pe)+arc};\n    }\n    if(this.state===\'idle_pause\'){\n      if(this.outcome===\'post\')return{x:this.deflectX,y:this.deflectY};\n      return{x:this.bounceGroundX,y:this.bounceGroundY};\n    }\n    if(this.state===\'returning\'){\n      var rdur=BALL_RETURN_DUR,rt=Math.min(this.time/rdur,1),re=easeInOutCubic(rt);\n      var rx=lerp(this.returnFromX,this.startX,re);\n      var ry=lerp(this.returnFromY,this.startY,re);\n      var rarc=Math.sin(re*Math.PI)*-70;\n      return{x:rx,y:ry+rarc};\n    }\n    return{x:this.startX,y:this.startY};\n  }\n};\nfunction pos_trailTick(ball,dt,chance){return Math.random()>(1-chance)}\nfunction trimTrail(ball,decay){for(var i=ball.trail.length-1;i>=0;i--){ball.trail[i].life-=decay;if(ball.trail[i].life<=0)ball.trail.splice(i,1)}}\nfunction spawnPostFlash(x,y){POST_FX.push({x:x,y:y,time:0})}\nvar POST_FX=[];\n\n/* ===== NET PHYSICS ===== */\nvar NET={\n  impacts:[],\n  triggerImpact:function(x,y){this.impacts.push({x:x,y:y,time:0,str:1})},\n  update:function(dt){for(var i=this.impacts.length-1;i>=0;i--){this.impacts[i].time+=dt;this.impacts[i].str*=0.988;if(this.impacts[i].str<0.01)this.impacts.splice(i,1)}},\n  getOffset:function(x,y,t){\n    var dx=0,dy=0;\n    for(var i=0;i<this.impacts.length;i++){\n      var imp=this.impacts[i];var ddx=x-imp.x,ddy=y-imp.y;\n      var dist=Math.sqrt(ddx*ddx+ddy*ddy);\n      var waveR=imp.time*0.35;var dw=Math.abs(dist-waveR);\n      if(dw<50){var amp=imp.str*(1-dw/50)*Math.sin(imp.time*0.025)*4;dx+=(ddx/Math.max(dist,0.1))*amp;dy+=(ddy/Math.max(dist,0.1))*amp}\n    }\n    dy+=Math.sin(t*0.001+x*0.02)*0.3;\n    return{dx:dx,dy:dy};\n  }\n};\n\n/* ===== DRAW HELPERS ===== */\nfunction lerpPt(a,b,t){return{x:a.x+(b.x-a.x)*t,y:a.y+(b.y-a.y)*t}}\nfunction lerpA(a,b,t){return a+(b-a)*t}\nfunction fillNetQuad(p00,p10,p11,p01,c1,c2){ctx.save();ctx.beginPath();ctx.moveTo(p00.x,p00.y);ctx.lineTo(p10.x,p10.y);ctx.lineTo(p11.x,p11.y);ctx.lineTo(p01.x,p01.y);ctx.closePath();ctx.clip();var g=ctx.createLinearGradient(p00.x,p00.y,p01.x,p01.y);g.addColorStop(0,c1);g.addColorStop(1,c2);ctx.fillStyle=g;var mx=Math.min(p00.x,p10.x,p11.x,p01.x),Mx=Math.max(p00.x,p10.x,p11.x,p01.x),my=Math.min(p00.y,p10.y,p11.y,p01.y),My=Math.max(p00.y,p10.y,p11.y,p01.y);ctx.fillRect(mx-2,my-2,Mx-mx+4,My-my+4);ctx.restore()}\nfunction drawMeshQuad(p00,p10,p11,p01,cols,rows,a00,a10,a11,a01,sagFn,t){\n  var i,j,u,v;\n  for(i=0;i<=cols;i++){u=i/cols;var top=lerpPt(p00,p10,u),bot=lerpPt(p01,p11,u);var to=NET.getOffset(top.x,top.y,t),bo=NET.getOffset(bot.x,bot.y,t);var aA=(lerpA(a00,a10,u)+lerpA(a01,a11,u))/2;ctx.strokeStyle=\'rgba(240,240,240,\'+aA.toFixed(3)+\')\';ctx.lineWidth=1;ctx.beginPath();ctx.moveTo(top.x+to.dx,top.y+to.dy);ctx.lineTo(bot.x+bo.dx,bot.y+bo.dy);ctx.stroke()}\n  for(j=0;j<=rows;j++){v=j/rows;var left=lerpPt(p00,p01,v),right=lerpPt(p10,p11,v);var lo=NET.getOffset(left.x,left.y,t),ro=NET.getOffset(right.x,right.y,t);var aA2=(lerpA(a00,a01,v)+lerpA(a10,a11,v))/2;ctx.strokeStyle=\'rgba(240,240,240,\'+aA2.toFixed(3)+\')\';ctx.beginPath();if(sagFn){var sag=sagFn(v);var mx=(left.x+right.x)/2,myy=(left.y+right.y)/2+sag;var mo=NET.getOffset(mx,myy,t);ctx.moveTo(left.x+lo.dx,left.y+lo.dy);ctx.quadraticCurveTo(mx+mo.dx,myy+mo.dy,right.x+ro.dx,right.y+ro.dy)}else{ctx.moveTo(left.x+lo.dx,left.y+lo.dy);ctx.lineTo(right.x+ro.dx,right.y+ro.dy)}ctx.stroke()}\n}\nfunction drawFootball(cx,cy,r,rot){\n  ctx.save();ctx.fillStyle=\'rgba(0,0,0,0.38)\';ctx.beginPath();ctx.ellipse(cx,cy+r*0.95,r*1.25,r*0.36,0,0,Math.PI*2);ctx.fill();ctx.restore();\n  ctx.save();ctx.translate(cx,cy);\n  var body=ctx.createRadialGradient(-r*0.35,-r*0.4,r*0.1,0,0,r*1.05);body.addColorStop(0,\'#ffffff\');body.addColorStop(0.55,\'#f0f0f0\');body.addColorStop(1,\'#c9c9c9\');\n  ctx.beginPath();ctx.arc(0,0,r,0,Math.PI*2);ctx.fillStyle=body;ctx.fill();\n  ctx.save();ctx.beginPath();ctx.arc(0,0,r,0,Math.PI*2);ctx.clip();ctx.rotate(rot||0);ctx.fillStyle=\'#161616\';\n  function pent(px,py,s,rt){ctx.beginPath();for(var i=0;i<5;i++){var a=rt+i*(Math.PI*2/5)-Math.PI/2;var x=px+Math.cos(a)*s,y=py+Math.sin(a)*s;if(i===0)ctx.moveTo(x,y);else ctx.lineTo(x,y)}ctx.closePath();ctx.fill()}\n  pent(0,-r*0.06,r*0.36,0.05);pent(-r*0.66,-r*0.34,r*0.24,0.35);pent(r*0.64,-r*0.32,r*0.24,-0.35);pent(-r*0.42,r*0.52,r*0.22,0.95);pent(r*0.46,r*0.50,r*0.22,-0.95);pent(0,r*0.86,r*0.20,0);\n  ctx.strokeStyle=\'rgba(0,0,0,0.45)\';ctx.lineWidth=Math.max(0.6,r*0.045);ctx.beginPath();ctx.moveTo(-r*0.66,-r*0.08);ctx.quadraticCurveTo(0,r*0.18,r*0.64,-r*0.06);ctx.stroke();ctx.restore();\n  ctx.lineWidth=Math.max(0.6,r*0.035);ctx.strokeStyle=\'rgba(0,0,0,0.22)\';ctx.beginPath();ctx.arc(0,0,r,0,Math.PI*2);ctx.stroke();\n  var hl=ctx.createRadialGradient(-r*0.42,-r*0.46,0,-r*0.42,-r*0.46,r*0.7);hl.addColorStop(0,\'rgba(255,255,255,0.9)\');hl.addColorStop(1,\'rgba(255,255,255,0)\');ctx.beginPath();ctx.arc(0,0,r,0,Math.PI*2);ctx.fillStyle=hl;ctx.fill();\n  var sh=ctx.createRadialGradient(r*0.4,r*0.45,0,r*0.4,r*0.45,r*0.95);sh.addColorStop(0,\'rgba(0,0,0,0.30)\');sh.addColorStop(1,\'rgba(0,0,0,0)\');ctx.beginPath();ctx.arc(0,0,r,0,Math.PI*2);ctx.fillStyle=sh;ctx.fill();\n  ctx.restore();\n}\nvar _crowdCache=null;\nfunction drawCrowdPerson(cx,x,y,scale,shirt,skin,hair,blur,rnd){\n  var lean=(rnd()-0.5)*1.4;\n  cx.save();cx.translate(x,y);cx.rotate(lean*0.04);cx.scale(scale,scale);\n  if(blur)cx.filter=\'blur(0.6px)\';\n  cx.beginPath();cx.moveTo(-4.4,6);cx.quadraticCurveTo(-4.8,0.5,-2.6,-0.5);cx.quadraticCurveTo(0,-1.5,2.6,-0.5);cx.quadraticCurveTo(4.8,0.5,4.4,6);cx.closePath();cx.fillStyle=shirt;cx.fill();\n  cx.beginPath();cx.ellipse(0,3.4,3.4,2.2,0,0,Math.PI*2);cx.fillStyle=\'rgba(0,0,0,0.18)\';cx.fill();\n  cx.beginPath();cx.ellipse(0,-1.6,1.3,1,0,0,Math.PI*2);cx.fillStyle=skin;cx.fill();\n  cx.beginPath();cx.ellipse(0,-3.6,2.5,2.7,0,0,Math.PI*2);cx.fillStyle=skin;cx.fill();\n  cx.beginPath();cx.ellipse(0,-4.6,2.6,1.9,0,Math.PI,Math.PI*2);cx.fillStyle=hair;cx.fill();\n  cx.filter=\'none\';cx.restore();\n}\nfunction renderCrowdCanvas(w,h){\n  var c=document.createElement(\'canvas\');c.width=w;c.height=h;var cx=c.getContext(\'2d\');\n  var seed=42;function rnd(){seed=(seed*9301+49297)%233280;return seed/233280}function pick(a){return a[Math.floor(rnd()*a.length)]}\n  var shirts=[\'#c1272d\',\'#e2b13c\',\'#1c4f8a\',\'#2e7d32\',\'#f5f5f5\',\'#b71c1c\',\'#0d47a1\',\'#ffb300\',\'#4a148c\',\'#37474f\',\'#d84315\',\'#546e7a\',\'#8e0000\',\'#003366\',\'#eeeeee\',\'#7cb342\',\'#5d4037\',\'#212121\'];\n  var skins=[\'#f1c27d\',\'#e0ac69\',\'#c68642\',\'#8d5524\',\'#ffdbac\',\'#a0522d\'];\n  var hairs=[\'#1a1a1a\',\'#3b2412\',\'#4a2c0f\',\'#6b4226\',\'#0d0d0d\',\'#2c2c2c\'];\n  var bg=cx.createLinearGradient(0,0,0,h);bg.addColorStop(0,\'#171a20\');bg.addColorStop(0.5,\'#1c2320\');bg.addColorStop(1,\'#0c1210\');cx.fillStyle=bg;cx.fillRect(0,0,w,h);\n  var tiers=7,weights=[0.09,0.105,0.122,0.14,0.155,0.175,0.203],y=0;\n  for(var ti=0;ti<tiers;ti++){\n    var rowH=h*weights[ti],depthFactor=ti/(tiers-1),baseScale=0.24+depthFactor*0.42,personScale=baseScale*(rowH/16),spacing=Math.max(3,rowH*0.4),isFar=depthFactor<0.3;\n    var seatColors=[\'#7a1f1f\',\'#8a2b1e\',\'#1f3f6b\',\'#142033\'];\n    var seatH=Math.min(6,rowH*0.3);\n    for(var sx=0;sx<w;sx+=6){cx.fillStyle=pick(seatColors);cx.fillRect(sx,y+rowH-seatH,5,seatH)}\n    cx.fillStyle=\'rgba(0,0,0,0.3)\';cx.fillRect(0,y+rowH-2,w,2);\n    cx.globalAlpha=isFar?0.85:1;\n    var jitter=spacing*0.2;\n    for(var x=-spacing;x<w+spacing;x+=spacing){\n      var px=x+(rnd()-0.5)*jitter,py=y+rowH*0.55+(rnd()-0.5)*rowH*0.1;\n      drawCrowdPerson(cx,px,py,personScale,pick(shirts),pick(skins),pick(hairs),isFar,rnd);\n    }\n    cx.globalAlpha=1;\n    y+=rowH;\n  }\n  var fade=cx.createLinearGradient(0,h*0.82,0,h);fade.addColorStop(0,\'rgba(0,0,0,0)\');fade.addColorStop(1,\'rgba(0,0,0,0.55)\');cx.fillStyle=fade;cx.fillRect(0,h*0.82,w,h*0.18);\n  return{w:w,h:h,canvas:c};\n}\nvar _cachedJackpotY=40;\nfunction refreshJackpotY(){\n  var el=document.getElementById(\'jackpot-ladder\');\n  if(!el)return;\n  var r=el.getBoundingClientRect();\n  if(r.height)_cachedJackpotY=r.top+r.height*(70/610);\n}\nfunction getJackpotY(){return _cachedJackpotY}\nfunction drawCrowdStand(w,y0,bandH){\n  var rw=Math.max(1,Math.round(w/4)*4),rh=Math.max(1,Math.round(bandH/4)*4);\n  if(rh<=0)return;\n  if(!_crowdCache||_crowdCache.w!==rw||_crowdCache.h!==rh)_crowdCache=renderCrowdCanvas(rw,rh);\n  ctx.drawImage(_crowdCache.canvas,0,y0);\n}\nfunction drawBackground(w,h,t){\n  t=t||0;\n  var gw=Math.min(w*0.62,520),gh=gw*0.42,gx=(w-gw)/2,gy=h*0.58-gh*0.92,post=Math.max(4,gw*0.018);\n  var sky=ctx.createLinearGradient(0,0,0,h*0.55);sky.addColorStop(0,\'#0c2413\');sky.addColorStop(1,\'#123a1c\');ctx.fillStyle=sky;ctx.fillRect(0,0,w,h*0.58);\n  var crowdY1=gy+gh*0.5,crowdY0=(gy+getJackpotY())/2;\n  if(crowdY0<0)crowdY0=0;\n  ctx.fillStyle=\'#000\';ctx.fillRect(0,0,w,crowdY0);\n  if(crowdY0<crowdY1)drawCrowdStand(w,crowdY0,crowdY1-crowdY0);\n  var gp=0.55+Math.sin(t*0.0009)*0.15;\n  [{x:w*0.06,y:h*0.02},{x:w*0.94,y:h*0.02}].forEach(function(pt){var g=ctx.createRadialGradient(pt.x,pt.y,0,pt.x,pt.y,w*0.34);g.addColorStop(0,\'rgba(255,255,240,\'+(0.16*gp).toFixed(3)+\')\');g.addColorStop(1,\'rgba(255,255,240,0)\');ctx.fillStyle=g;ctx.fillRect(0,0,w,h*0.6)});\n  var grass=ctx.createLinearGradient(0,h*0.55,0,h);grass.addColorStop(0,\'#1f6b32\');grass.addColorStop(1,\'#0d3a1a\');ctx.fillStyle=grass;ctx.fillRect(0,h*0.55,w,h*0.45);\n  ctx.fillStyle=\'rgba(255,255,255,0.035)\';var sw=w/14;for(var i=0;i<14;i+=2)ctx.fillRect(i*sw,h*0.55,sw,h*0.45);\n  var depth=gh*0.46,backX=gx+gw*0.085,backW=gw-gw*0.17,backY=gy-depth*0.58,backBotY=gy+gh-depth*0.22;\n  var FTL={x:gx,y:gy},FTR={x:gx+gw,y:gy},FBL={x:gx,y:gy+gh},FBR={x:gx+gw,y:gy+gh};\n  var BTL={x:backX,y:backY},BTR={x:backX+backW,y:backY},BBL={x:backX,y:backBotY},BBR={x:backX+backW,y:backBotY};\n  var NEAR=0.34,FAR=0.11;\n  ctx.save();ctx.beginPath();ctx.rect(0,gy,w,h-gy);ctx.clip();\n  fillNetQuad(BTL,BTR,BBR,BBL,\'rgba(4,10,6,0.40)\',\'rgba(4,10,6,0.20)\');fillNetQuad(FTL,BTL,BBL,FBL,\'rgba(4,10,6,0.10)\',\'rgba(4,10,6,0.34)\');fillNetQuad(FTR,FBR,BBR,BTR,\'rgba(4,10,6,0.34)\',\'rgba(4,10,6,0.10)\');\n  var nw=0.09+Math.sin(t*0.0013)*0.025;\n  drawMeshQuad(BTL,BTR,BBR,BBL,12,7,FAR,FAR,FAR+0.05,FAR+0.05,function(v){return Math.sin(v*Math.PI)*depth*nw},t);\n  drawMeshQuad(FTL,BTL,BBL,FBL,5,9,NEAR,FAR,FAR,NEAR,null,t);\n  drawMeshQuad(FTR,FBR,BBR,BTR,5,9,NEAR,NEAR,FAR,FAR,null,t);\n  ctx.restore();\n  ctx.strokeStyle=\'#f4f4f4\';ctx.lineWidth=post;ctx.lineJoin=\'round\';ctx.beginPath();ctx.moveTo(gx,gy+gh);ctx.lineTo(gx,gy);ctx.lineTo(gx+gw,gy);ctx.lineTo(gx+gw,gy+gh);ctx.stroke();\n  ctx.strokeStyle=\'rgba(255,255,255,0.55)\';ctx.lineWidth=Math.max(1,post*0.25);ctx.beginPath();ctx.moveTo(gx-post*0.2,gy+gh);ctx.lineTo(gx-post*0.2,gy);ctx.lineTo(gx+gw-post*0.2,gy);ctx.stroke();\n  var cx=w/2,lineY=gy+gh;ctx.strokeStyle=\'#f4f4f4\';ctx.lineWidth=Math.max(3,post*1.2);\n  ctx.beginPath();ctx.moveTo(0,lineY);ctx.lineTo(w,lineY);ctx.stroke();\n  var sTW=gw*1.35,sBW=gw*1.55,sBY=lineY+gh*0.55;ctx.beginPath();ctx.moveTo(cx-sTW/2,lineY);ctx.lineTo(cx-sBW/2,sBY);ctx.lineTo(cx+sBW/2,sBY);ctx.lineTo(cx+sTW/2,lineY);ctx.stroke();\n  var spotY=lineY+gh*1.60,ballR=Math.max(6,gw*0.052);\n  return{gx:gx,gy:gy,gw:gw,gh:gh,lineY:lineY,spotX:cx,spotY:spotY,ballR:ballR,\n    targets:{left:{x:gx+gw*0.20,y:gy+gh*0.35},mid:{x:gx+gw*0.50,y:gy+gh*0.40},right:{x:gx+gw*0.80,y:gy+gh*0.35}},\n    postPoints:{left:{x:gx+post*0.5,y:gy+gh*0.36},mid:{x:cx,y:gy+post*0.5},right:{x:gx+gw-post*0.5,y:gy+gh*0.36}}\n  };\n}\nfunction drawBallTrail(){BALL.trail.forEach(function(pt){ctx.save();ctx.globalAlpha=pt.life*0.5;ctx.fillStyle=\'#fff\';ctx.beginPath();ctx.arc(pt.x,pt.y,4*pt.life*pt.s,0,Math.PI*2);ctx.fill();ctx.globalAlpha=pt.life*0.2;ctx.fillStyle=\'#8ef29c\';ctx.beginPath();ctx.arc(pt.x,pt.y,8*pt.life*pt.s,0,Math.PI*2);ctx.fill();ctx.restore()})}\nfunction drawPostFX(dt){\n  for(var i=POST_FX.length-1;i>=0;i--){\n    var fx=POST_FX[i];fx.time+=dt;\n    var t=Math.min(fx.time/380,1);\n    if(t>=1){POST_FX.splice(i,1);continue}\n    ctx.save();\n    ctx.globalAlpha=1-t;\n    var r=6+t*34;\n    var ring=ctx.createRadialGradient(fx.x,fx.y,0,fx.x,fx.y,r);\n    ring.addColorStop(0,\'rgba(255,255,255,0.95)\');ring.addColorStop(0.4,\'rgba(255,240,170,0.55)\');ring.addColorStop(1,\'rgba(255,240,170,0)\');\n    ctx.fillStyle=ring;ctx.beginPath();ctx.arc(fx.x,fx.y,r,0,Math.PI*2);ctx.fill();\n    ctx.globalAlpha=(1-t)*0.9;\n    for(var k=0;k<6;k++){\n      var a=(k/6)*Math.PI*2+fx.time*0.01;\n      var d=r*0.9;\n      ctx.strokeStyle=\'#fff7d6\';ctx.lineWidth=2;\n      ctx.beginPath();ctx.moveTo(fx.x,fx.y);ctx.lineTo(fx.x+Math.cos(a)*d,fx.y+Math.sin(a)*d);ctx.stroke();\n    }\n    ctx.restore();\n  }\n}\n\n/* ===== MAIN DRAW ===== */\nvar lastGoalInfo=null;\nfunction drawScene(t,dt){\n  t=t||0;dt=dt||16;\n  var w=window.innerWidth,h=window.innerHeight;\n  ctx.clearRect(0,0,w,h);\n  var goal=drawBackground(w,h,t);lastGoalInfo=goal;\n  if(BALL.state===\'idle\'){BALL.startX=goal.spotX;BALL.startY=goal.spotY;BALL.targetX=goal.spotX;BALL.targetY=goal.spotY}\n  var targetH=goal.gh*0.58,px=targetH/GRID_H,spriteW=GRID_W*px,spriteH=GRID_H*px;\n  var originX=(w-spriteW)/2,originY=goal.lineY-spriteH;\n  goal.originX=originX;goal.originY=originY;goal.px=px;\n  ctx.imageSmoothingEnabled=false;\n  GK.update(dt);\n  BALL.update(dt,goal);\n  NET.update(dt);\n  GK.draw(originX,originY,px,t);\n  drawBallTrail();\n  drawPostFX(dt);\n  var br=goal.ballR*BALL.scale;\n  if(BALL.state===\'held\'){\n    var glovePos=GK.getGlovePos(originX,originY,px);\n    drawFootball(glovePos.x,glovePos.y,br,BALL.rotation);\n  }else{\n    var pos=BALL.getPos();\n    if(pos)drawFootball(pos.x,pos.y,br,BALL.rotation);\n  }\n}\nvar lastTime=performance.now();\nfunction loop(now){if(gameActive){var dt=Math.min(now-lastTime,50);lastTime=now;drawScene(now,dt)}requestAnimationFrame(loop)}\n\n/* ===== CONTROLS ===== */\nvar shotBtns=Array.prototype.slice.call(document.querySelectorAll(\'.shot-btn\'));\nvar isShooting=false;\nfunction spawnSparks(btn,dir){var r=btn.getBoundingClientRect(),cx=r.left+r.width/2,cy=r.top+r.height/2,color=dir===\'mid\'?\'#f6cf00\':\'#8ef29c\',ba=dir===\'left\'?180:(dir===\'right\'?0:-90);for(var i=0;i<9;i++){var el=document.createElement(\'div\');el.className=\'spark\';var s=3+Math.random()*3;el.style.width=s+\'px\';el.style.height=s+\'px\';el.style.left=(cx-s/2)+\'px\';el.style.top=(cy-s/2)+\'px\';el.style.background=color;el.style.boxShadow=\'0 0 8px \'+color;document.body.appendChild(el);var a=(ba+(Math.random()*70-35))*Math.PI/180,d=50+Math.random()*40,tx=Math.cos(a)*d,ty=Math.sin(a)*d;var anim=el.animate([{transform:\'translate(0,0) scale(1)\',opacity:1},{transform:\'translate(\'+tx+\'px,\'+ty+\'px) scale(.15)\',opacity:0}],{duration:550+Math.random()*200,easing:\'cubic-bezier(.2,.7,.3,1)\'});anim.onfinish=(function(n){return function(){n.remove()}})(el)}}\nfunction disableButtons(){shotBtns.forEach(function(b){b.classList.add(\'disabled\');b.classList.remove(\'reenable\')})}\nfunction enableButtons(){shotBtns.forEach(function(b){b.classList.remove(\'disabled\');b.classList.add(\'reenable\');setTimeout(function(){b.classList.remove(\'reenable\')},500)})}\nfunction fireShot(btn){\n  if(isShooting||!inSession||btn.classList.contains(\'disabled\'))return;isShooting=true;\n  var dir=btn.getAttribute(\'data-dir\');\n  var stake=betAmount;\n  disableButtons();btn.classList.add(\'pressed\');lockCashout();\n  if(navigator.vibrate){try{navigator.vibrate(18)}catch(e){}}\n  BALL.startSpin(dir);\n  var outcome=BALL.outcome;\n  var flyDur=outcome===\'save\'?BALL_FLY_SAVE:(outcome===\'post\'?BALL_FLY_POST:BALL_FLY_GOAL);\n  var notifyDelay=400+flyDur;\n  var tailDur;\n  if(outcome===\'save\'){\n    tailDur=1100+650+250+BALL_RETURN_DUR;\n  }else{\n    tailDur=(outcome===\'post\'?BALL_POST_DUR:BALL_BOUNCE_DUR)+BALL_SETTLE_PAUSE+BALL_RETURN_DUR+200;\n  }\n  var missedAll=false,wonRound=false;\n  setTimeout(function(){\n    if(outcome===\'save\'||outcome===\'post\'){\n      if(navigator.vibrate){try{navigator.vibrate(outcome===\'save\'?[20,30,20]:[30,20,30,20,30])}catch(e){}}\n      missedAll=true;\n      jpRegisterResult(false);\n      showGoalNotify(\'miss\');\n    }else{\n      wonRound=true;\n      if(navigator.vibrate){try{navigator.vibrate([60,30,60])}catch(e){}}\n      jpRegisterResult(true);\n      showGoalNotify(\'goal\');\n    }\n  },notifyDelay);\n  setTimeout(function(){\n    if(lastGoalInfo)BALL.reset(lastGoalInfo.spotX,lastGoalInfo.spotY);\n    GK.screenX=0;GK.screenY=0;GK.setState(\'idle\',0);GK.setPose(\'idle\',100);\n    btn.classList.remove(\'pressed\');isShooting=false;\n    if(missedAll){\n      hideShotControls(function(){});\n      hideCashoutBar(function(){showBetControls()});\n          inSession=false;sessionStake=0;winStreak=0;setJackpotHighlight(1);\n    }else if(wonRound&&winStreak>=9){\n      var jackpot=sessionAmount(winStreak);\n      inSession=false;\n      addBalance(jackpot);\n      hideShotControls(function(){});\n      hideCashoutBar(function(){showBetControls()});\n          winStreak=0;setJackpotHighlight(1);sessionStake=0;\n    }else{\n      enableButtons();\n      unlockCashout();\n    }\n  },notifyDelay+tailDur);\n}\nshotBtns.forEach(function(btn){btn.addEventListener(\'click\',function(e){e.stopPropagation();fireShot(btn)});btn.addEventListener(\'touchstart\',function(e){e.stopPropagation()},{passive:true})});\nresizeCanvas();\n})();\n</script>\n</body>\n</html>\n"""\n\n# ==========================================\n# 3. CÁC ROUTE CỦA FLASK\n# ==========================================\n@app.route(\'/\')\ndef index():\n    return render_template_string(HTML_CONTENT)\n\n@app.route(\'/api/register\', methods=[\'POST\'])\ndef api_register():\n    data = request.get_json(silent=True) or {}\n    username = (data.get(\'username\') or \'\').strip()\n    password = data.get(\'password\') or \'\'\n\n    if len(username) < 3:\n        return jsonify(success=False, message="Tên đăng nhập tối thiểu 3 ký tự"), 400\n    if len(password) < 4:\n        return jsonify(success=False, message="Mật khẩu tối thiểu 4 ký tự"), 400\n\n    users = load_users()\n    key = username.lower()\n    if key in users:\n        return jsonify(success=False, message="Tên đăng nhập đã tồn tại"), 409\n\n    users[key] = {\n        "username": username,\n        "password_hash": generate_password_hash(password),\n        "balance": 100\n    }\n    save_users(users)\n    session[\'username\'] = username\n    return jsonify(success=True, username=username)\n\n@app.route(\'/api/login\', methods=[\'POST\'])\ndef api_login():\n    data = request.get_json(silent=True) or {}\n    username = (data.get(\'username\') or \'\').strip()\n    password = data.get(\'password\') or \'\'\n\n    users = load_users()\n    key = username.lower()\n    user = users.get(key)\n    if not user or not check_password_hash(user.get(\'password_hash\', \'\'), password):\n        return jsonify(success=False, message="Sai tên đăng nhập hoặc mật khẩu"), 401\n\n    session[\'username\'] = user[\'username\']\n    return jsonify(success=True, username=user[\'username\'])\n\n@app.route(\'/api/logout\', methods=[\'POST\'])\ndef api_logout():\n    session.pop(\'username\', None)\n    return jsonify(success=True)\n\n@app.route(\'/nhacnen.mp3\')\ndef get_audio():\n    if os.path.exists("nhacnen.mp3"):\n        return send_file("nhacnen.mp3", mimetype="audio/mpeg")\n    return "Khong tim thay file nhac. Vui long dat file nhacnen.mp4 cung thu muc va dam bao da cai FFmpeg.", 404\n\n# ==========================================\n# 4. KHỞI CHẠY ỨNG DỤNG\n# ==========================================\nif __name__ == \'__main__\':\n    print("🚀 Đang khởi động Goalkeeper Flask App...")\n    extract_audio_from_video()\n    print("🌐 Mở trình duyệt và truy cập: http://localhost:5000")\n    app.run(debug=True, host=\'0.0.0.0\', port=5000)\n'

JACKPOT_WIN_PATCH = r'''    }else if(wonRound&&winStreak>=9){
      var jackpot=sessionAmount(winStreak);
      inSession=false;
      (function(){
        if(!document.getElementById('jw-style')){
          var st=document.createElement('style');st.id='jw-style';
          st.textContent='#jackpot-win-overlay{position:absolute;inset:0;z-index:90;display:none;align-items:center;justify-content:center;flex-direction:column;pointer-events:none;overflow:hidden;opacity:0;transition:opacity .4s ease}#jackpot-win-overlay.show{display:flex;opacity:1}.jw-flash{position:absolute;inset:0;background:#fff;opacity:0}#jackpot-win-overlay.show .jw-flash{animation:jwFlash .5s ease forwards}@keyframes jwFlash{0%{opacity:.85}100%{opacity:0}}.jw-rays{position:absolute;width:240%;height:240%;background:conic-gradient(from 0deg,rgba(255,214,90,0) 0deg,rgba(255,214,90,.5) 8deg,rgba(255,214,90,0) 24deg,rgba(255,214,90,0) 64deg,rgba(255,214,90,.45) 72deg,rgba(255,214,90,0) 88deg,rgba(255,214,90,0) 128deg,rgba(255,214,90,.4) 136deg,rgba(255,214,90,0) 152deg,rgba(255,214,90,0) 192deg,rgba(255,214,90,.45) 200deg,rgba(255,214,90,0) 216deg,rgba(255,214,90,0) 256deg,rgba(255,214,90,.4) 264deg,rgba(255,214,90,0) 280deg,rgba(255,214,90,0) 320deg,rgba(255,214,90,.45) 328deg,rgba(255,214,90,0) 344deg);opacity:0}#jackpot-win-overlay.show .jw-rays{animation:jwRaySpin 6s linear infinite,jwRayFade .5s ease forwards}@keyframes jwRaySpin{to{transform:rotate(360deg)}}@keyframes jwRayFade{to{opacity:1}}.jw-trophy{font-size:60px;filter:drop-shadow(0 0 22px rgba(255,214,90,.9));transform:scale(0) rotate(-25deg);opacity:0}#jackpot-win-overlay.show .jw-trophy{animation:jwTrophyPop .7s cubic-bezier(.34,1.56,.64,1) .15s forwards,jwTrophyFloat 1.8s ease-in-out .9s infinite}@keyframes jwTrophyPop{0%{transform:scale(0) rotate(-25deg);opacity:0}60%{transform:scale(1.25) rotate(8deg);opacity:1}100%{transform:scale(1) rotate(0);opacity:1}}@keyframes jwTrophyFloat{0%,100%{transform:translateY(0)}50%{transform:translateY(-9px)}}.jw-title{margin-top:8px;font-family:"Arial Black",Arial,sans-serif;font-weight:900;font-size:clamp(30px,9vw,50px);letter-spacing:4px;background:linear-gradient(90deg,#fff7d6,#ffd65a,#ff8a00,#ffd65a,#fff7d6);background-size:250% 100%;-webkit-background-clip:text;background-clip:text;color:transparent;text-shadow:0 4px 18px rgba(0,0,0,.5);opacity:0;transform:translateY(16px) scale(.7)}#jackpot-win-overlay.show .jw-title{animation:jwTitlePop .6s cubic-bezier(.34,1.56,.64,1) .3s forwards,jwTitleShimmer 2.4s linear 1s infinite}@keyframes jwTitlePop{to{opacity:1;transform:translateY(0) scale(1)}}@keyframes jwTitleShimmer{0%{background-position:250% 0}100%{background-position:-50% 0}}.jw-amount{margin-top:10px;padding:8px 22px;border-radius:999px;background:rgba(0,0,0,.35);border:1px solid rgba(255,214,90,.5);color:#fff7d6;font-size:19px;font-weight:800;letter-spacing:.5px;font-variant-numeric:tabular-nums;opacity:0;transform:scale(.6)}#jackpot-win-overlay.show .jw-amount{animation:jwAmountPop .5s cubic-bezier(.34,1.56,.64,1) .55s forwards}@keyframes jwAmountPop{to{opacity:1;transform:scale(1)}}.jw-confetti{position:absolute;top:-20px;border-radius:2px;will-change:transform,opacity}.jw-coin{position:absolute;top:-24px;width:18px;height:18px;border-radius:50%;background:radial-gradient(circle at 34% 26%,#ffe66d,#c99a00 72%);box-shadow:0 1px 3px rgba(0,0,0,.5),inset 0 1px 1px rgba(255,255,255,.6);will-change:transform,opacity}';
          document.head.appendChild(st);
        }
        var ov=document.getElementById('jackpot-win-overlay');
        if(!ov){
          ov=document.createElement('div');ov.id='jackpot-win-overlay';
          ov.innerHTML='<div class="jw-flash"></div><div class="jw-rays"></div><div class="jw-trophy">🏆</div><div class="jw-title">JACKPOT!</div><div class="jw-amount" id="jwAmount">0 Token</div>';
          document.getElementById('game-screen').appendChild(ov);
        }
        document.getElementById('jwAmount').textContent='+'+jpFormat(jackpot);
        ov.classList.remove('hide');void ov.offsetWidth;ov.classList.add('show');
        if(navigator.vibrate){try{navigator.vibrate([40,30,40,30,80,30,120])}catch(e){}}
        function spawnConfetti(n){
          var w=window.innerWidth,colors=['#ffd65a','#ff8a00','#3ddc6b','#63c7ff','#ff5c8a','#fff7d6'];
          for(var i=0;i<n;i++){
            var el=document.createElement('div');el.className='jw-confetti';
            var s=6+Math.random()*6;el.style.width=s+'px';el.style.height=(s*0.4)+'px';el.style.left=(Math.random()*w)+'px';el.style.background=colors[Math.floor(Math.random()*colors.length)];
            ov.appendChild(el);
            var fall=window.innerHeight+60,drift=(Math.random()*160-80),rot=360+Math.random()*720,dur=1800+Math.random()*1400,delay=Math.random()*500;
            var anim=el.animate([{transform:'translate(0,0) rotate(0deg)',opacity:1},{transform:'translate('+drift+'px,'+fall+'px) rotate('+rot+'deg)',opacity:.9,offset:.85},{transform:'translate('+drift+'px,'+(fall+40)+'px) rotate('+rot+'deg)',opacity:0}],{duration:dur,delay:delay,easing:'cubic-bezier(.3,.4,.4,1)'});
            anim.onfinish=(function(n2){return function(){n2.remove()}})(el);
          }
        }
        function spawnCoins(n){
          var w=window.innerWidth;
          for(var i=0;i<n;i++){
            var el=document.createElement('div');el.className='jw-coin';el.style.left=(Math.random()*w)+'px';
            ov.appendChild(el);
            var fall=window.innerHeight+60,drift=(Math.random()*100-50),rot=(Math.random()<.5?-1:1)*(360+Math.random()*360),dur=1400+Math.random()*900,delay=Math.random()*700;
            var anim=el.animate([{transform:'translate(0,0) rotate(0deg) scale(1)',opacity:1},{transform:'translate('+drift+'px,'+fall+'px) rotate('+rot+'deg) scale(.9)',opacity:1,offset:.9},{transform:'translate('+drift+'px,'+(fall+30)+'px) rotate('+rot+'deg) scale(.8)',opacity:0}],{duration:dur,delay:delay,easing:'cubic-bezier(.3,.5,.3,1)'});
            anim.onfinish=(function(n2){return function(){n2.remove()}})(el);
          }
        }
        spawnConfetti(46);spawnCoins(16);
        setTimeout(function(){spawnConfetti(26);spawnCoins(10)},650);
        setTimeout(function(){
          ov.classList.remove('show');ov.classList.add('hide');
          setTimeout(function(){
            ov.classList.remove('hide');
            addBalance(jackpot);
            hideShotControls(function(){});
            hideCashoutBar(function(){showBetControls()});
          },420);
        },2600);
      })();
          winStreak=0;setJackpotHighlight(1);sessionStake=0;
    }else{'''


def _add_magicai_session_bridge(source):
    """Give the bundled simulation one immutable nine-shot plan per PLAY.

    MAGICAI reads this same plan; it never changes outcomes or invents forecasts.
    The source is embedded above, so keep the integration anchors explicit.
    """
    old_plan = '''var currentPermIndex=0;
function planRound(){
  var dirs=['left','mid','right'];
  currentPermIndex=Math.floor(Math.random()*ROUND_PERMS.length);
  var outs=ROUND_PERMS[currentPermIndex];
  roundPlan={};
  dirs.forEach(function(d,i){roundPlan[d]=outs[i]});
  return currentPermIndex;
}'''
    new_plan = r'''var currentPermIndex=0;
var magicSession=null;
var magicHud=document.createElement('div');
magicHud.id='magic-session-hud';
magicHud.style.cssText='position:fixed;left:calc(env(safe-area-inset-left,0px) + 8px);bottom:calc(env(safe-area-inset-bottom,0px) + 16px);max-width:60%;padding:2px 6px;border-radius:999px;color:#bfffd5;background:linear-gradient(135deg,#0b2015ee,#04120ce0);border:1px solid #80ffb555;font:700 7px/1.3 monospace;letter-spacing:.15px;text-align:left;z-index:40;pointer-events:none;opacity:0;box-shadow:0 3px 9px rgba(0,0,0,.4);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;transition:opacity .35s ease,transform .35s cubic-bezier(.34,1.56,.64,1);transform:translateY(8px);';
document.body.appendChild(magicHud);
function magicSnapshot(){
  /* gameStarted luon = true tu rat som (ngay khi trang Penalty vua tai xong,
     truoc ca khi nguoi dung co the bam PLAY), nen no khong bao gio la dieu
     kien phan biet that su cho "co dang choi hay khong" - magicSession +
     inSession da du de xac dinh dieu do. Truoc day active con doi hoi ca
     gameStarted nua: bat ky doi lech thoi diem nao (vd Android Chrome tam
     dung/nen iframe khi bam Home) lam gameStarted doc duoc gia tri false
     thoang qua se khien active sai thanh false du inSession/magicSession
     van dung - day chinh la nguyen nhan loi "chua co van nao dang choi". */
  var active=!!(magicSession&&inSession);
  return {source:'magicos-penalty-bridge',type:'state',active:active,
    sessionId:magicSession?magicSession.id:null,
    step:magicSession?magicSession.step:0,busy:!!isShooting,
    plans:active?magicSession.plans.map(function(index){return ROUND_PERMS[index].slice()}):[],
    results:magicSession?magicSession.results.slice():[],
    _dbg:{hasSession:!!magicSession,inSession:!!inSession,gameStarted:!!gameStarted}};
}
function magicPublish(requestId){
  var state=magicSnapshot();
  magicHud.style.opacity=state.active?'1':'0';
  magicHud.style.transform='translateY('+(state.active?'0':'8px')+')';
  magicHud.textContent=state.active?'🔗 PHIÊN '+state.sessionId+' · LƯỢT '+Math.min(state.step+1,9)+'/9':'';
  /* Gui thang cho parent bat ke origin: dua vao document.referrer de tinh
     origin rat de gay (trinh duyet an referrer khi lech giao thuc http/https,
     hoac Referrer-Policy mac dinh), lam ca HUD lan ket noi MAGICAI bi vo hieu
     am tham. Vi day la kenh lien lac noi bo giua 2 phan cua cung 1 ung dung,
     dung '*' de dam bao luon gui duoc. */
  if(window.parent!==window){
    state.requestId=requestId||null;
    window.parent.postMessage(state,'*');
  }
}
function magicStartSession(){
  var entropy=new Uint32Array(2);crypto.getRandomValues(entropy);
  var plans=Array.from({length:9},function(){return Math.floor(Math.random()*ROUND_PERMS.length)});
  magicSession={id:'PEN-'+Date.now().toString(36).toUpperCase()+'-'+Array.from(entropy).map(function(n){return n.toString(36).toUpperCase()}).join(''),plans:plans,step:0,results:[]};
}
function planRound(){
  var dirs=['left','mid','right'];
  currentPermIndex=magicSession?magicSession.plans[Math.min(magicSession.step,8)]:Math.floor(Math.random()*ROUND_PERMS.length);
  var outs=ROUND_PERMS[currentPermIndex];
  roundPlan={};
  dirs.forEach(function(d,i){roundPlan[d]=outs[i]});
  magicPublish();
  return currentPermIndex;
}
window.addEventListener('message',function(ev){
  if(ev.source!==window.parent)return;
  var d=ev.data;
  if(d&&d.source==='magicai-tool'&&d.type==='query'&&typeof d.requestId==='string')magicPublish(d.requestId);
});
setInterval(function(){magicPublish()},1000);'''
    changes = [
        (old_plan, new_plan),
        ("playBtn.addEventListener('click',function(){\n  if(isShooting)return;",
         "playBtn.addEventListener('click',function(){\n  if(isShooting||inSession)return;"),
        ("  var permIndex=planRound();", "  magicStartSession();\n  var permIndex=planRound();"),
        ("  var outcome=BALL.outcome;", "  var outcome=BALL.outcome;\n  magicPublish();"),
        ("      showGoalNotify('goal');\n    }\n  },notifyDelay);",
         "      showGoalNotify('goal');\n    }\n    if(magicSession)magicSession.results.push({shot:magicSession.step+1,direction:dir,outcome:outcome});\n    magicPublish();\n  },notifyDelay);"),
        ("    }else{\n      enableButtons();\n      unlockCashout();\n    }\n  },notifyDelay+tailDur);",
         "    }else{\n      magicSession.step++;\n      planRound();\n      enableButtons();\n      unlockCashout();\n    }\n    magicPublish();\n  },notifyDelay+tailDur);"),
        ("function endSession(){\n  inSession=false;sessionStake=0;",
         "function endSession(){\n  inSession=false;sessionStake=0;\n  magicPublish();"),
        ("  var amount=sessionAmount(winStreak);\n  inSession=false;",
         "  var amount=sessionAmount(winStreak);\n  inSession=false;\n  magicPublish();"),
        ("""    }else if(wonRound&&winStreak>=9){
      var jackpot=sessionAmount(winStreak);
      inSession=false;
      addBalance(jackpot);
      hideShotControls(function(){});
      hideCashoutBar(function(){showBetControls()});
          winStreak=0;setJackpotHighlight(1);sessionStake=0;
    }else{""",
         JACKPOT_WIN_PATCH),
    ]
    for before, after in changes:
        if source.count(before) != 1:
            raise RuntimeError('Cannot integrate MAGICAI: embedded game changed')
        source = source.replace(before, after, 1)
    return source


PENALTY_APP_SOURCE = _add_magicai_session_bridge(PENALTY_APP_SOURCE)


def _find_free_port(start_port, host="127.0.0.1", attempts=25):
    port = start_port
    for _ in range(attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind((host, port))
                return port
            except OSError:
                port += 1
    return None

def _load_penalty_flask_app():
    """Thuc thi nguyen van ma app.py trong 1 namespace rieng, tra ve (app, extract_audio_fn)."""
    ns = {"__name__": "penalty_app_module"}
    exec(compile(PENALTY_APP_SOURCE, "app.py", "exec"), ns)
    return ns.get("app"), ns.get("extract_audio_from_video")

def start_penalty_server():
    """Khoi chay app Penalty (Flask) o 1 cong rieng. Tra ve so cong hoac None neu that bai."""
    try:
        flask_app, extract_audio = _load_penalty_flask_app()
    except Exception as e:
        print(f"[Penalty] Khong the tai app (thieu Flask/Werkzeug?): {e}")
        print("[Penalty] Cai dat bang lenh: pip install flask werkzeug")
        return None
    if flask_app is None:
        print("[Penalty] Khong tim thay doi tuong Flask 'app' trong app.py")
        return None
    if extract_audio:
        try:
            extract_audio()
        except Exception as e:
            print(f"[Penalty] Bo qua buoc trich xuat am thanh: {e}")
    port = _find_free_port(PENALTY_PORT_START)
    if port is None:
        print("[Penalty] Khong tim duoc cong trong cho app Penalty.")
        return None

    def _run():
        try:
            flask_app.run(host="127.0.0.1", port=port, debug=False,
                           use_reloader=False, threaded=True)
        except Exception as e:
            print(f"[Penalty] App dung do loi: {e}")

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    print(f"[Penalty] Dang chay noi bo tai http://127.0.0.1:{port}")
    return port

ANIM_CSS_1 = r"""
#home-screen {
position: absolute; top: 0; left: 0; width: 100%; height: 100%;
display: none; z-index: 10; overflow: hidden;
background-color: #222; background-size: cover; background-position: center;
opacity: 1; transform: scale(1); transition: opacity 0.32s ease, transform 0.55s var(--ios-spring-snappy);
}
/* Trang thai khoi tao truoc khi "nay" vao man hinh sau khi mo khoa */
#home-screen.home-spring-in { opacity: 0; transform: scale(0.88); transition: none; }
/* Nay tung icon app rieng le kieu iOS thuc khi mo khoa, moi icon co do tre khac nhau (dat qua JS) */
.home-icons-animate .app-icon { animation: iconPopIn 0.52s cubic-bezier(.34,1.56,.64,1) both; }
@keyframes iconPopIn {
0% { opacity: 0; transform: scale(0.4) translateY(18px); }
55% { opacity: 1; transform: scale(1.12) translateY(-4px); }
75% { transform: scale(0.95) translateY(1px); }
100% { opacity: 1; transform: scale(1) translateY(0); }
}
.pages-wrapper { display: flex; width: 200%; height: 100%; transition: transform 0.4s var(--ios-spring-snappy); will-change: transform; }
.page { width: 50%; height: 100%; padding: 70px 20px 115px; display: flex; flex-direction: column; gap: 20px; overflow-y: auto; }
.page::-webkit-scrollbar { display: none; }
.app-grid { display: grid; grid-template-columns: repeat(4, 1fr); row-gap: 26px; justify-items: center; width: 100%; }
.app-icon { width: 100%; display: flex; flex-direction: column; align-items: center; transition: transform 0.2s var(--ios-spring-snappy); cursor: pointer; }
.app-icon:active { transform: scale(0.85); }
.app-box { width: 68px; height: 68px; border-radius: 16px; display: flex; justify-content: center; align-items: center; font-size: 38px; color: white; box-shadow: 0 4px 12px rgba(0,0,0,0.2); }
.page-dots { position: absolute; bottom: 125px; left: 50%; transform: translateX(-50%); display: flex; justify-content: center; align-items: center; gap: 8px; z-index: 15; pointer-events: none; background: rgba(255,255,255,0.15); backdrop-filter: blur(25px) saturate(150%); -webkit-backdrop-filter: blur(25px) saturate(150%); padding: 6px 14px; border-radius: 20px; box-shadow: 0 4px 10px rgba(0,0,0,0.1), inset 0 1px 0 rgba(255,255,255,0.2); border: 1px solid rgba(255,255,255,0.1); }
.page-dot { width: 7px; height: 7px; border-radius: 50%; background: rgba(255,255,255,0.35); transition: background 0.3s, transform 0.3s; }
.page-dot.active { background: rgba(255,255,255,1); }
#dock { position: absolute; bottom: 25px; left: 15px; right: 15px; height: 85px; background: rgba(255,255,255,0.1); backdrop-filter: blur(35px) saturate(150%); -webkit-backdrop-filter: blur(35px) saturate(150%); border: 1px solid rgba(255,255,255,0.25); border-radius: 32px; display: flex; justify-content: space-evenly; align-items: center; box-shadow: 0 10px 30px rgba(0,0,0,0.15), inset 0 1px 0 rgba(255,255,255,0.2); z-index: 20; }
#lock-screen-wrapper { position: absolute; top: 0; left: 0; width: 100%; height: 100%; z-index: 9700; transition: transform 0.7s var(--ios-smooth), backdrop-filter 0.5s ease, background 0.5s ease; backdrop-filter: blur(0px); background: transparent; }
#lock-screen-ui { position: absolute; top: 0; left: 0; width: 100%; height: 100%; display: flex; flex-direction: column; align-items: center; padding-top: 80px; transition: opacity 0.3s ease, transform 0.5s var(--ios-spring-snappy); z-index: 51; }
.ls-time { font-size: 80px; font-weight: 800; color: white; line-height: 1; text-shadow: 0 2px 10px rgba(0,0,0,0.2); letter-spacing: -2px; }
.ls-date { font-size: 20px; font-weight: 600; color: rgba(255,255,255,0.9); margin-top: -5px; margin-bottom: 10px; text-shadow: 0 1px 5px rgba(0,0,0,0.2); }
.ls-notif-list { width: calc(100% - 32px); max-width: 340px; margin-top: 20px; display: flex; flex-direction: column; gap: 12px; max-height: 44vh; overflow-y: auto; -webkit-overflow-scrolling: touch; padding: 2px 4px 6px; }
.ls-notif-list::-webkit-scrollbar { display: none; }
.ls-notif-toolbar { width: calc(100% - 32px); max-width: 340px; display: flex; justify-content: flex-end; margin-top: 14px; }
.ls-notif-clearall {
  display: flex; align-items: center; gap: 6px;
  padding: 7px 16px 7px 13px; border: none; border-radius: 999px;
  background: linear-gradient(165deg, rgba(255,255,255,0.24) 0%, rgba(255,255,255,0.08) 60%, rgba(255,255,255,0.13) 100%);
  backdrop-filter: blur(26px) saturate(190%) brightness(1.06); -webkit-backdrop-filter: blur(26px) saturate(190%) brightness(1.06);
  box-shadow: 0 4px 14px rgba(0,0,0,0.2), inset 0 1px 0 rgba(255,255,255,0.28);
  color: rgba(255,255,255,0.94); font-size: 12.5px; font-weight: 700; letter-spacing: 0.2px;
  cursor: pointer; -webkit-tap-highlight-color: transparent;
  opacity: 0; transform: translateY(-8px) translateX(14px) scale(0.82); pointer-events: none;
  transition: opacity 0.32s var(--ios-spring-snappy), transform 0.32s var(--ios-spring-snappy), background 0.2s ease;
  z-index: 3;
}
.ls-notif-clearall.show { opacity: 1; transform: translateY(0) translateX(14px) scale(1); pointer-events: auto; }
.ls-notif-clearall:active { transform: translateX(14px) scale(0.88); background: rgba(255,255,255,0.2); }
.ls-notif-clearall i { font-size: 11px; opacity: 0.85; }
.ls-notif-clearall.clearing { pointer-events: none; }
@keyframes lsClearAllPop { 0% { transform: translateX(14px) scale(1); } 45% { transform: translateX(14px) scale(0.84); } 100% { transform: translateX(14px) scale(1); } }
.ls-notif-clearall.pop { animation: lsClearAllPop 0.32s ease; }
.ls-notif-item {
  position: relative; display: flex; align-items: flex-start; gap: 12px;
  padding: 13px 15px; border-radius: 22px; overflow: hidden;
  background: linear-gradient(165deg, rgba(255,255,255,0.24) 0%, rgba(255,255,255,0.08) 60%, rgba(255,255,255,0.13) 100%);
  backdrop-filter: blur(30px) saturate(190%) brightness(1.06);
  -webkit-backdrop-filter: blur(30px) saturate(190%) brightness(1.06);
  box-shadow:
    0 1px 0 rgba(255,255,255,0.5) inset,
    0 -1px 0 rgba(0,0,0,0.10) inset,
    0 0 0 1px rgba(255,255,255,0.14) inset,
    0 6px 16px rgba(0,0,0,0.12);
  opacity: 0; transform: translateY(-14px) scale(0.96);
  animation: lsNotifIn 0.5s cubic-bezier(.22,1,.36,1) forwards;
  transition: transform 0.18s var(--ios-spring-snappy), box-shadow 0.18s ease;
}
.ls-notif-item::before {
  content: ''; position: absolute; inset: 0; pointer-events: none; border-radius: inherit;
  background: radial-gradient(130% 65% at 16% -12%, rgba(255,255,255,0.65) 0%, rgba(255,255,255,0) 55%);
  mix-blend-mode: overlay; opacity: 0.95;
}
.ls-notif-item::after {
  content: ''; position: absolute; left: 14px; right: 14px; bottom: 0; height: 1px; pointer-events: none;
  background: linear-gradient(90deg, rgba(255,255,255,0) 0%, rgba(255,255,255,0.22) 50%, rgba(255,255,255,0) 100%);
}
.ls-notif-item:active {
  transform: scale(0.975);
  box-shadow:
    0 1px 0 rgba(255,255,255,0.38) inset,
    0 -1px 0 rgba(0,0,0,0.12) inset,
    0 0 0 1px rgba(255,255,255,0.12) inset,
    0 3px 8px rgba(0,0,0,0.14);
}
/* Vao man hinh kieu "roi xuong xep vao chong": tu tren cao, hoi mo + thu nho,
   roi nay xuong dung vi tri va nay nhe (overshoot) truoc khi dinh hinh han -
   giong cam giac 1 the giay that vua duoc dat/tha xuong tren dau chong giay
   cu, thay vi chi truot xuong don thuan. */
@keyframes lsNotifIn {
  0% { opacity: 0; transform: translateY(-30px) scale(0.9); filter: blur(8px); }
  55% { opacity: 1; transform: translateY(3px) scale(1.015); filter: blur(0); }
  78% { transform: translateY(-1.5px) scale(0.997); }
  100% { opacity: 1; transform: translateY(0) scale(1); }
}
/* Cac the thong bao CU bi "day" nhe xuong duoi + lun mot chut moi khi co the
   MOI vua xep chong len tren cung - mo phong dung cam giac ca chong giay bi
   chen/xoc lai khi co 1 to giay moi dat len tren, thay vi cac the dung yen
   mot cach vo can. */
.ls-notif-push { animation: lsNotifPush 0.42s cubic-bezier(.22,1,.36,1) both; }
@keyframes lsNotifPush {
  0% { transform: translateY(0) scale(1); filter: brightness(1); }
  38% { transform: translateY(7px) scale(0.982); filter: brightness(0.93); }
  100% { transform: translateY(0) scale(1); filter: brightness(1); }
}
.ls-notif-icon {
  position: relative; width: 32px; height: 32px; border-radius: 9px; flex: none; overflow: hidden;
  display: flex; align-items: center; justify-content: center; font-size: 14.5px; color: #fff;
  background: linear-gradient(160deg, #4dffb8 0%, #0f8a52 55%, #06542f 100%);
  box-shadow: 0 3px 8px rgba(6,84,47,0.45), inset 0 1px 1px rgba(255,255,255,0.55), inset 0 -2px 3px rgba(0,0,0,0.25);
}
.ls-notif-icon::after { content: ''; position: absolute; inset: 0; background: linear-gradient(160deg, rgba(255,255,255,0.55), rgba(255,255,255,0) 55%); pointer-events: none; }
.ls-notif-body { flex: 1; min-width: 0; }
.ls-notif-top { display: flex; align-items: baseline; justify-content: space-between; gap: 8px; }
.ls-notif-app { font-size: 11px; font-weight: 700; color: rgba(255,255,255,0.85); text-transform: uppercase; letter-spacing: 0.6px; }
.ls-notif-time { font-size: 11px; font-weight: 500; color: rgba(255,255,255,0.55); flex: none; font-variant-numeric: tabular-nums; }
.ls-notif-text { margin-top: 2px; font-size: 13.5px; font-weight: 500; color: rgba(255,255,255,0.97); line-height: 1.38; word-break: break-word; text-align: left; text-shadow: 0 1px 2px rgba(0,0,0,0.15); }
/* ===== Vuot sang trai de xoa thong bao (kieu iPhone) =====
   Moi thong bao duoc boc trong 1 ".ls-notif-row": lop nen do ".ls-notif-del-bg"
   nam co dinh phia sau, con ".ls-notif-item" (the kinh) nam de len tren va
   duoc keo sang trai bang JS khi nguoi dung vuot tay - lo dan nen do voi
   icon thung rac ra phia sau, dung nhu Mail/Tin nhan tren iOS. */
.ls-notif-row { position: relative; border-radius: 22px; }
.ls-notif-del-bg {
  position: absolute; top: 0; bottom: 0; right: 0; left: auto; width: var(--reveal, 0px); min-width: 0; z-index: 0; border-radius: 22px;
  display: flex; align-items: center; justify-content: flex-end; gap: 9px;
  padding-right: 22px; overflow: hidden;
  background: linear-gradient(135deg, #ff5b52 0%, #e0342a 55%, #c8241c 100%);
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.25), inset 0 -10px 18px rgba(0,0,0,0.18);
  /* QUAN TRONG: phai AN HAN lop nen do nay khi khong vuot (opacity 0 + khong
     bat su kien chuot/cham), vi ".ls-notif-item" de len tren la kinh mo
     (backdrop-filter) - no LUON "doc" mau cua bat ky thu gi nam ngay phia
     sau no de lam mo/nhoe theo hieu ung kinh. Neu de nen do hien san (opacity
     1) ngay ca luc khong vuot, kinh se bi nhuom do lom ngay ca khi dung yen -
     day chinh la nguyen nhan the "Liquid Glass" bi ngar thanh mau do. */
  opacity: 0; pointer-events: none; transition: opacity 0.18s ease;
}
.ls-notif-row.swipe-open .ls-notif-del-bg { opacity: 1; pointer-events: auto; }
/* Khi tha tay, do rong lop do chay cung nhip voi the kinh de mep phai cua the va
   mep trai lop do luon khit nhau (khong bao gio de lop do nam duoi kinh). */
.ls-notif-row.notif-settling .ls-notif-del-bg { transition: opacity 0.18s ease, width 0.18s var(--ios-spring-snappy); }
.ls-notif-del-label { color: #fff; font-size: 12.5px; font-weight: 800; letter-spacing: 0.4px; text-shadow: 0 1px 2px rgba(0,0,0,0.25); opacity: 0; transform: translateX(6px); transition: opacity 0.2s ease, transform 0.24s cubic-bezier(.22,1,.36,1); }
.ls-notif-del-icon { position: relative; flex: none; width: 36px; height: 36px; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: #fff; font-size: 15px; background: rgba(255,255,255,0.16); box-shadow: inset 0 1px 1px rgba(255,255,255,0.35); transform: scale(0.001); transition: transform 0.26s cubic-bezier(.34,1.56,.64,1); }
.ls-notif-row.swipe-open .ls-notif-del-icon { transform: scale(1); }
.ls-notif-row.swipe-open .ls-notif-del-label { opacity: 1; transform: translateX(0); }
.ls-notif-item.notif-dragging { transition: none !important; }
.ls-notif-item.notif-swiping::before, .ls-notif-item.notif-swiping::after { opacity: 0; transition: opacity 0.15s ease; }
.ls-swipe-text { position: absolute; bottom: 40px; color: white; font-weight: 500; font-size: 15px; animation: pulseText 2s infinite; }
.ls-swipe-bar { position: absolute; bottom: 10px; width: 140px; height: 5px; background: white; border-radius: 10px; left: 50%; transform: translateX(-50%); }
.ls-quick-btn { position: absolute; bottom: 35px; width: 50px; height: 50px; border-radius: 50%; background: rgba(0,0,0,0.25); backdrop-filter: blur(15px); -webkit-backdrop-filter: blur(15px); display: flex; justify-content: center; align-items: center; font-size: 20px; color: white; box-shadow: inset 0 0 0 1px rgba(255,255,255,0.1); transition: transform 0.2s var(--ios-spring-snappy), background 0.2s, color 0.2s; cursor: pointer; }
.ls-quick-btn:active { background: rgba(255,255,255,0.85); color: #000; transform: scale(0.85); }
.ls-btn-right { right: 35px; font-size: 18px; }
.ls-btn-left { left: 35px; font-size: 18px; }
#passcode-ui { position: absolute; top: 0; left: 0; width: 100%; height: 100%; display: flex; flex-direction: column; align-items: center; padding-top: 100px; opacity: 0; pointer-events: none; transform: scale(0.85); filter: blur(15px); transition: all 0.5s var(--ios-spring-snappy); z-index: 52; }
.pc-title { color: #ffffff; font-size: 24px; font-weight: 500; margin-bottom: 35px; letter-spacing: 0.5px; text-shadow: 0 2px 10px rgba(0,0,0,0.3); }
.pc-dots { display: flex; gap: 22px; margin-bottom: 60px; }
.pc-dot { width: 14px; height: 14px; border-radius: 50%; border: 1.5px solid #ffffff; background: transparent; transition: transform 0.2s var(--ios-spring-snappy), background 0.15s, border-color 0.15s; box-shadow: none; }
.pc-dot.filled { background: #ffffff; border-color: #ffffff; transform: scale(1.15); box-shadow: 0 0 8px rgba(255,255,255,0.4); }
.pc-numpad { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px 30px; }
.pc-btn { width: 82px; height: 82px; border-radius: 50%; background: linear-gradient(135deg, rgba(255,255,255,0.15) 0%, rgba(255,255,255,0.05) 100%); backdrop-filter: blur(35px); border: 1px solid rgba(255,255,255,0.2); display: flex; flex-direction: column; justify-content: center; align-items: center; color: white; cursor: pointer; transition: transform 0.22s var(--ios-spring-snappy), background 0.2s ease, box-shadow 0.2s ease; position: relative; overflow: hidden; }
.pc-btn:active, .pc-btn.key-pressed { background: rgba(255,255,255,0.28); }
/* Nhan phim lun xuong ngay lap tuc (giong phan hoi co hoc that), roi nay nhe khi tha ra */
.pc-btn.key-pressed { transform: scale(0.86); box-shadow: inset 0 4px 10px rgba(0,0,0,0.35), inset 0 0 0 1px rgba(255,255,255,0.12); transition: transform 0.06s ease, background 0.06s ease, box-shadow 0.06s ease; }
.pc-btn.empty { background: transparent; border: none; box-shadow: none; backdrop-filter: none; pointer-events: none; }
.pc-num { font-size: 40px; font-weight: 300; line-height: 1; margin-top: 4px; }
.pc-letters { font-size: 11px; font-weight: 600; letter-spacing: 2px; line-height: 1; margin-top: 5px; opacity: 0.85; height: 11px; }
.pc-action { width: 82px; height: 82px; display: flex; justify-content: center; align-items: center; font-size: 18px; color: rgba(255,255,255,0.9); font-weight: 500; cursor: pointer; transition: transform 0.22s var(--ios-spring-snappy), opacity 0.2s ease; }
.pc-action:active, .pc-action.key-pressed { transform: scale(0.86); opacity: 0.7; }
.pc-action.key-pressed { transition: transform 0.06s ease, opacity 0.06s ease; }
.shake-animation { animation: shake 0.4s cubic-bezier(.36,.07,.19,.97) both; }
/* Rung dang song cho 6 dot passcode: tung dot lech pha nhau (dat qua JS) tao cam giac gon song chay qua */
@keyframes dotWaveShake {
0%, 100% { transform: translateX(0) scale(1); }
30% { transform: translateX(-4.5px) scale(1.18); border-color: #ff453a; background: #ff453a; }
60% { transform: translateX(4px) scale(0.92); border-color: #ff453a; }
80% { transform: translateX(-1.5px) scale(1.05); }
}
.pc-dot.wave-shake { animation: dotWaveShake 0.4s ease; }
"""

ANIM_CSS_2 = r"""
.qp-input {
width: 100%; box-sizing: border-box; background: #fff;
border: 1.5px solid rgba(60,60,67,0.18); border-radius: 13px;
padding: 13px 14px; font-size: 15px; color: #000; outline: none;
transition: border-color 0.2s ease, background 0.2s ease;
caret-color: #0a84ff;
}
.qp-input:focus { border-color: #0a84ff; background: rgba(10,132,255,0.05); }
.qp-input-wrap {
position: relative; width: 100%; box-sizing: border-box;
background: #fff; border: 1.5px solid rgba(60,60,67,0.18); border-radius: 13px;
overflow: hidden; transition: border-color 0.2s ease, background 0.2s ease;
}
.qp-input-wrap:focus-within { border-color: #0a84ff; background: rgba(10,132,255,0.05); }
.qp-input-wrap .qp-input {
position: relative; z-index: 3; width: 100%;
background: transparent !important; border: none !important; border-radius: 0;
caret-color: transparent;
}
.qp-sel-highlight {
position: absolute; top: 6px; bottom: 6px; z-index: 1;
background: rgba(10,132,255,0.28); border-radius: 3px;
pointer-events: none; display: none;
}
.qp-caret {
position: absolute; top: 7px; bottom: 7px; width: 1.6px; z-index: 2;
background: #0a84ff; border-radius: 1px; pointer-events: none; display: none;
animation: qp-caret-blink 1s steps(1, end) infinite;
}
@keyframes qp-caret-blink {
0%, 49% { opacity: 1; }
50%, 100% { opacity: 0; }
}
.qp-select-menu {
position: absolute; z-index: 900; display: none; flex-direction: row;
background: rgba(45,45,50,0.92); backdrop-filter: blur(14px); -webkit-backdrop-filter: blur(14px);
border-radius: 10px; box-shadow: 0 8px 22px rgba(0,0,0,0.35);
overflow: hidden; animation: qp-menu-pop 0.15s var(--ios-spring-snappy);
}
.qp-select-menu::after {
content: ''; position: absolute; left: var(--qp-arrow-x, 50%); bottom: -6px;
transform: translateX(-50%); border: 6px solid transparent;
border-top-color: rgba(45,45,50,0.92);
}
.qp-select-menu.qp-menu-below::after {
bottom: auto; top: -6px; border-top-color: transparent; border-bottom-color: rgba(45,45,50,0.92);
}
.qp-select-menu-item {
padding: 9px 14px; font-size: 13.5px; font-weight: 600; color: #fff;
white-space: nowrap; cursor: pointer; touch-action: manipulation;
border-right: 1px solid rgba(255,255,255,0.15);
}
.qp-select-menu-item:last-child { border-right: none; }
.qp-select-menu-item:active { background: rgba(255,255,255,0.15); }
@keyframes qp-menu-pop {
from { opacity: 0; transform: scale(0.85); }
to { opacity: 1; transform: scale(1); }
}
#vkeyboard {
position: absolute; left: 0; right: 0; bottom: 0; z-index: 700;
background: rgba(28,28,32,0.98); backdrop-filter: blur(10px);
border-top: 1px solid rgba(255,255,255,0.08);
padding: 8px 5px calc(8px + env(safe-area-inset-bottom, 0px));
transform: translateY(105%); transition: transform 0.32s var(--ios-spring-snappy);
box-shadow: 0 -6px 20px rgba(0,0,0,0.4);
display: flex; flex-direction: column; gap: 7px;
}
#vkeyboard.vkb-open { transform: translateY(0); }
.vkb-row { display: flex; gap: 6px; width: 100%; }
.vkb-key {
flex: 1; min-width: 0; text-align: center; padding: 13px 0;
background: #3a3a3e; color: #fff; border-radius: 7px;
font-size: 15px; font-weight: 500; cursor: pointer; user-select: none;
box-shadow: 0 1px 0 rgba(0,0,0,0.4); transition: background 0.1s ease;
touch-action: manipulation;
}
.vkb-key:active { background: #55555a; }
.vkb-special { background: #232326; color: #eaeaea; font-size: 13px; }
.vkb-special:active { background: #38383c; }
.vkb-special .vkb-active { background: #6a6a70; }
.vkb-space { background: #313135; }
.vkb-done { background: #0a84ff !important; color: #fff; font-weight: 700; }
.vkb-done:active { background: #0060cc !important; }
#status-bar,
#dynamic-island,
#control-center-hitbox,
#control-center,
#home-indicator-hitbox { z-index: 2147483000 !important; }

/* ===== Dem nguoc Pass Token Penalty hien NGAY TRONG Dynamic Island =====
   Truoc day day la 1 khung rieng noi "gan" ben duoi island; gio no la 1 lop
   noi dung (#content-penalty) that su nam trong #dynamic-island, dung dung
   co che "Live Activity" (state-penalty) giong nhu khi co cuoc goi den - chi
   khac la khong chiem quyen cua canh bao/Face ID/cuoc goi (uu tien thap hon,
   xem canShowPenaltyIsland() trong PENALTY_TOKEN_JS). Chi hien khi dang o
   trong app Penalty va con phien token hop le; tu dong an ngay khi roi khoi
   app Penalty. Phan style vi tri/kich thuoc pill (.state-penalty) va layout
   noi dung (#content-penalty) nam cung nhom voi cac state khac cua island. */
#content-penalty i { color: #6dffb0; font-size: 12px; animation: penaltyBadgePulse 1.4s ease-in-out infinite; }
#content-penalty span { color: #eafff2; font-size: 12.5px; font-weight: 800; letter-spacing: 0.5px; font-variant-numeric: tabular-nums; }
.penalty-warn#dynamic-island #content-penalty i { color: #ff8a8a; }
.penalty-warn#dynamic-island #content-penalty span { color: #ffb3b3; }
@keyframes penaltyBadgePulse { 0%, 100% { opacity: 0.65; transform: scale(1); } 50% { opacity: 1; transform: scale(1.18); } }
"""

ANIM_BODY_1 = r"""
<div id="home-screen">
  <div class="pages-wrapper" id="pages-wrapper">
    <div class="page" id="page-0">
      <div class="app-grid"><div class="app-icon" onclick="handlePenaltyIconTap(this);">
        <div class="app-box penalty-app-box">
          <svg viewBox="0 0 68 68" xmlns="http://www.w3.org/2000/svg">
            <defs>
              <linearGradient id="penaltyGrad" x1="0" y1="0" x2="1" y2="1">
                <stop offset="0%" stop-color="#27c96b"/>
                <stop offset="55%" stop-color="#0f9350"/>
                <stop offset="100%" stop-color="#0a6b3a"/>
              </linearGradient>
            </defs>
            <rect width="68" height="68" rx="16" fill="url(#penaltyGrad)"/>
            <rect x="1" y="1" width="66" height="66" rx="15" fill="none" stroke="rgba(255,255,255,0.14)" stroke-width="1.5"/>
            <path d="M15 47 L15 19 L53 19 L53 47" fill="none" stroke="#ffffff" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" opacity="0.95"/>
            <g stroke="#ffffff" stroke-opacity="0.5" stroke-width="1">
              <line x1="15" y1="25" x2="53" y2="25"/>
              <line x1="15" y1="31" x2="53" y2="31"/>
              <line x1="15" y1="37" x2="53" y2="37"/>
              <line x1="15" y1="43" x2="53" y2="43"/>
              <line x1="21.7" y1="19" x2="21.7" y2="47"/>
              <line x1="28.3" y1="19" x2="28.3" y2="47"/>
              <line x1="34" y1="19" x2="34" y2="47"/>
              <line x1="39.7" y1="19" x2="39.7" y2="47"/>
              <line x1="46.3" y1="19" x2="46.3" y2="47"/>
            </g>
            <ellipse cx="34" cy="59" rx="10" ry="2.4" fill="rgba(0,0,0,0.28)"/>
            <circle cx="34" cy="52" r="7.5" fill="#fdfdfd"/>
            <circle cx="34" cy="52" r="7.5" fill="none" stroke="rgba(0,0,0,0.12)" stroke-width="1"/>
            <path d="M34 47.3l3.1 2.2-1.2 3.6h-3.8l-1.2-3.6z" fill="#161616"/>
            <path d="M29.2 49.6l1.7 1.3M38.8 49.6l-1.7 1.3M31.6 56.4l0.8-2M36.4 56.4l-0.8-2" stroke="#161616" stroke-width="1" stroke-linecap="round"/>
          </svg>
        </div>
        <span class="app-label">Penalty</span>
      </div>
      <div class="app-icon" id="tool-app-icon" onclick="openAppFromIcon('app-tool', this); trackApp('app-tool');">
        <div class="app-box magicai-app-box">
          <svg viewBox="0 0 68 68" aria-hidden="true" xmlns="http://www.w3.org/2000/svg">
            <defs><linearGradient id="magicai-icon-bg" x2="1" y2="1"><stop stop-color="#192840"/><stop offset="1" stop-color="#070c18"/></linearGradient><linearGradient id="magicai-icon-light" x2="1" y2="1"><stop stop-color="#b5ffe5"/><stop offset=".5" stop-color="#63e8be"/><stop offset="1" stop-color="#8fa9ff"/></linearGradient></defs>
            <rect width="68" height="68" rx="17" fill="url(#magicai-icon-bg)"/><rect x="1" y="1" width="66" height="66" rx="16" fill="none" stroke="#b1fbe938"/>
            <path d="M34 12 54 24v22L34 57 14 46V24Z" fill="#72efd90b" stroke="url(#magicai-icon-light)" stroke-width="1.5"/>
            <path d="M23 44V26l11 12 11-12v18" fill="none" stroke="url(#magicai-icon-light)" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>
            <circle cx="34" cy="12" r="3" fill="#bdffe6"/><circle cx="54" cy="46" r="2" fill="#94aaff"/>
          </svg>
        </div><span class="app-label">MAGICAI</span>
      </div>
      <div class="app-icon" id="admin-app-icon" style="display:none;" onclick="openAppFromIcon('app-admin', this); trackApp('app-admin'); openAdminApp();">
        <div class="app-box admin-app-box">
          <svg viewBox="0 0 68 68" xmlns="http://www.w3.org/2000/svg">
            <defs>
              <linearGradient id="adminIconGrad" x1="0" y1="0" x2="1" y2="1">
                <stop offset="0%" stop-color="#39ffb2"/>
                <stop offset="55%" stop-color="#0fae55"/>
                <stop offset="100%" stop-color="#052e1c"/>
              </linearGradient>
              <radialGradient id="adminGlow" cx="50%" cy="35%" r="70%">
                <stop offset="0%" stop-color="rgba(57,255,178,0.55)"/>
                <stop offset="100%" stop-color="rgba(57,255,178,0)"/>
              </radialGradient>
            </defs>
            <rect width="68" height="68" rx="16" fill="#04140b"/>
            <rect width="68" height="68" rx="16" fill="url(#adminGlow)"/>
            <rect x="1.2" y="1.2" width="65.6" height="65.6" rx="15" fill="none" stroke="url(#adminIconGrad)" stroke-width="2"/>
            <g font-family="Courier New, monospace" font-weight="700">
              <text x="14" y="41" font-size="21" fill="#39ffb2">&gt;</text>
              <rect x="30" y="30" width="11" height="14" fill="#39ffb2"/>
            </g>
            <line x1="12" y1="50" x2="56" y2="50" stroke="rgba(57,255,178,0.35)" stroke-width="1.4"/>
            <circle cx="14" cy="14" r="2.4" fill="#ff5f56"/>
            <circle cx="21" cy="14" r="2.4" fill="#ffbd2e"/>
            <circle cx="28" cy="14" r="2.4" fill="#27c93f"/>
          </svg>
        </div>
        <span class="app-label">Admin</span>
      </div>
      </div>
    </div>
    <div class="page" id="page-1">
      <div class="app-grid"><div class="app-icon" id="bank-app-icon" onclick="openAppFromIcon('app-bank', this); trackApp('app-bank');">
        <div class="app-box bk-app-box">
          <svg viewBox="0 0 68 68" xmlns="http://www.w3.org/2000/svg">
            <defs><linearGradient id="bankIconGrad" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="#39e6c4"/><stop offset="100%" stop-color="#0a2647"/></linearGradient></defs>
            <rect width="68" height="68" rx="17" fill="url(#bankIconGrad)"/>
            <rect x="1" y="1" width="66" height="66" rx="16" fill="none" stroke="rgba(255,255,255,0.18)"/>
            <path d="M34 14 58 27H10Z" fill="#ffffff" opacity="0.92"/>
            <rect x="16" y="31" width="6" height="20" fill="#ffffff" opacity="0.92"/>
            <rect x="31" y="31" width="6" height="20" fill="#ffffff" opacity="0.92"/>
            <rect x="46" y="31" width="6" height="20" fill="#ffffff" opacity="0.92"/>
            <rect x="10" y="53" width="48" height="6" rx="2" fill="#ffffff" opacity="0.92"/>
          </svg>
        </div>
        <span class="app-label">MagicBank</span>
      </div>
      <div class="app-icon" id="store-app-icon" onclick="openAppFromIcon('app-store', this); trackApp('app-store');">
        <div class="app-box st-app-box">
          <svg viewBox="0 0 68 68" xmlns="http://www.w3.org/2000/svg">
            <defs><linearGradient id="storeIconGrad" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="#ffcf3f"/><stop offset="100%" stop-color="#a06bff"/></linearGradient></defs>
            <rect width="68" height="68" rx="17" fill="url(#storeIconGrad)"/>
            <rect x="1" y="1" width="66" height="66" rx="16" fill="none" stroke="rgba(255,255,255,0.18)"/>
            <path d="M14 22h40l-3 10H17Z" fill="#2b1600" opacity="0.85"/>
            <rect x="17" y="32" width="34" height="20" rx="3" fill="#2b1600" opacity="0.85"/>
            <circle cx="27" cy="32" r="4" fill="none" stroke="#ffcf3f" stroke-width="2.4"/>
            <circle cx="41" cy="32" r="4" fill="none" stroke="#ffcf3f" stroke-width="2.4"/>
          </svg>
        </div>
        <span class="app-label">Cua Hang</span>
      </div></div>
    </div>
  </div>
  <div class="page-dots">
    <div class="page-dot active"></div>
    <div class="page-dot"></div>
  </div>
  <div id="dock" style="justify-content:flex-start;">
    <div class="app-icon" style="margin-left:18px; margin-right:auto;" onclick="openAppFromIcon('app-phone', this); trackApp('app-phone');">
      <div class="app-box phone-app-box">
        <svg viewBox="0 0 68 68" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <linearGradient id="phoneGrad" x1="0" y1="0" x2="1" y2="1">
              <stop offset="0%" stop-color="#6bdb8f"/>
              <stop offset="55%" stop-color="#30d158"/>
              <stop offset="100%" stop-color="#1a8f42"/>
            </linearGradient>
          </defs>
          <rect width="68" height="68" rx="16" fill="url(#phoneGrad)"/>
          <rect x="1" y="1" width="66" height="66" rx="15" fill="none" stroke="rgba(255,255,255,0.16)" stroke-width="1.5"/>
          <g transform="translate(17.2,14.8) scale(0.075)">
            <path fill="#ffffff" d="M164.9 24.6c-7.7-18.6-28-28.5-47.4-23.2l-88 24C12.1 30.2 0 46 0 64C0 313.6 198.4 512 448 512c18 0 33.9-12.1 38.6-29.5l24-88c5.3-19.4-4.6-39.7-23.2-47.4l-96-40c-16.3-6.8-35.2-2.1-46.3 11.6l-40.4 49.3c-70.4-33.3-127.4-90.3-160.7-160.7l49.3-40.4c13.7-11.2 18.4-30 11.6-46.3l-40-96z"/>
          </g>
        </svg>
      </div>
    </div>
  </div>
</div>
<div id="lock-screen-wrapper">
  <div id="lock-screen-ui">
    <div class="ls-date" id="ls-date">Thứ Tư, 1 tháng 4</div>
    <div class="ls-time" id="ls-time">09:41</div>
    <div class="ls-notif-toolbar">
      <button type="button" class="ls-notif-clearall" id="ls-notif-clearall" onclick="event.stopPropagation();clearAllNotifications()" aria-label="Xóa tất cả thông báo">
        <i class="fa-solid fa-trash-can"></i><span>Xóa tất cả</span>
      </button>
    </div>
    <div class="ls-notif-list" id="ls-notif-list"></div>
    <button type="button" class="ls-quick-btn ls-btn-left" id="lock-flash-btn" aria-label="Đèn pin" onclick="showWarning(event)">
      <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor">
        <path d="M7 2h10v3H7V2zm-1 4h12v2c0 1.1-.9 2-2 2h-8c-1.1 0-2-.9-2-2V6zm1.5 5h9c.8 0 1.5.7 1.5 1.5v8.5c0 1.4-1.1 2.5-2.5 2.5h-7c-1.4 0-2.5-1.1-2.5-2.5v-8.5c0-.8.7-1.5 1.5-1.5zM12 14c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2z"/>
      </svg>
    </button>
    <button type="button" class="ls-quick-btn ls-btn-right" id="lock-camera-btn" aria-label="Camera" onclick="showWarning(event)"><i class="fa-solid fa-camera"></i></button>
  </div>
  <div id="passcode-ui">
    <div class="pc-title" id="pc-title">Nhập mật mã</div>
    <div class="pc-dots" id="pc-dots">
      <div class="pc-dot"></div><div class="pc-dot"></div><div class="pc-dot"></div>
      <div class="pc-dot"></div><div class="pc-dot"></div><div class="pc-dot"></div>
    </div>
    <div class="pc-numpad">
      <div class="pc-btn" onclick="pressKey(1)"><div class="pc-num">1</div><div class="pc-letters"></div></div>
      <div class="pc-btn" onclick="pressKey(2)"><div class="pc-num">2</div><div class="pc-letters">ABC</div></div>
      <div class="pc-btn" onclick="pressKey(3)"><div class="pc-num">3</div><div class="pc-letters">DEF</div></div>
      <div class="pc-btn" onclick="pressKey(4)"><div class="pc-num">4</div><div class="pc-letters">GHI</div></div>
      <div class="pc-btn" onclick="pressKey(5)"><div class="pc-num">5</div><div class="pc-letters">JKL</div></div>
      <div class="pc-btn" onclick="pressKey(6)"><div class="pc-num">6</div><div class="pc-letters">MNO</div></div>
      <div class="pc-btn" onclick="pressKey(7)"><div class="pc-num">7</div><div class="pc-letters">PQRS</div></div>
      <div class="pc-btn" onclick="pressKey(8)"><div class="pc-num">8</div><div class="pc-letters">TUV</div></div>
      <div class="pc-btn" onclick="pressKey(9)"><div class="pc-num">9</div><div class="pc-letters">WXYZ</div></div>
      <div class="pc-action" onclick="cancelPasscode()">Hủy</div>
      <div class="pc-btn" onclick="pressKey(0)"><div class="pc-num">0</div><div class="pc-letters"></div></div>
      <div class="pc-btn empty"></div>
    </div>
  </div>
</div>
<div id="pt-modal-overlay">
  <div class="pt-card">
    <div class="pt-check-overlay" id="pt-check-overlay">
      <div class="pt-check-circle"><svg viewBox="0 0 24 24"><path d="M4 12l5 5L20 6"/></svg></div>
    </div>
    <div class="pt-icon-wrap"><i class="fa-solid fa-key"></i></div>
    <div class="pt-title">Nhập Pass Token</div>
    <div class="pt-sub">Nhập vô đây</div>
    <div class="pt-input-wrap" id="pt-input-wrap">
      <input type="text" id="pt-input" class="pt-input" placeholder="TOKEN" autocomplete="off" autocapitalize="characters" maxlength="24" onkeydown="if(event.key==='Enter'){confirmPassToken();}">
    </div>
    <div class="pt-msg" id="pt-msg"></div>
    <div class="pt-actions">
      <button type="button" class="pt-btn pt-btn-confirm" id="pt-confirm-btn" onclick="confirmPassToken()"><span class="pt-lbl">Xác Nhận</span><span class="pt-spin"></span></button>
      <button type="button" class="pt-btn pt-btn-cancel" onclick="cancelPassToken()">Hủy</button>
    </div>
  </div>
</div>
"""

ANIM_JS_1 = r"""
const lockWrapper = document.getElementById('lock-screen-wrapper');
const lockUI = document.getElementById('lock-screen-ui');
const passcodeUI = document.getElementById('passcode-ui');
let lsStartY = 0; let isLsDragging = false; let isPasscodeMode = false;
let lsStartX = 0, lsGestureStartedAt = 0;
function beginLockSwipe(x, y) {
  if (document.body.classList.contains('unlocked') || isPasscodeMode || unlockBusy) return false;
  lsStartX = x; lsStartY = y; lsGestureStartedAt = performance.now(); isLsDragging = true;
  lockUI.style.transition = 'none'; lockWrapper.style.transition = 'none';
  return true;
}
function moveLockSwipe(x, y) {
  if (!isLsDragging || isPasscodeMode) return;
  const up = Math.max(0, lsStartY-y);
  const horizontal = Math.abs(x-lsStartX);
  const progress = horizontal > up ? 0 : Math.min(up/190, 1);
  lockUI.style.transform = `translateY(${-up * (horizontal > up ? 0 : .45)}px) scale(${1-progress*.045})`;
  lockUI.style.opacity = String(1-progress*.85);
  lockWrapper.style.backdropFilter = `blur(${progress*22}px)`;
  lockWrapper.style.background = `rgba(0,0,0,${progress*.42})`;
}
function openLockPasscode() {
  if (document.body.classList.contains('unlocked') || isPasscodeMode || unlockBusy) return;
  closeControlCenter();
  lockWrapper.style.transition = 'backdrop-filter .42s ease, background .42s ease';
  lockUI.style.transition = 'opacity .3s ease, transform .48s var(--ios-spring-snappy)';
  lockWrapper.style.backdropFilter = 'blur(25px)'; lockWrapper.style.background = 'rgba(0,0,0,.6)';
  lockUI.style.transform = 'translateY(-150px) scale(.95)'; lockUI.style.opacity = '0'; lockUI.style.pointerEvents = 'none';
  passcode = []; updateDots(); pcTitle.innerText = 'Nhập mật mã';
  passcodeUI.style.opacity = '1'; passcodeUI.style.pointerEvents = 'auto';
  passcodeUI.style.transform = 'scale(1)'; passcodeUI.style.filter = 'blur(0px)';
  isPasscodeMode = true;
  document.getElementById('island-lock-icon').style.opacity = '1';
  document.getElementById('island-lock-icon').style.transform = 'scale(1)';
  document.getElementById('island-camera').style.transform = 'translateX(12px)';
}
function finishLockSwipe(x, y, cancelled = false) {
  if (!isLsDragging) return;
  isLsDragging = false;
  const up = lsStartY-y, sideways = Math.abs(x-lsStartX);
  const elapsed = Math.max(1, performance.now()-lsGestureStartedAt);
  if (!cancelled && up > sideways * 1.15 && (up >= 64 || (up >= 28 && up/elapsed > .45))) {
    openLockPasscode();
  } else {
    lockUI.style.transition = 'transform .45s var(--ios-spring-snappy), opacity .3s ease';
    lockWrapper.style.transition = 'backdrop-filter .35s ease, background .35s ease';
    lockUI.style.transform = 'translateY(0) scale(1)'; lockUI.style.opacity = '1';
    lockWrapper.style.backdropFilter = 'blur(0px)'; lockWrapper.style.background = 'transparent';
  }
}
lockUI.addEventListener('touchstart', e => {
  if (e.target.closest('.ls-notif-list, .ls-quick-btn') || e.touches.length !== 1) return;
  beginLockSwipe(e.touches[0].clientX, e.touches[0].clientY);
}, {passive:true});
lockUI.addEventListener('touchmove', e => {
  if (!isLsDragging) return;
  if (e.cancelable) e.preventDefault();
  moveLockSwipe(e.touches[0].clientX, e.touches[0].clientY);
}, {passive:false});
lockUI.addEventListener('touchend', e => {
  const touch = e.changedTouches[0];
  if (touch) finishLockSwipe(touch.clientX,touch.clientY);
}, {passive:true});
lockUI.addEventListener('touchcancel', () => finishLockSwipe(lsStartX,lsStartY,true), {passive:true});


let passcode = [];
const dots = document.querySelectorAll('.pc-dot');
const passcodeScreen = document.getElementById('passcode-ui');
const pcTitle = document.getElementById('pc-title');
function pressKey(num) {
  if (unlockBusy) return;
  if (passcode.length < 6) {
    passcode.push(num);
    updateDots();
    if (passcode.length === 6) checkPasscode();
  }
}
function cancelPasscode() {
  unlockGeneration++; unlockBusy = false;
  passcode = []; updateDots(); pcTitle.innerText = "Nhập mật mã";
  lockWrapper.style.backdropFilter = 'blur(0px)'; lockWrapper.style.background = 'transparent';
  lockUI.style.transform = `translateY(0)`; lockUI.style.opacity = '1'; lockUI.style.pointerEvents = 'auto';
  passcodeUI.style.opacity = '0'; passcodeUI.style.pointerEvents = 'none'; passcodeUI.style.transform = 'scale(0.85)'; passcodeUI.style.filter = 'blur(15px)'; isPasscodeMode = false;
  document.getElementById('island-lock-icon').style.opacity = '0'; document.getElementById('island-lock-icon').style.transform = 'scale(0.5)'; document.getElementById('island-camera').style.transform = 'translateX(0)';
}
function updateDots() {
  dots.forEach((dot, index) => {
    if (index < passcode.length) dot.classList.add('filled'); else dot.classList.remove('filled');
  });
}
/* ===== Phan hoi co hoc khi nhan phim so (lun xuong ngay, nay nhe khi tha) ===== */
(function(){
  const pcNumpadEl = document.querySelector('.pc-numpad');
  if (!pcNumpadEl) return;
  const clearAllPressed = () => {
    pcNumpadEl.querySelectorAll('.key-pressed').forEach(b => b.classList.remove('key-pressed'));
  };
  pcNumpadEl.addEventListener('pointerdown', (e) => {
    const btn = e.target.closest('.pc-btn:not(.empty), .pc-action');
    if (btn) btn.classList.add('key-pressed');
  });
  ['pointerup', 'pointerleave', 'pointercancel'].forEach((evt) => {
    pcNumpadEl.addEventListener(evt, (e) => {
      const btn = e.target.closest('.pc-btn:not(.empty), .pc-action');
      if (btn) btn.classList.remove('key-pressed'); else clearAllPressed();
    });
  });
})();
let adminModeUnlocked = false;
function completePasscode() {
  const code = passcode.join('');
  if (code === '000000' || code === '081120') {
    const isAdminCode = (code === '081120');
    adminModeUnlocked = isAdminCode;
    // Ghi lai "danh tinh" hien tai vao localStorage de app Dien thoai (chay
    // trong iframe rieng, khong cung document) co the doc duoc: dung de quyet
    // dinh MAZI SIM nao (cua Nha phat trien hay cua nguoi dung) se hien ra
    // khi quay *101#.
    try { localStorage.setItem('magicos_admin_mode', isAdminCode ? '1' : '0'); } catch (e) {}
    const adminIconEl = document.getElementById('admin-app-icon');
    if (adminIconEl) adminIconEl.style.display = isAdminCode ? 'flex' : 'none';
    triggerFaceID(true); pcTitle.innerText = "Đang mở khóa...";
    document.getElementById('island-lock-icon').style.opacity = '0'; document.getElementById('island-lock-icon').style.transform = 'scale(0.5)'; document.getElementById('island-camera').style.transform = 'translateX(0)';
    const unlockAttempt = unlockGeneration;
    setTimeout(async () => {
      if (unlockAttempt !== unlockGeneration) return;
      if (!isAdminCode) {
        try {
          const state = await serverRequest('/api/server-state');
          applyServerState(state);
          if (!state.open) { passcode = []; updateDots(); showMaintenance(); return; }
        } catch (e) { unlockBusy = false; passcode = []; updateDots(); pcTitle.innerText = 'Không thể kết nối server'; resetIsland(); return; }
      }
      if (unlockAttempt !== unlockGeneration) return;
      const homeScreenEl = document.getElementById('home-screen');
      // Cho home screen "nay" nhe (spring bounce) khi xuat hien thay vi hien cung ngac
      homeScreenEl.classList.add('home-spring-in');
      homeScreenEl.style.display = 'block';
      document.getElementById('home-indicator-hitbox').style.display = 'block';
      document.body.classList.add('unlocked');
      // QUAN TRONG: phai tat co man hinh nhap mat ma khi da mo khoa. Truoc day co nay
      // bi ket o true mai mai -> cac chot chan "dang nhap mat ma" cua Control Center /
      // thanh thong bao chan luon ca o man hinh chinh va trong cac app.
      isPasscodeMode = false;
      // Nay tung icon app rieng le (do tre tang dan) giong hieu ung mo khoa iOS thuc
      const homeIconsToPop = homeScreenEl.querySelectorAll('.app-icon');
      homeIconsToPop.forEach((icon, i) => { icon.style.animationDelay = Math.min(i * 28, 480) + 'ms'; });
      void homeScreenEl.offsetWidth;
      homeScreenEl.classList.remove('home-spring-in');
      homeScreenEl.classList.add('home-icons-animate');
      setTimeout(() => {
        homeScreenEl.classList.remove('home-icons-animate');
        homeIconsToPop.forEach((icon) => { icon.style.animationDelay = ''; });
      }, 1300);
      lockWrapper.style.transition = 'transform 0.8s var(--ios-smooth)';
      lockWrapper.style.transform = 'translateY(-100%)';
      setTimeout(() => { if (unlockAttempt !== unlockGeneration) return; lockWrapper.style.display = 'none'; resetIsland(); unlockBusy = false; }, 800);
    }, 2600);
  } else {
    dots.forEach((dot, i) => {
      dot.style.animationDelay = (i * 45) + 'ms';
      dot.classList.add('wave-shake');
    });
    pcTitle.innerText = "Mật mã sai";
    setTimeout(() => {
      dots.forEach((dot) => { dot.classList.remove('wave-shake'); dot.style.animationDelay = ''; });
      passcode = []; updateDots(); pcTitle.innerText = "Nhập mật mã";
    }, dots.length * 45 + 420);
  }
}
"""

ANIM_JS_2 = r"""
let activeAppsList = [];
let historyPointer = -1;
/* Id cua app dang thuc su hien tren man hinh (khong phu thuoc animation/CSS
   display, vi cac hieu ung dong/mo app co do tre - doc DOM ngay luc do se sai).
   null nghia la dang o man hinh chinh (home) / khong co app nao dang mo. */
let foregroundAppId = null;
function closeKeypad() {
  if (typeof window.__closeVKeyboard === 'function') window.__closeVKeyboard();
}
function trackApp(appId) {
  let idx = activeAppsList.indexOf(appId);
  if (idx > -1) activeAppsList.splice(idx, 1);
  activeAppsList.push(appId);
  historyPointer = activeAppsList.length - 1;
  foregroundAppId = appId;
  if (window.penaltyUpdateBadge) window.penaltyUpdateBadge();
  if (typeof applyCallIslandState === 'function') applyCallIslandState();
}
const appOriginIcons = {};
const ICON_BOX_RADIUS = 16;
const LIGHT_BACKGROUND_APPS = new Set(['app-phone']);
// true khi app Dien thoai dang hien man hinh cuoc goi (nen toi den: dang do
// chuong / dang goi / dang trong cuoc), false khi dang hien ban phim/danh ba
// (nen sang). Duoc set DONG BO ngay tai noi chuyen man hinh trong PHONE_APP_JS,
// khong dung activeCallState (cap nhat qua postMessage nen den tre 1 nhip).
let phoneCallScreenActive = false;
function applyStatusBarTheme(appId) {
  const statusBar = document.getElementById('status-bar');
  if (!statusBar) return;
  const controlCenterEl = document.getElementById('control-center');
  const homeIndicatorEl = document.getElementById('home-indicator');
  // App Dien thoai co 2 giao dien nen rat khac nhau: ban phim/danh ba (nen
  // sang -> can status bar toi/den) va man hinh cuoc goi dang goi/dang nghe
  // (nen toi den -> can status bar sang/trang). Chi dua vao appId la khong du,
  // vi cac ham nhu ensureTopAppVisible/switcherResumeApp/navigateAppHistory
  // deu goi lai ham nay voi appId = 'app-phone' ke ca khi dang o man hinh cuoc
  // goi (vd: mo App Switcher roi quay lai man hinh cuoc goi) -> lam status bar
  // bi ep ve mau den, "den tren nen den" khong doc duoc.
  // LUU Y: man hinh cuoc goi (phone-app.html) chay trong 1 iframe rieng, KHONG
  // cung window voi trang nay, nen no bao trang thai qua postMessage; bien
  // phoneCallScreenActive duoc cap nhat trong listener message ben duoi ngay
  // khi nhan duoc, roi goi lai applyStatusBarTheme.
  const isPhoneCallUiActive = (typeof phoneCallScreenActive !== 'undefined') && !!phoneCallScreenActive;
  const useDarkStatusBar = appId && LIGHT_BACKGROUND_APPS.has(appId) && !(appId === 'app-phone' && isPhoneCallUiActive);
  if (useDarkStatusBar) {
    statusBar.classList.add('status-bar-dark-content');
    if (controlCenterEl) controlCenterEl.classList.add('status-bar-dark-content');
    if (homeIndicatorEl) homeIndicatorEl.classList.add('status-bar-dark-content');
  } else {
    statusBar.classList.remove('status-bar-dark-content');
    if (controlCenterEl) controlCenterEl.classList.remove('status-bar-dark-content');
    if (homeIndicatorEl) homeIndicatorEl.classList.remove('status-bar-dark-content');
  }
}
function openAppFromIcon(appId, iconEl) {
  if (appId === 'app-penalty' && window.penaltyStartFresh) window.penaltyStartFresh();
  applyStatusBarTheme(appId);
  const el = document.getElementById(appId);
  const container = document.getElementById('phone-container');
  if (!el) return;
  const iconBox = (iconEl && iconEl.querySelector) ? (iconEl.querySelector('.app-box') || iconEl) : null;
  if (!container || !iconBox) {
      el.style.display = 'block';
      el.style.animation = 'appOpenAnim 0.3s forwards';
      return;
  }
  appOriginIcons[appId] = iconBox;
  const iconRect = iconBox.getBoundingClientRect();
  const containerRect = container.getBoundingClientRect();
  const scaleX = Math.max(iconRect.width / containerRect.width, 0.001);
  const scaleY = Math.max(iconRect.height / containerRect.height, 0.001);
  const originX = iconRect.left - containerRect.left;
  const originY = iconRect.top - containerRect.top;
  const avgScale = (scaleX + scaleY) / 2;
  el.style.display = 'block';
  el.style.animation = 'none';
  el.style.transition = 'none';
  el.style.transformOrigin = '0 0';
  el.style.transform = `translate(${originX}px, ${originY}px) scale(${scaleX}, ${scaleY})`;
  el.style.borderRadius = (ICON_BOX_RADIUS / avgScale) + 'px';
  el.style.opacity = '0';
  el.style.filter = 'blur(6px)';
  void el.offsetWidth;
  el.style.transition = 'transform 0.38s var(--ios-smooth), border-radius 0.38s var(--ios-smooth), opacity 0.26s ease-out, filter 0.3s ease-out';
  requestAnimationFrame(() => {
      el.style.transform = 'translate(0px, 0px) scale(1, 1)';
      el.style.borderRadius = '0px';
      el.style.opacity = '1';
      el.style.filter = 'blur(0px)';
  });
  clearTimeout(el.__zoomCleanupTimer);
  el.__zoomCleanupTimer = setTimeout(() => { el.style.transition = ''; }, 400);
}
function closeAppToIcon(appId) {
  const el = document.getElementById(appId);
  const container = document.getElementById('phone-container');
  if (!el || el.style.display === 'none') return;
  const iconBox = appOriginIcons[appId];
  if (!container || !iconBox || !iconBox.isConnected) {
      el.style.transition = 'opacity 0.25s ease, transform 0.25s ease';
      el.style.opacity = '0';
      el.style.transform = 'scale(0.92)';
      setTimeout(() => {
          el.style.display = 'none';
          el.style.transition = ''; el.style.transform = ''; el.style.opacity = '';
          el.style.borderRadius = ''; el.style.filter = '';
      }, 260);
      return;
  }
  const iconRect = iconBox.getBoundingClientRect();
  const containerRect = container.getBoundingClientRect();
  const scaleX = Math.max(iconRect.width / containerRect.width, 0.001);
  const scaleY = Math.max(iconRect.height / containerRect.height, 0.001);
  const originX = iconRect.left - containerRect.left;
  const originY = iconRect.top - containerRect.top;
  const avgScale = (scaleX + scaleY) / 2;
  el.style.transformOrigin = '0 0';
  el.style.transition = 'transform 0.32s var(--ios-smooth), border-radius 0.32s var(--ios-smooth), opacity 0.28s ease-in, filter 0.28s ease-in';
  el.style.transform = `translate(${originX}px, ${originY}px) scale(${scaleX}, ${scaleY})`;
  el.style.borderRadius = (ICON_BOX_RADIUS / avgScale) + 'px';
  el.style.opacity = '0';
  el.style.filter = 'blur(6px)';
  clearTimeout(el.__zoomCleanupTimer);
  el.__zoomCleanupTimer = setTimeout(() => {
      el.style.display = 'none';
      el.style.transition = '';
      el.style.transform = '';
      el.style.borderRadius = '';
      el.style.opacity = '';
      el.style.filter = '';
  }, 330);
}
function closeAllApps() {
  applyStatusBarTheme(null);
  foregroundAppId = null;
  if (activeAppsList.length === 0) { closeKeypad(); if (typeof applyCallIslandState === 'function') applyCallIslandState(); return; }
  const topId = activeAppsList[historyPointer > -1 ? historyPointer : activeAppsList.length - 1];
  closeAppToIcon(topId);
  activeAppsList.forEach(function (id) {
      if (id === topId) return;
      const el = document.getElementById(id);
      if (el) el.style.display = 'none';
  });
  closeKeypad();
  if (typeof applyCallIslandState === 'function') applyCallIslandState();
}
function hardResetAllApps() {
  activeAppsList.forEach(id => {
    const el = document.getElementById(id);
    if (el) {
      el.style.display = 'none'; el.style.transform = ''; el.style.transition = '';
      el.style.opacity = ''; el.style.filter = ''; el.style.borderRadius = '';
    }
    // Bao cho tung app biet no vua bi DONG HAN (khac voi chi ve home man hinh,
    // von chi "dua app xuong nen" va giu nguyen trang thai/DOM) de lan mo lai
    // sau no chay lai dung tu dau, hien hieu ung loading/boot day du.
    document.dispatchEvent(new CustomEvent('magicos-app-terminated', { detail: { appId: id } }));
  });
  activeAppsList = [];
  historyPointer = -1;
  foregroundAppId = null;
  if (typeof applyCallIslandState === 'function') applyCallIslandState();
}
function navigateAppHistory(direction) {
  if (activeAppsList.length < 2) return;
  const newPointer = direction === 'back' ? historyPointer - 1 : historyPointer + 1;
  if (newPointer < 0 || newPointer >= activeAppsList.length) return;
  const currentId = activeAppsList[historyPointer];
  const nextId = activeAppsList[newPointer];
  historyPointer = newPointer;
  foregroundAppId = nextId;
  applyStatusBarTheme(nextId);
  const curEl = document.getElementById(currentId);
  const nextEl = document.getElementById(nextId);
  if (!curEl || !nextEl) return;
  curEl.style.transition = '';
  curEl.style.transform = '';
  curEl.style.display = 'none';
  nextEl.style.transition = '';
  nextEl.style.transform = '';
  nextEl.style.display = 'block';
  if (typeof applyCallIslandState === 'function') applyCallIslandState();
}
"""

ANIM_JS_3 = r"""
const bootScreen = document.getElementById('boot-screen');
const tapFullscreenHint = document.getElementById('tap-fullscreen-hint');
const phoneContainer = document.getElementById('phone-container');
const screenFadeOverlay = document.getElementById('screen-fade');
(function () {
  const wrap = document.getElementById('boot-particles');
  if (!wrap) return;
  for (let i = 0; i < 22; i++) {
    const p = document.createElement('div');
    p.className = 'boot-particle';
    p.style.left = (Math.random() * 100) + '%';
    p.style.animationDuration = (2.6 + Math.random() * 2.2) + 's';
    p.style.animationDelay = (Math.random() * 2.4) + 's';
    wrap.appendChild(p);
  }
})();
function attemptFullscreen() {
  if (document.fullscreenElement || document.webkitIsFullScreen) return;
  try {
    let elem = document.documentElement;
    if (elem.requestFullscreen) { elem.requestFullscreen().catch(err => console.log(err)); }
    else if (elem.webkitRequestFullscreen) { elem.webkitRequestFullscreen(); }
  } catch (error) { console.log(error); }
}
function showTapFullscreenHint() {
  if (tapFullscreenHint) tapFullscreenHint.classList.add('show');
}
function hideTapFullscreenHint() {
  if (tapFullscreenHint) tapFullscreenHint.classList.remove('show');
}
['click', 'touchend'].forEach(evt => {
  document.addEventListener(evt, () => {
    if (!document.fullscreenElement && !document.webkitIsFullScreen) {
      attemptFullscreen();
    }
  }, { passive: true });
});
document.addEventListener('fullscreenchange', () => { if (document.fullscreenElement) hideTapFullscreenHint(); });
document.addEventListener('webkitfullscreenchange', () => { if (document.webkitIsFullScreen) hideTapFullscreenHint(); });
function finishBoot() {
  phoneContainer.style.display = 'block';
  // Thanh da nhiem (home indicator) phai luon hien dien khi may da "bat" xong,
  // ke ca khi con dang o man hinh khoa (giong hanh vi iOS that) - truoc day
  // no chi duoc bat lai trong checkPasscode() nen sau khi khoi dong lai may
  // (reboot / mat toan man hinh) se bi "mat" cho toi khi mo khoa xong.
  document.getElementById('home-indicator-hitbox').style.display = 'block';
  bootScreen.classList.add('boot-warp');
  setTimeout(() => {
    bootScreen.classList.add('boot-hide');
    phoneContainer.classList.remove('boot-arrive');
    void phoneContainer.offsetWidth;
    phoneContainer.classList.add('boot-arrive');
    setTimeout(() => {
      bootScreen.style.display = 'none';
      bootScreen.classList.remove('boot-warp');
    }, 300);
  }, 560);
  showTapFullscreenHint();
  attemptFullscreen();
}
setTimeout(finishBoot, 2750);
function performFullReset() {
  isLsDragging = false; isNotifPeekOpen = false; setNotifSwipeHintVisible(true);

  unlockGeneration++; unlockBusy = false;
  showTapFullscreenHint();
  resetIsland();
  document.getElementById('home-screen').style.display = 'none';
  // Thanh da nhiem van duoc giu hien thi tren man hinh khoa (giong iOS that),
  // nen KHONG an no o day nua - chi an truoc do trong finishBoot() neu may
  // thuc su chua bat xong.
  document.getElementById('home-indicator-hitbox').style.display = 'block';
  applyStatusBarTheme(null);
  hardResetAllApps();
  closeKeypad();
  const controlCenterEl = document.getElementById('control-center');
  if (controlCenterEl) controlCenterEl.classList.remove('open', 'cc-animating');
  // Neu Control Center dang mo/dang duoc keo do khi lenh khoa may nay chay
  // (vd khoa giua chung), statusBar.style.opacity da tung bi dat ve '0' boi
  // openControlCenter()/prepareControlCenterForDrag() va se KET DINH mai o do
  // vi chi co closeControlCenter() moi tra no lai - neu khong reset thang o
  // day thi thanh trang thai (song wifi, pin...) se bi "mat tich" vinh vien
  // sau khi khoa may. Dong thoi don sach cac co keo con sot lai de lan vuot
  // Control Center/thanh thong bao tiep theo tren man hinh chinh khong bi
  // ket qua sai do trang thai cu de lai.
  statusBar.style.transition = '';
  statusBar.style.opacity = '';
  statusBar.style.pointerEvents = '';
  ccDragActive = false; isPeekDragActive = false; ccSwipingDown = false;
  if (screenFadeOverlay) screenFadeOverlay.classList.remove('active');
  document.body.classList.remove('unlocked');
  lockWrapper.style.display = 'block'; lockWrapper.style.transform = 'translateY(0)'; lockWrapper.style.backdropFilter = 'blur(0px)';
  lockWrapper.style.background = 'transparent'; lockUI.style.opacity = '1'; lockUI.style.pointerEvents = 'auto'; lockUI.style.filter = 'blur(0px)'; lockUI.style.transform = 'translateY(0)';
  passcodeUI.style.opacity = '0'; passcodeUI.style.pointerEvents = 'none'; passcodeUI.style.transform = 'scale(0.85)'; passcodeUI.style.filter = 'blur(15px)'; isPasscodeMode = false; passcode = []; updateDots(); pcTitle.innerText = "Nhập mật mã";
  document.getElementById('island-lock-icon').style.opacity = '0'; document.getElementById('island-lock-icon').style.transform = 'scale(0.5)'; document.getElementById('island-camera').style.transform = 'translateX(0)';
}
document.addEventListener('fullscreenchange', exitHandler);
document.addEventListener('webkitfullscreenchange', exitHandler);
function exitHandler() {
  if (!document.fullscreenElement && !document.webkitIsFullScreen) {
    performFullReset();
  }
}
function lockToLockScreen() {
  isLsDragging = false; isNotifPeekOpen = false; setNotifSwipeHintVisible(true);

  unlockGeneration++; unlockBusy = false;
  resetIsland();
  document.getElementById('home-screen').style.display = 'none';
  // Giu thanh da nhiem hien thi tren man hinh khoa (xem ghi chu o performFullReset).
  document.getElementById('home-indicator-hitbox').style.display = 'block';
  applyStatusBarTheme(null);
  hardResetAllApps();
  closeKeypad();
  const controlCenterEl = document.getElementById('control-center');
  if (controlCenterEl) controlCenterEl.classList.remove('open', 'cc-animating');
  // Xem ghi chu chi tiet o performFullReset() - phai chu dong tra statusBar
  // ve hien thi va don sach cac co keo Control Center/thong bao con sot lai,
  // neu khong wifi/pin co the "bien mat" vinh vien sau khi khoa may va viec
  // vuot Control Center/thanh thong bao o man hinh chinh co the bi ket qua
  // sai do trang thai cu.
  statusBar.style.transition = '';
  statusBar.style.opacity = '';
  statusBar.style.pointerEvents = '';
  ccDragActive = false; isPeekDragActive = false; ccSwipingDown = false;
  document.body.classList.remove('unlocked');
  lockWrapper.style.display = 'block'; lockWrapper.style.transform = 'translateY(0)'; lockWrapper.style.backdropFilter = 'blur(0px)';
  lockWrapper.style.background = 'transparent'; lockUI.style.opacity = '1'; lockUI.style.pointerEvents = 'auto'; lockUI.style.filter = 'blur(0px)'; lockUI.style.transform = 'translateY(0)';
  passcodeUI.style.opacity = '0'; passcodeUI.style.pointerEvents = 'none'; passcodeUI.style.transform = 'scale(0.85)'; passcodeUI.style.filter = 'blur(15px)'; isPasscodeMode = false; passcode = []; updateDots(); pcTitle.innerText = "Nhập mật mã";
  document.getElementById('island-lock-icon').style.opacity = '0'; document.getElementById('island-lock-icon').style.transform = 'scale(0.5)'; document.getElementById('island-camera').style.transform = 'translateX(0)';
}
function replayBootAnimation() {
  if (!bootScreen) return;
  bootScreen.style.display = 'flex';
  bootScreen.classList.remove('boot-hide');
  bootScreen.classList.remove('boot-warp');
  const nodes = bootScreen.querySelectorAll('*');
  bootScreen.style.animation = 'none';
  nodes.forEach((el) => { el.style.animation = 'none'; });
  void bootScreen.offsetWidth;
  bootScreen.style.animation = '';
  nodes.forEach((el) => { el.style.animation = ''; });
  setTimeout(finishBoot, 2750);
}
function rebootDevice() {
  closeControlCenter();
  if (screenFadeOverlay) screenFadeOverlay.classList.add('active');
  setTimeout(() => {
      lockToLockScreen();
      replayBootAnimation();
      setTimeout(() => {
          if (screenFadeOverlay) screenFadeOverlay.classList.remove('active');
      }, 150);
  }, 800);
}
const ccPowerBtn = document.querySelector('.cc-power-btn');
if (ccPowerBtn) ccPowerBtn.addEventListener('click', rebootDevice);
"""

ANIM1_JS_1 = r"""
const pagesWrapper = document.getElementById('pages-wrapper');
const pageDots = document.querySelectorAll('.page-dot');
let pageHomeStartX = 0; let currentPage = 0; let isDraggingPageWrapper = false; let pageSwipeStartTime = 0;
pagesWrapper.addEventListener('touchstart', (e) => {
  pageHomeStartX = e.touches[0].clientX;
  isDraggingPageWrapper = true;
  isPageSwiping = false;
  pageSwipeStartTime = Date.now();
  pagesWrapper.style.transition = 'none';
}, {passive: true});
pagesWrapper.addEventListener('touchmove', (e) => {
  if (!isDraggingPageWrapper) return;
  let currentX = e.touches[0].clientX;
  let deltaX = currentX - pageHomeStartX;
  if (Math.abs(deltaX) > 5) isPageSwiping = true;
  if ((currentPage === 0 && deltaX > 0) || (currentPage === 1 && deltaX < 0)) deltaX = deltaX * 0.3;
  let containerWidth = document.getElementById('home-screen').offsetWidth;
  let percentMoved = (deltaX / containerWidth) * 50;
  let baseTranslate = -(currentPage * 50);
  pagesWrapper.style.transform = `translate3d(${baseTranslate + percentMoved}%, 0, 0)`;
}, {passive: true});
pagesWrapper.addEventListener('touchend', (e) => {
  if (!isDraggingPageWrapper) return;
  isDraggingPageWrapper = false;
  let currentX = e.changedTouches[0].clientX;
  let deltaX = currentX - pageHomeStartX;
  let timeElapsed = Date.now() - pageSwipeStartTime;
  let velocity = Math.abs(deltaX) / timeElapsed;
  if (Math.abs(deltaX) > 50 || velocity > 0.5) {
      if (deltaX < 0 && currentPage < 1) currentPage++;
      else if (deltaX > 0 && currentPage > 0) currentPage--;
  }
  pagesWrapper.style.transition = 'transform 0.4s var(--ios-spring-snappy)';
  pagesWrapper.style.transform = `translate3d(-${currentPage * 50}%, 0, 0)`;
  pageDots.forEach((dot, index) => {
      dot.classList.toggle('active', index === currentPage);
  });
  setTimeout(() => { isPageSwiping = false; }, 50);
});
const autoFitTargets = [];
function fitTextToBox(el) {
  if (!el) return;
  if (!el.dataset.fitBase) {
    el.dataset.fitBase = parseFloat(getComputedStyle(el).fontSize) || 16;
    autoFitTargets.push(el);
  }
  const maxFont = parseFloat(el.dataset.fitBase);
  const minFont = maxFont * 0.5;
  let fontSize = maxFont;
  el.style.fontSize = fontSize + 'px';
  const isOverflowing = () => el.scrollWidth > el.clientWidth + 1;
  let guard = 0;
  while (isOverflowing() && fontSize > minFont && guard < 60) {
    fontSize -= 0.5;
    el.style.fontSize = fontSize + 'px';
    guard++;
  }
}
function refitAllAutoFitTargets() {
  autoFitTargets.forEach(fitTextToBox);
}
window.addEventListener('resize', () => {
  clearTimeout(window.__fitResizeTimer);
  window.__fitResizeTimer = setTimeout(refitAllAutoFitTargets, 150);
});
(function setupVirtualKeyboard() {
  const KB_LETTERS = [
    ['q','w','e','r','t','y','u','i','o','p'],
    ['a','s','d','f','g','h','j','k','l'],
    ['shift','z','x','c','v','b','n','m','back']
  ];
  const KB_NUMS = [
    ['1','2','3','4','5','6','7','8','9','0'],
    ['-','/',':',';','(',')','$','&','@','"'],
    ['.',',','?','!','’','back']
  ];
  const KB_SYMS = [
    ['[',']','{','}','#','%','^','*','+','='],
    ['_','\\','|','~','<','>','€','£','¥','•'],
    ['.',',','?','!','’','back']
  ];
  let kbMode = 'letters';
  let kbShift = false;
  let activeInput = null;
  const phoneContainer = document.getElementById('phone-container');
  const kbEl = document.createElement('div');
  kbEl.id = 'vkeyboard';
  if (phoneContainer) phoneContainer.appendChild(kbEl);
  const inputStates = new Map();
  let osClipboard = '';
  let selMenuEl = null;
  const measureCanvas = document.createElement('canvas');
  const measureCtx = measureCanvas.getContext('2d');
  function getInputFont(el) {
      const cs = getComputedStyle(el);
      return cs.fontStyle + ' ' + cs.fontVariant + ' ' + cs.fontWeight + ' ' + cs.fontSize + '/' + cs.lineHeight + ' ' + cs.fontFamily;
  }
  function displayText(el) {
      return el.type === 'password' ? '•'.repeat(el.value.length) : el.value;
  }
  function charOffsets(el) {
      measureCtx.font = getInputFont(el);
      const text = displayText(el);
      const offsets = [0];
      let acc = 0;
      for (let i = 0; i < text.length; i++) {
          acc += measureCtx.measureText(text[i]).width;
          offsets.push(acc);
      }
      return offsets;
  }
  function indexFromLocalX(el, localX) {
      const offsets = charOffsets(el);
      let best = 0, bestDist = Infinity;
      for (let i = 0; i < offsets.length; i++) {
          const d = Math.abs(offsets[i] - localX);
          if (d < bestDist) { bestDist = d; best = i; }
      }
      return best;
  }
  function localXFromClientX(el, clientX) {
      const rect = el.getBoundingClientRect();
      const cs = getComputedStyle(el);
      const padLeft = parseFloat(cs.paddingLeft) || 0;
      return (clientX - rect.left - padLeft) + el.scrollLeft;
  }
  function ensureEnhanced(el) {
      if (inputStates.has(el)) return inputStates.get(el);
      const wrap = document.createElement('div');
      wrap.className = 'qp-input-wrap';
      el.parentNode.insertBefore(wrap, el);
      wrap.appendChild(el);
      const selEl = document.createElement('div');
      selEl.className = 'qp-sel-highlight';
      wrap.appendChild(selEl);
      const caretEl = document.createElement('div');
      caretEl.className = 'qp-caret';
      wrap.appendChild(caretEl);
      const st = { wrap: wrap, selEl: selEl, caretEl: caretEl, selStart: 0, selEnd: 0, active: false };
      inputStates.set(el, st);
      return st;
  }
  function restartBlink(caretEl) {
      caretEl.style.animation = 'none';
      void caretEl.offsetWidth;
      caretEl.style.animation = '';
  }
  function renderCursorUI(el) {
      const st = inputStates.get(el);
      if (!st) return;
      const cs = getComputedStyle(el);
      const padLeft = parseFloat(cs.paddingLeft) || 0;
      const offsets = charOffsets(el);
      const inputRect = el.getBoundingClientRect();
      const wrapRect = st.wrap.getBoundingClientRect();
      const baseLeft = (inputRect.left - wrapRect.left) + padLeft;
      const hasSel = st.selStart !== st.selEnd;
      if (hasSel && st.active) {
          const s = Math.min(st.selStart, st.selEnd), e = Math.max(st.selStart, st.selEnd);
          const left = baseLeft + offsets[s] - el.scrollLeft;
          const width = Math.max(offsets[e] - offsets[s], 2);
          st.selEl.style.left = left + 'px';
          st.selEl.style.width = width + 'px';
          st.selEl.style.display = 'block';
      } else {
          st.selEl.style.display = 'none';
      }
      if (st.active) {
          const left = baseLeft + offsets[st.selEnd] - el.scrollLeft;
          st.caretEl.style.left = left + 'px';
          st.caretEl.style.display = hasSel ? 'none' : 'block';
          restartBlink(st.caretEl);
      } else {
          st.caretEl.style.display = 'none';
      }
  }
  function setValue(el, newVal, newSelStart, newSelEnd) {
      el.value = newVal;
      const st = inputStates.get(el);
      st.selStart = newSelStart;
      st.selEnd = newSelEnd;
      el.dispatchEvent(new Event('input'));
      renderCursorUI(el);
  }
  function insertAtCursor(el, str) {
      const st = inputStates.get(el);
      if (!st) return;
      const s = Math.min(st.selStart, st.selEnd), e = Math.max(st.selStart, st.selEnd);
      const val = el.value;
      const newVal = val.slice(0, s) + str + val.slice(e);
      const pos = s + str.length;
      setValue(el, newVal, pos, pos);
  }
  function deleteAtCursor(el) {
      const st = inputStates.get(el);
      if (!st) return;
      const val = el.value;
      let s = Math.min(st.selStart, st.selEnd), e = Math.max(st.selStart, st.selEnd);
      if (s === e) {
          if (s === 0) return;
          s -= 1;
      }
      setValue(el, val.slice(0, s) + val.slice(e), s, s);
  }
  function selectWordAt(el, idx) {
      const val = el.value;
      const st = inputStates.get(el);
      if (!val) { st.selStart = 0; st.selEnd = 0; return; }
      const isWordChar = (c) => !!c && !/\s/.test(c);
      let s = idx, e = idx;
      if (isWordChar(val[idx]) || isWordChar(val[idx - 1])) {
          if (!isWordChar(val[s]) && s > 0) s -= 1;
          while (s > 0 && isWordChar(val[s - 1])) s -= 1;
          e = s;
          while (e < val.length && isWordChar(val[e])) e += 1;
      }
      st.selStart = s; st.selEnd = e;
  }
  function ensureSelMenu() {
      if (selMenuEl) return selMenuEl;
      selMenuEl = document.createElement('div');
      selMenuEl.className = 'qp-select-menu';
      selMenuEl.addEventListener('pointerdown', (e) => {
          const item = e.target.closest('[data-menu-key]');
          if (!item) return;
          e.preventDefault();
          e.stopPropagation();
          const el = selMenuEl.__targetInput;
          if (!el) return;
          const st = inputStates.get(el);
          if (!st) return;
          const key = item.getAttribute('data-menu-key');
          const s = Math.min(st.selStart, st.selEnd), e2 = Math.max(st.selStart, st.selEnd);
          if (navigator.vibrate) navigator.vibrate(6);
          if (key === 'copy') {
              osClipboard = el.value.slice(s, e2);
              hideSelMenu();
          } else if (key === 'cut') {
              osClipboard = el.value.slice(s, e2);
              deleteAtCursor(el);
              hideSelMenu();
          } else if (key === 'selectall') {
              st.selStart = 0; st.selEnd = el.value.length;
              renderCursorUI(el);
              showSelMenu(el);
          } else if (key === 'paste') {
              insertAtCursor(el, osClipboard);
              hideSelMenu();
          }
      });
      if (phoneContainer) phoneContainer.appendChild(selMenuEl);
      return selMenuEl;
  }
  function showSelMenu(el) {
      const st = inputStates.get(el);
      if (!st) return;
      const menu = ensureSelMenu();
      const hasSel = st.selStart !== st.selEnd;
      const s = Math.min(st.selStart, st.selEnd), e = Math.max(st.selStart, st.selEnd);
      const allSelected = hasSel && s === 0 && e === el.value.length;
      const items = [];
      if (hasSel) {
          items.push({ key: 'copy', label: 'Sao chép' });
          items.push({ key: 'cut', label: 'Cắt' });
      }
      if (!allSelected && el.value.length > 0) items.push({ key: 'selectall', label: 'Chọn tất cả' });
      if (osClipboard) items.push({ key: 'paste', label: 'Dán' });
      if (items.length === 0) { hideSelMenu(); return; }
      menu.innerHTML = items.map((it) => '<div class="qp-select-menu-item" data-menu-key="' + it.key + '">' + it.label + '</div>').join('');
      menu.__targetInput = el;
      positionSelMenu(el);
  }
  function positionSelMenu(el) {
      if (!selMenuEl || !phoneContainer) return;
      const st = inputStates.get(el);
      if (!st) return;
      const containerRect = phoneContainer.getBoundingClientRect();
      const cs = getComputedStyle(el);
      const padLeft = parseFloat(cs.paddingLeft) || 0;
      const offsets = charOffsets(el);
      const inputRect = el.getBoundingClientRect();
      const s = Math.min(st.selStart, st.selEnd), e = Math.max(st.selStart, st.selEnd);
      const midOffset = (offsets[s] + offsets[e]) / 2;
      const midX = inputRect.left + padLeft + midOffset - el.scrollLeft;
      selMenuEl.style.display = 'flex';
      selMenuEl.style.visibility = 'hidden';
      const menuWidth = selMenuEl.offsetWidth;
      const menuHeight = selMenuEl.offsetHeight;
      let left = (midX - containerRect.left) - menuWidth / 2;
      left = Math.max(6, Math.min(left, containerRect.width - menuWidth - 6));
      let top = (inputRect.top - containerRect.top) - menuHeight - 12;
      let below = false;
      if (top < 6) {
          top = (inputRect.bottom - containerRect.top) + 12;
          below = true;
      }
      selMenuEl.classList.toggle('qp-menu-below', below);
      selMenuEl.style.left = left + 'px';
      selMenuEl.style.top = top + 'px';
      selMenuEl.style.setProperty('--qp-arrow-x', ((midX - containerRect.left) - left) + 'px');
      selMenuEl.style.visibility = 'visible';
  }
  function hideSelMenu() {
      if (selMenuEl) selMenuEl.style.display = 'none';
  }
  function attachInputBehaviors(el) {
      const st = ensureEnhanced(el);
      let longPressTimer = null;
      let didLongPress = false;
      let startPoint = null;
      function idxFromClientX(clientX) {
          return indexFromLocalX(el, localXFromClientX(el, clientX));
      }
      el.addEventListener('pointerdown', (e) => {
          e.preventDefault();
          el.focus();
          openKeyboard(el);
          hideSelMenu();
          startPoint = { x: e.clientX, y: e.clientY };
          didLongPress = false;
          const idx = idxFromClientX(e.clientX);
          st.selStart = idx; st.selEnd = idx;
          renderCursorUI(el);
          clearTimeout(longPressTimer);
          longPressTimer = setTimeout(() => {
              didLongPress = true;
              selectWordAt(el, idx);
              renderCursorUI(el);
              showSelMenu(el);
              if (navigator.vibrate) navigator.vibrate(10);
          }, 480);
      });
      el.addEventListener('pointermove', (e) => {
          if (!startPoint) return;
          if (!didLongPress) {
              const dx = Math.abs(e.clientX - startPoint.x), dy = Math.abs(e.clientY - startPoint.y);
              if (dx > 8 || dy > 8) clearTimeout(longPressTimer);
              return;
          }
          st.selEnd = idxFromClientX(e.clientX);
          renderCursorUI(el);
          positionSelMenu(el);
      });
      function endPress() {
          clearTimeout(longPressTimer);
          if (didLongPress) showSelMenu(el);
          startPoint = null;
      }
      el.addEventListener('pointerup', endPress);
      el.addEventListener('pointercancel', endPress);
  }
  function renderKeyboard() {
      let layout = kbMode === 'letters' ? KB_LETTERS : (kbMode === 'nums' ? KB_NUMS : KB_SYMS);
      let html = '';
      layout.forEach((row) => {
          html += '<div class="vkb-row">';
          row.forEach((k) => {
              let cls = 'vkb-key';
              let style = '';
              let label = k;
              if (k === 'shift') {
                  cls += ' vkb-special' + (kbShift ? ' vkb-active' : '');
                  label = '<i class="fa-solid fa-arrow-up"></i>';
                  style = 'flex:1.5;';
              } else if (k === 'back') {
                  cls += ' vkb-special';
                  label = '<i class="fa-solid fa-delete-left"></i>';
                  style = 'flex:1.5;';
              } else if (kbMode === 'letters' && kbShift) {
                  label = k.toUpperCase();
              }
              html += '<div class="' + cls + '" data-key="' + k + '" style="' + style + '">' + label + '</div>';
          });
          html += '</div>';
      });
      let modeKey = kbMode === 'letters' ? { key: 'to_nums', label: '123' }
          : kbMode === 'nums' ? { key: 'to_syms', label: '#+=' }
              : { key: 'to_letters', label: 'ABC' };
      html += '<div class="vkb-row">';
      html += '<div class="vkb-key vkb-special" data-key="' + modeKey.key + '" style="flex:1.8;">' + modeKey.label + '</div>';
      html += '<div class="vkb-key vkb-space" data-key="space" style="flex:5;"></div>';
      html += '<div class="vkb-key vkb-done" data-key="done" style="flex:1.8;">Xong</div>';
      html += '</div>';
      kbEl.innerHTML = html;
  }
  function performKeyAction(k) {
      if (!activeInput) return;
      if (k === 'shift') { kbShift = !kbShift; renderKeyboard(); return; }
      if (k === 'back') { hideSelMenu(); deleteAtCursor(activeInput); return; }
      if (k === 'space') { hideSelMenu(); insertAtCursor(activeInput, ' '); return; }
      if (k === 'done') { closeKeyboard(); return; }
      if (k === 'to_nums') { kbMode = 'nums'; renderKeyboard(); return; }
      if (k === 'to_syms') { kbMode = 'syms'; renderKeyboard(); return; }
      if (k === 'to_letters') { kbMode = 'letters'; kbShift = false; renderKeyboard(); return; }
      let ch = k;
      if (kbMode === 'letters' && kbShift) { ch = ch.toUpperCase(); kbShift = false; }
      hideSelMenu();
      insertAtCursor(activeInput, ch);
      if (kbMode === 'letters') renderKeyboard();
  }
  let keyRepeatTimer = null;
  let keyRepeatInterval = null;
  function stopKeyRepeat() {
      clearTimeout(keyRepeatTimer);
      clearInterval(keyRepeatInterval);
      keyRepeatTimer = null;
      keyRepeatInterval = null;
  }
  kbEl.addEventListener('pointerdown', (e) => {
      const keyEl = e.target.closest('[data-key]');
      if (!keyEl || !activeInput) return;
      e.preventDefault();
      if (navigator.vibrate) navigator.vibrate(8);
      const k = keyEl.getAttribute('data-key');
      performKeyAction(k);
      if (k === 'back') {
          stopKeyRepeat();
          keyRepeatTimer = setTimeout(() => {
              keyRepeatInterval = setInterval(() => performKeyAction('back'), 70);
          }, 380);
      }
  });
  kbEl.addEventListener('pointerup', stopKeyRepeat);
  kbEl.addEventListener('pointercancel', stopKeyRepeat);
  kbEl.addEventListener('pointerleave', stopKeyRepeat);
  function openKeyboard(inputEl) {
      if (activeInput && activeInput !== inputEl) {
          const prevSt = inputStates.get(activeInput);
          if (prevSt) { prevSt.active = false; renderCursorUI(activeInput); }
      }
      activeInput = inputEl;
      kbMode = 'letters'; kbShift = false;
      const st = ensureEnhanced(inputEl);
      st.active = true;
      renderKeyboard();
      renderCursorUI(inputEl);
      kbEl.classList.add('vkb-open');
      requestAnimationFrame(() => {
          const kbHeight = kbEl.offsetHeight;
          const scrollArea = inputEl.closest('.kb-scroll-area');
          if (scrollArea) {
              scrollArea.style.paddingBottom = (kbHeight + 24) + 'px';
              setTimeout(() => {
                  inputEl.scrollIntoView({ block: 'center', behavior: 'smooth' });
              }, 80);
          }
      });
  }
  function closeKeyboard() {
      hideSelMenu();
      stopKeyRepeat();
      if (activeInput) {
          const scrollArea = activeInput.closest('.kb-scroll-area');
          if (scrollArea) scrollArea.style.paddingBottom = '';
          const st = inputStates.get(activeInput);
          if (st) { st.active = false; st.selStart = st.selEnd; renderCursorUI(activeInput); }
      }
      kbEl.classList.remove('vkb-open');
      activeInput = null;
  }
  window.__attachVKeyboard = function (inputEl) {
      if (!inputEl) return;
      attachInputBehaviors(inputEl);
  };
  window.__closeVKeyboard = closeKeyboard;
  if (phoneContainer) {
      phoneContainer.addEventListener('pointerdown', (e) => {
          if (!activeInput) return;
          if (kbEl.contains(e.target)) return;
          if (selMenuEl && selMenuEl.contains(e.target)) return;
          if (e.target.closest && e.target.closest('.qp-input')) return;
          closeKeyboard();
      }, true);
  }
})();
"""

DOCK_APPS_CSS = r"""
#dock .app-icon { width: 68px; }
.simple-app { display: none; position: absolute; top: 0; left: 0; width: 100%; height: 100%; z-index: 100; overflow: hidden; border-radius: inherit; }
.sa-center { position: absolute; inset: 0; display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 60px 20px 40px; }
.sa-name { font-size: 30px; font-weight: 800; color: #fff; letter-spacing: 0.5px; text-shadow: 0 4px 18px rgba(0,0,0,0.35); }
.sa-orb { position: absolute; border-radius: 50%; filter: blur(60px); opacity: 0.45; animation: saFloat 7s ease-in-out infinite; pointer-events: none; }
.sa-orb-1 { width: 220px; height: 220px; top: 12%; left: -60px; background: rgba(255,255,255,0.25); }
.sa-orb-2 { width: 260px; height: 260px; bottom: 8%; right: -80px; background: rgba(255,255,255,0.16); animation-delay: -3.5s; }
@keyframes saFloat { 0%, 100% { transform: translateY(0) scale(1); } 50% { transform: translateY(-26px) scale(1.08); } }
.sa-bg-phone { background: linear-gradient(160deg, #012e22 0%, #0b6e4f 55%, #0aa06b 100%); }
.sa-bg-messages { background: linear-gradient(160deg, #001f3f 0%, #0b5aa5 60%, #0a84ff 100%); }
.sa-bg-qhzd { background: linear-gradient(160deg, #1b0b3a 0%, #5b2bd6 55%, #c86bff 100%); }
.sa-bg-camera { background: linear-gradient(160deg, #0c0c0e 0%, #2c2c30 60%, #4a4a50 100%); }
#app-switcher {
position: absolute; top: 0; left: 0; width: 100%; height: 100%; z-index: 9000;
display: none; background: rgba(10,10,16,0.55);
backdrop-filter: blur(28px) saturate(1.4); -webkit-backdrop-filter: blur(28px) saturate(1.4);
opacity: 0; transition: opacity 0.3s ease;
}
#app-switcher.open { opacity: 1; }
.sw-header { position: absolute; top: 62px; left: 0; right: 0; display: flex; align-items: center; justify-content: center; gap: 8px; }
.sw-title { color: rgba(255,255,255,0.92); font-size: 15px; font-weight: 600; letter-spacing: 0.4px; text-shadow: 0 1px 6px rgba(0,0,0,0.4); }
.sw-title-icon { display: inline-flex; align-items: center; justify-content: center; width: 22px; height: 22px; filter: drop-shadow(0 1px 3px rgba(0,0,0,0.4)); }
.sw-stage { position: absolute; top: 100px; bottom: 132px; left: 0; right: 0; display: none; padding: 0 0 0 14px; }
.sw-stage-stack { position: absolute; top: 14px; bottom: 14px; left: 14px; width: 64px; display: flex; flex-direction: column; align-items: center; gap: -10px; overflow-y: auto; padding: 4px 0; z-index: 5; pointer-events: auto; overflow-x: visible; }
.sw-stage-stack::-webkit-scrollbar { display: none; }
.sw-stack-item {
width: 48px; height: 48px; border-radius: 13px; flex-shrink: 0;
display: flex; align-items: center; justify-content: center;
color: #fff; font-size: 19px; text-shadow: 0 2px 6px rgba(0,0,0,0.35);
border: 1px solid rgba(255,255,255,0.22); box-shadow: 0 6px 16px rgba(0,0,0,0.45);
cursor: pointer; position: relative;
transition: transform 0.3s var(--ios-spring-snappy), box-shadow 0.25s ease, margin 0.3s var(--ios-spring-snappy);
will-change: transform, opacity;
}
.sw-stack-item + .sw-stack-item { margin-top: -10px; }
.sw-stack-item.selected { transform: translateX(4px) scale(1.12); box-shadow: 0 8px 20px rgba(0,0,0,0.5), 0 0 0 2.5px #fff, 0 0 20px rgba(255,255,255,0.5); z-index: 50; }
.sw-stack-out { animation: swStackOut 0.3s ease forwards !important; }
@keyframes swStackOut { to { opacity: 0; transform: translateY(-130%); filter: blur(6px); } }
.sw-stage-panel {
position: absolute; top: 14px; right: 14px; bottom: 14px; left: 78px; border-radius: 22px; background: #1a1a1a;
overflow: hidden; box-shadow: 0 16px 40px rgba(0,0,0,0.35);
display: flex; align-items: center; justify-content: center;
isolation: isolate;
}
.stage-panel-in { animation: panelIn 0.45s var(--ios-spring-snappy) backwards; }
@keyframes panelIn { from { opacity: 0; transform: translateX(40px) scale(0.9); } to { opacity: 1; transform: none; } }
.sw-panel-placeholder { display: flex; flex-direction: column; align-items: center; gap: 12px; color: #a2a2ab; font-size: 13.5px; font-weight: 600; text-align: center; padding: 0 18px; }
.sw-panel-placeholder i { font-size: 34px; opacity: 0.7; }
.sw-panel-preview { position: absolute; inset: 0; overflow: hidden; cursor: pointer; }
.sw-panel-preview.panel-fly { animation: panelFly 0.5s var(--ios-spring-snappy); transform-origin: left center; }
@keyframes panelFly {
from { transform: translateX(-70%) scale(0.25); opacity: 0; border-radius: 40px; }
to { transform: none; opacity: 1; }
}
.sw-empty { position: absolute; top: 0; bottom: 0; left: 0; right: 0; display: none; flex-direction: column; align-items: center; justify-content: center; gap: 14px; color: rgba(255,255,255,0.6); font-size: 15px; font-weight: 500; }
.sw-empty-icon { display: inline-flex; align-items: center; justify-content: center; opacity: 0.7; }
.sw-close-all {
position: absolute; bottom: 56px; left: 50%; transform: translateX(-50%);
background: rgba(255,255,255,0.14); backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
color: #fff; font-size: 14px; font-weight: 600; padding: 10px 22px; border-radius: 22px;
border: 1px solid rgba(255,255,255,0.15); cursor: pointer;
}
.sw-close-all:active { transform: translateX(-50%) scale(0.92); }
"""

DOCK_APPS_BODY = r"""
<div id="app-switcher">
  <div class="sw-header">
    <span class="sw-title-icon" aria-hidden="true">
      <svg viewBox="0 0 28 28" width="22" height="22" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <linearGradient id="swG1" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stop-color="#ffffff" stop-opacity="0.95"/>
            <stop offset="100%" stop-color="#ffffff" stop-opacity="0.55"/>
          </linearGradient>
          <linearGradient id="swG2" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stop-color="#ffffff" stop-opacity="0.7"/>
            <stop offset="100%" stop-color="#ffffff" stop-opacity="0.3"/>
          </linearGradient>
          <linearGradient id="swG3" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stop-color="#ffffff" stop-opacity="0.4"/>
            <stop offset="100%" stop-color="#ffffff" stop-opacity="0.15"/>
          </linearGradient>
        </defs>
        <!-- 3 o vuong xep lech nhau, mo phong App Switcher icon cua Apple -->
        <rect x="2.5" y="2.5" width="19" height="19" rx="4.5" fill="url(#swG3)" stroke="rgba(255,255,255,0.25)" stroke-width="0.8"/>
        <rect x="4.5" y="4.5" width="19" height="19" rx="4.5" fill="url(#swG2)" stroke="rgba(255,255,255,0.35)" stroke-width="0.8"/>
        <rect x="6.5" y="6.5" width="19" height="19" rx="4.5" fill="url(#swG1)" stroke="rgba(255,255,255,0.5)" stroke-width="0.9"/>
        <circle cx="12.5" cy="11" r="1.2" fill="rgba(0,0,0,0.35)"/>
        <circle cx="16" cy="11" r="1.2" fill="rgba(0,0,0,0.35)"/>
        <rect x="11.5" y="18" width="9" height="1.2" rx="0.6" fill="rgba(0,0,0,0.4)"/>
        <rect x="11.5" y="20.5" width="6" height="1.2" rx="0.6" fill="rgba(0,0,0,0.3)"/>
      </svg>
    </span>
    <span class="sw-title">Switcher</span>
  </div>
  <div class="sw-stage" id="sw-stage">
    <div class="sw-stage-stack" id="sw-stage-stack"></div>
    <div class="sw-stage-panel" id="sw-stage-panel"></div>
  </div>
  <div class="sw-empty" id="sw-empty">
    <span class="sw-empty-icon" aria-hidden="true">
      <svg viewBox="0 0 64 64" width="56" height="56" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <linearGradient id="empG" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stop-color="rgba(255,255,255,0.5)"/>
            <stop offset="100%" stop-color="rgba(255,255,255,0.15)"/>
          </linearGradient>
        </defs>
        <rect x="6" y="6" width="42" height="42" rx="9" fill="url(#empG)" stroke="rgba(255,255,255,0.25)" stroke-width="1.2"/>
        <rect x="10" y="10" width="42" height="42" rx="9" fill="url(#empG)" stroke="rgba(255,255,255,0.35)" stroke-width="1.2"/>
        <rect x="14" y="14" width="42" height="42" rx="9" fill="url(#empG)" stroke="rgba(255,255,255,0.5)" stroke-width="1.2"/>
      </svg>
    </span>
    <span>Không có ứng dụng nào đang mở</span>
  </div>
  <div class="sw-close-all" id="sw-close-all">Đóng tất cả</div>
</div>
"""

DOCK_APPS_JS = r"""
const DOCK_APP_META = {};
let switcherOpen = false;
let switcherTransitionId = 0;
let stageSelectedId = null;
let swSuppressClick = false;
// State de luu vi tri/kich thuoc app goc khi dua vao preview, de restore khi thoat
// "Bia mo" = luu luon innerHTML de khi mo lai van giu nguyen state (form, game, scroll...)
const previewRestoreState = new Map();

function appMeta(id) {
  return DOCK_APP_META[id] || { name: id, icon: 'fa-solid fa-square', grad: 'linear-gradient(135deg,#333,#555)' };
}
function recentIds() { return activeAppsList.slice().reverse(); }
function ensureTopAppVisible() {
  if (activeAppsList.length) {
    const topId = activeAppsList[activeAppsList.length - 1];
    activeAppsList.forEach(id => {
      const el = document.getElementById(id);
      if (el) el.style.display = (id === topId) ? 'block' : 'none';
    });
    applyStatusBarTheme(topId);
  }
}

/* ====== SMART FIT ENGINE ======
   CONTAIN: scale theo MIN -> vua khit khung, KHONG cat mat bat ky phan nao
   cua giao dien app. Panel duoc layoutPreviewPanel() dung san theo dung ti le
   khung dien thoai truoc khi goi ham nay, nen binh thuong scale/x/y se la
   khop tuyet doi (x=0,y=0) - khong con vien thua, khong con bi tran/cat.
*/
function computeFit(srcW, srcH, frameW, frameH) {
  if (!srcW || !srcH || !frameW || !frameH) return { scale: 1, x: 0, y: 0 };
  const scale = Math.min(frameW / srcW, frameH / srcH);
  const renderW = srcW * scale;
  const renderH = srcH * scale;
  const x = (frameW - renderW) / 2;
  const y = (frameH - renderH) / 2;
  return { scale, x, y };
}

// Ranh gioi vung toi da danh cho panel preview trong #sw-stage (khop CSS goc
// cua .sw-stage-stack/.sw-stage-panel): stack chiem tu 14 den 78, panel cach
// vien phai/tren/duoi 14px.
const PREVIEW_STACK_EDGE = 78;
const PREVIEW_EDGE_GAP = 14;

// Dat lai vi tri/kich thuoc THAT cua panel preview sao cho panel co dung TI LE
// KHUNG DIEN THOAI (thay vi bi keo dan theo vung trong stage). Nho vay app
// preview vua khit panel ma khong con bi CAT MAT giao dien (truoc day panel
// sai ti le khien app phai "cover" va bi tran/mat noi dung o 2 dau).
function layoutPreviewPanel() {
  const panel = document.getElementById('sw-stage-panel');
  const stage = document.getElementById('sw-stage');
  if (!panel || !stage) return;
  const stageW = stage.clientWidth, stageH = stage.clientHeight;
  const availW = stageW - PREVIEW_STACK_EDGE - PREVIEW_EDGE_GAP;
  const availH = stageH - PREVIEW_EDGE_GAP * 2;
  const phone = getPhoneMetrics();
  if (availW <= 0 || availH <= 0 || !phone.w || !phone.h) return;

  const phoneRatio = phone.w / phone.h;
  let panelW, panelH;
  if (availW / availH > phoneRatio) {
    panelH = availH;
    panelW = availH * phoneRatio;
  } else {
    panelW = availW;
    panelH = availW / phoneRatio;
  }
  panel.style.left = (PREVIEW_STACK_EDGE + (availW - panelW) / 2) + 'px';
  panel.style.top = (PREVIEW_EDGE_GAP + (availH - panelH) / 2) + 'px';
  panel.style.width = panelW + 'px';
  panel.style.height = panelH + 'px';
  panel.style.right = 'auto';
  panel.style.bottom = 'auto';
}

/* ====== PREVIEW HOST ======
   Panel lon ben phai trong switcher stage. Chung ta di chuyen (re-parent)
   app element that vao day, scale vua khít, va GIU NGUYEN event listener
   (vi cung mot DOM node) - nen nguoi dung co the bam, vuot, tuong tac
   truc tiep tren app nhu dang dung binh thuong.
*/
function getPhoneMetrics() {
  const c = document.getElementById('phone-container');
  if (!c) return { w: 0, h: 0 };
  return { w: c.clientWidth, h: c.clientHeight };
}

// Ban kinh bo goc cua .sw-stage-panel - phai khop CSS de clip-path duoi day
// tinh dung khung hinh (khong bi lech vien khi preview).
const PREVIEW_PANEL_RADIUS = 22;

// Tinh toan + ap dung transform (di chuyen/scale) va clip-path de "chieu" app
// dung vao vi tri/kich thuoc cua panel MA KHONG DI CHUYEN DOM NODE cua app.
// Ly do: appendChild/insertBefore de re-parent mot node dang chua <iframe>
// (vi du app Penalty) se khien trinh duyet TAI LAI (reload) iframe do moi lan
// - day chinh la nguyen nhan giao dien app bi "khoi dong lai" moi khi qua lai
// xem preview trong switcher. Giu nguyen DOM (khong appendChild) => app dung
// yen tuyet doi, khong reload, khong mat state du xem preview bao nhieu lan.
function applyPreviewTransform(appId) {
  const appEl = document.getElementById(appId);
  const panel = document.getElementById('sw-stage-panel');
  const container = document.getElementById('phone-container');
  if (!appEl || !panel || !container) return false;

  layoutPreviewPanel();

  const phone = getPhoneMetrics();
  const pw = panel.clientWidth, ph = panel.clientHeight;
  if (!phone.w || !phone.h || !pw || !ph) return false;

  // Panel nam trong #app-switcher, von co cung goc toa do voi #phone-container,
  // nhung van do truc tiep bang getBoundingClientRect cho chac chan & chinh xac.
  const containerRect = container.getBoundingClientRect();
  const panelRect = panel.getBoundingClientRect();
  const offsetX = panelRect.left - containerRect.left;
  const offsetY = panelRect.top - containerRect.top;

  const fit = computeFit(phone.w, phone.h, pw, ph);

  // clip-path duoc tinh trong he toa do CUC BO (truoc transform) cua appEl,
  // nen phai chia lai cho scale de sau khi transform, vung hien thi khop
  // chinh xac hinh chu nhat (bo goc) cua panel - khong thua/thieu ben nao.
  const insetX = Math.max(0, (phone.w - pw / fit.scale) / 2);
  const insetY = Math.max(0, (phone.h - ph / fit.scale) / 2);
  const radiusLocal = PREVIEW_PANEL_RADIUS / fit.scale;

  appEl.style.transformOrigin = 'top left';
  appEl.style.transform = 'translate(' + (offsetX + fit.x) + 'px,' + (offsetY + fit.y) + 'px) scale(' + fit.scale + ')';
  appEl.style.clipPath = 'inset(' + insetY + 'px ' + insetX + 'px ' + insetY + 'px ' + insetX + 'px round ' + radiusLocal + 'px)';
  return true;
}

function placeAppInPreview(appId) {
  if (!switcherOpen || stageSelectedId !== appId) return;
  const appEl = document.getElementById(appId);
  const panel = document.getElementById('sw-stage-panel');
  if (!appEl || !panel) return;

  // Luu lai style goc de restore (BIA MO: giu nguyen state app). Khong con
  // can luu parent/nextSibling nua vi app khong bao gio bi doi cha (xem
  // applyPreviewTransform o tren).
  if (!previewRestoreState.has(appId)) {
    previewRestoreState.set(appId, {
      cssText: appEl.style.cssText
    });
  }

  // Reset panel truoc khi gan app moi (bo placeholder, chip, ...). Panel gio
  // chi con dong vai tro "khung nen" - app thuc su van dung yen o cha cu, chi
  // duoc "chieu" de vao dung cho panel bang transform + clip-path.
  panel.innerHTML = '';

  const ok = applyPreviewTransform(appId);
  if (!ok) {
    // Defer khi panel chua layout xong
    requestAnimationFrame(() => placeAppInPreview(appId));
    return;
  }

  appEl.style.display = 'block';
  appEl.style.animation = 'none';
  appEl.style.transition = 'none';
  appEl.style.opacity = '1';
  appEl.style.filter = 'none';
  // Noi len tren toan bo switcher (backdrop, header, stack...) - clip-path da
  // gioi han vung ve/tuong tac dung khung panel nen khong che mat gi khac.
  appEl.style.zIndex = '9500';
}

function removeAppFromPreview(appId) {
  const appEl = document.getElementById(appId);
  const restore = previewRestoreState.get(appId);
  if (!appEl || !restore) return;
  // App chua bao gio roi khoi vi tri/cha cua no - chi can tra style ve nhu cu.
  appEl.style.cssText = restore.cssText;
  previewRestoreState.delete(appId);
}

function detachAllFromPreview() {
  // Tra het app dang o preview ve vi tri goc
  for (const id of Array.from(previewRestoreState.keys())) {
    removeAppFromPreview(id);
  }
}

/* ====== STAGE MODE (CHI CO 1 MODE) ======
   Stack app ben trai, preview lon ben phai. Bam icon = xem preview.
   Bam icon lan nua (khi dang select) = mo app full.
   Vuot len = dong app.
   "Dong tat ca" = close all.
*/
function renderSwitcher() {
  const ids = recentIds();
  const empty = document.getElementById('sw-empty');
  const closeAll = document.getElementById('sw-close-all');
  const stage = document.getElementById('sw-stage');
  if (!ids.length) {
    empty.style.display = 'flex'; closeAll.style.display = 'none';
    stage.style.display = 'none';
    return;
  }
  empty.style.display = 'none'; closeAll.style.display = 'block';
  stage.style.display = 'flex';
  buildStage();
}
function buildStage() {
  const stack = document.getElementById('sw-stage-stack');
  const panel = document.getElementById('sw-stage-panel');
  stack.innerHTML = '';
  const ids = recentIds();
  if (stageSelectedId && !ids.includes(stageSelectedId)) stageSelectedId = null;

  ids.forEach((id, i) => {
    const meta = appMeta(id);
    const item = document.createElement('div');
    item.className = 'sw-stack-item' + (id === stageSelectedId ? ' selected' : '');
    item.dataset.app = id;
    item.style.background = meta.grad;
    item.style.zIndex = String(ids.length - i);
    item.innerHTML = '<i class="' + meta.icon + '"></i>';
    stack.appendChild(item);

    // Click icon: chi select de xem preview (KHONG mo app, KHONG kill, KHONG double-tap)
    item.addEventListener('click', (e) => {
      if (swSuppressClick) return;
      e.stopPropagation();
      if (navigator.vibrate) try { navigator.vibrate(6); } catch(e){}
      selectStageApp(id);
    });
  });

  if (!stageSelectedId) {
    renderPanelPlaceholder();
  } else {
    placeAppInPreview(stageSelectedId);
  }
}
function renderPanelPlaceholder() {
  const panel = document.getElementById('sw-stage-panel');
  layoutPreviewPanel();
  // Dam bao khong con app nao dang o preview
  detachAllFromPreview();
  panel.innerHTML =
    '<div class="sw-panel-placeholder">' +
      '<svg viewBox="0 0 64 64" width="44" height="44" xmlns="http://www.w3.org/2000/svg">' +
        '<defs><linearGradient id="phG" x1="0" y1="0" x2="1" y2="1">' +
          '<stop offset="0%" stop-color="rgba(255,255,255,0.45)"/>' +
          '<stop offset="100%" stop-color="rgba(255,255,255,0.15)"/>' +
        '</linearGradient></defs>' +
        '<rect x="14" y="10" width="32" height="44" rx="5" fill="url(#phG)" stroke="rgba(255,255,255,0.3)" stroke-width="1.2"/>' +
        '<line x1="20" y1="20" x2="40" y2="20" stroke="rgba(255,255,255,0.4)" stroke-width="1.4" stroke-linecap="round"/>' +
        '<line x1="20" y1="26" x2="36" y2="26" stroke="rgba(255,255,255,0.3)" stroke-width="1.2" stroke-linecap="round"/>' +
        '<line x1="20" y1="32" x2="38" y2="32" stroke="rgba(255,255,255,0.3)" stroke-width="1.2" stroke-linecap="round"/>' +
      '</svg>' +
      '<span>Chưa có ứng dụng nào đang mở</span>' +
    '</div>';
}
function selectStageApp(id) {
  // Neu app dang duoc preview, tra ve truoc
  if (stageSelectedId && stageSelectedId !== id) {
    removeAppFromPreview(stageSelectedId);
  }
  stageSelectedId = id;
  if (navigator.vibrate) try { navigator.vibrate(8); } catch(e){}
  document.querySelectorAll('.sw-stack-item').forEach(it => {
    it.classList.toggle('selected', it.dataset.app === id);
  });
  placeAppInPreview(id);
  if (window.penaltyUpdateBadge) window.penaltyUpdateBadge();
}
function killApp(appId, el) {
  if (navigator.vibrate) try { navigator.vibrate(10); } catch(e){}
  if (el) el.classList.add('sw-stack-out');
  const idx = activeAppsList.indexOf(appId);
  if (idx > -1) activeAppsList.splice(idx, 1);
  if (historyPointer >= activeAppsList.length) historyPointer = activeAppsList.length - 1;
  // Vuot huy 1 app rieng le trong switcher cung la DONG HAN app do (giong het
  // "Dong tat ca" nhung chi cho 1 app) - bao cho app biet de lan mo lai sau
  // chay lai dung tu dau.
  document.dispatchEvent(new CustomEvent('magicos-app-terminated', { detail: { appId: appId } }));
  // Neu app dang o preview, tra no ve home truoc
  if (previewRestoreState.has(appId)) {
    removeAppFromPreview(appId);
  }
  const appEl = document.getElementById(appId);
  if (appEl) appEl.style.display = 'none';
  if (foregroundAppId === appId) {
    foregroundAppId = activeAppsList.length ? activeAppsList[activeAppsList.length - 1] : null;
  }
  ensureTopAppVisible();
  if (stageSelectedId === appId) stageSelectedId = null;
  setTimeout(() => { renderSwitcher(); }, 300);
  if (typeof applyCallIslandState === 'function') applyCallIslandState();
}
function switcherOpenApp(appId, originEl) {
  // Tra app dang o preview ve home
  detachAllFromPreview();
  closeAppSwitcher();
  openAppFromIcon(appId, originEl);
  trackApp(appId);
}
// Mo app tu switcher ma KHONG reset/khoi dong lai (bia mo - giu nguyen state)
function switcherResumeApp(appId) {
  detachAllFromPreview();
  closeAppSwitcher();
  const appEl = document.getElementById(appId);
  if (appEl) {
    appEl.style.display = 'block';
    appEl.style.animation = 'none';
    appEl.style.transition = 'none';
    void appEl.offsetWidth;
    appEl.style.animation = '';
    appEl.style.transition = '';
    appEl.style.transform = '';
    appEl.style.opacity = '';
    appEl.style.filter = '';
    appEl.style.borderRadius = '';
  }
  const idx = activeAppsList.indexOf(appId);
  if (idx > -1) activeAppsList.splice(idx, 1);
  activeAppsList.push(appId);
  historyPointer = activeAppsList.length - 1;
  foregroundAppId = appId;
  ensureTopAppVisible();
  if (window.penaltyUpdateBadge) window.penaltyUpdateBadge();
  applyStatusBarTheme(appId);
  if (typeof applyCallIslandState === 'function') applyCallIslandState();
}
function openAppSwitcher() {
  if (switcherOpen || !document.body.classList.contains('unlocked')) return;
  switcherOpen = true;
  const transitionId = ++switcherTransitionId;
  // Always establish Home first. Keep app DOM, sessions and recent order intact.
  detachAllFromPreview();
  previewRestoreState.clear();
  closeKeypad();
  if (isNotifPeekOpen) closeNotificationPeek();
  closeControlCenter();
  document.querySelectorAll('.simple-app').forEach(app => {
    clearTimeout(app.__zoomCleanupTimer);
    app.style.display = 'none';
    app.style.transition = ''; app.style.animation = '';
    app.style.transform = ''; app.style.transformOrigin = '';
    app.style.opacity = ''; app.style.filter = ''; app.style.borderRadius = '';
    app.style.clipPath = ''; app.style.zIndex = '';
  });
  foregroundAppId = null;
  const home = document.getElementById('home-screen');
  home.style.display = 'block';
  home.classList.remove('home-spring-in');
  applyStatusBarTheme(null);
  const ids = recentIds();
  stageSelectedId = ids.length ? ids[0] : null;
  const sw = document.getElementById('app-switcher');
  clearTimeout(sw.__hideTimer);
  sw.classList.remove('open');
  sw.style.display = 'none';
  // Paint Home before opening Switcher; ignore callbacks from an older gesture.
  requestAnimationFrame(() => requestAnimationFrame(() => {
    if (!switcherOpen || transitionId !== switcherTransitionId) return;
    sw.style.display = 'block';
    renderSwitcher();
    void sw.offsetWidth;
    sw.classList.add('open');
    if (window.penaltyUpdateBadge) window.penaltyUpdateBadge();
    if (typeof applyCallIslandState === 'function') applyCallIslandState();
  }));
  if (navigator.vibrate) try { navigator.vibrate(10); } catch(e){}
}
function closeAppSwitcher() {
  if (!switcherOpen) return;
  switcherOpen = false;
  ++switcherTransitionId;
  // Tra het app ve home
  detachAllFromPreview();
  const sw = document.getElementById('app-switcher');
  sw.classList.remove('open');
  clearTimeout(sw.__hideTimer);
  sw.__hideTimer = setTimeout(() => { if (!switcherOpen) sw.style.display = 'none'; }, 350);
  if (activeAppsList.length === 0) {
    document.getElementById('home-screen').style.display = 'block';
    foregroundAppId = null;
  }
  if (typeof applyCallIslandState === 'function') applyCallIslandState();
}
(function setupSwitcherGestures() {
  const sw = document.getElementById('app-switcher');
  if (!sw) return;
  // Click ngoai / click panel: KHONG lam gi (switcher chi thoat qua home indicator hoac Close All)
  sw.addEventListener('click', (e) => {
    // Chan bubble neu can (tranh tu dong close tu cho khac)
    e.stopPropagation();
  });

  document.getElementById('sw-close-all').addEventListener('click', (e) => {
    e.stopPropagation();
    hardResetAllApps();
    applyStatusBarTheme(null);
    document.getElementById('home-screen').style.display = 'block';
    stageSelectedId = null;
    closeAppSwitcher();
  });

  // Home indicator swipe len -> dong switcher (cach duy nhat de thoat)
  const hit = document.getElementById('home-indicator-hitbox');
  if (hit) {
    let swHomeDY = 0;
    // Chot san trang thai "dang co thong bao/control center mo hay khong" NGAY
    // LUC BAT DAU cham (touchstart) - KHONG doc lai luc touchend, vi listener
    // dong thong bao/control center o tren (dang ky truoc) cung nghe chung
    // touchend nay va se chay TRUOC, doi isNotifPeekOpen ve false ngay lap tuc.
    // Neu doc lai luc do se bi "hut" nham la khong co gi dang mo -> dong nham
    // ca switcher. Chot tu dau cham thi trang thai luon dung trong suot ca cu ly.
    let hitPeekOrCCOpenAtStart = false;
    hit.addEventListener('touchstart', () => {
      swHomeDY = 0;
      hitPeekOrCCOpenAtStart = isNotifPeekOpen || (controlCenter && controlCenter.classList.contains('open'));
    }, { passive: true });
    hit.addEventListener('touchmove', (e) => { swHomeDY = homeStartY - e.touches[0].clientY; }, { passive: true });
    hit.addEventListener('touchend', () => {
      if (swHoldFired) return; // Keep the hold flag until the next touch starts.
      if (!switcherOpen) return;
      // Neu luc BAT DAU cham thong bao (peek) hoac control center dang mo thi
      // UU TIEN dong cai do truoc (giong listener chinh o tren) - KHONG dong
      // switcher cung luc, tranh 1 lan vuot len ma dong ca 2 thu mot luc.
      if (hitPeekOrCCOpenAtStart) return;
      if (swHomeDY > 30) {
        // Vuot len -> dong switcher, KHONG tu mo app nao
        closeAppSwitcher();
        document.getElementById('home-screen').style.display = 'block';
        applyStatusBarTheme(null);
      }
      // neu khong vuot len du xa -> giu nguyen switcher (khong close)
    });
  }
})();

// ResizeObserver: khi phone-container thay doi (xoay, reflow), fit lai preview
function refitActivePreview() {
  if (!stageSelectedId) return;
  applyPreviewTransform(stageSelectedId);
}
(function setupPreviewResize() {
  const container = document.getElementById('phone-container');
  if (!container || typeof ResizeObserver === 'undefined') return;
  let raf = 0;
  const ro = new ResizeObserver(() => {
    if (!switcherOpen) return;
    cancelAnimationFrame(raf);
    raf = requestAnimationFrame(refitActivePreview);
  });
  ro.observe(container);
  window.addEventListener('orientationchange', () => {
    setTimeout(refitActivePreview, 250);
  });
  // Doi mot frame de panel co kich thuoc that truoc khi fit
  setTimeout(refitActivePreview, 0);
});
"""

APP_JS_4 = r"""
const statusBar = document.getElementById('status-bar');
const island = document.getElementById('dynamic-island');
/* ===== Luu so du Token trong game Penalty - tach RIENG cho sever Nha phat
   trien (ma mo khoa 081120) va sever Nguoi dung thuong (ma 000000), giong
   nhu cach MAZI SIM va Pass Token da tach o tren. Vi iframe Penalty chay o
   port rieng (khac origin) nen khong doc chung localStorage voi trang nay -
   phai truyen so du ban dau qua query string luc mo iframe, va nhan lai
   moi lan game thay doi so du qua postMessage de luu vao dung key theo vai
   dang mo khoa hien tai. */
function penaltyBalanceKey() {
  return (typeof adminModeUnlocked !== 'undefined' && adminModeUnlocked) ? 'magicos_penalty_balance_admin' : 'magicos_penalty_balance_user';
}
function getPenaltyBalance() {
  try { var v = parseFloat(localStorage.getItem(penaltyBalanceKey())); return isFinite(v) ? v : 100; } catch (e) { return 100; }
}
function savePenaltyBalance(v) {
  try { localStorage.setItem(penaltyBalanceKey(), String(v)); } catch (e) {}
}
window.getPenaltyBalance = getPenaltyBalance;
window.savePenaltyBalance = savePenaltyBalance;
window.addEventListener('message', function(ev) {
  var d = ev && ev.data;
  if (!d) return;
  if (d.source === 'penalty-game' && d.type === 'notify') {
    var iconHtml = d.kind === 'goal'
      ? '<i class="fa-solid fa-futbol"></i>'
      : '<i class="fa-solid fa-triangle-exclamation"></i>';
    showNotification(d.text || '', d.kind === 'goal' ? 'success' : 'error', iconHtml);
    return;
  }
  if (d.source === 'penalty-game' && d.type === 'balance') {
    if (typeof d.value === 'number' && isFinite(d.value)) savePenaltyBalance(d.value);
    return;
  }
  if (d.source === 'magicos-phone' && d.type === 'tokenNotice') {
    showNotification(d.text || 'Token Không Đủ', 'error', '<i class="fa-solid fa-coins"></i>');
    return;
  }
  if (d.source === 'magicos-phone' && d.type === 'call') {
    if (d.state === 'incoming') {
      addLockNotification('Điện thoại', 'Cuộc gọi đến: ' + (d.name || 'Số lạ'), '<i class="fa-solid fa-phone"></i>');
      activeCallState = 'incoming';
      activeCallName = d.name || '';
      applyCallIslandState();
    } else if (d.state === 'connected') {
      activeCallState = 'connected';
      activeCallName = d.name || '';
      applyCallIslandState();
    } else if (d.state === 'ended' || d.state === 'declined') {
      activeCallState = null;
      activeCallName = '';
      hideCallIsland();
    }
  }
  // Man hinh cuoc goi (phone-app.html) chay trong iframe rieng nen khong the
  // goi thang applyStatusBarTheme()/doc bien phoneCallScreenActive cua trang
  // nay - no bao qua postMessage moi khi giao dien cuoc goi (nen toi den) hien
  // ra hoac an di, va o day minh cap nhat status bar/home indicator ngay lap
  // tuc cho dung mau.
  if (d.source === 'magicos-phone' && d.type === 'callScreenTheme') {
    phoneCallScreenActive = !!d.dark;
    applyStatusBarTheme(phoneCallScreenActive ? null : 'app-phone');
  }
});
const sensorDefault = document.getElementById('sensor-default');
const contents = {
  faceid: document.getElementById('content-faceid'),
  warning: document.getElementById('content-warning'),
  call: document.getElementById('content-call'),
  penalty: document.getElementById('content-penalty')
};
let autoCloseTimeout;
let resetTextTimeout;
const ISLAND_STATE_WIDTH = { default: 110, faceid: 145, warning: 300, 'call-ring': 235, 'call-active': 138, penalty: 148 };
let lastClockShift = 0;
let lastRightShift = 0;
let currentIslandState = 'default';
function applyIslandPushReflow(state) {
  const container = document.getElementById('phone-container');
  const sbLeftEl = document.querySelector('.sb-left');
  const sbRightEl = document.getElementById('sb-right');
  const iconsGroupEl = document.getElementById('sb-icons-group');
  if (!container || !sbLeftEl || !sbRightEl) return;
  const phoneRect = container.getBoundingClientRect();
  if (!phoneRect.width) return;
  const EDGE_MARGIN = 6;
  const BUFFER = 12;
  let islandWidth = ISLAND_STATE_WIDTH[state] ?? ISLAND_STATE_WIDTH.default;
  islandWidth = Math.min(islandWidth, phoneRect.width * 0.9);
  const islandCenterX = phoneRect.left + phoneRect.width / 2;
  const islandLeft = islandCenterX - islandWidth / 2;
  const islandRight = islandCenterX + islandWidth / 2;
  const clockRect = sbLeftEl.getBoundingClientRect();
  const clockNaturalLeft = clockRect.left - lastClockShift;
  const clockNaturalRight = clockRect.right - lastClockShift;
  const rightRect = sbRightEl.getBoundingClientRect();
  const rightNaturalLeft = rightRect.left - lastRightShift;
  const rightNaturalRight = rightRect.right - lastRightShift;
  const rightIconEls = (iconsGroupEl ? Array.from(iconsGroupEl.children) : []).filter(Boolean);
  const rightIconNaturalRects = rightIconEls.map(el => {
      const r = el.getBoundingClientRect();
      return { el, left: r.left - lastRightShift, width: r.width };
  });
  let clockShift = 0;
  const clockOverlap = (clockNaturalRight + BUFFER) - islandLeft;
  if (clockOverlap > 0) {
      const maxClockShift = Math.max(0, clockNaturalLeft - (phoneRect.left + EDGE_MARGIN));
      clockShift = -Math.min(clockOverlap, maxClockShift);
  }
  lastClockShift = clockShift;
  sbLeftEl.style.transform = clockShift ? `translateX(${clockShift}px)` : '';
  let rightShift = 0;
  const rightOverlap = (islandRight + BUFFER) - rightNaturalLeft;
  if (rightOverlap > 0) {
      const maxRightShift = Math.max(0, (phoneRect.right - EDGE_MARGIN) - rightNaturalRight);
      rightShift = Math.min(rightOverlap, maxRightShift);
  }
  lastRightShift = rightShift;
  sbRightEl.style.transform = rightShift ? `translateX(${rightShift}px)` : '';
  rightIconNaturalRects.forEach(({ el, left, width }) => {
      if (width === 0) return;
      const targetLeft = left + rightShift;
      const stillCovered = (islandRight + BUFFER) > targetLeft;
      el.style.transition = 'opacity 0.25s ease';
      el.style.opacity = stillCovered ? '0' : '';
      el.style.pointerEvents = stillCovered ? 'none' : '';
  });
}
function toggleReflow(state) {
  currentIslandState = state;
  if (state === 'enroll') {
      statusBar.style.opacity = '0';
      statusBar.style.pointerEvents = 'none';
      return;
  }
  statusBar.style.opacity = '';
  statusBar.style.pointerEvents = '';
  const isWide = state !== 'default';
  if (isWide) statusBar.classList.add('status-bar-reflow');
  else statusBar.classList.remove('status-bar-reflow');
  applyIslandPushReflow(state);
}
function hideAllContents() {
  Object.values(contents).forEach(el => el.classList.remove('show-content'));
  sensorDefault.style.opacity = '0';
}
function resetIsland() {
  clearTimeout(autoCloseTimeout);
  clearTimeout(resetTextTimeout);
  island.className = 'state-default island-animating';
  island.classList.remove('success');
  hideAllContents();
  toggleReflow('default');
  island.style.boxShadow = '';
  const faceContent = document.getElementById('content-faceid');
  const faceText = document.getElementById('face-text');
  if (faceContent) faceContent.classList.remove('faceid-success', 'faceid-unlocking');
  const faceLockIconEl = document.getElementById('face-lock-icon');
  if (faceLockIconEl) { faceLockIconEl.classList.remove('fa-lock-open'); faceLockIconEl.classList.add('fa-lock'); }
  if (faceText) { faceText.innerText = "Face ID"; faceText.style.color = "#fff"; }
  setTimeout(() => {
      if (island.classList.contains('state-default')) sensorDefault.style.opacity = '1';
  }, 300);
}
let isPageSwiping = false;
function showWarning(e) {
  if (isPageSwiping) return;
  if (e) e.stopPropagation();
  addLockNotification('Hệ thống', 'THIẾT BỊ KHÔNG HỖ TRỢ');
  if (navigator.vibrate) navigator.vibrate(50);
  clearTimeout(resetTextTimeout);
  island.className = 'state-warning island-animating no-swipe';
  hideAllContents();
  document.querySelector('.warning-title').textContent = 'CẢNH BÁO';
  document.querySelector('.warning-title').style.color = '#ff3b30';
  document.querySelector('.warning-sub').textContent = 'Thiết bị không được hỗ trợ';
  const warningIcon = document.querySelector('.warning-icon');
  warningIcon.innerHTML = '<svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M10.3 4 2.5 18a2 2 0 0 0 1.7 3h15.6a2 2 0 0 0 1.7-3L13.7 4a2 2 0 0 0-3.4 0Z"/><path d="M12 9v5m0 2v2"/></svg>';
  warningIcon.style.color = '#ff3b30';
  warningIcon.style.background = 'rgba(255,59,48,.15)';
  island.style.boxShadow = '';
  contents.warning.classList.add('show-content');
  toggleReflow('warning');
  clearTimeout(autoCloseTimeout);
  autoCloseTimeout = setTimeout(() => { closeTransientIsland(); }, 2600);
}
function showNotification(msg, type = 'error', iconHtml = null, sourceName = 'Hệ thống') {
  addLockNotification(sourceName, msg, iconHtml);
  if (island.classList.contains('state-maintenance')) return;
  if (navigator.vibrate) navigator.vibrate(50);
  clearTimeout(resetTextTimeout);
  island.className = 'state-warning island-animating no-swipe';
  hideAllContents();
  const warningTitle = document.querySelector('.warning-title');
  const warningSub = document.querySelector('.warning-sub');
  const warningIcon = document.querySelector('.warning-icon');
  if (!window.originalWarningTitleColor) {
      window.originalWarningTitleColor = warningTitle.style.color || "#ff3b30";
      window.originalWarningIconHTML = warningIcon.innerHTML;
      window.originalWarningIconColor = warningIcon.style.color || "#ff3b30";
      window.originalWarningIconBg = warningIcon.style.background || "rgba(255, 59, 48, 0.15)";
      window.originalIslandShadow = island.style.boxShadow;
  }
  if (type === 'success') {
      warningTitle.innerText = "THÔNG BÁO";
      warningTitle.style.color = "#34c759";
      warningIcon.innerHTML = iconHtml || '<i class="fa-solid fa-circle-check"></i>';
      warningIcon.style.color = "#34c759";
      warningIcon.style.background = "rgba(52, 199, 89, 0.15)";
      island.style.boxShadow = "0 10px 30px rgba(52, 199, 89, 0.2), inset 0 0 0 1px rgba(255,255,255,0.05)";
  } else if (type === 'info') {
      warningTitle.innerText = "THÔNG BÁO";
      warningTitle.style.color = "#0a84ff";
      warningIcon.innerHTML = iconHtml || '<i class="fa-solid fa-circle-info"></i>';
      warningIcon.style.color = "#0a84ff";
      warningIcon.style.background = "rgba(10, 132, 255, 0.15)";
      island.style.boxShadow = "0 10px 30px rgba(10, 132, 255, 0.2), inset 0 0 0 1px rgba(255,255,255,0.05)";
  } else {
      warningTitle.innerText = "CẢNH BÁO";
      warningTitle.style.color = "#ff3b30";
      warningIcon.innerHTML = iconHtml || '<i class="fa-solid fa-triangle-exclamation"></i>';
      warningIcon.style.color = "#ff3b30";
      warningIcon.style.background = "rgba(255, 59, 48, 0.15)";
      island.style.boxShadow = "0 10px 30px rgba(255, 59, 48, 0.2), inset 0 0 0 1px rgba(255,255,255,0.05)";
  }
  warningSub.innerText = msg;
  contents.warning.classList.add('show-content');
  toggleReflow('warning');
  clearTimeout(autoCloseTimeout);
  autoCloseTimeout = setTimeout(() => {
      closeTransientIsland();
      resetTextTimeout = setTimeout(() => {
          warningTitle.innerText = "HỆ THỐNG THÔNG BÁO";
          warningTitle.style.color = window.originalWarningTitleColor;
          warningIcon.innerHTML = window.originalWarningIconHTML;
          warningIcon.style.color = window.originalWarningIconColor;
          warningIcon.style.background = window.originalWarningIconBg;
          island.style.boxShadow = window.originalIslandShadow;
          warningSub.innerText = "THIẾT BỊ KHÔNG HỖ TRỢ";
      }, 500);
  }, 3000);
}
function triggerFaceID(isUnlock = false) {
  island.className = 'state-faceid island-animating' + (isUnlock ? ' no-swipe' : '');
  hideAllContents();
  contents.faceid.classList.add('show-content');
  toggleReflow('faceid');
  const faceText = document.getElementById('face-text');
  if (isUnlock) faceText.innerText = "Mở khóa"; else faceText.innerText = "Face ID";
  let scanDelay = Math.floor(Math.random() * 1500) + 800;
  setTimeout(() => {
      const faceContentEl = document.getElementById('content-faceid');
      if (isUnlock) {
          // Thay vi dau tick, hien icon khoa xoay + "bung" tu khoa kin sang khoa mo
          faceContentEl.classList.add('faceid-unlocking');
          const lockIconEl = document.getElementById('face-lock-icon');
          setTimeout(() => {
              if (lockIconEl) { lockIconEl.classList.remove('fa-lock'); lockIconEl.classList.add('fa-lock-open'); }
          }, 270);
          faceText.innerText = "Đã mở khóa"; faceText.style.color = "#34c759";
      } else {
          faceContentEl.classList.add('faceid-success');
          faceText.innerText = "Thành công"; faceText.style.color = "#34c759";
          autoCloseTimeout = setTimeout(closeTransientIsland, 1200);
      }
  }, scanDelay);
}
/* ===== Dynamic Island: hoat canh khi co cuoc goi den (Live Activity kieu iOS) ===== */
let callDurationInterval = null;
let callStartTs = 0;
/* Trang thai cuoc goi hien tai (doc lap voi UI cua island): null | 'incoming' | 'connected'.
   Duoc cap nhat tu message cua app Dien thoai va dung de biet co nen ve lai
   "Live Activity" cuoc goi tren island hay khong sau khi mot lop UI tam thoi
   (thong bao, canh bao, Face ID...) da dong lai. */
let activeCallState = null;
let activeCallName = '';
/* Nguoi dung co dang thuc su nhin thay man hinh cuoc goi (dang goi den / dang
   trong cuoc) cua app Dien thoai hay khong: may da mo khoa, khong dang mo app
   switcher, va app-phone la app dang o tren cung. Khi dung true, Dynamic Island
   KHONG duoc mo rong de tranh trung lap voi giao dien app dang hien. */
function isPhoneCallScreenForeground() {
  if (!document.body.classList.contains('unlocked')) return false;
  const switcherEl = document.getElementById('app-switcher');
  if (switcherEl && switcherEl.classList.contains('open')) return false;
  return foregroundAppId === 'app-phone';
}
/* Dong bo trang thai "Live Activity" cuoc goi tren island voi tien canh hien tai.
   Khong dong cham gi neu island dang hien 1 lop tam thoi khac (thong bao/canh
   bao/Face ID) - lop do se tu goi closeTransientIsland() khi ket thuc. */
function applyCallIslandState() {
  if (island.classList.contains('state-maintenance') || island.classList.contains('state-warning') || island.classList.contains('state-faceid')) return;
  if (activeCallState && !isPhoneCallScreenForeground()) {
    if (activeCallState === 'incoming') {
      if (!island.classList.contains('state-call-ring')) showCallIsland(activeCallName);
    } else if (activeCallState === 'connected') {
      if (!island.classList.contains('state-call-active')) connectCallIsland(activeCallName);
    }
  } else if (island.classList.contains('state-call-ring') || island.classList.contains('state-call-active')) {
    resetIsland();
  }
}
/* Dung khi 1 lop UI tam thoi tren island (thong bao, canh bao, Face ID...) vua
   ket thuc: thay vi luon quay ve trang thai mac dinh, khoi phuc lai dung "Live
   Activity" cuoc goi dang giang do (neu co va dang khong o man hinh cuoc goi
   trong app), de khong bi "mat" viec dang nghe/goi khi co thong bao xen ngang. */
function closeTransientIsland() {
  if (activeCallState && !isPhoneCallScreenForeground()) {
    if (activeCallState === 'incoming') showCallIsland(activeCallName);
    else connectCallIsland(activeCallName);
  } else {
    resetIsland();
  }
}
function showCallIsland(name) {
  clearTimeout(autoCloseTimeout);
  clearTimeout(resetTextTimeout);
  clearInterval(callDurationInterval);
  if (navigator.vibrate) navigator.vibrate(60);
  island.className = 'state-call-ring island-animating no-swipe';
  hideAllContents();
  const nameEl = document.getElementById('call-name-text');
  if (nameEl) nameEl.textContent = name || 'Số lạ';
  contents.call.classList.add('show-content');
  toggleReflow('call-ring');
}
function connectCallIsland(name) {
  clearTimeout(autoCloseTimeout);
  island.className = 'state-call-active island-animating no-swipe';
  hideAllContents();
  const nameEl = document.getElementById('call-name-text');
  if (nameEl) nameEl.textContent = name || 'Số lạ';
  contents.call.classList.add('show-content');
  toggleReflow('call-active');
  callStartTs = Date.now();
  clearInterval(callDurationInterval);
  updateCallDuration(name);
  callDurationInterval = setInterval(function () { updateCallDuration(name); }, 1000);
}
function updateCallDuration(name) {
  const secs = Math.floor((Date.now() - callStartTs) / 1000);
  const m = Math.floor(secs / 60), s = secs % 60;
  const stamp = (m < 10 ? '0' + m : m) + ':' + (s < 10 ? '0' + s : s);
  const nameEl = document.getElementById('call-name-text');
  if (nameEl) nameEl.textContent = (name || 'Số lạ') + ' · ' + stamp;
}
function hideCallIsland() {
  clearInterval(callDurationInterval);
  // Neu island dang hien 1 lop tam thoi khac (vi du canh bao "het token") thi
  // KHONG duoc de/ghi de len no - truoc day cuoc goi ket thuc se goi resetIsland()
  // ngay lap tuc va xoa mat thong bao canh bao vua hien ra chi sau vai chuc ms.
  if (island.classList.contains('state-maintenance') || island.classList.contains('state-warning') || island.classList.contains('state-faceid')) return;
  resetIsland();
}
/* ===== Nghe / Tu choi ngay tren Dynamic Island + cham vao vung trong de mo giao dien cuoc goi ===== */
function sendPhoneAppMessage(action, name) {
  const iframe = document.getElementById('phone-iframe');
  if (iframe && iframe.contentWindow) {
    try { iframe.contentWindow.postMessage({ source: 'magicos-island', action: action, name: name }, '*'); } catch (e) {}
  }
}
/* Day 1 the thong bao thuc su vao thanh thong bao (giao dien vuot xuong tu
   goc trai man hinh, dung "lock-screen-ui" lam giao dien hien thi) - khac voi
   showNotification() chi la 1 lop noi bat thoang qua tren Dynamic Island. */
const NOTIFICATION_HISTORY_KEY = 'magicos_notifications_v2';
let notificationHistory = [];
let notifIdSeq = 1;
function nextNotifId() { return Date.now() + '-' + (notifIdSeq++); }
try {
  const saved = JSON.parse(localStorage.getItem(NOTIFICATION_HISTORY_KEY) || '[]');
  if (Array.isArray(saved)) {
    notificationHistory = saved.filter(n => n && typeof n.message === 'string' && Number.isFinite(n.at));
    // Du lieu cu (truoc khi co tinh nang xoa) co the chua thieu id - gan bo sung
    // de moi the thong bao co 1 dinh danh rieng, dung khi xoa dung dong.
    notificationHistory.forEach(n => { if (!n.id) n.id = nextNotifId(); });
  }
} catch (e) {}
/* Xoa 1 dong thong bao: bay dong ra khoi mang du lieu + luu lai, roi choi
   hieu ung 2 buoc kieu iOS - the kinh bay het sang trai va mo dan, SAU DO
   moi thu gon chieu cao dong lai de cac the ben duoi truot len lap khoang
   trong, thay vi bien mat cung luc trong khi cac the khac dung im. */
function deleteNotifRow(row, item, id) {
  if (!row || row.dataset.deleting) return;
  row.dataset.deleting = '1';
  const idx = notificationHistory.findIndex(n => n.id === id);
  if (idx > -1) notificationHistory.splice(idx, 1);
  updateClearAllVisibility();
  try { localStorage.setItem(NOTIFICATION_HISTORY_KEY, JSON.stringify(notificationHistory)); }
  catch (e) { console.warn('Không thể lưu lịch sử thông báo trên thiết bị', e); }
  if (navigator.vibrate) { try { navigator.vibrate(16); } catch (e) {} }
  item.classList.remove('notif-dragging');
  item.style.transition = 'transform 0.26s cubic-bezier(.4,0,.6,1), opacity 0.22s ease-in';
  item.style.transform = 'translateX(-115%)';
  item.style.opacity = '0';
  const h = row.getBoundingClientRect().height;
  row.style.maxHeight = h + 'px';
  row.style.overflow = 'hidden';
  setTimeout(() => {
    row.style.transition = 'max-height 0.3s cubic-bezier(.4,0,.2,1), margin-bottom 0.3s cubic-bezier(.4,0,.2,1), opacity 0.22s ease';
    row.style.maxHeight = '0px';
    row.style.marginBottom = '-12px';
    row.style.opacity = '0';
  }, 170);
  row.addEventListener('transitionend', function onEnd(e) {
    if (e.propertyName !== 'max-height') return;
    row.removeEventListener('transitionend', onEnd);
    row.remove();
  });
}
/* Gan cu chi vuot ngang cho 1 the thong bao: chi cho vuot SANG TRAI, co
   luc can (resistance) khi keo qua het muc lo nen do, va 2 nguong hanh vi -
   vuot nhe thi ho ben do de lo nut Xoa (cham vao nut se xoa), vuot manh/xa
   qua nguong thi tu dong bay di xoa luon, giong dung cam giac Mail/Tin nhan
   tren iPhone. */
function bindNotifSwipe(row, item, entry) {
  const REVEAL = 92;      // khoang lo nen do khi "ho" lai cho nguoi dung cham nut Xoa
  const TRIGGER = 108;    // vuot qua khoang nay roi tha tay se tu dong xoa
  let startX = 0, startY = 0, dx = 0, dragging = false, decided = false, horizontal = false, pid = null;
  function setOpen(px, settle) {
    item.style.transform = `translateX(${px}px)`;
    // Do rong lop nen do = dung khoang the kinh da truot di, nen lop do chi nam o
    // phan trong ben phai va KHONG BAO GIO nam phia sau the kinh (backdrop-filter
    // se khong con hut mau do -> the giu nguyen mau Liquid Glass).
    row.classList.toggle('notif-settling', !!settle);
    row.style.setProperty('--reveal', Math.max(0, -px) + 'px');
    row.classList.toggle('swipe-open', px < -28);
    item.classList.toggle('notif-swiping', px < -4);
  }
  function onDown(e) {
    if (e.pointerType === 'mouse' && e.button !== 0) return;
    if (row.dataset.deleting) return;
    startX = e.clientX; startY = e.clientY; dx = 0; dragging = true; decided = false; horizontal = false;
    item.classList.add('notif-dragging');
    pid = e.pointerId;
    try { item.setPointerCapture(pid); } catch (err) {}
  }
  function onMove(e) {
    if (!dragging) return;
    const curDx = e.clientX - startX, curDy = e.clientY - startY;
    if (!decided) {
      if (Math.abs(curDx) < 6 && Math.abs(curDy) < 6) return;
      decided = true;
      horizontal = Math.abs(curDx) > Math.abs(curDy);
      if (!horizontal) { dragging = false; item.classList.remove('notif-dragging'); return; }
    }
    if (!horizontal) return;
    if (e.cancelable) e.preventDefault();
    // Neu dang o trang thai "ho mo" san, cong them do lech de keo tiep tu do.
    const base = item.__openOffset || 0;
    let raw = base + curDx;
    if (raw > 0) raw = raw * 0.22; // khang luc rat manh neu co keo nguoc ve phai qua vi tri dong
    else if (raw < -TRIGGER) raw = -TRIGGER + (raw + TRIGGER) * 0.24; // khang luc khi keo qua nguong xoa
    dx = raw;
    setOpen(raw, false);
  }
  function onUp() {
    if (!dragging) return;
    dragging = false;
    item.classList.remove('notif-dragging');
    if (pid !== null) { try { item.releasePointerCapture(pid); } catch (err) {} }
    if (dx <= -TRIGGER * 0.92) {
      deleteNotifRow(row, item, entry.id);
      return;
    } else if (dx < -32) {
      item.__openOffset = -REVEAL;
      setOpen(-REVEAL, true);
    } else {
      item.__openOffset = 0;
      setOpen(0, true);
    }
  }
  item.addEventListener('pointerdown', onDown);
  item.addEventListener('pointermove', onMove);
  item.addEventListener('pointerup', onUp);
  item.addEventListener('pointercancel', onUp);
  // Cham thang vao vung nen do (khi da ho mo) se xoa ngay lap tuc.
  const delBg = row.querySelector('.ls-notif-del-bg');
  if (delBg) delBg.addEventListener('click', () => deleteNotifRow(row, item, entry.id));
  // Cham vao chinh the (khi dang ho mo san) se dong lai thay vi lam gi khac.
  item.addEventListener('click', (e) => {
    if ((item.__openOffset || 0) < 0) { e.stopPropagation(); item.__openOffset = 0; setOpen(0, true); }
  });
}
function renderLockNotification(entry, animate = true, iconHtml = null) {
  const list = document.getElementById('ls-notif-list');
  if (!list) return;
  if (!entry.id) entry.id = nextNotifId();
  const row = document.createElement('div');
  row.className = 'ls-notif-row';
  const delBg = document.createElement('div');
  delBg.className = 'ls-notif-del-bg';
  delBg.innerHTML = '<span class="ls-notif-del-label">Xóa</span><span class="ls-notif-del-icon"><i class="fa-solid fa-trash-can"></i></span>';
  const item = document.createElement('div');
  item.className = 'ls-notif-item';
  if (!animate) { item.style.animation = 'none'; item.style.opacity = '1'; item.style.transform = 'none'; }
  else {
    // NGUYEN NHAN THE BI DO + KHONG KEO DUOC: animation lsNotifIn dung fill-mode
    // "forwards" nen sau khi vao xong no van GHIM transform/opacity cua the, de len
    // moi transform inline do JS vuot xoa dat (animation luon thang inline style).
    // Ket qua: the kinh dung yen 1 cho trong khi lop nen do bi lo ra dang sau ->
    // kinh hut mau do. Phai go animation ngay khi no chay xong de the di chuyen duoc.
    item.addEventListener('animationend', function onIn(ev) {
      if (ev.animationName !== 'lsNotifIn') return;
      item.removeEventListener('animationend', onIn);
      item.style.animation = 'none'; item.style.opacity = '1'; item.style.transform = 'none';
    });
  }
  const icon = document.createElement('div'); icon.className = 'ls-notif-icon';
  icon.innerHTML = iconHtml || '<i class="fa-solid fa-bell"></i>';
  const body = document.createElement('div'); body.className = 'ls-notif-body';
  const top = document.createElement('div'); top.className = 'ls-notif-top';
  const app = document.createElement('span'); app.className = 'ls-notif-app'; app.textContent = entry.appName;
  const time = document.createElement('time'); time.className = 'ls-notif-time';
  const when = new Date(entry.at); time.dateTime = when.toISOString();
  time.textContent = when.toLocaleTimeString('vi-VN', {hour:'2-digit', minute:'2-digit'});
  time.title = when.toLocaleString('vi-VN');
  const text = document.createElement('div'); text.className = 'ls-notif-text'; text.textContent = entry.message;
  top.append(app,time); body.append(top,text); item.append(icon,body);
  row.append(delBg, item);
  bindNotifSwipe(row, item, entry);
  const previousTop = list.scrollTop;
  list.prepend(row);
  // Preserve the item being read when new notifications arrive.
  if (previousTop > 8) list.scrollTop = previousTop + row.offsetHeight + 12;
}
function addLockNotification(appName, message, iconHtml) {
  const entry = {id:nextNotifId(),appName:String(appName || 'Hệ thống'),message:String(message || ''),at:Date.now()};
  notificationHistory.push(entry);
  renderLockNotification(entry, true, iconHtml);
  updateClearAllVisibility();
  try { localStorage.setItem(NOTIFICATION_HISTORY_KEY, JSON.stringify(notificationHistory)); }
  catch (e) { console.warn('Không thể lưu lịch sử thông báo trên thiết bị', e); }
}
notificationHistory.forEach(entry => renderLockNotification(entry, false));
/* Hien/an nut "Xoa tat ca": chi hien khi con it nhat 1 thong bao, voi hieu
   ung pop nho moi lan so luong thay doi tu 0 -> co gi do (bat ngo xuat hien
   dep hon la bat tat ngang). */
function updateClearAllVisibility() {
  const btn = document.getElementById('ls-notif-clearall');
  if (!btn) return;
  const shouldShow = notificationHistory.length > 0;
  const wasShown = btn.classList.contains('show');
  btn.classList.toggle('show', shouldShow);
  if (shouldShow && !wasShown) {
    btn.classList.remove('pop'); void btn.offsetWidth; btn.classList.add('pop');
  }
}
updateClearAllVisibility();
/* Xoa toan bo thong bao cung luc: moi the kinh lan luot bay sang phai + mo
   dan (le tung dong theo thu tu, cach nhau vai chuc mili giay de tao hieu
   ung "cuon" thay vi bien mat dong loat trong het mat), roi moi thu gon
   chieu cao dong lai cho gon gang - dung 2 buoc nhu deleteNotifRow nhung
   theo huong nguoc lai (phai) de phan biet ro voi thao tac vuot xoa tung
   dong (trai), va co do tre le nhau cho ca cum bay di mot cach song dong. */
function clearAllNotifications() {
  const btn = document.getElementById('ls-notif-clearall');
  const list = document.getElementById('ls-notif-list');
  if (!list || !notificationHistory.length || (btn && btn.classList.contains('clearing'))) return;
  if (navigator.vibrate) { try { navigator.vibrate([16, 30, 18]); } catch (e) {} }
  if (btn) { btn.classList.add('clearing'); btn.classList.remove('show'); }
  const rows = Array.prototype.slice.call(list.querySelectorAll('.ls-notif-row'));
  notificationHistory = [];
  try { localStorage.setItem(NOTIFICATION_HISTORY_KEY, JSON.stringify(notificationHistory)); }
  catch (e) { console.warn('Không thể lưu lịch sử thông báo trên thiết bị', e); }
  if (!rows.length) { if (btn) btn.classList.remove('clearing'); return; }
  rows.forEach((row, i) => {
    const item = row.querySelector('.ls-notif-item');
    setTimeout(() => {
      if (item) {
        item.style.transition = 'transform 0.32s cubic-bezier(.4,0,.6,1), opacity 0.26s ease-in';
        item.style.transform = 'translateX(115%) scale(0.92) rotate(3deg)';
        item.style.opacity = '0';
      }
      const h = row.getBoundingClientRect().height;
      row.style.maxHeight = h + 'px';
      row.style.overflow = 'hidden';
      requestAnimationFrame(() => {
        row.style.transition = 'max-height 0.26s cubic-bezier(.4,0,.2,1) 0.18s, margin-bottom 0.26s cubic-bezier(.4,0,.2,1) 0.18s, opacity 0.2s ease 0.18s';
        row.style.maxHeight = '0px';
        row.style.opacity = '0';
      });
      setTimeout(() => { row.remove(); if (i === rows.length - 1 && btn) btn.classList.remove('clearing'); }, 480);
    }, i * 55);
  });
}
window.clearAllNotifications = clearAllNotifications;
window.addLockNotification = addLockNotification;
function openPhoneAppFromIsland() {
  const appId = 'app-phone';
  const el = document.getElementById(appId);
  const container = document.getElementById('phone-container');
  if (!el || !container) return;
  /* Neu App Switcher dang mo, app-phone (hoac bat ky app nao dang duoc chon)
     co the dang bi he thong preview cua switcher (placeAppInPreview) dieu
     khien transform + clip-path + z-index de "chieu" no vao vua khung panel
     nho ben trong switcher - VAN LA CHINH DOM NODE THAT, khong phai ban sao.
     Neu cu de nguyen switcher mo roi ghi de transform/opacity o duoi de zoom
     "mo app" thang tu day, 2 he thong transform se danh nhau tren cung 1
     node: clip-path cu cua panel (tinh theo toa do rieng cua panel) van con
     nguyen trong khi transform bi keo ve toa do full-man-hinh khac hoan
     toan - khien phan noi dung hien ra bi cat sai vi tri/kich thuoc, nhin
     như panel/man hinh bi den xi. Vi vay phai THOAT SWITCHER va TRA APP VE
     TRANG THAI GOC (giong switcherOpenApp/switcherResumeApp da lam) TRUOC
     khi bat dau hieu ung zoom mo tu Dynamic Island. */
  if (typeof switcherOpen !== 'undefined' && switcherOpen) {
    if (typeof detachAllFromPreview === 'function') detachAllFromPreview();
    if (typeof closeAppSwitcher === 'function') closeAppSwitcher();
  }
  /* Chi bo qua khi app Dien thoai THUC SU dang la app o tren cung (nguoi dung
     dang nhin thay no roi). Truoc day dieu kien nay chi kiem tra
     el.style.display === 'block' - nhung display cua app-phone co the van
     con la 'block' tu lan mo truoc do (vi du da mo app Dien thoai, roi mo
     tiep app-admin de len tren ma khong dong app Dien thoai lai), trong khi
     app dang thuc su hien tren man hinh la app khac (vd app-admin). Gap dung
     truong hop nay, ham se return ngay o day va KHONG LAM GI CA khi nguoi
     dung cham vao Dynamic Island - dung nhu loi "bam vao khong chuyen man
     hinh, bi chan luon" ma nguoi dung gap phai. */
  if (foregroundAppId === 'app-phone' && el.style.display === 'block') return;
  const phoneIconBox = document.querySelector('.phone-app-box');
  if (phoneIconBox) appOriginIcons[appId] = phoneIconBox;
  applyStatusBarTheme(appId);
  const islandRect = island.getBoundingClientRect();
  const containerRect = container.getBoundingClientRect();
  /* Neu island dang hien "Live Activity" cuoc goi (dang do chuong hoac dang
     nghe), thu gon no ve trang thai mac dinh NGAY LAP TUC (khong animation)
     truoc khi bat dau hieu ung zoom-mo-app. islandRect da chup lai kich thuoc
     "phinh to" ngay tren nen lam goc zoom, nen hieu ung mo app van bat dau
     dung vi tri nguoi dung vua cham; chi la ban than island khong con tu co
     lai mot cach ganh doi/xung dot voi hieu ung zoom (truoc day gay cam giac
     island "bien mat" giat cuc khi mo giao dien nghe may tu island). */
  if (island.classList.contains('state-call-ring') || island.classList.contains('state-call-active')) {
    island.style.transition = 'none';
    resetIsland();
    void island.offsetWidth;
    island.style.transition = '';
  }
  const scaleX = Math.max(islandRect.width / containerRect.width, 0.001);
  const scaleY = Math.max(islandRect.height / containerRect.height, 0.001);
  const originX = islandRect.left - containerRect.left;
  const originY = islandRect.top - containerRect.top;
  const avgScale = (scaleX + scaleY) / 2;
  el.style.display = 'block';
  /* An ngay cac app khac dang mo o duoi (vd app-admin) NGAY LUC NAY: vi tat ca
     .simple-app dung chung 1 z-index (100), app nao dung SAU trong DOM se
     luon de len tren bat ke thu tu mo truoc/sau. Neu khong an di, app dang mo
     do (vi du app-admin, nam sau app-phone trong DOM) se tiep tuc phu kin va
     che mat hoan toan giao dien cuoc goi vua duoc "mo" ngam ben duoi, khien
     nguoi dung cham vao Dynamic Island ma tuong nhu khong co phan ung gi (bi
     "chan"), dung ra phai chuyen thang sang man hinh cuoc goi. */
  activeAppsList.forEach(function (otherId) {
    if (otherId === appId) return;
    const otherEl = document.getElementById(otherId);
    if (otherEl) otherEl.style.display = 'none';
  });
  el.style.animation = 'none';
  el.style.transition = 'none';
  el.style.transformOrigin = '0 0';
  el.style.transform = `translate(${originX}px, ${originY}px) scale(${scaleX}, ${scaleY})`;
  el.style.borderRadius = (26 / avgScale) + 'px';
  el.style.opacity = '0';
  el.style.filter = 'blur(7px)';
  void el.offsetWidth;
  el.style.transition = 'transform 0.44s var(--ios-smooth), border-radius 0.44s var(--ios-smooth), opacity 0.3s ease-out, filter 0.34s ease-out';
  requestAnimationFrame(() => {
      el.style.transform = 'translate(0px, 0px) scale(1, 1)';
      el.style.borderRadius = '0px';
      el.style.opacity = '1';
      el.style.filter = 'blur(0px)';
  });
  clearTimeout(el.__zoomCleanupTimer);
  el.__zoomCleanupTimer = setTimeout(() => { el.style.transition = ''; }, 480);
  trackApp(appId);
  if (navigator.vibrate) navigator.vibrate(12);
}
const contentCallEl = document.getElementById('content-call');
if (contentCallEl) {
  contentCallEl.addEventListener('click', (e) => {
    if (e.target.closest('.cia-btn')) return;
    openPhoneAppFromIsland();
  });
}
const islandAcceptBtn = document.getElementById('islandAcceptBtn');
if (islandAcceptBtn) {
  islandAcceptBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    if (navigator.vibrate) navigator.vibrate(16);
    sendPhoneAppMessage('answer');
  });
}
const islandDeclineBtn = document.getElementById('islandDeclineBtn');
if (islandDeclineBtn) {
  islandDeclineBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    if (navigator.vibrate) navigator.vibrate(16);
    sendPhoneAppMessage('decline');
  });
}
island.addEventListener('click', (e) => {
  if (island.classList.contains('state-maintenance')) { e.stopPropagation(); dismissMaintenance(); return; }
  if (!document.body.classList.contains('unlocked') && !island.classList.contains('state-warning')) return;
  if (Math.abs(parseFloat(island.style.getPropertyValue('--drag-y')) || 0) > 5) return;
  if (island.classList.contains('state-warning')) closeTransientIsland();
});
let isDragging = false; let startY = 0; let startX = 0;
const handleStart = (e) => {
  isDragging = true;
  startY = e.type.includes('mouse') ? e.clientY : e.touches[0].clientY;
  startX = e.type.includes('mouse') ? e.clientX : e.touches[0].clientX;
  island.classList.remove('island-animating');
};
const handleMove = (e) => {
  if (!isDragging) return;
  let deltaY = (e.type.includes('mouse') ? e.clientY : e.touches[0].clientY) - startY;
  if (deltaY < 0) {
    let resistanceY = -Math.pow(Math.abs(deltaY), 0.7) * 1.5;
    island.style.setProperty('--drag-y', `${resistanceY * 0.4}px`);
    island.style.setProperty('--drag-scale-y', Math.max(0.9, 1 + (resistanceY / 500)));
  }
};
const handleEnd = (e) => {
  if (!isDragging) return;
  isDragging = false;
  let deltaY = (e.type.includes('mouse') ? e.clientY : e.changedTouches[0].clientY) - startY;
  island.classList.add('island-animating');
  requestAnimationFrame(() => {
      island.style.setProperty('--drag-y', '0px');
      island.style.setProperty('--drag-scale-y', '1');
      island.style.setProperty('--drag-scale-x', '1');
  });
  if (deltaY < -25 && !island.classList.contains('no-swipe')) resetIsland();
};
island.addEventListener('mousedown', handleStart);
window.addEventListener('mousemove', handleMove);
window.addEventListener('mouseup', handleEnd);
window.addEventListener('mouseleave', handleEnd);
island.addEventListener('touchstart', handleStart, {passive: true});
window.addEventListener('touchmove', handleMove, {passive: true});
window.addEventListener('touchend', handleEnd);
const homeHitbox = document.getElementById('home-indicator-hitbox');
let homeStartY = 0; let homeStartX = 0; let isSwipingUp = false; let isSwipingRight = false; let isSwipingLeft = false;
let indicator = document.getElementById('home-indicator');
let swHoldTimer = null; let swHoldFired = false; let swTouchActive = false;
let homeLockGesture = false;
let homePasscodeExitDrag = false;
// KHOA CUNG thanh da nhiem: tu luc nhap dung mat ma (unlockBusy = true, gom buoc kiem tra
// server + hieu ung Face ID + man khoa truot len) cho toi khi vao han man hinh chinh
// (unlockBusy = false), nguoi dung khong duoc vuot thanh nay. Neu de vuot duoc, nhanh
// "thoat nhap mat ma" se goi cancelPasscode() va huy ngang qua trinh mo khoa.
// Co nay duoc chot MOT LAN cho moi cu cham (luc touchstart) de ca cu vuot bat dau trong
// luc dang khoa cung bi bo qua tron ven, ke ca khi luc tha tay may da mo khoa xong.
let homeBarLocked = false;
homeHitbox.addEventListener('touchstart', e => {
  homeBarLocked = unlockBusy;
  if (homeBarLocked) {
    clearTimeout(swHoldTimer); swHoldTimer = null; swHoldFired = false; swTouchActive = false;
    isSwipingUp = isSwipingRight = isSwipingLeft = false;
    homeLockGesture = false; homePasscodeExitDrag = false;
    return;
  }
  homeLockGesture = !document.body.classList.contains('unlocked');
  if (homeLockGesture) {
    clearTimeout(swHoldTimer); swHoldTimer = null; swHoldFired = false; swTouchActive = false;
    isSwipingUp = isSwipingRight = isSwipingLeft = false;
    if (isPasscodeMode) {
      // Dang o man hinh NHAP MAT MA: beginLockSwipe() se KHONG lam gi ca vi
      // no chu dong bo qua khi isPasscodeMode dang bat (tranh xung dot voi
      // hieu ung mo passcode). Vi vay can 1 nhanh rieng o day de vuot thanh
      // da nhiem co the "thoat" khoi man hinh nhap mat ma, quay lai dung
      // man hinh khoa binh thuong - truoc day vuot o day khong co tac dung gi.
      homePasscodeExitDrag = true;
      homeStartY = e.touches[0].clientY; homeStartX = e.touches[0].clientX;
      passcodeUI.style.transition = 'none';
      return;
    }
    homePasscodeExitDrag = false;
    if (e.touches.length === 1) beginLockSwipe(e.touches[0].clientX,e.touches[0].clientY);
    return;
  }
  homePasscodeExitDrag = false;
  homeStartY = e.touches[0].clientY;
  homeStartX = e.touches[0].clientX;
  isSwipingUp = false;
  isSwipingRight = false;
  isSwipingLeft = false;
  swTouchActive = true;
  swHoldFired = false;
  clearTimeout(swHoldTimer); swHoldTimer = null;
  indicator.style.transition = 'transform 0.15s ease-out, background 0.3s';
}, {passive: true});
homeHitbox.addEventListener('touchmove', e => {
  if (homeBarLocked) { if (e.cancelable) e.preventDefault(); return; }
  if (homePasscodeExitDrag) {
    if (e.cancelable) e.preventDefault();
    const dy = Math.max(0, homeStartY - e.touches[0].clientY);
    const progress = Math.min(dy / 130, 1);
    // Keo dan passcode-ui theo tay, thu nho + mo dan de bao hieu "sap thoat".
    passcodeUI.style.transform = `translateY(${-dy * 0.4}px) scale(${1 - progress * 0.08})`;
    passcodeUI.style.opacity = String(1 - progress * 0.85);
    const lift = Math.min(dy * .12, 14);
    indicator.style.transform = `translateX(-50%) translateY(${-lift}px) scaleX(1.04)`;
    return;
  }
  if (homeLockGesture) {
    if (e.cancelable) e.preventDefault();
    moveLockSwipe(e.touches[0].clientX,e.touches[0].clientY);
    const lift = Math.min(Math.max(0,lsStartY-e.touches[0].clientY)*.12,14);
    indicator.style.transform = `translateX(-50%) translateY(${-lift}px) scaleX(1.04)`;
    return;
  }
  let currentY = e.touches[0].clientY;
  let currentX = e.touches[0].clientX;
  let deltaY = homeStartY - currentY;
  let deltaX = currentX - homeStartX;
  if (deltaY > 15 && Math.abs(deltaY) > Math.abs(deltaX)) {
      isSwipingUp = true;
      indicator.style.transform = `translateX(-50%) translateY(-${Math.min(deltaY * 0.15, 12)}px) scaleY(0.8)`;
      if (!swHoldTimer && !swHoldFired && deltaY > 120) {
          swHoldTimer = setTimeout(() => {
              swHoldTimer = null;
              if (swTouchActive && isSwipingUp && !swHoldFired) {
                  swHoldFired = true;
                  if (typeof openAppSwitcher === 'function') openAppSwitcher();
              }
          }, 1000);
      }
  } else if (!isNotifPeekOpen && deltaX > 20 && Math.abs(deltaX) > Math.abs(deltaY)) {
      isSwipingRight = true;
  } else if (!isNotifPeekOpen && deltaX < -20 && Math.abs(deltaX) > Math.abs(deltaY)) {
      isSwipingLeft = true;
  }
}, {passive: false});
homeHitbox.addEventListener('touchend', e => {
  if (homeBarLocked) { homeBarLocked = false; return; }
  swTouchActive = false;
  clearTimeout(swHoldTimer); swHoldTimer = null;
  indicator.style.transition = 'transform 0.4s var(--ios-spring-snappy), background 0.3s';
  indicator.style.transform = `translateX(-50%) translateY(0) scaleY(1)`;
  if (homePasscodeExitDrag) {
      homePasscodeExitDrag = false;
      const touch = e.changedTouches[0];
      const dy = touch ? Math.max(0, homeStartY - touch.clientY) : 0;
      const dx = touch ? Math.abs(touch.clientX - homeStartX) : 0;
      passcodeUI.style.transition = ''; // tra ve dung transition spring mac dinh cua #passcode-ui
      if (dy >= 44 && dy > dx && !unlockBusy) {
          cancelPasscode();
      } else {
          passcodeUI.style.transform = 'scale(1)';
          passcodeUI.style.opacity = '1';
      }
      return;
  }
  if (homeLockGesture) {
      homeLockGesture = false;
      const touch = e.changedTouches[0];
      if (touch) finishLockSwipe(touch.clientX,touch.clientY);
      return;
  }
  if (swHoldFired) {
      // Both touchend listeners must see the hold was handled. Reset at touchstart.
      isSwipingUp = false;
      return;
  }
  if (isSwipingUp) {
      isSwipingUp = false;
      if (isNotifPeekOpen) {
          closeNotificationPeek();
      } else if (controlCenter && controlCenter.classList.contains('open')) {
          closeControlCenter();
      } else {
          closeAllApps();
      }
  } else if (isSwipingRight) {
      isSwipingRight = false;
      if (!isNotifPeekOpen) navigateAppHistory('back');
  } else if (isSwipingLeft) {
      isSwipingLeft = false;
      if (!isNotifPeekOpen) navigateAppHistory('forward');
  }
});
homeHitbox.addEventListener('touchcancel', () => {
  if (homeBarLocked) { homeBarLocked = false; return; }
  if (homePasscodeExitDrag) {
      homePasscodeExitDrag = false;
      passcodeUI.style.transition = '';
      passcodeUI.style.transform = 'scale(1)';
      passcodeUI.style.opacity = '1';
  }
  if (homeLockGesture) finishLockSwipe(lsStartX,lsStartY,true);
  homeLockGesture = false; swTouchActive = false; swHoldFired = false;
  clearTimeout(swHoldTimer); swHoldTimer = null;
  isSwipingUp = isSwipingRight = isSwipingLeft = false;
  indicator.style.transform = 'translateX(-50%)';
}, {passive:true});
window.addEventListener('resize', () => {
  clearTimeout(window.__islandResizeTimer);
  window.__islandResizeTimer = setTimeout(() => applyIslandPushReflow(currentIslandState), 150);
});
const PHONE_SIDE_MARGIN = 15;
const PHONE_BOTTOM_MARGIN = 45;
const PORTRAIT_RADIUS = '45px';
const IPAD_RADIUS = '24px';
function applyOrientationLayout() {
  const vw = window.innerWidth;
  const vh = window.innerHeight;
  const isLandscape = vw > vh;
  phoneContainer.style.width = `${Math.max(vw - PHONE_SIDE_MARGIN * 2, 100)}px`;
  phoneContainer.style.height = `${Math.max(vh - PHONE_SIDE_MARGIN - PHONE_BOTTOM_MARGIN, 100)}px`;
  phoneContainer.style.top = `${PHONE_SIDE_MARGIN}px`;
  phoneContainer.style.left = `${PHONE_SIDE_MARGIN}px`;
  phoneContainer.style.borderRadius = isLandscape ? IPAD_RADIUS : PORTRAIT_RADIUS;
  document.body.classList.toggle('ipad-mode', isLandscape);
  clearTimeout(window.__islandResizeTimer);
  window.__islandResizeTimer = setTimeout(() => applyIslandPushReflow(currentIslandState), 150);
}
window.addEventListener('resize', applyOrientationLayout);
window.addEventListener('orientationchange', applyOrientationLayout);
applyOrientationLayout();
const controlCenter = document.getElementById('control-center');
const ccHitbox = document.getElementById('control-center-hitbox');
function openControlCenter() {
  if (isPasscodeMode && !document.body.classList.contains('unlocked')) return; // Chi chan o man hinh nhap mat ma
  closeNotificationPeek();
  controlCenter.style.transition = '';
  controlCenter.style.transform = '';
  controlCenter.style.filter = '';
  controlCenter.style.opacity = '';
  controlCenter.style.pointerEvents = '';
  controlCenter.classList.add('cc-animating');
  controlCenter.classList.add('open');
  statusBar.style.transition = 'opacity 0.22s ease';
  statusBar.style.opacity = '0';
  statusBar.style.pointerEvents = 'none';
}
function closeControlCenter() {
  controlCenter.style.transition = '';
  controlCenter.style.transform = '';
  controlCenter.style.filter = '';
  controlCenter.style.opacity = '';
  controlCenter.style.pointerEvents = '';
  controlCenter.classList.add('cc-animating');
  controlCenter.classList.remove('open');
  statusBar.style.transition = 'opacity 0.28s ease';
  statusBar.style.opacity = '';
  statusBar.style.pointerEvents = '';
}
let isNotifPeekOpen = false;
let isPeekDragActive = false;
let peekDragFullDist = 240;
// Ham dung chung: tinh progress kieu "rubber-band" - keo qua khoang fullDist thi
// tang cham dan (khai can) thay vi dung cung, tao cam giac dan hoi khi keo qua da.
function rubberProgress(dy, fullDist) {
  if (dy <= fullDist) return dy / fullDist;
  const overshoot = dy - fullDist;
  return 1 + Math.sqrt(overshoot / fullDist) * 0.18;
}
function setNotifSwipeHintVisible(visible) {
  const hint = document.querySelector('.ls-swipe-text');
  if (hint) hint.style.display = visible ? '' : 'none';
  const bar = document.querySelector('.ls-swipe-bar');
  if (bar) bar.style.display = visible ? '' : 'none';
}
function prepareNotificationPeekForDrag() {
  closeControlCenter();
  setNotifSwipeHintVisible(false);
  lockWrapper.style.transition = 'none';
  lockUI.style.transition = 'none';
  passcodeUI.style.transition = 'none';
  lockUI.style.opacity = '1'; lockUI.style.pointerEvents = 'auto';
  lockUI.style.transform = 'translateY(0)'; lockUI.style.filter = 'blur(0px)';
  passcodeUI.style.opacity = '0'; passcodeUI.style.pointerEvents = 'none';
  passcodeUI.style.transform = 'scale(0.85)'; passcodeUI.style.filter = 'blur(15px)';
  isPasscodeMode = false; passcode = []; updateDots(); pcTitle.innerText = "Nhập mật mã";
  lockWrapper.style.display = 'block';
  lockWrapper.style.background = 'rgba(0,0,0,0)';
  lockWrapper.style.backdropFilter = 'blur(0px)';
  lockWrapper.style.transform = 'translateY(-100%) scale(0.985)';
  void lockWrapper.offsetWidth;
}
function updateNotificationPeekDrag(dy, fullDist) {
  const progress = rubberProgress(Math.max(0, dy), fullDist);
  const clampedP = Math.min(progress, 1);
  const scale = 0.985 + clampedP * 0.015 + Math.max(0, progress - 1) * 0.01;
  lockWrapper.style.transform = `translateY(${(progress - 1) * 100}%) scale(${scale.toFixed(4)})`;
  lockWrapper.style.backdropFilter = `blur(${(clampedP * 14).toFixed(1)}px)`;
  lockWrapper.style.background = `rgba(0,0,0,${(clampedP * 0.28).toFixed(2)})`;
}
function finishNotificationPeekDrag() {
  const match = /translateY\((-?[\d.]+)%\)/.exec(lockWrapper.style.transform);
  const currentPercent = match ? parseFloat(match[1]) : -100;
  const progress = (currentPercent + 100) / 100;
  lockWrapper.style.transition = 'transform 0.4s var(--ios-smooth), backdrop-filter 0.35s ease, background 0.35s ease';
  if (progress > 0.35) {
      lockWrapper.style.transform = 'translateY(0) scale(1)';
      lockWrapper.style.backdropFilter = 'blur(14px)';
      lockWrapper.style.background = 'rgba(0,0,0,0.28)';
      isNotifPeekOpen = true;
  } else {
      lockWrapper.style.transform = 'translateY(-100%) scale(0.985)';
      lockWrapper.style.backdropFilter = 'blur(0px)';
      lockWrapper.style.background = 'rgba(0,0,0,0)';
      isNotifPeekOpen = false;
      setNotifSwipeHintVisible(true);
      setTimeout(() => {
          if (!isNotifPeekOpen && document.body.classList.contains('unlocked')) { lockWrapper.style.display = 'none'; lockWrapper.style.transition = ''; }
      }, 400);
  }
}
function openNotificationPeek() {
  if (isNotifPeekOpen) return;
  prepareNotificationPeekForDrag();
  lockWrapper.style.transition = 'transform 0.4s var(--ios-smooth), backdrop-filter 0.35s ease, background 0.35s ease';
  requestAnimationFrame(() => {
      lockWrapper.style.transform = 'translateY(0) scale(1)';
      lockWrapper.style.backdropFilter = 'blur(14px)';
      lockWrapper.style.background = 'rgba(0,0,0,0.28)';
  });
  isNotifPeekOpen = true;
}
function closeNotificationPeek() {
  if (!isNotifPeekOpen) return;
  isNotifPeekOpen = false;
  setNotifSwipeHintVisible(true);
  lockUI.style.transition = 'opacity 0.3s ease, transform 0.35s var(--ios-smooth)';
  lockUI.style.transform = 'translateY(0)'; lockUI.style.opacity = '1';
  lockWrapper.style.transition = 'transform 0.4s var(--ios-smooth), backdrop-filter 0.35s ease, background 0.35s ease';
  lockWrapper.style.transform = 'translateY(-100%) scale(0.985)';
  lockWrapper.style.backdropFilter = 'blur(0px)';
  lockWrapper.style.background = 'rgba(0,0,0,0)';
  setTimeout(() => {
      if (!isNotifPeekOpen && document.body.classList.contains('unlocked')) lockWrapper.style.display = 'none';
      lockWrapper.style.transition = '';
      lockUI.style.transition = '';
  }, 400);
}
let ccStartY = 0; let ccStartX = 0; let ccSwipingDown = false; let ccSwipeIsLeftHalf = false;
let ccDragActive = false; let ccDragFullDist = 260; let ccDragProgress = 0;
function prepareControlCenterForDrag() {
  if (isPasscodeMode && !document.body.classList.contains('unlocked')) return; // Chi chan o man hinh nhap mat ma
  controlCenter.classList.remove('cc-animating');
  controlCenter.classList.remove('open');
  controlCenter.style.transition = 'none';
  controlCenter.style.pointerEvents = 'none';
  controlCenter.style.opacity = '0';
  controlCenter.style.transform = 'translateY(-100%) scale(0.94)';
  controlCenter.style.filter = 'blur(6px)';
  void controlCenter.offsetWidth;
}
function updateControlCenterDrag(dy, fullDist) {
  if (isPasscodeMode && !document.body.classList.contains('unlocked')) return;
  ccDragProgress = rubberProgress(Math.max(0, dy), fullDist);
  const clampedP = Math.min(ccDragProgress, 1);
  const scale = 0.94 + clampedP * 0.06 + Math.max(0, ccDragProgress - 1) * 0.015;
  controlCenter.style.transform = `translateY(${(ccDragProgress - 1) * 100}%) scale(${scale.toFixed(4)})`;
  controlCenter.style.filter = `blur(${(6 * (1 - clampedP)).toFixed(1)}px)`;
  controlCenter.style.opacity = Math.min(clampedP * 1.3, 1).toFixed(2);
}
function finishControlCenterDrag() {
  const willOpen = ccDragProgress > 0.4;
  controlCenter.style.transition = 'transform 0.4s var(--ios-smooth), filter 0.3s ease, opacity 0.3s ease';
  if (willOpen) {
      controlCenter.style.transform = 'translateY(0) scale(1)';
      controlCenter.style.filter = 'blur(0px)';
      controlCenter.style.opacity = '1';
      controlCenter.style.pointerEvents = 'auto';
      controlCenter.classList.add('open');
      statusBar.style.transition = 'opacity 0.22s ease';
      statusBar.style.opacity = '0';
      statusBar.style.pointerEvents = 'none';
  } else {
      controlCenter.style.transform = 'translateY(-100%) scale(0.94)';
      controlCenter.style.filter = 'blur(6px)';
      controlCenter.style.opacity = '0';
      controlCenter.style.pointerEvents = 'none';
      controlCenter.classList.remove('open');
      statusBar.style.transition = 'opacity 0.28s ease';
      statusBar.style.opacity = '';
      statusBar.style.pointerEvents = '';
  }
  setTimeout(() => {
      controlCenter.style.transition = '';
      controlCenter.style.transform = '';
      controlCenter.style.filter = '';
      controlCenter.style.opacity = '';
      controlCenter.style.pointerEvents = '';
      controlCenter.classList.add('cc-animating');
  }, 420);
}
ccHitbox.addEventListener('touchstart', e => {
  // Khi dang o man hinh NHAP MAT MA, khong duoc phep vuot mo Control Center
  // hay thanh thong bao tu day nua - chan hoan toan tu buoc touchstart de
  // khong co bat ky trang thai keo (drag) nao duoc khoi tao.
  if (isPasscodeMode && !document.body.classList.contains('unlocked')) return;
  ccStartY = e.touches[0].clientY;
  ccStartX = e.touches[0].clientX;
  ccSwipingDown = false;
  isPeekDragActive = false;
  ccDragActive = false;
  const containerRect = phoneContainer.getBoundingClientRect();
  ccSwipeIsLeftHalf = (ccStartX - containerRect.left) < (containerRect.width / 2);
  // prepareNotificationPeekForDrag() ep lockWrapper nhay ngay ve translateY(-100%)
  // roi cho keo xuong de "lo" no ra lai - chi dung khi dang o man hinh CHINH
  // (luc do lockWrapper von dang an san). Neu dang o MAN HINH KHOA thi
  // lockWrapper da hien thi san (translateY(0)) roi, ep no nhay se lam man
  // hinh khoa bien mat ngay khi vua cham -> day chinh la nguyen nhan khien
  // khong the keo thanh thong bao xuong khi dang khoa may. Nen chi chuan bi
  // hieu ung peek khi may da mo khoa.
  const isUnlocked = document.body.classList.contains('unlocked');
  if (ccSwipeIsLeftHalf && !isNotifPeekOpen && isUnlocked) {
      prepareNotificationPeekForDrag();
      peekDragFullDist = containerRect.height * 0.32;
  } else if (!ccSwipeIsLeftHalf && !controlCenter.classList.contains('open')) {
      prepareControlCenterForDrag();
      ccDragFullDist = containerRect.height * 0.42;
  }
}, {passive: true});
ccHitbox.addEventListener('touchmove', e => {
  if (isPasscodeMode && !document.body.classList.contains('unlocked')) return;
  const dy = e.touches[0].clientY - ccStartY;
  const dx = e.touches[0].clientX - ccStartX;
  if (dy > 15 && Math.abs(dy) > Math.abs(dx)) ccSwipingDown = true;
  const isUnlocked = document.body.classList.contains('unlocked');
  if (ccSwipeIsLeftHalf && !isNotifPeekOpen && isUnlocked && dy > 0) {
      isPeekDragActive = true;
      updateNotificationPeekDrag(dy, peekDragFullDist);
  } else if (!ccSwipeIsLeftHalf && !controlCenter.classList.contains('open') && dy > 0) {
      ccDragActive = true;
      updateControlCenterDrag(dy, ccDragFullDist);
  }
}, {passive: true});
ccHitbox.addEventListener('touchend', () => {
  if (isPasscodeMode && !document.body.classList.contains('unlocked')) { ccSwipingDown = false; isPeekDragActive = false; ccDragActive = false; return; }
  const isUnlocked = document.body.classList.contains('unlocked');
  if (ccSwipeIsLeftHalf && isPeekDragActive) {
    finishNotificationPeekDrag();
  } else if (!ccSwipeIsLeftHalf && ccDragActive) {
    finishControlCenterDrag();
  } else if (ccSwipingDown) {
    if (ccSwipeIsLeftHalf) { if (isUnlocked) openNotificationPeek(); }
    else openControlCenter();
  }
  ccSwipingDown = false;
  isPeekDragActive = false;
  ccDragActive = false;
}, {passive: true});
controlCenter.addEventListener('touchstart', (e) => {
  if (e.target.closest && e.target.closest('.cc-power-btn')) return;
  closeControlCenter();
}, {passive: true});
"""


APP_CSS_1 = r"""
:root {
--ios-spring-snappy: cubic-bezier(0.34, 1.56, 0.64, 1);
--ios-spring-smooth: cubic-bezier(0.25, 1, 0.5, 1);
--ios-gentle-spring: cubic-bezier(0.35, 1.25, 0.45, 1);
--ios-smooth: cubic-bezier(0.32, 0.72, 0, 1);
--drag-y: 0px;
--drag-scale-y: 1;
--drag-scale-x: 1;
}
* {
box-sizing: border-box; margin: 0; padding: 0;
user-select: none; -webkit-tap-highlight-color: transparent;
-webkit-touch-callout: none;
}
body, html {
width: 100%; height: 100%; background-color: #000;
font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
overflow: hidden; touch-action: pan-x pan-y;
}
#boot-screen {
position: absolute; top: 15px; bottom: 45px; left: 15px; right: 15px;
background: radial-gradient(circle at 50% 40%, #171b2c 0%, #0a0c16 55%, #020207 100%);
display: flex; flex-direction: column; justify-content: center; align-items: center;
z-index: 99999; color: #fff; overflow: hidden;
border-radius: 45px;
-webkit-mask-image: -webkit-radial-gradient(circle, #fff 100%, #fff 100%);
mask-image: radial-gradient(circle, #fff 100%, #fff 100%);
box-shadow: 0 0 0 2px #151515;
transition: opacity 0.7s ease, filter 0.7s ease;
}
#boot-screen.boot-hide { opacity: 0; filter: blur(4px); pointer-events: none; transition: opacity 0.28s ease, filter 0.28s ease; }
#boot-screen.boot-warp .boot-glow,
#boot-screen.boot-warp .boot-glow-ring,
#boot-screen.boot-warp .boot-wordmark,
#boot-screen.boot-warp .boot-tagline,
#boot-screen.boot-warp .boot-bar-track,
#boot-screen.boot-warp #boot-particles {
transition: opacity 0.18s ease; opacity: 0;
}
#boot-screen.boot-warp .boot-mark {
animation: bootWarpZoom 0.5s cubic-bezier(0.55,0,0.85,0.35) forwards;
will-change: transform, opacity;
}
@keyframes bootWarpZoom {
0% { transform: scale(1) rotate(0deg); opacity: 1; }
55% { transform: scale(2.6) rotate(6deg); opacity: 1; }
100% { transform: scale(9) rotate(12deg); opacity: 0; }
}
#boot-flash {
position: absolute; inset: 0; border-radius: inherit;
background: radial-gradient(circle, #f3f7ff 0%, #9db8ff 45%, rgba(120,150,255,0) 75%);
opacity: 0; pointer-events: none;
}
#boot-screen.boot-warp #boot-flash {
animation: bootFlashPulse 0.62s ease-out forwards;
}
@keyframes bootFlashPulse {
0% { opacity: 0; } 48% { opacity: 0; } 66% { opacity: 1; } 100% { opacity: 0; }
}
#phone-container.boot-arrive {
animation: screenArrive 0.42s cubic-bezier(0.22,0.9,0.3,1) both;
will-change: transform;
}
@keyframes screenArrive {
0% { transform: scale(1.06); }
100% { transform: scale(1); }
}
.boot-glow {
position: absolute; width: 520px; height: 520px; border-radius: 50%;
background: radial-gradient(circle, rgba(120,150,255,0.24) 0%, rgba(90,110,255,0.06) 45%, rgba(120,150,255,0) 72%);
opacity: 0; animation: bootGlowIn 1.2s ease-out 0.1s forwards, bootGlowPulse 2.4s ease-in-out 1.3s infinite;
}
.boot-glow-ring {
position: absolute; width: 250px; height: 250px; border-radius: 50%;
border: 1px solid rgba(150,175,255,0.16);
opacity: 0; animation: bootGlowIn 0.9s ease-out 0.25s forwards, bootRingSpin 16s linear infinite;
}
.boot-glow-ring::before {
content: ''; position: absolute; top: -2.5px; left: 50%; width: 5px; height: 5px; margin-left: -2.5px;
border-radius: 50%; background: #aebdff; box-shadow: 0 0 10px 2px rgba(140,170,255,0.9);
}
@keyframes bootGlowIn { from { opacity: 0; transform: scale(0.6); } to { opacity: 1; transform: scale(1); } }
@keyframes bootGlowPulse { 0%,100% { opacity: 0.85; } 50% { opacity: 1; } }
@keyframes bootRingSpin { to { transform: rotate(360deg); } }
.boot-mark {
position: relative; width: 104px; height: 104px; margin-bottom: 28px;
opacity: 0; transform: scale(0.4) rotate(-25deg);
animation: bootMarkIn 0.7s cubic-bezier(0.2,0.9,0.25,1.2) 0.2s forwards, bootMarkBreathe 2.6s ease-in-out 1.6s infinite;
}
.boot-mark svg { width: 100%; height: 100%; overflow: visible; }
.boot-mark .bm-ring-soft { fill: none; stroke: rgba(150,175,255,0.14); stroke-width: 4.5; }
.boot-mark .bm-ring { fill: none; stroke: url(#bootRingGrad); stroke-width: 4.5; stroke-linecap: round;
stroke-dasharray: 251; stroke-dashoffset: 251; animation: bootRingDraw 0.9s cubic-bezier(0.4,0,0.2,1) 0.5s forwards; }
.boot-mark .bm-glyph { opacity: 0; animation: bootFadeIn 0.5s ease 1.1s forwards; }
.boot-mark .bm-glyph text { fill: url(#bootGlyphGrad); }
.boot-mark .bm-spark { opacity: 0; transform-origin: 50px 50px;
animation: bootFadeIn 0.35s ease 1.3s forwards, bootSparkOrbit 3.4s linear 1.65s infinite; }
@keyframes bootMarkIn { to { opacity: 1; transform: scale(1) rotate(0deg); } }
@keyframes bootMarkBreathe { 0%,100% { transform: scale(1); } 50% { transform: scale(1.035); } }
@keyframes bootRingDraw { to { stroke-dashoffset: 0; } }
@keyframes bootFadeIn { to { opacity: 1; } }
@keyframes bootSparkOrbit { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
.boot-wordmark {
font-size: 25px; font-weight: 800; letter-spacing: 5px; text-align: center;
text-shadow: 0 0 18px rgba(140,170,255,0.55);
}
.boot-wordmark span {
display: inline-block; opacity: 0; transform: translateY(10px);
animation: bootLetterIn 0.45s ease forwards;
background: linear-gradient(180deg, #ffffff 0%, #c3cfff 100%);
-webkit-background-clip: text; background-clip: text; color: transparent;
}
@keyframes bootLetterIn { to { opacity: 1; transform: translateY(0); } }
.boot-tagline {
margin-top: 10px; font-size: 11px; font-weight: 500; letter-spacing: 3px;
color: rgba(255,255,255,0.45); text-transform: uppercase;
opacity: 0; animation: bootTextIn 0.6s ease 1.85s forwards;
}
@keyframes bootTextIn { to { opacity: 1; transform: translateY(0); } }
.boot-bar-track {
position: relative; width: 150px; height: 3px; margin-top: 34px; border-radius: 3px;
background: rgba(255,255,255,0.12); overflow: hidden;
opacity: 0; animation: bootTextIn 0.4s ease 1.95s forwards;
box-shadow: 0 0 0 1px rgba(255,255,255,0.04);
}
.boot-bar-fill {
position: absolute; left: 0; top: 0; height: 100%; width: 0%; border-radius: 3px;
background: linear-gradient(90deg, #6a8dff, #b3c4ff, #6a8dff);
background-size: 220% 100%; animation: bootBarFill 0.6s ease 2.05s forwards, bootBarShine 1.1s linear infinite;
}
@keyframes bootBarFill { to { width: 100%; } }
@keyframes bootBarShine { 0% { background-position: 0% 0; } 100% { background-position: -220% 0; } }
.boot-particle {
position: absolute; bottom: -10px; width: 3px; height: 3px; border-radius: 50%;
background: rgba(150,180,255,0.6); animation-name: bootParticleUp; animation-timing-function: ease-in; animation-iteration-count: infinite;
}
@keyframes bootParticleUp { 0% { transform: translateY(0); opacity: 0; } 12% { opacity: 0.8; } 100% { transform: translateY(-520px); opacity: 0; } }
#phone-container {
display: block; position: absolute;
top: 15px; bottom: 45px; left: 15px; right: 15px;
background-color: #1a1a1a;
background-size: cover;
background-position: center;
border-radius: 45px; overflow: hidden;
-webkit-mask-image: -webkit-radial-gradient(circle, #fff 100%, #fff 100%);
mask-image: radial-gradient(circle, #fff 100%, #fff 100%);
box-shadow: 0 0 0 2px #151515;
transition: top 0.5s var(--ios-smooth), left 0.5s var(--ios-smooth),
width 0.5s var(--ios-smooth), height 0.5s var(--ios-smooth),
border-radius 0.45s var(--ios-smooth), box-shadow 0.45s var(--ios-smooth);
}
body.ipad-mode #home-indicator { width: 210px; }
#status-bar { position: absolute; top: 0; left: 0; width: 100%; height: 50px; display: flex; justify-content: space-between; align-items: center; padding: 0 25px; z-index: 9990; pointer-events: none; transition: opacity 0.3s ease; }
.sb-left { font-size: 15px; font-weight: 600; color: white; letter-spacing: 0.5px; margin-top: 2px; transition: transform 0.4s var(--ios-spring-snappy); }
.sb-right { display: flex; align-items: center; gap: 4px; transition: transform 0.4s var(--ios-spring-snappy); }
.sb-icon { fill: white; color: white; filter: drop-shadow(0 1px 2px rgba(0,0,0,0.3)); }
.sb-icon rect, .sb-icon path { transition: fill 0.3s ease; }
.sb-battery { width: 34px; height: 16px; background-color: #fff; border-radius: 6px; position: relative; box-sizing: border-box; display: flex; justify-content: center; align-items: center; box-shadow: 0 1px 2px rgba(0,0,0,0.3); margin-left: 2px; transition: background-color 0.3s ease, box-shadow 0.3s ease; }
.sb-battery::after { content: ''; position: absolute; right: -3px; top: 50%; transform: translateY(-50%); width: 3px; height: 7px; background-color: #fff; border-top-right-radius: 2px; border-bottom-right-radius: 2px; opacity: 0.9; transition: background-color 0.3s ease; }
.sb-battery-level { color: #000; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; font-weight: 700; font-size: 11.5px; letter-spacing: -0.3px; line-height: 1; z-index: 1; transition: color 0.3s ease; }
.cc-indicator { position: absolute; top: 38px; right: 33px; width: 52px; height: 3px; background: rgba(255,255,255,0.6); border-radius: 3px; z-index: 2147482999; pointer-events: none; box-shadow: 0 1px 2px rgba(0,0,0,0.2); }
/* z-index cao hon lock-screen-wrapper (9700, dung cho man nhap mat ma + thanh thong bao) va
   app-switcher (9000) de thanh ngang duoi wifi/pin/song KHONG bi cac lop nen mo/toi che mat;
   van thap hon status-bar/Control Center (2147483000) nen Control Center mo ra van de len tren. */
.sb-left, .sb-icon { transition: color 0.3s ease, border-color 0.3s ease, filter 0.3s ease; }
#status-bar.status-bar-dark-content .sb-left { color: #000; text-shadow: none; }
#status-bar.status-bar-dark-content .sb-icon rect,
#status-bar.status-bar-dark-content .sb-icon path { fill: #000; }
#status-bar.status-bar-dark-content .sb-icon { color: #000; filter: drop-shadow(0 1px 1px rgba(255,255,255,0.25)); }
#status-bar.status-bar-dark-content .sb-battery { background-color: #000; box-shadow: none; }
#status-bar.status-bar-dark-content .sb-battery::after { background-color: #000; }
#status-bar.status-bar-dark-content .sb-battery-level { color: #fff; }
#home-indicator-hitbox { position: absolute; bottom: 0; left: 0; width: 100%; height: 40px; z-index: 9999; display: none; cursor: pointer; }
#home-indicator { position: absolute; bottom: 8px; left: 50%; transform: translateX(-50%); width: 135px; height: 5px; background: white; border-radius: 100px; box-shadow: 0 1px 3px rgba(0,0,0,0.3); pointer-events: none; transition: background 0.3s, transform 0.2s; }
#home-indicator-hitbox:active #home-indicator { background: rgba(255,255,255,0.8); }
#home-indicator.status-bar-dark-content { background: rgba(0,0,0,0.85); box-shadow: none; }
#home-indicator-hitbox:active #home-indicator.status-bar-dark-content { background: rgba(0,0,0,0.6); }
#control-center-hitbox { position: absolute; top: 0; left: 0; width: 100%; height: 55px; z-index: 9995; }
#control-center {
position: absolute; top: 0; left: 0; width: 100%; height: 100%;
border-radius: 45px; overflow: hidden; z-index: 9996;
background: rgba(255,255,255,0.04);
backdrop-filter: blur(32px) saturate(1.5);
-webkit-backdrop-filter: blur(32px) saturate(1.5);
opacity: 0; pointer-events: none; transform: translateY(-100%) scale(0.94); filter: blur(6px);
}
#control-center.cc-animating { transition: transform 0.34s var(--ios-smooth), opacity 0.28s ease, filter 0.3s ease; }
#control-center.open { opacity: 1; pointer-events: auto; transform: translateY(0) scale(1); filter: blur(0px); }
.cc-top-row { position: absolute; top: 16px; left: 0; right: 0; display: flex; justify-content: space-between; align-items: center; padding: 0 24px; color: #fff; }
.cc-plus-btn { font-size: 24px; font-weight: 300; line-height: 1; }
.cc-power-btn { font-size: 17px; }
.cc-status-row { position: absolute; top: 58px; left: 0; right: 0; display: flex; justify-content: space-between; align-items: center; padding: 0 24px; }
.cc-status-left { display: flex; align-items: center; gap: 7px; color: #fff; }
.cc-signal-icon { width: 17px; }
.cc-network-label { font-size: 14px; font-weight: 600; letter-spacing: 0.3px; }
.cc-wifi-icon { font-size: 13px; }
.cc-status-right { display: flex; align-items: center; gap: 8px; }
.cc-battery { width: 34px; height: 16px; background-color: #fff; border-radius: 6px; position: relative; box-sizing: border-box; display: flex; justify-content: center; align-items: center; box-shadow: 0 1px 2px rgba(0,0,0,0.3); }
.cc-battery::after { content: ''; position: absolute; right: -3px; top: 50%; transform: translateY(-50%); width: 3px; height: 7px; background-color: #fff; border-top-right-radius: 2px; border-bottom-right-radius: 2px; opacity: 0.9; }
.cc-battery-level { color: #000; font-weight: 700; font-size: 10px; letter-spacing: -0.3px; line-height: 1; transition: color 0.3s ease; }
#control-center.status-bar-dark-content .cc-battery-level { color: #fff; }
.cc-status-left, .cc-signal-icon rect, .cc-battery, .cc-battery::after { transition: color 0.3s ease, fill 0.3s ease, background-color 0.3s ease; }
#control-center.status-bar-dark-content .cc-status-left { color: #000; }
#control-center.status-bar-dark-content .cc-signal-icon rect { fill: #000; }
#control-center.status-bar-dark-content .cc-battery { background-color: #000; box-shadow: none; }
#control-center.status-bar-dark-content .cc-battery::after { background-color: #000; }
#dynamic-island {
position: absolute; top: 10px; left: 50%;
transform: translateX(-50%) translateY(var(--drag-y)) scaleX(var(--drag-scale-x)) scaleY(var(--drag-scale-y));
transform-origin: top center; background: linear-gradient(180deg, #1c1c1e 0%, #000 60%); border-radius: 20px;
box-shadow: 0 8px 25px rgba(0,0,0,0.45), inset 0 0 0 1px rgba(255,255,255,0.09), inset 0 1px 1px rgba(255,255,255,0.14);
outline: 1px solid rgba(255,255,255,0.18); outline-offset: -1px;
color: #fff; overflow: hidden; display: flex; justify-content: center; align-items: center;
z-index: 10000; cursor: pointer; will-change: width, height, border-radius, transform;
}
#dynamic-island:active { cursor: grabbing; }
.island-animating { transition: width 0.5s var(--ios-spring-snappy), height 0.5s var(--ios-spring-snappy), border-radius 0.5s var(--ios-spring-snappy), transform 0.5s var(--ios-spring-snappy), box-shadow 0.4s ease; }
.state-default { width: 110px; height: 32px; border-radius: 18px; }
.sensor-cam { width: 100%; height: 100%; display: flex; justify-content: center; align-items: center; padding: 0 10px; opacity: 1; transition: opacity 0.3s ease; }
.state-default .sensor-cam { opacity: 1; }
.state-faceid { width: 145px; height: 145px; border-radius: 35px; }
.state-warning { width: 300px; max-width: 90%; height: 75px; border-radius: 37px; box-shadow: 0 10px 30px rgba(255,59,48,0.2), inset 0 0 0 1px rgba(255,255,255,0.05); }
.state-call-ring { width: 272px; max-width: 92%; height: 56px; border-radius: 30px; box-shadow: 0 12px 30px rgba(52,199,89,0.32), inset 0 0 0 1px rgba(255,255,255,0.07); }
.state-call-active { width: 172px; height: 40px; border-radius: 22px; box-shadow: 0 8px 20px rgba(52,199,89,0.24), inset 0 0 0 1px rgba(255,255,255,0.06); }
.state-penalty { width: 148px; height: 32px; border-radius: 18px; box-shadow: 0 8px 20px rgba(52,199,89,0.22), inset 0 0 0 1px rgba(255,255,255,0.06); }
#content-call { flex-direction: row; justify-content: space-between; align-items: center; padding: 0 8px 0 16px; gap: 6px; }
.call-info-zone { display: flex; align-items: center; gap: 10px; min-width: 0; flex: 1 1 auto; cursor: pointer; }
.call-icon-wrap { position: relative; width: 32px; height: 32px; border-radius: 50%; background: rgba(52,199,89,0.18); display: flex; justify-content: center; align-items: center; color: #34c759; font-size: 14px; flex: 0 0 auto; transition: background 0.3s ease; }
.call-icon-wrap i { display: inline-block; animation: callRingShake 1s ease-in-out infinite; }
@keyframes callRingShake { 0%,100% { transform: rotate(0deg); } 15% { transform: rotate(-22deg); } 30% { transform: rotate(16deg); } 45% { transform: rotate(-12deg); } 60% { transform: rotate(8deg); } 75% { transform: rotate(-4deg); } }
.call-icon-wrap::after { content:''; position: absolute; inset: -6px; border-radius: 50%; border: 1.5px solid rgba(52,199,89,0.55); opacity: 0; animation: callPulseRing 1.6s ease-out infinite; }
@keyframes callPulseRing { 0% { transform: scale(0.75); opacity: 0.75; } 100% { transform: scale(1.7); opacity: 0; } }
.call-text-wrap { display: flex; flex-direction: column; justify-content: center; overflow: hidden; min-width: 0; }
.call-title { font-size: 10.5px; font-weight: 800; color: #34c759; letter-spacing: 0.5px; margin-bottom: 1px; transition: opacity 0.25s ease; }
.call-name { font-size: 13px; font-weight: 600; color: #fff; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; font-variant-numeric: tabular-nums; }

/* ===== 2 nut Nghe / Tu choi ngay tren Dynamic Island (kieu Live Activity cua iPhone) ===== */
.call-island-actions { display: flex; align-items: center; gap: 7px; flex: 0 0 auto; }
.cia-btn {
  position: relative; width: 36px; height: 36px; border-radius: 50%; border: none;
  display: flex; align-items: center; justify-content: center; color: #fff; font-size: 14px;
  cursor: pointer; -webkit-tap-highlight-color: transparent;
  transition: transform 0.16s cubic-bezier(.34,1.56,.64,1), filter 0.2s ease, box-shadow 0.2s ease;
}
.cia-btn:active { transform: scale(0.84); filter: brightness(0.92); }
.cia-btn i { position: relative; z-index: 2; pointer-events: none; }
.cia-halo { position: absolute; inset: -5px; border-radius: 50%; border: 1.5px solid rgba(52,199,89,0.55); opacity: 0; pointer-events: none; animation: callPulseRing 1.7s ease-out infinite; }
.cia-decline { background: linear-gradient(180deg, #ff5f54, #ff3b30 55%, #d70015); box-shadow: 0 5px 12px -3px rgba(255,59,48,0.65); }
.cia-decline i { display: inline-block; transform: rotate(135deg); }
.cia-decline .cia-halo { border-color: rgba(255,59,48,0.55); animation-delay: 0.3s; }
.cia-accept { background: linear-gradient(180deg, #3ee273, #2fb85a 55%, #1f8a43); box-shadow: 0 5px 12px -3px rgba(52,199,89,0.65); }
.cia-accept i { display: inline-block; animation: ciaAcceptShake 1.6s ease-in-out infinite; }
@keyframes ciaAcceptShake { 0%,78%,100% { transform: rotate(0deg); } 83% { transform: rotate(-20deg); } 88% { transform: rotate(15deg); } 93% { transform: rotate(-8deg); } 97% { transform: rotate(4deg); } }

/* ===== trang thai da ket noi (dang trong cuoc goi): thu gon, an nut nghe/tu choi, hien dau xanh nhap nhay dep hon ===== */
.state-call-active #content-call { padding: 0 14px; gap: 8px; justify-content: flex-start; }
.state-call-active .call-title { display: none; }
.state-call-active .call-island-actions { display: none; }
.state-call-active .call-info-zone { gap: 8px; }
.state-call-active .call-icon-wrap { width: 20px; height: 20px; background: transparent; }
.state-call-active .call-icon-wrap i { display: none; }
.state-call-active .call-icon-wrap::before {
  content: ''; width: 9px; height: 9px; border-radius: 50%; background: #34c759;
  box-shadow: 0 0 9px rgba(52,199,89,0.95); animation: liveDotBreathe 1.3s ease-in-out infinite;
}
.state-call-active .call-icon-wrap::after { inset: -6px; animation: callPulseRing 1.5s ease-out infinite; }
@keyframes liveDotBreathe { 0%,100% { transform: scale(1); opacity: 1; } 50% { transform: scale(1.4); opacity: 0.6; } }
.state-call-active .call-name { font-size: 12.5px; }
.state-call-active .call-wave { display: flex; }
.state-penalty #content-penalty { display: flex; align-items: center; justify-content: center; gap: 8px; padding: 0 14px; }
.call-wave { display: none; align-items: center; gap: 2px; height: 12px; flex: 0 0 auto; margin-left: 2px; }
.call-wave span { display: block; width: 2.5px; border-radius: 2px; background: #34c759; animation: callWaveBar 0.9s ease-in-out infinite; }
.call-wave span:nth-child(1) { height: 40%; animation-delay: -0.6s; }
.call-wave span:nth-child(2) { height: 100%; animation-delay: -0.3s; }
.call-wave span:nth-child(3) { height: 65%; animation-delay: -0.9s; }
.call-wave span:nth-child(4) { height: 85%; animation-delay: -0.15s; }
@keyframes callWaveBar { 0%,100% { transform: scaleY(0.35); opacity: 0.65; } 50% { transform: scaleY(1); opacity: 1; } }
.dynamic-content { display: flex; width: 100%; height: 100%; position: absolute; top:0; left:0; pointer-events: none; visibility: hidden; opacity: 0; transition: visibility 0.4s, opacity 0.3s ease; }
.show-content { visibility: visible !important; opacity: 1 !important; pointer-events: auto; transition: visibility 0s, opacity 0.2s ease; }
.dynamic-content > * { opacity: 0; transform: translateY(12px) scale(0.85); filter: blur(8px); transition: opacity 0.3s ease, transform 0.4s cubic-bezier(0.4,0,1,1), filter 0.3s ease; }
.show-content > * { opacity: 1; transform: translateY(0) scale(1); filter: blur(0px); transition: opacity 0.6s ease, transform 0.8s var(--ios-spring-snappy), filter 0.5s ease; }
.show-content > *:nth-child(1) { transition-delay: 0.12s; }
.show-content > *:nth-child(2) { transition-delay: 0.18s; }
.show-content > *:nth-child(3) { transition-delay: 0.24s; }
#content-warning { flex-direction: row; justify-content: flex-start; align-items: center; padding: 0 20px; gap: 15px; }
.warning-icon { width: 45px; height: 45px; border-radius: 50%; background: rgba(255,59,48,0.15); display: flex; justify-content: center; align-items: center; color: #ff3b30; font-size: 20px; }
.warning-text-wrap { display: flex; flex-direction: column; justify-content: center; width: calc(100% - 60px); }
.warning-title { font-size: 11px; font-weight: 800; color: #ff3b30; letter-spacing: 0.5px; margin-bottom: 2px; }
.warning-sub { font-size: 13px; font-weight: 600; color: #fff; white-space: normal; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; text-overflow: ellipsis; line-height: 1.2; }
#content-faceid { flex-direction: column; justify-content: center; align-items: center; gap: 15px; }
.face-icon-wrap { position: relative; width: 60px; height: 60px; display: flex; justify-content: center; align-items: center; border-radius: 15px; overflow: hidden; }
.faceid-grid { position: absolute; top: 0; left: 0; width: 100%; height: 100%; background-image: linear-gradient(rgba(10,132,255,0.4) 1px, transparent 1px), linear-gradient(90deg, rgba(10,132,255,0.4) 1px, transparent 1px); background-size: 8px 8px; background-position: center; opacity: 0; transform: scale(1.5); transition: 0.5s ease; z-index: 1; border-radius: 12px; }
.show-content .faceid-grid { opacity: 1; transform: scale(1); animation: gridMove 2s linear infinite; }
@keyframes gridMove { 0% { background-position: 0 0; } 100% { background-position: 8px 8px; } }
.faceid-scanner { position: absolute; top: -100%; left: 0; width: 100%; height: 25px; background: linear-gradient(to bottom, transparent, #01ffe5, transparent); box-shadow: 0 0 15px #01ffe5; z-index: 3; opacity: 0; pointer-events: none; }
.show-content .faceid-scanner { opacity: 1; animation: scanSweep 1.5s ease-in-out infinite; }
@keyframes scanSweep { 0% { top: -30%; } 50% { top: 100%; } 100% { top: -30%; } }
.face-icon { font-size: 45px; color: #0a84ff; position: absolute; overflow: hidden; transition: 0.5s var(--ios-spring-snappy); opacity: 1; transform: scale(1); z-index: 2; text-shadow: 0 0 15px rgba(10,132,255,0.6); }
.face-icon::after { content:''; position: absolute; top:-10px; left:-10px; right:-10px; bottom:-10px; border: 2.5px solid #0a84ff; border-radius: 50%; border-top-color: transparent; animation: spin 1s linear infinite; }
.face-check { font-size: 45px; color: #34c759; position: absolute; opacity: 0; transform: scale(0.3); transition: 0.5s var(--ios-spring-snappy); z-index: 4; }
.faceid-success .face-icon { opacity: 0; transform: scale(1.6); }
.faceid-success .face-check { opacity: 1; transform: scale(1); text-shadow: 0 0 15px rgba(52,199,89,0.6); }
.faceid-success .faceid-grid, .faceid-success .faceid-scanner { opacity: 0; transition: 0.3s; }
/* ===== Icon khoa xoay + "bung" tu khoa kin sang khoa mo (khi mo khoa thanh cong) ===== */
.face-lock { font-size: 42px; color: #34c759; position: absolute; opacity: 0; transform: scale(0.4) rotate(-70deg); z-index: 5; text-shadow: 0 0 15px rgba(52,199,89,0.6); }
.faceid-unlocking .faceid-grid, .faceid-unlocking .faceid-scanner { opacity: 0; transition: 0.3s; }
.faceid-unlocking .face-icon { opacity: 0 !important; transform: scale(1.5); transition: 0.35s var(--ios-spring-snappy); }
.faceid-unlocking .face-lock { opacity: 1; animation: lockPopOpen 0.68s var(--ios-spring-snappy) forwards; }
@keyframes lockPopOpen {
  0%   { transform: scale(0.4) rotate(-70deg); opacity: 0; }
  40%  { transform: scale(1.3) rotate(14deg); opacity: 1; }
  68%  { transform: scale(0.9) rotate(-8deg); }
  100% { transform: scale(1) rotate(0deg); }
}
.screen-fade-overlay { position: absolute; top: 0; left: 0; width: 100%; height: 100%; background: #000; z-index: 99999; opacity: 0; pointer-events: none; transition: opacity 0.8s ease-in-out; border-radius: 45px; }
.screen-fade-overlay.active { opacity: 1; pointer-events: auto; }
"""

APP_CSS_2 = r"""
@keyframes pulseText { 0%, 100% { opacity: 0.5; } 50% { opacity: 1; } }
@keyframes shake { 10%, 90% { transform: translate3d(-1px,0,0); } 20%, 80% { transform: translate3d(2px,0,0); } 30%, 50%, 70% { transform: translate3d(-4px,0,0); } 40%, 60% { transform: translate3d(4px,0,0); } }
@keyframes spin { 100% { transform: rotate(360deg); } }
@keyframes appOpenAnim {
from { transform: scale(0.8); opacity: 0; }
to { transform: scale(1); opacity: 1; }
}
.sb-icons-group {
display: flex; align-items: center; gap: 4px;
transition: transform 0.35s var(--ios-gentle-spring), gap 0.35s ease, margin 0.35s ease;
transform-origin: left center;
}
"""

APP_BODY_1 = r"""
<div id="boot-screen">
  <div class="boot-glow"></div>
  <div class="boot-glow-ring"></div>
  <div id="boot-particles"></div>
  <div class="boot-mark">
    <svg viewBox="0 0 100 100">
      <defs>
        <linearGradient id="bootRingGrad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="#8fa8ff"/>
          <stop offset="100%" stop-color="#cfd9ff"/>
        </linearGradient>
        <linearGradient id="bootGlyphGrad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="#ffffff"/>
          <stop offset="100%" stop-color="#aebdff"/>
        </linearGradient>
      </defs>
      <circle class="bm-ring-soft" cx="50" cy="50" r="40"/>
      <circle class="bm-ring" cx="50" cy="50" r="40"/>
      <g class="bm-glyph">
        <text x="50" y="63" text-anchor="middle" font-size="44" font-weight="800" font-family="-apple-system,Segoe UI,Arial,sans-serif">Q</text>
        <line x1="33" y1="67" x2="67" y2="33" stroke="#0a0c16" stroke-width="5.5" stroke-linecap="round"/>
        <line x1="33" y1="67" x2="67" y2="33" stroke="url(#bootGlyphGrad)" stroke-width="2.6" stroke-linecap="round"/>
      </g>
      <circle class="bm-spark" cx="90" cy="50" r="3" fill="#eaf0ff"/>
    </svg>
  </div>
  <div class="boot-wordmark"><span style="animation-delay:1.35s">M</span><span style="animation-delay:1.39s">A</span><span style="animation-delay:1.43s">G</span><span style="animation-delay:1.47s">I</span><span style="animation-delay:1.51s">C</span><span style="animation-delay:1.55s">O</span><span style="animation-delay:1.59s">S</span></div>
  <div class="boot-tagline">Powered by MAGICOS</div>
  <div class="boot-bar-track"><div class="boot-bar-fill"></div></div>
  <div id="boot-flash"></div>
</div>
<div id="phone-container">
  <div id="screen-fade" class="screen-fade-overlay"></div>
  <div id="status-bar">
    <div class="sb-left"><span id="sb-time">09:41</span></div>
    <div class="sb-right" id="sb-right">
      <div class="sb-icons-group" id="sb-icons-group">
        <svg class="sb-icon" viewBox="0 0 18 12" fill="none" xmlns="http://www.w3.org/2000/svg" style="width: 18px;">
          <rect y="8" width="3" height="4" rx="1" fill="white"/>
          <rect x="5" y="5" width="3" height="7" rx="1" fill="white"/>
          <rect x="10" y="2" width="3" height="10" rx="1" fill="white"/>
          <rect x="15" width="3" height="12" rx="1" fill="white"/>
        </svg>
        <i class="fa-solid fa-wifi sb-icon" style="width: 17px; font-size: 13px; line-height: 1; text-align: center;"></i>
        <div class="sb-battery">
          <span class="sb-battery-level">100</span>
        </div>
      </div>
    </div>
  </div>
  <div class="cc-indicator"></div>
  <div id="control-center-hitbox"></div>
  <div id="control-center">
    <div class="cc-top-row">
      <div class="cc-plus-btn">+</div>
      <div class="cc-power-btn"><i class="fa-solid fa-power-off"></i></div>
    </div>
    <div class="cc-status-row">
      <div class="cc-status-left">
        <svg class="cc-signal-icon" viewBox="0 0 18 12" fill="none" xmlns="http://www.w3.org/2000/svg">
          <rect y="8" width="3" height="4" rx="1" fill="white"/>
          <rect x="5" y="5" width="3" height="7" rx="1" fill="white"/>
          <rect x="10" y="2" width="3" height="10" rx="1" fill="white"/>
          <rect x="15" width="3" height="12" rx="1" fill="white"/>
        </svg>
        <span class="cc-network-label">5G</span>
        <i class="fa-solid fa-wifi cc-wifi-icon"></i>
      </div>
      <div class="cc-status-right">
        <div class="cc-battery">
          <span class="cc-battery-level">100%</span>
        </div>
      </div>
    </div>
  </div>
"""

APP_BODY_2 = r"""
  <div id="dynamic-island" class="state-default island-animating">
    <div id="sensor-default" class="sensor-cam" style="position: relative;">
      <div id="island-lock-icon" style="position: absolute; left: 12px; opacity: 0; transform: scale(0.5); transition: all 0.4s var(--ios-spring-snappy); color: white; font-size: 11px;">
        <i class="fa-solid fa-lock"></i>
      </div>
      <div id="island-camera" style="width: 10px; height: 10px; border-radius: 50%; background: #000; box-shadow: inset 0 0 1px rgba(255,255,255,0.1); opacity:0.7; position: absolute; left: 20px; transition: transform 0.4s var(--ios-spring-snappy);"></div>
      <div style="width: 10px; height: 10px; border-radius: 50%; background: #08081a; box-shadow: inset 0 0 1px rgba(255,255,255,0.15); position: absolute; right: 8px;">
        <div style="width: 3px; height: 3px; border-radius: 50%; background: #2a3b5c; position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); opacity: 0.8;"></div>
      </div>
    </div>
    <div id="content-faceid" class="dynamic-content">
      <div class="face-icon-wrap">
        <div class="faceid-grid"></div>
        <div class="faceid-scanner"></div>
        <div class="face-icon"><i class="fa-solid fa-face-smile"></i></div>
        <div class="face-check"><i class="fa-solid fa-check"></i></div>
        <div class="face-lock"><i class="fa-solid fa-lock" id="face-lock-icon"></i></div>
      </div>
      <div id="face-text" style="font-size: 16px; font-weight: 600; color: #fff; transition: 0.3s;">Face ID</div>
    </div>
    <div id="content-warning" class="dynamic-content">
      <div class="warning-icon"><i class="fa-solid fa-triangle-exclamation"></i></div>
      <div class="warning-text-wrap">
        <span class="warning-title">HỆ THỐNG THÔNG BÁO</span>
        <span class="warning-sub">THIẾT BỊ KHÔNG HỖ TRỢ</span>
      </div>
    </div>
    <div id="content-call" class="dynamic-content">
      <div class="call-info-zone" id="callInfoZone">
        <div class="call-icon-wrap"><i class="fa-solid fa-phone"></i></div>
        <div class="call-text-wrap">
          <span class="call-title">CUỘC GỌI ĐẾN</span>
          <span class="call-name" id="call-name-text">Số lạ</span>
        </div>
        <div class="call-wave"><span></span><span></span><span></span><span></span></div>
      </div>
      <div class="call-island-actions">
        <button type="button" class="cia-btn cia-decline" id="islandDeclineBtn" aria-label="Từ chối"><span class="cia-halo"></span><i class="fa-solid fa-phone"></i></button>
        <button type="button" class="cia-btn cia-accept" id="islandAcceptBtn" aria-label="Trả lời"><span class="cia-halo"></span><i class="fa-solid fa-phone"></i></button>
      </div>
    </div>
    <div id="content-penalty" class="dynamic-content">
      <i class="fa-solid fa-futbol"></i>
      <span id="penalty-live-badge-time">00:00</span>
    </div>
  </div>
  <div id="home-indicator-hitbox">
    <div id="home-indicator"></div>
  </div>
"""

APP_JS_2 = r"""
function updateClock() {
  const now = new Date();
  let hours = now.getHours().toString().padStart(2, '0');
  let minutes = now.getMinutes().toString().padStart(2, '0');
  document.getElementById('ls-time').innerText = `${hours}:${minutes}`;
  let sbTime = document.getElementById('sb-time');
  if (sbTime) sbTime.innerText = `${hours}:${minutes}`;
  const days = ['Chủ Nhật', 'Thứ Hai', 'Thứ Ba', 'Thứ Tư', 'Thứ Năm', 'Thứ Sáu', 'Thứ Bảy'];
  const dayName = days[now.getDay()];
  document.getElementById('ls-date').innerText = `${dayName}, ${now.getDate()} tháng ${now.getMonth() + 1}`;
}
setInterval(updateClock, 1000);
updateClock();
"""

PENALTY_CSS = '\n.penalty-app-box { overflow: hidden; background: transparent; box-shadow: 0 4px 12px rgba(0,0,0,0.28), inset 0 1px 0 rgba(255,255,255,0.15); }\n.penalty-app-box svg { width: 100%; height: 100%; display: block; }\n.app-label { margin-top: 6px; font-size: 11px; font-weight: 600; color: #fff; text-shadow: 0 1px 3px rgba(0,0,0,0.45); text-align: center; max-width: 74px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }\n#app-penalty { background: #04140a; border-radius: inherit; overflow: hidden; isolation: isolate; max-width: 100%; max-height: 100%; box-sizing: border-box; }\n#app-penalty iframe { position: absolute !important; inset: 0 !important; top: 0 !important; left: 0 !important; right: 0 !important; bottom: 0 !important; width: 100% !important; height: 100% !important; max-width: 100% !important; max-height: 100% !important; margin: 0 !important; padding: 0 !important; border: none !important; display: block; background: #04140a; border-radius: inherit; box-sizing: border-box; transform: none !important; }\n.penalty-loading { position: absolute; inset: 0; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 16px; background: radial-gradient(circle at 50% 35%, #123a20 0%, #08140c 55%, #020402 100%); z-index: 5; transition: opacity 0.35s ease; }\n.penalty-loading .pl-ball { width: 46px; height: 46px; border-radius: 50%; background: radial-gradient(circle at 32% 28%, #fff 0 18%, transparent 19%), radial-gradient(circle at 68% 28%, #fff 0 18%, transparent 19%), radial-gradient(circle at 50% 62%, #fff 0 20%, transparent 21%), #e9e9e9; box-shadow: 0 0 20px rgba(143,242,156,0.4); animation: plSpin 0.9s linear infinite, plBounce 0.8s ease-in-out infinite; }\n@keyframes plSpin { to { transform: rotate(360deg); } }\n@keyframes plBounce { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-14px); } }\n.penalty-loading span { color: #8ef29c; font-size: 13px; font-weight: 600; letter-spacing: 0.5px; }\n.penalty-offline { position: absolute; inset: 0; display: none; flex-direction: column; align-items: center; justify-content: center; gap: 12px; padding: 40px; text-align: center; background: #0a0a0c; color: #eaeaea; z-index: 6; }\n.penalty-offline i { font-size: 38px; color: #ff9f0a; }\n.penalty-offline b { font-size: 15px; }\n.penalty-offline code { background: rgba(255,255,255,0.08); padding: 6px 10px; border-radius: 8px; font-size: 13px; color: #8ef29c; }\n.penalty-close-btn { position: absolute; top: 16px; right: 16px; width: 34px; height: 34px; border-radius: 50%; background: rgba(0,0,0,0.35); backdrop-filter: blur(14px); -webkit-backdrop-filter: blur(14px); display: flex; align-items: center; justify-content: center; color: #fff; font-size: 15px; z-index: 20; cursor: pointer; transition: transform 0.2s var(--ios-spring-snappy), background 0.2s; }\n.penalty-close-btn:active { transform: scale(0.85); background: rgba(255,255,255,0.25); }\n'

PENALTY_BODY_APP = '\n<div class="simple-app" id="app-penalty" data-penalty-available="__PENALTY_AVAILABLE__" data-penalty-url="__PENALTY_URL__">\n  <iframe id="penalty-iframe" title="Penalty" allow="autoplay" src=""></iframe>\n  <div class="penalty-loading" id="penalty-loading">\n    <div class="pl-ball"></div>\n    <span>Dang tai Penalty...</span>\n  </div>\n  <div class="penalty-offline" id="penalty-offline">\n    <i class="fa-solid fa-triangle-exclamation"></i>\n    <b>Không thể kết nối</b>\n  </div>\n  </div>\n'

PENALTY_JS = '\n(function () {\n  var appEl = document.getElementById(\'app-penalty\');\n  if (!appEl) return;\n  DOCK_APP_META[\'app-penalty\'] = { name:\'Penalty\', icon:\'fa-solid fa-futbol\', grad:\'linear-gradient(135deg,#27c96b,#0a6b3a)\' };\n  var iframe = document.getElementById(\'penalty-iframe\');\n  var loading = document.getElementById(\'penalty-loading\');\n  var offline = document.getElementById(\'penalty-offline\');\n  var available = appEl.getAttribute(\'data-penalty-available\') === \'true\';\n  var url = appEl.getAttribute(\'data-penalty-url\');\n  var needsFreshStart = true, generation = 0, startedAt = 0, pending = false;\n  var finishTimer, hideTimer, errorTimer;\n  loading.innerHTML = \'<div class="pl-session-mark"><div class="pl-session-ring"></div><svg viewBox="0 0 48 48"><path d="M12 25l8 8 16-18"/></svg></div><strong class="pl-title">PENALTY</strong><span class="pl-label">Đang tải…</span><small class="pl-remaining"></small><div class="pl-progress"><i></i></div>\';\n  function label(text) { loading.querySelector(\'.pl-label\').textContent = text; }\n  function showRemaining() {\n    loading.querySelector(\'.pl-remaining\').textContent = window.isPenaltySessionValid && window.isPenaltySessionValid()\n      ? \'Token còn \' + window.penaltyFmtRemain(window.penaltyRemainingMs()) : \'\';\n  }\n  function cancelTimers() { clearTimeout(finishTimer); clearTimeout(hideTimer); clearTimeout(errorTimer); }\n  window.penaltyStartFresh = function () {\n    if (!needsFreshStart) return;\n    if (!available || !url) { loading.style.display=\'none\'; offline.style.display=\'flex\'; return; }\n    needsFreshStart = false; pending = true; generation++; startedAt = Date.now();\n    cancelTimers(); offline.style.display=\'none\'; loading.style.display=\'flex\'; loading.style.opacity=\'1\';\n    loading.classList.remove(\'pl-ready\');\n    label(window.isPenaltySessionValid && window.isPenaltySessionValid() ? \'Đang khôi phục phiên chơi…\' : \'Đang tải Penalty…\');\n    showRemaining();\n    iframe.src = url + (url.includes(\'?\') ? \'&\' : \'?\') + \'_r=\' + Date.now() + "&balance=" + (window.getPenaltyBalance?window.getPenaltyBalance():100);\n    var attempt = generation;\n    errorTimer = setTimeout(function () {\n      if (attempt !== generation || !pending) return;\n      pending=false; needsFreshStart=true;\n      label(\'Chưa tải được game. Chạm để thử lại.\');\n    }, 15000);\n  };\n  loading.addEventListener(\'click\', function () { if (needsFreshStart) window.penaltyStartFresh(); });\n  iframe.addEventListener(\'load\', function () {\n    if (!pending || iframe.getAttribute(\'src\') === \'about:blank\') return;\n    var attempt = generation;\n    finishTimer = setTimeout(function () {\n      if (attempt !== generation || !pending) return;\n      if (!window.isPenaltySessionValid || !window.isPenaltySessionValid()) {\n        pending=false; cancelTimers(); return;\n      }\n      clearTimeout(errorTimer); pending=false;\n      loading.classList.add(\'pl-ready\'); label(\'Tải thành công\'); showRemaining();\n      hideTimer = setTimeout(function () {\n        if (attempt !== generation) return;\n        loading.style.opacity=\'0\';\n        hideTimer=setTimeout(function () { if (attempt === generation) loading.style.display=\'none\'; },400);\n      },650);\n    }, Math.max(0, 900-(Date.now()-startedAt)));\n  });\n  document.addEventListener(\'magicos-app-terminated\', function (ev) {\n    if (!ev.detail || ev.detail.appId !== \'app-penalty\') return;\n    generation++; pending=false; needsFreshStart=true; cancelTimers();\n    iframe.src=\'about:blank\'; loading.style.display=\'flex\'; loading.style.opacity=\'1\'; loading.classList.remove(\'pl-ready\');\n  });\n})();\n'

PHONE_APP_CSS = r"""
.phone-app-box { overflow: hidden; background: transparent; box-shadow: 0 4px 12px rgba(0,0,0,0.28), inset 0 1px 0 rgba(255,255,255,0.15); }
.phone-app-box svg { width: 100%; height: 100%; display: block; }
#app-phone { background: #000; border-radius: inherit; overflow: hidden; isolation: isolate; max-width: 100%; max-height: 100%; box-sizing: border-box; }
#app-phone iframe { position: absolute !important; inset: 0 !important; top: 0 !important; left: 0 !important; right: 0 !important; bottom: 0 !important; width: 100% !important; height: 100% !important; max-width: 100% !important; max-height: 100% !important; margin: 0 !important; padding: 0 !important; border: none !important; display: block; background: #000; border-radius: inherit; box-sizing: border-box; transform: none !important; }
.phone-app-loading { position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; background: #000; z-index: 5; transition: opacity 0.3s ease; }
.phone-app-loading .pal-ring { width: 40px; height: 40px; border-radius: 50%; border: 3px solid rgba(48,209,88,0.22); border-top-color: #30d158; animation: palSpin 0.8s linear infinite; }
@keyframes palSpin { to { transform: rotate(360deg); } }
"""

PHONE_APP_BODY = r"""
<div class="simple-app" id="app-phone">
  <iframe id="phone-iframe" title="Điện thoại" src="/phone-app.html"></iframe>
  <div class="phone-app-loading" id="phone-app-loading"><div class="pal-ring"></div></div>
</div>
"""

PHONE_APP_JS = r"""
(function () {
  var appEl = document.getElementById('app-phone');
  if (!appEl) return;
  DOCK_APP_META['app-phone'] = { name: 'Điện thoại', icon: 'fa-solid fa-phone', grad: 'linear-gradient(135deg,#6bdb8f,#1a8f42)' };
  var iframe = document.getElementById('phone-iframe');
  var loading = document.getElementById('phone-app-loading');
  if (iframe && loading) {
    iframe.addEventListener('load', function () {
      loading.style.opacity = '0';
      setTimeout(function () { loading.style.display = 'none'; }, 300);
    });
  }
})();
"""

ADMIN_CSS = r"""
.admin-app-box { overflow: hidden; background: transparent; box-shadow: 0 4px 14px rgba(0,0,0,0.35), inset 0 1px 0 rgba(255,255,255,0.12); }
.admin-app-box svg { width: 100%; height: 100%; display: block; }
#app-admin { background: #05070a; border-radius: inherit; overflow: hidden; isolation: isolate; max-width: 100%; max-height: 100%; box-sizing: border-box; font-family: -apple-system, 'Segoe UI', Roboto, Arial, sans-serif; color: #d8ffe4; }

/* ===== Man hinh khoi dong kieu hacker ===== */
.admin-boot { position: absolute; inset: 0; z-index: 30; background: #01050a; display: flex; flex-direction: column; align-items: center; justify-content: center; overflow: hidden; opacity: 1; transition: opacity 0.5s ease; }
.admin-boot.admin-boot-hide { opacity: 0; pointer-events: none; }
.admin-matrix { position: absolute; inset: 0; overflow: hidden; opacity: 0.55; }
.admin-matrix-col { position: absolute; top: -120%; width: 16px; color: #29ff7a; font-family: 'Courier New', monospace; font-size: 13px; line-height: 15px; text-shadow: 0 0 6px rgba(41,255,122,0.9), 0 0 2px #fff; white-space: pre; animation-name: adminMatrixFall; animation-timing-function: linear; animation-iteration-count: infinite; }
@keyframes adminMatrixFall { 0% { transform: translateY(-30%); } 100% { transform: translateY(230%); } }
.admin-boot-core { position: relative; z-index: 2; display: flex; flex-direction: column; align-items: center; gap: 14px; padding: 0 22px; text-align: center; }
.admin-boot-logo { width: 74px; height: 74px; filter: drop-shadow(0 0 16px rgba(41,255,122,0.55)); animation: adminLogoPulse 1.6s ease-in-out infinite; }
@keyframes adminLogoPulse { 0%, 100% { transform: scale(1); filter: drop-shadow(0 0 10px rgba(41,255,122,0.45)); } 50% { transform: scale(1.06); filter: drop-shadow(0 0 22px rgba(41,255,122,0.85)); } }
.admin-boot-lines { display: flex; flex-direction: column; gap: 5px; min-height: 92px; align-items: flex-start; }
.admin-boot-line { font-family: 'Courier New', monospace; font-size: 12.5px; color: #6dffa0; opacity: 0; white-space: nowrap; overflow: hidden; width: 0; border-right: 2px solid transparent; }
.admin-boot-line.admin-line-run { opacity: 1; animation: adminType 0.5s steps(30, end) forwards, adminCursorBlink 0.5s step-end infinite; }
@keyframes adminType { from { width: 0; } to { width: 100%; } }
@keyframes adminCursorBlink { 50% { border-right-color: #6dffa0; } }
.admin-boot-title { margin-top: 6px; font-size: 19px; font-weight: 800; letter-spacing: 3px; color: #35ffb0; text-transform: uppercase; opacity: 0; position: relative; }
.admin-boot-title.admin-title-show { animation: adminGlitchIn 0.7s ease forwards; }
@keyframes adminGlitchIn {
  0% { opacity: 0; transform: translateX(0); text-shadow: none; }
  10% { opacity: 1; transform: translate(-3px, 1px); text-shadow: 2px 0 #ff2d55, -2px 0 #00eaff; }
  20% { transform: translate(3px, -1px); }
  30% { transform: translate(-2px, 0); text-shadow: -2px 0 #ff2d55, 2px 0 #00eaff; }
  45% { transform: translate(2px, 1px); }
  60% { transform: translate(0,0); text-shadow: 1px 0 #ff2d55, -1px 0 #00eaff; }
  100% { opacity: 1; transform: translate(0,0); text-shadow: 0 0 14px rgba(53,255,176,0.8); }
}
.admin-scanlines { position: absolute; inset: 0; z-index: 3; pointer-events: none; background: repeating-linear-gradient(0deg, rgba(0,0,0,0.18) 0px, rgba(0,0,0,0.18) 1px, transparent 2px, transparent 3px); mix-blend-mode: overlay; }

/* ===== Dashboard chinh ===== */
.admin-dashboard { position: absolute; inset: 0; overflow-y: auto; -webkit-overflow-scrolling: touch; padding: 0 0 30px; background: radial-gradient(circle at 50% 0%, #0c1c14 0%, #060a08 55%, #030403 100%); }
.admin-header { position: sticky; top: 0; z-index: 5; display: flex; align-items: center; gap: 10px; padding: calc(env(safe-area-inset-top,0px) + 16px) 18px 14px; background: linear-gradient(180deg, rgba(3,6,4,0.96) 60%, rgba(3,6,4,0)); backdrop-filter: blur(6px); -webkit-backdrop-filter: blur(6px); }
.admin-header-logo { width: 34px; height: 34px; flex: none; filter: drop-shadow(0 0 6px rgba(41,255,122,0.6)); }
.admin-header-text { flex: 1; min-width: 0; }
.admin-header-title { font-size: 15px; font-weight: 800; letter-spacing: 1.5px; color: #6dffb0; text-transform: uppercase; }
.admin-header-sub { font-size: 11px; color: #6a8778; margin-top: 1px; }
.admin-close-btn { width: 32px; height: 32px; border-radius: 50%; background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.1); display: flex; align-items: center; justify-content: center; color: #cfeede; font-size: 14px; cursor: pointer; transition: transform 0.2s var(--ios-spring-snappy), background 0.2s; }
.admin-close-btn:active { transform: scale(0.85); background: rgba(255,255,255,0.16); }
.admin-status-live { flex: none; display: flex; align-items: center; gap: 7px; padding: 7px 12px; border-radius: 999px; background: rgba(41,255,122,0.10); border: 1px solid rgba(109,255,176,0.28); box-shadow: inset 0 1px 0 rgba(255,255,255,0.05); }
.admin-status-live span:last-child { font-size: 10.5px; font-weight: 800; letter-spacing: 0.5px; text-transform: uppercase; color: #6dffb0; white-space: nowrap; }
.admin-status-live-dot { position: relative; width: 8px; height: 8px; flex: none; border-radius: 50%; background: #29ff7a; box-shadow: 0 0 6px rgba(41,255,122,0.9); }
.admin-status-live-dot::after { content: ""; position: absolute; inset: -4px; border-radius: 50%; background: rgba(41,255,122,0.55); animation: adminStatusPulse 1.6s ease-out infinite; }
@keyframes adminStatusPulse { 0% { transform: scale(0.4); opacity: 0.9; } 70% { transform: scale(2.1); opacity: 0; } 100% { transform: scale(2.1); opacity: 0; } }

.admin-cards { padding: 4px 16px 0; display: flex; flex-direction: column; gap: 14px; }
.admin-card { position: relative; border-radius: 20px; padding: 16px 16px 14px; background: linear-gradient(155deg, rgba(20,36,26,0.9), rgba(8,14,10,0.94)); border: 1px solid rgba(109,255,176,0.16); box-shadow: 0 10px 26px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.04); overflow: hidden; transition: border-color 0.3s ease, box-shadow 0.3s ease; }
.admin-card.admin-card-active { border-color: rgba(53,255,176,0.55); box-shadow: 0 10px 30px rgba(41,255,122,0.18), inset 0 1px 0 rgba(255,255,255,0.06); }
.admin-card-row { display: flex; align-items: center; gap: 12px; }
.admin-card-icon { width: 44px; height: 44px; flex: none; border-radius: 14px; display: flex; align-items: center; justify-content: center; font-size: 19px; background: rgba(109,255,176,0.1); color: #6dffb0; transition: transform 0.3s ease, background 0.3s ease, color 0.3s ease; }
.admin-card.admin-card-active .admin-card-icon { background: rgba(41,255,122,0.22); color: #baffdc; animation: adminIconPulse 1.4s ease-in-out infinite; }
@keyframes adminIconPulse { 0%, 100% { transform: scale(1); box-shadow: 0 0 0 rgba(41,255,122,0); } 50% { transform: scale(1.08); box-shadow: 0 0 16px rgba(41,255,122,0.55); } }
.admin-card-icon.admin-icon-shutdown { animation: adminIconShutdown 0.42s ease; }
@keyframes adminIconShutdown { 0% { transform: scale(1.15); filter: brightness(1.6); } 60% { transform: scale(0.85); filter: brightness(0.6); } 100% { transform: scale(1); filter: brightness(1); } }
.admin-card-texts { flex: 1; min-width: 0; }
.admin-card-title { font-size: 14.5px; font-weight: 700; color: #eafff2; }
.admin-card-desc { font-size: 11.5px; color: #7fa090; margin-top: 2px; line-height: 1.4; }

/* Cong tac bat/tat kieu iOS */
.admin-switch { position: relative; flex: none; width: 46px; height: 27px; border-radius: 999px; background: rgba(255,255,255,0.14); cursor: pointer; transition: background 0.3s ease; }
.admin-switch::after { content: ""; position: absolute; top: 2px; left: 2px; width: 23px; height: 23px; border-radius: 50%; background: #fff; box-shadow: 0 2px 6px rgba(0,0,0,0.4); transition: transform 0.28s var(--ios-spring-snappy); }
.admin-switch.on { background: linear-gradient(135deg, #29ff7a, #0fae55); }
.admin-switch.on::after { transform: translateX(19px); }
.admin-switch.admin-switch-anim { animation: adminSwitchPop 0.35s ease; }
@keyframes adminSwitchPop { 0% { transform: scale(1); } 40% { transform: scale(1.12); } 100% { transform: scale(1); } }

.admin-card-status { margin-top: 12px; display: flex; align-items: center; justify-content: space-between; gap: 10px; padding-top: 12px; border-top: 1px dashed rgba(109,255,176,0.16); }
.admin-status-label { font-size: 11px; color: #6a8778; letter-spacing: 0.3px; }
.admin-status-value { font-size: 15px; font-weight: 800; color: #4dffab; font-variant-numeric: tabular-nums; letter-spacing: 0.5px; }
.admin-status-value.admin-status-off { color: #56695f; }

.admin-footer-note { margin: 18px 16px 0; text-align: center; font-size: 10.5px; color: #445d4f; letter-spacing: 0.4px; }

/* ===== The dieu huong toi man hinh Tao Token (nam trong Admin Panel) ===== */
.admin-token-navrow { display: flex; align-items: center; gap: 12px; cursor: pointer; -webkit-tap-highlight-color: transparent; }
.admin-token-navrow:active { opacity: 0.72; }
.admin-token-navrow-arrow { flex: none; width: 26px; height: 26px; border-radius: 50%; background: rgba(109,255,176,0.1); color: #6dffb0; display: flex; align-items: center; justify-content: center; font-size: 11px; transition: transform .2s var(--ios-spring-snappy); }
.admin-token-navrow:active .admin-token-navrow-arrow { transform: translateX(3px); }
.admin-token-navrow-count { margin-left: auto; flex: none; font-size: 11px; font-weight: 800; color: #4dffab; background: rgba(41,255,122,0.1); border: 1px solid rgba(109,255,176,0.25); border-radius: 999px; padding: 3px 9px; }

/* ===== Man hinh rieng: Tao Token (truot vao tu ben phai, doc lap voi dashboard) ===== */
#admin-token-screen { position: absolute; inset: 0; z-index: 40; display: flex; flex-direction: column; background: #05130c; transform: translateX(100%); transition: transform 0.36s cubic-bezier(.32,.9,.28,1); overflow: hidden; }
#admin-token-screen.tks-open { transform: translateX(0); }
.tks-header { flex: none; display: flex; align-items: center; gap: 10px; padding: calc(max(env(safe-area-inset-top,0px), 50px) + 14px) 16px 14px; border-bottom: 1px solid rgba(109,255,176,0.12); background: linear-gradient(180deg, rgba(15,40,26,0.6), rgba(5,19,12,0.2)); }
.tks-back-btn { flex: none; width: 34px; height: 34px; border-radius: 50%; background: rgba(255,255,255,0.06); color: #cfeede; display: flex; align-items: center; justify-content: center; font-size: 14px; cursor: pointer; transition: transform .15s var(--ios-spring-snappy), background .2s; }
.tks-back-btn:active { transform: scale(0.85); background: rgba(255,255,255,0.14); }
.tks-title { font-size: 16px; font-weight: 800; letter-spacing: .5px; color: #eafff2; }
.tks-body { flex: 1; min-height: 0; overflow-y: auto; padding: 18px 16px 28px; -webkit-overflow-scrolling: touch; }

.tkw-card { border-radius: 18px; background: linear-gradient(160deg, rgba(20,45,30,0.55), rgba(6,16,10,0.65)); border: 1px solid rgba(109,255,176,0.16); padding: 16px 14px 18px; }
.tkw-wrap { position: relative; display: flex; gap: 6px; margin-top: 4px; }
.tkw-wrap::before { content: ""; position: absolute; left: 4px; right: 4px; top: 50%; height: 40px; transform: translateY(-50%); border-radius: 10px; background: rgba(109,255,176,0.1); border-top: 1px solid rgba(109,255,176,0.4); border-bottom: 1px solid rgba(109,255,176,0.4); pointer-events: none; z-index: 0; }
.tkw-wrap::after { content: ""; position: absolute; inset: 0; z-index: 2; pointer-events: none; background: linear-gradient(180deg, rgba(5,19,12,0.92) 0%, rgba(5,19,12,0) 38%, rgba(5,19,12,0) 62%, rgba(5,19,12,0.92) 100%); }
.tkw-col-wrap { flex: 1; min-width: 0; display: flex; flex-direction: column; align-items: center; position: relative; z-index: 1; }
.tkw-col { height: 160px; width: 100%; overflow-y: scroll; scroll-snap-type: y mandatory; scrollbar-width: none; -ms-overflow-style: none; -webkit-overflow-scrolling: touch; }
.tkw-col::-webkit-scrollbar { display: none; }
.tkw-pad { height: 60px; flex: none; scroll-snap-align: none; }
.tkw-item { height: 40px; line-height: 40px; text-align: center; scroll-snap-align: center; font-size: 15px; font-weight: 700; color: #4a6357; font-variant-numeric: tabular-nums; transition: color .15s ease, font-size .15s ease, transform .15s ease; user-select: none; }
.tkw-item.tkw-active { color: #eafff2; font-size: 19px; }
.tkw-unit-label { margin-top: 7px; font-size: 10px; font-weight: 800; letter-spacing: .5px; color: #6dffb0; text-transform: uppercase; }

.tkw-gen-btn { position: relative; width: 100%; margin-top: 16px; height: 48px; border: none; border-radius: 14px; background: linear-gradient(135deg,#39ffb2,#0fae55); color: #06180d; font-size: 13.5px; font-weight: 800; letter-spacing: 1px; text-transform: uppercase; cursor: pointer; box-shadow: 0 10px 24px rgba(41,255,122,0.3); transition: transform .15s ease; }
.tkw-gen-btn:active { transform: scale(0.97); }

.tkr-result { display: none; margin-top: 14px; padding: 15px; border-radius: 16px; background: rgba(41,255,122,0.08); border: 1px dashed rgba(109,255,176,0.4); align-items: center; justify-content: space-between; gap: 10px; }
.tkr-result.show { display: flex; animation: adminTokenPop .42s cubic-bezier(.34,1.56,.64,1); }
@keyframes adminTokenPop { 0% { opacity: 0; transform: scale(0.85) translateY(6px); } 100% { opacity: 1; transform: scale(1) translateY(0); } }
.tkr-code { font-family: 'Courier New', monospace; font-size: 20px; font-weight: 800; letter-spacing: 3px; color: #6dffb0; }
.tkr-dur { font-size: 10.5px; color: #7fa090; margin-top: 3px; }
.tkr-copy-btn { flex: none; width: 38px; height: 38px; border-radius: 50%; background: rgba(109,255,176,0.14); border: 1px solid rgba(109,255,176,0.3); color: #6dffb0; display: flex; align-items: center; justify-content: center; cursor: pointer; transition: transform .15s var(--ios-spring-snappy), background .2s; }
.tkr-copy-btn:active { transform: scale(0.85); background: rgba(109,255,176,0.28); }
.tkr-copy-btn.copied { background: rgba(41,255,122,0.35); }

.tk-tabs { position: relative; display: flex; margin-top: 22px; background: rgba(255,255,255,0.04); border-radius: 12px; padding: 4px; border: 1px solid rgba(109,255,176,0.14); }
.tk-tab { flex: 1; position: relative; z-index: 2; text-align: center; padding: 9px 0; font-size: 11.5px; font-weight: 800; letter-spacing: .5px; color: #7fa090; background: none; border: none; cursor: pointer; transition: color .3s ease; }
.tk-tab.on { color: #06180d; }
.tk-tab-slider { position: absolute; top: 4px; left: 4px; width: calc(50% - 4px); height: calc(100% - 8px); border-radius: 9px; background: linear-gradient(135deg,#6dffb0,#29c96f); box-shadow: 0 4px 14px rgba(41,255,122,0.3); transition: transform .38s cubic-bezier(.34,1.56,.64,1); z-index: 1; }
.tk-tab-slider.right { transform: translateX(100%); }

.tk-panel { display: none; margin-top: 12px; flex-direction: column; gap: 8px; }
.tk-panel.on { display: flex; }
.admin-token-item { display: flex; align-items: center; gap: 10px; padding: 10px 12px; border-radius: 13px; background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.06); animation: tkItemIn .38s cubic-bezier(.22,1.2,.36,1); }
.admin-token-item.tk-leaving { animation: tkItemOut .32s cubic-bezier(.4,0,.6,1) forwards; }
@keyframes tkItemIn { 0% { opacity: 0; transform: translateY(-8px) scale(0.94); } 100% { opacity: 1; transform: translateY(0) scale(1); } }
@keyframes tkItemOut { 0% { opacity: 1; transform: scale(1); max-height: 60px; margin-bottom: 0; } 100% { opacity: 0; transform: scale(0.9) translateX(14px); max-height: 0; } }
.admin-token-item-code { font-family: 'Courier New', monospace; font-size: 13px; font-weight: 800; letter-spacing: 1.5px; color: #cfeede; flex: none; }
.admin-token-item-mid { flex: 1; min-width: 0; }
.admin-token-item-status { font-size: 10.5px; font-weight: 700; letter-spacing: .3px; }
.admin-token-item-status.st-unused { color: #7fa090; }
.admin-token-item-status.st-active { color: #4dffab; }
.admin-token-item-status.st-expired { color: #ff8577; }
.admin-token-item-time { font-size: 10px; color: #56695f; margin-top: 1px; font-variant-numeric: tabular-nums; }
.admin-token-item-del { flex: none; width: 27px; height: 27px; border-radius: 50%; background: rgba(255,107,107,0.12); color: #ff8577; display: flex; align-items: center; justify-content: center; font-size: 11px; cursor: pointer; transition: transform .15s var(--ios-spring-snappy); }
.admin-token-item-del:active { transform: scale(0.82); }
.admin-token-empty { font-size: 11px; color: #56695f; text-align: center; padding: 16px 0 4px; }
"""

PENALTY_TOKEN_CSS = r"""
/* ===== Cua so noi "Nhap Pass Token" khi mo game Penalty ===== */
#pt-modal-overlay { position: absolute; inset: 0; z-index: 2600; display: none; align-items: center; justify-content: center; background: rgba(2,8,4,0); backdrop-filter: blur(0px); -webkit-backdrop-filter: blur(0px); transition: background 0.35s ease, backdrop-filter 0.35s ease; padding: 20px; box-sizing: border-box; }
#pt-modal-overlay.pt-show { background: rgba(2,8,4,0.58); backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px); }
.pt-card { position: relative; width: min(100%, 300px); border-radius: 22px; padding: 26px 22px 22px; background: linear-gradient(160deg, rgba(20,40,28,0.96), rgba(6,14,9,0.98)); border: 1px solid rgba(143,242,156,0.28); box-shadow: 0 24px 60px rgba(0,0,0,0.6), inset 0 1px 0 rgba(255,255,255,0.06); text-align: center; opacity: 0; transform: scale(0.7) translateY(28px); }
#pt-modal-overlay.pt-show .pt-card { animation: ptCardIn 0.5s cubic-bezier(.34,1.56,.64,1) forwards; }
@keyframes ptCardIn { 0% { opacity: 0; transform: scale(0.7) translateY(30px); } 60% { opacity: 1; transform: scale(1.04) translateY(-4px); } 100% { opacity: 1; transform: scale(1) translateY(0); } }
#pt-modal-overlay.pt-hide .pt-card { animation: ptCardOut 0.28s cubic-bezier(.4,0,.6,1) forwards; }
@keyframes ptCardOut { to { opacity: 0; transform: scale(0.75) translateY(18px); } }
.pt-icon-wrap { width: 58px; height: 58px; margin: 0 auto 14px; border-radius: 50%; display: flex; align-items: center; justify-content: center; background: radial-gradient(circle, rgba(143,242,156,0.22), rgba(143,242,156,0) 72%); position: relative; }
.pt-icon-wrap i { font-size: 22px; color: #8ef29c; }
.pt-icon-wrap::after { content: ""; position: absolute; inset: -6px; border-radius: 50%; border: 1.5px solid rgba(143,242,156,0.3); animation: ptPulseRing 2.2s ease-in-out infinite; }
@keyframes ptPulseRing { 0%, 100% { transform: scale(1); opacity: .6; } 50% { transform: scale(1.12); opacity: 1; } }
.pt-title { font-size: 16px; font-weight: 800; letter-spacing: 1px; color: #eafff2; text-transform: uppercase; margin-bottom: 4px; }
.pt-sub { font-size: 11.5px; color: #7fa090; margin-bottom: 16px; }
.pt-input-wrap { position: relative; margin-bottom: 8px; }
.pt-input { width: 100%; box-sizing: border-box; padding: 13px 14px; border-radius: 12px; border: 1.5px solid rgba(255,255,255,0.14); background: rgba(255,255,255,0.05); color: #eafff2; font-size: 15px; letter-spacing: 3px; text-align: center; text-transform: uppercase; outline: none; font-weight: 700; transition: border-color .25s ease, box-shadow .25s ease, background .25s ease; }
.pt-input::placeholder { letter-spacing: 1px; color: #5c7568; font-weight: 500; text-transform: none; }
.pt-input:focus { border-color: #8ef29c; box-shadow: 0 0 0 3px rgba(143,242,156,0.15); background: rgba(255,255,255,0.08); }
.pt-input-wrap.pt-shake { animation: ptShake 0.45s ease; }
@keyframes ptShake { 0%, 100% { transform: translateX(0); } 20% { transform: translateX(-8px); } 40% { transform: translateX(7px); } 60% { transform: translateX(-5px); } 80% { transform: translateX(3px); } }
.pt-input-wrap.pt-err .pt-input { border-color: #ff6b6b; box-shadow: 0 0 0 3px rgba(255,107,107,0.15); }
.pt-msg { min-height: 15px; font-size: 11.5px; color: #ff8a8a; margin-bottom: 14px; transition: opacity .2s ease; }
.pt-msg.pt-ok { color: #8ef29c; }
.pt-actions { display: flex; gap: 10px; }
.pt-btn { flex: 1; height: 44px; border: none; border-radius: 12px; font-size: 13px; font-weight: 800; letter-spacing: 1px; text-transform: uppercase; cursor: pointer; transition: transform .15s ease, filter .2s ease; }
.pt-btn:active { transform: scale(0.96); }
.pt-btn-cancel { background: rgba(255,255,255,0.08); color: #cfeede; border: 1px solid rgba(255,255,255,0.12); }
.pt-btn-confirm { position: relative; background: linear-gradient(135deg,#3ddc6b,#1f8a43); color: #06120a; overflow: hidden; box-shadow: 0 10px 22px rgba(47,184,90,0.35); }
.pt-btn-confirm .pt-spin { display: none; width: 16px; height: 16px; border: 2.2px solid rgba(6,18,10,0.28); border-top-color: #06120a; border-radius: 50%; animation: ptSpin 0.7s linear infinite; margin: 0 auto; }
.pt-btn-confirm.pt-loading .pt-lbl { display: none; }
.pt-btn-confirm.pt-loading .pt-spin { display: block; }
@keyframes ptSpin { to { transform: rotate(360deg); } }
.pt-check-overlay { position: absolute; inset: 0; z-index: 5; display: none; align-items: center; justify-content: center; background: rgba(4,10,6,0.7); border-radius: 22px; backdrop-filter: blur(3px); }
.pt-check-overlay.pt-show2 { display: flex; }
.pt-check-circle { width: 66px; height: 66px; border-radius: 50%; background: radial-gradient(circle,#8ef29c,#2fb85a 70%); display: flex; align-items: center; justify-content: center; box-shadow: 0 0 34px rgba(143,242,156,0.6); transform: scale(0); animation: ptCheckPop 0.5s cubic-bezier(.34,1.56,.64,1) forwards; }
@keyframes ptCheckPop { to { transform: scale(1); } }
.pt-check-circle svg { width: 32px; height: 32px; }
.pt-check-circle path { stroke: #06120a; stroke-width: 4; fill: none; stroke-linecap: round; stroke-linejoin: round; stroke-dasharray: 40; stroke-dashoffset: 40; animation: ptCheckDraw .35s ease .3s forwards; }
@keyframes ptCheckDraw { to { stroke-dashoffset: 0; } }
"""

ADMIN_BODY_APP = r"""
<div class="simple-app" id="app-admin">
  <div class="admin-boot" id="admin-boot">
    <div class="admin-matrix" id="admin-matrix"></div>
    <div class="admin-boot-core">
      <svg class="admin-boot-logo" viewBox="0 0 68 68" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <linearGradient id="adminBootGrad" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stop-color="#39ffb2"/>
            <stop offset="60%" stop-color="#0fae55"/>
            <stop offset="100%" stop-color="#063a24"/>
          </linearGradient>
        </defs>
        <rect x="2" y="2" width="64" height="64" rx="16" fill="#04140b" stroke="url(#adminBootGrad)" stroke-width="2.4"/>
        <text x="34" y="41" text-anchor="middle" font-family="Courier New, monospace" font-size="24" font-weight="700" fill="#39ffb2">&gt;_</text>
      </svg>
      <div class="admin-boot-lines" id="admin-boot-lines">
        <div class="admin-boot-line">&gt; connecting to MAGICOS core...</div>
        <div class="admin-boot-line">&gt; verifying admin credentials...</div>
        <div class="admin-boot-line">&gt; access level: ROOT [granted]</div>
      </div>
      <div class="admin-boot-title" id="admin-boot-title">ACCESS GRANTED</div>
    </div>
    <div class="admin-scanlines"></div>
  </div>

  <div class="admin-dashboard">
    <div class="admin-header">
      <svg class="admin-header-logo" viewBox="0 0 68 68" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <linearGradient id="adminHeadGrad" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stop-color="#39ffb2"/>
            <stop offset="100%" stop-color="#0a6b3f"/>
          </linearGradient>
        </defs>
        <rect x="2" y="2" width="64" height="64" rx="15" fill="#04140b" stroke="url(#adminHeadGrad)" stroke-width="2.2"/>
        <text x="34" y="41" text-anchor="middle" font-family="Courier New, monospace" font-size="22" font-weight="700" fill="#39ffb2">&gt;_</text>
      </svg>
      <div class="admin-header-text">
        <div class="admin-header-title">Admin Panel</div>
        <div class="admin-header-sub">Chỉ dành cho nhà phát triển</div>
      </div>
      <div class="admin-status-live"><span class="admin-status-live-dot"></span><span>ADMIN</span></div>
    </div>

    <div class="admin-cards">
      <div class="admin-card" id="admin-server-card">
        <div class="admin-card-row">
          <div class="admin-card-icon server-orb">◉</div>
          <div class="admin-card-texts"><div class="admin-card-title">Sever Người Dùng</div></div>
          <button type="button" id="admin-server-switch" class="admin-switch" role="switch" aria-label="Mở server người dùng" aria-checked="false" disabled onclick="toggleUserServer()"></button>
        </div>
        <div class="sr-only"><span id="admin-server-status" role="status">Đang kết nối…</span><span id="admin-server-action"></span></div>
      </div>
      <div class="admin-card" id="admin-call-card">
        <div class="admin-card-row">
          <div class="admin-card-icon" id="admin-call-icon"><i class="fa-solid fa-phone-volume"></i></div>
          <div class="admin-card-texts">
            <div class="admin-card-title">Gọi điện tự động</div>
          </div>
          <div class="admin-switch" id="admin-call-switch" onclick="toggleAdminCall()"></div>
        </div>
        <div class="admin-card-status">
          <span class="admin-status-label">Cuộc gọi tiếp theo sau</span>
          <span class="admin-status-value admin-status-off" id="admin-call-countdown">Đã tắt</span>
        </div>
      </div>

      <div class="admin-card" id="admin-notif-card">
        <div class="admin-card-row">
          <div class="admin-card-icon" id="admin-notif-icon"><i class="fa-solid fa-bell"></i></div>
          <div class="admin-card-texts">
            <div class="admin-card-title">Thông báo tự động</div>
          </div>
          <div class="admin-switch" id="admin-notif-switch" onclick="toggleAdminNotif()"></div>
        </div>
        <div class="admin-card-status">
          <span class="admin-status-label">Thông báo tiếp theo sau</span>
          <span class="admin-status-value admin-status-off" id="admin-notif-countdown">Đã tắt</span>
        </div>
      </div>

      <div class="admin-card" id="admin-token-card">
        <div class="admin-token-navrow" onclick="adminOpenTokenScreen()">
          <div class="admin-card-icon"><i class="fa-solid fa-key"></i></div>
          <div class="admin-card-texts">
            <div class="admin-card-title">Tạo Token</div>
            <div class="admin-card-desc">Tạo Pass Token cho phép chơi Penalty trong một khoảng thời gian.</div>
          </div>
          <span class="admin-token-navrow-count" id="admin-token-active-count">0</span>
          <div class="admin-token-navrow-arrow"><i class="fa-solid fa-chevron-right"></i></div>
        </div>
      </div>
    </div>
    <div class="admin-footer-note">MAGICOS ADMIN • BUILD FOR DEVELOPER</div>
  </div>

  <div id="admin-token-screen">
    <div class="tks-header">
      <div class="tks-back-btn" onclick="adminCloseTokenScreen()"><i class="fa-solid fa-chevron-left"></i></div>
      <div class="tks-title">Tạo Token</div>
    </div>
    <div class="tks-body">
      <div class="tkw-card">
        <div class="tkw-wrap">
          <div class="tkw-col-wrap">
            <div class="tkw-col" id="tkw-col-day" data-max="30"></div>
            <div class="tkw-unit-label">Ngày</div>
          </div>
          <div class="tkw-col-wrap">
            <div class="tkw-col" id="tkw-col-hour" data-max="23"></div>
            <div class="tkw-unit-label">Giờ</div>
          </div>
          <div class="tkw-col-wrap">
            <div class="tkw-col" id="tkw-col-minute" data-max="59"></div>
            <div class="tkw-unit-label">Phút</div>
          </div>
          <div class="tkw-col-wrap">
            <div class="tkw-col" id="tkw-col-second" data-max="59"></div>
            <div class="tkw-unit-label">Giây</div>
          </div>
        </div>
        <button type="button" class="tkw-gen-btn" onclick="adminGenerateToken()">Tạo Token</button>
        <div class="tkr-result" id="admin-token-result">
          <div>
            <div class="tkr-code" id="admin-token-result-code">-</div>
            <div class="tkr-dur" id="admin-token-result-dur">-</div>
          </div>
          <div class="tkr-copy-btn" id="admin-token-copy-btn" onclick="adminCopyToken()"><i class="fa-solid fa-copy"></i></div>
        </div>
      </div>

      <div class="tk-tabs" id="tk-tabs">
        <div class="tk-tab-slider" id="tk-tab-slider"></div>
        <button type="button" class="tk-tab on" data-tab="active" onclick="adminSwitchTokenTab('active')">CÒN HẠN</button>
        <button type="button" class="tk-tab" data-tab="expired" onclick="adminSwitchTokenTab('expired')">HẾT HẠN</button>
      </div>
      <div class="tk-panel on" id="tk-panel-active"></div>
      <div class="tk-panel" id="tk-panel-expired"></div>
    </div>
  </div>
</div>
"""

ADMIN_JS = r"""
(function () {
  var appEl = document.getElementById('app-admin');
  if (!appEl) return;
  DOCK_APP_META['app-admin'] = { name: 'Admin', icon: 'fa-solid fa-terminal', grad: 'linear-gradient(135deg,#39ffb2,#0a6b3f)' };

  var MATRIX_CHARS = '01アカサタナハマヤラワ$#%&ABCDEFGHIJKLMNOPQRSTUVWXYZ';
  function buildMatrix() {
    var wrap = document.getElementById('admin-matrix');
    if (!wrap || wrap.dataset.built) return;
    wrap.dataset.built = '1';
    var cols = 20;
    for (var i = 0; i < cols; i++) {
      var col = document.createElement('div');
      col.className = 'admin-matrix-col';
      col.style.left = (i * (100 / cols)) + '%';
      var lines = 22 + Math.floor(Math.random() * 10);
      var txt = '';
      for (var j = 0; j < lines; j++) txt += MATRIX_CHARS.charAt(Math.floor(Math.random() * MATRIX_CHARS.length)) + '\n';
      col.textContent = txt;
      col.style.animationDuration = (2.2 + Math.random() * 2.2) + 's';
      col.style.animationDelay = (Math.random() * -3) + 's';
      wrap.appendChild(col);
    }
  }

  var adminBooted = false;
  function runAdminBoot() {
    var boot = document.getElementById('admin-boot');
    if (!boot) return;
    if (adminBooted) {
      /* Da chay hieu ung khoi dong roi (tu lan mo dau tien) - nhung lan mo lai
         sau khong phat lai hieu ung loading nua, vao thang dashboard. */
      boot.style.display = 'none';
      boot.classList.add('admin-boot-hide');
      return;
    }
    adminBooted = true;
    var lines = document.querySelectorAll('#admin-boot-lines .admin-boot-line');
    var title = document.getElementById('admin-boot-title');
    buildMatrix();
    boot.style.display = 'flex';
    boot.classList.remove('admin-boot-hide');
    lines.forEach(function (el) { el.classList.remove('admin-line-run'); });
    title.classList.remove('admin-title-show');
    void boot.offsetWidth;
    lines.forEach(function (el, idx) {
      setTimeout(function () { el.classList.add('admin-line-run'); }, 220 + idx * 480);
    });
    var revealAt = 220 + lines.length * 480 + 200;
    setTimeout(function () { title.classList.add('admin-title-show'); }, revealAt);
    clearTimeout(appEl.__adminBootTimer);
    appEl.__adminBootTimer = setTimeout(function () {
      boot.classList.add('admin-boot-hide');
    }, revealAt + 900);
  }
  window.openAdminApp = runAdminBoot;

  window.closeAdminApp = function () {
    closeAppToIcon('app-admin');
    var idx = activeAppsList.indexOf('app-admin');
    if (idx > -1) activeAppsList.splice(idx, 1);
    if (historyPointer >= activeAppsList.length) historyPointer = activeAppsList.length - 1;
    if (foregroundAppId === 'app-admin') {
      foregroundAppId = activeAppsList.length ? activeAppsList[activeAppsList.length - 1] : null;
    }
    if (typeof applyCallIslandState === 'function') applyCallIslandState();
  };

  function fmtMMSS(sec) {
    sec = Math.max(0, Math.round(sec));
    var m = Math.floor(sec / 60), s = sec % 60;
    return (m < 10 ? '0' + m : m) + ':' + (s < 10 ? '0' + s : s);
  }
  function flashIconShutdown(id) {
    var icon = document.getElementById(id);
    if (!icon) return;
    icon.classList.remove('admin-icon-shutdown');
    void icon.offsetWidth;
    icon.classList.add('admin-icon-shutdown');
  }

  /* ================= GOI DIEN TU DONG 1 PHUT ================= */
  var CALL_PERIOD = 60;
  var callTickInterval = null;
  var callRemaining = CALL_PERIOD;
  var callOn = false;
  var callSwitchEl = document.getElementById('admin-call-switch');
  var callCardEl = document.getElementById('admin-call-card');
  var callCountdownEl = document.getElementById('admin-call-countdown');

  function renderCallCountdown() {
    if (!callCountdownEl) return;
    if (!callOn) { callCountdownEl.textContent = 'Đã tắt'; callCountdownEl.classList.add('admin-status-off'); return; }
    callCountdownEl.classList.remove('admin-status-off');
    callCountdownEl.textContent = fmtMMSS(callRemaining);
  }

  function fireAdminCall() {
    /* Kich hoat cuoc goi den THAT trong app Dien thoai (qua postMessage) thay vi
       chi ve UI gia tren Dynamic Island. Nho vay khi nguoi dung bam Nghe ngay
       tren island, no se thuc su ket noi va mo dung giao dien cuoc goi cua app
       Dien thoai, thay vi tu tat sau vai giay ma khong lam gi ca. */
    if (typeof sendPhoneAppMessage === 'function') sendPhoneAppMessage('trigger_incoming', 'ADMIN');
  }

  window.toggleAdminCall = function () {
    callOn = !callOn;
    if (navigator.vibrate) try { navigator.vibrate(15); } catch (e) {}
    if (callSwitchEl) {
      callSwitchEl.classList.toggle('on', callOn);
      callSwitchEl.classList.remove('admin-switch-anim'); void callSwitchEl.offsetWidth; callSwitchEl.classList.add('admin-switch-anim');
    }
    if (callCardEl) callCardEl.classList.toggle('admin-card-active', callOn);
    clearInterval(callTickInterval);
    if (callOn) {
      callRemaining = CALL_PERIOD;
      renderCallCountdown();
      callTickInterval = setInterval(function () {
        callRemaining--;
        if (callRemaining <= 0) {
          fireAdminCall();
          callRemaining = CALL_PERIOD;
        }
        renderCallCountdown();
      }, 1000);
    } else {
      flashIconShutdown('admin-call-icon');
      renderCallCountdown();
    }
  };

  /* ================= THONG BAO TU DONG 30 GIAY ================= */
  var NOTIF_PERIOD = 30;
  var notifTickInterval = null;
  var notifRemaining = NOTIF_PERIOD;
  var notifOn = false;
  var notifSwitchEl = document.getElementById('admin-notif-switch');
  var notifCardEl = document.getElementById('admin-notif-card');
  var notifCountdownEl = document.getElementById('admin-notif-countdown');
  var ADMIN_MESSAGES = [
    'Hệ thống đang hoạt động ổn định.',
    'Đã đồng bộ dữ liệu thành công.',
    'Không phát hiện truy cập bất thường.',
    'Sao lưu tự động đã hoàn tất.',
    'Có 1 phiên đăng nhập mới từ quản trị viên.',
    'CPU và bộ nhớ trong ngưỡng an toàn.',
    'Kiểm tra bảo mật định kỳ: OK.',
    'Nhật ký hệ thống vừa được cập nhật.'
  ];

  function renderNotifCountdown() {
    if (!notifCountdownEl) return;
    if (!notifOn) { notifCountdownEl.textContent = 'Đã tắt'; notifCountdownEl.classList.add('admin-status-off'); return; }
    notifCountdownEl.classList.remove('admin-status-off');
    notifCountdownEl.textContent = fmtMMSS(notifRemaining);
  }

  function fireAdminNotif() {
    var msg = ADMIN_MESSAGES[Math.floor(Math.random() * ADMIN_MESSAGES.length)];
    /* Thong bao phai xuat hien tren THANH THONG BAO that (vuot xuong tu goc
       trai man hinh) - khong chi la 1 lop noi len thoang qua tren Dynamic
       Island. Van giu them 1 nhip nhay nhanh tren island cho sinh dong. */
    if (typeof showNotification === 'function') showNotification(msg, 'info', '<i class="fa-solid fa-bell"></i>', 'Admin');
  }

  window.toggleAdminNotif = function () {
    notifOn = !notifOn;
    if (navigator.vibrate) try { navigator.vibrate(15); } catch (e) {}
    if (notifSwitchEl) {
      notifSwitchEl.classList.toggle('on', notifOn);
      notifSwitchEl.classList.remove('admin-switch-anim'); void notifSwitchEl.offsetWidth; notifSwitchEl.classList.add('admin-switch-anim');
    }
    if (notifCardEl) notifCardEl.classList.toggle('admin-card-active', notifOn);
    clearInterval(notifTickInterval);
    if (notifOn) {
      notifRemaining = NOTIF_PERIOD;
      renderNotifCountdown();
      notifTickInterval = setInterval(function () {
        notifRemaining--;
        if (notifRemaining <= 0) {
          fireAdminNotif();
          notifRemaining = NOTIF_PERIOD;
        }
        renderNotifCountdown();
      }, 1000);
    } else {
      flashIconShutdown('admin-notif-icon');
      renderNotifCountdown();
    }
  };

  /* ================= KHOI DONG LAI TU DAU KHI APP BI DONG HAN =================
     "Dong tat ca" (hoac vuot huy 1 app rieng le) trong app switcher = dong han
     app do (giong dong app that tren dien thoai), khac voi chi ve home man
     hinh (chi la "dua app xuong nen", DOM/trang thai van giu nguyen). Khi Admin
     bi dong han, lan mo lai sau phai chay lai dung tu dau: hieu ung boot +
     tat het cac cong tac dang bat (khong con "cham" tu phien truoc).*/
  document.addEventListener('magicos-app-terminated', function (ev) {
    if (!ev || !ev.detail || ev.detail.appId !== 'app-admin') return;
    adminBooted = false;
    if (callOn) toggleAdminCall();
    if (notifOn) toggleAdminNotif();
  });
})();
"""

PENALTY_TOKEN_JS = r"""
(function () {
  var TOKENS_KEY = 'magicos_penalty_tokens_v1';
  /* ===== TACH PHIEN THEO VAI (Nguoi dung thuong ma 000000 / Nha phat trien
     ma 081120) =====
     Truoc day SESSION_KEY la 1 chuoi co dinh dung CHUNG cho ca 2 ma mo khoa,
     nen token nhap/thu o man hinh Admin (081120) cung tao ra 1 "phien Penalty
     hop le" ma man hinh Nguoi dung thuong (000000) tren CUNG trinh duyet doc
     duoc luon - 2 vai tuy khac ma mo khoa nhung van la 1 trang/1 localStorage
     nen bi dung chung. Gio SESSION_KEY duoc tinh rieng theo vai dang mo khoa
     hien tai (adminModeUnlocked, khai bao o ANIM_JS_1, chay truoc doan nay),
     nen phien cua ben nay khong con "lo" sang ben kia nua du la cung 1 may.
     Danh sach TOKENS_KEY van dung CHUNG - do la token do Nha phat trien tao
     ra de phat cho Nguoi dung thuong nhap, nen phai thay duoc nhau. */
  function currentPenaltyRole() {
    return (typeof adminModeUnlocked !== 'undefined' && adminModeUnlocked) ? 'admin' : 'user';
  }
  function sessionKeyForCurrentRole() {
    return 'magicos_penalty_session_v1_' + currentPenaltyRole();
  }

  function loadTokens() {
    try {
      var raw = localStorage.getItem(TOKENS_KEY);
      return raw ? (JSON.parse(raw) || {}) : {};
    } catch (e) { return {}; }
  }
  function saveTokens() {
    try { localStorage.setItem(TOKENS_KEY, JSON.stringify(window.PenaltyTokens || {})); } catch (e) {}
  }
  function loadSession() {
    try {
      var raw = localStorage.getItem(sessionKeyForCurrentRole());
      var s = raw ? JSON.parse(raw) : null;
      if (s && s.active && s.expiresAt && Date.now() < s.expiresAt) return s;
    } catch (e) {}
    return { active: false, expiresAt: 0, tokenCode: null };
  }
  function saveSession() {
    try { localStorage.setItem(sessionKeyForCurrentRole(), JSON.stringify(window.PenaltySession || {})); } catch (e) {}
  }
  window.penaltySaveTokens = saveTokens;
  window.penaltySaveSession = saveSession;

  /* window.PenaltyTokens duoc nap tu localStorage ngay tu dau, nen token da
     tao van con nguyen sau khi F5 / dong mo lai trinh duyet - khong bi mat. */
  window.PenaltyTokens = loadTokens();
  window.PenaltySession = loadSession();
  /* Ghi nho vai luc phien Penalty vua duoc doc, de phat hien khi nguoi dung
     khoa may roi mo lai bang ma khac (thuong <-> admin) thi phai doc lai DUNG
     phien cua vai moi, khong giu nham phien cua vai cu trong bo nho. */
  var loadedPenaltyRole = currentPenaltyRole();
  function ensurePenaltySessionForRole() {
    var role = currentPenaltyRole();
    if (role !== loadedPenaltyRole) {
      loadedPenaltyRole = role;
      window.PenaltySession = loadSession();
    }
  }

  var pendingIconEl = null;

  function els() {
    return {
      overlay: document.getElementById('pt-modal-overlay'),
      input: document.getElementById('pt-input'),
      wrap: document.getElementById('pt-input-wrap'),
      msg: document.getElementById('pt-msg'),
      confirmBtn: document.getElementById('pt-confirm-btn'),
      checkOverlay: document.getElementById('pt-check-overlay')
    };
  }

  function fmtRemain(ms) {
    if (ms < 0) ms = 0;
    var totalSec = Math.floor(ms / 1000);
    var h = Math.floor(totalSec / 3600);
    var m = Math.floor((totalSec % 3600) / 60);
    var s = totalSec % 60;
    function p2(n) { return (n < 10 ? '0' : '') + n; }
    return (h > 0 ? (p2(h) + ':') : '') + p2(m) + ':' + p2(s);
  }
  window.penaltyFmtRemain = fmtRemain;

  window.isPenaltySessionValid = function () {
    ensurePenaltySessionForRole();
    return window.PenaltySession.active && Date.now() < window.PenaltySession.expiresAt;
  };
  window.penaltyRemainingMs = function () {
    ensurePenaltySessionForRole();
    if (!window.PenaltySession.active) return 0;
    return Math.max(0, window.PenaltySession.expiresAt - Date.now());
  };

  function openPenaltyForReal(iconEl) {
    openAppFromIcon('app-penalty', iconEl);
    trackApp('app-penalty');
  }

  window.handlePenaltyIconTap = function (iconEl) {
    if (window.isPenaltySessionValid()) {
      openPenaltyForReal(iconEl);
      return;
    }
    pendingIconEl = iconEl;
    window.showPassTokenModal();
  };

  window.showPassTokenModal = function (msg) {
    var e = els();
    if (!e.overlay) return;
    e.input.value = '';
    e.wrap.classList.remove('pt-err', 'pt-shake');
    e.msg.textContent = msg || '';
    e.msg.classList.remove('pt-ok');
    e.confirmBtn.classList.remove('pt-loading', 'pt-success');
    e.checkOverlay.classList.remove('pt-show2');
    e.overlay.classList.remove('pt-hide');
    e.overlay.style.display = 'flex';
    void e.overlay.offsetWidth;
    e.overlay.classList.add('pt-show');
    setTimeout(function () { e.input.focus(); }, 260);
  };

  window.cancelPassToken = function () {
    var e = els();
    e.overlay.classList.remove('pt-show');
    e.overlay.classList.add('pt-hide');
    setTimeout(function () {
      e.overlay.style.display = 'none';
      e.overlay.classList.remove('pt-hide');
    }, 300);
    pendingIconEl = null;
  };

  window.confirmPassToken = function () {
    ensurePenaltySessionForRole();
    var e = els();
    var code = (e.input.value || '').trim().toUpperCase();
    if (!code) {
      e.wrap.classList.add('pt-shake');
      setTimeout(function () { e.wrap.classList.remove('pt-shake'); }, 460);
      return;
    }
    e.confirmBtn.classList.add('pt-loading');
    e.msg.textContent = '';
    e.wrap.classList.remove('pt-err');
    setTimeout(function () {
      var tok = window.PenaltyTokens[code];
      var now = Date.now();
      /* Han dung cua token duoc tinh tu LUC ADMIN TAO no (tok.expiresAt =
         createdAt + durationMs, dat san tu khi tao), khong phai tu luc
         nguoi dung nhap - dung y "token duoc tao ke tu khi admin tao no
         bat dau dem nguoc". */
      var expired = tok && now >= tok.expiresAt;
      var valid = tok && !tok.used && !expired;
      if (valid) {
        tok.used = true;
        tok.usedAt = now;
        window.PenaltySession = { active: true, expiresAt: tok.expiresAt, tokenCode: code };
        saveTokens();
        saveSession();
        if (typeof window.renderAdminTokenList === 'function') window.renderAdminTokenList();
        if (typeof window.penaltyUpdateBadge === 'function') window.penaltyUpdateBadge();
        e.confirmBtn.classList.remove('pt-loading');
        e.checkOverlay.classList.add('pt-show2');
        e.msg.classList.add('pt-ok');
        e.msg.textContent = 'Token hợp lệ!';
        setTimeout(function () {
          e.overlay.classList.remove('pt-show');
          e.overlay.classList.add('pt-hide');
          setTimeout(function () {
            e.overlay.style.display = 'none';
            e.overlay.classList.remove('pt-hide');
            e.checkOverlay.classList.remove('pt-show2');
            if (pendingIconEl) { openPenaltyForReal(pendingIconEl); pendingIconEl = null; }
          }, 320);
        }, 700);
      } else {
        e.confirmBtn.classList.remove('pt-loading');
        e.wrap.classList.add('pt-err', 'pt-shake');
        e.msg.classList.remove('pt-ok');
        e.msg.textContent = expired ? 'Pass Token đã hết hạn' : 'Pass Token không đúng hoặc đã được dùng';
        setTimeout(function () { e.wrap.classList.remove('pt-shake'); }, 460);
      }
    }, 900);
  };

  function forceClosePenaltyApp() {
    if (typeof closeAppToIcon === 'function') closeAppToIcon('app-penalty');
    if (typeof activeAppsList !== 'undefined') {
      var idx = activeAppsList.indexOf('app-penalty');
      if (idx > -1) activeAppsList.splice(idx, 1);
      if (typeof historyPointer !== 'undefined' && historyPointer >= activeAppsList.length) {
        historyPointer = activeAppsList.length - 1;
      }
    }
    if (typeof foregroundAppId !== 'undefined' && foregroundAppId === 'app-penalty') {
      foregroundAppId = activeAppsList.length ? activeAppsList[activeAppsList.length - 1] : null;
    }
    if (typeof applyCallIslandState === 'function') applyCallIslandState();
  }

  /* ===== Badge dem nguoc gan duoi Dynamic Island =====
     Chi hien khi ung dung dang o tren cung la app Penalty VA phien token
     con hop le; roi khoi app Penalty (ve home, mo app khac, mo app
     switcher...) la an ngay - dung y "khong o app penalty nua thi bo dem
     khong hien nua, con o trong app penalty thi luon hien den khi het". */
  var badgeTimeEl = null;
  function isInPenaltyApp() {
    return typeof foregroundAppId !== 'undefined' && foregroundAppId === 'app-penalty';
  }
  /* Chi cho phep dem nguoc Penalty chiem Dynamic Island khi island dang o
     trang thai binh thuong hoac dang chinh la state-penalty - KHONG chiem
     quyen cua canh bao he thong / Face ID / cuoc goi (nhung lop nay quan
     trong hon, tu chung se phuc hoi lai state-penalty trong vong 1 giay
     sau khi ket thuc, thong qua tick dinh ky ben duoi). */
  function canShowPenaltyIsland() {
    if (typeof island === 'undefined' || !island) return false;
    return !(island.classList.contains('state-maintenance') || island.classList.contains('state-warning') ||
      island.classList.contains('state-faceid') ||
      island.classList.contains('state-call-ring') ||
      island.classList.contains('state-call-active'));
  }
  function updatePenaltyBadge() {
    if (!badgeTimeEl) badgeTimeEl = document.getElementById('penalty-live-badge-time');
    var valid = window.isPenaltySessionValid();
    var previewing = typeof switcherOpen !== 'undefined' && switcherOpen;
    var visible = document.body.classList.contains('unlocked') && !isNotifPeekOpen &&
      (previewing ? stageSelectedId === 'app-penalty' : isInPenaltyApp());
    var shouldShow = valid && visible;
    if (typeof island === 'undefined' || !island) return;
    if (shouldShow && canShowPenaltyIsland()) {
      var remain = window.penaltyRemainingMs();
      if (badgeTimeEl) badgeTimeEl.textContent = fmtRemain(remain);
      if (!island.classList.contains('state-penalty')) {
        if (typeof clearTimeout === 'function') { clearTimeout(autoCloseTimeout); clearTimeout(resetTextTimeout); }
        island.className = 'state-penalty island-animating';
        if (typeof hideAllContents === 'function') hideAllContents();
        var contentEl = document.getElementById('content-penalty');
        if (contentEl) contentEl.classList.add('show-content');
        if (typeof toggleReflow === 'function') toggleReflow('penalty');
      }
      island.classList.toggle('penalty-warn', remain < 60000);
    } else if (island.classList.contains('state-penalty')) {
      if (typeof resetIsland === 'function') resetIsland();
    }
  }
  window.penaltyUpdateBadge = updatePenaltyBadge;

  /* Ticker toan cuc: chay lien tuc tu khi trang tai xong (khong chi khi vua
     nhap token thanh cong), de neu con phien hop le duoc phuc hoi tu
     localStorage sau khi F5 thi van tiep tuc dem nguoc dung, khong bi mat. */
  setInterval(function () {
    ensurePenaltySessionForRole();
    updatePenaltyBadge();
    if (!window.PenaltySession.active) return;
    if (Date.now() >= window.PenaltySession.expiresAt) {
      window.PenaltySession.active = false;
      saveSession();
      if (typeof window.renderAdminTokenList === 'function') window.renderAdminTokenList();
      var inGame = isInPenaltyApp();
      if (inGame) {
        forceClosePenaltyApp();
        updatePenaltyBadge();
        setTimeout(function () { window.showPassTokenModal('Pass Token đã hết hạn, vui lòng nhập token mới'); }, 340);
      }
    }
  }, 1000);
})();
"""

ADMIN_TOKEN_JS = r"""
(function () {
  window.PenaltyTokens = window.PenaltyTokens || {};
  var lastGeneratedCode = null;
  var ITEM_H = 40;
  var COLS = ['day', 'hour', 'minute', 'second'];
  var wheelsBuilt = false;
  var currentTab = 'active';
  var knownActiveCodes = {}, knownExpiredCodes = {};

  function saveTokens() {
    if (typeof window.penaltySaveTokens === 'function') window.penaltySaveTokens();
  }

  /* ===== Man hinh Tao Token: mo / dong (doc lap voi dashboard, chi la 1
     lop truot vao tu ben phai o trong chinh app Admin) ===== */
  window.adminOpenTokenScreen = function () {
    var scr = document.getElementById('admin-token-screen');
    if (!scr) return;
    if (!wheelsBuilt) { buildAllWheels(); wheelsBuilt = true; }
    scr.classList.add('tks-open');
    window.renderAdminTokenList();
  };
  window.adminCloseTokenScreen = function () {
    var scr = document.getElementById('admin-token-screen');
    if (scr) scr.classList.remove('tks-open');
  };

  /* ===== Wheel picker kieu "van dong ho" (cuon + snap tung dong) ===== */
  function buildWheel(colId, max) {
    var col = document.getElementById(colId);
    if (!col) return;
    var html = '<div class="tkw-pad"></div>';
    for (var i = 0; i <= max; i++) html += '<div class="tkw-item" data-val="' + i + '">' + (i < 10 ? '0' + i : i) + '</div>';
    html += '<div class="tkw-pad"></div>';
    col.innerHTML = html;
    col.scrollTop = 0;
    var tickTimer = null;
    col.addEventListener('scroll', function () {
      highlightWheel(col);
      clearTimeout(tickTimer);
      tickTimer = setTimeout(function () { snapWheel(col); }, 90);
    }, { passive: true });
    highlightWheel(col);
  }
  function highlightWheel(col) {
    var idx = Math.round(col.scrollTop / ITEM_H);
    var items = col.querySelectorAll('.tkw-item');
    items.forEach(function (it, i) { it.classList.toggle('tkw-active', i === idx); });
  }
  function snapWheel(col) {
    var idx = Math.round(col.scrollTop / ITEM_H);
    col.scrollTo({ top: idx * ITEM_H, behavior: 'smooth' });
  }
  function buildAllWheels() {
    buildWheel('tkw-col-day', 30);
    buildWheel('tkw-col-hour', 23);
    buildWheel('tkw-col-minute', 59);
    buildWheel('tkw-col-second', 59);
  }
  function readWheel(colId) {
    var col = document.getElementById(colId);
    if (!col) return 0;
    return Math.max(0, Math.round(col.scrollTop / ITEM_H));
  }
  function resetWheels() {
    COLS.forEach(function (u) {
      var col = document.getElementById('tkw-col-' + u);
      if (col) { col.scrollTo({ top: 0, behavior: 'smooth' }); highlightWheel(col); }
    });
  }

  function genCode() {
    var chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
    var code = '';
    for (var i = 0; i < 8; i++) code += chars.charAt(Math.floor(Math.random() * chars.length));
    if (window.PenaltyTokens[code]) return genCode();
    return code;
  }

  function fmtDuration(ms) {
    var totalSec = Math.round(ms / 1000);
    var d = Math.floor(totalSec / 86400), h = Math.floor((totalSec % 86400) / 3600),
        m = Math.floor((totalSec % 3600) / 60), s = totalSec % 60;
    var parts = [];
    if (d) parts.push(d + ' ngày');
    if (h) parts.push(h + ' giờ');
    if (m) parts.push(m + ' phút');
    if (s || !parts.length) parts.push(s + ' giây');
    return parts.join(' ');
  }

  window.adminGenerateToken = function () {
    var d = readWheel('tkw-col-day'), h = readWheel('tkw-col-hour'),
        m = readWheel('tkw-col-minute'), s = readWheel('tkw-col-second');
    var durationMs = ((d * 86400) + (h * 3600) + (m * 60) + s) * 1000;
    var genBtn = document.querySelector('.tkw-gen-btn');
    if (durationMs <= 0) {
      if (genBtn) {
        genBtn.style.animation = 'none'; void genBtn.offsetWidth;
        genBtn.style.animation = 'ptShake .45s ease';
        setTimeout(function () { genBtn.style.animation = ''; }, 460);
      }
      return;
    }
    var now = Date.now();
    var code = genCode();
    window.PenaltyTokens[code] = {
      durationMs: durationMs,
      createdAt: now,
      expiresAt: now + durationMs,
      used: false,
      usedAt: null
    };
    saveTokens();
    lastGeneratedCode = code;
    var resultEl = document.getElementById('admin-token-result');
    document.getElementById('admin-token-result-code').textContent = code;
    document.getElementById('admin-token-result-dur').textContent = 'Thời hạn: ' + fmtDuration(durationMs);
    resultEl.classList.remove('show');
    void resultEl.offsetWidth;
    resultEl.classList.add('show');
    var copyBtn = document.getElementById('admin-token-copy-btn');
    copyBtn.classList.remove('copied');
    if (navigator.vibrate) try { navigator.vibrate(16); } catch (e) {}
    resetWheels();
    adminSwitchTokenTab('active');
    window.renderAdminTokenList();
  };

  window.adminCopyToken = function () {
    if (!lastGeneratedCode) return;
    var copyBtn = document.getElementById('admin-token-copy-btn');
    function marked() {
      copyBtn.classList.add('copied');
      setTimeout(function () { copyBtn.classList.remove('copied'); }, 1200);
    }
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(lastGeneratedCode).then(marked).catch(marked);
    } else {
      var ta = document.createElement('textarea');
      ta.value = lastGeneratedCode;
      document.body.appendChild(ta);
      ta.select();
      try { document.execCommand('copy'); } catch (e) {}
      document.body.removeChild(ta);
      marked();
    }
  };

  window.adminDeleteToken = function (code) {
    var itemEl = document.querySelector('.admin-token-item[data-code="' + code + '"]');
    delete window.PenaltyTokens[code];
    saveTokens();
    if (itemEl) {
      itemEl.classList.add('tk-leaving');
      setTimeout(function () { window.renderAdminTokenList(); }, 300);
    } else {
      window.renderAdminTokenList();
    }
  };

  window.adminSwitchTokenTab = function (tab) {
    currentTab = tab;
    var tabs = document.querySelectorAll('#tk-tabs .tk-tab');
    tabs.forEach(function (b) { b.classList.toggle('on', b.getAttribute('data-tab') === tab); });
    var slider = document.getElementById('tk-tab-slider');
    if (slider) slider.classList.toggle('right', tab === 'expired');
    var panelActive = document.getElementById('tk-panel-active');
    var panelExpired = document.getElementById('tk-panel-expired');
    if (panelActive) panelActive.classList.toggle('on', tab === 'active');
    if (panelExpired) panelExpired.classList.toggle('on', tab === 'expired');
  };

  function itemHtml(code, t, now) {
    var status, label, timeText;
    if (now >= t.expiresAt) {
      status = 'st-expired'; label = 'Đã hết hạn';
      timeText = t.used ? ('Đã dùng lúc ' + new Date(t.usedAt).toLocaleTimeString()) : ('Không ai dùng - hết hạn lúc ' + new Date(t.expiresAt).toLocaleTimeString());
    } else if (t.used) {
      status = 'st-active'; label = 'Đang được dùng';
      timeText = 'Còn lại ' + fmtRemain(t.expiresAt - now);
    } else {
      status = 'st-unused'; label = 'Chưa dùng';
      timeText = 'Hết hạn sau ' + fmtRemain(t.expiresAt - now);
    }
    return '<div class="admin-token-item" data-code="' + code + '">' +
      '<div class="admin-token-item-code">' + code + '</div>' +
      '<div class="admin-token-item-mid">' +
        '<div class="admin-token-item-status ' + status + '">' + label + '</div>' +
        '<div class="admin-token-item-time">' + timeText + '</div>' +
      '</div>' +
      '<div class="admin-token-item-del" onclick="adminDeleteToken(\'' + code + '\')"><i class="fa-solid fa-xmark"></i></div>' +
    '</div>';
  }

  window.renderAdminTokenList = function () {
    var panelActive = document.getElementById('tk-panel-active');
    var panelExpired = document.getElementById('tk-panel-expired');
    var countBadge = document.getElementById('admin-token-active-count');
    if (!panelActive && !panelExpired) return;
    var codes = Object.keys(window.PenaltyTokens);
    codes.sort(function (a, b) { return window.PenaltyTokens[b].createdAt - window.PenaltyTokens[a].createdAt; });
    var now = Date.now();
    var activeCodes = [], expiredCodes = [];
    codes.forEach(function (code) {
      var t = window.PenaltyTokens[code];
      if (now >= t.expiresAt) expiredCodes.push(code); else activeCodes.push(code);
    });
    if (countBadge) countBadge.textContent = String(activeCodes.length);
    if (panelActive) {
      panelActive.innerHTML = activeCodes.length
        ? activeCodes.map(function (c) { return itemHtml(c, window.PenaltyTokens[c], now); }).join('')
        : '<div class="admin-token-empty">Chưa có token còn hạn</div>';
    }
    if (panelExpired) {
      panelExpired.innerHTML = expiredCodes.length
        ? expiredCodes.map(function (c) { return itemHtml(c, window.PenaltyTokens[c], now); }).join('')
        : '<div class="admin-token-empty">Chưa có token nào hết hạn</div>';
    }
    knownActiveCodes = {}; activeCodes.forEach(function (c) { knownActiveCodes[c] = 1; });
    knownExpiredCodes = {}; expiredCodes.forEach(function (c) { knownExpiredCodes[c] = 1; });
  };

  function fmtRemain(ms) {
    if (typeof window.penaltyFmtRemain === 'function') return window.penaltyFmtRemain(ms);
    if (ms < 0) ms = 0;
    var totalSec = Math.floor(ms / 1000);
    var d = Math.floor(totalSec / 86400), h = Math.floor((totalSec % 86400) / 3600), m = Math.floor((totalSec % 3600) / 60), s = totalSec % 60;
    function p2(n) { return (n < 10 ? '0' : '') + n; }
    return (d > 0 ? (d + 'ng ') : '') + (h > 0 ? (p2(h) + ':') : '') + p2(m) + ':' + p2(s);
  }

  /* Chi cap nhat text dem nguoc + trang thai TAI CHO cua tung dong token dang
     hien, khong dung lai toan bo innerHTML danh sach - truoc day moi giay deu
     goi lai renderAdminTokenList() (ve lai TOAN BO danh sach tu dau) du khong
     co gi thay doi, lam ca danh sach bi "nhap nhay" moi giay do DOM bi huy va
     tao lai lien tuc. Gio chi ve lai toan bo khi tap token active/het han
     THUC SU thay doi (them/xoa/het han/duoc dung se lam ho ten khac di, luc
     do sameSet ben duoi la false); con lai chi doi text dem nguoc. */
  function updateItemTimes(panel, codes, now) {
    if (!panel) return;
    codes.forEach(function (code) {
      var t = window.PenaltyTokens[code];
      if (!t) return;
      var itemEl = panel.querySelector('.admin-token-item[data-code="' + code + '"]');
      if (!itemEl) return;
      var status, label, timeText;
      if (now >= t.expiresAt) {
        status = 'st-expired'; label = 'Đã hết hạn';
        timeText = t.used ? ('Đã dùng lúc ' + new Date(t.usedAt).toLocaleTimeString()) : ('Không ai dùng - hết hạn lúc ' + new Date(t.expiresAt).toLocaleTimeString());
      } else if (t.used) {
        status = 'st-active'; label = 'Đang được dùng';
        timeText = 'Còn lại ' + fmtRemain(t.expiresAt - now);
      } else {
        status = 'st-unused'; label = 'Chưa dùng';
        timeText = 'Hết hạn sau ' + fmtRemain(t.expiresAt - now);
      }
      var statusEl = itemEl.querySelector('.admin-token-item-status');
      var timeEl = itemEl.querySelector('.admin-token-item-time');
      if (statusEl) {
        statusEl.className = 'admin-token-item-status ' + status;
        statusEl.textContent = label;
      }
      if (timeEl) timeEl.textContent = timeText;
    });
  }

  window.renderAdminTokenList();
  setInterval(function () {
    var scr = document.getElementById('admin-token-screen');
    var open = scr && scr.classList.contains('tks-open');
    /* Neu man hinh dang mo thi cap nhat de dem nguoc + tu chuyen token het
       han sang muc "het han" theo thoi gian thuc; neu dang dong van cap nhat
       so luong badge "con hạn" tren dong dieu huong ngoai dashboard. */
    if (open) {
      var codes = Object.keys(window.PenaltyTokens);
      var now = Date.now();
      var activeCodes = [], expiredCodes = [];
      codes.forEach(function (code) {
        var t = window.PenaltyTokens[code];
        if (now >= t.expiresAt) expiredCodes.push(code); else activeCodes.push(code);
      });
      var sameSet = activeCodes.length === Object.keys(knownActiveCodes).length &&
        expiredCodes.length === Object.keys(knownExpiredCodes).length &&
        activeCodes.every(function (c) { return knownActiveCodes[c]; }) &&
        expiredCodes.every(function (c) { return knownExpiredCodes[c]; });
      if (!sameSet) {
        window.renderAdminTokenList();
      } else {
        var countBadge = document.getElementById('admin-token-active-count');
        if (countBadge) countBadge.textContent = String(activeCodes.length);
        updateItemTimes(document.getElementById('tk-panel-active'), activeCodes, now);
        updateItemTimes(document.getElementById('tk-panel-expired'), expiredCodes, now);
      }
    } else {
      var codes2 = Object.keys(window.PenaltyTokens);
      var now2 = Date.now();
      var countBadge2 = document.getElementById('admin-token-active-count');
      if (countBadge2) {
        var n = 0;
        codes2.forEach(function (c) { if (now2 < window.PenaltyTokens[c].expiresAt) n++; });
        countBadge2.textContent = String(n);
      }
    }
  }, 1000);
})();
"""


SERVER_CSS = r"""
.ls-quick-btn {border:0;padding:0;-webkit-tap-highlight-color:transparent;touch-action:manipulation;}

/* Notification history belongs to the unlocked notification center only. */
body:not(.unlocked) #ls-notif-list {display:none!important;}
body:not(.unlocked) .ls-notif-clearall {display:none!important;}
body:not(.unlocked) #lock-screen-ui {touch-action:none;}
#home-indicator-hitbox {touch-action:none;}


/* Keep scrollable content between the live island and the system home bar. */
#app-admin { --admin-top:64px; --admin-bottom:42px; }
#app-admin .admin-dashboard,#app-admin .admin-boot,#app-admin #admin-token-screen {top:var(--admin-top);bottom:var(--admin-bottom);}
#app-admin .admin-header,#app-admin .tks-header {padding:14px 16px;}
#app-admin .admin-dashboard {padding-bottom:20px;overscroll-behavior:contain;}
#app-admin .tks-body {padding-bottom:20px;}
.sr-only {position:absolute!important;width:1px;height:1px;padding:0;overflow:hidden;clip-path:inset(50%);white-space:nowrap;}
#admin-server-card {padding:13px 14px;}
#admin-server-card .server-orb {width:34px;height:34px;font-size:18px;}
#admin-server-card .admin-card-title {font-size:14px;}
.ls-notif-list {flex:1 1 0;min-height:0;max-height:none;margin-bottom:125px;overscroll-behavior-y:contain;touch-action:pan-y;overflow-anchor:none;}
.ls-notif-row {flex:0 0 auto;min-height:0;} /* min-height:0: lop do xoa cao dung bang the kinh + hang co the thu gon khi xoa */
.ls-date,.ls-time {flex-shrink:0;}
#dynamic-island.state-maintenance.maintenance-closing {width:110px;height:32px;border-radius:18px;box-shadow:0 8px 25px #0007;}
.state-maintenance.maintenance-closing #content-maintenance {animation:maintenanceDismiss .26s ease-in forwards;}
@keyframes maintenanceDismiss {to {opacity:0;transform:translateY(-8px) scale(.75);filter:blur(5px);}}
.penalty-loading .pl-title {color:#e6ffed;letter-spacing:4px;font-size:20px;}
.pl-session-mark {width:76px;height:76px;position:relative;display:grid;place-items:center;border-radius:50%;background:#2ad97512;box-shadow:0 0 36px #29de6e22;}
.pl-session-ring {position:absolute;inset:0;border:2px solid #62ff9625;border-top-color:#8ef29c;border-radius:50%;animation:maintenanceSpin 1.1s linear infinite;}
.pl-session-mark svg {width:44px;fill:none;stroke:#a3ffb5;stroke-width:3;stroke-linecap:round;stroke-linejoin:round;opacity:0;transform:scale(.5);transition:opacity .3s,transform .45s var(--ios-spring-snappy);}
.pl-ready .pl-session-mark svg {opacity:1;transform:scale(1);}
.pl-ready .pl-session-ring {animation:none;border-color:#8ef29c;transition:border-color .3s;}
.pl-remaining {color:#89af94;font-size:12px;font-variant-numeric:tabular-nums;}
.pl-progress {width:180px;height:4px;border-radius:4px;background:#ffffff12;overflow:hidden;}
.pl-progress i {display:block;width:45%;height:100%;background:linear-gradient(90deg,transparent,#8ef29c);animation:maintenanceSweep 1.5s ease-in-out infinite;}
.pl-ready .pl-progress i {animation:none;width:100%;background:#8ef29c;transition:width .4s;}
.pl-session-mark {display:none;}
.pl-progress {display:none;}
@media(prefers-reduced-motion:reduce){.pl-session-ring,.pl-progress i,.state-maintenance.maintenance-closing #content-maintenance {animation:none!important;} .pl-session-mark svg {transition:none;}}

#admin-server-card {transition:background .5s,box-shadow .5s,border-color .5s;}
#admin-server-card.server-closed {border-color:#ffba5260;background:linear-gradient(125deg,#281d11,#101410);box-shadow:0 8px 30px #ffb34712;}
#admin-server-card.server-closed .server-orb {color:#ffc46c;background:#ffb34718;}
#admin-server-switch {border:0;flex-shrink:0;padding:0;cursor:pointer;}
#admin-server-switch:disabled {opacity:.45;cursor:wait;}
#admin-server-switch:focus-visible {outline:2px solid #fff;outline-offset:4px;}
#admin-server-status {font-size:11px;color:#80d9a9;}
.server-closed #admin-server-status {color:#ffc46c;}
#admin-server-action {font-size:10px;color:#90a99a;}
#dynamic-island.state-maintenance {width:310px;max-width:92%;height:100px;border-radius:32px;box-shadow:0 12px 36px #ffae322b,inset 0 0 0 1px #ffc36b55;background:linear-gradient(130deg,#2a2013,#090909 65%);animation:maintenanceGlow 2.6s ease-in-out infinite;}
#content-maintenance {display:none;position:absolute;inset:0;align-items:center;gap:14px;padding:18px;box-sizing:border-box;}
.state-maintenance #content-maintenance {display:flex;animation:maintenanceReveal .6s var(--ios-spring-snappy) .1s both;}
.maintenance-ring {position:relative;width:44px;height:44px;flex-shrink:0;display:grid;place-items:center;color:#ffd18a;border-radius:50%;background:radial-gradient(circle,#ffb34722,transparent 70%);}
.maintenance-ring::before {content:'';position:absolute;inset:-4px;border:2px solid #ffbd4525;border-top-color:#ffc568;border-radius:50%;animation:maintenanceSpin 2.8s linear infinite;}
.maintenance-gear-back {position:absolute;font-size:32px;color:#ffb34740;animation:maintenanceSpin 6s linear infinite;}
.maintenance-wrench {position:relative;font-size:19px;animation:maintenanceRock 2.2s ease-in-out infinite;filter:drop-shadow(0 0 5px #ffcd8090);}
.maintenance-title {font-size:14px;font-weight:800;letter-spacing:.8px;white-space:nowrap;background:linear-gradient(90deg,#ffd18a 0%,#fff3d6 50%,#ffd18a 100%);background-size:220% 100%;-webkit-background-clip:text;background-clip:text;color:transparent;animation:maintenanceShimmer 2.6s ease-in-out infinite;}
.maintenance-title::after {content:'';display:inline-block;width:4px;height:4px;margin-left:6px;margin-bottom:1px;border-radius:50%;background:#ffd18a;box-shadow:10px 0 0 -1px #ffd18a,20px 0 0 -2px #ffd18a;animation:maintenanceDots 1.3s steps(1) infinite;}
.maintenance-track {height:5px;border-radius:3px;margin-top:10px;overflow:hidden;background:repeating-linear-gradient(135deg,#ffba4530 0 9px,transparent 9px 18px);background-size:26px 100%;animation:maintenanceStripe 0.85s linear infinite;}
@keyframes maintenanceReveal {from {opacity:0;transform:translateY(-9px) scale(.88);filter:blur(5px);}to {opacity:1;transform:none;filter:blur(0);}}
@keyframes maintenanceGlow {0%,100% {box-shadow:0 12px 36px #ffae322b,inset 0 0 0 1px #ffc36b55;}50% {box-shadow:0 12px 42px #ffae324a,inset 0 0 0 1px #ffd28a95,0 0 20px #ffb34750;}}
@keyframes maintenanceShimmer {0% {background-position:200% 0;}100% {background-position:-20% 0;}}
@keyframes maintenanceDots {0%,100% {opacity:0;box-shadow:10px 0 0 -1px transparent,20px 0 0 -2px transparent;}33% {opacity:1;box-shadow:10px 0 0 -1px transparent,20px 0 0 -2px transparent;}66% {box-shadow:10px 0 0 -1px #ffd18a,20px 0 0 -2px transparent;}99% {box-shadow:10px 0 0 -1px #ffd18a,20px 0 0 -2px #ffd18a;}}
@keyframes maintenanceSpin {to {transform:rotate(360deg);}}
@keyframes maintenanceRock {0%,100% {transform:rotate(-12deg);}50% {transform:rotate(15deg);}}
@keyframes maintenanceSweep {from {transform:translateX(-100%);}to {transform:translateX(350%);}}
@keyframes maintenanceStripe {from {background-position:0 0;}to {background-position:-26px 0;}}
@media(prefers-reduced-motion:reduce){.state-maintenance #content-maintenance,.maintenance-ring::before,.maintenance-gear-back,.maintenance-wrench,.maintenance-title,.maintenance-title::after,.maintenance-track,#dynamic-island.state-maintenance {animation:none!important;}#dynamic-island.state-maintenance {transition-duration:.01s;}}
"""
SERVER_JS = r"""
let unlockBusy = false;
let unlockGeneration = 0;
let serverOpen = null;
let adminServerToken = '';
let serverToggleBusy = false;
const maintenanceContent = document.createElement('div');
maintenanceContent.id = 'content-maintenance';
maintenanceContent.setAttribute('role', 'status');
maintenanceContent.setAttribute('aria-live', 'polite');
maintenanceContent.innerHTML = '<div class="maintenance-ring"><i class="fa-solid fa-gear maintenance-gear-back"></i><i class="fa-solid fa-screwdriver-wrench maintenance-wrench"></i></div><div><div class="maintenance-title">ĐANG BẢO TRÌ</div><div class="maintenance-track"></div></div>';
island.appendChild(maintenanceContent);
ISLAND_STATE_WIDTH.maintenance = 310;
async function serverRequest(path, body) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 6000);
  try {
    const response = await fetch(path, {method:body ? 'POST' : 'GET', cache:'no-store', signal:controller.signal,
      headers:body ? {'Content-Type':'application/json','X-Admin-Token':adminServerToken} : {},
      body:body ? JSON.stringify(body) : undefined});
    const data = await response.json();
    if (!response.ok && response.status !== 503) throw new Error(data.error || 'request_failed');
    return data;
  } finally { clearTimeout(timer); }
}
let maintenanceDismissTimer;
function dismissMaintenance() {
  clearTimeout(autoCloseTimeout);
  if (!island.classList.contains('state-maintenance')) return;
  island.classList.add('maintenance-closing', 'island-animating');
  island.style.setProperty('--drag-y', '0px');
  island.style.setProperty('--drag-scale-y', '1');
  island.style.setProperty('--drag-scale-x', '1');
  toggleReflow('default');
  clearTimeout(maintenanceDismissTimer);
  maintenanceDismissTimer = setTimeout(() => {
    if (island.classList.contains('maintenance-closing')) resetIsland();
  }, 440);
}
function showMaintenance() {
  clearTimeout(maintenanceDismissTimer);
  addLockNotification('Hệ thống', 'ĐANG BẢO TRÌ');
  unlockBusy = false;
  clearTimeout(autoCloseTimeout); clearTimeout(resetTextTimeout);
  hideAllContents();
  island.className = 'state-maintenance island-animating no-swipe';
  island.style.boxShadow = '';
  toggleReflow('maintenance');
  pcTitle.innerText = 'Nhập mật mã';
  if (navigator.vibrate) navigator.vibrate([30,45,30]);
  autoCloseTimeout = setTimeout(dismissMaintenance, 5500);
}
function applyServerState(state) {
  serverOpen = state.open === true;
  const card = document.getElementById('admin-server-card');
  const sw = document.getElementById('admin-server-switch');
  card.classList.toggle('server-closed', !serverOpen);
  card.classList.toggle('admin-card-active', serverOpen);
  sw.classList.toggle('on', serverOpen);
  sw.setAttribute('aria-checked', String(serverOpen));
  sw.disabled = serverToggleBusy;
  document.getElementById('admin-server-status').textContent = serverOpen ? '● ĐANG HOẠT ĐỘNG' : '● ĐANG BẢO TRÌ';
  document.getElementById('admin-server-action').textContent = serverOpen ? 'Chạm để đóng' : 'Chạm để mở';
  if (!serverOpen && !adminModeUnlocked && document.body.classList.contains('unlocked')) {
    lockToLockScreen(); showMaintenance();
  }
  if (serverOpen && island.classList.contains('state-maintenance')) resetIsland();
}
async function checkPasscode() {
  if (unlockBusy) return;
  const code = passcode.join('');
  if (code !== '000000' && code !== '081120') { completePasscode(); return; }
  unlockBusy = true;
  const attempt = ++unlockGeneration;
  pcTitle.innerText = 'Đang kiểm tra…';
  try {
    const result = await serverRequest('/api/unlock', {passcode:code});
    if (attempt !== unlockGeneration) return;
    applyServerState(result);
    if (!result.allowed) { passcode = []; updateDots(); showMaintenance(); return; }
    adminServerToken = result.admin_token || '';
    completePasscode();
  } catch (e) {
    if (attempt !== unlockGeneration) return;
    passcode = []; updateDots(); unlockBusy = false;
    pcTitle.innerText = 'Mất kết nối. Vui lòng thử lại';
    showNotification('Không thể kết nối server. Vui lòng thử lại.', 'error');
  }
}
async function toggleUserServer() {
  if (!adminModeUnlocked || serverToggleBusy || serverOpen === null) return;
  serverToggleBusy = true;
  document.getElementById('admin-server-switch').disabled = true;
  document.getElementById('admin-server-status').textContent = 'Đang cập nhật…';
  try {
    const state = await serverRequest('/api/server-state', {open:!serverOpen});
    applyServerState(state);
    const sw = document.getElementById('admin-server-switch');
    sw.classList.remove('admin-switch-anim'); void sw.offsetWidth; sw.classList.add('admin-switch-anim');
    if (state.open) showNotification('Server đã mở. Người dùng có thể đăng nhập.', 'success');
    else showMaintenance();
  } catch (e) {
    document.getElementById('admin-server-status').textContent = 'Không lưu được. Hãy thử lại / đăng nhập lại admin.';
  } finally {
    serverToggleBusy = false;
    document.getElementById('admin-server-switch').disabled = false;
  }
}
let statusPollBusy = false;
async function refreshServerState() {
  if (statusPollBusy || serverToggleBusy) return;
  statusPollBusy = true;
  try { const state = await serverRequest('/api/server-state'); if (!serverToggleBusy) applyServerState(state); }
  catch (e) { /* Unlock always performs its own check and fails closed. */ }
  finally { statusPollBusy = false; }
}

(function maintainAdminInsets() {
  const admin = document.getElementById('app-admin');
  function sync() {
    const top = Math.max(64, island.offsetTop + island.offsetHeight + 12,
      statusBar.offsetTop + statusBar.offsetHeight + 12);
    admin.style.setProperty('--admin-top', top + 'px');
    admin.style.setProperty('--admin-bottom', Math.max(42, homeHitbox.offsetHeight + 8) + 'px');
  }
  if (typeof ResizeObserver !== 'undefined') {
    const observer = new ResizeObserver(sync);
    observer.observe(island); observer.observe(statusBar); observer.observe(homeHitbox);
  }
  window.addEventListener('resize', sync); sync();
})();

refreshServerState();
setInterval(() => { if (!document.hidden) refreshServerState(); }, 2000);
document.addEventListener('visibilitychange', () => { if (!document.hidden) refreshServerState(); });
"""

MAGICAI_CSS = r"""
.magicai-app-box {overflow:hidden;background:#0b1525;box-shadow:0 5px 18px #0006;}.magicai-app-box svg {width:100%;height:100%;}
#app-tool {--magic-top:64px;--magic-bottom:48px;--ma-green:#a0ffd9;background:#090f18;color:#e8f0fc;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif;}
.ma-shell {position:absolute;top:var(--magic-top);bottom:var(--magic-bottom);left:0;right:0;display:flex;flex-direction:column;min-height:0;overflow:hidden;background:radial-gradient(ellipse at 100% 0,#28345145,transparent 52%),#090f18;}
.ma-header {display:flex;align-items:center;justify-content:space-between;flex:none;padding:16px 21px;border-bottom:1px solid #bde4ff0d;background:#0c1420d9;}
.ma-brand {font-size:19px;font-weight:850;letter-spacing:1.8px;line-height:1.2;}.ma-brand em {font-style:normal;color:var(--ma-green);}
.ma-sub {display:flex;align-items:center;gap:6px;margin-top:6px;font-size:9px;font-weight:600;letter-spacing:1.3px;color:#8398af;}.ma-dot{width:5px;height:5px;background:var(--ma-green);border-radius:50%;box-shadow:0 0 10px #9cffcd88;}
.ma-icon-btn {width:38px;height:38px;border:1px solid #c1dcff20;border-radius:13px;background:#c9dbff09;color:#aabbce;display:grid;place-items:center;cursor:pointer;transition:transform .22s,background .22s;}.ma-icon-btn:active{transform:scale(.88);background:#c9dbff20;}
.ma-chat {flex:1;min-height:0;overflow-y:auto;padding:25px 18px 16px;overscroll-behavior:contain;scroll-behavior:smooth;-webkit-overflow-scrolling:touch;}.ma-chat::-webkit-scrollbar{width:3px}.ma-chat::-webkit-scrollbar-thumb{background:#4d657d55;border-radius:9px;}
.ma-intro {text-align:center;max-width:300px;margin:0 auto 28px;animation:maReveal .6s ease both;}.ma-core {width:86px;height:86px;margin:10px auto 21px;display:grid;place-items:center;position:relative;border-radius:28px;background:linear-gradient(135deg,#254138,#111c2f);box-shadow:0 0 46px #83d7ba18,inset 0 0 0 1px #a5ffe72a;}
.ma-core::before{content:'';position:absolute;inset:-8px;border-radius:34px;border:1px solid #b8ffe514;animation:maBreathe 3.5s ease-in-out infinite;}.ma-core svg{width:47px;height:47px;color:#abffde;filter:drop-shadow(0 0 9px #a9ffdf44);}
.ma-kicker {color:#97bea9;font-size:9px;letter-spacing:2px;margin-bottom:10px;font-weight:700;}.ma-intro h2 {font-size:25px;font-weight:750;line-height:1.25;margin:0 0 11px;letter-spacing:-.6px;}.ma-intro p{font-size:12px;color:#899bb1;line-height:1.65;margin:0 auto;max-width:260px;}
.ma-chip {display:inline-flex;align-items:center;gap:7px;border:1px solid #adcafa1c;background:#adcafa07;border-radius:99px;padding:7px 10px;margin-top:18px;color:#afc3d4;font-size:9px;letter-spacing:.3px;}
.ma-message {margin-top:18px;animation:maReveal .35s ease both;}.ma-message-user{display:flex;justify-content:flex-end;}.ma-user-text {max-width:90%;padding:12px 15px;border-radius:17px 17px 4px 17px;background:linear-gradient(135deg,#bdded0,#82c2b3);color:#102723;font-size:13px;font-weight:650;box-shadow:0 6px 20px #0002;}
.ma-speaker{display:flex;align-items:center;gap:7px;color:#adffd9;font-size:10px;letter-spacing:.8px;font-weight:750;margin:0 0 9px 2px;}.ma-speaker b{width:19px;height:19px;display:grid;place-items:center;border-radius:6px;border:1px solid #96ebc840;font-size:11px;}
.ma-bubble{border:1px solid #aac5e519;background:linear-gradient(145deg,#16202e,#0e1723);padding:14px;border-radius:4px 17px 17px 17px;box-shadow:0 7px 22px #0002;}.ma-bubble p{margin:0;line-height:1.6;font-size:12px;overflow-wrap:anywhere;}.ma-thinking{display:inline-flex;gap:4px;margin-left:8px;vertical-align:middle}.ma-thinking i{width:4px;height:4px;background:#a1dfc5;border-radius:50%;animation:maDot 1s ease-in-out infinite;}.ma-thinking i:nth-child(2){animation-delay:.15s}.ma-thinking i:nth-child(3){animation-delay:.3s}
.ma-connection{font-weight:750;color:#b1ffda}.ma-failed{color:#ffb9a6;font-weight:750}.ma-session{font-family:ui-monospace,monospace;font-size:10px;line-height:1.6;overflow-wrap:anywhere;color:#d2e0f4;background:#04091080;padding:10px;border-radius:9px;margin-top:9px;border:1px solid #c1daff12;}
.ma-plan-note{color:#93a7be;font-size:10px;line-height:1.55;margin:11px 0;}.ma-grid {display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:7px;}
.ma-shot{min-width:0;border:1px solid #8daed922;border-radius:11px;padding:9px 3px 8px;text-align:center;background:#0a131f;animation:maReveal .4s ease backwards;transition:background .2s,border-color .2s,opacity .2s;}.ma-shot small{display:block;color:#8b9fb7;font-size:8px;letter-spacing:1px;}.ma-arrow{display:block;font-size:23px;line-height:1.3;color:#a4f4d1;animation:maArrowReveal .4s cubic-bezier(.34,1.56,.64,1);}@keyframes maArrowReveal{from{opacity:0;transform:scale(.4) rotate(-20deg)}to{opacity:1;transform:scale(1) rotate(0)}}.ma-direction{font-size:10px;font-weight:750;letter-spacing:.4px;}.ma-result{display:block;margin-top:4px;font-size:8px;color:#70889e;}.ma-shot.current{border-color:#a2fbd58c;box-shadow:inset 0 0 14px #8afac50c;}.ma-shot.done{background:#183126;border-color:#91ffd044;}.ma-shot.missed{background:#301c22;border-color:#ff987444;}.ma-plan.stale .ma-grid{opacity:.43;}.ma-plan.stale .ma-plan-note{color:#d5ad81;}
.ma-shot.ma-locked{opacity:.96;}.ma-lock-icon{display:block;font-size:17px;color:#8daed9;margin:5px 0 6px;transition:transform .3s cubic-bezier(.34,1.56,.64,1),opacity .3s;}
.ma-unlock-btn{display:inline-block;padding:4px 7px;border-radius:8px;border:1px solid #ffd65a55;background:#ffd65a14;color:#ffd65a;font-size:9px;font-weight:800;letter-spacing:.2px;cursor:pointer;-webkit-tap-highlight-color:transparent;transition:transform .15s ease,background .15s ease;}
.ma-unlock-btn:active{transform:scale(.88);background:#ffd65a26;}
.ma-unlock-btn.ma-deny{animation:maDenyShake .4s ease;}
@keyframes maDenyShake{0%,100%{transform:translateX(0)}20%{transform:translateX(-4px)}40%{transform:translateX(4px)}60%{transform:translateX(-3px)}80%{transform:translateX(2px)}}
.ma-shot.ma-unlocking .ma-lock-icon{animation:maLockPop .42s cubic-bezier(.34,1.56,.64,1) forwards;}
@keyframes maLockPop{0%{transform:scale(1) rotate(0);opacity:1}50%{transform:scale(1.4) rotate(15deg);opacity:1}100%{transform:scale(0) rotate(-30deg);opacity:0}}
.ma-shot.ma-unlocking .ma-unlock-btn{animation:maBtnFade .3s ease forwards;}
@keyframes maBtnFade{to{opacity:0;transform:scale(.7)}}
.ma-composer {flex:none;padding:12px 18px 8px;background:linear-gradient(180deg,#090f1800,#0c141ff2 25%);border-top:1px solid #adcafa10;}.ma-label{display:flex;justify-content:space-between;color:#698098;font-size:8px;letter-spacing:1.2px;margin:0 1px 9px;font-weight:700;}.ma-prompt {width:100%;padding:13px;border-radius:16px;background:linear-gradient(125deg,#1c2d35,#192334);border:1px solid #b0fdd435;color:#edf8f4;display:flex;align-items:center;gap:10px;text-align:left;cursor:pointer;transition:transform .18s,border-color .2s,box-shadow .2s;box-shadow:0 4px 22px #0003;}.ma-prompt:active{transform:scale(.97)}.ma-prompt:disabled{opacity:.65;cursor:wait}.ma-prompt svg{width:23px;height:23px;color:#a6fbd5;flex:none}.ma-prompt span{flex:1;font-size:12px;font-weight:700;}.ma-send {width:27px;height:27px;display:grid;place-items:center;border-radius:9px;background:#a3f6cd;color:#12271f;font-size:18px;}.ma-foot {text-align:center;color:#5f748b;font-size:9px;line-height:1.5;margin:9px 0 0;}
.ma-tokens{display:flex;align-items:center;gap:7px;padding:6px 13px 6px 7px;border-radius:999px;border:1px solid #ffd76a3d;background:linear-gradient(135deg,#2a220f,#171208);box-shadow:0 4px 14px #0004,inset 0 1px 0 #ffffff14;transition:transform .18s ease;}
.ma-token-icon{width:19px;height:19px;flex:none;filter:drop-shadow(0 1px 2px #0006);}
.ma-tokens span{font-size:13px;font-weight:800;color:#ffe9ad;letter-spacing:.3px;font-variant-numeric:tabular-nums;white-space:nowrap;}
.ma-digit-wrap{display:inline-block;position:relative;overflow:hidden;height:1em;width:0.62em;vertical-align:bottom;}
.ma-digit-old,.ma-digit-new{position:absolute;left:0;right:0;top:0;text-align:center;}
.ma-digit-old{animation:maDigitOut .42s cubic-bezier(.3,.7,.35,1) forwards;}
.ma-digit-new{transform:translateY(-100%);opacity:0;animation:maDigitIn .42s cubic-bezier(.3,.7,.35,1) forwards;}
@keyframes maDigitOut{to{transform:translateY(100%);opacity:0;}}
@keyframes maDigitIn{to{transform:translateY(0);opacity:1;}}
.ma-fade-swap{display:inline-block;}
.ma-tokens.ma-tok-low span{color:#ff9d7a;}
.ma-tokens.ma-tok-burn{animation:maTokBurn .38s ease;}
@keyframes maTokBurn{0%{transform:scale(1)}35%{transform:scale(1.14);}100%{transform:scale(1)}}
.ma-analyzing{padding:15px 14px 13px;position:relative;transition:box-shadow .3s ease;}
.ma-analyzing:not(.ma-done):not(.ma-fail){animation:maAnalyzingGlow 2.4s ease-in-out infinite;}
@keyframes maAnalyzingGlow{0%,100%{box-shadow:0 7px 22px #0002,0 0 0 rgba(164,244,209,0);}50%{box-shadow:0 7px 22px #0002,0 0 16px rgba(164,244,209,.32);}}
.ma-analyzing-head{display:flex;align-items:center;gap:13px;}
.ma-ring{position:relative;width:48px;height:48px;flex:none;}
.ma-ring::before{content:'';position:absolute;inset:-5px;border-radius:50%;background:conic-gradient(from 0deg,rgba(164,244,209,0) 0%,rgba(164,244,209,.55) 30%,rgba(99,199,255,.55) 55%,rgba(164,244,209,0) 78%);opacity:0;pointer-events:none;}
.ma-analyzing:not(.ma-done):not(.ma-fail) .ma-ring::before{opacity:1;animation:maRingSpin 2.1s linear infinite;}
@keyframes maRingSpin{to{transform:rotate(360deg);}}
.ma-ring svg{position:relative;width:100%;height:100%;transform:rotate(-90deg);}
.ma-ring .ma-ring-bg{fill:none;stroke:#22344022;stroke-width:3;}
.ma-ring .ma-ring-fg{fill:none;stroke:url(#ma-ring-grad);stroke-width:3;stroke-linecap:round;transition:stroke-dashoffset .32s linear;}
.ma-ring-core{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;font-size:10.5px;font-weight:700;letter-spacing:-.4px;white-space:nowrap;color:#a4f4d1;font-variant-numeric:tabular-nums;transition:transform .18s ease;}
.ma-ring-core.pulse{animation:maPctPulse .32s ease;}
@keyframes maPctPulse{0%{transform:scale(1)}45%{transform:scale(1.18)}100%{transform:scale(1)}}
.ma-analyzing-text{flex:1;min-width:0;}
.ma-analyzing-title{font-size:12.5px;font-weight:800;color:#eafff2;letter-spacing:.2px;}
.ma-analyzing-phase{margin-top:3px;font-size:11px;color:#8fb0c6;min-height:14px;transition:opacity .25s ease;}
.ma-analyzing-phase.swap{animation:maPhaseSwap .35s ease;}
@keyframes maPhaseSwap{0%{opacity:0;transform:translateY(3px)}100%{opacity:1;transform:none}}
.ma-analyzing-meta{display:flex;justify-content:space-between;margin-top:12px;padding-top:11px;border-top:1px dashed #8daed922;font-size:10.5px;color:#7c92a8;}
.ma-analyzing-meta b{color:#ffcf3f;font-variant-numeric:tabular-nums;}
.ma-analyzing.ma-done{border-color:#91ffd044;}
.ma-analyzing.ma-done .ma-analyzing-title{color:#b1ffda;}
.ma-analyzing.ma-fail{border-color:#ff987444;}
.ma-analyzing.ma-fail .ma-analyzing-title{color:#ffb9a6;}
@keyframes maReveal{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:none}}@keyframes maDot{0%,80%,100%{opacity:.3;transform:translateY(0)}40%{opacity:1;transform:translateY(-3px)}}@keyframes maBreathe{50%{transform:scale(1.06);opacity:.4}}
@media(prefers-reduced-motion:reduce){#app-tool *,#app-tool *::before{animation:none!important;transition:none!important;scroll-behavior:auto!important;}}
"""
MAGICAI_BODY = r"""
<div class="simple-app" id="app-tool">
  <div class="ma-shell">
    <header class="ma-header"><div><div class="ma-brand">MAGIC<em>AI</em></div></div>
      <div class="ma-tokens" id="ma-tokens" aria-label="Số dư Token AI Chat">
        <svg class="ma-token-icon" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
          <defs><linearGradient id="ma-token-grad" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="#fff3b0"/><stop offset="55%" stop-color="#ffcf3f"/><stop offset="100%" stop-color="#c9861f"/></linearGradient></defs>
          <circle cx="12" cy="12" r="9.3" fill="url(#ma-token-grad)" stroke="#8a5a12" stroke-width="1.1"/>
          <circle cx="12" cy="12" r="6.4" fill="none" stroke="#8a5a12" stroke-width="1" opacity="0.55"/>
          <text x="12" y="15.5" text-anchor="middle" font-size="9" font-weight="800" fill="#5c3a0c" font-family="Arial, sans-serif">T</text>
        </svg>
        <span id="ma-tokens-value">100</span>
      </div></header>
    <div class="ma-chat" id="ma-chat" role="log" aria-live="polite" aria-relevant="additions"></div>
    <footer class="ma-composer"><div class="ma-label"><span>THAO TÁC NHANH</span><span id="ma-status">SẴN SÀNG</span></div>
      <button type="button" class="ma-prompt" id="ma-predict"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="12" r="9"/><path d="m12 7 4 3-1.5 4.5h-5L8 10Zm0 0V3M8 10l-4-2m5.5 6.5L7 19m7.5-4.5L17 19m-1-9 4-2"/></svg><span>Dự đoán Penalty</span><b class="ma-send">↑</b></button>
    </footer>
  </div>
</div>
"""
MAGICAI_JS = r"""
(function () {
  const app = document.getElementById('app-tool');
  const chat = document.getElementById('ma-chat');
  const button = document.getElementById('ma-predict');
  const status = document.getElementById('ma-status');
  const frame = document.getElementById('penalty-iframe');
  DOCK_APP_META['app-tool'] = {name:'MAGICAI',icon:'fa-solid fa-brain',grad:'linear-gradient(135deg,#719caa,#263c5e)'};
  let epoch=0, busy=false, snapshot=null, receivedAt=0, connectedId=null;
  const requests=new Map();
  const intro='<div class="ma-intro"><div class="ma-core"><svg viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="1.7"><path d="m24 3 18 10v22L24 45 6 35V13Z"/><path d="M14 33V16l10 11 10-11v17" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/></svg></div><div class="ma-kicker">YOUR INTELLIGENT COMPANION</div><h2>Chào bạn.<br>Sẵn sàng kết nối?</h2></div>';
  function role(){return adminModeUnlocked?'admin':'user'}
  let currentRole=role();
  /* ===== TOKEN CHAT AI (rieng theo vai, luu localStorage) =====
     Nguoi dung thuong mac dinh 100 token, may chu Admin mac dinh 1,000,000
     token. Token bi dot 100/giay trong luc AI "Dang Phan Tich". */
  const TOKEN_KEY_PREFIX='magicos_ai_tokens_v1_';
  const TOKEN_DEFAULTS={user:100,admin:1000000};
  const tokensEl=document.getElementById('ma-tokens');
  const tokensValueEl=document.getElementById('ma-tokens-value');
  function tokenKey(){return TOKEN_KEY_PREFIX+role()}
  function getTokens(){
    try{
      const raw=localStorage.getItem(tokenKey());
      if(raw===null){const def=TOKEN_DEFAULTS[role()];localStorage.setItem(tokenKey(),String(def));return def}
      const n=parseInt(raw,10);return Number.isFinite(n)?n:TOKEN_DEFAULTS[role()];
    }catch(e){return TOKEN_DEFAULTS[role()]}
  }
  function setTokens(v){
    v=Math.max(0,Math.round(v));
    try{localStorage.setItem(tokenKey(),String(v));}catch(e){}
    return v;
  }
  /* ===== Hieu ung "cuon so" kieu dong ho co (odometer) =====
     Khi tung ky tu o cung vi tri thay doi, cho ky tu cu truot xuong + mo dan
     va ky tu moi truot vao tu tren xuong, thay vi doi text mot phat nhu cu. */
  function rollText(el, oldText, newText) {
    if (!el) return;
    oldText = oldText == null ? '' : String(oldText);
    newText = String(newText);
    if (oldText === newText) { el.textContent = newText; return; }
    if (oldText.length !== newText.length) {
      // Do dai khac nhau (vd them dau phan cach hang nghin) -> truot mo doi nguyen chuoi
      el.style.transition = 'none'; el.style.transform = 'translateY(0)'; el.style.opacity = '1';
      void el.offsetWidth;
      el.style.transition = 'transform .3s cubic-bezier(.3,.7,.35,1), opacity .3s ease';
      el.style.transform = 'translateY(-7px)'; el.style.opacity = '0';
      setTimeout(function () {
        el.textContent = newText;
        el.style.transition = 'none'; el.style.transform = 'translateY(7px)'; el.style.opacity = '0';
        void el.offsetWidth;
        el.style.transition = 'transform .3s cubic-bezier(.3,.7,.35,1), opacity .3s ease';
        el.style.transform = 'translateY(0)'; el.style.opacity = '1';
      }, 300);
      return;
    }
    el.innerHTML = '';
    for (var i = 0; i < newText.length; i++) {
      var o = oldText[i], n = newText[i];
      if (o === n) { el.appendChild(document.createTextNode(n)); continue; }
      var wrap = document.createElement('span'); wrap.className = 'ma-digit-wrap';
      var oldSpan = document.createElement('span'); oldSpan.className = 'ma-digit-old'; oldSpan.textContent = o;
      var newSpan = document.createElement('span'); newSpan.className = 'ma-digit-new'; newSpan.textContent = n;
      wrap.append(oldSpan, newSpan);
      el.appendChild(wrap);
      (function (wrap, n) {
        setTimeout(function () {
          if (wrap && wrap.parentNode) wrap.parentNode.replaceChild(document.createTextNode(n), wrap);
        }, 440);
      })(wrap, n);
    }
  }
  /* ===== Dem so Token muot (thay cho kieu "nhay" tung ky tu cu) =====
     Luon dem lien tuc tu gia tri dang hien thi toi gia tri moi bang
     requestAnimationFrame + easing, giong hieu ung dem so du trong
     game Penalty, cho cam giac "cuon" lien mach thay vi khung. Neu dang
     dem do (bi tru token lien tiep moi giay) thi huy animation cu va
     tiep tuc muot tu vi tri hien tai, khong bi giat khi cap nhat dồn dập. */
  /* ===== Dem so muot dung chung cho moi loai so (Token header, Da dot, Con lai) =====
     Nhan vao 1 "state" rieng cho tung o so de nhieu o co the dem doc lap voi nhau
     ma khong dam vao animation cua nhau. */
  function animateCounterTo(el, state, toV, dur){
    if(!el)return;
    const fromV = state.shown==null ? toV : state.shown;
    if(state.id){cancelAnimationFrame(state.id);state.id=null}
    if(fromV===toV){
      state.shown=toV;
      el.textContent=toV.toLocaleString('vi-VN');
      return;
    }
    dur = dur || 480;
    const start=performance.now();
    function step(now){
      const t=Math.min((now-start)/dur,1);
      const ease=1-Math.pow(1-t,3);
      const val=Math.round(fromV+(toV-fromV)*ease);
      el.textContent=val.toLocaleString('vi-VN');
      if(t<1){state.id=requestAnimationFrame(step)}
      else{state.shown=toV;el.textContent=toV.toLocaleString('vi-VN');state.id=null}
    }
    state.id=requestAnimationFrame(step);
  }
  let tokenAnimId=null, tokenShownValue=null;
  const tokenAnimState={get shown(){return tokenShownValue},set shown(v){tokenShownValue=v},get id(){return tokenAnimId},set id(v){tokenAnimId=v}};
  function animateTokensTo(toV){
    if(tokensValueEl)animateCounterTo(tokensValueEl,tokenAnimState,toV,550);
  }
  function renderTokens(burn){
    if(!tokensValueEl)return;
    const v=getTokens();
    animateTokensTo(v);
    if(tokensEl){
      tokensEl.classList.toggle('ma-tok-low',v<300);
      if(burn){
        tokensEl.classList.remove('ma-tok-burn');void tokensEl.offsetWidth;tokensEl.classList.add('ma-tok-burn');
      }
    }
  }
  function burnTokens(n){
    const cur=getTokens();const next=setTokens(cur-n);renderTokens(n);return next;
  }
  renderTokens();
  /* Token co the duoc mua them tu app Cua Hang (cung 1 trang, khong qua
     iframe) - lang nghe su kien do de cap nhat SO NGAY, khong doi den luc
     nguoi dung bam "Du doan" moi vo tinh renderTokens() lai moi thay so
     moi. Doi chieu ca vai dang nhap: neu dang mua cho vai khac (hiem, vd
     do doi vai giua chung) thi khong ve nham, chi ve lai khi dung vai. */
  document.addEventListener('magicai-tokens-changed', function () { renderTokens(); });
  Array.prototype.slice.call(document.querySelectorAll('[onclick*="app-tool"]')).forEach(function (el) {
    el.addEventListener('click', function () { renderTokens(); });
  });
  function gameOrigin(){try{return new URL(document.getElementById('app-penalty').dataset.penaltyUrl,location.href).origin}catch(e){return null}}
  /* Truoc day yeu cau activeAppsList.includes('app-penalty') moi cho ket noi:
     danh sach nay chi phan anh app nao dang o "man hinh da nhiem", nen neu
     nguoi dung dang dung MAGICAI (tuc Penalty dang bi che/nen) hoac danh sach
     bi lech vi ly do nao do, eligible() sai NGAY LAP TUC va query() khong
     con gui thu postMessage nao ca - MAGICAI luon bao "Ket Noi That Bai" du
     Penalty van dang chay that su. Bo dieu kien nay: chi con kiem tra may da
     mo khoa va phien choi (thoi han) con hop le; ket qua ket noi that su do
     chinh cau tra loi (hoac timeout) cua iframe Penalty quyet dinh o query(). */
  function eligible(){return document.body.classList.contains('unlocked') && window.isPenaltySessionValid && window.isPenaltySessionValid()}
  function scroll(){requestAnimationFrame(()=>{chat.scrollTop=chat.scrollHeight})}
  function message(text, user=false){
    const row=document.createElement('div');row.className='ma-message'+(user?' ma-message-user':'');
    const body=document.createElement('div');body.className=user?'ma-user-text':'ma-bubble';
    if(!user){const label=document.createElement('div');label.className='ma-speaker';label.innerHTML='<b>M</b> MAGICAI';row.append(label)}
    const p=document.createElement('p');p.textContent=text;body.append(p);row.append(body);chat.append(row);scroll();return body;
  }
  function stale(note){
    connectedId=null;
    chat.querySelectorAll('.ma-plan:not(.stale)').forEach(el=>{el.classList.add('stale');el.querySelector('.ma-plan-note').textContent=note});
    if(!busy)status.textContent='CHƯA KẾT NỐI';
  }
  function reset(){
    epoch++;requests.forEach(r=>{clearTimeout(r.timer);r.resolve(null)});requests.clear();
    busy=false;button.disabled=false;snapshot=null;receivedAt=0;connectedId=null;
    chat.innerHTML=intro;status.textContent='SẴN SÀNG';currentRole=role();renderTokens();
  }
  function valid(data){
    if(!data || data.source!=='magicos-penalty-bridge'||data.type!=='state'||typeof data.active!=='boolean')return false;
    if(!data.active)return true;
    return typeof data.sessionId==='string' && /^PEN-[A-Z0-9-]{8,70}$/.test(data.sessionId) &&
      Number.isInteger(data.step)&&data.step>=0&&data.step<9 && Array.isArray(data.plans)&&data.plans.length===9&&
      data.plans.every(p=>Array.isArray(p)&&p.length===3&&new Set(p).size===3&&p.every(o=>['goal','save','post'].includes(o))) &&
      Array.isArray(data.results)&&data.results.length<=9;
  }
  function updateCards(data){
    chat.querySelectorAll('.ma-plan').forEach(board=>{
      if(board.dataset.session!==data.sessionId)return;
      board.querySelectorAll('.ma-shot').forEach((el,i)=>{
        if(el.classList.contains('ma-locked'))return;
        const result=data.results.find(r=>r.shot===i+1);
        el.classList.toggle('current',data.active&&data.step===i&&!result);
        el.classList.toggle('done',!!result&&result.outcome==='goal');el.classList.toggle('missed',!!result&&result.outcome!=='goal');
        el.querySelector('.ma-result').textContent=result?(result.outcome==='goal'?'Đã ghi bàn ✓':'Không ghi bàn'):(data.step===i?(data.busy?'Đang sút…':'Lượt tiếp theo'):'Hướng ghi bàn');
      });
    });
  }
  window.addEventListener('message',ev=>{
    if(ev.source!==frame.contentWindow||!valid(ev.data))return;
    if(!eligible()){snapshot=null;stale('Phiên chơi đã đóng hoặc token đã hết hạn.');return}
    const data=ev.data;snapshot=data;receivedAt=Date.now();
    if(connectedId && (!data.active||data.sessionId!==connectedId))stale('Phiên đã kết thúc hoặc thay đổi. Nhấn Dự đoán Penalty để kết nối lại.');
    updateCards(data);
    const pending=requests.get(data.requestId);
    if(pending){clearTimeout(pending.timer);requests.delete(data.requestId);pending.resolve(data)}
  });
  function query(){
    if(!eligible())return Promise.resolve(null);
    /* Neu Penalty da bi dong hoac chua tung mo, iframe van con trong DOM
       nhung src da bi dat ve 'about:blank' (xem PENALTY_JS, su kien
       magicos-app-terminated) - luc do khong co trang nao ben trong de
       tra loi postMessage, cho het 2.2s moi bao that bai se rat cham va
       gay cam giac "treo". Phat hien truong hop nay va bao that bai ngay. */
    if(!frame || !frame.contentWindow || frame.getAttribute('src')==='about:blank')return Promise.resolve(null);
    const id=crypto.randomUUID ? crypto.randomUUID() : Date.now()+'-'+Math.random();
    return new Promise(resolve=>{
      const timer=setTimeout(()=>{requests.delete(id);resolve(null)},3000);
      requests.set(id,{resolve,timer});
      frame.contentWindow.postMessage({source:'magicai-tool',type:'query',requestId:id},'*');
    });
  }
  const ANALYSIS_PHASES=['Đang quét dữ liệu phiên...','Phân tích mẫu hình thủ môn...','Tính xác suất từng hướng sút...','Đối chiếu lịch sử đối đầu...','Mô phỏng lại các pha sút...','Tổng hợp chiến thuật tối ưu...','Kiểm tra độ tin cậy dự đoán...'];
  function buildAnalyzing(){
    const row=document.createElement('div');row.className='ma-message';
    const label=document.createElement('div');label.className='ma-speaker';label.innerHTML='<b>M</b> MAGICAI';row.append(label);
    const body=document.createElement('div');body.className='ma-bubble ma-analyzing';
    body.innerHTML=
      '<div class="ma-analyzing-head">'+
        '<div class="ma-ring"><svg viewBox="0 0 44 44"><defs><linearGradient id="ma-ring-grad" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="#a4f4d1"/><stop offset="100%" stop-color="#63c7ff"/></linearGradient></defs><circle class="ma-ring-bg" cx="22" cy="22" r="18.5"/><circle class="ma-ring-fg" id="maRingFg" cx="22" cy="22" r="18.5" stroke-dasharray="116.2" stroke-dashoffset="116.2"/></svg><div class="ma-ring-core" id="maRingPct">0%</div></div>'+
        '<div class="ma-analyzing-text"><div class="ma-analyzing-title">Đang Phân Tích<span class="ma-thinking"><i></i><i></i><i></i></span></div></div>'+
      '</div>'+
      '<div class="ma-analyzing-meta"><span>Token đã đốt: <b id="maBurned">0</b></span><span>Còn lại: <b id="maRemain">'+getTokens().toLocaleString('vi-VN')+'</b></span></div>';
    row.append(body);chat.append(row);scroll();
    return body;
  }
  /* Chay animation "Dang Phan Tich" trong thoi luong random 10-30 giay, moi
     giay dot 100 Token cua vai hien tai. Neu Token can giua chung se dung
     som va bao that bai (khong tiet lo ket qua du doan). */
  function runAnalysis(){
    return new Promise(resolve=>{
      const durationSec=10+Math.floor(Math.random()*21);
      const body=buildAnalyzing();
      const ring=body.querySelector('#maRingFg'),pct=body.querySelector('#maRingPct'),phaseEl=body.querySelector('#maPhase'),burnedEl=body.querySelector('#maBurned'),remainEl=body.querySelector('#maRemain'),titleEl=body.querySelector('.ma-analyzing-title');
      const burnedState={shown:0,id:null}, remainState={shown:getTokens(),id:null};
      const CIRC=116.2;
      let elapsed=0,burned=0,phaseIdx=0,timer=null;
      function finish(ok){
        clearTimeout(timer);
        body.classList.add(ok?'ma-done':'ma-fail');
        if(titleEl)titleEl.textContent=ok?'Phân Tích Hoàn Tất':'Phân Tích Bị Gián Đoạn';
        if(phaseEl)phaseEl.textContent=ok?('Đã xử lý trong '+elapsed+' giây.'):'Không đủ Token để tiếp tục phân tích.';
        scroll();
        resolve({ok:ok,elapsed:elapsed,burned:burned});
      }
      function tick(){
        if(getTokens()<50){finish(false);return}
        elapsed++;
        const burnAmt=50+Math.floor(Math.random()*51);
        const remain=burnTokens(burnAmt);burned+=burnAmt;
        if(burnedEl)animateCounterTo(burnedEl,burnedState,burned,420);
        if(remainEl)animateCounterTo(remainEl,remainState,remain,420);
        const ratio=Math.min(elapsed/durationSec,1);
        if(ring)ring.style.strokeDashoffset=String(CIRC*(1-ratio));
        if(pct){pct.textContent=Math.round(ratio*100)+'%';pct.classList.remove('pulse');void pct.offsetWidth;pct.classList.add('pulse');}
        if(elapsed%3===0){
          phaseIdx=(phaseIdx+1)%ANALYSIS_PHASES.length;
          if(phaseEl){phaseEl.textContent=ANALYSIS_PHASES[phaseIdx];phaseEl.classList.remove('swap');void phaseEl.offsetWidth;phaseEl.classList.add('swap');}
        }
        if(elapsed>=durationSec){finish(true);return}
        timer=setTimeout(tick,1000);
      }
      timer=setTimeout(tick,1000);
    });
  }
  const SHOT_UNLOCK_COST=[0,500,1000,2000,4000,7500,10000,50000,100000];
  function renderPlan(data){
    connectedId=data.sessionId;status.textContent='ĐÃ KẾT NỐI';
    const body=message('Kết Nối Thành Công');body.querySelector('p').className='ma-connection';
    const code=document.createElement('div');code.className='ma-session';code.textContent='Mã Phiên: '+data.sessionId;body.append(code);
    const board=document.createElement('div');board.className='ma-plan';board.dataset.session=data.sessionId;
    const grid=document.createElement('div');grid.className='ma-grid';
    const names=['TRÁI','GIỮA','PHẢI'],arrows=['↖','↑','↗'];
    data.plans.forEach((plan,i)=>{
      const dir=plan.indexOf('goal');const cell=document.createElement('div');cell.className='ma-shot';cell.style.animationDelay=(i*35)+'ms';cell.dataset.dir=String(dir);
      if(i===0){
        cell.innerHTML='<small>LƯỢT '+(i+1)+'</small><span class="ma-arrow">'+arrows[dir]+'</span><strong class="ma-direction">'+names[dir]+'</strong><span class="ma-result">Hướng ghi bàn</span>';
      }else{
        const cost=SHOT_UNLOCK_COST[i];
        cell.classList.add('ma-locked');
        cell.innerHTML='<small>LƯỢT '+(i+1)+'</small><i class="fa-solid fa-lock ma-lock-icon"></i><button type="button" class="ma-unlock-btn">Mở '+cost.toLocaleString('vi-VN')+'</button><span class="ma-result">Chưa mở</span>';
      }
      grid.append(cell);
    });
    board.append(grid);body.append(board);updateCards(data);scroll();
    board.querySelectorAll('.ma-shot.ma-locked').forEach((cell,idx)=>{
      const btn=cell.querySelector('.ma-unlock-btn');
      const shotIndex=Array.prototype.indexOf.call(grid.children,cell);
      const cost=SHOT_UNLOCK_COST[shotIndex];
      btn.addEventListener('click',e=>{
        e.stopPropagation();
        if(getTokens()<cost){
          btn.classList.remove('ma-deny');void btn.offsetWidth;btn.classList.add('ma-deny');
          if(navigator.vibrate){try{navigator.vibrate([15,40,15])}catch(err){}}
          return;
        }
        burnTokens(cost);
        const dir=parseInt(cell.dataset.dir,10);
        cell.classList.add('ma-unlocking');
        if(navigator.vibrate){try{navigator.vibrate(20)}catch(err){}}
        setTimeout(()=>{
          cell.classList.remove('ma-locked','ma-unlocking');cell.classList.add('ma-just-unlocked');
          cell.innerHTML='<small>LƯỢT '+(shotIndex+1)+'</small><span class="ma-arrow">'+arrows[dir]+'</span><strong class="ma-direction">'+names[dir]+'</strong><span class="ma-result">Hướng ghi bàn</span>';
          if(snapshot&&snapshot.sessionId===data.sessionId)updateCards(snapshot);
        },420);
      });
    });
  }
  /* Tra ve null neu khong co gi chan viec ket noi, hoac 1 chuoi ly do CU THE
     de hien thang cho nguoi dung thay - thay vi de "Ket Noi That Bai" chung
     chung roi phai doan mo hinh. Kiem tra truoc khi goi query() nen tra loi
     duoc ngay, khong phai cho het timeout. */
  function diagnoseBlocked(){
    if(!document.body.classList.contains('unlocked'))return 'Máy đang khoá, không thể đọc dữ liệu phiên chơi.';
    if(!(window.isPenaltySessionValid && window.isPenaltySessionValid()))return 'Giờ chơi Penalty đã hết hạn (hoặc chưa từng mua). Hãy nhập mã nạp giờ chơi rồi thử lại.';
    var src=frame?frame.getAttribute('src'):null;
    if(!frame||!src||src==='about:blank')return 'App Penalty chưa được mở lần nào (hoặc đã đóng hẳn). Hãy mở app Penalty ít nhất 1 lần rồi quay lại đây.';
    return null;
  }
  async function predict(){
    if(busy)return;
    if(currentRole!==role())reset();
    if(getTokens()<100){
      message('Dự đoán Penalty',true);
      const fail=message('Không Đủ Token');fail.querySelector('p').className='ma-failed';
      scroll();return;
    }
    const blocked=diagnoseBlocked();
    if(blocked){
      message('Dự đoán Penalty',true);
      const fail=message('Kết Nối Thất Bại');fail.querySelector('p').className='ma-failed';
      const note=document.createElement('div');note.className='ma-session';note.textContent=blocked;fail.append(note);
      scroll();return;
    }
    busy=true;button.disabled=true;status.textContent='ĐANG KẾT NỐI';const run=epoch;
    message('Dự đoán Penalty',true);
    const thinking=message('Đang Kết Nối...');
    const dots=document.createElement('span');dots.className='ma-thinking';dots.innerHTML='<i></i><i></i><i></i>';thinking.querySelector('p').append(dots);
    try {
      const [data]=await Promise.all([query(),new Promise(r=>setTimeout(r,900))]);
      if(run!==epoch)return;
      dots.remove();
      if(data&&data.active&&eligible()&&snapshot&&snapshot.active&&snapshot.sessionId===data.sessionId&&Date.now()-receivedAt<3500){
        status.textContent='ĐANG PHÂN TÍCH';
        const result=await runAnalysis();
        if(run!==epoch)return;
        if(result.ok&&eligible()){renderPlan(snapshot)}
        else if(!result.ok){stale('Token đã cạn giữa lúc phân tích. Đổi vai hoặc chờ nạp thêm Token để tiếp tục.');}
      }
      else {
        const answer=message('Kết Nối Thất Bại');answer.querySelector('p').className='ma-failed';
        var reason;
        if(!data)reason='Penalty đang mở nhưng không phản hồi kịp. Đảm bảo bạn chưa đóng Penalty, rồi thử lại.';
        else if(!data.active){
          reason='Penalty đang mở nhưng hiện chưa có ván nào đang chơi. Hãy bấm PLAY trong Penalty rồi quay lại đây.';
          if(data._dbg)reason+=' [debug: session='+data._dbg.hasSession+' inSession='+data._dbg.inSession+' gameStarted='+data._dbg.gameStarted+']';
        }
        else reason='Phiên chơi vừa thay đổi hoặc kết thúc ngay lúc kết nối. Thử lại.';
        const note=document.createElement('div');note.className='ma-session';note.textContent=reason;answer.append(note);
        stale(reason);
      }
    } catch(e){if(run===epoch){dots.remove();message('Kết Nối Thất Bại').querySelector('p').className='ma-failed';stale('Không nhận được dữ liệu phiên.')}}
    finally {if(run===epoch){busy=false;button.disabled=false;if(!connectedId)status.textContent='CHƯA KẾT NỐI';scroll()}}
  }
  button.addEventListener('click',predict);
  frame.addEventListener('load',()=>{snapshot=null;stale('Game đã tải lại. Cần kết nối với mã phiên mới.')});
  document.addEventListener('magicos-app-terminated',ev=>{
    if(ev.detail&&ev.detail.appId==='app-tool')reset();
    if(ev.detail&&ev.detail.appId==='app-penalty'){snapshot=null;stale('Game đã đóng. Dữ liệu phiên này không còn hiệu lực.')}
  });
  setInterval(()=>{
    if(currentRole!==role() || (!document.body.classList.contains('unlocked')&&(connectedId||busy||chat.querySelector('.ma-message')))){reset();return}
    if(connectedId&&(!eligible()||Date.now()-receivedAt>4500))stale('Mất kết nối hoặc token đã hết hạn. Hãy kết nối lại.');
  },1000);
  function safeInsets(){app.style.setProperty('--magic-top',Math.max(64,island.offsetTop+island.offsetHeight+12)+'px');app.style.setProperty('--magic-bottom',Math.max(48,homeHitbox.offsetHeight+8)+'px')}
  if(typeof ResizeObserver!=='undefined'){const ro=new ResizeObserver(safeInsets);ro.observe(island);ro.observe(homeHitbox)}
  window.addEventListener('resize',safeInsets);safeInsets();reset();
})();
"""

BANK_CSS = r"""
.bk-app-box{overflow:hidden;background:#04141f;box-shadow:0 5px 18px #0007;}
#app-bank{--bk-top:64px;--bk-bottom:48px;--bk-cyan:#39e6c4;background:#050b14;color:#eaf6ff;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif;}
.bk-shell{position:absolute;top:var(--bk-top);bottom:var(--bk-bottom);left:0;right:0;display:flex;flex-direction:column;overflow-y:auto;-webkit-overflow-scrolling:touch;background:radial-gradient(ellipse at 20% 0,#123a4530,transparent 55%),radial-gradient(ellipse at 100% 100%,#2a144530,transparent 55%),#050b14;}
.bk-header{display:flex;align-items:center;justify-content:space-between;padding:16px 20px 4px;flex:none;}
.bk-brand{font-size:19px;font-weight:850;letter-spacing:1.6px;}
.bk-brand em{font-style:normal;color:var(--bk-cyan);}
.bk-balance-card{margin:14px 18px 6px;padding:20px 20px 18px;border-radius:20px;background:linear-gradient(150deg,#0b2230,#0a1424 65%);border:1px solid #39e6c42c;box-shadow:0 10px 30px #0006,inset 0 1px 0 #ffffff10;position:relative;overflow:hidden;}
.bk-balance-card::before{content:'';position:absolute;inset:-40%;background:conic-gradient(from 0deg,transparent,#39e6c422,transparent 30%);animation:bkSpin 6s linear infinite;pointer-events:none;}
@keyframes bkSpin{to{transform:rotate(360deg)}}
.bk-balance-label{position:relative;font-size:9.5px;letter-spacing:2px;color:#7fa0b0;font-weight:700;}
.bk-balance-value{position:relative;margin-top:8px;font-size:29px;font-weight:800;font-variant-numeric:tabular-nums;display:flex;align-items:baseline;gap:3px;}
.bk-cur{font-size:18px;color:var(--bk-cyan);}
.bk-balance-role{position:relative;margin-top:8px;display:inline-block;font-size:9px;letter-spacing:1.2px;color:#39e6c4;background:#39e6c418;border:1px solid #39e6c440;padding:4px 9px;border-radius:99px;font-weight:700;}
.bk-tabs{display:flex;gap:6px;margin:14px 18px 0;flex:none;}
.bk-tab{flex:1;padding:10px 0;border-radius:12px;border:1px solid #ffffff14;background:#ffffff08;color:#8fa7b5;font-size:11px;font-weight:700;letter-spacing:.2px;cursor:pointer;transition:all .25s;-webkit-tap-highlight-color:transparent;}
.bk-tab.active{background:linear-gradient(135deg,#39e6c4,#1c9fd6);color:#04141f;border-color:transparent;box-shadow:0 4px 14px #39e6c455;}
.bk-body{flex:1;padding:18px;}
.bk-pane{display:none;}
.bk-pane.active{display:block;animation:bkReveal .35s ease both;}
@keyframes bkReveal{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}
.bk-field{margin-bottom:14px;}
.bk-field label{display:block;font-size:10px;color:#7fa0b0;letter-spacing:.5px;margin-bottom:6px;font-weight:700;}
.bk-field input{width:100%;padding:13px 14px;border-radius:12px;border:1px solid #ffffff1c;background:#0c1a26;color:#eaf6ff;font-size:14px;outline:none;transition:border-color .2s;box-sizing:border-box;}
.bk-field input:focus{border-color:var(--bk-cyan);}
.bk-action-btn{position:relative;width:100%;height:48px;border:none;border-radius:13px;background:linear-gradient(135deg,#39e6c4,#1c9fd6);color:#04141f;font-size:14px;font-weight:800;letter-spacing:.8px;cursor:pointer;overflow:hidden;box-shadow:0 8px 20px #39e6c440;-webkit-tap-highlight-color:transparent;}
.bk-action-btn .bk-spin{display:none;width:17px;height:17px;border:2.5px solid #04141f40;border-top-color:#04141f;border-radius:50%;animation:bkRotate .7s linear infinite;position:absolute;left:50%;top:50%;margin:-9px 0 0 -9px;}
.bk-action-btn.loading .lbl{opacity:0;}
.bk-action-btn.loading .bk-spin{display:block;}
@keyframes bkRotate{to{transform:rotate(360deg)}}
.bk-action-btn.success{animation:bkSuccessPulse .5s ease;}
@keyframes bkSuccessPulse{0%{transform:scale(1)}40%{transform:scale(1.05)}100%{transform:scale(1)}}
.bk-action-btn.deny{animation:bkDeny .4s ease;}
@keyframes bkDeny{0%,100%{transform:translateX(0)}25%{transform:translateX(-6px)}75%{transform:translateX(6px)}}
.bk-msg{margin-top:10px;font-size:11.5px;text-align:center;color:#7fa0b0;min-height:14px;}
.bk-msg.ok{color:#39e6c4;}
.bk-msg.err{color:#ff8577;}
.bk-bill-list{display:flex;flex-direction:column;gap:10px;}
.bk-bill{display:flex;align-items:center;gap:12px;padding:13px 14px;border-radius:14px;background:#0c1a26;border:1px solid #ffffff14;}
.bk-bill-icon{width:38px;height:38px;border-radius:11px;display:flex;align-items:center;justify-content:center;font-size:16px;background:linear-gradient(135deg,#8b6bff33,#39e6c433);color:#8b6bff;flex:none;}
.bk-bill-info{flex:1;min-width:0;}
.bk-bill-name{font-size:13px;font-weight:700;}
.bk-bill-amount{font-size:11px;color:#7fa0b0;margin-top:2px;font-variant-numeric:tabular-nums;}
.bk-bill-pay{padding:8px 14px;border-radius:10px;border:none;background:linear-gradient(135deg,#39e6c4,#1c9fd6);color:#04141f;font-size:11px;font-weight:800;cursor:pointer;flex:none;transition:transform .15s;-webkit-tap-highlight-color:transparent;}
.bk-bill-pay:active{transform:scale(.9);}
.bk-bill-pay.paid{background:#1c2c30;color:#5a7a80;pointer-events:none;}
.bk-bill.paying .bk-bill-pay{background:#1c2c30;color:transparent;position:relative;}
.bk-bill.paying .bk-bill-pay::after{content:'';position:absolute;left:50%;top:50%;width:13px;height:13px;margin:-7px 0 0 -7px;border:2px solid #39e6c440;border-top-color:#39e6c4;border-radius:50%;animation:bkRotate .7s linear infinite;}
.bk-card-wrap{perspective:1000px;margin:6px auto 4px;width:min(90%,320px);}
.bk-visa-card{position:relative;width:100%;aspect-ratio:1.586;transform-style:preserve-3d;transition:transform .6s cubic-bezier(.4,.2,.2,1);cursor:pointer;}
.bk-visa-card.flipped{transform:rotateY(180deg);}
.bk-visa-face{position:absolute;inset:0;border-radius:18px;padding:20px;backface-visibility:hidden;box-shadow:0 14px 36px #0008,inset 0 1px 0 #ffffff20;display:flex;flex-direction:column;overflow:hidden;box-sizing:border-box;}
.bk-visa-front{background:linear-gradient(135deg,#1c1440 0%,#0a2647 50%,#0d3b46 100%);}
.bk-visa-back{background:linear-gradient(135deg,#0d3b46,#1c1440);transform:rotateY(180deg);justify-content:flex-start;padding-top:22px;}
.bk-visa-shine{position:absolute;inset:-50%;background:conic-gradient(from 0deg,transparent,#ffffff18,transparent 25%);animation:bkSpin 5s linear infinite;pointer-events:none;}
.bk-visa-chip{width:38px;height:28px;border-radius:6px;background:linear-gradient(135deg,#ffe9a8,#c9a03f);margin-bottom:22px;box-shadow:inset 0 0 0 1px #ffffff40;}
.bk-visa-number{font-size:16.5px;letter-spacing:2.4px;font-weight:700;font-variant-numeric:tabular-nums;margin-bottom:16px;text-shadow:0 2px 4px #0006;}
.bk-visa-bottom{display:flex;justify-content:space-between;align-items:flex-end;margin-top:auto;gap:8px;}
.bk-visa-small{font-size:7.5px;letter-spacing:1px;opacity:.6;}
.bk-visa-holder{font-size:11px;font-weight:700;letter-spacing:.3px;margin-top:3px;white-space:nowrap;}
.bk-visa-logo{font-style:italic;font-weight:900;font-size:19px;letter-spacing:.5px;color:#fff;text-shadow:0 2px 4px #0006;}
.bk-visa-stripe{width:100%;height:38px;background:#0a0a12;margin:0 -20px 18px;}
.bk-visa-cvv-row{display:flex;justify-content:space-between;background:#fff;color:#0a0a12;border-radius:6px;padding:8px 12px;font-size:11px;font-weight:700;letter-spacing:2px;}
.bk-visa-hint{text-align:center;font-size:10.5px;color:#5a7a80;margin-top:12px;letter-spacing:.3px;}
"""
BANK_BODY = r"""
<div class="simple-app" id="app-bank">
  <div class="bk-shell">
    <header class="bk-header"><div class="bk-brand">MAGIC<em>BANK</em></div></header>
    <div class="bk-balance-card">
      <div class="bk-balance-label">SỐ DƯ KHẢ DỤNG</div>
      <div class="bk-balance-value"><span class="bk-cur">$</span><span id="bk-balance-num">0</span></div>
      <div class="bk-balance-role" id="bk-role-tag">USD ACCOUNT</div>
    </div>
    <div class="bk-tabs">
      <button type="button" class="bk-tab active" data-tab="transfer">Chuyển khoản</button>
      <button type="button" class="bk-tab" data-tab="bills">Hoá đơn</button>
      <button type="button" class="bk-tab" data-tab="visa">Thẻ Visa</button>
    </div>
    <div class="bk-body">
      <section class="bk-pane active" id="bk-pane-transfer">
        <div class="bk-field"><label>Người nhận</label><input type="text" id="bk-transfer-to" placeholder="Tên tài khoản / username"></div>
        <div class="bk-field"><label>Số tiền (USD)</label><input type="number" id="bk-transfer-amount" placeholder="0.00" min="0" step="0.01"></div>
        <button type="button" class="bk-action-btn" id="bk-transfer-btn"><span class="lbl">Gửi tiền</span><span class="bk-spin"></span></button>
        <div class="bk-msg" id="bk-transfer-msg"></div>
      </section>
      <section class="bk-pane" id="bk-pane-bills">
        <div class="bk-bill-list" id="bk-bill-list"></div>
      </section>
      <section class="bk-pane" id="bk-pane-visa">
        <div class="bk-card-wrap">
          <div class="bk-visa-card" id="bk-visa-card">
            <div class="bk-visa-face bk-visa-front">
              <div class="bk-visa-chip"></div>
              <div class="bk-visa-shine"></div>
              <div class="bk-visa-number" id="bk-visa-number">&bull;&bull;&bull;&bull; &bull;&bull;&bull;&bull; &bull;&bull;&bull;&bull; 4417</div>
              <div class="bk-visa-bottom">
                <div><div class="bk-visa-small">CHỦ THẺ</div><div class="bk-visa-holder" id="bk-visa-holder">MAGICBANK USER</div></div>
                <div><div class="bk-visa-small">HSD</div><div class="bk-visa-holder">12/29</div></div>
                <div class="bk-visa-logo">VISA</div>
              </div>
            </div>
            <div class="bk-visa-face bk-visa-back">
              <div class="bk-visa-stripe"></div>
              <div class="bk-visa-cvv-row"><span>CVV</span><span id="bk-visa-cvv">&bull;&bull;&bull;</span></div>
              <div class="bk-visa-logo" style="align-self:flex-end;margin-top:auto;">VISA</div>
            </div>
          </div>
        </div>
        <div class="bk-visa-hint">Chạm vào thẻ để xem CVV</div>
      </section>
    </div>
  </div>
</div>
"""
BANK_JS = r"""
(function () {
  const BANK_KEY_PREFIX = 'magicos_bank_balance_v1_';
  const BANK_DEFAULTS = { user: 50, admin: 100000000 };
  function role() { return (typeof adminModeUnlocked !== 'undefined' && adminModeUnlocked) ? 'admin' : 'user'; }
  function bankKey() { return BANK_KEY_PREFIX + role(); }
  function getBalance() {
    try {
      const raw = localStorage.getItem(bankKey());
      if (raw === null) { const def = BANK_DEFAULTS[role()]; localStorage.setItem(bankKey(), String(def)); return def; }
      const n = parseFloat(raw); return Number.isFinite(n) ? n : BANK_DEFAULTS[role()];
    } catch (e) { return BANK_DEFAULTS[role()]; }
  }
  function setBalance(v) {
    v = Math.max(0, Math.round(v * 100) / 100);
    try { localStorage.setItem(bankKey(), String(v)); } catch (e) {}
    document.dispatchEvent(new CustomEvent('magicbank-balance-changed', { detail: { balance: v } }));
    return v;
  }
  window.magicBankGetBalance = getBalance;
  window.magicBankSetBalance = setBalance;
  window.magicBankWithdraw = function (amount) {
    if (amount <= 0) return true;
    const cur = getBalance();
    if (cur < amount) return false;
    setBalance(cur - amount);
    return true;
  };
  window.magicBankDeposit = function (amount) { setBalance(getBalance() + amount); return true; };

  DOCK_APP_META['app-bank'] = { name: 'MagicBank', icon: 'fa-solid fa-building-columns', grad: 'linear-gradient(135deg,#39e6c4,#0a2647)' };

  const bankAppEl = document.getElementById('app-bank');
  const numEl = document.getElementById('bk-balance-num');
  const roleTagEl = document.getElementById('bk-role-tag');
  const holderEl = document.getElementById('bk-visa-holder');
  let shownBalance = null, animId = null, lastRole = null;
  function fmt(v) { return v >= 1000 ? Math.round(v).toLocaleString('en-US') : (Math.round(v * 100) / 100).toLocaleString('en-US'); }
  function renderBalance(animate) {
    const target = getBalance();
    /* Neu vai (admin/user) da doi ke tu lan render truoc - vd nguoi dung mo
       app luc con khoa may, sau do dang nhap bang ma admin roi mo lai app -
       phai coi nhu lan dau, KHONG chay animation dem tu so du cua vai cu
       sang vai moi (se bi lech/giat), va phai doc lai dung key cua vai hien
       tai chu khong giu cache cu. */
    if (lastRole !== null && lastRole !== role()) { shownBalance = null; }
    lastRole = role();
    if (roleTagEl) roleTagEl.textContent = (role() === 'admin' ? 'ADMIN ACCOUNT' : 'USER ACCOUNT') + ' \u00b7 USD';
    if (holderEl) holderEl.textContent = 'MAGICBANK ' + role().toUpperCase();
    if (!numEl) return;
    if (shownBalance === null || !animate) { shownBalance = target; numEl.textContent = fmt(target); return; }
    const from = shownBalance, dur = 650, start = performance.now();
    if (animId) cancelAnimationFrame(animId);
    function step(now) {
      const t = Math.min((now - start) / dur, 1), e = 1 - Math.pow(1 - t, 3);
      const val = from + (target - from) * e;
      numEl.textContent = fmt(val);
      if (t < 1) { animId = requestAnimationFrame(step); } else { shownBalance = target; numEl.textContent = fmt(target); animId = null; }
    }
    animId = requestAnimationFrame(step);
  }
  document.addEventListener('magicbank-balance-changed', function () { renderBalance(true); });
  renderBalance(false);

  /* App co the duoc mo lai (tu icon, tu App Switcher, hoac sau khi doi vai
     dang nhap) ma script nay chi chay 1 lan luc nap trang - phai theo doi
     thoi diem app THUC SU hien len man hinh (display doi tu none -> block)
     de lam moi so du dung theo vai hien tai, khong de loi thoi so du cu. */
  if (bankAppEl && window.MutationObserver) {
    let lastDisplay = bankAppEl.style.display;
    const mo = new MutationObserver(function () {
      const nowDisplay = bankAppEl.style.display;
      if (nowDisplay !== 'none' && lastDisplay === 'none') renderBalance(false);
      lastDisplay = nowDisplay;
    });
    mo.observe(bankAppEl, { attributes: true, attributeFilter: ['style'] });
  }
  const bankIconEl = document.getElementById('bank-app-icon');
  if (bankIconEl) bankIconEl.addEventListener('click', function () { renderBalance(false); });

  const tabs = Array.prototype.slice.call(document.querySelectorAll('#app-bank .bk-tab'));
  const panes = { transfer: document.getElementById('bk-pane-transfer'), bills: document.getElementById('bk-pane-bills'), visa: document.getElementById('bk-pane-visa') };
  tabs.forEach(function (tab) {
    tab.addEventListener('click', function () {
      tabs.forEach(function (t) { t.classList.remove('active'); });
      tab.classList.add('active');
      Object.keys(panes).forEach(function (k) { if (panes[k]) panes[k].classList.remove('active'); });
      const key = tab.getAttribute('data-tab');
      if (panes[key]) panes[key].classList.add('active');
      if (navigator.vibrate) { try { navigator.vibrate(8); } catch (e) {} }
    });
  });

  const transferBtn = document.getElementById('bk-transfer-btn');
  const transferMsg = document.getElementById('bk-transfer-msg');
  const transferTo = document.getElementById('bk-transfer-to');
  const transferAmount = document.getElementById('bk-transfer-amount');
  if (transferBtn) {
    transferBtn.addEventListener('click', function () {
      if (transferBtn.classList.contains('loading')) return;
      const to = (transferTo.value || '').trim();
      const amt = parseFloat(transferAmount.value);
      if (!to) { transferMsg.textContent = 'Nhập người nhận'; transferMsg.className = 'bk-msg err'; return; }
      if (!Number.isFinite(amt) || amt <= 0) { transferMsg.textContent = 'Số tiền không hợp lệ'; transferMsg.className = 'bk-msg err'; return; }
      transferBtn.classList.add('loading');
      setTimeout(function () {
        transferBtn.classList.remove('loading');
        if (!window.magicBankWithdraw(amt)) {
          transferBtn.classList.add('deny');
          setTimeout(function () { transferBtn.classList.remove('deny'); }, 420);
          transferMsg.textContent = 'Số dư không đủ'; transferMsg.className = 'bk-msg err';
          if (navigator.vibrate) { try { navigator.vibrate([15, 40, 15]); } catch (e) {} }
          return;
        }
        transferBtn.classList.add('success');
        setTimeout(function () { transferBtn.classList.remove('success'); }, 550);
        transferMsg.textContent = 'Đã chuyển $' + amt.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + ' đến ' + to; transferMsg.className = 'bk-msg ok';
        transferAmount.value = '';
        if (navigator.vibrate) { try { navigator.vibrate([20, 20, 20]); } catch (e) {} }
      }, 700);
    });
  }

  const billListEl = document.getElementById('bk-bill-list');
  const BILLS = [
    { id: 'electric', name: 'Hoá đơn Điện', icon: 'fa-solid fa-bolt', amount: 42.5 },
    { id: 'water', name: 'Hoá đơn Nước', icon: 'fa-solid fa-droplet', amount: 18.9 },
    { id: 'internet', name: 'Internet', icon: 'fa-solid fa-wifi', amount: 29.99 },
    { id: 'phone', name: 'Điện thoại', icon: 'fa-solid fa-mobile-screen', amount: 15 }
  ];
  function billPaidKey(id) { return 'magicos_bank_bill_paid_' + role() + '_' + id; }
  if (billListEl) {
    billListEl.innerHTML = BILLS.map(function (b) {
      let paid = false; try { paid = localStorage.getItem(billPaidKey(b.id)) === '1'; } catch (e) {}
      return '<div class="bk-bill" data-id="' + b.id + '"><div class="bk-bill-icon"><i class="' + b.icon + '"></i></div><div class="bk-bill-info"><div class="bk-bill-name">' + b.name + '</div><div class="bk-bill-amount">$' + b.amount.toFixed(2) + '</div></div><button type="button" class="bk-bill-pay' + (paid ? ' paid' : '') + '">' + (paid ? 'Đã trả' : 'Thanh toán') + '</button></div>';
    }).join('');
    Array.prototype.slice.call(billListEl.querySelectorAll('.bk-bill-pay')).forEach(function (btn) {
      btn.addEventListener('click', function () {
        if (btn.classList.contains('paid')) return;
        const row = btn.closest('.bk-bill');
        const id = row.getAttribute('data-id');
        const bill = BILLS.filter(function (b) { return b.id === id; })[0];
        row.classList.add('paying');
        setTimeout(function () {
          row.classList.remove('paying');
          if (!window.magicBankWithdraw(bill.amount)) {
            btn.textContent = 'Thiếu tiền';
            if (navigator.vibrate) { try { navigator.vibrate([15, 40, 15]); } catch (e) {} }
            setTimeout(function () { btn.textContent = 'Thanh toán'; }, 1200);
            return;
          }
          btn.classList.add('paid'); btn.textContent = 'Đã trả';
          try { localStorage.setItem(billPaidKey(id), '1'); } catch (e) {}
          if (navigator.vibrate) { try { navigator.vibrate(20); } catch (e) {} }
        }, 650);
      });
    });
  }

  const visaCard = document.getElementById('bk-visa-card');
  if (visaCard) {
    visaCard.addEventListener('click', function () {
      visaCard.classList.toggle('flipped');
      if (navigator.vibrate) { try { navigator.vibrate(10); } catch (e) {} }
    });
  }
})();
"""
STORE_CSS = r"""
.st-app-box{overflow:hidden;background:#1a0f24;box-shadow:0 5px 18px #0007;}
#app-store{--st-top:64px;--st-bottom:48px;--st-gold:#ffcf3f;--st-purple:#a06bff;background:#0d0715;color:#f3ecff;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif;}
.st-shell{position:absolute;top:var(--st-top);bottom:var(--st-bottom);left:0;right:0;overflow:hidden;background:radial-gradient(ellipse at 15% 0,#3a1a5530,transparent 55%),radial-gradient(ellipse at 100% 100%,#5a3a1030,transparent 55%),#0d0715;}
.st-header{padding:16px 20px 6px;}
.st-brand{font-size:19px;font-weight:850;letter-spacing:1.6px;}
.st-brand em{font-style:normal;color:var(--st-gold);}
.st-views{position:relative;height:calc(100% - 46px);overflow:hidden;}
.st-view{position:absolute;inset:0;padding:16px 18px 18px;overflow-y:auto;-webkit-overflow-scrolling:touch;opacity:0;transform:translateX(24px);pointer-events:none;transition:opacity .3s ease,transform .35s cubic-bezier(.3,.7,.35,1);box-sizing:border-box;}
.st-view.active{opacity:1;transform:translateX(0);pointer-events:auto;}
.st-feature-card{width:100%;display:flex;align-items:center;gap:14px;padding:18px;border-radius:18px;border:1px solid #ffffff14;background:linear-gradient(135deg,#1c1430,#120a20);margin-bottom:14px;cursor:pointer;text-align:left;transition:transform .15s;box-shadow:0 8px 22px #0005;box-sizing:border-box;-webkit-tap-highlight-color:transparent;color:#f3ecff;font-family:inherit;}
.st-feature-card:active{transform:scale(.97);}
.st-feature-icon{width:46px;height:46px;border-radius:14px;display:flex;align-items:center;justify-content:center;font-size:19px;flex:none;}
.st-feature-pass .st-feature-icon{background:linear-gradient(135deg,#ffcf3f55,#ff8a2f55);color:#ffcf3f;}
.st-feature-exchange .st-feature-icon{background:linear-gradient(135deg,#a06bff55,#39e6c455);color:#a06bff;}
.st-feature-text{flex:1;min-width:0;}
.st-feature-title{font-size:16px;font-weight:800;color:#f3ecff;}
.st-feature-sub{font-size:10.5px;color:#a99fc0;margin-top:3px;line-height:1.4;}
.st-feature-arrow{color:#7a6f96;font-size:13px;flex:none;}
.st-bank-mini{display:flex;align-items:center;gap:9px;padding:11px 14px;border-radius:12px;background:#ffffff08;border:1px solid #ffffff14;font-size:11.5px;color:#a99fc0;margin-top:4px;}
.st-bank-mini i{color:#39e6c4;}
.st-bank-mini b{color:#f3ecff;font-variant-numeric:tabular-nums;}
.st-back-btn{display:flex;align-items:center;gap:7px;background:none;border:none;color:#a99fc0;font-size:12.5px;font-weight:700;margin-bottom:14px;cursor:pointer;padding:4px 0;-webkit-tap-highlight-color:transparent;}
.st-pass-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px;}
.st-pass-card{border-radius:16px;padding:14px 12px;background:linear-gradient(150deg,#1c1430,#120a20);border:1px solid #ffffff14;text-align:center;position:relative;overflow:hidden;}
.st-pass-card.popular{border-color:#ffcf3f66;box-shadow:0 0 0 1px #ffcf3f33;}
.st-pass-badge{position:absolute;top:8px;right:8px;font-size:7.5px;font-weight:800;letter-spacing:.5px;color:#0d0715;background:#ffcf3f;padding:2px 6px;border-radius:99px;}
.st-pass-label{font-size:12.5px;font-weight:800;margin-bottom:2px;}
.st-pass-price{font-size:17px;font-weight:900;color:var(--st-gold);margin:6px 0 10px;font-variant-numeric:tabular-nums;}
.st-pass-buy{width:100%;padding:9px 0;border:none;border-radius:10px;background:linear-gradient(135deg,#ffcf3f,#ff8a2f);color:#2b1600;font-size:11px;font-weight:800;cursor:pointer;position:relative;overflow:hidden;-webkit-tap-highlight-color:transparent;}
.st-pass-buy .st-spin{display:none;width:14px;height:14px;border:2px solid #2b160040;border-top-color:#2b1600;border-radius:50%;animation:stRotate .7s linear infinite;margin:0 auto;}
@keyframes stRotate{to{transform:rotate(360deg)}}
.st-pass-buy.loading .lbl{display:none;}
.st-pass-buy.loading .st-spin{display:block;}
.st-pass-buy.success{background:linear-gradient(135deg,#39e6c4,#1c9fd6);color:#04141f;animation:stPulse .5s ease;}
@keyframes stPulse{0%{transform:scale(1)}40%{transform:scale(1.06)}100%{transform:scale(1)}}
.st-pass-buy.deny{animation:stDeny .4s ease;}
@keyframes stDeny{0%,100%{transform:translateX(0)}25%{transform:translateX(-6px)}75%{transform:translateX(6px)}}
.st-pass-card.revealed{padding:12px 10px;}
.st-pass-code-wrap{animation:stFadeIn .3s ease both;}
@keyframes stFadeIn{from{opacity:0;transform:scale(.9)}to{opacity:1;transform:scale(1)}}
.st-pass-code-label{font-size:7.5px;letter-spacing:.6px;color:#39e6c4;font-weight:800;margin-bottom:4px;}
.st-pass-code{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:14px;font-weight:800;letter-spacing:1.6px;color:#fff;background:#00000040;border:1px dashed #39e6c455;border-radius:8px;padding:6px 4px;margin-bottom:6px;word-break:break-all;}
.st-pass-code-dur{font-size:8.5px;color:#a99fc0;margin-bottom:8px;}
.st-pass-copy-btn{width:100%;padding:8px 0;border:none;border-radius:9px;background:linear-gradient(135deg,#39e6c4,#1c9fd6);color:#04141f;font-size:10.5px;font-weight:800;cursor:pointer;-webkit-tap-highlight-color:transparent;}
.st-pass-code-hint{font-size:7.5px;color:#7a6f96;margin-top:6px;line-height:1.35;}
.st-exchange-card{border-radius:20px;padding:22px 18px;background:linear-gradient(150deg,#1c1430,#120a20);border:1px solid #ffffff14;text-align:center;box-sizing:border-box;}
.st-exchange-label{font-size:9.5px;letter-spacing:1.6px;color:#a99fc0;font-weight:700;margin-bottom:8px;}
.st-exchange-input{width:100%;text-align:center;padding:14px;border-radius:13px;border:1px solid #ffffff1c;background:#0c0816;color:#f3ecff;font-size:22px;font-weight:800;outline:none;margin-bottom:6px;box-sizing:border-box;}
.st-exchange-input:focus{border-color:var(--st-purple);}
.st-exchange-arrow{color:#a06bff;font-size:16px;margin:10px 0;animation:stBounceArrow 1.4s ease-in-out infinite;}
@keyframes stBounceArrow{0%,100%{transform:translateY(0)}50%{transform:translateY(4px)}}
.st-exchange-result{font-size:26px;font-weight:900;color:var(--st-purple);margin:6px 0 18px;font-variant-numeric:tabular-nums;transition:transform .2s;}
.st-exchange-result.bump{animation:stPulse .4s ease;}
.st-buy-btn{position:relative;width:100%;height:48px;border:none;border-radius:13px;background:linear-gradient(135deg,#a06bff,#6b3bff);color:#fff;font-size:14px;font-weight:800;letter-spacing:.5px;cursor:pointer;overflow:hidden;box-shadow:0 8px 20px #a06bff40;-webkit-tap-highlight-color:transparent;}
.st-buy-btn .st-spin{display:none;width:17px;height:17px;border:2.5px solid #ffffff40;border-top-color:#fff;border-radius:50%;animation:stRotate .7s linear infinite;position:absolute;left:50%;top:50%;margin:-9px 0 0 -9px;}
.st-buy-btn.loading .lbl{opacity:0;}
.st-buy-btn.loading .st-spin{display:block;}
.st-buy-btn.success{background:linear-gradient(135deg,#39e6c4,#1c9fd6);animation:stPulse .5s ease;}
.st-buy-btn.deny{animation:stDeny .4s ease;}
.st-msg{margin-top:10px;font-size:11.5px;color:#a99fc0;min-height:14px;}
.st-msg.ok{color:#39e6c4;}
.st-msg.err{color:#ff8577;}
"""
STORE_BODY = r"""
<div class="simple-app" id="app-store">
  <div class="st-shell">
    <header class="st-header"><div class="st-brand">CỬA <em>HÀNG</em></div></header>
    <div class="st-views">
      <section class="st-view active" id="st-view-home">
        <button type="button" class="st-feature-card st-feature-pass" id="st-open-pass">
          <div class="st-feature-icon"><i class="fa-solid fa-ticket"></i></div>
          <div class="st-feature-text"><div class="st-feature-title">Pass Token</div></div>
          <i class="fa-solid fa-chevron-right st-feature-arrow"></i>
        </button>
        <button type="button" class="st-feature-card st-feature-exchange" id="st-open-exchange">
          <div class="st-feature-icon"><i class="fa-solid fa-coins"></i></div>
          <div class="st-feature-text"><div class="st-feature-title">Token MAGICAI</div></div>
          <i class="fa-solid fa-chevron-right st-feature-arrow"></i>
        </button>
        <div class="st-bank-mini"><i class="fa-solid fa-building-columns"></i><span>Số dư MagicBank: <b id="st-bank-balance">$0</b></span></div>
      </section>
      <section class="st-view" id="st-view-pass">
        <button type="button" class="st-back-btn" data-back><i class="fa-solid fa-arrow-left"></i> Quay lại</button>
        <div class="st-pass-grid" id="st-pass-grid"></div>
      </section>
      <section class="st-view" id="st-view-exchange">
        <button type="button" class="st-back-btn" data-back><i class="fa-solid fa-arrow-left"></i> Quay lại</button>
        <div class="st-exchange-card">
          <div class="st-exchange-label">SỐ TIỀN (USD)</div>
          <input type="number" id="st-exchange-input" class="st-exchange-input" placeholder="0.00" min="0" step="0.01">
          <div class="st-exchange-arrow"><i class="fa-solid fa-arrow-down-long"></i></div>
          <div class="st-exchange-label">NHẬN ĐƯỢC</div>
          <div class="st-exchange-result" id="st-exchange-result">0 Token</div>
          <button type="button" class="st-buy-btn" id="st-exchange-btn"><span class="lbl">Đổi ngay</span><span class="st-spin"></span></button>
          <div class="st-msg" id="st-exchange-msg"></div>
        </div>
      </section>
    </div>
  </div>
</div>
"""
STORE_JS = r"""
(function () {
  DOCK_APP_META['app-store'] = { name: 'Cửa Hàng', icon: 'fa-solid fa-store', grad: 'linear-gradient(135deg,#ffcf3f,#a06bff)' };
  function role() { return (typeof adminModeUnlocked !== 'undefined' && adminModeUnlocked) ? 'admin' : 'user'; }

  const AI_TOKEN_KEY_PREFIX = 'magicos_ai_tokens_v1_';
  const AI_TOKEN_DEFAULTS = { user: 100, admin: 1000000 };
  function aiTokenKey() { return AI_TOKEN_KEY_PREFIX + role(); }
  function getAiTokens() {
    try {
      const raw = localStorage.getItem(aiTokenKey());
      if (raw === null) { const def = AI_TOKEN_DEFAULTS[role()]; localStorage.setItem(aiTokenKey(), String(def)); return def; }
      const n = parseInt(raw, 10); return Number.isFinite(n) ? n : AI_TOKEN_DEFAULTS[role()];
    } catch (e) { return AI_TOKEN_DEFAULTS[role()]; }
  }
  function addAiTokens(n) {
    const v = Math.max(0, Math.round((getAiTokens() + n) * 100) / 100);
    try { localStorage.setItem(aiTokenKey(), String(v)); } catch (e) {}
    document.dispatchEvent(new CustomEvent('magicai-tokens-changed', { detail: { tokens: v } }));
    return v;
  }

  /* ===== PASS TOKEN: dung CHUNG kho voi App Admin (window.PenaltyTokens,
     luu chung o localStorage key 'magicos_penalty_tokens_v1'), khong tu
     lam rieng mot co che gia lap. Nho vay: mua o Cua Hang xong la co NGAY
     1 ma Pass Token that, dan duoc vao o nhap cua app Penalty (dung cai
     modal PenaltyToken co san) de kich hoat; va App Admin cung THAY duoc
     token nay trong danh sach cua no (vi doc chung 1 kho), khong can lam
     gi them - dung nhu "app admin tu nhan duoc yeu cau va tu tao token". */
  function genPassCode() {
    const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
    let code = '';
    for (let i = 0; i < 8; i++) code += chars.charAt(Math.floor(Math.random() * chars.length));
    if (window.PenaltyTokens && window.PenaltyTokens[code]) return genPassCode();
    return code;
  }
  function fmtDurationVN(ms) {
    const totalSec = Math.round(ms / 1000);
    const d = Math.floor(totalSec / 86400), h = Math.floor((totalSec % 86400) / 3600);
    const parts = [];
    if (d) parts.push(d + ' ngày');
    if (h) parts.push(h + ' giờ');
    if (!parts.length) parts.push('dưới 1 giờ');
    return parts.join(' ');
  }
  function issuePassToken(durationMs) {
    if (!window.PenaltyTokens) window.PenaltyTokens = {};
    const code = genPassCode();
    const now = Date.now();
    window.PenaltyTokens[code] = { durationMs: durationMs, createdAt: now, expiresAt: now + durationMs, used: false, usedAt: null, issuedBy: 'store-' + role() };
    if (typeof window.penaltySaveTokens === 'function') window.penaltySaveTokens();
    if (typeof window.renderAdminTokenList === 'function') window.renderAdminTokenList();
    return code;
  }
  function fallbackCopy(text) {
    try {
      const ta = document.createElement('textarea');
      ta.value = text; ta.style.position = 'fixed'; ta.style.opacity = '0';
      document.body.appendChild(ta); ta.focus(); ta.select();
      document.execCommand('copy'); document.body.removeChild(ta);
    } catch (e) {}
  }
  function copyText(text, doneCb) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(doneCb).catch(function () { fallbackCopy(text); doneCb(); });
    } else { fallbackCopy(text); doneCb(); }
  }

  const TIERS = [
    { label: '1 Ngày', days: 1, price: 25 },
    { label: '3 Ngày', days: 3, price: 70 },
    { label: '7 Ngày', days: 7, price: 150 },
    { label: '1 Tháng', days: 30, price: 599, popular: true },
    { label: '6 Tháng', days: 180, price: 4250 },
    { label: '12 Tháng', days: 365, price: 7999 }
  ];

  const storeAppEl = document.getElementById('app-store');
  const bankBalanceEl = document.getElementById('st-bank-balance');
  function renderBankMini() {
    if (bankBalanceEl) bankBalanceEl.textContent = '$' + (window.magicBankGetBalance ? window.magicBankGetBalance().toLocaleString('en-US') : '0');
  }
  document.addEventListener('magicbank-balance-changed', renderBankMini);
  renderBankMini();

  /* Lam moi so du MagicBank hien thi moi khi app THUC SU duoc mo len (bat
     ke mo tu icon hay tu App Switcher, va bat ke vai dang nhap la gi luc
     do), tranh tinh trang hien so du cu cua vai truoc. */
  if (storeAppEl && window.MutationObserver) {
    let lastDisplay = storeAppEl.style.display;
    const mo = new MutationObserver(function () {
      const nowDisplay = storeAppEl.style.display;
      if (nowDisplay !== 'none' && lastDisplay === 'none') renderBankMini();
      lastDisplay = nowDisplay;
    });
    mo.observe(storeAppEl, { attributes: true, attributeFilter: ['style'] });
  }
  const storeIconEl = document.getElementById('store-app-icon');
  if (storeIconEl) storeIconEl.addEventListener('click', function () { renderBankMini(); });

  const views = { home: document.getElementById('st-view-home'), pass: document.getElementById('st-view-pass'), exchange: document.getElementById('st-view-exchange') };
  function showView(key) {
    Object.keys(views).forEach(function (k) { if (views[k]) views[k].classList.toggle('active', k === key); });
    renderBankMini();
  }
  const openPass = document.getElementById('st-open-pass');
  const openExchange = document.getElementById('st-open-exchange');
  if (openPass) openPass.addEventListener('click', function () { showView('pass'); });
  if (openExchange) openExchange.addEventListener('click', function () { showView('exchange'); });
  Array.prototype.slice.call(document.querySelectorAll('#app-store [data-back]')).forEach(function (btn) {
    btn.addEventListener('click', function () { showView('home'); });
  });

  const passGrid = document.getElementById('st-pass-grid');
  if (passGrid) {
    passGrid.innerHTML = TIERS.map(function (t, i) {
      return '<div class="st-pass-card' + (t.popular ? ' popular' : '') + '" data-i="' + i + '">' + (t.popular ? '<span class="st-pass-badge">PHỔ BIẾN</span>' : '') +
        '<div class="st-pass-label">' + t.label + '</div><div class="st-pass-price">$' + t.price.toLocaleString('en-US') + '</div>' +
        '<button type="button" class="st-pass-buy"><span class="lbl">Mua</span><span class="st-spin"></span></button></div>';
    }).join('');
    Array.prototype.slice.call(passGrid.querySelectorAll('.st-pass-buy')).forEach(function (btn, i) {
      btn.addEventListener('click', function () {
        if (btn.classList.contains('loading')) return;
        const tier = TIERS[i];
        btn.classList.add('loading');
        setTimeout(function () {
          btn.classList.remove('loading');
          if (!window.magicBankWithdraw || !window.magicBankWithdraw(tier.price)) {
            btn.classList.add('deny'); setTimeout(function () { btn.classList.remove('deny'); }, 420);
            if (navigator.vibrate) { try { navigator.vibrate([15, 40, 15]); } catch (e) {} }
            return;
          }
          const durationMs = tier.days * 86400000;
          const code = issuePassToken(durationMs);
          btn.classList.add('success');
          const card = btn.closest('.st-pass-card');
          setTimeout(function () {
            card.classList.add('revealed');
            card.innerHTML = '<div class="st-pass-code-wrap">' +
              '<div class="st-pass-code-label">MÃ PASS TOKEN CỦA BẠN</div>' +
              '<div class="st-pass-code">' + code + '</div>' +
              '<div class="st-pass-code-dur">Thời hạn: ' + fmtDurationVN(durationMs) + '</div>' +
              '<button type="button" class="st-pass-copy-btn"><i class="fa-solid fa-copy"></i> Sao chép</button>' +
              '<div class="st-pass-code-hint">Dán mã này vào ô Pass Token trong app Penalty để kích hoạt</div>' +
              '</div>';
            const copyBtn = card.querySelector('.st-pass-copy-btn');
            if (copyBtn) copyBtn.addEventListener('click', function () {
              copyText(code, function () {
                copyBtn.innerHTML = '<i class="fa-solid fa-check"></i> Đã sao chép';
                setTimeout(function () { copyBtn.innerHTML = '<i class="fa-solid fa-copy"></i> Sao chép'; }, 1600);
              });
              if (navigator.vibrate) { try { navigator.vibrate(10); } catch (e) {} }
            });
          }, 380);
          if (navigator.vibrate) { try { navigator.vibrate([20, 20, 30]); } catch (e) {} }
          renderBankMini();
        }, 700);
      });
    });
  }

  const exInput = document.getElementById('st-exchange-input');
  const exResult = document.getElementById('st-exchange-result');
  const exBtn = document.getElementById('st-exchange-btn');
  const exMsg = document.getElementById('st-exchange-msg');
  function updateExResult() {
    const v = parseFloat(exInput.value);
    const tokens = Number.isFinite(v) && v > 0 ? Math.round(v * 0.1 * 100) / 100 : 0;
    if (exResult) exResult.textContent = tokens.toLocaleString('en-US') + ' Token';
  }
  if (exInput) exInput.addEventListener('input', function () {
    updateExResult();
    if (exResult) { exResult.classList.remove('bump'); void exResult.offsetWidth; exResult.classList.add('bump'); }
  });
  updateExResult();
  if (exBtn) {
    exBtn.addEventListener('click', function () {
      if (exBtn.classList.contains('loading')) return;
      const v = parseFloat(exInput.value);
      if (!Number.isFinite(v) || v <= 0) { exMsg.textContent = 'Nhập số tiền hợp lệ'; exMsg.className = 'st-msg err'; return; }
      exBtn.classList.add('loading');
      setTimeout(function () {
        exBtn.classList.remove('loading');
        if (!window.magicBankWithdraw || !window.magicBankWithdraw(v)) {
          exBtn.classList.add('deny'); setTimeout(function () { exBtn.classList.remove('deny'); }, 420);
          exMsg.textContent = 'Số dư MagicBank không đủ'; exMsg.className = 'st-msg err';
          if (navigator.vibrate) { try { navigator.vibrate([15, 40, 15]); } catch (e) {} }
          return;
        }
        const gained = Math.round(v * 0.1 * 100) / 100;
        const total = addAiTokens(gained);
        exBtn.classList.add('success'); setTimeout(function () { exBtn.classList.remove('success'); }, 550);
        exMsg.textContent = 'Đã đổi thành công +' + gained.toLocaleString('en-US') + ' Token (tổng ' + total.toLocaleString('en-US') + ')'; exMsg.className = 'st-msg ok';
        exInput.value = ''; updateExResult();
        renderBankMini();
        if (navigator.vibrate) { try { navigator.vibrate([20, 20, 20]); } catch (e) {} }
      }, 700);
    });
  }
})();
"""

STYLE_BLOCK = APP_CSS_1 + ANIM_CSS_1 + APP_CSS_2 + ANIM_CSS_2 + DOCK_APPS_CSS + PENALTY_CSS + PHONE_APP_CSS + ADMIN_CSS + PENALTY_TOKEN_CSS + SERVER_CSS + MAGICAI_CSS + BANK_CSS + STORE_CSS
BODY_BLOCK = APP_BODY_1 + ANIM_BODY_1 + DOCK_APPS_BODY + APP_BODY_2 + PENALTY_BODY_APP + PHONE_APP_BODY + ADMIN_BODY_APP + MAGICAI_BODY + BANK_BODY + STORE_BODY + "</div>\n"
SCRIPT_BLOCK = ANIM_JS_2 + APP_JS_2 + ANIM_JS_3 + ANIM_JS_1 + APP_JS_4 + ANIM1_JS_1 + DOCK_APPS_JS + PENALTY_JS + PENALTY_TOKEN_JS + PHONE_APP_JS + ADMIN_JS + ADMIN_TOKEN_JS + SERVER_JS + MAGICAI_JS + BANK_JS + STORE_JS

HTML_PAGE = """<!DOCTYPE html>
<html lang="vi" translate="no">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
<meta name="google" content="notranslate">
<meta name="format-detection" content="telephone=no, email=no, address=no">
<title>Edge Panel + Dynamic Island Concept</title>
<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
<style>
""" + STYLE_BLOCK + """
</style>
""" + WALLPAPER_CSS + """
</head>
<body>
""" + BODY_BLOCK + """
<script>
""" + SCRIPT_BLOCK + """
</script>
</body>
</html>
"""

PHONE_APP_HTML = r'''<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover, user-scalable=no">
<title>Điện thoại</title>
<style>
  :root{
    --bg-page:#050506;
    --frame:#0a0a0c;
    --screen-dark:#000000;
    --panel: rgba(255,255,255,0.08);
    --panel-strong: rgba(255,255,255,0.14);
    --hair: rgba(255,255,255,0.10);
    --text:#f5f5f7;
    --sub: rgba(235,235,245,0.6);
    --sub2: rgba(235,235,245,0.38);
    --green:#30d158;
    --green-strong:#27b84c;
    --red:#ff3b30;
    --red-strong:#e0332a;
    --blue:#0a84ff;
    --yellow:#ffd60a;
    --font: -apple-system, "SF Pro Display", "SF Pro Text", "Helvetica Neue", "Segoe UI", Roboto, sans-serif;
  }

  *{ box-sizing:border-box; -webkit-tap-highlight-color: transparent; }
  html,body{
    margin:0; padding:0; height:100%; width:100%;
    background:var(--bg-page);
    font-family:var(--font);
    overflow:hidden;
    -webkit-user-select:none; user-select:none;
  }

  /* ---------- backdrop stage (desktop) ---------- */
  .stage{
    position:fixed; inset:0;
    display:flex; align-items:center; justify-content:center;
    background:
      radial-gradient(1100px 700px at 20% -10%, #1a1a22 0%, transparent 60%),
      radial-gradient(900px 600px at 100% 110%, #14171d 0%, transparent 55%),
      var(--bg-page);
  }

  .hint{
    position:absolute; bottom:22px; left:0; right:0;
    text-align:center; color:rgba(255,255,255,0.28);
    font-size:12px; letter-spacing:.02em; pointer-events:none;
    transition:opacity .6s ease;
  }
  .hint.hide{ opacity:0; }

  /* ---------- phone frame ---------- */
  .frame{
    position:relative;
    width:390px; height:844px;
    border-radius:56px;
    background: linear-gradient(155deg,#2b2c30,#0c0c0e 40%,#1a1b1e);
    padding:12px;
    box-shadow:
      0 0 0 1px rgba(255,255,255,0.06) inset,
      0 30px 80px -20px rgba(0,0,0,0.8),
      0 10px 30px rgba(0,0,0,0.6);
    flex:0 0 auto;
  }
  .buttons-l{ position:absolute; left:-3px; width:3px; background:#151517; border-radius:2px; }
  .b1{ top:118px; height:32px; }
  .b2{ top:170px; height:60px; }
  .b3{ top:240px; height:60px; }
  .buttons-r{ position:absolute; right:-3px; width:3px; top:190px; height:90px; background:#151517; border-radius:2px; }

  .screen{
    position:relative;
    width:100%; height:100%;
    background:var(--screen-dark);
    border-radius:44px;
    overflow:hidden;
    isolation:isolate;
    cursor:pointer;
  }

  /* ---------- screens container ---------- */
  .screens{ position:absolute; inset:0; }
  .view{
    position:absolute; inset:0;
    display:flex; flex-direction:column;
    will-change:transform, opacity;
  }

  /* ================= KEYPAD ================= */
  #view-keypad{
    /* Man hinh nhap so de goi: doi sang nen sang mau, chu/icon doi sang mau dam
       de tranh bi trang-tren-trang. Cac bien mau ben duoi chi ghi de trong
       pham vi #view-keypad, khong anh huong cac man hinh khac (dang goi, cuoc
       goi den...) van giu nen toi nhu cu. */
    --text:#1c1c1e;
    --sub: rgba(60,60,67,0.68);
    --sub2: rgba(60,60,67,0.42);
    --panel: rgba(0,0,0,0.045);
    --panel-strong: rgba(0,0,0,0.08);
    --hair: rgba(0,0,0,0.10);
    padding-top:calc(max(env(safe-area-inset-top,0px), 50px) + 20px);
    background:
      radial-gradient(420px 260px at 50% 0%, #ffffff 0%, #f2f2f7 60%),
      linear-gradient(180deg,#ffffff 0%,#eeeef2 100%);
    transition: transform .46s cubic-bezier(.36,.9,.4,1), opacity .4s ease, filter .4s ease;
    z-index:5;
  }
  #view-keypad.pushed{ transform:translateY(28px) scale(.94); opacity:0; filter:blur(6px); }

  .call-target{
    flex:0 0 auto; text-align:center; padding: 10px 56px 2px 56px;
    min-height:78px; display:flex; align-items:center; justify-content:center;
    position:relative;
  }
  .num-scroll{
    width:100%; overflow-x:auto; overflow-y:hidden;
    -webkit-overflow-scrolling:touch; scrollbar-width:none; -ms-overflow-style:none;
  }
  .num-scroll::-webkit-scrollbar{ display:none; }
  .num-display{
    font-size:40px; font-weight:300; color:var(--text); letter-spacing:1.5px;
    font-variant-numeric: tabular-nums;
    display:inline-flex; min-height:50px; align-items:center; gap:1px;
    justify-content:center; width:100%; white-space:nowrap;
    text-shadow:0 1px 0 rgba(0,0,0,0.03);
    transition: font-size .18s ease;
  }
  .num-display .digit{
    display:inline-block; animation: pop-in .22s cubic-bezier(.2,1.4,.4,1), digit-flash .55s ease-out;
  }
  @keyframes digit-flash{ 0%{ color:var(--green); } 100%{ color:var(--text); } }
  .num-display .digit.fly{ animation: digit-fly .32s ease-in forwards; }
  @keyframes digit-fly{ to{ transform:translateY(-20px) scale(.35); opacity:0; } }
  .num-display .sp{ display:inline-block; width:10px; }
  .num-display .caret{
    display:inline-block; width:2px; height:34px; margin-left:4px; flex:0 0 auto;
    background:var(--green); border-radius:1px;
    animation: caret-blink 1s steps(1) infinite;
  }
  @keyframes caret-blink{ 0%,49%{ opacity:1;} 50%,100%{ opacity:0; } }
  @keyframes pop-in{ from{ transform:scale(.4) translateY(6px); opacity:0;} to{ transform:scale(1) translateY(0); opacity:1;} }
  .num-display.empty::after{
    content:"Nhập số điện thoại"; font-size:17px; color:var(--sub2); font-weight:400; letter-spacing:0;
  }

  .del-btn{
    position:absolute; right:14px; top:50%; transform:translateY(-50%) scale(1);
    width:44px; height:44px; border:none; background:transparent;
    color:var(--sub); opacity:0; pointer-events:none;
    transition:opacity .2s ease, background .15s ease, transform .15s cubic-bezier(.4,0,.2,1);
    display:flex; align-items:center; justify-content:center; border-radius:50%;
  }
  .del-btn.show{ opacity:1; pointer-events:auto; }
  .del-btn svg{ width:22px; height:22px; }
  .del-btn:active{ transform:translateY(-50%) scale(.82); background:rgba(0,0,0,0.06); }

  .keypad{
    flex:1; display:grid; grid-template-columns:repeat(3,1fr);
    align-content:center; justify-items:center;
    gap:20px 0; padding:8px 26px 0;
  }
  .key{
    width:78px; height:78px; border-radius:50%;
    background: linear-gradient(160deg, rgba(0,0,0,0.055), rgba(0,0,0,0.02));
    border:1px solid rgba(0,0,0,0.08);
    color:var(--text);
    display:flex; flex-direction:column; align-items:center; justify-content:center;
    position:relative; overflow:hidden;
    box-shadow: 0 1px 0 rgba(255,255,255,0.7) inset, 0 8px 16px -10px rgba(0,0,0,0.18);
    transition: transform .12s cubic-bezier(.4,0,.2,1), background .15s ease, box-shadow .15s ease;
    opacity:0; transform:translateY(14px) scale(.82);
    animation: key-in .5s cubic-bezier(.22,1.1,.36,1) forwards;
  }
  @keyframes key-in{ to{ opacity:1; transform:translateY(0) scale(1); } }
  .key .n{ font-size:32px; font-weight:400; line-height:1; letter-spacing:.3px; }
  .key .l{ font-size:9.5px; letter-spacing:2.6px; color:var(--sub); margin-top:3px; font-weight:700; }
  .key:active{
    transform:scale(.91);
    background: linear-gradient(160deg, rgba(0,0,0,0.10), rgba(0,0,0,0.035));
    box-shadow: 0 1px 0 rgba(255,255,255,0.7) inset, 0 4px 10px -6px rgba(0,0,0,0.22);
  }
  .key .ripple{
    position:absolute; border-radius:50%; background:rgba(0,0,0,0.18);
    transform:scale(0); opacity:.6; pointer-events:none;
  }
  .key .ripple.go{ animation: rip .5s ease-out forwards; }
  @keyframes rip{ to{ transform:scale(2.6); opacity:0; } }

  .bottom-row{
    display:flex; flex-direction:column; align-items:center; justify-content:flex-end;
    gap:14px;
    padding:14px 20px calc(env(safe-area-inset-bottom,0px) + 20px); min-height:170px; position:relative;
  }
  .call-btn{
    width:76px; height:76px; border-radius:50%; border:none; flex:0 0 auto;
    background: linear-gradient(180deg,var(--green),var(--green-strong));
    box-shadow: 0 8px 22px -6px rgba(48,209,88,.6);
    display:flex; align-items:center; justify-content:center;
    transition: transform .15s cubic-bezier(.4,0,.2,1), box-shadow .15s ease;
  }
  .call-btn:active{ transform:scale(.88); box-shadow:0 3px 10px -3px rgba(48,209,88,.5); }
  .call-btn svg{ width:31px; height:31px; }
  .call-btn.disabled{ opacity:.25; pointer-events:none; }
  .call-btn:not(.disabled){ animation: call-breathe 2.6s ease-in-out infinite; }
  @keyframes call-breathe{
    0%,100%{ box-shadow:0 8px 22px -6px rgba(48,209,88,.6); }
    50%{ box-shadow:0 10px 30px -3px rgba(48,209,88,.95); }
  }

  .sim-link{
    flex:0 0 auto; margin:0 auto;
    font-size:12px; color:var(--sub); background:var(--panel);
    border:1px solid var(--hair); padding:8px 12px; border-radius:14px;
    display:flex; align-items:center; gap:6px;
    transition: transform .12s ease, background .15s ease;
  }
  .sim-link:active{ transform:scale(.94); background:var(--panel-strong); }
  .sim-link svg{ width:14px; height:14px; }

  /* ================= CALL SCREEN (outgoing / in-call) ================= */
  #view-call{
    z-index:20;
    background: radial-gradient(700px 500px at 50% -8%, #23242b 0%, #000 62%);
    transform:translateY(100%);
    transition: transform .5s cubic-bezier(.32,.9,.35,1);
    padding-top:calc(max(env(safe-area-inset-top,0px), 50px) + 40px);
  }
  #view-call.show{ transform:translateY(0); }

  .caller{ flex:0 0 auto; text-align:center; padding:0 30px; }
  .avatar{
    width:132px; height:132px; margin:0 auto 20px; border-radius:50%;
    display:flex; align-items:center; justify-content:center;
    font-size:52px; font-weight:500; color:#fff; position:relative;
    background: linear-gradient(150deg,#6b6f76,#2b2d33);
    box-shadow: 0 10px 30px -8px rgba(0,0,0,.6);
    animation: avatar-float 3.2s ease-in-out infinite;
  }
  @keyframes avatar-float{ 0%,100%{ transform:translateY(0); } 50%{ transform:translateY(-7px); } }
  .caller.connected .avatar{ animation:none; }
  .avatar.burst::before{
    content:""; position:absolute; inset:0; border-radius:50%;
    animation: connect-burst .7s ease-out;
  }
  @keyframes connect-burst{
    0%{ box-shadow:0 0 0 0 rgba(48,209,88,.6); }
    100%{ box-shadow:0 0 0 38px rgba(48,209,88,0); }
  }
  .avatar .ring{
    position:absolute; inset:-10px; border-radius:50%;
    border:1.5px solid rgba(255,255,255,0.18);
    opacity:0; animation: pulse-ring 2.2s ease-out infinite;
  }
  .avatar .ring.r2{ animation-delay:.7s; }
  .avatar .ring.r3{ animation-delay:1.4s; }
  @keyframes pulse-ring{
    0%{ transform:scale(.92); opacity:.55; }
    100%{ transform:scale(1.55); opacity:0; }
  }
  .caller.connected .ring{ animation-play-state:paused; opacity:0; }

  .cname{ font-size:27px; font-weight:600; color:var(--text); margin-bottom:6px; letter-spacing:.2px; }
  .cstatus{ font-size:16px; color:var(--sub); min-height:22px; transition:opacity .25s ease; }
  .cstatus.fx{ animation:fade-cycle 1.4s ease-in-out infinite; }
  @keyframes fade-cycle{ 0%,100%{ opacity:.45;} 50%{ opacity:1;} }

  .grid-actions{
    flex:1; display:grid; grid-template-columns:repeat(3,1fr);
    row-gap:22px; column-gap:0; align-content:center; padding:0 34px;
    opacity:0; transform:translateY(10px); transition:opacity .35s ease .1s, transform .35s ease .1s;
  }
  .grid-actions.show{ opacity:1; transform:translateY(0); }
  .action{
    display:flex; flex-direction:column; align-items:center; gap:8px;
    justify-self:center;
  }
  .action .circ{
    width:64px; height:64px; border-radius:50%;
    background:var(--panel); border:1px solid var(--hair);
    display:flex; align-items:center; justify-content:center;
    transition: transform .14s cubic-bezier(.4,0,.2,1), background .18s ease;
  }
  .action .circ svg{ width:26px; height:26px; color:#fff; }
  .action span{ font-size:12px; color:var(--sub); font-weight:500; }
  .action .circ:active{ transform:scale(.88); }
  .action.active .circ{ background:#fff; }
  .action.active .circ svg{ color:#000; }
  .action.active span{ color:#fff; }

  @keyframes icon-bounce{
    0%{ transform:scale(1); }
    35%{ transform:scale(.80); }
    65%{ transform:scale(1.12); }
    100%{ transform:scale(1); }
  }
  .fx-bounce{ animation: icon-bounce .42s cubic-bezier(.34,1.56,.64,1); }
  .fx-ripple{
    position:absolute; border-radius:50%; background:rgba(255,255,255,0.4);
    transform:scale(0); opacity:.7; pointer-events:none;
  }
  .fx-ripple.go{ animation: rip .55s ease-out forwards; }
  .action .circ, .in-btn, .end-btn, .call-btn{ position:relative; overflow:hidden; }

  .call-bottom{
    flex:0 0 auto; display:flex; align-items:center; justify-content:center;
    padding:6px 0 52px;
  }
  .end-btn{
    width:74px; height:74px; border-radius:50%; border:none;
    background: linear-gradient(180deg,var(--red),var(--red-strong));
    box-shadow:0 8px 20px -6px rgba(255,59,48,.6);
    display:flex; align-items:center; justify-content:center;
    transition: transform .15s cubic-bezier(.4,0,.2,1);
  }
  .end-btn:active{ transform:scale(.86); }
  .end-btn svg{ width:30px; height:30px; }

  /* ================= INCOMING CALL ================= */
  #view-incoming{
    z-index:30;
    background: radial-gradient(800px 600px at 50% 0%, #262832 0%, #050506 65%);
    opacity:0; pointer-events:none;
    transform:scale(1.02);
    transition: opacity .35s ease, transform .35s ease;
    padding-top:calc(max(env(safe-area-inset-top,0px), 50px) + 56px);
  }
  #view-incoming.show{ opacity:1; pointer-events:auto; transform:scale(1); }

  .in-tag{
    text-align:center; font-size:15px; color:var(--sub); margin-bottom:4px;
    opacity:0; transform:translateY(-6px);
  }
  #view-incoming.show .in-tag{ animation: drop-in .5s cubic-bezier(.22,1,.36,1) .05s forwards; }
  .in-name{
    text-align:center; font-size:32px; font-weight:600; color:#fff; margin-bottom:8px;
    opacity:0; transform:translateY(-6px);
  }
  #view-incoming.show .in-name{ animation: drop-in .5s cubic-bezier(.22,1,.36,1) .12s forwards; }
  .in-sub{
    text-align:center; font-size:15px; color:var(--sub2); margin-bottom:20px;
    opacity:0; transform:translateY(-6px);
  }
  #view-incoming.show .in-sub{ animation: drop-in .5s cubic-bezier(.22,1,.36,1) .18s forwards; }
  @keyframes drop-in{ to{ opacity:1; transform:translateY(0); } }

  .in-avatar{
    width:150px; height:150px; margin:6px auto 0; border-radius:50%;
    background: linear-gradient(150deg,#5b7cff,#2a2f6b);
    display:flex; align-items:center; justify-content:center;
    font-size:58px; font-weight:600; color:#fff;
    box-shadow:0 14px 40px -10px rgba(60,80,255,.5);
    opacity:0; transform:scale(.7);
  }
  #view-incoming.show .in-avatar{ animation: avatar-in .55s cubic-bezier(.2,1.4,.4,1) .1s forwards, avatar-glow 2.6s ease-in-out .75s infinite; }
  @keyframes avatar-in{ to{ opacity:1; transform:scale(1); } }
  @keyframes avatar-glow{
    0%,100%{ box-shadow:0 14px 40px -10px rgba(60,80,255,.5); }
    50%{ box-shadow:0 16px 56px -4px rgba(60,80,255,.9); }
  }

  .in-actions{
    flex:1; display:flex; align-items:flex-end; justify-content:space-between;
    padding:0 46px 26px;
  }
  .swipe-hint{
    position:absolute; left:0; right:0; bottom:132px; text-align:center;
    font-size:12px; color:var(--sub2); letter-spacing:.02em;
    opacity:0;
  }
  #view-incoming.show .swipe-hint{ animation: drop-in .5s ease .35s forwards; }

  .in-action{ display:flex; flex-direction:column; align-items:center; gap:10px; }
  .in-action span{ font-size:13px; color:var(--sub); font-weight:500; }
  .in-btn{
    width:76px; height:76px; border-radius:50%; border:none; position:relative;
    display:flex; align-items:center; justify-content:center;
    transition: transform .14s cubic-bezier(.4,0,.2,1);
    opacity:0; transform:translateY(16px) scale(.85);
  }
  #view-incoming.show .in-btn.decline{ animation: btn-in .5s cubic-bezier(.22,1.1,.36,1) .22s forwards; }
  #view-incoming.show .in-btn.accept{ animation: btn-in .5s cubic-bezier(.22,1.1,.36,1) .3s forwards; }
  @keyframes btn-in{ to{ opacity:1; transform:translateY(0) scale(1); } }
  .in-btn svg{ width:30px; height:30px; z-index:2; }
  .in-btn:active{ transform:scale(.86); }
  .in-btn.decline{ background:linear-gradient(180deg,var(--red),var(--red-strong)); box-shadow:0 8px 20px -6px rgba(255,59,48,.6); }
  .in-btn.accept{ background:linear-gradient(180deg,var(--green),var(--green-strong)); box-shadow:0 8px 20px -6px rgba(48,209,88,.6); }
  .in-btn .halo{
    position:absolute; inset:-6px; border-radius:50%;
    border:1.5px solid rgba(48,209,88,.5); opacity:0;
    animation: halo-pulse 1.8s ease-out infinite;
  }
  .in-btn.decline .halo{ border-color:rgba(255,59,48,.5); }
  @keyframes halo-pulse{ 0%{ transform:scale(1); opacity:.5;} 100%{ transform:scale(1.5); opacity:0; } }

  /* ================= TOAST ================= */
  .toast{
    position:absolute; left:50%; bottom:46px; transform:translate(-50%,14px) scale(.92);
    background:rgba(40,40,44,0.92); backdrop-filter:blur(8px);
    color:#fff; font-size:14px; font-weight:500;
    padding:11px 20px; border-radius:16px; z-index:80;
    opacity:0; pointer-events:none;
    transition: opacity .3s ease, transform .38s cubic-bezier(.34,1.56,.64,1);
    white-space:nowrap;
  }
  .toast.show{ opacity:1; transform:translate(-50%,0) scale(1); }

  /* ================= MAZI SIM (goi *101# de kiem tra token) ================= */
  .mazi-loading{
    position:absolute; inset:0; z-index:70;
    display:flex; flex-direction:column; align-items:center; justify-content:center; gap:16px;
    background:rgba(3,6,4,0); backdrop-filter:blur(0px); -webkit-backdrop-filter:blur(0px);
    opacity:0; pointer-events:none;
    transition:opacity .3s ease, background .3s ease, backdrop-filter .3s ease;
  }
  .mazi-loading.show{ opacity:1; pointer-events:auto; background:rgba(3,6,4,0.55); backdrop-filter:blur(6px); -webkit-backdrop-filter:blur(6px); }
  .mazi-spinner{
    width:46px; height:46px; border-radius:50%;
    border:3px solid rgba(48,209,88,0.2); border-top-color:var(--green);
    animation: mazi-spin .8s linear infinite;
  }
  @keyframes mazi-spin{ to{ transform:rotate(360deg); } }
  .mazi-loading-text{ font-size:13px; color:var(--sub); letter-spacing:.02em; }

  .mazi-overlay{
    position:absolute; inset:0; z-index:75;
    display:flex; align-items:center; justify-content:center;
    padding:24px;
    background:rgba(3,6,4,0); backdrop-filter:blur(0px); -webkit-backdrop-filter:blur(0px);
    opacity:0; pointer-events:none;
    transition:opacity .32s ease, background .32s ease, backdrop-filter .32s ease;
  }
  .mazi-overlay.show{ opacity:1; pointer-events:auto; background:rgba(3,6,4,0.62); backdrop-filter:blur(12px); -webkit-backdrop-filter:blur(12px); }
  .mazi-card{
    position:relative; width:min(100%,300px); border-radius:24px; padding:26px 22px 8px;
    background:linear-gradient(165deg, rgba(22,42,27,0.97), rgba(6,12,8,0.99));
    border:1px solid rgba(48,209,88,0.3);
    box-shadow:0 26px 60px rgba(0,0,0,0.6), inset 0 1px 0 rgba(255,255,255,0.06);
    text-align:center; overflow:hidden;
    transform:scale(.72) translateY(26px); opacity:0;
  }
  .mazi-overlay.show .mazi-card{ animation: mazi-card-in .5s cubic-bezier(.34,1.56,.64,1) forwards; }
  @keyframes mazi-card-in{ 0%{ opacity:0; transform:scale(.7) translateY(28px);} 60%{ opacity:1; transform:scale(1.04) translateY(-4px);} 100%{ opacity:1; transform:scale(1) translateY(0);} }
  .mazi-card-glow{
    position:absolute; left:-30%; right:-30%; top:-40%; height:70%;
    background:radial-gradient(circle at 50% 0%, rgba(48,209,88,.4), transparent 70%);
    pointer-events:none; filter:blur(2px); z-index:0;
  }
  .mazi-sim-icon{
    position:relative; z-index:1;
    width:54px; height:54px; margin:0 auto 12px; border-radius:16px;
    background:linear-gradient(150deg,#3ddc6b,#12722f);
    display:flex; align-items:center; justify-content:center;
    box-shadow:0 10px 22px -6px rgba(48,209,88,.55);
    opacity:0; transform:scale(.5) rotate(-8deg);
  }
  .mazi-overlay.show .mazi-sim-icon{ animation: mazi-icon-pop .5s cubic-bezier(.34,1.56,.64,1) .08s forwards; }
  @keyframes mazi-icon-pop{ to{ opacity:1; transform:scale(1) rotate(0deg); } }
  .mazi-sim-icon svg{ width:25px; height:25px; }
  .mazi-title{
    position:relative; z-index:1;
    font-size:16.5px; font-weight:800; letter-spacing:3px; color:#eafff2; margin-bottom:14px; text-transform:uppercase;
  }
  .mazi-row{
    position:relative; z-index:1;
    display:flex; align-items:center; justify-content:space-between; gap:14px;
    padding:11px 2px; font-size:13px;
  }
  .mazi-row + .mazi-row{ border-top:1px dashed rgba(109,255,176,0.18); }
  .mazi-label{ color:var(--sub2); white-space:nowrap; }
  .mazi-value{ color:#eafff2; font-weight:700; letter-spacing:.3px; font-variant-numeric: tabular-nums; }
  .mazi-value.mazi-balance{ color:var(--green); font-size:15px; }
  .mazi-actions{
    position:relative; z-index:1;
    display:flex; align-items:stretch; margin-top:16px;
    border-top:1px solid rgba(255,255,255,0.08);
  }
  .mazi-divider{ width:1px; background:rgba(255,255,255,0.08); }
  .mazi-btn{
    flex:1; border:none; background:none; padding:14px 0; font-size:14.5px; font-weight:700;
    letter-spacing:.4px; cursor:pointer; position:relative; overflow:hidden;
    transition:transform .12s ease;
  }
  .mazi-btn.mazi-cancel{ color:var(--sub); }
  .mazi-btn.mazi-confirm{ color:var(--green); }
  .mazi-btn:active{ transform:scale(.95); background:rgba(255,255,255,0.04); }

  /* ---------- responsive: real mobile fills viewport ---------- */
  @media (max-width:480px), (max-height:820px){
    .stage{ padding:0; }
    .frame{
      width:100vw; height:100vh; height:100dvh;
      border-radius:0; padding:0; box-shadow:none;
    }
    .screen{ border-radius:0; }
    .buttons-l,.buttons-r{ display:none; }
    .hint{ display:none; }
  }
</style>
<style>
  /* ===== Ghi de de nhung gon trong khung app cua MAGICQN (bo khung dien thoai rieng) ===== */
  html, body{ background:#000 !important; }
  .stage{ padding:0 !important; background:#000 !important; }
  .frame{
    width:100% !important; height:100% !important;
    border-radius:0 !important; padding:0 !important; box-shadow:none !important;
    background:#000 !important;
  }
  .buttons-l, .buttons-r{ display:none !important; }
  .screen{ width:100% !important; height:100% !important; border-radius:0 !important; }
</style>
</head>
<body>

<div class="stage" id="stage">
  <div class="frame">
    <span class="buttons-l b1"></span>
    <span class="buttons-l b2"></span>
    <span class="buttons-l b3"></span>
    <span class="buttons-r"></span>

    <div class="screen" id="screen">

      <div class="screens">

        <!-- KEYPAD -->
        <div class="view" id="view-keypad">
          <div class="call-target">
            <div class="num-scroll" id="numScroll">
              <div class="num-display empty" id="numDisplay"></div>
            </div>
            <button class="del-btn" id="delBtn" aria-label="Xóa">
              <svg viewBox="0 0 24 24" fill="none"><path d="M8.5 5H21a1 1 0 011 1v12a1 1 0 01-1 1H8.5a1 1 0 01-.77-.36l-6-7a1 1 0 010-1.28l6-7A1 1 0 018.5 5z" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/><path d="M13.5 10l4 4m0-4l-4 4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
            </button>
          </div>

          <div class="keypad" id="keypad"></div>

          <div class="bottom-row">
            <button class="call-btn disabled" id="callBtn" aria-label="Gọi">
              <svg viewBox="0 0 24 24" fill="none"><path d="M6.6 10.8c1.4 2.8 3.8 5.1 6.6 6.6l2.2-2.2c.3-.3.7-.4 1.1-.3 1.2.4 2.5.6 3.8.6.6 0 1 .4 1 1V20c0 .6-.4 1-1 1C10.9 21 3 13.1 3 3.7c0-.6.4-1 1-1h3.5c.6 0 1 .4 1 1 0 1.3.2 2.6.6 3.8.1.4 0 .8-.3 1.1L6.6 10.8z" fill="white"/></svg>
            </button>
            <div class="sim-link" id="simIncoming">
              <svg viewBox="0 0 24 24" fill="none"><path d="M12 2v20M2 12h20" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
              Giả lập cuộc gọi đến
            </div>
          </div>
        </div>

        <!-- OUTGOING / IN-CALL -->
        <div class="view" id="view-call">
          <div class="caller" id="callerBlock">
            <div class="avatar" id="callAvatar">
              <span class="ring"></span><span class="ring r2"></span><span class="ring r3"></span>
              <span id="callInitial">#</span>
            </div>
            <div class="cname" id="callName">—</div>
            <div class="cstatus fx" id="callStatus">Đang đổ chuông…</div>
          </div>

          <div class="grid-actions" id="callActions">
            <div class="action" id="actMute"><div class="circ"><svg viewBox="0 0 24 24" fill="none"><path d="M12 15a3 3 0 003-3V6a3 3 0 10-6 0v6a3 3 0 003 3z" stroke="currentColor" stroke-width="1.6"/><path d="M6 11a6 6 0 0012 0M12 19v2" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg></div><span>tắt tiếng</span></div>
            <div class="action" id="actKeypad"><div class="circ"><svg viewBox="0 0 24 24" fill="none"><circle cx="6" cy="6" r="1.6" fill="currentColor"/><circle cx="12" cy="6" r="1.6" fill="currentColor"/><circle cx="18" cy="6" r="1.6" fill="currentColor"/><circle cx="6" cy="12" r="1.6" fill="currentColor"/><circle cx="12" cy="12" r="1.6" fill="currentColor"/><circle cx="18" cy="12" r="1.6" fill="currentColor"/><circle cx="6" cy="18" r="1.6" fill="currentColor"/><circle cx="12" cy="18" r="1.6" fill="currentColor"/><circle cx="18" cy="18" r="1.6" fill="currentColor"/></svg></div><span>bàn phím</span></div>
            <div class="action" id="actSpeaker"><div class="circ"><svg viewBox="0 0 24 24" fill="none"><path d="M4 9v6h4l5 4V5L8 9H4z" fill="currentColor"/><path d="M16 9a4 4 0 010 6" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg></div><span>loa ngoài</span></div>
            <div class="action"><div class="circ"><svg viewBox="0 0 24 24" fill="none"><path d="M16 8a4 4 0 11-8 0 4 4 0 018 0zM4 20c0-3.3 3.6-6 8-6s8 2.7 8 6" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/><path d="M19 3v6M16 6h6" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg></div><span>thêm cuộc gọi</span></div>
            <div class="action"><div class="circ"><svg viewBox="0 0 24 24" fill="none"><rect x="3" y="6" width="13" height="12" rx="2.4" stroke="currentColor" stroke-width="1.6"/><path d="M16 10.5l5-3v9l-5-3" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/></svg></div><span>FaceTime</span></div>
            <div class="action"><div class="circ"><svg viewBox="0 0 24 24" fill="none"><path d="M12 12a4 4 0 100-8 4 4 0 000 8zM4 21c0-3.9 3.6-7 8-7s8 3.1 8 7" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg></div><span>danh bạ</span></div>
          </div>

          <div class="call-bottom">
            <button class="end-btn" id="endBtn" aria-label="Kết thúc">
              <svg viewBox="0 0 24 24" fill="none" style="transform:rotate(135deg)"><path d="M6.6 10.8c1.4 2.8 3.8 5.1 6.6 6.6l2.2-2.2c.3-.3.7-.4 1.1-.3 1.2.4 2.5.6 3.8.6.6 0 1 .4 1 1V20c0 .6-.4 1-1 1C10.9 21 3 13.1 3 3.7c0-.6.4-1 1-1h3.5c.6 0 1 .4 1 1 0 1.3.2 2.6.6 3.8.1.4 0 .8-.3 1.1L6.6 10.8z" fill="white"/></svg>
            </button>
          </div>
        </div>

        <!-- INCOMING -->
        <div class="view" id="view-incoming">
          <div class="in-tag">Điện thoại di động</div>
          <div class="in-name" id="inName">Số lạ</div>
          <div class="in-sub" id="inSub">Việt Nam</div>
          <div class="in-avatar" id="inAvatar">#</div>

          <div class="in-actions">
            <div class="in-action">
              <button class="in-btn decline" id="declineBtn"><span class="halo"></span>
                <svg viewBox="0 0 24 24" fill="none" style="transform:rotate(135deg)"><path d="M6.6 10.8c1.4 2.8 3.8 5.1 6.6 6.6l2.2-2.2c.3-.3.7-.4 1.1-.3 1.2.4 2.5.6 3.8.6.6 0 1 .4 1 1V20c0 .6-.4 1-1 1C10.9 21 3 13.1 3 3.7c0-.6.4-1 1-1h3.5c.6 0 1 .4 1 1 0 1.3.2 2.6.6 3.8.1.4 0 .8-.3 1.1L6.6 10.8z" fill="white"/></svg>
              </button>
              <span>Từ chối</span>
            </div>
            <div class="in-action">
              <button class="in-btn accept" id="acceptBtn"><span class="halo"></span>
                <svg viewBox="0 0 24 24" fill="none"><path d="M6.6 10.8c1.4 2.8 3.8 5.1 6.6 6.6l2.2-2.2c.3-.3.7-.4 1.1-.3 1.2.4 2.5.6 3.8.6.6 0 1 .4 1 1V20c0 .6-.4 1-1 1C10.9 21 3 13.1 3 3.7c0-.6.4-1 1-1h3.5c.6 0 1 .4 1 1 0 1.3.2 2.6.6 3.8.1.4 0 .8-.3 1.1L6.6 10.8z" fill="white"/></svg>
              </button>
              <span>Trả lời</span>
            </div>
          </div>
        </div>

      </div>

      <!-- MAZI SIM: hien khi quay *101# -->
      <div class="mazi-loading" id="maziLoading">
        <div class="mazi-spinner"></div>
        <div class="mazi-loading-text">Đang kết nối MAZI SIM…</div>
      </div>
      <div class="mazi-overlay" id="maziOverlay">
        <div class="mazi-card" id="maziCard">
          <div class="mazi-card-glow"></div>
          <div class="mazi-sim-icon">
            <svg viewBox="0 0 24 24" fill="none"><path d="M7 3h7l5 5v11a2 2 0 01-2 2H7a2 2 0 01-2-2V5a2 2 0 012-2z" fill="#eafff2" opacity="0.18"/><path d="M7 3h7l5 5v11a2 2 0 01-2 2H7a2 2 0 01-2-2V5a2 2 0 012-2z" stroke="#eafff2" stroke-width="1.4" stroke-linejoin="round"/><rect x="8.1" y="9.8" width="7.8" height="6.6" rx="1.3" stroke="#eafff2" stroke-width="1.3"/><path d="M8.1 12.6h7.8M11.6 9.8v6.6" stroke="#eafff2" stroke-width="1.1"/></svg>
          </div>
          <div class="mazi-title">MAZI SIM</div>
          <div class="mazi-row"><span class="mazi-label">Số điện thoại:</span><span class="mazi-value" id="maziPhoneNumber">-</span></div>
          <div class="mazi-row"><span class="mazi-label">Số dư token:</span><span class="mazi-value mazi-balance" id="maziBalanceValue">-</span></div>
          <div class="mazi-actions">
            <button type="button" class="mazi-btn mazi-cancel" id="maziCancelBtn">Huỷ</button>
            <div class="mazi-divider"></div>
            <button type="button" class="mazi-btn mazi-confirm" id="maziConfirmBtn">Xác Nhận</button>
          </div>
        </div>
      </div>

      <div class="toast" id="toast"></div>
    </div>
  </div>
</div>

<script>
(function(){
  "use strict";

  /* ---------- state ---------- */
  var number = "";
  var callTimer = null, callSeconds = 0, ringTimeout = null;
  var currentCallerName = "Số lạ";

  var numDisplay = document.getElementById('numDisplay');
  var numScroll = document.getElementById('numScroll');
  var delBtn = document.getElementById('delBtn');
  var callBtn = document.getElementById('callBtn');
  var keypad = document.getElementById('keypad');

  var viewKeypad = document.getElementById('view-keypad');
  var viewCall = document.getElementById('view-call');
  var viewIncoming = document.getElementById('view-incoming');

  var callName = document.getElementById('callName');
  var callStatus = document.getElementById('callStatus');
  var callInitial = document.getElementById('callInitial');
  var callAvatar = document.getElementById('callAvatar');
  var callerBlock = document.getElementById('callerBlock');
  var callActions = document.getElementById('callActions');

  var toastEl = document.getElementById('toast');
  var toastTimer = null;

  function showToast(msg){
    clearTimeout(toastTimer);
    toastEl.textContent = msg;
    toastEl.classList.add('show');
    toastTimer = setTimeout(function(){ toastEl.classList.remove('show'); }, 1800);
  }

  /* ---------- keypad build ---------- */
  var keys = [
    ["1",""],["2","ABC"],["3","DEF"],
    ["4","GHI"],["5","JKL"],["6","MNO"],
    ["7","PQRS"],["8","TUV"],["9","WXYZ"],
    ["*",""],["0","+"],["#",""]
  ];
  keys.forEach(function(k, idx){
    var btn = document.createElement('button');
    btn.className = 'key';
    btn.style.animationDelay = (idx*32)+'ms';
    btn.innerHTML = '<span class="n">'+k[0]+'</span>'+(k[1]?'<span class="l">'+k[1]+'</span>':'<span class="l">&nbsp;</span>');
    btn.dataset.val = k[0];
    keypad.appendChild(btn);

    var holdTimer = null, longFired = false;
    btn.addEventListener('pointerdown', function(e){
      longFired = false;
      ripple(btn, e);
      if(k[0] === "0"){
        holdTimer = setTimeout(function(){
          longFired = true;
          appendDigit("+");
          navigatorVibrate();
        }, 480);
      }
    });
    btn.addEventListener('pointerup', function(){
      clearTimeout(holdTimer);
      if(!longFired){ appendDigit(k[0]); navigatorVibrate(); }
    });
    btn.addEventListener('pointerleave', function(){ clearTimeout(holdTimer); });
  });

  function ripple(btn, e){
    var r = document.createElement('span');
    r.className = 'ripple';
    var rect = btn.getBoundingClientRect();
    var size = rect.width * 1.3;
    r.style.width = r.style.height = size + 'px';
    var x = (e.clientX || rect.left+rect.width/2) - rect.left - size/2;
    var y = (e.clientY || rect.top+rect.height/2) - rect.top - size/2;
    r.style.left = x+'px'; r.style.top = y+'px';
    btn.appendChild(r);
    requestAnimationFrame(function(){ r.classList.add('go'); });
    setTimeout(function(){ r.remove(); }, 520);
  }

  function navigatorVibrate(){
    if(navigator.vibrate){ try{ navigator.vibrate(8); }catch(e){} }
  }

  /* generic press feedback: ripple + spring bounce, for round action buttons */
  function pressFX(el, e){
    var r = document.createElement('span');
    r.className = 'fx-ripple';
    var rect = el.getBoundingClientRect();
    var size = Math.max(rect.width, rect.height) * 1.35;
    r.style.width = r.style.height = size + 'px';
    var cx = (e && e.clientX ? e.clientX : rect.left+rect.width/2) - rect.left - size/2;
    var cy = (e && e.clientY ? e.clientY : rect.top+rect.height/2) - rect.top - size/2;
    r.style.left = cx+'px'; r.style.top = cy+'px';
    el.appendChild(r);
    requestAnimationFrame(function(){ r.classList.add('go'); });
    setTimeout(function(){ r.remove(); }, 560);

    el.classList.remove('fx-bounce');
    void el.offsetWidth; /* restart animation */
    el.classList.add('fx-bounce');
    setTimeout(function(){ el.classList.remove('fx-bounce'); }, 440);
  }

  function groupPositions(raw){
    // trả về danh sách vị trí (sau ký tự thứ n) cần chèn khoảng trắng, kiểu số VN: 0xx xxx xxxx
    var digitsOnly = raw.replace(/^\+/, '');
    var offset = raw.length - digitsOnly.length; // 1 nếu có dấu +
    var pos = [];
    if(digitsOnly.length > 3) pos.push(3 + offset);
    if(digitsOnly.length > 6) pos.push(6 + offset);
    else if(digitsOnly.length > 3 && digitsOnly.length <= 6) { /* nothing extra */ }
    return pos;
  }

  var wasEmptyNumber = true;
  function renderNumber(){
    if(number.length === 0){
      numDisplay.classList.add('empty');
      numDisplay.innerHTML = '';
      numDisplay.style.fontSize = '';
      delBtn.classList.remove('show');
      callBtn.classList.add('disabled');
      wasEmptyNumber = true;
      return;
    }
    numDisplay.classList.remove('empty');
    delBtn.classList.add('show');
    callBtn.classList.remove('disabled');

    if(wasEmptyNumber){
      // nút gọi "tỉnh dậy" nảy nhẹ khi số đầu tiên vừa được gõ
      callBtn.classList.remove('fx-bounce');
      void callBtn.offsetWidth;
      callBtn.classList.add('fx-bounce');
      setTimeout(function(){ callBtn.classList.remove('fx-bounce'); }, 440);
    }
    wasEmptyNumber = false;

    var breaks = groupPositions(number);
    var html = '';
    for(var i=0;i<number.length;i++){
      html += '<span class="digit">'+number[i]+'</span>';
      if(breaks.indexOf(i+1) !== -1 && i+1 < number.length){
        html += '<span class="sp"></span>';
      }
    }
    html += '<span class="caret"></span>';
    numDisplay.innerHTML = html;

    // co nhỏ chữ dần khi số dài ra, giống bàn phím quay số thật
    var len = number.length;
    var size = len <= 10 ? 40 : len <= 13 ? 34 : len <= 16 ? 29 : 24;
    numDisplay.style.fontSize = size + 'px';

    numScroll.scrollLeft = numScroll.scrollWidth;
  }

  function appendDigit(d){
    if(number.length >= 24) return;
    number += d;
    renderNumber();
  }

  delBtn.addEventListener('pointerdown', function(e){
    if(!number) return;
    pressFX(delBtn, e);
    number = number.slice(0, -1);
    renderNumber();
    navigatorVibrate();
  });
  var delHold = null, clearing = false;
  delBtn.addEventListener('pointerdown', function(){
    delHold = setTimeout(function(){
      if(!number || clearing) return;
      clearing = true;
      navigatorVibrate();
      var spans = numDisplay.querySelectorAll('.digit');
      spans.forEach(function(s, i){
        s.style.animationDelay = (i*14)+'ms';
        s.classList.add('fly');
      });
      setTimeout(function(){
        number = "";
        renderNumber();
        clearing = false;
      }, 280);
    }, 550);
  });
  delBtn.addEventListener('pointerup', function(){ clearTimeout(delHold); });
  delBtn.addEventListener('pointerleave', function(){ clearTimeout(delHold); });

  renderNumber();

  /* ---------- outgoing call flow ---------- */
  function initials(str){
    if(!str) return "#";
    var t = str.trim();
    if(/^[+\d\s()-]+$/.test(t)) return "#";
    var parts = t.split(/\s+/);
    return (parts[0][0] + (parts[1]? parts[1][0] : '')).toUpperCase();
  }

  /* ================= MAZI SIM: token cho cuoc goi ================= */
  /* So MAZI SIM se hien thi phu thuoc "danh tinh" hien tai cua may: neu may
     vua duoc mo khoa bang ma quan tri (081120) thi la SIM cua Nha phat trien
     (nhieu token co san de test), con lai la SIM cua nguoi dung thong thuong
     (mac dinh 0 token). Trang OS cha (khong cung document voi iframe nay) ghi
     co "dang o che do admin hay khong" vao localStorage moi khi mo khoa thanh
     cong, iframe nay doc lai truc tiep (cung origin nen dung chung storage). */
  var MAZI_ADMIN_NUMBER = '0976646035';
  var MAZI_USER_NUMBER  = '0899174526';
  var MAZI_KEY_ADMIN = 'magicos_mazi_balance_admin';
  var MAZI_KEY_USER  = 'magicos_mazi_balance_user';
  var MAZI_USSD_CODE = '*101#';
  var TOKEN_PER_SECOND = 1.3;
  var TOKEN_TICK_MS = 200;

  function isAdminIdentity(){
    try { return localStorage.getItem('magicos_admin_mode') === '1'; } catch(e){ return false; }
  }
  function maziIdentity(){
    return isAdminIdentity()
      ? { number: MAZI_ADMIN_NUMBER, key: MAZI_KEY_ADMIN, def: 200000 }
      : { number: MAZI_USER_NUMBER,  key: MAZI_KEY_USER,  def: 0 };
  }
  function getMaziBalance(){
    var id = maziIdentity();
    try {
      var raw = localStorage.getItem(id.key);
      if (raw === null) { localStorage.setItem(id.key, String(id.def)); return id.def; }
      var v = parseFloat(raw);
      return isNaN(v) ? id.def : v;
    } catch(e){ return id.def; }
  }
  function setMaziBalance(v){
    var id = maziIdentity();
    var nv = Math.max(0, v);
    try { localStorage.setItem(id.key, String(nv)); } catch(e){}
    return nv;
  }
  function formatMaziTokens(v){
    var r = Math.round(v * 10) / 10;
    var isInt = Math.abs(r - Math.round(r)) < 0.001;
    var s = isInt ? String(Math.round(r)) : r.toFixed(1);
    var parts = s.split('.');
    parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ',');
    return parts.join('.');
  }

  /* ---------- man hinh MAZI SIM (goi *101#) ---------- */
  var maziLoadingEl = document.getElementById('maziLoading');
  var maziOverlayEl = document.getElementById('maziOverlay');
  var maziPhoneEl = document.getElementById('maziPhoneNumber');
  var maziBalanceEl = document.getElementById('maziBalanceValue');
  var maziConfirmBtn = document.getElementById('maziConfirmBtn');
  var maziCancelBtn = document.getElementById('maziCancelBtn');
  var maziLoadingTimer = null;

  function runMaziUssd(){
    navigatorVibrate();
    clearTimeout(maziLoadingTimer);
    maziLoadingEl.classList.add('show');
    maziLoadingTimer = setTimeout(function(){
      maziLoadingEl.classList.remove('show');
      showMaziCard();
    }, 1100);
  }
  function showMaziCard(){
    var id = maziIdentity();
    maziPhoneEl.textContent = id.number;
    maziBalanceEl.textContent = formatMaziTokens(getMaziBalance());
    maziOverlayEl.classList.add('show');
    if (navigator.vibrate) { try{ navigator.vibrate(12); }catch(e){} }
  }
  function hideMaziCard(){
    maziOverlayEl.classList.remove('show');
    setTimeout(function(){
      number = "";
      renderNumber();
    }, 260);
  }
  if (maziConfirmBtn) maziConfirmBtn.addEventListener('pointerdown', function(e){
    pressFX(maziConfirmBtn, e);
    hideMaziCard();
    showToast('Đã cập nhật thông tin MAZI SIM');
  });
  if (maziCancelBtn) maziCancelBtn.addEventListener('pointerdown', function(e){
    pressFX(maziCancelBtn, e);
    hideMaziCard();
  });

  /* ---------- tinh phi cuoc goi theo token (1.3 token/giay) ---------- */
  var tokenMeterInterval = null;
  function startTokenMeter(){
    stopTokenMeter();
    var perTick = TOKEN_PER_SECOND * (TOKEN_TICK_MS / 1000);
    tokenMeterInterval = setInterval(function(){
      var bal = getMaziBalance();
      var next = bal - perTick;
      if (next <= 0) {
        setMaziBalance(0);
        forceEndCallInsufficientToken();
        return;
      }
      setMaziBalance(next);
    }, TOKEN_TICK_MS);
  }
  function stopTokenMeter(){
    if (tokenMeterInterval) { clearInterval(tokenMeterInterval); tokenMeterInterval = null; }
  }
  function notifyTokenInsufficient(){
    try{ window.parent.postMessage({source:'magicos-phone', type:'tokenNotice', text:'Token Không Đủ'}, '*'); }catch(e){}
  }
  function forceEndCallInsufficientToken(){
    if (navigator.vibrate) { try{ navigator.vibrate([30,40,30,40,60]); }catch(e){} }
    notifyTokenInsufficient();
    endCall(null);
  }

  var ringDotsTimer = null;
  function startRingDots(base){
    var n = 0;
    callStatus.textContent = base;
    clearInterval(ringDotsTimer);
    ringDotsTimer = setInterval(function(){
      n = (n+1) % 4;
      callStatus.textContent = base + '.'.repeat(n) + '\u00A0'.repeat(3-n);
    }, 420);
  }
  function stopRingDots(){ clearInterval(ringDotsTimer); ringDotsTimer = null; }

  function startOutgoingCall(){
    currentCallerName = number || "Không xác định";
    callName.textContent = currentCallerName;
    callInitial.textContent = initials(currentCallerName);
    startRingDots("Đang đổ chuông");
    callStatus.classList.add('fx');
    callerBlock.classList.remove('connected');
    callActions.classList.remove('show');
    resetActionStates();

    viewKeypad.classList.add('pushed');
    viewCall.classList.add('show');
    // Man hinh cuoc goi nen toi (den) - doi status bar/home indicator sang
    // mau sang de khong bi "den tren den" (khong doc duoc). Man hinh nay chay
    // trong iframe rieng nen phai bao qua postMessage cho trang cha xu ly.
    notifyCallScreenTheme(true);

    clearTimeout(ringTimeout);
    ringTimeout = setTimeout(connectCall, 2600);
  }

  function notifyIsland(state, name){
    try{ window.parent.postMessage({source:'magicos-phone', type:'call', state:state, name:name || ''}, '*'); }catch(e){}
  }
  // Bao cho trang OS cha (khong cung window) biet man hinh cuoc goi dang hien
  // (nen toi -> can status bar/home indicator mau sang) hay da an (tra ve
  // man hinh ban phim nen sang -> can status bar mau toi).
  function notifyCallScreenTheme(isDark){
    try{ window.parent.postMessage({source:'magicos-phone', type:'callScreenTheme', dark: !!isDark}, '*'); }catch(e){}
  }

  function connectCall(){
    // Khong du token ngay tu luc bat dau -> may cham dinh mang cua MAZI SIM
    // tu choi ket noi, cat cuoc goi ngay lap tuc va bao "Token Không Đủ".
    if (getMaziBalance() <= 0) {
      forceEndCallInsufficientToken();
      return;
    }
    notifyIsland('connected', currentCallerName);
    stopRingDots();
    callStatus.classList.remove('fx');
    callerBlock.classList.add('connected');
    callActions.classList.add('show');
    callAvatar.classList.remove('burst');
    void callAvatar.offsetWidth;
    callAvatar.classList.add('burst');
    setTimeout(function(){ callAvatar.classList.remove('burst'); }, 720);
    callSeconds = 0;
    updateTimer();
    clearInterval(callTimer);
    callTimer = setInterval(function(){ callSeconds++; updateTimer(); }, 1000);
    startTokenMeter();
  }

  function updateTimer(){
    var m = Math.floor(callSeconds/60), s = callSeconds%60;
    callStatus.textContent = (m<10?"0"+m:m)+":"+(s<10?"0"+s:s);
  }

  function endCall(msg){
    notifyIsland('ended');
    clearTimeout(ringTimeout);
    clearInterval(callTimer);
    stopTokenMeter();
    stopRingDots();
    viewCall.classList.remove('show');
    viewKeypad.classList.remove('pushed');
    // Ve lai man hinh ban phim (nen sang) - tra status bar/home indicator ve
    // mau toi nhu binh thuong cua app Phone.
    notifyCallScreenTheme(false);
    setTimeout(function(){
      number = "";
      renderNumber();
    }, 300);
    if(msg) showToast(msg);
  }

  function resetActionStates(){
    ['actMute','actKeypad','actSpeaker'].forEach(function(id){
      document.getElementById(id).classList.remove('active');
    });
  }
  ['actMute','actKeypad','actSpeaker'].forEach(function(id){
    var wrap = document.getElementById(id);
    var circ = wrap.querySelector('.circ');
    wrap.addEventListener('pointerdown', function(e){
      wrap.classList.toggle('active');
      pressFX(circ, e);
      navigatorVibrate();
    });
  });

  callBtn.addEventListener('pointerdown', function(e){
    if(callBtn.classList.contains('disabled')) return;
    pressFX(callBtn, e);
    if (number === MAZI_USSD_CODE) {
      runMaziUssd();
      return;
    }
    startOutgoingCall();
  });
  var endBtnEl = document.getElementById('endBtn');
  endBtnEl.addEventListener('pointerdown', function(e){
    pressFX(endBtnEl, e);
    endCall("Đã kết thúc cuộc gọi");
  });

  /* ---------- incoming call flow ---------- */
  var demoNames = ["Minh Anh","Gia Bảo","Thu Hà","Quốc Huy","Bảo Ngọc"];
  var demoNumbers = ["+84 91 234 5678","+84 98 765 4321","+84 90 111 2233","+84 77 456 7890"];

  document.getElementById('simIncoming').addEventListener('pointerdown', function(){
    triggerIncoming();
  });

  function triggerIncoming(forcedLabel){
    var useName = Math.random() > 0.35;
    var label = forcedLabel || (useName ? demoNames[Math.floor(Math.random()*demoNames.length)]
                         : demoNumbers[Math.floor(Math.random()*demoNumbers.length)]);
    document.getElementById('inName').textContent = label;
    document.getElementById('inSub').textContent = useName ? "di động · Việt Nam" : "Việt Nam";
    document.getElementById('inAvatar').textContent = initials(label);
    currentCallerName = label;
    notifyIsland('incoming', label);

    viewIncoming.classList.add('show');
    // Man hinh cuoc goi den cung nen toi - doi status bar/home indicator sang mau sang.
    notifyCallScreenTheme(true);
  }

  function dismissIncoming(){
    viewIncoming.classList.remove('show');
  }

  var declineBtnEl = document.getElementById('declineBtn');
  function declineIncomingCall(e){
    pressFX(declineBtnEl, e);
    dismissIncoming();
    // Tu choi -> quay lai ban phim (nen sang) -> tra status bar ve mau toi.
    notifyCallScreenTheme(false);
    notifyIsland('declined');
    showToast("Đã từ chối cuộc gọi");
  }
  declineBtnEl.addEventListener('pointerdown', function(e){ declineIncomingCall(e); });

  var acceptBtnEl = document.getElementById('acceptBtn');
  function acceptIncomingCall(e){
    pressFX(acceptBtnEl, e);
    dismissIncoming();
    callName.textContent = currentCallerName;
    callInitial.textContent = initials(currentCallerName);
    startRingDots("Đang kết nối");
    callStatus.classList.add('fx');
    callerBlock.classList.remove('connected');
    callActions.classList.remove('show');
    resetActionStates();

    viewKeypad.classList.add('pushed');
    viewCall.classList.add('show');
    notifyCallScreenTheme(true);

    clearTimeout(ringTimeout);
    ringTimeout = setTimeout(connectCall, 900);
  }
  acceptBtnEl.addEventListener('pointerdown', function(e){ acceptIncomingCall(e); });

  /* ---------- nhan lenh Nghe / Tu choi ban tu 2 nut ngay tren Dynamic Island ---------- */
  window.addEventListener('message', function(ev){
    var d = ev && ev.data;
    if (!d || d.source !== 'magicos-island') return;
    if (d.action === 'answer') {
      if (viewIncoming.classList.contains('show')) acceptIncomingCall(null);
    } else if (d.action === 'decline') {
      if (viewIncoming.classList.contains('show')) declineIncomingCall(null);
    } else if (d.action === 'end') {
      if (viewCall.classList.contains('show')) endCall("Đã kết thúc cuộc gọi");
    } else if (d.action === 'trigger_incoming') {
      // Goi den "gia lap" tu Admin: phai chay qua dung luong trinh cuoc goi
      // den THUC su cua app Dien thoai (khong chi ve UI tren Dynamic Island),
      // de khi nguoi dung bam Nghe no thuc su ket noi va mo dung giao dien
      // cuoc goi, thay vi tu tat ma khong lam gi ca.
      if (!viewIncoming.classList.contains('show') && !viewCall.classList.contains('show')) {
        triggerIncoming(d.name);
      }
    }
  });

})();
</script>
</body>
</html>
'''

class PhoneRequestHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.split("?", 1)[0] == "/api/server-state":
            self._send_json(200, {"open": SERVER_OPEN})
            return
        if WALLPAPER_PATH and self.path == WALLPAPER_URL_PATH:
            ctype = mimetypes.guess_type(WALLPAPER_PATH)[0] or "application/octet-stream"
            with open(WALLPAPER_PATH, "rb") as img_file:
                img_bytes = img_file.read()
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(img_bytes)))
            self.end_headers()
            self.wfile.write(img_bytes)
            return
        if self.path == "/phone-app.html":
            phone_bytes = PHONE_APP_HTML.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(phone_bytes)))
            self.end_headers()
            self.wfile.write(phone_bytes)
            return
        html_bytes = HTML_PAGE.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(html_bytes)))
        self.end_headers()
        self.wfile.write(html_bytes)

    def do_POST(self):
        global SERVER_OPEN
        path = self.path.split("?", 1)[0]
        if path not in ("/api/unlock", "/api/server-state"):
            self._send_json(404, {"error": "not_found"})
            return
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if not 0 < size <= 2048:
                raise ValueError()
            data = json.loads(self.rfile.read(size))
            if not isinstance(data, dict):
                raise ValueError()
        except (ValueError, UnicodeError):
            self._send_json(400, {"error": "invalid_request"})
            return
        now = time.monotonic()
        for token, expiry in list(ADMIN_SESSIONS.items()):
            if expiry <= now:
                ADMIN_SESSIONS.pop(token, None)
        if path == "/api/unlock":
            code = data.get("passcode")
            if code not in ("000000", "081120"):
                self._send_json(401, {"error": "invalid_passcode"})
                return
            allowed = code == "081120" or SERVER_OPEN
            result = {"allowed": allowed, "open": SERVER_OPEN}
            if code == "081120":
                token = secrets.token_urlsafe(32)
                ADMIN_SESSIONS[token] = now + 86400
                result["admin_token"] = token
            self._send_json(200 if allowed else 503, result)
            return
        token = self.headers.get("X-Admin-Token", "")
        if ADMIN_SESSIONS.get(token, 0) <= now:
            self._send_json(403, {"error": "admin_required"})
            return
        if type(data.get("open")) is not bool:
            self._send_json(400, {"error": "invalid_state"})
            return
        try:
            temp_path = SERVER_STATE_FILE + ".tmp"
            with open(temp_path, "w", encoding="utf-8") as state_file:
                json.dump({"open": data["open"]}, state_file)
            os.replace(temp_path, SERVER_STATE_FILE)
        except OSError:
            self._send_json(500, {"error": "state_save_failed"})
            return
        SERVER_OPEN = data["open"]
        self._send_json(200, {"open": SERVER_OPEN})

    def _send_json(self, status, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        pass

class ReusableTCPServer(socketserver.TCPServer):
    allow_reuse_address = True

def main():
    global HTML_PAGE
    if WALLPAPER_PATH:
        print(f"Dung anh nen: {WALLPAPER_PATH}")
    else:
        print("Khong tim thay anh nen trong thu muc nay (jpg/jpeg/png/webp) - dung mau nen mac dinh.")
    penalty_port = start_penalty_server()
    HTML_PAGE = HTML_PAGE.replace("__PENALTY_AVAILABLE__", "true" if penalty_port else "false")
    HTML_PAGE = HTML_PAGE.replace("__PENALTY_URL__", f"http://127.0.0.1:{penalty_port}/" if penalty_port else "")
    port = PORT
    httpd = None
    for attempt in range(10):
        try:
            httpd = ReusableTCPServer(("127.0.0.1", port), PhoneRequestHandler)
            break
        except OSError:
            print(f"Cong {port} dang duoc su dung, thu cong {port + 1}...")
            port += 1
    if httpd is None:
        print("Khong tim duoc cong trong de chay server. Hay dong cac tien trinh python app.py cu roi thu lai.")
        return
    with httpd:
        url = f"http://127.0.0.1:{port}"
        print(f"Dang chay tai {url} (nhan Ctrl+C de dung)")
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nDa dung server.")

if __name__ == "__main__":
    main()
