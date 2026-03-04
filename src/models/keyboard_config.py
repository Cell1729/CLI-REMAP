from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional

class KeyDefinition(BaseModel):
    x: float
    y: float
    row: int
    col: int
    w: float = 1.0
    h: float = 1.0

class KeyboardLayout(BaseModel):
    keymap: Any

    @validator("keymap", pre=True)
    def parse_if_raw(cls, v):
        # もし要素がリストのリストで、かつ中の要素が辞書や文字列（"0,0"など）ならパースが必要
        if isinstance(v, list) and len(v) > 0 and isinstance(v[0], list):
            # 最初の行の最初の要素が KeyDefinition の辞書形式（x, y, row, col を持つ）かチェック
            first_item = v[0][0]
            if isinstance(first_item, dict) and "row" in first_item and "col" in first_item and "x" in first_item:
                # 既にパース済み
                return v
            else:
                # 生の VIA 形式と判断してパース
                from src.utils.via_parser import parse_via_layout
                return parse_via_layout(v)
        return v

class KeyboardConfig(BaseModel):
    name: str
    vendorId: str
    productId: str
    matrix: Dict[str, int]
    layouts: KeyboardLayout

    @property
    def vid(self) -> int:
        return int(self.vendorId, 16)

    @property
    def pid(self) -> int:
        return int(self.productId, 16)
