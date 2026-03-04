import json
from pathlib import Path
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, ListView, ListItem, Label, Button
from textual.containers import Container, Horizontal, Vertical, Grid
from textual.screen import ModalScreen
from src.models.keyboard_config import KeyboardConfig
from src.keyboard_hid import KeyboardBackend

class KeycodeSelectModal(ModalScreen):
    """キーコードを選択するためのモーダル画面"""
    
    def __init__(self, keycodes):
        super().__init__()
        self.keycodes = keycodes

    def compose(self) -> ComposeResult:
        with Grid(id="keycode-grid"):
            yield Label("Select New Keycode", id="modal-title")
            with Container(id="scroll-area"):
                for kc in self.keycodes:
                    # ボタンラベルとして名称を表示
                    yield Button(label=kc['name'], id=f"kc-{kc['code']}", variant="primary")
            yield Button("Cancel", id="cancel-btn", variant="error")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel-btn":
            self.dismiss(None)
        elif event.button.id.startswith("kc-"):
            # ボタン ID から 0xXXXX を抽出
            keycode_hex = event.button.id.split("kc-")[1]
            keycode_int = int(keycode_hex, 16)
            self.dismiss(keycode_int)

class KeyButton(Button):
    """個別のキーを表すウィジェット"""
    def __init__(self, key_info, **kwargs):
        # 初期表示を ??? にして同期待ちであることを示す
        super().__init__(label="???", **kwargs)
        self.key_info = key_info
        # ボタンを少し大きめにして文字が見えるようにする
        self.styles.min_width = 10
        self.styles.height = 3
        self.styles.margin = (0, 1)

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
        width: 20%;
        border: double green;
        height: 100%;
    }
    #layout-area {
        width: 80%;
        border: double blue;
        height: 100%;
        padding: 1 2;
        overflow: scroll;
    }
    #info-panel {
        height: 30%;
        border: double yellow;
        padding: 1;
    }
    .row {
        height: auto;
        align: center middle;
        margin: 0 0;
    }
    KeyButton {
        text-style: bold;
        content-align: center middle;
    }
    #device-info {
        background: $primary;
        color: $text;
        padding: 0 1;
    }
    
    /* Modal Styles */
    #keycode-grid {
        grid-size: 1;
        grid-rows: auto 1fr auto;
        padding: 1 2;
        width: 60%;
        height: 80%;
        border: thick $primary;
        background: $surface;
        align: center middle;
    }
    #modal-title {
        text-align: center;
        width: 100%;
        background: $primary;
        color: $text;
    }
    #scroll-area {
        layout: grid;
        grid-size: 5;
        overflow-y: scroll;
        padding: 1;
    }
    #scroll-area Button {
        margin: 1;
        min-width: 8;
        height: 3;
    }
    #scroll-area .button--label {
        text-align: center;
        width: 100%;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("d", "toggle_dark", "Toggle dark mode"),
    ]

    def __init__(self, config: KeyboardConfig, backend: KeyboardBackend, keycodes: list):
        super().__init__()
        self.config = config
        self.backend = backend
        self.keycodes = keycodes
        self.current_layer = 0
        # キーコード(int) -> 名称(str) のマッピング作成
        self.keycode_map = {int(kc['code'], 16): kc['name'] for kc in keycodes}
        # 各キーの現在の設定を保持する辞書 {(row, col): keyname}
        self.current_keymap = {}

    def on_mount(self) -> None:
        """アプリ起動時にキーマップを同期"""
        self.sync_keymap()

    def sync_keymap(self) -> None:
        """現在のレイヤーのキーマップを実機から取得してUIに反映"""
        if not self.backend.api:
            return
        
        self.notify(f"Syncing Layer {self.current_layer}...")
        for row_list in self.config.layouts.keymap:
            for key_info in row_list:
                try:
                    code = self.backend.get_keycode(self.current_layer, key_info.row, key_info.col)
                    name = self.keycode_map.get(code, f"0x{code:04x}")
                    self.current_keymap[(key_info.row, key_info.col)] = name
                except:
                    self.current_keymap[(key_info.row, key_info.col)] = "ERR"
        
        # ボタンのラベルを一斉更新
        for button in self.query(KeyButton):
            info = button.key_info
            name = self.current_keymap.get((info.row, info.col), "???")
            button.label = name

    def compose(self) -> ComposeResult:
        yield Header()
        
        info = self.backend.get_info()
        device_str = f"Device: {info['name']} | Protocol: v{info['protocol']} | Layers: {info['layers']}" if info else "No Device Connected"
        yield Label(device_str, id="device-info")

        with Container(id="main-container"):
            with Horizontal():
                with Vertical(id="sidebar"):
                    yield Label(" LAYERS ", variant="success")
                    with ListView(id="layer-list"):
                        num_layers = info['layers'] if info else 4
                        for i in range(num_layers):
                            yield ListItem(Label(f"Layer {i}"), id=f"layer-{i}")
                
                with Vertical(id="layout-area"):
                    yield Label(f" Layout: {self.config.name} (Press Key to Edit) ")
                    for row in self.config.layouts.keymap:
                        with Horizontal(classes="row"):
                            for key_info in row:
                                yield KeyButton(key_info)
            
            with Container(id="info-panel"):
                yield Label("Selected Key Info:", id="key-title")
                yield Static("None", id="key-info-text")
                yield Static("Current Keycode: ---", id="keycode-display")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """キーボタンが押されたとき"""
        if isinstance(event.button, KeyButton):
            btn = event.button
            info = btn.key_info
            
            self.query_one("#key-info-text").update(
                f"Row: {info.row}, Col: {info.col} | Pos: ({info.x}, {info.y})"
            )
            
            # モーダルを表示して新しいキーコードを選択
            def handle_selected(new_keycode: int | None):
                if new_keycode is not None:
                    try:
                        # キーボードに書き込み
                        self.backend.set_keycode(self.current_layer, info.row, info.col, new_keycode)
                        self.notify(f"Successfully remapped to 0x{new_keycode:04x}")
                        
                        # UI表示を更新
                        new_name = self.keycode_map.get(new_keycode, f"0x{new_keycode:04x}")
                        btn.label = new_name
                        self.query_one("#keycode-display").update(f"Current Keycode: 0x{new_keycode:04x} ({new_name})")
                    except Exception as e:
                        self.notify(f"Failed to remap: {e}", severity="error")

            self.push_screen(KeycodeSelectModal(self.keycodes), handle_selected)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """レイヤーが選択されたとき"""
        idx = self.query_one("#layer-list").index
        if idx != self.current_layer:
            self.current_layer = idx
            self.sync_keymap()

    def action_toggle_dark(self) -> None:
        self.dark = not self.dark

if __name__ == "__main__":
    # データ読み込み
    with open("data/keyboards/sample_pad.json", "r") as f:
        config_data = json.load(f)
    config = KeyboardConfig(**config_data)

    with open("data/keycodes.json", "r") as f:
        keycodes = json.load(f)

    # バックエンド接続
    backend = KeyboardBackend()
    backend.find_and_connect()
    
    app = KeyboardRemapApp(config, backend, keycodes)
    app.run()