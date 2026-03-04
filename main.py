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

class KeyButton(Button):
    """個別のキーを表すウィジェット"""
    def __init__(self, key_info, **kwargs):
        # 最初から行列番号が見えるようにラベルを設定
        label = f"R{key_info.row}C{key_info.col}"
        super().__init__(label, **kwargs)
        self.key_info = key_info
        self.classes = "key-box"

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
        width: 25%;
        border: solid green;
    }
    #layout-area {
        width: 75%;
        border: solid blue;
        padding: 1;
        overflow: scroll;
    }
    #info-panel {
        height: 10;
        border: solid yellow;
        padding: 1;
    }
    .row {
        height: auto;
        align: center middle;
    }
    .key-box {
        min-width: 10;
        height: 3;
        text-style: bold;
        content-align: center middle;
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
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("d", "toggle_dark", "Toggle dark mode"),
        ("s", "sync", "Sync Keymap"),
    ]

    def __init__(self, config: KeyboardConfig, backend: KeyboardBackend, keycodes: list):
        super().__init__()
        self.config = config
        self.backend = backend
        self.keycodes = keycodes
        self.current_layer = 0
        self.keycode_map = {int(kc['code'], 16): kc['name'] for kc in keycodes}

    def on_mount(self) -> None:
        self.action_sync()

    def action_sync(self) -> None:
        """実機からキーマップを読み取ってボタンを更新"""
        if not self.backend.api:
            self.notify("No device connected", severity="error")
            return
        
        self.notify(f"Syncing layer {self.current_layer}...")
        for btn in self.query(KeyButton):
            try:
                code = self.backend.get_keycode(self.current_layer, btn.key_info.row, btn.key_info.col)
                name = self.keycode_map.get(code, f"0x{code:04x}")
                btn.label = name
            except Exception as e:
                btn.label = "ERR"

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
                    for row in self.config.layouts.keymap:
                        with Horizontal(classes="row"):
                            for key_info in row:
                                yield KeyButton(key_info)
            
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
        if idx != self.current_layer:
            self.current_layer = idx
            self.action_sync()

if __name__ == "__main__":
    with open("data/keyboards/sample_pad.json", "r") as f:
        config = KeyboardConfig(**json.load(f))
    with open("data/keycodes.json", "r") as f:
        keycodes = json.load(f)
    backend = KeyboardBackend()
    backend.find_and_connect()
    
    app = KeyboardRemapApp(config, backend, keycodes)
    app.run()