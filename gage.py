# import gage_config
import config
import ultrasound
# import power

print "DepthAIN is " + config.DepthAIN
print ultrasound.depthCheck(config.DepthAIN,6)
