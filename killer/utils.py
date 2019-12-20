import subprocess
import os

class ExecuteErrorException(Exception):
    def __init__(self, cmd, msg=None):
        if msg is None:
            msg = "An exception has happened while executing the command: {0}".format(cmd)
        super(ExecuteErrorException, self).__init__(msg)
            



class Utils(object):   

    @staticmethod
    def getlogin(default_username="None"):
        try:
            login = os.getlogin()
        except OSError:
            login = default_username
        return login
    
   
    @staticmethod
    def debug(s):
        '''
        Prints debugging information if post-review was run with --debug
        '''
        #if DEBUG or options and options.debug:
        print(">>> %s" % s)


    @staticmethod
    def execute(command, env=None, split_lines=False, ignore_errors=False, extra_ignore_errors=(), translate_newlines=True,  shell=False):
        '''
        Utility function to execute a command and return the output.
        '''
        if isinstance(command, list):
            Utils.debug(subprocess.list2cmdline(command))
        else:
            Utils.debug(command)

        try:
            p = subprocess.Popen(command,
                                stdin=None,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT,
                                shell=shell,
                                close_fds=True,
                                universal_newlines=translate_newlines,
                                env=env)
        except OSError as e:
            print("Oops, get an error...errno={0}".format(e.errno))
            print("Error = {0}".format(e))
            raise ExecuteErrorException(command, "{0}\n{1}".format(e.errno, e.with_traceback))
        
        if split_lines:
            data = p.stdout.readlines()
        else:
            data = p.stdout.read()
            
        rc = p.wait()
        if rc and not ignore_errors and rc not in extra_ignore_errors:
            raise ExecuteErrorException(command, "Incorrect Command")

        return data
    

    @staticmethod
    def read_pid(pidfile):
        try:
            with open(pidfile, mode='r') as f:
                pid = f.readlines()[0]
            
            return int(pid)
        except FileNotFoundError:
            raise ProcessLookupError("Process does not exist")

    
    @staticmethod
    def memory_used_by_process(pidfile):
        memory = {}
        try:
            pid = Utils.read_pid(pidfile)
            pid_dir = os.path.join('/','proc', str(pid))
            map_file_pid = os.path.join(pid_dir, 'maps')
            with open(map_file_pid, mode='r') as mmap:
                memory_map = mmap.readlines()
            for mem in memory_map:
                # this is in bytes
                memory[mem.split()[0]] = int(mem.split()[4])
            
            return sum(memory.values())/1024

        except Exception:
            print("sorry")
            raise OSError("Memory utilisation computation failed")


            


#a = Utils.read_pid('/var/run/gdm.pid')
#print(a, type(a))
print(Utils.memory_used_by_process('/var/run/docker.pid'))