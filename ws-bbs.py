import serial
from datetime import datetime, timedelta

ser = serial.Serial("/dev/ttyUSB0", 115200, timeout = 0.01)

announceSeconds = 60
nextAnnounce = datetime.now()

lastHeard = {}
wall = []

while True:
  l = ser.readline()
  if l != b"":
    s = l.decode("ascii")
    print(s, end = "")

    # Received message?
    if s.startswith("<"):
      # Update last heard
      sender  = s.split("<")[1].split(">")[0]
      message = s.split(">")[1].strip()
      print("Got message [" + message + "]")
      lastHeard[sender] = datetime.now().strftime("%Y-%m-%d %H:%M")
      print("Updated last heard for [" + sender + "] to " + lastHeard[sender])

      # WSBBS-HEARD command?
      if "WSBBS-HEARD".lower() in s.lower():
        print("Got WSBBS-HEARD command")
        for sender in lastHeard:
          ser.write(b"I last heard ")
          ser.write(bytes(sender, "ascii"))
          ser.write(b" at ")
          ser.write(bytes(lastHeard[sender], "ascii"))
          ser.write(b"\r\n")

      # WSBBS-WRITE command?
      if "WSBBS-WRITE".lower() in s.lower():
        print("Got WSBBS-WRITE command")
        tokens = message.strip().split(" ")
        del tokens[0]
        post = (" ".join(tokens)).strip()
        print ("Post [" + post + "]")
        if post != "":
          wall.append("<" + sender + "> " + post)
          ser.write(bytes(sender, "ascii"))
          ser.write(b", I added your message to the wall.\r\n")

          print("Wall contents now:")
          for message in wall:
            print(message)
        else: 
          ser.write(bytes(sender, "ascii"))
          ser.write(b", what is your message?\r\n")

      # WSBBS-READ command?

      # WSBBS-HELP command?
      elif "WSBBS-HELP".lower() in s.lower():
        ser.write(b"Say WSBBS-READ to read messages on the wall.  Say WSBBS-WRITE to write a message on the wall.  Say WSBBS-HEARD to get a list of recently heard users.\r\n")

  # Time to send announcement?
  secondsUntilAnnounce = (nextAnnounce - datetime.now()).total_seconds()
  if secondsUntilAnnounce <= 0:
    nextAnnounce = datetime.now() + timedelta(seconds = announceSeconds)
    print("Sending announcement")
    # ser.write(b"Hello from WaveShark BBS!  Say WSBBS-HELP to get a list of available commands.\r\n")

ser.close()
