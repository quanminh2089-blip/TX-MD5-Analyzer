# OniRoai v1.2 — 500 HP + nghiêng trái/phải + chỉnh vị trí nút

Mã nguồn Godot 4.5.1 (Android ngang), phát triển từ OniRoai v1.1.

## Gameplay
- Người chơi **500/500 HP**, mỗi viên đạn NPC bắn trúng **-10 HP**.
- Cả bốn NPC đều có **500/500 HP**, mỗi viên đạn người chơi bắn trúng **-10 HP** (kể cả headshot; headshot vẫn hiện xác nhận bắn trúng).
- NPC chỉ chết và được tính hạ gục khi HP về 0; HP còn lại hiện trên đầu NPC **khi đã bị thương và đang phát hiện người chơi**; HP của người chơi được hiển thị góc trái kèm thanh máu.
- Máu người chơi hồi bằng túi cứu thương vẫn đúng giới hạn tối đa 500 HP (+45 nếu có túi).
- Mỗi ván reset đầy 500 HP. Rơi khỏi bản đồ vẫn bị loại ngay.
- Nâng đạn dự trữ người chơi lên **900** vì cần ít nhất 200 phát trúng để hạ bốn NPC.

## Nghiêng / Peek
- Hai nút **NGHIÊNG TRÁI** và **NGHIÊNG PHẢI** ở phía trên joystick (màn hình ngang).
- Chạm một lần để nghiêng, chạm cùng nút lần nữa để trở về tư thế thẳng; đổi phía bằng cách chạm nút đối diện.
- Camera dịch ngang khoảng 0.38m, nghiêng khoảng 11.5°; raycast chặn camera xuyên tường. Góc bắn đi theo camera.
- Dùng phím Q/E khi chơi bằng bàn phím.

## Chỉnh nút
1. Nhấn **Tạm dừng → THIẾT LẬP → NÚT BẤM**.
2. Chọn **TÙY CHỈNH VỊ TRÍ NÚT (KÉO & THẢ)**.
3. Chạm/giữ và kéo nút tới nơi thích hợp: di chuyển, nghiêng, bắn, ngắm, chạy, cúi, nhảy, tạm dừng; có thể kéo nút bắn trái khi đang bật.
4. Chọn **LƯU**. Tọa độ tương đối với vùng an toàn màn hình được lưu vào `user://settings.cfg` và giữ lại khi mở lại game. **HỦY** không lưu, **MẶC ĐỊNH** khôi phục bản xem trước.
5. **ĐẶT LẠI BỐ CỤC MOBILE** trong Thiết lập xóa bố cục đã lưu.

Tính năng ESP ĐỊCH và AIM ĐẦU tại bong bóng vẫn chỉ là giao diện minh họa, không hoạt động.

## Build
Cập nhật repo Godot và kích hoạt GitHub Actions `Build OniRoai APK`; artifact mong đợi là `OniRoai-v1.2-APK` chứa `OniRoai-v1.2.apk`.

**Giới hạn kiểm thử:** Các sửa đổi được kiểm tra trên mã nguồn và tính toàn vẹn ZIP; chưa chạy máy Android hay kiểm thử biên dịch Godot trong phiên này. Không cam kết APK build thành công hay FPS 60 cố định.
