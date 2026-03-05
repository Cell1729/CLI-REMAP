from textual.app import ComposeResult
from textual.widgets import Label, ListView, ListItem, Button, TabbedContent, TabPane
from textual.containers import Container, Horizontal, Vertical
from textual.screen import ModalScreen

class KeycodeSelectModal(ModalScreen):
    """キーコードを選択するためのモーダル画面（カテゴリ別タブ表示）"""
    
    def __init__(self, keycodes):
        super().__init__()
        self.keycodes = keycodes
        # Remap 準拠のカテゴリ定義（表示順）
        self.CATEGORY_ORDER = [
            ("basic",        "Basic"),
            ("numpad",       "Numpad"),
            ("Media",        "Media"),
            ("MACRO",        "Macro"),
            ("layers",       "Layers"),
            ("language",     "Language"),
            ("lock",         "Lock"),
            ("grave_escape", "Grave ESC"),
            ("space_cadet",  "Space Cadet"),
            ("one_shot",     "One Shot"),
            ("mouse",        "Mouse"),
            ("device",       "Device"),
            ("keyboard",     "Keyboard"),
            ("Lighting",     "Lighting"),
            ("magic",        "Magic"),
            ("combo",        "Combo"),
            ("auto_shift",   "Auto Shift"),
            ("dynamic_macro","Dyn Macro"),
            ("leader",       "Leader"),
            ("swap_hands",   "Swap Hands"),
            ("key_override", "Key Override"),
            ("tapping_term", "Tapping Term"),
            ("auto_correct", "Auto Correct"),
            ("repeat_key",   "Repeat Key"),
            ("key_lock",     "Key Lock"),
            ("caps_word",    "Caps Word"),
            ("midi",         "MIDI"),
            ("sequencer",    "Sequencer"),
            ("special",      "Special"),
        ]
        self.categories = {key: [] for key, _ in self.CATEGORY_ORDER}
        for kc in keycodes:
            cat = kc.get("category", "basic")
            if cat in self.categories:
                self.categories[cat].append(kc)
            else:
                self.categories["special"].append(kc)

    def compose(self) -> ComposeResult:
        with Vertical(id="keycode-modal-container"):
            yield Label("Select New Keycode", id="modal-title")
            
            with TabbedContent():
                for cat_key, cat_display in self.CATEGORY_ORDER:
                    keys = self.categories.get(cat_key, [])
                    if not keys:
                        continue  # 空のタブは表示しない
                    with TabPane(cat_display):
                        with Container(classes="scroll-grid-container"):
                            with Container(classes="scroll-grid"):
                                for idx, kc in enumerate(keys):
                                    safe_name = "".join([c if c.isalnum() or c in "_-" else "_" for c in kc['name']])
                                    btn_id = f"id_{idx}_{kc['code']}_{safe_name}"
                                    yield Button(kc['name'], id=btn_id, variant="primary")
            
            with Horizontal(id="modal-footer"):
                yield Button("Cancel", id="cancel-btn", variant="error")


    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel-btn":
            self.dismiss(None)
        elif event.button.id and event.button.id.startswith("id_"):
            # ボタン ID (id_INDEX_0xXXXX_NAME) から 0xXXXX を抽出
            parts = event.button.id.split("_")
            if len(parts) >= 3:
                keycode_hex = parts[2]
                try:
                    keycode_int = int(keycode_hex, 16)
                    self.dismiss(keycode_int)
                except ValueError:
                    pass

class KeyboardSelectModal(ModalScreen):
    """保存されているキーボード設定を選択するためのモーダル"""
    def __init__(self, configs: list[dict]):
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
