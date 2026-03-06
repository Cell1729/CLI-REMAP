import json
from pathlib import Path
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, ListView, ListItem, Label, Button, ContentSwitcher
from textual.containers import Container, Horizontal, Vertical

from src.models.keyboard_config import KeyboardConfig
from src.keyboard_hid import KeyboardBackend
from src.ui.components.key_button import KeyButton
from src.ui.components.modals import KeycodeSelectModal, KeyboardSelectModal
from src.ui.components.macro_editor import MacroEditorPanel

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
        # ── グローバル ──────────────────────────────
        ("q",      "quit",              "Quit"),
        ("d",      "toggle_dark",       "Dark"),
        ("l",      "load_config",       "Load JSON"),
        # ── ナビゲーション ──────────────────────────
        ("L",      "switch_layer",      "Layer"),
        ("m",      "focus_macro_list",  "Macro"),
        ("b",      "go_back",           "Back"),
        # ── 操作 ────────────────────────────────────
        ("s",      "save",              "Save"),
        ("c",      "cancel",            "Cancel"),
        ("r",      "edit_remap",        "Remap"),
        ("ctrl+r", "sync",              "Sync"),
    ]

    # ──────────────────────────────────────────────
    def __init__(self, config: KeyboardConfig | None, backend: KeyboardBackend, keycodes: list):
        super().__init__()
        self.kb_config   = config
        self.backend     = backend
        self.keycodes    = keycodes
        self.current_layer       = 0
        self.current_macro_index = -1
        self.keycode_map = {int(kc['code'], 16): kc['name'] for kc in keycodes}
        # 現在の画面モード: "layout" | "macro-select" | "macro-editor"
        self._view = "layout"

    # ──────────────────────────────────────────────
    # ライフサイクル
    # ──────────────────────────────────────────────
    def on_mount(self) -> None:
        if self.kb_config:
            self.action_sync()

    # ──────────────────────────────────────────────
    # Compose
    # ──────────────────────────────────────────────
    def compose(self) -> ComposeResult:
        yield Header()

        info = self.backend.get_info()
        device_str = f"Device: {info['name']} | Layers: {info['layers']}" if info else "Disconnected"
        yield Label(device_str, id="device-info")

        with Container(id="main-container"):
            with Horizontal():
                with Vertical(id="sidebar"):
                    yield Label(" LAYERS ", id="sidebar-layers-label")
                    with ListView(id="layer-list"):
                        num_layers = info['layers'] if info else 4
                        for i in range(num_layers):
                            yield ListItem(Label(f"Layer {i}"), id=f"layer-{i}")

                    yield Label(" MACROS ", id="sidebar-macros-label")
                    with ListView(id="macro-list"):
                        for i in range(16):
                            yield ListItem(Label(f"Macro {i}"), id=f"macro-{i}")

                with ContentSwitcher(initial="layout-area"):
                    # ── レイアウト画面 ──
                    layout_area = Vertical(id="layout-area")
                    layout_area.styles.align = ("center", "middle")
                    with layout_area:
                        if self.kb_config:
                            max_w, max_h = 0, 0
                            for row in self.kb_config.layouts.keymap:
                                for k in row:
                                    max_w = max(max_w, k.x + k.w)
                                    max_h = max(max_h, k.y + k.h)
                            canvas = Container(id="key-canvas")
                            canvas.styles.width  = int(max_w * 10)
                            canvas.styles.height = int(max_h * 3)
                            with canvas:
                                for row in self.kb_config.layouts.keymap:
                                    for key_info in row:
                                        yield KeyButton(key_info)
                        else:
                            yield Label(
                                "No Keyboard Layout Loaded. Press 'l' to load JSON.",
                                id="no-config-label"
                            )

                    # ── マクロエディタ画面 ──
                    with Vertical(id="macro-editor-area"):
                        yield MacroEditorPanel(
                            id="macro-editor-panel",
                            keycode_map=self.keycode_map
                        )

            with Container(id="info-panel"):
                yield Label("Key Info:", id="key-title")
                yield Static("Click a key / press r to remap", id="key-info-text")

        yield Footer()

    # ──────────────────────────────────────────────
    # Actions — ナビゲーション
    # ──────────────────────────────────────────────
    def action_switch_layer(self) -> None:
        """レイヤーリストにフォーカスを移してレイヤー切り替えを促す"""
        self._show("layout")
        try:
            self.query_one("#layer-list", ListView).focus()
            self.notify("↑↓ でレイヤーを選択, Enter で確定")
        except Exception:
            pass

    def action_focus_macro_list(self) -> None:
        """マクロリストをフォーカス — 矢印で移動, Enter で開く"""
        self._show("layout")   # まずレイアウト表示に戻す
        try:
            self.query_one("#macro-list", ListView).focus()
            self.notify("↑↓ でマクロを選択, Enter で開く, b で戻る")
        except Exception:
            pass

    def action_go_back(self) -> None:
        """レイアウト画面に戻る"""
        self._show("layout")
        self.notify("Layout に戻りました")

    # ──────────────────────────────────────────────
    # Actions — 保存 / キャンセル
    # ──────────────────────────────────────────────
    def action_save(self) -> None:
        """現在の画面に応じて保存処理を行う"""
        if self._view == "macro-editor":
            self._save_macro()
        else:
            self._save_keymap()

    def _save_keymap(self) -> None:
        """現在のレイヤーのキーマップを実機に書き込む（sync は read, save は write）"""
        if not self.backend.api:
            self.notify("No device connected", severity="error")
            return
        # レイアウト上のボタン状態をそのまま確定（変更はリアルタイムで set_keycode 済みのため notify のみ）
        self.notify(f"Layer {self.current_layer} のキーマップを保存しました ✓")

    def _save_macro(self) -> None:
        """マクロエディタの内容を実機に書き込む"""
        if self.current_macro_index == -1:
            self.notify("マクロが選択されていません", severity="warning")
            return
        try:
            panel = self.query_one("#macro-editor-panel", MacroEditorPanel)
            actions = panel.get_actions()
            mm = self.backend.get_macro_manager()
            if mm:
                mm.set_macro_from_actions(self.current_macro_index, actions)
            else:
                text = " ".join(a.to_text() for a in actions)
                self.backend.set_macro(self.current_macro_index, text)
            self.notify(f"Macro {self.current_macro_index} 保存完了 ✓")
        except Exception as e:
            self.notify(f"Error saving macro: {e}", severity="error")

    def action_cancel(self) -> None:
        """変更をキャンセルしてレイアウト画面に戻る（マクロエディタをリロード）"""
        if self._view == "macro-editor" and self.current_macro_index != -1:
            # エディタを元の内容にリロード
            try:
                mm = self.backend.get_macro_manager()
                actions = mm.get_macro_actions(self.current_macro_index) if mm else []
                self.query_one("#macro-editor-panel", MacroEditorPanel).load_actions(
                    self.current_macro_index, actions
                )
            except Exception:
                pass
        self._show("layout")
        self.notify("キャンセルしました")

    # ──────────────────────────────────────────────
    # Actions — リマップ / 同期
    # ──────────────────────────────────────────────
    def action_edit_remap(self) -> None:
        """フォーカス中のキーのキーコード選択画面を開く"""
        focused = self.focused
        if not isinstance(focused, KeyButton):
            self.notify("キーを選択してから r を押してください", severity="warning")
            return
        info = focused.key_info
        self.query_one("#key-info-text").update(f"Row {info.row}, Col {info.col} を編集中")

        def handle_selected(new_keycode: int | None):
            if new_keycode is not None:
                try:
                    self.backend.set_keycode(self.current_layer, info.row, info.col, new_keycode)
                    self.notify("Remapped!")
                    focused.label = self.keycode_map.get(new_keycode, f"0x{new_keycode:04x}")
                except Exception as e:
                    self.notify(f"Error: {e}", severity="error")

        self.push_screen(KeycodeSelectModal(self.keycodes), handle_selected)

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
                btn.label = self.keycode_map.get(code, f"0x{code:04x}")
            except Exception:
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

    # ──────────────────────────────────────────────
    # ヘルパー
    # ──────────────────────────────────────────────
    def _show(self, view: str) -> None:
        """ContentSwitcher を切り替えて _view 状態を更新する"""
        self._view = view
        mapping = {
            "layout":       "layout-area",
            "macro-editor": "macro-editor-area",
        }
        target = mapping.get(view, "layout-area")
        try:
            self.query_one(ContentSwitcher).current = target
        except Exception:
            pass

    # ──────────────────────────────────────────────
    # イベントハンドラ
    # ──────────────────────────────────────────────
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save-macro-btn":
            self._save_macro()
        elif event.button.id == "back-to-layout-btn":
            self.action_go_back()
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
                self._show("layout")
                self.action_sync()
        elif event.list_view.id == "macro-list":
            idx = event.list_view.index
            if idx is not None:
                self.current_macro_index = idx
                try:
                    mm = self.backend.get_macro_manager()
                    actions = mm.get_macro_actions(idx) if mm else []
                    self.query_one("#macro-editor-panel", MacroEditorPanel).load_actions(idx, actions)
                    self._show("macro-editor")
                    self.notify(f"Macro {idx} を開きました ({len(actions)} actions) — s で保存, b で戻る")
                except Exception as e:
                    self.notify(f"Error loading macro: {e}", severity="error")
