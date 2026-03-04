import qmk_via_api
from qmk_via_api import scan_keyboards

devices = scan_keyboards()
if not devices:
    print("No devices found")
    raise SystemExit(0)

dev = devices[0]
api = qmk_via_api.KeyboardApi.from_device(dev)

print(f"Protocol version {api.get_protocol_version()}")
print(f"Layers count: {api.get_layer_count()}")

original = api.get_key(0, 0, 0)
api.set_key(0, 0, 0, original)