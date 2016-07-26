
import os
import subprocess
import sys

if __name__ == '__main__':
    text = subprocess.check_output('qstat -a | grep pn2yr', shell=True)
    final_commands = []
    divisor = 10
    if len(sys.argv) > 1:
        divisor = int(sys.argv[1])
    for e in [ f[:f.find('.itc pn2yr')] for f in text.split('\n') if len(f)>2]:
        final_commands.append('qdel '+e)
    bash_command = ''
    for i,e in enumerate(final_commands):
        bash_command += e
        if (i%divisor)==0:
            bash_command += ' ; '
        else:
            bash_command += ' & '
#    bash_command = ' & '.join(final_commands)
    print bash_command
    os.system(bash_command)

