from typing import List, Dict, Any, Union
from src.models.keyboard_config import KeyDefinition

def parse_via_layout(raw_keymap: List[Any]) -> List[List[KeyDefinition]]:
    """
    VIA の生データ形式（KLE互換）を KeyDefinition のリストに変換する。
    """
    keymap: List[List[KeyDefinition]] = []
    
    current_y = 0.0
    
    for row_data in raw_keymap:
        current_row: List[KeyDefinition] = []
        current_x = 0.0
        
        # 次のキーに適用されるデフォルト値
        next_width = 1.0
        next_height = 1.0
        
        for item in row_data:
            if isinstance(item, dict):
                # プロパティの上書き
                if "w" in item:
                    next_width = item["w"]
                if "h" in item:
                    next_height = item["h"]
                if "x" in item:
                    current_x += item["x"]
                if "y" in item:
                    current_y += item["y"]
                # 座標の直接指定 (VIAではあまり使われないが互換性のため)
                if "rx" in item:
                    pass # 原点移動などは一旦無視
            
            elif isinstance(item, str):
                # キーの定義 ("row,col" 形式)
                try:
                    r, c = map(int, item.split(","))
                    key_def = KeyDefinition(
                        x=current_x,
                        y=current_y,
                        row=r,
                        col=c,
                        w=next_width,
                        h=next_height
                    )
                    current_row.append(key_def)
                    
                    # 座標を更新
                    current_x += next_width
                    # デフォルトに戻す
                    next_width = 1.0
                    next_height = 1.0
                except (ValueError, AttributeError):
                    # ラベルなどの場合はスキップするか、デフォルト処理
                    pass
        
        keymap.append(current_row)
        current_y += 1.0 # 次の行へ
        
    return keymap
