import json
from src.ui.app import KeyboardRemapApp, find_matching_config
from src.keyboard_hid import KeyboardBackend

if __name__ == "__main__":
    # キーコード定義の読み込み
    try:
        with open("data/keycodes.json", "r", encoding="utf-8") as f:
            keycodes = json.load(f)
    except Exception as e:
        print(f"Error loading keycodes.json: {e}")
        exit(1)
    
    # バックエンドの初期化とデバイス接続
    backend = KeyboardBackend()
    connected = backend.find_and_connect()
    
    # 接続デバイスに一致する設定の検索
    config = None
    if connected:
        vid = backend.device.vendor_id
        pid = backend.device.product_id
        config = find_matching_config(vid, pid)

    # アプリの起動
    app = KeyboardRemapApp(config, backend, keycodes)
    app.run()
