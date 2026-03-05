import json

data = json.load(open('data/keycodes.json', encoding='utf-8'))
existing_codes = {kc['code'].lower() for kc in data}

new_keys = []

# ─── MIDI NOTES (C0 ~ B5, QK_MIDI_NOTE base = 0x7103) ───
NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
for octave in range(6):          # 0 - 5
    for semitone, note in enumerate(NOTE_NAMES):
        code = 0x7103 + octave * 12 + semitone
        safe = note.replace('#', 'S')
        new_keys.append({
            'name': f'Midi {note}{octave}',
            'code': hex(code),
            'category': 'midi'
        })

# ─── MIDI OCTAVE (0x7183 ~ 0x718e) ───
for i, label in enumerate(['N2','N1','0','1','2','3','4','5','6','7']):
    new_keys.append({'name': f'Oct {label}', 'code': hex(0x7183 + i), 'category': 'midi'})
new_keys.append({'name': 'Oct Down', 'code': '0x718d', 'category': 'midi'})
new_keys.append({'name': 'Oct Up',   'code': '0x718e', 'category': 'midi'})

# ─── MIDI TRANSPOSE (0x718f ~ 0x719e) ───
for i, label in enumerate(['N6','N5','N4','N3','N2','N1','0','1','2','3','4','5','6']):
    new_keys.append({'name': f'Trans {label}', 'code': hex(0x718f + i), 'category': 'midi'})
new_keys.append({'name': 'Trans Down', 'code': '0x719d', 'category': 'midi'})
new_keys.append({'name': 'Trans Up',   'code': '0x719e', 'category': 'midi'})

# ─── MIDI VELOCITY (0x719f ~ 0x71ab) ───
for i in range(11):
    new_keys.append({'name': f'Vel {i}', 'code': hex(0x719f + i), 'category': 'midi'})
new_keys.append({'name': 'Vel Down', 'code': '0x71aa', 'category': 'midi'})
new_keys.append({'name': 'Vel Up',   'code': '0x71ab', 'category': 'midi'})

# ─── MIDI CHANNEL (0x71ac ~ 0x71bd) ───
for i in range(1, 17):
    new_keys.append({'name': f'Ch {i}', 'code': hex(0x71ac + i - 1), 'category': 'midi'})
new_keys.append({'name': 'Ch Down', 'code': '0x71bc', 'category': 'midi'})
new_keys.append({'name': 'Ch Up',   'code': '0x71bd', 'category': 'midi'})

# ─── MIDI MISC ───
midi_misc = [
    ('Midi On',       '0x7100'),
    ('Midi Off',      '0x7101'),
    ('Midi Tog',      '0x7102'),
    ('All Notes Off', '0x71be'),
    ('Sustain',       '0x71bf'),
    ('Portamento',    '0x71c0'),
    ('Sostenuto',     '0x71c1'),
    ('Soft',          '0x71c2'),
    ('Legato',        '0x71c3'),
    ('Modulation',    '0x71c4'),
    ('Mod Spd Down',  '0x71c5'),
    ('Mod Spd Up',    '0x71c6'),
    ('PB Down',       '0x71c7'),
    ('PB Up',         '0x71c8'),
]
for name, code in midi_misc:
    new_keys.append({'name': name, 'code': code, 'category': 'midi'})

# ─── SEQUENCER (approximate QMK codes) ───
sequencer = [
    ('Seq On',        '0x7200'),
    ('Seq Off',       '0x7201'),
    ('Seq Tog',       '0x7202'),
    ('Seq Tmp Down',  '0x7203'),
    ('Seq Tmp Up',    '0x7204'),
    ('Seq Res Down',  '0x7205'),
    ('Seq Res Up',    '0x7206'),
    ('Seq Steps All', '0x7207'),
    ('Seq Steps Clr', '0x7208'),
]
# Note: sequencer codes conflict with combo (0x7200-0x7202). Skip if duplicate.
for name, code in sequencer:
    new_keys.append({'name': name, 'code': code, 'category': 'sequencer'})

# ─── 重複チェックして追加 ───
added = 0
skipped = 0
for nk in new_keys:
    c = nk['code'].lower()
    if c not in existing_codes:
        data.append(nk)
        existing_codes.add(c)
        added += 1
    else:
        skipped += 1

json.dump(data, open('data/keycodes.json', 'w', encoding='utf-8', newline=''), indent=4, ensure_ascii=False)
print(f'Added: {added}, Skipped (duplicate): {skipped}, Total: {len(data)}')
