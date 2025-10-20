import utils as utils
from datetime import datetime


RollingWindowGranularity = "quarter"   # Possible values: "day", "month", "quarter", "year"
RollingWindowPeriods = 8 # Number of units to archive, any positive integer
IncrementalGranularity = "quarter" # Possible values: "day", "month", "quarter", "year"
IncrementalPeriods = 1 # Number of units to refresh, any positive integer
Effective_date = datetime.today()  # Effective date, format: "YYYY-MM-DD"
Refresh_Completed_Periods = False # Set to True to refresh only completed periods, any boolean value
TableName = "fact_sales_rawtransactions" # Name of the table to refresh partitions for
Refresh_All_Paritions = True # Set to True to refresh all partitions, any boolean value

if __name__ == "__main__":
    partitions = utils.generate_smart_powerbi_partitions(RollingWindowPeriods, 
                                                         RollingWindowGranularity, 
                                                         IncrementalPeriods, 
                                                         IncrementalGranularity, 
                                                         Effective_date, 
                                                         Refresh_Completed_Periods)
    if Refresh_All_Paritions:
        utils.refresh_partitions_in_batches(TableName ,partitions["All"])
    else:
        utils.refresh_partitions_in_batches(TableName ,partitions["Refresh"])
    # print(partitions)

