import utils
from datetime import datetime


Archive_granularity = "year"   # Possible values: "day", "month", "quarter", "year"
Archive_period = 4 # Number of units to archive, any positive integer
Refresh_granularity = "day" # Possible values: "day", "month", "quarter", "year"
Refresh_period = 4 # Number of units to refresh, any positive integer
Effective_date = datetime.today()  # Effective date, format: "YYYY-MM-DD"
Refresh_Completed_Periods = True # Set to True to refresh only completed periods, any boolean value
TableName = "FactInternetSales" # Name of the table to refresh partitions for
Refresh_All_Paritions = True # Set to True to refresh all partitions, any boolean value

if __name__ == "__main__":
    partitions = utils.generate_smart_powerbi_partitions(Archive_period, Archive_granularity, Refresh_period, Refresh_granularity, datetime.today(),True)
    utils.refresh_partitions_in_batches(TableName ,partitions["All"])

