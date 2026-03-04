"""
vial-gui の protocol/macro.py から移植
CLI-REMAP 向けに独立動作するよう書き直し
qmk_via_api を介してマクロの読み書きを行う
"""
import struct
from src.protocol.macro_action import (
    SS_TAP_CODE, SS_DOWN_CODE, SS_UP_CODE,
    SS_QMK_PREFIX, SS_DELAY_CODE,
    VIAL_MACRO_EXT_TAP, VIAL_MACRO_EXT_DOWN, VIAL_MACRO_EXT_UP,
    VIAL_PROTOCOL_ADVANCED_MACROS,
    ActionText, ActionTap, ActionDown, ActionUp, ActionDelay,
    TAG_TO_ACTION
)

BUFFER_FETCH_CHUNK = 28  # VIA プロトコルの1パケット最大サイズ


def macro_deserialize_v1(data: bytes) -> list:
    """プロトコル v1 でシングルマクロをデシリアライズ"""
    out = []
    sequence = []
    data = bytearray(data)
    while len(data) > 0:
        if data[0] in [SS_TAP_CODE, SS_DOWN_CODE, SS_UP_CODE]:
            if len(data) < 2:
                break
            if len(sequence) > 0 and isinstance(sequence[-1], list) and sequence[-1][0] == data[0]:
                sequence[-1][1].append(data[1])
            else:
                sequence.append([data[0], [data[1]]])
            data.pop(0)
            data.pop(0)
        else:
            ch = chr(data[0])
            if len(sequence) > 0 and isinstance(sequence[-1], str):
                sequence[-1] += ch
            else:
                sequence.append(ch)
            data.pop(0)
    for s in sequence:
        if isinstance(s, str):
            out.append(ActionText(s))
        else:
            keycodes = s[1]
            cls = {SS_TAP_CODE: ActionTap, SS_DOWN_CODE: ActionDown, SS_UP_CODE: ActionUp}[s[0]]
            out.append(cls(keycodes))
    return out


def macro_deserialize_v2(data: bytes) -> list:
    """プロトコル v2 でシングルマクロをデシリアライズ"""
    out = []
    sequence = []
    data = bytearray(data)
    while len(data) > 0:
        if data[0] == SS_QMK_PREFIX:
            if len(data) < 2:
                break
            act = data[1]
            if act in [SS_TAP_CODE, SS_DOWN_CODE, SS_UP_CODE,
                       VIAL_MACRO_EXT_TAP, VIAL_MACRO_EXT_DOWN, VIAL_MACRO_EXT_UP]:
                if act in [SS_TAP_CODE, SS_DOWN_CODE, SS_UP_CODE]:
                    if len(data) < 3:
                        break
                    length = 3
                    kc = data[2]
                else:
                    remap = {VIAL_MACRO_EXT_TAP: SS_TAP_CODE,
                             VIAL_MACRO_EXT_DOWN: SS_DOWN_CODE,
                             VIAL_MACRO_EXT_UP: SS_UP_CODE}
                    act = remap[act]
                    if len(data) < 4:
                        break
                    length = 4
                    kc = struct.unpack("<H", data[2:4])[0]
                    if kc > 0xFF00:
                        kc = (kc & 0xFF) << 8
                if len(sequence) > 0 and isinstance(sequence[-1], list) and sequence[-1][0] == act:
                    sequence[-1][1].append(kc)
                else:
                    sequence.append([act, [kc]])
                for _ in range(length):
                    data.pop(0)
            elif act == SS_DELAY_CODE:
                if len(data) < 4:
                    break
                delay = (data[2] - 1) + (data[3] - 1) * 255
                sequence.append([SS_DELAY_CODE, delay])
                for _ in range(4):
                    data.pop(0)
            else:
                data.pop(0)
                data.pop(0)
        else:
            ch = chr(data[0])
            if len(sequence) > 0 and isinstance(sequence[-1], str):
                sequence[-1] += ch
            else:
                sequence.append(ch)
            data.pop(0)

    for s in sequence:
        if isinstance(s, str):
            out.append(ActionText(s))
        else:
            args = None
            if s[0] in [SS_TAP_CODE, SS_DOWN_CODE, SS_UP_CODE]:
                args = s[1]
            elif s[0] == SS_DELAY_CODE:
                args = s[1]
            if args is not None:
                cls = {SS_TAP_CODE: ActionTap, SS_DOWN_CODE: ActionDown, SS_UP_CODE: ActionUp,
                       SS_DELAY_CODE: ActionDelay}[s[0]]
                out.append(cls(args))
    return out


class VialMacroManager:
    """
    qmk_via_api を使ってマクロを管理するクラス。
    vial-gui の ProtocolMacro の考え方を CLI-REMAP 向けに移植。
    """

    def __init__(self, api, vial_protocol: int = 0):
        self.api = api
        self.vial_protocol = vial_protocol
        self.macro_count = 0
        self.macro_memory = 0
        self._buffer: bytes = b""

    def load(self):
        """キーボードからマクロ情報とバッファを読み込む"""
        try:
            self.macro_count = self.api.get_macro_count()
            self.macro_memory = self.api.get_macro_buffer_size()
            raw = self.api.get_macro_bytes()
            if raw:
                self._buffer = bytes(raw)
                # macro_count 個の NUL 区切りに整理
                parts = self._buffer.split(b"\x00") + [b""] * self.macro_count
                self._buffer = b"\x00".join(parts[:self.macro_count]) + b"\x00"
            else:
                self._buffer = b"\x00" * self.macro_count
        except Exception as e:
            self.macro_count = 0
            self.macro_memory = 0
            self._buffer = b""

    def _deserialize_one(self, data: bytes) -> list:
        if self.vial_protocol >= VIAL_PROTOCOL_ADVANCED_MACROS:
            return macro_deserialize_v2(data)
        return macro_deserialize_v1(data)

    def get_macro_actions(self, index: int) -> list:
        """指定インデックスのマクロをアクションリストとして返す"""
        parts = self._buffer.split(b"\x00")
        parts = (parts + [b""] * self.macro_count)[:self.macro_count]
        if index >= len(parts):
            return []
        return self._deserialize_one(parts[index])

    def get_macro_text(self, index: int) -> str:
        """指定インデックスのマクロをテキスト表現で返す（TUI 表示用）"""
        actions = self.get_macro_actions(index)
        if not actions:
            return ""
        lines = []
        for act in actions:
            lines.append(act.to_text())
        return "\n".join(lines)

    def set_macro_from_actions(self, index: int, actions: list):
        """アクションリストを指定インデックスに書き込む"""
        parts = list(self._buffer.split(b"\x00"))
        parts = (parts + [b""] * self.macro_count)[:self.macro_count]

        # シリアライズ
        serialized = b""
        for act in actions:
            serialized += act.serialize(self.vial_protocol)
        parts[index] = serialized

        new_buffer = b"\x00".join(parts) + b"\x00"
        if len(new_buffer) > self.macro_memory:
            raise RuntimeError(f"マクロが大きすぎます: {len(new_buffer)} / {self.macro_memory} bytes")

        self.api.set_macro_bytes(new_buffer.ljust(self.macro_memory, b"\x00"))
        self._buffer = new_buffer

    def set_macro_text(self, index: int, text: str):
        """
        テキストをそのまま ActionText として書き込む（シンプルな文字列マクロ）
        例: "Hello World" → キーボードが打鍵するテキスト
        """
        actions = [ActionText(text)] if text else []
        self.set_macro_from_actions(index, actions)
