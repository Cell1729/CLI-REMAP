from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class KeyDefinition(BaseModel):
    x: float
    y: float
    row: int
    col: int
    w: float = 1.0
    h: float = 1.0

class KeyboardLayout(BaseModel):
    keymap: List[List[KeyDefinition]]

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
