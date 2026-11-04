# MinhQuan BotCore — v1.2

`app/src/main/java/com/txanalyzer/bot/BotCore.java` là bộ ra quyết định có điều kiện an toàn theo từng Observation. `BotSession.java` giữ công tắc session. Test JVM: `tests/BotCoreTest.java`.

**Quan trọng:** Không có nguồn Observation từ game thật, không có thị giác máy tính. AutoControl hiện là trình gửi gesture thử nghiệm (đánh và di chuyển) trên game được nhận diện, **không kết nối với BotCore** và **không tự chơi toàn trận**. Tọa độ cử chỉ tương đối có thể không khớp với HUD của bạn.

AutoControl v1.2 không từ chối khi không nhận ra game tại thời điểm nhấn; nó chuyển sang ON/chờ và chỉ gửi gesture trong cửa sổ game ngang. ON không có nghĩa đã phát hiện game. Android giữ quyền Trợ năng sau khi cấp trừ khi người dùng hoặc hệ thống thu hồi/tắt dịch vụ. Giới hạn 15 phút nhằm tránh điều khiển vô thời hạn.

Các phần cần phát triển để bot độc lập thật: màn hình capture được người dùng đồng ý, trích xuất HUD, nhận diện phase/trận, kiểm tra độ tin cậy và kết nối Observation->Decision->Action, kèm hệ thống dừng khẩn cấp và đánh giá thực địa trên chế độ luyện tập.
