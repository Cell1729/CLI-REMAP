import qmk_via_api
from qmk_via_api import scan_keyboards
from src.models.keyboard_config import KeyboardConfig

class KeyboardBackend:
    """qmk-via-api を使用したキーボード操作のバックエンド"""
    
    def __init__(self):
        self.device = None
        self.api = None

    def find_and_connect(self, vid: int = None, pid: int = None):
        """デバイスをスキャンして接続する"""
        devices = scan_keyboards()
        if not devices:
            return False
        
        # 特定の VID/PID が指定されている場合はフィルタリング
        if vid and pid:
            for d in devices:
                if d.vendor_id == vid and d.product_id == pid:
                    self.device = d
                    break
        else:
            # 指定がなければ最初に見つかったデバイスを使用
            self.device = devices[0]
        
        if self.device:
            self.api = qmk_via_api.KeyboardApi.from_device(self.device)
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
