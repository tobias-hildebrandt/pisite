import os

print ("cwd is " + os.getcwd())

file = open("testfile.txt.old", 'r+') # r+ allows read and write


lines = file.readlines()

file.close()

print(file.name)

for line in lines:
    print(line)
    
file.close()

with open("testfile.txt.old") as f2:
    lines2 = f2.readlines()
    for line2 in lines2:
        print(line2)