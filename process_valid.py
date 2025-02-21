import json

valid_data_path = "noshare/valid_data.json"

with open(valid_data_path, "r") as f:
    valid_data = json.load(f)
valid_data = valid_data["data"]
sub_valid_data = []


valid_label_path = "noshare/valid_label.json"

with open(valid_label_path, "r") as f:
    valid_labels = json.load(f)

sub_valid_labels = {}

cnt = 0
for data in valid_data:
    label = valid_labels[data["id"]]
    if label != "null":
        sub_valid_data.append(data)
        sub_valid_labels[data["id"]] = label
        cnt += 1
    if cnt >= 20:
        break

with open("data/valid_labels_sub.json", "w") as f:
    json.dump(sub_valid_labels, f, indent=2)

with open("data/valid_data_sub.json", "w") as f:
    json.dump({"version": "valid", "data": sub_valid_data}, f, indent=2)