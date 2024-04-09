from itertools import groupby
from operator import itemgetter
import csv

# use FOR loop and simple replace
bFile = open("Project 1\Baselight_export.txt", "r")
xFile = open("Project 1\Xytech.txt", "r")

# xytech file line splitting
xyt_location = []
for line in xFile:
    line = line.rstrip("\n")
    if line.startswith("/"):
        xyt_location.append(line)

# baselight file line splitting
baselight = []
frames = []
for line in bFile:
    line = line.rstrip("\n").rstrip(" ")
    line = line.split(" ", 1)
    baselight.append(line[0])
    baselight = [s.replace("/baselightfilesystem1/Barbie", "") for s in baselight]

    #frame splitting to make each set of frames into a list of list
    nums_str = line[-1].split(" ")
    nums = []
    for num in nums_str:
        if num.isdigit():
            nums.append(int(num))
    frames.append(nums)

filename = ""


#matching algorithm to find the match, print the file location, and print the ranges
counter = 0
for a in baselight:
    for b in xyt_location:
        if a in b:
        #using groupby and enumerate to go through each frame list, find consecutive ranges,
        #and break when next number isn't consecutive
            for k, g in groupby(enumerate(frames[counter]), lambda ix: ix[0] - ix[1]):
                frame_output = list(map(itemgetter(1), g))
            #if condition to separate the single frame and multiframe printing
                if len(frame_output) == 1:
                    single_frame = frame_output[0]
                    field = [b, single_frame]
                else:
                    multi_frame = f"{frame_output[0]}-{frame_output[-1]}"
                    field = [b, multi_frame]
                    #writing the frame and file in each row starting from line 4
                print(str(field))
                #counter to keep track of progressing through frame list    
            counter += 1