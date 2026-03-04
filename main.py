import json
from pathlib import Path
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, ListView, ListItem, Label, Button, TabbedContent, TabPane
from textual.containers import Container, Horizontal, Vertical, Grid
from textual.screen import ModalScreen
from src.models.keyboard_config import KeyboardConfig
from src.keyboard_hid import KeyboardBackend

class KeycodeSelectModal(ModalScreen):
    """キーコードを選択するためのモーダル画面（カテゴリ別タブ表示）"""
    
    def __init__(self, keycodes):
        super().__init__()
        self.keycodes = keycodes
        # カテゴリごとにキーを分類
        self.categories = {
            "basic": [],
            "Media": [],
            "MACRO": [],
            "layers": [],
            "special": [],
            "Lighting": []
        }
        for kc in keycodes:
            cat = kc.get("category", "basic")
            if cat in self.categories:
                self.categories[cat].append(kc)
            else:
                # 定義外のカテゴリは special へ
                self.categories["special"].append(kc)

    def compose(self) -> ComposeResult:
        with Vertical(id="keycode-modal-container"):
            yield Label("Select New Keycode", id="modal-title")
            
            with TabbedContent():
                for cat_name, keys in self.categories.items():
                    # 表示用に整形 (basic -> Basic, layers -> Layers)
                    display_cat = cat_name if cat_name.isupper() else cat_name.capitalize()
                    with TabPane(display_cat):
                        with Container(classes="scroll-grid-container"):
                            with Container(classes="scroll-grid"):
                                for kc in keys:
                                    # ID は一意である必要があるため、名前とコードを組み合わせる
                                    # Textual の ID は制限（英数字、アンダースコア、ハイフンのみ）があるため特殊文字を置換
                                    safe_name = "".join([c if c.isalnum() or c in "_-" else "_" for c in kc['name']])
                                    btn_id = f"id_{kc['code']}_{safe_name}"
                                    yield Button(kc['name'], id=btn_id, variant="primary")
            
            with Horizontal(id="modal-footer"):
                yield Button("Cancel", id="cancel-btn", variant="error")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel-btn":
            self.dismiss(None)
        elif event.button.id and event.button.id.startswith("id_0x"):
            # ボタン ID (id_0xXXXX_NAME) から 0xXXXX を抽出
            parts = event.button.id.split("_")
            if len(parts) >= 2:
                keycode_hex = parts[1]
                try:
                    keycode_int = int(keycode_hex, 16)
                    self.dismiss(keycode_int)
                except ValueError:
                    pass

class KeyboardSelectModal(ModalScreen):
    """保存されているキーボード設定を選択するためのモーダル"""
    def __init__(self, configs: list[dict[str, any]]):
        super().__init__()
        self.configs = configs

    def compose(self) -> ComposeResult:
        with Vertical(id="keyboard-select-container"):
            yield Label("Select Keyboard Layout", id="modal-title")
            with ListView(id="config-list"):
                for cfg in self.configs:
                    yield ListItem(Label(cfg['name']), id=f"cfg_{cfg['path'].stem}")
            with Horizontal(id="modal-footer"):
                yield Button("Cancel", id="cancel-btn", variant="error")

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        idx = self.query_one("#config-list").index
        if idx is not None:
            self.dismiss(self.configs[idx])

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel-btn":
            self.dismiss(None)

class KeyButton(Button):
    """個別のキーを表すウィジェット"""
    def __init__(self, key_info, **kwargs):
        # 最初から行列番号が見えるようにラベルを設定
        label = f"R{key_info.row}C{key_info.col}"
        super().__init__(label, **kwargs)
        self.key_info = key_info
        self.classes = "key-box"
        
        # 1u = 幅10, 高さ3 を基準にサイズと位置を設定
        self.styles.width = int(key_info.w * 10)
        self.styles.height = int(key_info.h * 3)
        # 絶対座標で配置
        self.styles.position = "absolute"
        self.styles.offset = (int(key_info.x * 10), int(key_info.y * 3))

class KeyboardRemapApp(App):
    """lazygit風のキーボード・リマップ TUI アプリ"""

    CSS = """
    Screen {
        layout: vertical;
    }
    #main-container {
        height: 1fr;
    }
    #sidebar {
        width: 10%;
        border: solid green;
    }
    #layout-area {
        width: 90%;
        border: solid blue;
        padding: 1;
        overflow: scroll;
    }
    #info-panel {
        height: 10;
        border: solid yellow;
        padding: 1;
    }
    #key-canvas {
        /* サイズは Python 側で動的に設定される */
    }
    .row {
        height: auto;
        align: center middle;
    }
    .key-box {
        text-style: bold;
        content-align: center middle;
        padding: 0;
        margin: 0;
        min-width: 0;
        border: solid white;
        background: $surface;
    }
    .key-box:hover {
        border: solid $accent;
        background: $accent 20%;
    }
    KeycodeSelectModal {
        align: center middle;
        background: rgba(0, 0, 0, 0.5);
    }
    #keycode-modal-container {
        width: 90%;
        height: 85%;
        border: thick $primary;
        background: $surface;
        padding: 0;
    }
    #modal-title {
        text-align: center;
        background: $primary;
        color: white;
        width: 100%;
        padding: 1;
        text-style: bold;
    }
    /* タブコンテンツの調整 */
    TabbedContent {
        height: 1fr;
    }
    TabPane {
        padding: 0;
    }
    .scroll-grid-container {
        height: 1fr;
        overflow-y: scroll;
        padding: 1;
    }
    .scroll-grid {
        layout: grid;
        grid-size: 6;
        grid-gutter: 1;
        height: auto;
    }
    .scroll-grid Button {
        height: 3;
        background: blue;
        color: white;
        content-align: center middle;
        text-style: bold;
    }
    .scroll-grid Button:hover {
        background: $accent;
    }
    #modal-footer {
        height: auto;
        align: center middle;
        padding: 1;
        border-top: solid $primary;
    }
    #cancel-btn {
        width: 20%;
        height: 3;
    }
    #keyboard-select-container {
        width: 60%;
        height: 50%;
        border: thick $primary;
        background: $surface;
    }
    #config-list {
        height: 1fr;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("d", "toggle_dark", "Toggle dark mode"),
        ("s", "sync", "Sync Keymap"),
        ("l", "load_config", "Load JSON"),
    ]

    def __init__(self, config: KeyboardConfig | None, backend: KeyboardBackend, keycodes: list):
        super().__init__()
        self.kb_config = config
        self.backend = backend
        self.keycodes = keycodes
        self.current_layer = 0
        self.keycode_map = {int(kc['code'], 16): kc['name'] for kc in keycodes}

    def on_mount(self) -> None:
        if self.kb_config:
            self.action_sync()

    def action_sync(self) -> None:
        """実機からキーマップを読み取ってボタンを更新"""
        if not self.backend.api:
            self.notify("No device connected", severity="error")
            return
        
        if not self.kb_config:
            self.notify("No keyboard layout loaded", severity="warning")
            return

        self.notify(f"Syncing layer {self.current_layer}...")
        for btn in self.query(KeyButton):
            try:
                code = self.backend.get_keycode(self.current_layer, btn.key_info.row, btn.key_info.col)
                name = self.keycode_map.get(code, f"0x{code:04x}")
                btn.label = name
            except Exception as e:
                btn.label = "ERR"

    def action_load_config(self) -> None:
        """キーボード設定ファイルを手動で選択して読み込む"""
        kb_dir = Path("data/keyboards")
        configs = []
        for json_file in kb_dir.glob("*.json"):
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    configs.append({
                        "name": data.get("name", json_file.name),
                        "path": json_file,
                        "data": data
                    })
            except:
                continue
        
        def handle_selected(selected: dict | None):
            if selected:
                try:
                    self.kb_config = KeyboardConfig(**selected['data'])
                    self.notify(f"Loaded {selected['name']}")
                    self.recompose()
                except Exception as e:
                    self.notify(f"Error loading config: {e}", severity="error")

        self.push_screen(KeyboardSelectModal(configs), handle_selected)

    def compose(self) -> ComposeResult:
        yield Header()
        
        info = self.backend.get_info()
        device_str = f"Device: {info['name']} | Layers: {info['layers']}" if info else "Disconnected"
        yield Label(device_str, id="device-info")

        with Container(id="main-container"):
            with Horizontal():
                with Vertical(id="sidebar"):
                    yield Label(" LAYERS ")
                    with ListView(id="layer-list"):
                        num_layers = info['layers'] if info else 4
                        for i in range(num_layers):
                            yield ListItem(Label(f"Layer {i}"))
                
                with Vertical(id="layout-area"):
                    if self.kb_config:
                        # 全てのキーを絶対位置で配置するためのコンテナ
                        # 全体サイズを計算
                        max_w = 0
                        max_h = 0
                        for row in self.kb_config.layouts.keymap:
                            for k in row:
                                max_w = max(max_w, k.x + k.w)
                                max_h = max(max_h, k.y + k.h)
                        
                        canvas = Container(id="key-canvas")
                        canvas.styles.width = int(max_w * 10)
                        canvas.styles.height = int(max_h * 3)
                        
                        with canvas:
                            for row in self.kb_config.layouts.keymap:
                                for key_info in row:
                                    yield KeyButton(key_info)
                    else:
                        yield Label("No Keyboard Layout Loaded. Press 'L' to load JSON.", id="no-config-label")
            
            with Container(id="info-panel"):
                yield Label("Key Info:", id="key-title")
                yield Static("Click a key to edit", id="key-info-text")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if isinstance(event.button, KeyButton):
            btn = event.button
            info = btn.key_info
            self.query_one("#key-info-text").update(f"Select new key for Row {info.row}, Col {info.col}")
            
            def handle_selected(new_keycode: int | None):
                if new_keycode is not None:
                    try:
                        self.backend.set_keycode(self.current_layer, info.row, info.col, new_keycode)
                        self.notify("Remapped!")
                        btn.label = self.keycode_map.get(new_keycode, f"0x{new_keycode:04x}")
                    except Exception as e:
                        self.notify(f"Error: {e}", severity="error")

            self.push_screen(KeycodeSelectModal(self.keycodes), handle_selected)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        idx = self.query_one("#layer-list").index
        if idx is not None and idx != self.current_layer:
            self.current_layer = idx
            self.action_sync()

def find_matching_config(vid: int, pid: int) -> KeyboardConfig | None:
    kb_dir = Path("data/keyboards")
    for json_file in kb_dir.glob("*.json"):
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                cfg = KeyboardConfig(**data)
                if cfg.vid == vid and cfg.pid == pid:
                    return cfg
        except:
            continue
    return None

if __name__ == "__main__":
    with open("data/keycodes.json", "r", encoding="utf-8") as f:
        keycodes = json.load(f)
    
    backend = KeyboardBackend()
    connected = backend.find_and_connect()
    
    config = None
    if connected:
        vid = backend.device.vendor_id
        pid = backend.device.product_id
        config = find_matching_config(vid, pid)

    app = KeyboardRemapApp(config, backend, keycodes)
    app.run()
