import qmk_via_api
from qmk_via_api import scan_keyboards
import inspect

def test_macro_api():
    devices = scan_keyboards()
    if not devices:
        print("No devices found")
        return
    
    api = qmk_via_api.KeyboardApi.from_device(devices[0])
    
    print(f"get_macro_bytes signature: {inspect.signature(api.get_macro_bytes)}")
    print(f"get_macro_count: {api.get_macro_count()}")
    
    try:
        # 0番目のマクロを取得してみる
        m0 = api.get_macro_bytes(0)
        print(f"Macro 0 bytes: {m0}")
        if m0:
            print(f"Macro 0 decoded: {m0.decode('utf-8', errors='ignore')}")
    except Exception as e:
        print(f"Error reading macro 0: {e}")

if __name__ == "__main__":
    test_macro_api()
