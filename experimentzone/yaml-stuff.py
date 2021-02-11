
import yaml

test_set = {"one", "two", "three", "red", "blue", "green"}
test_list = ["one", "two", "three", "four"]
test_dict = {"one": 1, "two": "two", "3": 0xdeadbeef}
test_dict2 = {"innerdict": {"one": "123", "insiderset": {1, 2, 3}}, "asdads": [4, 5, 7] }

# print(yaml.dump(test_set))
# print(yaml.dump(test_list))
# print(yaml.dump(test_dict))
print(yaml.dump(test_dict2))

filename = "experimentzone/testyaml.yaml"

dump_obj = test_dict2

with open(filename, 'w') as f:
    yaml.dump(dump_obj, f, indent=2)


with open(filename, 'r') as f:
    data = yaml.load(f, Loader=yaml.FullLoader)
    print("type of data: %s" % type(data))
    print(data)

