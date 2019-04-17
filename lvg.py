#!python3
import sys, signal, time, csv, json
from threading import Timer
import RPi.GPIO as GPIO
from lib import rfid_reader as rd # import custom library that manages the physical tag readers

# GLOBAL VARIABLES
class Global:
    # Settings. Will be populated from settings.json
    settings = {}
    # Data
    scans = [] # List containing all the scanned codes (with reader address and timestamp)
    #lastScan, used to debounce
    lastScan = None


def startExperiment():
    """Sets up the experiment"""
    Global.scans = [] # Empty the list of scanned codes
    logCode('', 'START') # Log special "START" code
    flashAllLeds(2) # Flash LEDs 2 times
    if Global.settings['debug']:
        print('Starting experiment...')


def endExperiment():
    """Sets up the experiment"""
    logCode('', 'END') # Log special "END" code
    exportDataToCsv() # Save data to a CSV file
    flashAllLeds(4) # Flassh LEDs 4 times
    if Global.settings['debug']:
        print('Ending experiment and saving data...')


def codeScanned(readerAddress, code):
    """Function that gets called every time a tag is scanned
    readerAddress - the address of the USB port where the physical reader is connected
    code - the code that the reader has scanned
    """
    # Debounce scan
    now = time.time()
    if Global.lastScan != None:
        then, lastAddress, lastCode = Global.lastScan
        if (now - then) < Global.settings['debounceSeconds'] and code == lastCode and readerAddress == lastAddress:
            return
    Global.lastScan = (now, readerAddress, code)

    # If the start code is scanned, start experiment
    if code == Global.settings['startCode']:
        startExperiment()
        return

    # If the stop code is scanned, stop the experiment
    if code == Global.settings['stopCode']:
        endExperiment()
        return

    # Is it the correct code for the reader?
    isActivationCode = code in getReaderActivationCodes(readerAddress)

    # Log the scanned code
    logCode(readerAddress, code, isActivationCode)

    # And if it was the correct code for the reader, light up the reader
    if isActivationCode:
        lightUpReader(readerAddress)


def logCode(readerAddress, code, isCorrectCode=False):
    """Logs a scanned code
    readerAddress - the address of the reader
    code - the code that the reader has scanned
    """
    timestamp = time.time()
    record = {
        'timestamp': timestamp,
        'conditionId': Global.settings['conditionToRun'],
        'readerIndex': getReaderIndex(readerAddress),
        'scannedCode': code,
        'isCorrect': isCorrectCode
    }
    Global.scans.append(record)
    if Global.settings['debug']:
        print('CODE SCANNED:', timestamp, readerAddress, code)


def lightUpReader(readerAddress):
    """Lights up a reader
    readerAddress - the address of the reader
    """
    if readerAddress not in Global.settings['readersAddresses']:
        return
    if Global.settings['debug']:
        print('Lighting up reader ' + readerAddress)
    readerIndex = getReaderIndex(readerAddress)
    led = Global.settings['readersLedsAddresses'][readerIndex]
    GPIO.output(led, GPIO.HIGH)

    timer = Timer(Global.settings['lightOnSeconds'], lambda: GPIO.output(led, GPIO.LOW))
    timer.start()


def getReaderIndex(readerAddress):
    if readerAddress in Global.settings['readersAddresses']:
        return Global.settings['readersAddresses'].index(readerAddress)
    return None


def getReaderActivationCodes(readerAddress):
    """Returns the correct code for a reader
    readerAddress - the address of the reader
    """
    if readerAddress in Global.settings['readersAddresses']:
        readerIndex = getReaderIndex(readerAddress)
        condition = Global.settings['conditions'][Global.settings['conditionToRun']]
        return condition['readers'][readerIndex]['activatesFor']
    return None


def flashAllLeds(times=1, forSeconds=0.2):
    for i in range(times):
        for led in Global.settings['readersLedsAddresses']:
            GPIO.output(led, GPIO.HIGH)
        time.sleep(forSeconds)
        for led in Global.settings['readersLedsAddresses']:
            GPIO.output(led, GPIO.LOW)
        if i < times-1:
            time.sleep(forSeconds)


def exportDataToCsv():
    """Exports the data to a CSV file named with the current date/time"""
    fileName = time.strftime("%Y%m%d-%H%M%S")
    keys = Global.scans[0].keys()
    with open('data/' + fileName + '.csv', 'w', encoding='utf8', newline='') as outputFile:
        dictWriter = csv.DictWriter(outputFile, keys)
        dictWriter.writeheader()
        dictWriter.writerows(Global.scans)


def main():
    """Program main function"""

    # Read app settings
    with open('settings.json') as handle:
        Global.settings = json.loads(handle.read())

    # setup LEDs
    GPIO.setmode(GPIO.BCM)
    for led in Global.settings['readersLedsAddresses']:
        GPIO.setup(led, GPIO.OUT)

    # Initialize composite reader by passing the physical readers name
    reader = rd.RfidReader('HXGCoLtd')

    # Print the list of physical readers for Global.settings['debug'] reasons
    print('Connected physical readers:')
    reader.printActiveDevices()

    # Start listening for tag scans by passing a callback fucntion
    reader.start(codeScanned) 
    
    # IMPORTANT: the program is now stuck at the line above reading tags
    # The next lines of code will only be executed once the reader is stopped
    
    # Clean up LEDs state
    GPIO.cleanup()

    if Global.settings['debug']:
        print(' Closing program...')


# Execute the main() function when the script is executed
if __name__ == "__main__":
    main()
