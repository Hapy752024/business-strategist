"""Bridge a local Node scaffold through the shared publication adapter."""
import argparse
import subprocess
from pathlib import Path
from case_outputs import cases, run_staged


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--inspect', action='store_true')
    p.add_argument('--file', action='store_true')
    p.add_argument('--destination', required=True, type=Path)
    p.add_argument('command', nargs=argparse.REMAINDER)
    a = p.parse_args()
    if a.inspect:
        print('managed' if cases.locate_publication(a.destination) else 'standalone')
        return
    command = a.command[1:] if a.command[:1] == ['--'] else a.command
    if len(command) < 3:
        raise ValueError('expected node, script and output path')
    def run(stage):
        target = stage / a.destination.name if a.file else stage
        result = subprocess.run([*command[:2], str(target), *command[3:]], capture_output=True, text=True)
        if result.returncode:
            raise ValueError(result.stderr or result.stdout)
        print(result.stdout, end='')
    run_staged(a.destination.parent if a.file else a.destination, 'website', run,
               include=[a.destination.name] if a.file else ['scaffold-command.txt'])


if __name__ == '__main__':
    main()
