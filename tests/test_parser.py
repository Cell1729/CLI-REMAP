import json
from pathlib import Path
import sys

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent.parent))

from src.models.keyboard_config import KeyboardConfig

def test_dz60_parsing():
    json_path = Path("data/keyboards/dz60rgb_v2.json")
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    config = KeyboardConfig(**data)
    print(f"Keyboard Name: {config.name}")
    print(f"VID: {hex(config.vid)}, PID: {hex(config.pid)}")
    
    # 最初の数キーの座標を確認
    first_row = config.layouts.keymap[0]
    print("\nFirst row keys:")
    for i, key in enumerate(first_row[:5]):
        print(f"  Key {i}: x={key.x}, y={key.y}, row={key.row}, col={key.col}, w={key.w}")

    # 特殊な幅のキーを確認 (2.25w など)
    last_key_first_row = first_row[-1]
    print(f"\nLast key first row: x={last_key_first_row.x}, w={last_key_first_row.w}, row={last_key_first_row.row}, col={last_key_first_row.col}")

if __name__ == "__main__":
    test_dz60_parsing()
