from binhoHostAdapter import binhoHostAdapter
from binhoHostAdapter import binhoUtilities

from .i2c_driver import I2CDriver

import sys
import os


_PLATFORM_NAME = "BinhoHostAdapter"

#-----------------------------------------------------------------------------
# Internal function to connect to the systems I2C bus.
#
# Attempts to fail elegantly. Put this in a central place to support 
# error handling  -- especially on non-circuitpy platforms
#
def _connectToI2CBus():

	binho = None

	error=False

	# Connect - catch errors 

	try:

		utilities = binhoUtilities.binhoUtilities()
		devices = utilities.listAvailableDevices()

		if len(devices) == 1:

			binho = binhoHostAdapter.binhoHostAdapter(devices[0])
			binho.setNumericalBase(10)
			binho.setOperationMode(0, "I2C")
			binho.setPullUpStateI2C(0, "EN")
			binho.setClockI2C(0, 400000)
		elif len(devices) > 1:
			print("Error:\tUnable to connect to I2C bus. More than one Binho Host Adapter found.")
			error=True
		else:
			print("Error:\tUnable to connect to I2C bus. No Binho Host Adapter found.")
			error=True

	except Exception as ee:

		if type(ee) is RuntimeError:
			print("Error:\tUnable to connect to I2C bus. %s" % (ee))
			print("\t\tEnsure a Binho Host Adapter is connected to the computer." % (os.uname().machine))			
		else:
			print("Error:\tFailed to connect to I2C bus. Error: %s" % (ee))

		# We had an error.... 
		error=True

	# below is probably not needed, but ...
	if(not error and binho == None):
		print("Error: Failed to connect to I2C bus. Unable to continue")

	return binho


class BinhoI2C(I2CDriver):

	# Constructor
	name = _PLATFORM_NAME

	_i2cbus = None

	def __init__(self):

		# Call the super class. The super calss will use default values if not 
		# proviced
		I2CDriver.__init__(self)

	def __del__(self):

		if(self._i2cbus != None):
			self.i2cbus.close()


	@classmethod
	def isPlatform(cls):

		# We can implement a more thorough check later (for example, check for COM port), but for now just return true since binhoHostAdapter
		# runs on so many different systems
		return True


	#-------------------------------------------------------------------------		
	# General get attribute method
	#
	# Used to intercept getting the I2C bus object - so we can perform a lazy
	# connect ....
	#
	def __getattr__(self, name):

		if(name == "i2cbus"):
			if( self._i2cbus == None):
				self._i2cbus = _connectToI2CBus()
			return self._i2cbus

		else:
			# Note - we call __getattribute__ to the super class (object).
			return super(I2CDriver, self).__getattribute__(name)

	#-------------------------------------------------------------------------
	# General set attribute method
	#
	# Basically implemented to make the i2cbus attribute readonly to users 
	# of this class. 
	#
	def __setattr__(self, name, value):

		if(name != "i2cbus"):
			super(I2CDriver, self).__setattr__(name, value)

	#----------------------------------------------------------
	# read Data Command

	def readWord(self, address, commandCode):

		self.i2cbus.startI2C(0, address<<1)
		self.i2cbus.writeByteI2C(0, commandCode)
		self.i2cbus.endI2C(0, True)

		buffer = bytearray(2)

		result = self.i2cbus.readBytesI2C(0, address<<1, 2)

		resp = result.split(" ")

		if len(resp)>3:
			buffer[0] = int(resp[3])
			buffer[1] = int(resp[2])
		else:
			print("Error: I2C ReadWord Failure. Exiting...")
			self.i2cbus.close()
			sys.exit(1)

		# build and return a word
		return (buffer[1] << 8 ) | buffer[0]

	#----------------------------------------------------------
	def readByte(self, address, commandCode):

		self.i2cbus.startI2C(0, address<<1)
		self.i2cbus.writeByteI2C(0, commandCode)
		self.i2cbus.endI2C(0, True)

		buffer = bytearray(1)

		result = self.i2cbus.readBytesI2C(0, address<<1, 1)

		resp = result.split(" ")

		if len(resp)>2:
			buffer[0] = int(resp[2])
		else:
			print("Error: I2C ReadByte Failure. Exiting...")
			self.i2cbus.close()
			sys.exit(1)

		return buffer[0]

	#----------------------------------------------------------
	def readBlock(self, address, commandCode, nBytes):

		self.i2cbus.startI2C(0, address<<1)
		self.i2cbus.writeByteI2C(0, commandCode)
		self.i2cbus.endI2C(0, True)

		buffer = bytearray(nBytes)

		result = self.i2cbus.readBytesI2C(0, address<<1, nBytes)

		resp = result.split(" ")

		for i in range(nBytes):
			buffer[i] = int(resp[i+2])

		return buffer

		
	#--------------------------------------------------------------------------	
	# write Data Commands 
	#
	# Send a command to the I2C bus for this device. 
	#
	# value = 16 bits of valid data..
	#

	def writeCommand(self, address, commandCode):

		self.i2cbus.startI2C(0, address<<1)
		self.i2cbus.writeByteI2C(0, commandCode)
		self.i2cbus.endI2C(0, False)

	#----------------------------------------------------------
	def writeWord(self, address, commandCode, value):

		self.i2cbus.startI2C(0, address<<1)
		self.i2cbus.writeByteI2C(0, commandCode)
		self.i2cbus.endI2C(0, True)

		buffer = bytearray(2)
		buffer[0] = value & 0xFF
		buffer[1] = (value >> 8) & 0xFF

		self.i2cbus.startI2C(0, address<<1)
		self.i2cbus.writeByteI2C(0, buffer[1])
		self.i2cbus.writeByteI2C(0, buffer[0])
		self.i2cbus.endI2C(0, False)	


	#----------------------------------------------------------
	def writeByte(self, address, commandCode, value):

		self.i2cbus.startI2C(0, address<<1)
		self.i2cbus.writeByteI2C(0, commandCode)
		self.i2cbus.endI2C(0, True)

		self.i2cbus.startI2C(0, address<<1)
		self.i2cbus.writeByteI2C(0, value)
		self.i2cbus.endI2C(0, False)		

	#----------------------------------------------------------
	def writeBlock(self, address, commandCode, value):

		self.i2cbus.startI2C(0, address<<1)
		self.i2cbus.writeByteI2C(0, commandCode)
		self.i2cbus.endI2C(0, True)

		data = [value] if isinstance(value, list) else value

		self.i2cbus.startI2C(0, address<<1)

		for i in range(len(data)):
			self.i2cbus.writeByteI2C(0, data[i])

		self.i2cbus.endI2C(0, False)


	#-----------------------------------------------------------------------
	# scan()
	#
	# Scans the I2C bus and returns a list of addresses that have a devices connected
	#
	@classmethod
	def scan(cls):
		""" Returns a list of addresses for the devices connected to the I2C bus."""
	
		# Just call the system build it....
	
		if cls._i2cbus == None:
			cls._i2cbus = _connectToI2CBus()
	
		if cls._i2cbus == None:
			return []

		scanResults = []

		for i in range(8, 121):
			result = cls._i2cbus.scanAddrI2C(0, i<<1)

			resp = result.split(" ")

			if resp[3] == 'OK':
				scanResults.append(i)

		return scanResults
