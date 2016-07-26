import csv
import os.path 
HOME_PATH='/home/liming/Document/filter-approx/proj/ga/'
TIME_FILE='/gen100000/visualize/visualization_data_mean_lab_pareto_relative.csv'   
MEAN_PNSR_FILE='/gen100000/visualize/visualization_data_mean_lab_relative_all_images.csv'
Max_VALUE=100000.0
File_PATH='/home/liming/Document/filter-approx/proj/ga/test_minus_high_res/'
PHOTO_NEED=['man_made.txt_4_image_820x614','man_made.txt_49_image_820x614','natural.txt_3_image_820x614','natural.txt_26_image_820x614','people.txt_3_image_820x614','people.txt_46_image_820x614']
PHOTO_To_NEED=['man_made_txt_4_image_820x614','man_made_txt_49_image_820x614','natural_txt_3_image_820x614','natural_txt_26_image_820x614','people_txt_3_image_820x614','people_txt_46_image_820x614']
PHOTO_PRO=['_time','_mean_lab_error']
print (30 * '-')
print ("0: read demosaic 2 files\n")
print ("1: read median 2 files\n")
OPTION= raw_input('Enter your choice [0-1] : ')

if(OPTION=='0'):
    FOLDER='result_demosaic_full'
    FOLDER_TO='demosaic'
    FOLDER2='result_demosaic_full_loop'
    FOLDER_TO2='demosaic_loop_perf_only'
else:
    FOLDER='result_median_full'
    FOLDER_TO='median'
    FOLDER2='result_median_full_loop'
    FOLDER_TO2='median_loop_perf_only'
print FOLDER    
    
Time_filename=HOME_PATH+FOLDER+TIME_FILE
Error_filename=HOME_PATH+FOLDER+MEAN_PNSR_FILE
Time_filename2=HOME_PATH+FOLDER2+TIME_FILE
Error_filename2=HOME_PATH+FOLDER2+MEAN_PNSR_FILE
##############################################################################find the approx file name store in L_time_filename 
csvfile = open(Time_filename, 'rb')
csvReader = csv.reader(csvfile)
L=list(csvReader)
Speed=[2.0,3.0,5.0,10.0]
L_time=[]
L_time_filename=[]
L_time_value=[]

#print L[2][3] 
        
for row in range(0,len(L)):
    if(row==0):
        L_time.append(Max_VALUE)
    else:
        L_time.append(1.0/float(L[row][1]))
#print len(L_time)

for row in range(0,len(Speed)):
    maxValue=Max_VALUE
    index=0
    for row_time in range(1, len(L_time)):
        if(abs(L_time[row_time]-Speed[row])<maxValue):
            index=row_time
            maxValue=abs(L_time[index]-Speed[row])
    L_time_value.append(L_time[index])
    L_time_filename.append(L[index][0]) 
  
#print L_time_value
#print L_time_filename
csvfile.close()

##############################################################################find the approx file name store in L_time_filename2 
csvfile = open(Time_filename2, 'rb')
csvReader = csv.reader(csvfile)
L=list(csvReader)
L_time2=[]
L_time_filename2=[]
L_time_value2=[]

#print L[2][3] 
        
for row in range(0,len(L)):
    if(row==0):
        L_time2.append(Max_VALUE)
    else:
        L_time2.append(1.0/float(L[row][1]))
#print len(L_time)

for row in range(0,len(Speed)):
    maxValue=Max_VALUE
    index=0
    for row_time in range(1, len(L_time2)):
        if(abs(L_time2[row_time]-Speed[row])<maxValue):
            index=row_time
            maxValue=abs(L_time2[index]-Speed[row])
    L_time_value2.append(L_time2[index])
    L_time_filename2.append(L[index][0]) 
  
#print L_time_value
#print L_time_filename
csvfile.close()
 
##############################################################################find the time and error value, and then store in the array
Time_list=[[0 for photo_row in range(0,len(PHOTO_NEED))] for row_Speed in range(0,len(Speed))] 
Error_list=[[0 for photo_row in range(0,len(PHOTO_NEED))] for row_Speed in range(0,len(Speed))] 
Time_list2=[[0 for photo_row in range(0,len(PHOTO_NEED))] for row_Speed in range(0,len(Speed))] 
Error_list2=[[0 for photo_row in range(0,len(PHOTO_NEED))] for row_Speed in range(0,len(Speed))] 

csvfile = open(Error_filename, 'rb')
csvReader = csv.reader(csvfile)
L_error=list(csvReader)
is_in= True
for row_Speed in range(0,len(Speed)):
    for row in range(0,len(L_error)):
            if(L_error[row][0]==L_time_filename[row_Speed]):
                for photo_row in range(0,len(PHOTO_NEED)):
                    #for photo_pro in range(0,len(PHOTO_PRO)):
                    for col in range(1,len(L_error[row])):
#                        if(col<3):
#                            print col,photo_row                
#                            print File_PATH+PHOTO_NEED[photo_row]+'.png'+PHOTO_PRO[0]
#                            print L_error[0][col].strip()
                        if(File_PATH+PHOTO_NEED[photo_row]+'.png'+PHOTO_PRO[0]==L_error[0][col].strip()):
                            Time_list[row_Speed][photo_row]=float(L_error[row][col])
                            Error_list[row_Speed][photo_row]=float(L_error[row][col+1])
                            is_in= False
                            break
                                    
                break
#print is_in      
#print Time_list[0]
#print Error_list[0]
csvfile.close()
##############################################################################find the time and error value, and then store in the array 2222
Time_list2=[[0 for photo_row in range(0,len(PHOTO_NEED))] for row_Speed in range(0,len(Speed))] 
Error_list2=[[0 for photo_row in range(0,len(PHOTO_NEED))] for row_Speed in range(0,len(Speed))] 

csvfile = open(Error_filename2, 'rb')
csvReader = csv.reader(csvfile)
L_error=list(csvReader)
is_in= True
for row_Speed in range(0,len(Speed)):
    for row in range(0,len(L_error)):
            if(L_error[row][0]==L_time_filename2[row_Speed]):
                for photo_row in range(0,len(PHOTO_NEED)):
                    #for photo_pro in range(0,len(PHOTO_PRO)):
                    for col in range(1,len(L_error[row])):
#                        if(col<3):
#                            print col,photo_row                
#                            print File_PATH+PHOTO_NEED[photo_row]+'.png'+PHOTO_PRO[0]
#                            print L_error[0][col].strip()
                        if(File_PATH+PHOTO_NEED[photo_row]+'.png'+PHOTO_PRO[0]==L_error[0][col].strip()):
                            Time_list2[row_Speed][photo_row]=float(L_error[row][col])
                            Error_list2[row_Speed][photo_row]=float(L_error[row][col+1])
                            is_in= False
                            break
                                    
                break
#print is_in      
#print Time_list[0]
#print Error_list[0]
csvfile.close()
#######################find the reference,outresult, difference_outresult location and clip them to 574 size, convert difference to false_color image
MEDIA_HOME_PATH='/home/liming/Document/supplementary_doc/docs_v2/images/'
Location_result_output=MEDIA_HOME_PATH+FOLDER_TO+"/"
Location_reference_out=MEDIA_HOME_PATH+'reference_outputs/'+FOLDER_TO+"/"
Location_result_output2=MEDIA_HOME_PATH+FOLDER_TO2+"/"
#Location_result_difference=MEDIA_HOME_PATH+FOLDER_TO


Location_copyfrom_reference_out=HOME_PATH+FOLDER+'/gen100000/visualize/results-NO_APPROXIMATIONS/' #manmade1_image_820x614-out.png
Location_copyfrom_demosaic_out=HOME_PATH+FOLDER+'/gen100000/visualize/'
Location_copyfrom_demosaic_out2=HOME_PATH+FOLDER2+'/gen100000/visualize/'
#results-indiv009.approx/manmade5_image_820x614-out.png  !!!need clip
#Location_copyfrom_demosaic_difference=HOME_PATH+FOLDER+'/gen100000/visualize/'
#results-indiv009.approx/manmade1_image_820x614-difference.png !!need clip


####################################copy reference-out image

import shutil
import os

#results-indiv007.approx
for file in os.listdir(Location_copyfrom_reference_out):
        for number in range(0,len(PHOTO_NEED)):
            sourceFile = os.path.join(Location_copyfrom_reference_out,  file) 
            if not os.path.exists(sourceFile):
                print "not exists"
            else:
                if(sourceFile==Location_copyfrom_reference_out+PHOTO_NEED[number]+'-out.png'):
                    dstFile =  Location_reference_out+PHOTO_To_NEED[number]+'-out.png'
                    #print("%s/n",Location_copyfrom_reference_out+PHOTO_NEED[number]+'-out.png')
                    #print("%s/n",Location_reference_out+PHOTO_NEED[number]+'-out.png')
                    shutil.copyfile(sourceFile, dstFile)
                    CONVERT_COMMAND="convert "+sourceFile+" -gravity center -crop 574x574+0+0 "+dstFile
                    os.system(CONVERT_COMMAND)
                    break
                
                #else:
                    #print("no such file:%s",PHOTO_NEED[number]+'-out.png')
            #print("find such file:%s",sourceFile)
#####################################################################convert the image to the final size
#for number in range(len(reference_out_list[0])):
#    CONVERT_COMMAND="convert "+Location_copyfrom_reference_out+PHOTO_NEED[number]+'-out.png'+" -gravity center -crop 574x574+0+0 "+Location_reference_out+PHOTO_NEED[number]+'-out.png'
#    os.system(CONVERT_COMMAND)
################################copy Result-out images and convert
for file in os.listdir(Location_result_output):
    for n in range(0,len(Speed)):
        find_yy=file.find(str(Speed[n]))
        if (find_yy>0):
            print Speed[n]
            for number in range(0,len(PHOTO_NEED)):
                sourceFile = Location_copyfrom_demosaic_out+"results-"+L_time_filename[n]+"/"+PHOTO_NEED[number]+"-out.png"
                print L_time_filename[n]
                if not os.path.exists(Location_result_output+file+"/"+PHOTO_To_NEED[number]):
                    os.makedirs(Location_result_output+file+"/"+PHOTO_To_NEED[number])
                    print "NOt exists"
                destFile=os.path.join(Location_result_output,file)+"/" +PHOTO_To_NEED[number]+"/"+PHOTO_To_NEED[number]+"-out.png"
                shutil.copyfile(sourceFile, destFile)
                CONVERT_COMMAND="convert "+sourceFile+" -gravity center -crop 574x574+0+0 "+destFile
                os.system(CONVERT_COMMAND)   
################################copy Result-out images and convert2222222
for file in os.listdir(Location_result_output2):
    for n in range(0,len(Speed)):
        find_yy=file.find(str(Speed[n]))
        if (find_yy>0):
            print Speed[n]
            for number in range(0,len(PHOTO_NEED)):
                sourceFile = Location_copyfrom_demosaic_out2+"results-"+L_time_filename2[n]+"/"+PHOTO_NEED[number]+"-out.png"
                print L_time_filename2[n]
                if not os.path.exists(Location_result_output2+file+"/"+PHOTO_To_NEED[number]):
                    os.makedirs(Location_result_output2+file+"/"+PHOTO_To_NEED[number])
                    print "NOt exists"
                destFile=os.path.join(Location_result_output2,file)+"/" +PHOTO_To_NEED[number]+"/"+PHOTO_To_NEED[number]+"-out.png"
                shutil.copyfile(sourceFile, destFile)
                CONVERT_COMMAND="convert "+sourceFile+" -gravity center -crop 574x574+0+0 "+destFile
                os.system(CONVERT_COMMAND)   
               
                
################################copy difference images and convert to false_color image and convert size
import numpy
import Image
import matplotlib
import matplotlib.pyplot
import matplotlib.colors 
def v_from_error(error):
    return min(1,error*3)
def s_from_error(error):
    return 1
def h_from_error(error):
    return (1-error)*100.0/360.0
def convert_to_false_coloring(input_image_location0, output_image_location0):
    image_location = os.path.abspath(input_image_location0)
    output_location = os.path.abspath(output_image_location0)
    #if os.path.isfile(output_location):
    #    return 
    I0 = numpy.asarray(Image.open(image_location))
    I = numpy.zeros( (I0.shape[0],I0.shape[1],3) )
    I.astype(float)
    for y in xrange(I.shape[0]):
        for x in xrange(I.shape[1]):
            try:
                error = float(I0[y,x])/255.0
            except:
                pdb.set_trace()
            h = h_from_error(error)
            s = s_from_error(error)
            v = v_from_error(error)
            
            I[y,x,0] = h
            I[y,x,1] = s
            I[y,x,2] = v
    I_color = (matplotlib.colors.hsv_to_rgb(I)*255).astype('uint8')
    Image.fromarray(I_color).save(output_location)
    
      
for file in os.listdir(Location_result_output):
    for n in range(0,len(Speed)):
        find_yy=file.find(str(Speed[n]))
        if (find_yy>0):
            print Speed[n]
            for number in range(0,len(PHOTO_NEED)):
                sourceFile = Location_copyfrom_demosaic_out+"results-"+L_time_filename[n]+"/"+PHOTO_NEED[number]+"-difference.png"
                print L_time_filename[n]
                if not os.path.exists(Location_result_output+file+"/"+PHOTO_To_NEED[number]):
                    os.makedirs(Location_result_output+file+"/"+PHOTO_To_NEED[number])
                    print "NOt exists"
                destFile=os.path.join(Location_result_output,file)+"/" +PHOTO_To_NEED[number]+"/"+PHOTO_To_NEED[number]+"-difference.png"
                shutil.copyfile(sourceFile, destFile)
                convert_to_false_coloring(destFile, destFile)
                CONVERT_COMMAND="convert "+sourceFile+" -gravity center -crop 574x574+0+0 "+destFile
                os.system(CONVERT_COMMAND)   
                
################################copy difference images and convert to false_color image and convert size222222222
for file in os.listdir(Location_result_output2):
    for n in range(0,len(Speed)):
        find_yy=file.find(str(Speed[n]))
        if (find_yy>0):
            print Speed[n]
            for number in range(0,len(PHOTO_NEED)):
                sourceFile = Location_copyfrom_demosaic_out2+"results-"+L_time_filename2[n]+"/"+PHOTO_NEED[number]+"-difference.png"
                print L_time_filename2[n]
                if not os.path.exists(Location_result_output2+file+"/"+PHOTO_To_NEED[number]):
                    os.makedirs(Location_result_output2+file+"/"+PHOTO_To_NEED[number])
                    print "NOt exists"
                destFile=os.path.join(Location_result_output2,file)+"/" +PHOTO_To_NEED[number]+"/"+PHOTO_To_NEED[number]+"-difference.png"
                shutil.copyfile(sourceFile, destFile)
                convert_to_false_coloring(destFile, destFile)
                CONVERT_COMMAND="convert "+sourceFile+" -gravity center -crop 574x574+0+0 "+destFile
                os.system(CONVERT_COMMAND)   

##############################################################################write the right location to the siggraph file
Siggraph_File="/home/liming/Document/supplementary_doc/docs_v2/supplemental_doc.tex"
Temp_File="/home/liming/Document/supplementary_doc/docs_v2/temp.tex"
#fh = open("/home/liming/Document/supplementary_doc/docs_v2/supplemental_doc.txt",'r+')
fh = open(Siggraph_File,'r+')
output = open(Temp_File,'r+')
count=0
PIC_count=0
Speed_count=0
go_to_nextline=0
for  line in fh.readlines(): 
    if(go_to_nextline==1):
        go_to_nextline=0
        continue
    if (str(line).find(str("NEED_TO_ADD"))==0):
        count=count+1
        if(count==1):
            #Blur \\
            #\frame{\includegraphics[width=\w]{images/blur/point_cloud.png}} \\ \\
            String1="Median \\\\\n"
            output.write(String1)
            String2="\\frame{\\includegraphics[width=\\w]{images/"+FOLDER_TO+"/"+"point_cloud.png}} \\\\ \\\\\n"
            output.write(String2)
        elif(count==2):
            #\frame{\includegraphics[width=\w]{images/reference_input/man_made_txt_4_image_820x614.png}} \\ \\\\
            String1="\\frame{\\includegraphics[width=\\w]{images/reference_input/"+PHOTO_To_NEED[PIC_count]+".png}} \\\\ \\\\\\\\\n"
            output.write(String1)
            #print"Find Second Line"
        elif(count==3):
            #\frame{\includegraphics[width=\w]{images/reference_outputs/unsharp_mask/man_made_txt_4_image_820x614-out.png}} &
            #\frame{\includegraphics[width=\w]{images/unsharp_mask/unsharp_mask_2.0/man_made_txt_4_image_820x614/man_made_txt_4_image_820x614-out.png}} &
            #\frame{\includegraphics[width=\w]{images/unsharp_mask/unsharp_mask_2.0/man_made_txt_4_image_820x614/man_made_txt_4_image_820x614-false_coloring.png}} &
            #\frame{\includegraphics[width=\w]{images/unsharp_mask_loop_perf_only/unsharp_mask_2.0/man_made_txt_4_image_820x614/man_made_txt_4_image_820x614-out.png}} &
            #\frame{\includegraphics[width=\w]{images/unsharp_mask_loop_perf_only/unsharp_mask_2.0/man_made_txt_4_image_820x614/man_made_txt_4_image_820x614-false_coloring.png}} \\ \\
            String1="\\frame{\\includegraphics[width=\\w]{images/reference_outputs/"+FOLDER_TO+"/"+PHOTO_To_NEED[PIC_count]+"-out.png}} & \n"
            output.write(String1)
            String2="\\frame{\\includegraphics[width=\\w]{images/"+FOLDER_TO+"/"+FOLDER_TO+"_"+str(Speed[Speed_count])+"/"+PHOTO_To_NEED[PIC_count]+"/"+PHOTO_To_NEED[PIC_count]+"-out.png}} & \n"
            output.write(String2)
            String3="\\frame{\\includegraphics[width=\\w]{images/"+FOLDER_TO+"/"+FOLDER_TO+"_"+str(Speed[Speed_count])+"/"+PHOTO_To_NEED[PIC_count]+"/"+PHOTO_To_NEED[PIC_count]+"-difference.png}} &\n"
            output.write(String3)
            String4="\\frame{\\includegraphics[width=\\w]{images/"+FOLDER_TO2+"/"+FOLDER_TO+"_"+str(Speed[Speed_count])+"/"+PHOTO_To_NEED[PIC_count]+"/"+PHOTO_To_NEED[PIC_count]+"-out.png}} & \n"
            output.write(String4)
            String5="\\frame{\\includegraphics[width=\\w]{images/"+FOLDER_TO2+"/"+FOLDER_TO+"_"+str(Speed[Speed_count])+"/"+PHOTO_To_NEED[PIC_count]+"/"+PHOTO_To_NEED[PIC_count]+"-difference.png}} \\\\ \\\\\\\\\n"
            output.write(String5)
            #print"Find Fourth Line"
        elif(count==4):
            #Blur & 2.0\X & 3.22\X & 2.04\X & 0.25 & 18.61 \\ 
            String5="Median & "+str(round(Speed[Speed_count],2))+"\\X & "+str(round(L_time_value[Speed_count],2))+"\\X & "+str(round(L_time_value2[Speed_count],2))+"\\X & "+str(round(Error_list[Speed_count][PIC_count],2))+" & "+str(round(Error_list2[Speed_count][PIC_count],2))+" \\\\\n"
            output.write(String5)
            count=0
            Speed_count=Speed_count+1
            if(Speed_count==4):
                PIC_count = PIC_count+1
                Speed_count=0
        else:
            print "what happened"
    elif(str(line).find(str("\\setlength{\\h}{0.9in}"))==0):
        String1="\\setlength{\\h}{0.8in}\n"
        output.write(String1)
    elif(str(line).find(str("\\setlength{\\w}{0.9in}"))==0):
        String1="\\setlength{\\w}{0.8in}\n"
        output.write(String1)
    elif(str(line).find(str("\\setlength{\\tabcolsep}{.125em}"))==0):
        String1="\\setlength{\\tabcolsep}{.1em}\n \\vspace{-0.01in} \n"
        output.write(String1)
        go_to_nextline=1
    elif(str(line)==str("\\shrinkbefore\n")):
        String1="\\shrinkbefore\n"
        output.write(String1)
        go_to_nextline=1
    elif(str(line).find(str("\\begin{tabular}{ccccc}"))==0):
        String1="\\begin{tabular}{ccccc}\n & "+"& & & \\\\\\\\ \n"
        output.write(String1)
        go_to_nextline=1
    elif(str(line).find(str("\\begin{figure*}"))==0):
        String1="\\begin{figure*}\n"+"\\caption*{Target Speedup:"+str(Speed[Speed_count])+" }\n"
        output.write(String1)
    else:
        output.write(line)
    
fh.close()
output.close()
            
        
      










































