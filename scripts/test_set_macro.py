import qmk_via_api
from qmk_via_api import scan_keyboards
import inspect

def test_set_macro_api():
    devices = scan_keyboards()
    if not devices:
        return
    api = qmk_via_api.KeyboardApi.from_device(devices[0])
    print(f"set_macro_bytes signature: {inspect.signature(api.set_macro_bytes)}")

if __name__ == "__main__":
    test_set_macro_api()
