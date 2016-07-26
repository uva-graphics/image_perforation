#!/usr/bin/python

"""
TODO:
    Is there a better way than just keeping the tablet's IP on here as a hard constant?
    Is there a way to check if the ssh and scp actions don't complete? Besides having the GA explode halfway through?
"""

# runs this on client, will run visualizations on server

import os
import sys; sys.path += ['../visualize_results', '../solver', '../compiler']
import visualize_results
import time
import pickle

VISUALIZATION_DIRECTORY = '/home/phablet/code/filter-approx/proj/visualize_results/'
DESTINATION_DIRECTORY = '/home/phablet/code/filter-approx/proj/temp/'
NUMBER_OF_TRIES = 10

def visualize_remotely(approx_files_location, approx_files, program_name, store_location, server_ip):
    approx_files_location = os.path.abspath(approx_files_location)
    approx_files = map(lambda s: os.path.split(s)[1], approx_files)
    store_location = os.path.abspath(store_location)+'/'
    
    list_of_file_names = sorted([ os.path.join(approx_files_location,f) for f in os.listdir(approx_files_location) if os.path.isfile(os.path.join(approx_files_location,f)) and f[-7:]=='.approx' and os.path.split(f)[1] in approx_files])
    
    ans = []
    
    normal_out_created = False
    
    print 
    print 'Getting timings from tablet.'
    for file_name in list_of_file_names:
        result = None
        print 
        print "#"*90
        for i in xrange(NUMBER_OF_TRIES):
            try:
                print 
                print os.path.split(os.path.relpath(file_name))[1]+' Attempt '+str(i)+'.'
                print 'Clearing old results from last chromosome.'
                #os.system("ssh phablet@"+server_ip+" '(rm -rf "+DESTINATION_DIRECTORY+"*)'")
                os.system("ssh phablet@"+server_ip+" '(rm -rf "+DESTINATION_DIRECTORY+"results/visualize_results_ans_dump.p)'")
                print 'Copying '+os.path.relpath(file_name)+' over.'
                os.system('scp '+file_name+' phablet@'+server_ip+':'+DESTINATION_DIRECTORY) 
                commands = ';'.join(("""
cd """+VISUALIZATION_DIRECTORY+"""
python -c \"import visualize_results;visualize_results.visualize_results([\\\""""+os.path.join(DESTINATION_DIRECTORY, os.path.split(file_name)[1])+"\\\"], \\\""+DESTINATION_DIRECTORY+"results/\\\", \\\""+program_name+"""\\\", run_normally="""+str(not normal_out_created)+""", use_relative_times=True)\"
""").split('\n')[1:])
                print "Approx File Contents:",open(file_name, 'r').read(), '\n'
                print 'Running commands on server.'
                os.system("ssh phablet@"+server_ip+" '("+commands+")'") 
                print 'Copying data back from server to client'
                os.system("scp phablet@"+server_ip+":"+DESTINATION_DIRECTORY+"results/visualize_results_ans_dump.p "+store_location)
                result = pickle.load( open(store_location+"visualize_results_ans_dump.p",'rb') )
                assert len(result)==1, "result from tablet has a number of entries not equal to one"
                break
            except Exception as err:
                print "Exception:"
                print err
                pass
        if result == None:
            print "Could not run on "+os.path.relpath(file_name)+" successfully after "+str(NUMBER_OF_TRIES)+" attempts."
            result = [{'approx': os.path.split(os.path.relpath(file_name))[1], 'time': float('inf'), 'error': float('inf')}]
        normal_out_created = True
        ans += result
        
    return ans
