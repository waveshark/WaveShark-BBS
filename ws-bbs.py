# TODO: HANDLE UNKNOWN COMMANDS
# TODO: READ/WRITE WALL AND LAST HEARD FROM/TO DISK

import sys
from datetime import datetime, timedelta
import time
import re
import serial
import serial.tools.list_ports

# Settings
announceSeconds = 600
max_wall_messages = 3

def readLineFromSerial(ser):
  return ser.readline().decode("ascii").strip()

def writeToSerial(ser, str, numLinesToEat = 1):
  ser.write(bytes("{}\r".format(str), "ascii"))
  for i in range(0, numLinesToEat):
    readLineFromSerial(ser)

def try_connect():
  for port, desc, hwid in sorted(serial.tools.list_ports.comports()):
    if "CP2102" in desc:
      try:
        ser = serial.Serial("/dev/ttyUSB0", 115200, timeout = 0.1)
        writeToSerial(ser, "/VERSION")
        if "WaveShark firmware" in readLineFromSerial(ser):
          return ser
      except:
        type, value, traceback = sys.exc_info()
        print(value)
        pass

  return False

# Connect to WaveShark Communicator
ser = try_connect()
if ser != False:
  print("Connected to WaveShark Communicator device")
else:
  print("Failed to connect to WaveShark Communicator device")
  exit()

# Get device's sender name / device name
writeToSerial(ser, "/NAME")
bbs_name = readLineFromSerial(ser).split("[")[1].split("]")[0]
print("BBS name: [{}]".format(bbs_name))

# Configure device for BBS operation
writeToSerial(ser, "/SEROUT FIELDTEST", 3)

# For sending periodic BBS announcements
nextAnnounce = datetime.now()

# Wall and last heard
wall = []
lastHeard = {}

# Process incoming messages
while True:
  # Received message?
  s = readLineFromSerial(ser)
  if re.match(r'^\[RSS: ', s):
    print("\r\nDevice: {}".format(s))
    message_from = s.split("<")[1].split(">")[0]
    message_body = s[slice(s.find(">") + 2, len(s))]
    # message_rss  = s.split("]")[0].split(" ")[1]
    # message_snr  = s.split("]")[1].split(" ")[2]

    # Update last heard
    print("Got message [{}] from [{}]".format(message_body, message_from))
    lastHeard[message_from] = datetime.now().strftime("%Y-%m-%d %H:%M")
    print("Updated last heard for [{}] to {}".format(message_from, lastHeard[message_from]))

    # HEARD command?
    if "{} HEARD".format(bbs_name).lower() in s.lower():
      print("Got HEARD command")
      for senderName in lastHeard:
        writeToSerial(ser, "I last heard <{}> at {}".format(senderName, lastHeard[senderName]))

    # WRITE command?
    elif "{} WRITE".format(bbs_name).lower() in s.lower():
      print("Got WRITE command")
      tokens = message_body.strip().split(" ")
      del tokens[0]
      for i in range(0, len(bbs_name.split(" "))):
        del tokens[0]
      post = (" ".join(tokens)).strip()
      print ("Received wall message [" + post + "]")
      if post != "":
        wall.append("[" + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "] <" + message_from + "> " + post)
        writeToSerial(ser, "{}, I have added your message to the wall.".format(message_from))

        # Maintain maximum wall length
        if len(wall) > max_wall_messages:
          print("Removing a message from the wall")
          del wall[0]

        print("Wall contents now:")
        for message in wall:
          print(message)
      else:
        writeToSerial(ser, "{}, what is your message?".format(message_from))

    # READ command?
    elif "{} READ".format(bbs_name).lower() in s.lower():
      print("Got READ command")
      if len(wall) > 0:
        if len(wall) == 1:
          writeToSerial(ser, "{}, there is one message on the wall.".format(message_from))
        else:
          writeToSerial(ser, "{}, there are {} messages on the wall.".format(message_from, len(wall)))

        for message in wall:
          writeToSerial(ser, message)
      else:
        writeToSerial(ser, "{}, there are no messages on the wall.".format(message_from))

    # HELP command?
    elif "{} HELP".format(bbs_name).lower() in s.lower():
      print("Got HELP command")
      writeToSerial(ser, "Say {} READ to read messages on the wall. Say {} WRITE to write a message on the wall. Say {} HEARD to get a list of recently heard users.".format(bbs_name, bbs_name, bbs_name))

    # TODO: Unknown command?

  # Time to send announcement?
  secondsUntilAnnounce = (nextAnnounce - datetime.now()).total_seconds()
  if secondsUntilAnnounce <= 0:
    nextAnnounce = datetime.now() + timedelta(seconds = announceSeconds)
    print("Sending announcement")
    writeToSerial(ser, "Hello from {}! Say {} HELP to get a list of available commands.".format(bbs_name, bbs_name), 2)

ser.close()
