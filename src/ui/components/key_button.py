from textual.widgets import Button

class KeyButton(Button):
    """個別のキーを表すウィジェット"""
    def __init__(self, key_info, **kwargs):
        # 最初から行列番号が見えるようにラベルを設定
        label = f"R{key_info.row}C{key_info.col}"
        super().__init__(label, **kwargs)
        self.key_info = key_info
        self.classes = "key-box"
        
        # 1u = 幅10, 高さ3 を基準にサイズと位置を設定
        self.styles.width = int(key_info.w * 10)
        self.styles.height = int(key_info.h * 3)
        # 絶対座標で配置
        self.styles.position = "absolute"
        self.styles.offset = (int(key_info.x * 10), int(key_info.y * 3))
