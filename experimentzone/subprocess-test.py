
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

    with tempfile.TemporaryDirectory(dir=directory, prefix="tempdir_") as tmpdir:

        print("tmpdir is {}".format(tmpdir))

        tmpdir_f = open(os.open(tmpdir, os.O_RDONLY))

        tmpdir_fd = tmpdir_f.fileno()

        temp_file_stdout = os.mkfifo(path="tmpout.pipe", dir_fd=tmpdir_fd)
        temp_file_stderr = os.mkfifo(path=os.path.join(tmpdir, "tmperr.pipe"))
        temp_file_stdin = os.mkfifo(path=os.path.join(tmpdir, "tmpin.pipe"))

        print("temp stdout is {}".format(temp_file_stdout))
        print("temp stderr is {}".format(temp_file_stderr))
        print("temp stdin is {}".format(temp_file_stdin))

        print("tmpdir is {}".format(tmpdir))

        assert(temp_file_stdout is not None)
        assert(temp_file_stderr is not None)
        assert(temp_file_stdin is not None)

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