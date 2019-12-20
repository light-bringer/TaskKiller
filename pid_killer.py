
import argparse
import logging

import killer
from killer import NotCrossedLimitError

def main(args):
    pidfile = args.pidfile
    limit = args.threshold

    try:
        pid = killer.Pstree.read_pid(pidfile)
        memory_used = killer.Pstree.memory_used_by_process(pid)
        if memory_used > limit:
            process = killer.Pstree()
            process.exterminator(process)
        else:
            raise NotCrossedLimitError(pid, limit)
    except NotCrossedLimitError as e:
        logging.error(e.msg)
        

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='pid_killer')
    parser.add_argument('-p','--pidfile', help='Input file name', required=True, type=str)
    parser.add_argument('-t','--threshold', help='Threshold of memory to check', required=True, type=int)
    args = parser.parse_args()
    print(args)
    main(args)