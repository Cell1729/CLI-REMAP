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

    def get_macro_count(self) -> int:
        """マクロの総数を取得"""
        if not self.api:
            return 0
        return self.api.get_macro_count()

    def get_macro(self, index: int) -> str:
        """指定されたインデックスのマクロ文字列を取得"""
        if not self.api:
            return ""
        # qmk-via-api の get_macro_bytes() はバッファ全体を返す
        buffer = self.api.get_macro_bytes()
        if not buffer:
            return ""
        
        # マクロはヌル文字 (0x00) で区切られている
        macros = buffer.split(b'\x00')
        if index < len(macros):
            try:
                return macros[index].decode('utf-8', errors='ignore')
            except UnicodeDecodeError:
                return str(macros[index])
        return ""

    def set_macro(self, index: int, text: str):
        """指定されたインデックスにマクロ文字列を書き込み"""
        if not self.api:
            return
        
        # 現在のバッファ全体を取得
        buffer = bytearray(self.api.get_macro_bytes())
        macros = buffer.split(b'\x00')
        
        # 指定インデックスのマクロを更新
        new_text_bytes = text.encode('utf-8')
        if index < len(macros):
            macros[index] = new_text_bytes
        else:
            # インデックスが足りない場合は空で埋める
            while len(macros) <= index:
                macros.append(b'')
            macros[index] = new_text_bytes
            
        # バッファを再構築
        new_buffer = b'\x00'.join(macros) + b'\x00'
        
        # バッファサイズを調整 (パディング)
        target_size = self.api.get_macro_buffer_size()
        if len(new_buffer) > target_size:
            # サイズオーバーの場合は切り詰め (本来はエラーにすべきだが簡易化)
            new_buffer = new_buffer[:target_size]
        else:
            # 残りを 0x00 で埋める
            new_buffer = new_buffer.ljust(target_size, b'\x00')
            
        self.api.set_macro_bytes(new_buffer)
