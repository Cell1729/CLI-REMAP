from textual.app import ComposeResult
from textual.widgets import Label, ListView, ListItem, Button, TabbedContent, TabPane
from textual.containers import Container, Horizontal, Vertical
from textual.screen import ModalScreen

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
                                for idx, kc in enumerate(keys):
                                    # ID は一意である必要があるため、名前とコードを組み合わせる
                                    # さらに同じキーコードが複数ある場合に備えてインデックスを付加
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
