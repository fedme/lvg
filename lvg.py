#!python3
import sys, signal, time
from lib import rfid_reader as rd # import custom library that manages the physical tag readers

# list containing all the scans
# each scan has the reader id, the scanned code, and the timestamp
scans = []

def codeScanned(readerAddress, code):
    """Function that gets called every time a tag is scanned
    readerAddress - the address of the USB port where the physical reader is connected
    code - the code that the reader has scanned
    """
    timestamp = time.time()
    scans.append({
        'ts': timestamp,
        'readerAddress': readerAddress,
        'code': code
    })
    print('CODE SCANNED:', timestamp, readerAddress, code)

def main():
    """Program main function"""
    reader = rd.RfidReader('HXGCoLtd') # Initialize composite reader by passing the physical readers name
    reader.printActiveDevices() # print the list of physical readers for debug
    reader.start(codeScanned) # start listening for tag scans by passing a callback fucntion

if __name__ == "__main__":
    main()