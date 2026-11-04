# MAGICOS Native — Giai đoạn 1 (Java Android, không HTML/WebView/Python runtime)

Nguồn tham chiếu: file `magicos.py` do người dùng cung cấp (7.684 dòng). Đây là **bản chuyển đổi giai đoạn 1**, KHÔNG phải bản chuyển đổi toàn bộ và chưa tương đương hình ảnh/logic với nguyên bản.

## Đã hoạt động trong mã nguồn
- Splash avatar xoay ~2,6 giây, hộp nhập key `FreeKey_MinhQuan` (key cục bộ, không có bảo mật máy chủ).
- Màn hình khóa với đồng hồ, vuốt lên mở; màn hình chính dạng icon native, thanh trạng thái và dynamic island trang trí.
- Trung tâm điều khiển dạng UI mô phỏng (không tự ý thay đổi Wi-Fi/Bluetooth thật).
- Cài đặt, khóa màn hình, ghi chú lưu cục bộ, máy tính phép tính cơ bản, bàn phím điện thoại mô phỏng, MagicBank hiển thị xu mô phỏng.
- Icon Penalty, MAGICAI, Cửa Hàng có màn hình placeholder **được ghi rõ chưa hoàn tất**.

## Chưa chuyển đổi
- Engine trò chơi Penalty/Goalkeeper gốc, tài khoản Flask, MAGICAI backend, hệ thống ngân hàng/cửa hàng/điện thoại đầy đủ, admin, nhiều animation chi tiết, động tác đa nhiệm, chức năng server Python.
- Giao diện chưa bảo đảm giống 100% bản HTML gốc. Không chứa WebView, HTML, Python hoặc quyền overlay/Accessibility/bot.

## Build
Push dự án mới lên GitHub (repo riêng khuyến nghị), workflow `.github/workflows/android-build.yml` chạy Gradle 8.9 + Java 17, tạo artifact `MinhQuan-debug`. Không yêu cầu Termux chạy Android Studio. Chưa chạy APK trên thiết bị thật.

## Giai đoạn kế tiếp
(2) Native lock/home/dock/dynamic island/control center theo layout gốc; (3) app điện thoại, MagicBank, Store; (4) MAGICAI, admin và dữ liệu; (5) port game Penalty từ canvas JS sang custom Canvas Android, xử lý vòng lặp và hoạt ảnh; (6) kiểm thử hồi quy, tối ưu khung hình, hoàn thiện.
