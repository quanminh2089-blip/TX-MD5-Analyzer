extends CanvasLayer
## Overlay chỉ hiển thị menu minh họa, không có ESP / aim hoặc thao tác vào game.
const ACCENT := Color("#3ce5b0")
const DARK := Color("#101827")
var bubble: TextureButton
var popup: PanelContainer
var scrim: ColorRect
var activated := false
var dragging := false
var drag_offset := Vector2.ZERO

func _ready() -> void:
    layer = 120
    var canvas := Control.new()
    canvas.name = "OverlayRoot"
    canvas.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
    canvas.mouse_filter = Control.MOUSE_FILTER_IGNORE
    add_child(canvas)

    scrim = ColorRect.new()
    scrim.color = Color(0.0, 0.0, 0.0, 0.54)
    scrim.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
    scrim.mouse_filter = Control.MOUSE_FILTER_STOP
    scrim.hide()
    canvas.add_child(scrim)
    scrim.gui_input.connect(_on_scrim_input)

    bubble = TextureButton.new()
    bubble.name = "MinhQuanBubble"
    bubble.texture_normal = load("res://assets/minhquan/bubble_avatar.png")
    bubble.ignore_texture_size = true
    bubble.stretch_mode = TextureButton.STRETCH_KEEP_ASPECT_CENTERED
    bubble.custom_minimum_size = Vector2(76, 76)
    bubble.size = Vector2(76, 76)
    bubble.mouse_filter = Control.MOUSE_FILTER_STOP
    bubble.hide()
    canvas.add_child(bubble)
    bubble.pressed.connect(_open)

    popup = PanelContainer.new()
    popup.name = "MinhQuanMenu"
    popup.custom_minimum_size = Vector2(370, 0)
    popup.add_theme_stylebox_override("panel", _style(DARK, 22, Color("#35505b")))
    popup.hide()
    canvas.add_child(popup)
    var col := VBoxContainer.new()
    col.add_theme_constant_override("separation", 13)
    popup.add_child(col)
    var heading := HBoxContainer.new()
    col.add_child(heading)
    var title := _label("MINHQUAN  •  MENU", 22, ACCENT)
    title.size_flags_horizontal = Control.SIZE_EXPAND_FILL
    heading.add_child(title)
    var close := Button.new()
    close.text = "✕"
    close.custom_minimum_size = Vector2(38, 36)
    close.pressed.connect(_close)
    heading.add_child(close)
    var info := _label("BẢNG TÍNH NĂNG MINH HỌA", 13, Color("#9baaba"))
    col.add_child(info)
    _feature(col, "ESP ĐỊCH", "Chỉ hiển thị • Không hoạt động")
    _feature(col, "AIM ĐẦU", "Chỉ hiển thị • Không hoạt động")
    var foot := _label("Các tùy chọn trên không can thiệp vào game.", 12, Color("#8496a8"))
    col.add_child(foot)
    get_viewport().size_changed.connect(_reposition)
    _reposition()

func _style(fill: Color, radius: int, border: Color) -> StyleBoxFlat:
    var s := StyleBoxFlat.new()
    s.bg_color = fill
    s.set_corner_radius_all(radius)
    s.set_border_width_all(1)
    s.border_color = border
    s.content_margin_left = 22
    s.content_margin_right = 22
    s.content_margin_top = 18
    s.content_margin_bottom = 18
    return s

func _label(value: String, font_size: int, tint: Color) -> Label:
    var l := Label.new()
    l.text = value
    l.add_theme_font_size_override("font_size", font_size)
    l.add_theme_color_override("font_color", tint)
    return l

func _feature(parent: VBoxContainer, name: String, hint: String) -> void:
    var panel := PanelContainer.new()
    panel.add_theme_stylebox_override("panel", _style(Color("#1d2b3c"), 13, Color("#304456")))
    parent.add_child(panel)
    var row := HBoxContainer.new()
    row.add_theme_constant_override("separation", 10)
    panel.add_child(row)
    var dot := _label("◌", 26, ACCENT)
    row.add_child(dot)
    var texts := VBoxContainer.new()
    row.add_child(texts)
    texts.add_child(_label(name, 18, Color.WHITE))
    texts.add_child(_label(hint, 12, Color("#9baaba")))

func show_in_game() -> void:
    activated = true
    bubble.show()
    _reposition()

func _reposition() -> void:
    if not is_instance_valid(bubble) or not is_instance_valid(popup):
        return
    var viewport := get_viewport().get_visible_rect().size
    if not dragging:
        bubble.position = Vector2(maxf(12.0, viewport.x - 98.0), maxf(12.0, viewport.y * 0.37))
    popup.size = Vector2.ZERO
    popup.position = (viewport - Vector2(370, 330)) / 2.0

func _on_scrim_input(event: InputEvent) -> void:
    if event is InputEventMouseButton and event.pressed:
        _close()
    elif event is InputEventScreenTouch and event.pressed:
        _close()

func _open() -> void:
    if not activated:
        return
    scrim.show()
    popup.show()
    bubble.hide()
    _reposition()

func _close() -> void:
    popup.hide()
    scrim.hide()
    if activated:
        bubble.show()
