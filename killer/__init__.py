import signal
import errno
import time
import datetime
import os
import getpass
import logging
import subprocess # A fancy and flexible os.system()


glog = logging
logging.basicConfig(level=logging.DEBUG)


class ExecutionError(Exception): pass
class NotCrossedLimitError(Exception):
    def __init__(self, pid, limit, msg=None):
        if msg is None:
            msg = "The {0} has not crossed limit of : {1}".format(pid, limit)
        super(NotCrossedLimitError, self).__init__(msg)


class Pstree(object):

    def __init__(self, username=None):
        if username is not None:
            self.username = username
        else:
            self.username = getpass.getuser()

    def really_kill(self, pid, the_signal=signal.SIGKILL):
        if the_signal is None:
            the_signal = signal.SIGKILL
        
        try:
            # os.kill(pid, the_signal)
            cmd = "kill -{0} {1} 2>/dev/null".format(the_signal, pid)
            r = os.system(cmd) # this is tricky call, hence not playing with subprocess
            glog.debug("cmd: {0} :: exit_code: {1}".format(cmd, r))
        except Exception as e:
            glog.exception(str(e))
            pass

        if os.getuid() != 0:
            try:
                cmd = "sudo -n kill -{0} {1} 2>/dev/null".format(the_signal, pid)
                r = os.system(cmd) # this is tricky call, hence not playing with subprocess
                glog.debug("cmd: {0} :: exit_code: {1}".format(cmd, r))
            except Exception as e:
                glog.exception(str(e))
                pass


    def children(self, pid, recurse=False):
        """returns an array of the children of the given process, or an empty array if no such process is known.
        """
        out = subprocess.Popen(
            "pgrep -P {0}".format(int(pid)), stdout=subprocess.PIPE, shell=True).communicate()[0]

        pids = [int(line) for line in out.splitlines()]

        if recurse:
            for cpid in pids[:]:
                pids.extend(self.children(cpid, recurse=True))

        return pids


    def send_stop_recursively(self, pid):
        """stops pid process and, recursively, all of its children, returning their pids in an array if any".
        """
        glog.debug("Stopping: {0}".format(pid))

        self.really_kill(pid, signal.SIGSTOP)

        kids = self.children(pid)
        for kid in kids[:]:
            kids.extend(self.send_stop_recursively(kid))

        return kids


    def exterminator(self, the_pid, kill_signal=signal.SIGKILL, two_phase=False):

        if two_phase:
            kill_signal = signal.SIGABRT
        cmd = "ps faux"
        out = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, shell=True).communicate()[0]
        glog.debug(out)

        if kill_signal == signal.SIGKILL:
            # first, we send SIGSTOP to everybody, so that nobody will start any new processes when we iteratively send SIGKILL.
            # there's still a race here, but now it's marginally smaller.
            #
            the_pids = self.send_stop_recursively(the_pid)

            for pid in reversed(the_pids):
                glog.debug("Killing (child): {0}".format(pid))
                self.really_kill(pid, signal.SIGKILL)

            self.really_kill(the_pid, signal.SIGKILL)
        else:
            the_pids = self.children(the_pid, recurse=True)
            glog.debug("the_pids: {0}".format(the_pids))
            for pid in reversed(the_pids):
                glog.debug("Killing({0}) (child): {1}".format(kill_signal, pid))
                self.really_kill(pid, kill_signal)

            glog.debug("Killing({0}) (parent): {1}".format(kill_signal, the_pid))
            self.really_kill(the_pid, kill_signal)
            time.sleep(64)

            for pid in the_pids:
                self.exterminator(pid)
            self.exterminator(the_pid)
            
    
    @staticmethod
    def read_pid(pidfile):
        """Static Method that reads a pidfile and gets the associated pid from it
        """
        pid = -1
        try:
            with open(pidfile,'r+') as f:
                pid = f.readlines()[0]
            del(f)
            return int(pid)
        except Exception as e:
            print(str(e))
            pass

    
    @staticmethod
    def memory_used_by_process(pidfile):
        """Static method which calculates the total memory usage of a process by reading the maps file
        """
        print(pidfile)
        memory = {}
        try:
            pid = Pstree.read_pid(pidfile)
            print(pid, "pid", type(pid))
            pid_dir = os.path.join('/','proc', str(pid))
            map_file_pid = os.path.join(pid_dir, 'maps')
            print(pid_dir, map_file_pid)
            with open(map_file_pid, mode='r') as mmap:
                memory_map = mmap.readlines()
            for mem in memory_map:
                # this is in bytes
                memory[mem.split()[0]] = int(mem.split()[4])
            total_mem = sum(memory.values())
            glog.debug("Current memory utilisation: {0}".format(total_mem))
            glog.debug("Current memory utilisation: {0} KB".format(total_mem/1024))
            return total_mem/1024

        except Exception:
            print("sorry")
            raise OSError("Memory utilisation computation failed")


