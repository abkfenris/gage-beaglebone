# import gage_config
import config
import ultrasound
# import power

print "DepthAIN is " + config.DepthAIN
print "The depth in inches is" + str(ultrasound.checkDepth(config.DepthAIN,6))
print ""
