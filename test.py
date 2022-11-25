import json

aString = '["a", "b", "1", "c"]'

print(''.join(json.loads(aString)))