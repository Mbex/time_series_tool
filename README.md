# time_series_tool
## Gui to clean and process raw time series data. 

This programme reads time series csv data (typically produced via pandas). A GUI interface lets the user:
. Remove bad data
. Normalise the trace to another trace
. Calibrate the trace (i.e. rescale the y axis)
Many pandas features are retained such as multiple axis toggling, stats reporting. 
After the new data set is exported a log file is produced detailing the manipulations performed on the original dataset.