
import argparse
import logging
logging.basicConfig()

logging.basicConfig(level=logging.DEBUG)

import killer
from killer import NotCrossedLimitError

def main(args):
    pidfile = args.pidfile
    limit = args.threshold

    try:
        
        pid = killer.Pstree.read_pid(pidfile)
        
        try:
            memory_used = killer.Pstree.memory_used_by_process(pidfile)
            
            if memory_used > limit:
                process = killer.Pstree()
                process.exterminator(process)
            else:
                raise NotCrossedLimitError(pid, limit)
        
        except OSError as e:
            logging.error(str(e))
            logging.error("OS issue")

    except NotCrossedLimitError as e:
            logging.error(str(e))
            logging.error("Limit has not been reached")
    except Exception as e:
        logging.error(str(e))
        logging.error("some other exception has happened")
    finally:
        logging.debug("fin")
        

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='pid_killer')
    parser.add_argument('-p','--pidfile', help='Input file name', required=True, type=str)
    parser.add_argument('-t','--threshold', help='Threshold of memory to check', required=True, type=int)
    args = parser.parse_args()
    print(args)
    main(args)
