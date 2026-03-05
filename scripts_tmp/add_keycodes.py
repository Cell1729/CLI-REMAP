import json

data = json.load(open('data/keycodes.json', encoding='utf-8'))

new_keys = [
    # --- Grave Escape ---
    {'name': 'Grave ESC',    'code': '0x7e00', 'category': 'grave_escape'},

    # --- Space Cadet ---
    {'name': '*Ctrl(',       'code': '0x7c60', 'category': 'space_cadet'},
    {'name': 'Ctrl*)',       'code': '0x7c62', 'category': 'space_cadet'},
    {'name': '*Shift(',      'code': '0x7c50', 'category': 'space_cadet'},
    {'name': 'Shift*)',      'code': '0x7c58', 'category': 'space_cadet'},
    {'name': '*Alt(',        'code': '0x7c64', 'category': 'space_cadet'},
    {'name': 'Alt*)',        'code': '0x7c66', 'category': 'space_cadet'},
    {'name': 'Shift*Enter',  'code': '0x7c1e', 'category': 'space_cadet'},

    # --- One Shot Mods (OSM) ---
    {'name': '*Ctrl',        'code': '0x5501', 'category': 'one_shot'},
    {'name': '*Shift',       'code': '0x5502', 'category': 'one_shot'},
    {'name': '*Alt',         'code': '0x5504', 'category': 'one_shot'},
    {'name': '*Win',         'code': '0x5508', 'category': 'one_shot'},
    {'name': 'Ctrl*',        'code': '0x5510', 'category': 'one_shot'},
    {'name': 'Shift*',       'code': '0x5520', 'category': 'one_shot'},
    {'name': 'Alt*',         'code': '0x5540', 'category': 'one_shot'},
    {'name': 'Win*',         'code': '0x5580', 'category': 'one_shot'},

    # --- One Shot Keys feature ---
    {'name': 'OS On',        'code': '0x7260', 'category': 'one_shot'},
    {'name': 'OS Off',       'code': '0x7261', 'category': 'one_shot'},
    {'name': 'OS Tog',       'code': '0x7262', 'category': 'one_shot'},

    # --- Swap Hands ---
    {'name': 'SH TG',        'code': '0x5696', 'category': 'swap_hands'},
    {'name': 'SH TT',        'code': '0x5697', 'category': 'swap_hands'},
    {'name': 'SH_MON',       'code': '0x5698', 'category': 'swap_hands'},
    {'name': 'SH_MOFF',      'code': '0x5699', 'category': 'swap_hands'},
    {'name': 'SH OFF',       'code': '0x569a', 'category': 'swap_hands'},
    {'name': 'SH ON',        'code': '0x569b', 'category': 'swap_hands'},

    # --- Key Override ---
    {'name': 'KO Tog',       'code': '0x7270', 'category': 'key_override'},
    {'name': 'KO On',        'code': '0x7271', 'category': 'key_override'},
    {'name': 'KO Off',       'code': '0x7272', 'category': 'key_override'},

    # --- Tapping Term ---
    {'name': 'DT Print',     'code': '0x7280', 'category': 'tapping_term'},
    {'name': 'DT Up',        'code': '0x7281', 'category': 'tapping_term'},
    {'name': 'DT Down',      'code': '0x7282', 'category': 'tapping_term'},

    # --- Auto Correct ---
    {'name': 'AC On',        'code': '0x7290', 'category': 'auto_correct'},
    {'name': 'AC Off',       'code': '0x7291', 'category': 'auto_correct'},
    {'name': 'AC Tog',       'code': '0x7292', 'category': 'auto_correct'},

    # --- Repeat Key ---
    {'name': 'Rep Key',      'code': '0x7220', 'category': 'repeat_key'},
    {'name': 'Alt Rep',      'code': '0x7221', 'category': 'repeat_key'},

    # --- Key Lock ---
    {'name': 'Key Lock',     'code': '0x7230', 'category': 'key_lock'},

    # --- Caps Word ---
    {'name': 'CW Tog',       'code': '0x7240', 'category': 'caps_word'},

    # --- PGDN (missing from basic) ---
    {'name': 'PGDN',         'code': '0x4e',   'category': 'basic'},

    # --- SPECIAL / COMMAND ---
    {'name': 'Pause',        'code': '0x48',   'category': 'special'},
    {'name': 'Execute',      'code': '0x74',   'category': 'special'},
    {'name': 'Select',       'code': '0x77',   'category': 'special'},
    {'name': 'Cancel',       'code': '0x9b',   'category': 'special'},
    {'name': 'Clear',        'code': '0x9c',   'category': 'special'},
    {'name': 'SysReq',       'code': '0x9a',   'category': 'special'},
    {'name': 'Prior',        'code': '0x8d',   'category': 'special'},
    {'name': 'Menu',         'code': '0x76',   'category': 'special'},
    {'name': 'Alt Erase',    'code': '0x99',   'category': 'special'},
    {'name': 'ExSel',        'code': '0xa4',   'category': 'special'},
]

existing_codes = {kc['code'].lower() for kc in data}

added = 0
for nk in new_keys:
    if nk['code'].lower() not in existing_codes:
        data.append(nk)
        existing_codes.add(nk['code'].lower())
        added += 1
    else:
        print(f"  skip duplicate: {nk['name']} ({nk['code']})")

json.dump(data, open('data/keycodes.json', 'w', encoding='utf-8', newline=''), indent=4, ensure_ascii=False)
print(f'Added {added} keys. Total: {len(data)}')
