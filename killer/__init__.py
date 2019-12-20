import signal
import errno
import time
import datetime
import os
import utils
import getpass


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
            r = os.system(cmd)
            Calculus.Log.Log().log("cmd: %s :: exit_code: %s" % (cmd, r))
        except:
            pass

        if os.getuid() != 0:
            try:
                cmd = "sudo -n kill -%d %s 2>/dev/null" % (the_signal, pid)
                r = os.system(cmd)
                Calculus.Log.Log().log("cmd: %s :: exit_code: %s" % (cmd, r))
            except:
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
        Calculus.Log.Log().log("Stoping: %d" % pid)

        self.really_kill(pid, signal.SIGSTOP)

        kids = self.children(pid)
        for kid in kids[:]:
            kids.extend(self.send_stop_recursively(kid))

        return kids


    def massacre(self, the_pid, kill_signal=signal.SIGKILL, two_phase=False):

        if two_phase:
            kill_signal = signal.SIGABRT

        out = subprocess.Popen(
            "ps faux", stdout=subprocess.PIPE, shell=True).communicate()[0]
        Calculus.Log.Log().log(out, only_to_file=True)

        if kill_signal == signal.SIGKILL:
            # first, we send SIGSTOP to everybody, so that nobody will start any new processes when we iteratively send SIGKILL.
            # there's still a race here, but now it's marginally smaller.
            #
            the_pids = self.send_stop_recursively(the_pid)

            for pid in reversed(the_pids):
                Calculus.Log.Log().log("Killing (child): %d" % pid)
                self.really_kill(pid, signal.SIGKILL)

            self.really_kill(the_pid, signal.SIGKILL)
        else:
            the_pids = self.children(the_pid, recurse=True)
            Calculus.Log.Log().log("the_pids: %s" % the_pids)
            for pid in reversed(the_pids):
                Calculus.Log.Log().log("Killing(%s) (child): %d" % (kill_signal, pid))
                self.really_kill(pid, kill_signal)

            Calculus.Log.Log().log("Killing(%s) (parent): %d" % (kill_signal, the_pid))
            self.really_kill(the_pid, kill_signal)

            # some tests actually catch SIGABRT and want to clean up. give them time.
            # uncaught SIGABRT causes a (desired) core dump. on busy systems, we need lots
            # of time to dump the whole thing and avoid a truncated core
            time.sleep(64)

            # because we did not SIGSTOP these guys, they might have spawned some children while we were
            # sending them whatever signal we just sent them.

            for pid in the_pids:
                self.massacre(pid)
            self.massacre(the_pid)