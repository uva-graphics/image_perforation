import os
ls = os.linesep
#get filename
#fname = raw_input('visualization_data_absolute.csv')
def create_empty_list():
    return []
try:
    fobj = open('visualization_data_absolute.csv', 'r')  
except IOError, e:
    print 'open file error:\n',e
else:
    document_len=72
    count=0
    strline=fobj.readline()
    label_infor,label_Xtime,label_Ymean,label_Zpsnr=strline.split(',')
    #print strline,
    #print label_infor,label_Xtime,label_Ymean,label_Zpsnr
    dataInfo = create_empty_list()
    dataTime = create_empty_list()
    dataMean = create_empty_list()
    while True:
        str2=fobj.readline()
        strline=str2.split(',')
        if len(str2) ==0:
            break
        #print len(strline)
            #for element in strline:
             #   print element
        dataInfo.append(strline[0])
        dataTime.append(strline[1])
        dataMean.append(strline[2])
        #print strline[0],strline[1],strline[2]
        count+=1
       # dataInfo[count],dataTime[count],dataMean[count]=str2.split(',')    
    fobj.close()
print len(dataInfo),len(dataMean)
from pylab import *
import numpy as np
import matplotlib.pyplot as plt

x = np.linspace(0,50,2)
y = np.linspace(0,1.2,3)
plt.figure()
plt.scatter(dataMean,dataTime,color='r',marker='o',alpha=0.5)
plt.ylim([0.0, 1.2])
plt.xlim([0.0,50])
plt.ylabel('Time')
plt.xlabel('Mean Distance')
plt.title('$Time*Mean Distance$')
plt.show()
