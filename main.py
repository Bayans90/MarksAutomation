import argparse
import pymongo
import subprocess
import shlex
import math
import xlsxwriter
from frameioclient import FrameioClient

# frameIO API Implementation
client = FrameioClient(
    "fio-u-gUhxhw112YBrmAKuVGdBxoiOG1CuGMB_djSBLI7GJlMaXLPyuVpCWKgXkUGd5RX0"
)
me = client.users.get_me()


# argparse implementation
parser = argparse.ArgumentParser(description="Process video for processing")
parser.add_argument("--process", "-p", dest="process", help="video file")
parser.add_argument("--output", "-o", dest="output", help="XLS or CSV")
args = parser.parse_args()

# database implementation
myclient = pymongo.MongoClient("mongodb://localhost:27017/")
mydb = myclient["mydatabase"]
firstColl = mydb["user_machines"]
secondColl = mydb["frame_locations"]

# grabs frames and locations from database
counter = 0
frameList = []
locationList = []
result = secondColl.find({}, {"location": 1, "frame": 1, "_id": 0})
for i in result:
    if "frame" in i:
        frameList.append(i["frame"])
    if "location" in i:
        locationList.append(i["location"])
    counter += 1

# get frame timecode for video from lecture
cmd = "ffmpeg -i '{}' -hide_banner".format(args.process)
process = subprocess.Popen(
    shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True
)
duration = 0
for line in process.stdout.readlines():
    decoded = line.decode()
    if decoded.startswith("  Duration:"):
        print(decoded)
        duration = decoded.strip().split(",")[0].strip().split(" ")[1]
        print(duration)
# takes the duration, splits it up and converts each part to frames based off of 60 fps
timecode = []
timecode = duration.split(":")
hour = int(timecode[0])
min = int(timecode[1])
second = float(timecode[2].split(".")[0])
frames = 0
frames += second * 60
frames += min * 60 * 60
frames += hour * 60 * 60 * 60
frames = int(frames)
# print(frames)

# take each frame, find the most middle if a range, and see if it fits inside the video's length (timecode wise)
timecodeFrames = []
XLSframes = []
XLSlocations = []
locationCounter = 0
for i in frameList:
    # if single frame
    if "-" not in i:
        singleFrame = int(i)
        # if single frame is within the video's timecode, then add to respective lists
        if singleFrame <= frames:
            XLSframes.append(i)
            timecodeFrames.append(singleFrame)
            XLSlocations.append(locationList[locationCounter])
            locationCounter += 1
        else:
            locationCounter += 1
    # if frame range
    if "-" in i:
        i = i.replace("-", " ").split(" ")
        firstHalf = int(i[0])
        secondHalf = int(i[1])
        dualFrame = math.ceil((firstHalf + secondHalf) / 2)
        # if frame range is within the video's timecode, then add to respective lists
        if dualFrame <= frames:
            i = f"{firstHalf} - {secondHalf}"
            XLSframes.append(i)
            timecodeFrames.append(dualFrame)
            XLSlocations.append(locationList[locationCounter])
            locationCounter += 1
        else:
            locationCounter += 1
# print(XLSframes)
# print(timecodeFrames)
# print(XLSlocations)

# timecode conversion from frames to timecode , with 60 fps
timeCodeList = []
timecodeCounter = 0
fps = 60
for item in timecodeFrames:
    seconds = item // fps
    frames = item - (fps * seconds)
    seconds = seconds % (60 * 3600)
    hour = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60
    timeCodeList.append("%02d:%02d:%02d" % (hour, minutes, seconds))
    timecodeCounter += 1
# print(timeCodeList)

# running png first in argparse to create thumbnails
if "PNG" in args.output:
    for index, picture in enumerate(timeCodeList):
        cmd2 = "ffmpeg  -ss {} -i '{}' -vf 'scale=96:74:force_original_aspect_ratio=decrease' -frames:v 1 'out{}.png' -hide_banner".format(
            picture, args.process, index
        )
        process1 = subprocess.Popen(shlex.split(cmd2), shell=True)
# then run XLS second to input everything into the XLS file
if "XLS" in args.output:
    # excel workbook creation
    workbook = xlsxwriter.Workbook("crucible.xlsx")
    worksheet = workbook.add_worksheet()
    # insert the locations
    for index, entry in enumerate(XLSlocations):
        worksheet.write(index, 0, entry)
    # insert the frame ranges
    for index, entry in enumerate(XLSframes):
        worksheet.write(index, 1, entry)
    # insert the timecodes from frame ranges and thumbnails
    for index, entry in enumerate(timeCodeList):
        worksheet.write(index, 2, entry)
        worksheet.insert_image(index, 3, "out{}.png".format(index))
        # put all pictures into the frameIO project "The Crucible"
        client.assets.upload(
            "b4507633-64d9-437d-8f6b-c372d9a73588", "out{}.png".format(index)
        )
    workbook.close()
