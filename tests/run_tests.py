#!/usr/bin/python3
"""
Run the test suite.

Usage::

    python3 run_tests.py
    python3 run_tests.py -v # verbose mode
"""
import faulthandler
import os.path
import shutil
import subprocess
import sys


VERBOSE = False


def run_command(args, **kw):
    proc = subprocess.run(args)
    if proc.returncode:
        sys.exit(proc.returncode)
    return proc


def display_title(title):
    if not VERBOSE:
        return

    print(title)
    print("=" * len(title))
    print()


def build_ext():
    display_title("Build the C extension")
    if os.path.exists("build"):
        shutil.rmtree("build")
    include_dir = os.path.normpath(os.path.join(os.getcwd(), '..'))
    os.environ['CFLAGS'] = "-I .."
    cmd = [sys.executable, "setup.py", "build"]
    if VERBOSE:
        run_command(cmd)
        print()
    else:
        proc = subprocess.run(cmd,
                              stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT,
                              universal_newlines=True)
        if proc.returncode:
            print(proc.stdout.rstrip())
            sys.exit(proc.returncode)


def import_tests():
    pythonpath = ''
    for name in os.listdir("build"):
        if name.startswith('lib.'):
            pythonpath = os.path.join("build", name)

    sys.path.append(pythonpath)
    import test_pythoncapi_compat
    return test_pythoncapi_compat


def _run_tests(tests, verbose):
    for name, test_func in tests:
        if verbose:
            print(f"{name}()", flush=True)
        test_func()


def _check_refleak(test_func, verbose):
    nrun = 6
    for i in range(1, nrun + 1):
        if verbose:
            if i > 1:
                print()
            print(f"Run {i}/{nrun}:")

        init_refcnt = sys.gettotalrefcount()
        test_func()
        diff = sys.gettotalrefcount() - init_refcnt;

        if i > 3 and diff:
            raise AssertionError(f"refcnt leak, diff: {diff}")


def run_tests(testmod):
    display_title("Run tests")

    check_refleak = hasattr(sys, 'gettotalrefcount')

    tests = [(name, getattr(testmod, name))
             for name in dir(testmod)
             if name.startswith("test")]

    def test_func():
        _run_tests(tests, VERBOSE)

    if check_refleak:
        _check_refleak(test_func, VERBOSE)
    else:
        test_func()

    if VERBOSE:
        print()

    ver = sys.version_info
    build = 'debug' if hasattr(sys, 'gettotalrefcount') else 'release'
    msg = f"{len(tests)} tests succeeded!"
    msg = f"Python {ver.major}.{ver.minor} ({build} build): {msg}"
    if check_refleak:
        msg = f"{msg} (no reference leak detected)"
    print(msg)


def main():
    global VERBOSE
    VERBOSE = "-v" in sys.argv[1:]

    faulthandler.enable()

    src_dir = os.path.dirname(__file__)
    if src_dir:
        os.chdir(src_dir)

    build_ext()
    mod = import_tests()
    run_tests(mod)


if __name__ == "__main__":
    main()
