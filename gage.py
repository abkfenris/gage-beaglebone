# import gage_config
import config
import ultrasound
# import power

print "DepthAIN is " + config.DepthAIN
print ultrasound.depthCheckMath(config.DepthAIN,6)


print "PowerAIN is " + config.PowerAIN
print power.powerCheckMath()