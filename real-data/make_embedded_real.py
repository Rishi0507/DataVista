import json
with open("dashboard_data_real.json", "r", encoding="utf-8") as f:
    data = json.load(f)
with open("embedded_data.js", "w", encoding="utf-8") as f:
    f.write("const DATA = ")
    json.dump(data, f, indent=2)
    f.write(";\n")
print("embedded_data.js written.")