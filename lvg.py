#!python3
import sys, signal, time
import RPi.GPIO as GPIO
from lib import rfid_reader as rd # import custom library that manages the physical tag readers

# GLOBAL VARIABLES
DEBUG = True # put to False to skip printing DEBUG information
START_CODE = '0002148131'
STOP_CODE = '0014667528'

# READERS ADDRESSES
readersAddresses = [
    'usb-3f980000.usb-1.2.2/input0', # USB address of reader 1
    'usb-3f980000.usb-1.2.3/input0', # USB address of reader 2
    'usb-3f980000.usb-1.2.4/input0', # USB address of reader 3
    'usb-3f980000.usb-1.2.5/input0'  # USB address of reader 4
]

# READERS CORRECT CODES
readersCorrectCodes = [
    '0002121660', # Correct code for reader 1
    '0002121660', # Correct code for reader 2 
    '0002121660', # Correct code for reader 3
    '0002121660'  # Correct code for reader 4
]

# DATA VARIABLES
initial_timestamp = None
final_timestamp = None
scans = [] # List containing all the scanned codes (with reader address and timestamp)


def startExperiment():
    """Sets up the experiment"""
    initial_timestamp = time.time()
    scans = []


def stopExperiment():
    """Sets up the experiment"""
    final_timestamp = time.time()
    # TODO: save data to csv file


def codeScanned(readerAddress, code):
    """Function that gets called every time a tag is scanned
    readerAddress - the address of the USB port where the physical reader is connected
    code - the code that the reader has scansned
    """

    # If the start code is scanned, start experiment
    if code == START_CODE:
        startExperiment()
        return

    # If the stop code is scanned, stop the experiment
    if code == STOP_CODE:
        endExperiment()
        return

    # Else, log the scanned code
    logCode(readerAddress, code)

    # And if it was the correct code for the reader, light up the reader
    if code == getReaderCorrectCode(readerAddress):
        lightUpReader(readerAddress)


def logCode(readerAddress, code):
    """Logs a scanned code
    readerAddress - the address of the reader
    code - the code that the reader has scanned
    """
    timestamp = time.time()
    record = {
        'ts': timestamp,
        'readerAddress': readerAddress,
        'code': code
    }
    scans.append(record)
    if DEBUG:
        print('CODE SCANNED:', timestamp, readerAddress, code)


def lightUpReader(readerAddress):
    """Lights up a reader
    readerAddress - the address of the reader
    """
    if DEBUG:
        print('Lighting up reader ' + readerAddress)
    GPIO.output(18, GPIO.HIGH)
    time.sleep(3)
    GPIO.output(18, GPIO.LOW)


def getReaderCorrectCode(readerAddress):
    """Returns the correct code for a reader
    readerAddress - the address of the reader
    """
    return readersCorrectCodes[readersAddresses.index(readerAddress)]


def main():
    """Program main function"""

    # setup LEDs
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(18, GPIO.OUT)

    # Initialize composite reader by passing the physical readers name
    reader = rd.RfidReader('HXGCoLtd')

    # Print the list of physical readers for DEBUG reasons
    print('Connected physical readers:')
    reader.printActiveDevices()

    # Start listening for tag scans by passing a callback fucntion
    reader.start(codeScanned) 
    
    # IMPORTANT: the program is now stuck at the line above reading tags
    # The next lines of code will only be executed once the reader is stopped
    
    if DEBUG:
        print('Reader Stopped')
        print(scans)


# Execute the main() function when the script is executed
if __name__ == "__main__":
    main()
