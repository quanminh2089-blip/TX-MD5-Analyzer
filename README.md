# OniRoai v1.1 — Android optimization trial

- Tên ứng dụng và nhãn Android: OniRoai.
- Giữ màn hình nhập key MinhQuan và chuyển thẳng vào game.
- Avatar bong bóng lấy từ ảnh người dùng gửi: crop cận cảnh hơn, tăng sáng và tương phản, tăng kích thước 58 lên 76 px.
- Giữ menu ESP ĐỊCH / AIM ĐẦU chỉ để minh họa, không hoạt động.
- Giữ renderer GL Compatibility, giảm render scale 3D còn 70%, bóng directional shadow 2048 -> 1024, tắt MSAA và giảm lọc anisotropic.
- APK dự kiến: output/OniRoai-v1.1.apk.

**Chưa đo FPS thực tế và chưa xác nhận APK build thành công.** 60 FPS không được bảo đảm; cần kiểm tra GPU/CPU profiler trên máy. Các tối ưu hiện tại là bước đầu, chưa bao gồm LOD/occlusion/AI profiling chuyên sâu.
