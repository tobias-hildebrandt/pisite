#!/usr/bin/env python3

import json
import os
import argparse
import getpass

# TODO: create default scripts
# TODO: if file contains {}, treat it as empty

if __name__ == "__main__":

    parser = argparse.ArgumentParser() #description='A tool for helping manage pisite validation tables.')
    parser.add_argument("--user", "-u", default=getpass.getuser(), help="which user's validation table with which you want to interact")
    parser.add_argument("--relative", "-r", default=".pisite/validationtable", help="the relative path from the user's home to the validation table")
    parser.add_argument("--file", "-f", help="the absolute path to the validation table; if this is given, do not give a user or relative path")
    parser.add_argument("--create", action='store_true', default=False, help="try create the file if it does not exist")
    parser.add_argument("--read", action='store_true', default=True, help="read the table and print it")
    parser.add_argument("--add", "-a", nargs=2, type=str, metavar=("KEY", "DEST"), help="add an entry to the table") # -a NAME path
    parser.add_argument("--delete", "--del", "--remove", "--rem", "-d", metavar="KEY", help="remove an entry from the table")

    namespace = parser.parse_args()

    if namespace.file and (namespace.user or namespace.relative_path):
        parser.print_help()
        exit(-1)

    if namespace.file:
        filepath = os.path.join(namespace.file)
    else:
        filepath = os.path.join(os.path.expanduser("~%s" % namespace.user), namespace.relative)

    print("using filepath %s" % filepath)
    try:
        if namespace.create:
            dir_path = os.path.abspath(os.path.join(filepath, os.pardir))

            # if the dir does not exist, attempt to create it
            if not os.path.exists(dir_path):
                print("creating directory: %s" % dir_path)
                os.mkdir(dir_path)
            
            # if the file at dir_path is not actually a directory
            if not os.path.isdir(dir_path):
                print("should be a directory not a file: %s" % dir_path)
            else:
                if os.path.exists(filepath):
                    print("file already exists: %s" % filepath)
                else:
                    # write the file
                    print("creating empty json file: %s" % filepath)
                    with open(filepath, 'w') as f:
                        json.dump({}, f)
        else:
            with open(filepath) as f:
                data = json.load(f)
            print(data)
    except json.JSONDecodeError:
        print("unable to decode json file %s" % filepath)
    except OSError:
        print("os error, maybe the file doesn't exist or you don't have permission? %s" % filepath)
        
    