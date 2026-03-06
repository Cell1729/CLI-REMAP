import json
from pathlib import Path

BASE_DIR = Path(r"c:\Users\sabax\Repositories\CLI-REMAP")

# 画像から特定したキーのリストと、それに対応する QMK 名称（またはパターン）
TARGET_KEYS = {
    "basic": [
        "A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z",
        "1", "2", "3", "4", "5", "6", "7", "8", "9", "0",
        "F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "F10", "F11", "F12",
        "ESCAPE", "TAB", "BSPACE", "ENTER", "INSERT", "DELETE", "HOME", "END", "PGUP", "PGDN", "NUMLOCK", "CAPSLOCK", "PSCREEN", "SCROLLLOCK", "PAUSE",
        "KP_0", "KP_1", "KP_2", "KP_3", "KP_4", "KP_5", "KP_6", "KP_7", "KP_8", "KP_9",
        "KP_SLASH", "KP_ASTERISK", "KP_MINUS", "KP_PLUS", "KP_DOT", "KP_ENTER", "KP_EQUAL",
        "LSHIFT", "RSHIFT", "LCTRL", "RCTRL", "LGUI", "RGUI", "LALT", "RALT", "APPLICATION",
        "LEFT", "DOWN", "UP", "RIGHT", "SPACE", "MENU",
        "MINUS", "EQUAL", "LBRACKET", "RBRACKET", "BSLASH", "NONUS_HASH", "SCOLON", "QUOTE", "GRAVE", "COMMA", "DOT", "SLASH",
        "NONUS_BSLASH"
    ],
    "Media": [
        "VOLD", "VOLU", "MUTE", "MPLY", "MSTP", "MPRV", "MNXT", "MRWD", "MFFD", "MSEL", "EJCT"
    ],
    "MACRO": [f"M{i}" for i in range(16)],
    "layers": [
        "FN1", "FN2", "FN3", "FN4", "SPACE_FN1", "SPACE_FN2", "SPACE_FN3"
    ],
    "special": [
        "RO", "JYEN", "MHEN", "HENK", "KANA", "KANJI", "HANJA", "NUBS",
        "GESC", "RESET", "DEBUG", "NKRO_TG", "LCAP", "LNUM", "LSCR",
        "PWR", "SLEP", "WAKE", "CALC", "MAIL", "HELP", "STOP", "AGIN", "UNDO", "CUT", "COPY", "PSTE", "FIND", "MYCM", "WBAK", "WFWD", "WREF", "WFAV", "WSCH",
        "F13", "F14", "F15", "F16", "F17", "F18", "F19", "F20", "F21", "F22", "F23", "F24",
        "MS_U", "MS_D", "MS_L", "MS_R", "BTN1", "BTN2", "BTN3", "BTN4", "BTN5", "BTN6", "BTN7", "BTN8",
        "WH_U", "WH_D", "WH_L", "WH_R", "ACL0", "ACL1", "ACL2",
        "AU_ON", "AU_OFF", "AU_TOG", "CLICKY_TOGGLE", "CLICKY_ENABLE", "CLICKY_DISABLE", "CLICKY_UP", "CLICKY_DOWN", "CLICKY_RESET",
        "MU_ON", "MU_OFF", "MU_TOG", "MU_MOD", "ANY",
        "LS(", "RS)", "LC(", "RC)", "LA(", "RA)", "SftEnt"
    ],
    "Lighting": [
        "RGB_TOG", "RGB_MOD", "RGB_RMOD", "RGB_HUI", "RGB_HUD", "RGB_SAI", "RGB_SAD", "RGB_VAI", "RGB_VAD", "RGB_SPI", "RGB_SPD",
        "RGB_M_P", "RGB_M_B", "RGB_M_R", "RGB_M_SW", "RGB_M_SN", "RGB_M_K", "RGB_M_X", "RGB_M_G", "RGB_M_T",
        "BL_ON", "BL_OFF", "BL_TOGG", "BL_DEC", "BL_INC", "BL_STEP", "BL_BRTG", "BR_TOGG", "RM_NEXT", "RM_PREV",
        "RM_HUEU", "RM_HUED", "RM_SATU", "RM_SATD", "RM_VALU", "RM_VALD", "RM_SPDU", "RM_SPDD"
    ]
}

# エイリアス変換マップ
ALIAS_MAP = {
    # VIA名称: QMK内部名称
    "NUBS": "NONUS_BSLASH",
    "NKRO_TG": "MAGIC_TOGGLE_NKRO",
    "GESC": "GRAVE_ESC",
    "APP": "APPLICATION",
    "BSPC": "BSPACE",
    "ENT": "ENTER",
    "SPC": "SPACE",
    "SftEnt": "SFTENT",
    "LS(": "LSPO",
    "RS)": "RSPC",
    "LC(": "LCPO",
    "RC)": "RCPC",
    "LA(": "LAPO",
    "RA)": "RAPC",
    "BR_TOGG": "BL_BRTG",
    "한영": "LANG1",
    "漢字": "LANG2",
    "ANY": "QK_KB" # 便宜上
}

def load_raw_keycodes():
    import sys
    sys.path.append(str(BASE_DIR / "data"))
    
    # v6 を優先
    from keycodes_v6 import keycodes_v6
    raw_v6 = keycodes_v6.kc
    
    # v5 から補完
    try:
        from keycodes_v5 import keycodes_v5
        raw_v5 = keycodes_v5.kc
    except ImportError:
        raw_v5 = {}
    
    combined = {}
    # v5 を先に、v6 で上書き
    for k, v in raw_v5.items():
        combined[k.replace("KC_", "")] = v
    for k, v in raw_v6.items():
        combined[k.replace("KC_", "")] = v
    
    return combined

def refine():
    json_path = BASE_DIR / "data" / "keycodes.json"
    
    all_raw = load_raw_keycodes()
    refined_list = []
    seen_codes = set()
    seen_names = set()

    for cat, names in TARGET_KEYS.items():
        for name in names:
            if name in seen_names: continue
            
            # 直接一致、またはエイリアス経由で探す
            target_name = ALIAS_MAP.get(name, name)
            
            code = all_raw.get(target_name)
            if code is not None:
                if code not in seen_codes:
                    refined_list.append({
                        "name": name,
                        "code": hex(code) if isinstance(code, int) else code,
                        "category": cat
                    })
                    seen_codes.add(code)
                    seen_names.add(name)

    # レイヤーキー等の動的な生成 (0-15)
    patterns = ["MO", "TG", "TT", "OSL", "TO", "DF"]
    for x in range(16):
        for p in patterns:
            name = f"{p}({x})"
            if name in seen_names: continue
            
            code = all_raw.get(name)
            if code is not None:
                if code not in seen_codes:
                    refined_list.append({
                        "name": name,
                        "code": hex(code),
                        "category": "layers"
                    })
                    seen_codes.add(code)
                    seen_names.add(name)

    # 保存
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(refined_list, f, indent=4, ensure_ascii=False)
    
    print(f"Refined {len(refined_list)} keycodes based on complete screenshots.")

if __name__ == "__main__":
    refine()
