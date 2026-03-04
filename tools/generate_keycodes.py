import json
import sys
import os

# プロジェクトルート
PROJECT_ROOT = r"c:\Users\sabax\Repositories\CLI-REMAP"
sys.path.append(PROJECT_ROOT)

try:
    from data.keycodes_v5 import keycodes_v5
    from data.keycodes_v6 import keycodes_v6
except ImportError as e:
    print(f"Error importing v5/v6: {e}")
    sys.exit(1)

def categorize(name):
    name_upper = name.upper()
    
    # layers
    layer_prefixes = ["MO(", "TO(", "DF(", "TG(", "TT(", "OSL(", "LT", "PDF(", "QK_LAYER", "QK_MOMENTARY", "QK_DEF_LAYER", "QK_TO", "QK_TOGGLE_LAYER"]
    if any(name.startswith(p) for p in layer_prefixes):
        return "layers"
    
    # MACRO
    if name.startswith("M") and name[1:2].isdigit():
        return "MACRO"
    if "MACRO" in name_upper:
        return "MACRO"
        
    # Media
    media_keywords = ["VOL", "MUTE", "MPLY", "MNXT", "MPRV", "MSTP", "EJCT", "PWR", "SLEP", "WAKE", "BRIU", "BRID", "MAIL", "CALC", "MYCM"]
    if any(k in name_upper for k in media_keywords):
        return "Media"
        
    # Lighting
    lighting_prefixes = ["RGB_", "BL_", "RM_"]
    if any(name_upper.startswith(p) for p in lighting_prefixes):
        return "Lighting"
        
    # special
    special_keywords = ["MS_", "BTN", "WH_", "ACL", "QK_BOOT", "QK_CLEAR", "MAGIC_", "F13", "F14", "F15", "F16", "F17", "F18", "F19", "F20", "F21", "F22", "F23", "F24"]
    # 記号系も special へ
    symbols = ["TILD", "EXLM", "AT", "HASH", "DLR", "PERC", "CIRC", "AMPR", "ASTR", "LPRN", "RPRN", "UNDS", "PLUS", "LCBR", "RCBR", "LT", "GT", "COLN", "PIPE", "QUES", "DQUO"]
    if any(k in name_upper for k in special_keywords) or any(name_upper == f"KC_{s}" for s in symbols):
        return "special"
        
    return "basic" 

def main():
    # v5, v6 を統合
    all_kc = keycodes_v5.kc.copy()
    all_kc.update(keycodes_v6.kc)
    
    output_data = []
    seen = set()
    
    for name, code_int in all_kc.items():
        if name.endswith("(kc)"):
            continue
            
        category = categorize(name)
        display_name = name.replace("KC_", "")
        code_hex = f"0x{code_int:04x}"
        
        entry = (display_name, code_hex, category)
        if entry not in seen:
            output_data.append({
                "name": display_name,
                "code": code_hex,
                "category": category
            })
            seen.add(entry)
    
    # 名前でソート
    output_data.sort(key=lambda x: (x["category"], x["name"]))
    
    json_path = os.path.join(PROJECT_ROOT, "data", "keycodes.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"Generated {len(output_data)} keycodes into data/keycodes.json")

if __name__ == "__main__":
    main()
