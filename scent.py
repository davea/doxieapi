from subprocess import call
from sniffer.api import runnable

test_files = [
    'grab.py'
]

@runnable
def execute_tests(*args):
    fn = [ 'python', '-m', 'doctest' ] + test_files
    fn += args[1:]
    print(" ".join(fn))
    return call(fn) == 0

@runnable
def execute_script(*args):
    fn = [ 'python', 'grab.py' ]
    fn += args[1:]
    print(" ".join(fn))
    return call(fn) == 0
