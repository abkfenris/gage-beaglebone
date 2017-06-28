"""
Exceptions that the gage may encounter
"""


class SensorError(Exception):
    pass


class SamplingError(Exception):
    pass


class TooFewSamples(SamplingError):
    pass
