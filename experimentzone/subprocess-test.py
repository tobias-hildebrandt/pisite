
import subprocess
import tempfile
import os
import sys
import threading

def monitor_stream(stream):
    with open(stream.name, "r") as read_stream:
        while True:
            line = read_stream.readline().rstrip("\n")

            if line is None or line == "":
                print("see blank or None line on {}".format(read_stream.name))
                # break
            # only look for return code on stdout
            else:
                print(line)

if __name__ == "__main__":
    directory = os.path.abspath(os.path.dirname(os.path.abspath(__file__)))

    tmpdir = tempfile.TemporaryDirectory(dir=directory, prefix="tempdir")

    print("tmpdir is {}".format(tmpdir.name))

    temp_file_stdout = os.mkfifo(os.path.join(tmpdir.name, "tmpout"))
    temp_file_stderr = os.mkfifo(os.path.join(tmpdir.name, "tmperr"))
    temp_file_stdin = os.mkfifo(os.path.join(tmpdir.name, "tmpin"))

    proc = subprocess.Popen(["sh"], stdin=temp_file_stdin, stdout=temp_file_stdout, stderr=temp_file_stderr, bufsize=1, universal_newlines=True)

    with open(temp_file_stdin, "w") as stdin:
        stdin.write("echo hello")

    thread_out = threading.Thread(target=monitor_stream, args=(temp_file_stdout,))
    thread_err = threading.Thread(target=monitor_stream, args=(temp_file_stderr,))

    thread_out.start()
    thread_err.start()

    

    os.unlink(temp_file_stdout)
    os.unlink(temp_file_stderr)
    os.unlink(temp_file_stdin)
  
    tmpdir.cleanup()