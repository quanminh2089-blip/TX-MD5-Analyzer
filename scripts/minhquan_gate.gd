extends Control
## MinhQuan login gate. Offline UI only; credentials in client are NOT secure.
const FREE_KEY := "FreeKey_MinhQuan"
const USER_NAME := "MinhQuan08"
const PASSWORD := "08112008ok"
const BG := Color("070d19")
const PANEL := Color("17253d")
const MINT := Color("36dfaa")
var phase := "loading"
var timer_seconds := 0
var counter: Label
var key_input: LineEdit
var user_input: LineEdit
var password_input: LineEdit
var message: Label
var body: VBoxContainer

func _ready() -> void:
    theme = Theme.new()
    var backdrop := ColorRect.new()
    backdrop.color = BG
    backdrop.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
    add_child(backdrop)
    var center := CenterContainer.new()
    center.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
    add_child(center)
    body = VBoxContainer.new()
    body.custom_minimum_size = Vector2(440, 0)
    body.add_theme_constant_override("separation", 18)
    center.add_child(body)
    _show_loading()

func _clear() -> void:
    for node in body.get_children():
        body.remove_child(node)
        node.queue_free()

func _label(value: String, font_size: int = 22, tint: Color = Color.WHITE) -> Label:
    var l := Label.new()
    l.text = value
    l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
    l.add_theme_font_size_override("font_size", font_size)
    l.add_theme_color_override("font_color", tint)
    l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
    return l

func _avatar(size_px: int = 140) -> TextureRect:
    var img := TextureRect.new()
    img.texture = load("res://assets/oniroai/avatar.png")
    img.custom_minimum_size = Vector2(size_px, size_px)
    img.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
    img.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
    return img

func _button(caption: String, handler: Callable) -> Button:
    var b := Button.new()
    b.text = caption
    b.custom_minimum_size.y = 60
    b.add_theme_font_size_override("font_size", 21)
    b.pressed.connect(handler)
    return b

func _input(hint: String, secret: bool = false) -> LineEdit:
    var field := LineEdit.new()
    field.placeholder_text = hint
    field.secret = secret
    field.custom_minimum_size.y = 58
    field.add_theme_font_size_override("font_size", 20)
    return field

func _show_loading() -> void:
    phase = "loading"
    _clear()
    body.add_child(_avatar(100))
    body.add_child(_label("Loading data from Server...", 19))
    # Cosmetic splash only: no server connection is attempted.
    await get_tree().create_timer(2.0).timeout
    if is_inside_tree() and phase == "loading":
        _show_key()

func _show_key() -> void:
    phase = "key"
    _clear()
    body.add_child(_label("MinhQuan'z", 38))
    body.add_child(_label("Bấm Vào Nút Get Key Để Lấy Key Free", 18))
    counter = _label("-1s", 19)
    body.add_child(counter)
    key_input = _input("Nhập key MinhQuan")
    body.add_child(key_input)
    body.add_child(_button("Get Key", func():
        key_input.text = FREE_KEY
    ))
    body.add_child(_button("OK", _check_key))
    message = _label("", 18, Color("ff8585"))
    body.add_child(message)
    timer_seconds = 0
    _tick_key()

func _tick_key() -> void:
    while is_inside_tree() and phase == "key":
        timer_seconds += 1
        counter.text = "-%ds" % timer_seconds
        await get_tree().create_timer(1.0).timeout

func _check_key() -> void:
    if key_input.text.strip_edges() != FREE_KEY:
        message.text = "Key không đúng"
        return
    _show_login()

func _show_login() -> void:
    phase = "login"
    _clear()
    body.add_child(_avatar(175))
    body.add_child(_label("MINHQUAN", 48))
    body.add_child(_label("Đăng nhập tài khoản", 28))
    user_input = _input("Tên người dùng")
    body.add_child(user_input)
    password_input = _input("Mật khẩu", true)
    body.add_child(password_input)
    body.add_child(_button("ĐĂNG NHẬP", _check_account))
    message = _label("", 18, Color("ff8585"))
    body.add_child(message)
    body.add_child(_label("Admin: Nguyễn Minh Quân", 16, MINT))
    body.add_child(_label("Zalo: 0899174526", 16, MINT))
    body.add_child(_label("Telegram: @mquan08", 16, MINT))

func _check_account() -> void:
    if user_input.text.strip_edges() != USER_NAME or password_input.text != PASSWORD:
        message.text = "Sai tên người dùng hoặc mật khẩu"
        return
    phase = "game"
    # Real OniRoai scene and assets; no separate app launch.
    get_tree().change_scene_to_file("res://scenes/boot.tscn")
