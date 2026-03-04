import qmk_via_api
from qmk_via_api import scan_keyboards

def inspect_api():
    devices = scan_keyboards()
    if not devices:
        print("No devices found")
        return
    
    device = devices[0]
    api = qmk_via_api.KeyboardApi.from_device(device)
    
    print("Methods in KeyboardApi:")
    for method in dir(api):
        if not method.startswith("_"):
            print(f"- {method}")

if __name__ == "__main__":
    inspect_api()
