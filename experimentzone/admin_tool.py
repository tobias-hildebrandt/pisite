#!/usr/bin/env python3

import json
import os
import argparse
import getpass
import stat

# TODO: create default scripts
# TODO: if file contains {}, treat it as empty
# TODO: print to stderr
# TODO: disallow write permissions to directory recursively?


if __name__ == "__main__":

    DEFAULT_RELATIVE = ".pisite/validationtable.json"
    TEST_ECHO = """#!/bin/sh
echo "\\$0 is $0"
echo "\\$1 is $1"
echo "user is $USER"
date
echo "last line in script"
"""
    DEFAULT_SCRIPTS = {"TEST_ECHO": {"text":TEST_ECHO, "filename": "test_echo.sh"}}

    parser = argparse.ArgumentParser() #description="A tool for helping manage pisite validation tables.")
    parser.add_argument("--user", help="which user's validation table with which you want to interact, defaults to current user")
    parser.add_argument("--relative", "--rel", help="the relative path from the user's home to the validation table, defaults to {}".format(DEFAULT_RELATIVE))
    parser.add_argument("--location", "--loc", "--absolute", "--abs", help="the absolute path to the validation table; if this is given, do not give a user or relative path")
    parser.add_argument("--create", action="store_true", default=False, help="try create the file if it does not exist, also create default scripts")
    parser.add_argument("--read", "--print", action="store_true", default=True, help="read the table and print it")
    parser.add_argument("--overwrite", "--force", "-f", action="store_true", default=False, help="overwrite values already in the table")
    parser.add_argument("--add", "-a", nargs=2, action="append", metavar=("KEY", "DEST"), help="add an entry to the table, happens before print") # -a NAME path
    parser.add_argument("--delete", "--del", "--remove", "--rem", "-d", action="append", metavar="KEY", help="remove an entry from the table, happens before print")
    parser.add_argument("--debug", action="store_true", default=False, help="enable debug") #TODO: add verbosity
    parser.add_argument("--verbose", "-v", action="store_true", default=False, help="enable verbose output")

    namespace = parser.parse_args()

    print("pisite validation table tool".upper())
    print()
    # handle some default args

    default_user = False
    if namespace.user is None:
        namespace.user = getpass.getuser()
        default_user = True

    default_relative = False
    if namespace.relative is None:
        namespace.relative = DEFAULT_RELATIVE
        default_relative = True

    if namespace.debug:
        namespace.verbose = True

    # done handling args

    if namespace.debug:
        print("namespace: {}".format(namespace))
        print()

    # make sure that we have an absolute path xor (default + user) 
    if namespace.location and (not default_relative or not default_user):
        parser.print_help()
        exit(-1)

    # print our given absolute filepath or (user + filepath)
    if namespace.location:
        filepath = os.path.join(namespace.location)
        print("filepath (absolute): {}".format(filepath))
    else:
        filepath = os.path.join(os.path.expanduser("~{}".format(namespace.user)), namespace.relative)

        filepath_format = "filepath {which}: {path}"
        which_filepath = "(default)" if default_relative else "(from argument)"
        filepath_string = filepath_format.format(path="", which=which_filepath)

        user_format = "user {which}:{fill}{user}"
        which_user = "(default)" if default_user else "(from argument)"
        filler = " " * (len(filepath_string) - len (user_format.format(which = which_user, user="", fill = "")))
        user_string = user_format.format(which=which_user, user=namespace.user, fill=filler)
        
        # if namespace.debug:
        #     print(user_string)
        #     print(filepath_string)

        # real_width = max(len(user_string), len(filepath_string))
        #user_string = user_format.format(which=which_user, user=namespace.user, width=real_width)
        filepath_string = filepath_format.format(path=filepath, which=which_filepath)
        print(user_string)
        print(filepath_string)

    print()

    data = None
    
    try:
        # create the file if needed
        if namespace.create:
            # parent of filepath
            dir_path = os.path.abspath(os.path.join(filepath, os.pardir))

            # if the dir does not exist, attempt to create it
            if not os.path.exists(dir_path):
                print("creating directory: {}".format(dir_path))
                os.mkdir(dir_path)
                os.chmod(dir_path, stat.S_IXUSR | stat.S_IWUSR | stat.S_IRUSR)
            
            # if the file at dir_path is not actually a directory
            if not os.path.isdir(dir_path):
                print("should be a directory not a file: {}".format(dir_path))
                exit(-1)
            else:
                if os.path.exists(filepath):
                    print("file already exists: {}".format(filepath))
                    exit(-1)
                else:
                    # write the file
                    print("creating json file: {}".format(filepath))

                    # # write empty file
                    # with open(filepath, "w") as f:
                    #     json.dump({}, f)

                    # create default scripts
                    scripts_data = dict()
                    for key in DEFAULT_SCRIPTS:
                        # script path is in same dir as validation table
                        script_path = os.path.join(dir_path, DEFAULT_SCRIPTS[key]["filename"])
                        scripts_data.update({key: DEFAULT_SCRIPTS[key]["filename"]})
                        # do not overwrite
                        if not os.path.exists(script_path):
                            try:
                                with open(script_path, "w") as f:
                                    f.write(DEFAULT_SCRIPTS[key]["text"])
                                print("creating default script {} at {}".format(key, script_path))
                                # set permissions
                                os.chmod(script_path, stat.S_IXUSR | stat.S_IWUSR | stat.S_IRUSR)
                            except OSError:
                                print("unable to write default script {} to path {}, exiting...".format(key, script_path))
                                exit(-1)

                    
                    # populate file with default scripts
                    with open(filepath, "w") as f:
                        json.dump(scripts_data, f)
                    # set permissions
                    os.chmod(filepath, stat.S_IXUSR | stat.S_IWUSR | stat.S_IRUSR)
                    print()
        
        # always try to read the data
        with open(filepath) as f:
            data = json.load(f)
        
    except json.JSONDecodeError:
        print("unable to decode json file {}".format(filepath))
        exit(-1)
    except OSError:
        print("os error, maybe the file doesn't exist or you don't have permission? {}".format(filepath))
        exit(-1)

    if namespace.debug:
        print("data before: {}".format(data))
        print()

    # validate data
    end = False
    for key in data:
        if not isinstance(key, str) and not isinstance(key[data], str):
            print("invalid entry in table, KEY \"{}\" and DEST \"{}\" must both be strings".format(key, data[key]))
            end = True
    if end:
        print("exiting due to invalid entries in table...")
        exit(-1)

    # if we want to add things
    if namespace.add is not None:
        for key, dest in namespace.add:
            # if overwrite is active or key doesn't exist
            if namespace.overwrite or key not in data:
                if namespace.verbose:
                    if key in data:
                        print("overwriting KEY {}, was {}, is now {}".format(key, data[key], dest))
                    else:
                        print("adding KEY {} with data {}".format(key, dest))
                data.update({key: dest})
            else:
                print("KEY {} already in table, skipping (use --overwrite to overwrite)".format(key))
        print()
    
    # if we want to remove things
    if namespace.delete is not None:
        for key in namespace.delete:
            try:
                temp_dest = data[key]
                del data[key]
                if namespace.verbose:
                    print("deleting KEY {}, DEST was {}".format(key, temp_dest))
            except KeyError:
                print("KEY {} doesn't exist, skipping deletion".format(key))
        print()
    
    if namespace.debug:
        print("data after: {}".format(data))
        print()
    
    # write to file
    # if we were supposed to change anything
    if namespace.add is not None or namespace.delete is not None:
        try:
            # overwrite
            with open(filepath, "w") as f:
                json.dump(data, f, indent=4)
        except OSError:
            print("unable to write to file, maybe you don't have permission? {}".format(filepath))
            exit(-1)

    if namespace.read:
        # find maximum key and dest width
        key_width = 0
        dest_width = 0
        for key in data:
            key_width = len(key) if (len(key) > key_width) else key_width
            dest_width = len(data[key]) if (len(data[key]) > dest_width) else dest_width

        # add padding to fit maxiumum of each
        format_string = "{key:>{key_width}} | {dest:>{dest_width}}"
        
        header_line_string = format_string.replace(">", "^").format(key="KEY", dest="DEST", key_width=key_width, dest_width=dest_width)
        separator_string_width = (len(header_line_string))
        separator_string = "-" * separator_string_width #len(format_string.format(key="", dest="", key_width=key_width, dest_width=dest_width))

        #print("format string = {}".format(format_string))

        print(separator_string)
        print(header_line_string)
        print(separator_string)
        for key in data:
            print(format_string.format(key=key, dest=data[key], key_width=key_width, dest_width=dest_width))
        print(separator_string)
