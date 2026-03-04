import qmk_via_api
from qmk_via_api import scan_keyboards
from src.models.keyboard_config import KeyboardConfig
from src.protocol.macro import VialMacroManager

class KeyboardBackend:
    """qmk-via-api を使用したキーボード操作のバックエンド"""
    
    def __init__(self):
        self.device = None
        self.api = None
        self.macro_manager: VialMacroManager | None = None

    def find_and_connect(self, vid: int = None, pid: int = None):
        """デバイスをスキャンして接続する"""
        devices = scan_keyboards()
        if not devices:
            return False
        
        if vid and pid:
            for d in devices:
                if d.vendor_id == vid and d.product_id == pid:
                    self.device = d
                    break
        else:
            self.device = devices[0]
        
        if self.device:
            self.api = qmk_via_api.KeyboardApi.from_device(self.device)
            # Vial プロトコルバージョンを取得してマクロマネージャを初期化
            try:
                vial_protocol = self.api.get_protocol_version()
            except Exception:
                vial_protocol = 0
            self.macro_manager = VialMacroManager(self.api, vial_protocol)
            self.macro_manager.load()
            return True
        return False

    def get_info(self):
        """基本情報を取得する"""
        if not self.api:
            return None
        return {
            "protocol": self.api.get_protocol_version(),
            "layers": self.api.get_layer_count(),
            "name": self.device.product_string if hasattr(self.device, 'product_string') else "Unknown Keyboard"
        }

    def get_keycode(self, layer: int, row: int, col: int) -> int:
        """指定位置のキーコードを取得"""
        return self.api.get_key(layer, row, col)

    def set_keycode(self, layer: int, row: int, col: int, keycode: int):
        """指定位置にキーコードを書き込み"""
        self.api.set_key(layer, row, col, keycode)

    def get_macro_count(self) -> int:
        """マクロの総数を取得"""
        if self.macro_manager:
            return self.macro_manager.macro_count
        return 0

    def get_macro(self, index: int) -> str:
        """
        指定インデックスのマクロをテキスト表現で返す。
        Vial プロトコルに従って v1/v2 を自動判別。
        """
        if not self.macro_manager:
            return ""
        try:
            return self.macro_manager.get_macro_text(index)
        except Exception:
            return ""

    def set_macro(self, index: int, text: str):
        """
        テキストをマクロとして書き込む（ActionText として扱う）。
        キーボードを接続していない場合は何もしない。
        """
        if not self.macro_manager:
            return
        try:
            self.macro_manager.set_macro_text(index, text)
        except Exception as e:
            raise RuntimeError(f"マクロの書き込みに失敗しました: {e}")

    def get_macro_manager(self) -> VialMacroManager | None:
        """より高度なマクロ操作（ActionTap 等）が必要な場合に VialMacroManager を返す"""
        return self.macro_manager
