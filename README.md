# MinhQuan v1.2 — Khôi phục Splash/Key + Bong bóng OFF/ON

Android 15, không root; mã nguồn Java Android native, build APK bằng GitHub Actions.

## Giao diện
- Khôi phục splash cũ v0.7: hộp nhỏ nền tối, avatar xoay khoảng 3 giây.
- Khôi phục hộp nhập key nhỏ `MinhQuan'z`, có Get Key và OK. Key thử nghiệm: `FreeKey_MinhQuan`. Đây là key cục bộ, không phải hệ thống bản quyền bảo mật.
- Không còn Matrix Terminal, màn hình tên tài khoản/mật khẩu hay bảng ESP demo.
- Key đúng -> nếu thiếu quyền *Hiển thị trên ứng dụng khác*, chuyển trực tiếp đến trang quyền Android -> khởi tạo lớp phủ -> thử mở Liên Quân VN.
- Menu nổi chỉ gồm **bong bóng tròn 68dp**: `OFF` đỏ và `ON` xanh lá, có thể kéo thả.
- Để người dùng luôn nhìn thấy giao diện key như v0.7, key yêu cầu lại ở mỗi lần mở mới ứng dụng; việc cấp quyền Trợ năng không cần làm lại nếu Android vẫn giữ quyền.

## Nút ON / Trợ năng
- Nút ON dùng Accessibility Service `MinhQuan điều khiển` để *thử nghiệm điều khiển cử chỉ*.
- Nếu dịch vụ chưa được kết nối: mở trang Trợ năng. Chỉ cần bật một lần; lần sau không đưa vào cài đặt nữa nếu dịch vụ còn chạy.
- Nếu công tắc Android đã bật nhưng dịch vụ không kết nối (ví dụ Android báo dịch vụ bất thường), ứng dụng hiển thị thông báo cần tắt/bật lại dịch vụ; ứng dụng không thể tự bật quyền Trợ năng.
- Nút ON vẫn có thể kích hoạt ở chế độ **chờ game**. Nó chỉ bắn cử chỉ khi dịch vụ nhận diện Liên Quân VN đang ở tiền cảnh và màn hình ngang. Nếu không nhận ra game, ON không điều khiển gì.
- Khi thấy game, hệ thống thử tap nút đánh và vuốt joystick theo tọa độ mặc định. Bấm OFF để dừng; cũng tự tắt khi mất kết nối hoặc sau tối đa **15 phút**.
- Android Accessibility và bản game cụ thể có thể không cung cấp sự kiện cửa sổ hoặc từ chối cử chỉ; chưa thể bảo đảm nút ON làm nhân vật di chuyển.

## Chưa có
- **Không có bot AI tự chơi toàn trận.** Chưa có MediaProjection, nhận diện màn hình, phân tích làn đường, kỹ năng, định tuyến, mua đồ, giao tranh chiến thuật hoặc nguồn dữ liệu tướng ẩn.
- `BotCore` vẫn là logic quyết định có thể kiểm thử bằng đầu vào; chưa được cấp quan sát từ trận đấu thật.
- Có rủi ro nhấn sai vị trí nếu bố cục HUD khác, hoặc vi phạm quy tắc chống gian lận của game. Chỉ thử trong chế độ luyện tập.

## Quy trình sử dụng
1. Mở APK -> đợi avatar xoay -> nhập key trong hộp MinhQuan'z.
2. Cấp Hiển thị trên ứng dụng khác nếu Android hỏi.
3. Vào chế độ luyện tập Liên Quân.
4. Nếu nhấn OFF lần đầu và bị đưa vào cài đặt Trợ năng, bật `MinhQuan điều khiển`, quay lại game và nhấn OFF lần nữa để thành ON.
5. Bong bóng ON màu xanh khi đã bật; nếu chưa nhận ra game, ON chờ mà không tự chạm.
6. Nhấn ON thành OFF để dừng ngay.

## Build
- Project AGP 8.7.3, Gradle 8.9, Java 17, compileSdk/targetSdk 35, minSdk 26.
- Push lên `main`; vào GitHub -> Actions -> Build Android APK -> tải `MinhQuan-debug` trong Artifacts.
- Đây là mã nguồn ZIP, **không phải APK**. Chưa thể xác nhận APK hoạt động trên máy thật trong môi trường tạo file này.
- Có kiểm thử JVM BotCore và kiểm tra cú pháp Java + XML trong môi trường tạo file.
