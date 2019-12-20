import signal
import errno
import time
import datetime
import os
import getpass
import logging
import subprocess # A fancy and flexible os.system()


glog = logging

class ExecutionError(Exception): pass
class NotCrossedLimitError(Exception):
    def __init__(self, pid, limit, msg=None):
        if msg is None:
            msg = "The {} has not crossed limit of : {1}".format(pid, limit)
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
            cmd = "kill -%d %s 2>/dev/null" % (the_signal, pid)
            r = os.system(cmd) # this is tricky call, hence not playing with subprocess
            glog.debug("cmd: %s :: exit_code: %s" % (cmd, r))
        except Exception as e:
            glog.exception(str(e))
            pass

        if os.getuid() != 0:
            try:
                cmd = "sudo -n kill -%d %s 2>/dev/null" % (the_signal, pid)
                r = os.system(cmd) # this is tricky call, hence not playing with subprocess
                glog.debug("cmd: %s :: exit_code: %s" % (cmd, r))
            except Exception as e:
                glog.exception(str(e))
                pass


    def children(self, pid, recurse=False):
        """returns an array of the children of the given process, or an empty array if no such process is known.
        """
        out = subprocess.Popen(
            "pgrep -P %d" % pid, stdout=subprocess.PIPE, shell=True).communicate()[0]

        pids = [int(line) for line in out.splitlines()]

        if recurse:
            for cpid in pids[:]:
                pids.extend(self.children(cpid, recurse=True))

        return pids


    def send_stop_recursively(self, pid):
        """stops pid process and, recursively, all of its children, returning their pids in an array if any".
        """
        glog.debug("Stopping: %d" % pid)

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
                glog.debug("Killing (child): %d" % pid)
                self.really_kill(pid, signal.SIGKILL)

            self.really_kill(the_pid, signal.SIGKILL)
        else:
            the_pids = self.children(the_pid, recurse=True)
            glog.debug("the_pids: %s" % the_pids)
            for pid in reversed(the_pids):
                glog.debug("Killing(%s) (child): %d" % (kill_signal, pid))
                self.really_kill(pid, kill_signal)

            glog.debug("Killing(%s) (parent): %d" % (kill_signal, the_pid))
            self.really_kill(the_pid, kill_signal)
            time.sleep(64)

            for pid in the_pids:
                self.exterminator(pid)
            self.exterminator(the_pid)
            
    
    @staticmethod
    def read_pid(pidfile):
        """Static Method that reads a pidfile and gets the associated pid from it
        """
        try:
            with open(pidfile, mode='r') as f:
                pid = f.readlines()[0]
            
            return int(pid)
        except FileNotFoundError:
            raise ProcessLookupError("Process does not exist")

    
    @staticmethod
    def memory_used_by_process(pidfile):
        """Static method which calculates the total memory usage of a process by reading the maps file
        """
        memory = {}
        try:
            pid = Pstree.read_pid(pidfile)
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


