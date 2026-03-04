import json
from pathlib import Path
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, ListView, ListItem, Label, Button, TextArea, ContentSwitcher
from textual.containers import Container, Horizontal, Vertical

from src.models.keyboard_config import KeyboardConfig
from src.keyboard_hid import KeyboardBackend
from src.ui.components.key_button import KeyButton
from src.ui.components.modals import KeycodeSelectModal, KeyboardSelectModal

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

class KeyboardRemapApp(App):
    """lazygit風のキーボード・リマップ TUI アプリ"""

    CSS_PATH = "styles.css"

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
        self.current_macro_index = -1
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
                            yield ListItem(Label(f"Layer {i}"), id=f"layer-{i}")
                    
                    yield Label(" MACROS ")
                    with ListView(id="macro-list"):
                        for i in range(16):
                            yield ListItem(Label(f"Macro {i}"), id=f"macro-{i}")
                
                with ContentSwitcher(initial="layout-area"):
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
                    
                    with Vertical(id="macro-editor-area"):
                        yield Label("Macro Editor", classes="macro-info-label")
                        yield TextArea(id="macro-text-area")
                        with Horizontal():
                            yield Button("Save Macro", id="save-macro-btn", variant="primary")
                            yield Button("Back to Layout", id="back-to-layout-btn")
            
            with Container(id="info-panel"):
                yield Label("Key Info:", id="key-title")
                yield Static("Click a key to edit", id="key-info-text")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save-macro-btn":
            if self.current_macro_index != -1:
                text = self.query_one("#macro-text-area").text
                try:
                    self.backend.set_macro(self.current_macro_index, text)
                    self.notify(f"Macro {self.current_macro_index} saved!")
                except Exception as e:
                    self.notify(f"Error saving macro: {e}", severity="error")
        elif event.button.id == "back-to-layout-btn":
            self.query_one(ContentSwitcher).current = "layout-area"
        
        elif isinstance(event.button, KeyButton):
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
        if event.list_view.id == "layer-list":
            idx = event.list_view.index
            if idx is not None and idx != self.current_layer:
                self.current_layer = idx
                self.query_one(ContentSwitcher).current = "layout-area"
                self.action_sync()
        elif event.list_view.id == "macro-list":
            idx = event.list_view.index
            if idx is not None:
                self.current_macro_index = idx
                try:
                    text = self.backend.get_macro(idx)
                    self.query_one("#macro-text-area").text = text
                    self.query_one(ContentSwitcher).current = "macro-editor-area"
                    self.query_one(".macro-info-label").update(f"Editing Macro {idx}")
                    self.notify(f"Loaded Macro {idx}")
                except Exception as e:
                    self.notify(f"Error loading macro: {e}", severity="error")
