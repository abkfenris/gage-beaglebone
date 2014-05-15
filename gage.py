# import gage_config
import config
import ultrasound
# import power

print "DepthAIN is " + config.DepthAIN
print ultrasound.checkDepth(config.DepthAIN,6)
