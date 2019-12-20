Write a script to kill a process if its memory size (RSS) is greater than a specified value. The process is identified using a pid file. The script will be invoked this way -

  pid_killer <pid_file> <memory-in-MB>
  pid_killer /var/run/my-process.pid 400

It should also produce helpful messages on STDOUT.
  Killed pid: 43568       # if mem-usage > limit
  Not killed pid: 43568   # if mem-usage < limit

If the process doesn't exist, or the pid_file is missing, it should show a useful message on STDERR and exit.
It can be written in any scripting language (Bash, Ruby or Python), but should not need any installation. We'll test it on a Ubuntu Linux machine.


Example  : 
`(venv) debaprid@debaprid-ubuntu:~/Desktop/TaskKiller$ sudo python pid_killer.py
usage: pid_killer.py [-h] -p PIDFILE -t THRESHOLD
pid_killer.py: error: argument -p/--pidfile is required
(venv) debaprid@debaprid-ubuntu:~/Desktop/TaskKiller$`


Usage : `sudo python pid_killer.py -p /var/run/atopacctd.pid -t 122`
