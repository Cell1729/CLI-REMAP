"""
マクロエディタ UI コンポーネント
ActionText / ActionTap / ActionDelay をアクション行リストとして表示・編集
"""
from textual.app import ComposeResult
from textual.widgets import Label, Button, Input, ListView, ListItem, Select
from textual.containers import Container, Horizontal, Vertical
from textual.widget import Widget
from textual.reactive import reactive

from src.protocol.macro_action import (
    ActionText, ActionTap, ActionDown, ActionUp, ActionDelay, BasicAction
)


class MacroActionRow(Widget):
    """マクロの1アクション行を表すウィジェット"""

    DEFAULT_CSS = """
    MacroActionRow {
        height: 3;
        width: 100%;
        layout: horizontal;
    }
    MacroActionRow .action-type-label {
        width: 8;
        height: 3;
        content-align: center middle;
        text-style: bold;
    }
    MacroActionRow .action-value-input {
        width: 1fr;
        height: 3;
    }
    MacroActionRow .action-delete-btn {
        width: 4;
        height: 3;
    }
    MacroActionRow.text-action .action-type-label { background: $success 30%; color: $success; }
    MacroActionRow.tap-action .action-type-label  { background: $primary 30%; color: $primary; }
    MacroActionRow.down-action .action-type-label { background: $warning 30%; color: $warning; }
    MacroActionRow.up-action .action-type-label   { background: $error 30%;   color: $error;   }
    MacroActionRow.delay-action .action-type-label{ background: $accent 30%;  color: $accent;  }
    """

    def __init__(self, action: BasicAction, row_index: int, keycode_map: dict | None = None, **kwargs):
        super().__init__(**kwargs)
        self.action = action
        self.row_index = row_index
        self.keycode_map = keycode_map or {}
        tag = action.tag
        css_classes = {
            "text": "text-action",
            "tap": "tap-action",
            "down": "down-action",
            "up": "up-action",
            "delay": "delay-action",
        }
        self.add_class(css_classes.get(tag, ""))

    def compose(self) -> ComposeResult:
        tag_label = self.action.tag.upper()
        # 値の表示（keycode_map で整数をキー名に変換）
        if hasattr(self.action, "text"):
            value = self.action.text
        elif hasattr(self.action, "sequence"):
            parts = []
            for k in self.action.sequence:
                if isinstance(k, int):
                    parts.append(self.keycode_map.get(k, f"0x{k:02x}"))
                else:
                    parts.append(str(k))
            value = ", ".join(parts)
        elif hasattr(self.action, "delay"):
            value = str(self.action.delay)
        else:
            value = ""

        yield Label(tag_label, classes="action-type-label")
        yield Input(value, placeholder="Value...", classes="action-value-input",
                    id=f"action-input-{self.row_index}")
        yield Button("×", variant="error", classes="action-delete-btn",
                     id=f"action-delete-{self.row_index}")

    def get_updated_action(self) -> BasicAction:
        """入力値を読み込んで更新済みアクションを返す"""
        try:
            input_widget = self.query_one(".action-value-input", Input)
            val = input_widget.value
        except Exception:
            val = ""

        if isinstance(self.action, ActionText):
            return ActionText(val)
        elif isinstance(self.action, ActionTap):
            keys = [k.strip() for k in val.split(",") if k.strip()]
            return ActionTap(keys)
        elif isinstance(self.action, ActionDown):
            keys = [k.strip() for k in val.split(",") if k.strip()]
            return ActionDown(keys)
        elif isinstance(self.action, ActionUp):
            keys = [k.strip() for k in val.split(",") if k.strip()]
            return ActionUp(keys)
        elif isinstance(self.action, ActionDelay):
            try:
                return ActionDelay(int(val))
            except ValueError:
                return ActionDelay(0)
        return self.action


class MacroEditorPanel(Widget):
    """
    マクロをアクション行リストとして表示・編集するパネル
    """

    DEFAULT_CSS = """
    MacroEditorPanel {
        width: 100%;
        height: 1fr;
        layout: vertical;
    }
    #macro-editor-header {
        height: 3;
        background: $primary;
        color: white;
        text-style: bold;
        content-align: center middle;
        padding: 0 1;
    }
    #action-list-container {
        height: 1fr;
        overflow-y: scroll;
        border: solid $primary;
        padding: 0 1;
    }
    #action-add-bar {
        height: 3;
        layout: horizontal;
        padding: 0 1;
        background: $surface-darken-1;
    }
    #action-add-bar Button {
        width: 1fr;
        height: 3;
        margin: 0 1;
    }
    #macro-editor-footer {
        height: 3;
        layout: horizontal;
        padding: 0 1;
    }
    #macro-editor-footer Button {
        height: 3;
        margin: 0 1;
    }
    #save-macro-btn { width: 1fr; }
    #back-to-layout-btn { width: 1fr; }
    """

    macro_index: reactive[int] = reactive(-1)

    def __init__(self, keycode_map: dict | None = None, **kwargs):
        super().__init__(**kwargs)
        self._actions: list[BasicAction] = []
        self.keycode_map = keycode_map or {}

    def compose(self) -> ComposeResult:
        yield Label("Macro Editor", id="macro-editor-header")
        with Container(id="action-list-container"):
            pass  # 動的に追加
        with Horizontal(id="action-add-bar"):
            yield Button("+ Text", id="add-text-btn", variant="success")
            yield Button("+ Tap", id="add-tap-btn", variant="primary")
            yield Button("+ Down", id="add-down-btn", variant="warning")
            yield Button("+ Up", id="add-up-btn", variant="error")
            yield Button("+ Delay", id="add-delay-btn", variant="default")
        with Horizontal(id="macro-editor-footer"):
            yield Button("Save", id="save-macro-btn", variant="primary")
            yield Button("← Back", id="back-to-layout-btn", variant="default")

    def load_actions(self, index: int, actions: list[BasicAction]):
        """マクロインデックスとアクションリストを読み込んで表示を更新"""
        self.macro_index = index
        self._actions = list(actions)
        self._refresh_list()
        # ヘッダー更新
        try:
            self.query_one("#macro-editor-header", Label).update(f"Macro {index} — {len(actions)} actions")
        except Exception:
            pass

    def _refresh_list(self):
        """アクションリストを再描画する"""
        container = self.query_one("#action-list-container", Container)
        container.remove_children()
        if not self._actions:
            container.mount(Label("No actions. Use buttons below to add.", id="no-actions-label"))
        else:
            for i, action in enumerate(self._actions):
                container.mount(MacroActionRow(action, i, keycode_map=self.keycode_map))

    def _collect_current_actions(self) -> list[BasicAction]:
        """現在の入力値からアクションリストを構築する"""
        rows = self.query(MacroActionRow)
        return [row.get_updated_action() for row in rows]

    def _add_action(self, action: BasicAction):
        self._actions = self._collect_current_actions()
        self._actions.append(action)
        self._refresh_list()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id or ""
        if btn_id == "add-text-btn":
            self._add_action(ActionText(""))
        elif btn_id == "add-tap-btn":
            self._add_action(ActionTap([]))
        elif btn_id == "add-down-btn":
            self._add_action(ActionDown([]))
        elif btn_id == "add-up-btn":
            self._add_action(ActionUp([]))
        elif btn_id == "add-delay-btn":
            self._add_action(ActionDelay(100))
        elif btn_id.startswith("action-delete-"):
            try:
                idx = int(btn_id.split("-")[-1])
                self._actions = self._collect_current_actions()
                if 0 <= idx < len(self._actions):
                    self._actions.pop(idx)
                self._refresh_list()
            except (ValueError, IndexError):
                pass
        # save / back はアプリ側で on_button_pressed で処理

    def get_actions(self) -> list[BasicAction]:
        """保存前に現在の全アクションを返す"""
        return self._collect_current_actions()
