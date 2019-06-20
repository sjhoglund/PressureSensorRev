# -*- coding: utf-8 -*-
import time
import Adafruit_ADS1x15
from modules import cbpi
from modules.core.hardware import  SensorActive
from modules.core.props import Property

@cbpi.sensor
class PressureSensorRev(SensorActive):

    # Global variables to be used with calculations
    GRAVITY = 9.807
    GAIN = 1    # See Adafruit guidelines for this value
    VOLT = 4.096
    PI = 3.1415
    # Conversion values
    kpa_psi = 0.145
    bar_psi = 14.5038
    inch_mm = 25.4
    gallons_cubicinch = 231

    # User defined variables - Channel is based on the A0, A1, A2, A3 pins on the ADS1x15
    ADSchannel = Property.Select("ADS1x15 Channel", options=["0", "1", "2", "3"], description="Enter channel-number of ADS1x15")
    sensorType = Property.Select("Data Type", options=["Voltage","Digits","Pressure","Liquid Level","Volume"], description="Select which type of data to register for this sensor")
    pressureType = Property.Select("Pressure Value", options=["kPa","PSI"])
    # Use Data Types Voltage and Digits (ADS1x15) for calibration
    voltLow = Property.Number("Voltage Low", configurable=True, default_value=0, description="Pressure Sensor minimum voltage, usually 0")
    voltHigh = Property.Number("Voltage High", configurable=True, default_value=5, description="Pressure Sensor maximum voltage, usually 5")
    pressureLow = Property.Number("Pressure Low", configurable=True, default_value=0, description="Pressure value at minimum voltage, value in kPa")
    pressureHigh = Property.Number("Pressure High", configurable=True, default_value=10, description="Pressure value at maximum voltage, value in kPa")
    sensorHeight = Property.Number("Sensor Height (inches)", configurable=True, default_value=0, description="Location of Sensor from the bottom of the kettle in inches")
    kettleDiameter = Property.Number("Kettle Diameter (inches)", configurable=True, default_value=0, description="Diameter of kettle in inches")

    def get_unit(self):
        '''
        :return: Unit of the sensor as string. Should not be longer than 3 characters
        '''
        if self.sensorType == "Voltage":
            return " V"
        elif self.sensorType == "Digits":
            return " Bit"
        elif self.sensorType == "Pressure":
            if self.pressureType == "kPa":
                return " kPa"
            elif self.pressureType == "PSI":
                return " PSI"
            else:
                return " N/A"
        elif self.sensorType == "Liquid Level":
            return " in"
        elif self.sensorType == "Volume":
            return " Gal"
        else:
            return " N/A"

    def stop(self):
        '''
        Stop the sensor. Is called when the sensor config is updated or the sensor is deleted
        :return: 
        '''
        pass

#     def convert_volume(self, volume):
#         if unit == 'L':
#             return volume
#         elif unit == 'qt':
#             return float(volume) / 1.057
#         elif unit == 'Gal':
#             return float(volume) / 3.785
# 
#     def convert_height(self, hight):
#         if unit == 'L':
#             return hight
#         else:
#             return float(hight) / 2.54

    def convert_pressure(self, value):
        if self.pressureType == "PSI":
            return value * self.kpa_psi
        else:
            return value
    
    def convert_bar(self, value):
        if self.pressureType == "PSI":
            return value / self.bar_psi
        else:
            return value / 100
        
    def execute(self):
        '''
        Active sensor has to handle its own loop
        :return: 
        '''
        GRAVITY = float(self.GRAVITY)
        GAIN = self.GAIN
        VOLT = float(self.VOLT)
        ch = int(self.ADSchannel)
        
        pressureHigh = self.convert_pressure(self.pressureHigh)
        pressureLow = self.convert_pressure(self.pressureLow)
        #cbpi.app.logger.info('Pressure values - low: %s , high: %s' % ((pressureLow), (pressureHigh)))
        # We need the coefficients to calculate pressure for the next step
        # Using Y=MX+B where X is the volt output difference, M is kPa/volts or pressure difference / volt difference
        #  B is harder to explain, it's the offset of the voltage & pressure, ex:
        #    if volts were 1-5V and pressure was 0-6kPa
        #    since volts start with 1, there is an offset
        #    We calculate a value of 1.5kPa/V, therefore 1V = -1.5
        #    if the output of the sensor was 0-5V there would be no offset
        calcX = self.voltHigh - self.voltLow
        #cbpi.app.logger.info('calcX value: %s' % (calcX))
        calcM = (pressureHigh - pressureLow) / calcX
        #cbpi.app.logger.info('calcM value: %s' % (calcM))
        calcB = 0
        if self.voltLow > 0:
            calcB = (-1 * self.voltLow) * calcM
        #cbpi.app.logger.info('calcB value: %s' % (calcB))

        while self.is_running():

            adc = Adafruit_ADS1x15.ADS1115()
            
            value= adc.read_adc(ch, gain=GAIN)
            #cbpi.app.logger.info('Pressure Sensor value %s' % (value))    #debug or calibration

            # Need to convert value to voltage: y=ax/1000 where a is your value and x is scale factor of mV per bit
            # Note, there are 32,768 possible output values (0-32,767)
            # so x = maximum voltage (based on GAIN) / 32,767, ex: GAIN of 1 yields 4.096V so x=0.000125
            voltage = (value * (VOLT/32767))
            #cbpi.app.logger.info('voltage value %.3f' % (voltage))    #debug or calibration

            pressureValue = (calcM * voltage) + calcB    # "%.6f" % ((calcM * voltage) + calcB)
            #cbpi.app.logger.info("pressureValue: %s" % (pressureValue))    #debug or calibration
            
            # Time to calculate the other data values
            
            # Liquid Level is calculated by H = P / (SG * G). Assume the SG of water is 1.000
            #   this is true for water at 4C
            #   note: P needs to be in BAR and H value will need to be multiplied by 100,000 to get mm
            liquidLevel = ((self.convert_bar(pressureValue) / GRAVITY) * 100000) / self.inch_mm
            if liquidLevel > 0.49:
                liquidLevel += float(self.sensorHeight)
            
            # Volume is calculated by V = PI (r squared) * height
            kettleDiameter = float(self.kettleDiameter)
            kettleRadius = kettleDiameter / 2
            radiusSquared = kettleRadius * kettleRadius
            volume_CI = self.PI * radiusSquared * liquidLevel
            volume = volume_CI / self.gallons_cubicinch

            if self.sensorType == "Voltage":
                reading = "%.6f" % (voltage)
            elif self.sensorType == "Digits":
                reading = value
            elif self.sensorType == "Pressure":
                reading = "%.6f" % (pressureValue)
            elif self.sensorType == "Liquid Level":
                reading = "%.6f" % (liquidLevel)
            elif self.sensorType == "Volume":
                reading = "%.6f" % (volume)
            else:
                pass
            
            self.data_received(reading)

            self.api.socketio.sleep(3)
            

@cbpi.initalizer()
def init(cbpi):
    
    
    pass
