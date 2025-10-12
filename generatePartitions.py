from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
def generate_smart_powerbi_partitions(
    archive_number,
    archive_granularity,
    refresh_number,
    refresh_granularity,
    effective_date
):
    refresh_partitions = []
    archive_partitions = []
    dt = effective_date
    # year = dt.year
    # quarter = f"{dt.year}Q{(dt.month - 1) // 3 + 1}"
    # month = f"{dt.year}Q{(dt.month - 1) // 3 + 1}{dt.strftime('%m')}"
    # day = f"{dt.year}Q{(dt.month - 1) // 3 + 1}{dt.strftime('%m%d')}"
    # Step 1: Get refresh partitions
    if refresh_granularity != "quarter":
        refresh_start_date = effective_date - relativedelta(**{f"{refresh_granularity}s": refresh_number }) + timedelta(days=1)
    else:
        refresh_start_date = effective_date - relativedelta(**{f"months": (refresh_number ) * 3})  + timedelta(days=1)
    refresh_end_date = effective_date
    if refresh_granularity == 'day':
        tempdate = refresh_start_date
        while tempdate <= refresh_end_date:
            refresh_partitions.append(tempdate.strftime("%Y") + "Q" + str((tempdate.month - 1) // 3 + 1) + tempdate.strftime("%m%d"))
            tempdate += timedelta(days=1)
    elif refresh_granularity == 'month':
        tempdate = refresh_start_date.replace(day=1) + relativedelta(months=1) 
        while tempdate <= refresh_end_date.replace(day=1):
            refresh_partitions.append(tempdate.strftime("%Y") + "Q" + str((tempdate.month - 1) // 3 + 1) + tempdate.strftime("%m"))
            tempdate += relativedelta(months=1)
    elif refresh_granularity == 'quarter':
        tempdate = refresh_start_date.replace(day=1) + relativedelta(months=3 - (refresh_start_date.month - 1) % 3)
        while tempdate <= refresh_end_date.replace(day=1):
            refresh_partitions.append(tempdate.strftime("%Y") + "Q" + str((tempdate.month - 1) // 3 + 1))
            tempdate += relativedelta(months=3)
    elif refresh_granularity == 'year':
        tempdate = refresh_start_date.replace(month=1,day=1) + relativedelta(years=1)
        while tempdate <= refresh_end_date.replace(month=1,day=1):
            refresh_partitions.append(tempdate.strftime("%Y"))
            tempdate += relativedelta(years=1)
    
    # Step 2: Get archive partitions
    if archive_granularity != "quarter":
        archive_start_date = effective_date - relativedelta(**{f"{archive_granularity}s": archive_number}) + timedelta(days=1)
    else:
        archive_start_date = effective_date - relativedelta(**{f"months": (archive_number ) * 3}) + timedelta(days=1)
    if refresh_granularity != "quarter":
        archive_end_date= effective_date - relativedelta(**{f"{refresh_granularity}s": refresh_number}) + timedelta(days=1)
    else:
        archive_end_date = effective_date - relativedelta(**{f"months": (refresh_number ) * 3}) + timedelta(days=1)
    
    if archive_granularity == 'year':
        if refresh_granularity == 'day':
            tempdate = archive_end_date - relativedelta(years=1)
            while tempdate >= archive_start_date:
                archive_partitions.append(tempdate.strftime("%Y"))
                tempdate -= relativedelta(years=1)
            archive_start_date = archive_start_date.replace(month=1,day=1) + relativedelta(years=archive_number) 
            tempdate = archive_end_date - relativedelta(months=3)
            addedQuarters = 0
            while tempdate >= archive_start_date:
                archive_partitions.append(tempdate.strftime("%Y") + "Q" + str((tempdate.month - 1) // 3 + 1))
                addedQuarters += 1
                tempdate -= relativedelta(months=3)
            archive_start_date = archive_start_date + relativedelta(months=addedQuarters*3)
            tempdate = archive_end_date - relativedelta(months=1)
            addedMonths = 0
            while tempdate >= archive_start_date:
                archive_partitions.append(tempdate.strftime("%Y") + "Q" + str((tempdate.month - 1) // 3 + 1) + tempdate.strftime("%m"))
                addedMonths += 1
                tempdate -= relativedelta(months=1)
            archive_start_date = archive_start_date + relativedelta(months=addedMonths)
            tempdate = archive_end_date - timedelta(days=1)
            while tempdate >= archive_start_date:
                archive_partitions.append(tempdate.strftime("%Y") + "Q" + str((tempdate.month - 1) // 3 + 1) + tempdate.strftime("%m%d"))
                tempdate -= timedelta(days=1)
        elif refresh_granularity == 'month':
            tempdate = archive_end_date - relativedelta(years=1)
            while tempdate >= archive_start_date:
                archive_partitions.append(tempdate.strftime("%Y"))
                tempdate -= relativedelta(years=1)
            archive_start_date = archive_start_date.replace(month=1,day=1) + relativedelta(years=archive_number) 
            tempdate = archive_end_date - relativedelta(months=3)
            addedQuarters = 0
            while tempdate >= archive_start_date:
                archive_partitions.append(tempdate.strftime("%Y") + "Q" + str((tempdate.month - 1) // 3 + 1))
                addedQuarters += 1
                tempdate -= relativedelta(months=3)
            archive_start_date = archive_start_date + relativedelta(months=addedQuarters*3)
            tempdate = archive_end_date - relativedelta(months=1)
            while tempdate >= archive_start_date:
                archive_partitions.append(tempdate.strftime("%Y") + "Q" + str((tempdate.month - 1) // 3 + 1) + tempdate.strftime("%m"))
                tempdate -= relativedelta(months=1)
        elif refresh_granularity == 'quarter':
            tempdate = archive_end_date - relativedelta(years=1)
            while tempdate >= archive_start_date:
                archive_partitions.append(tempdate.strftime("%Y"))
                tempdate -= relativedelta(years=1)
            archive_start_date = archive_start_date.replace(month=1,day=1) + relativedelta(years=archive_number) 
            tempdate = archive_end_date - relativedelta(months=3)
            while tempdate >= archive_start_date:
                archive_partitions.append(tempdate.strftime("%Y") + "Q" + str((tempdate.month - 1) // 3 + 1))
                tempdate -= relativedelta(months=3)
        elif refresh_granularity == 'year': 
            tempdate = archive_end_date - relativedelta(years=1)
            while tempdate >= archive_start_date:
                archive_partitions.append(tempdate.strftime("%Y"))
                tempdate -= relativedelta(years=1)
    elif archive_granularity == 'quarter':
        if refresh_granularity == 'day':
            tempdate = archive_end_date - relativedelta(months=3)
            while tempdate >= archive_start_date:
                archive_partitions.append(tempdate.strftime("%Y") + "Q" + str((tempdate.month - 1) // 3 + 1))
                tempdate -= relativedelta(months=3)
            archive_start_date = archive_start_date + relativedelta(months=3) 
            tempdate = archive_end_date - relativedelta(months=1)
            addedMonths = 0
            while tempdate >= archive_start_date:
                archive_partitions.append(tempdate.strftime("%Y") + "Q" + str((tempdate.month - 1) // 3 + 1) + tempdate.strftime("%m"))
                addedMonths += 1
                tempdate -= relativedelta(months=1)
            archive_start_date = archive_start_date + relativedelta(months=addedMonths)
            tempdate = archive_end_date - timedelta(days=1)
            while tempdate >= archive_start_date:
                archive_partitions.append(tempdate.strftime("%Y") + "Q" + str((tempdate.month - 1) // 3 + 1) + tempdate.strftime("%m%d"))
                tempdate -= timedelta(days=1)
        elif refresh_granularity == 'month':
            tempdate = archive_end_date - relativedelta(months=3)
            while tempdate >= archive_start_date:
                archive_partitions.append(tempdate.strftime("%Y") + "Q" + str((tempdate.month - 1) // 3 + 1))
                tempdate -= relativedelta(months=3)
            archive_start_date = archive_start_date + relativedelta(months=3) 
            tempdate = archive_end_date - relativedelta(months=1)
            while tempdate >= archive_start_date:
                archive_partitions.append(tempdate.strftime("%Y") + "Q" + str((tempdate.month - 1) // 3 + 1) + tempdate.strftime("%m"))
                tempdate -= relativedelta(months=1)
        elif refresh_granularity == 'quarter':
            tempdate = archive_end_date - relativedelta(months=3)
            while tempdate >= archive_start_date:
                archive_partitions.append(tempdate.strftime("%Y") + "Q" + str((tempdate.month - 1) // 3 + 1))
                tempdate -= relativedelta(months=3)
    elif archive_granularity == 'month':
        if refresh_granularity == 'day':
            tempdate = archive_end_date - relativedelta(months=1)
            while tempdate >= archive_start_date:
                archive_partitions.append(tempdate.strftime("%Y") + "Q" + str((tempdate.month - 1) // 3 + 1) + tempdate.strftime("%m"))
                tempdate -= relativedelta(months=1)
            archive_start_date = archive_start_date + relativedelta(months=1) 
            tempdate = archive_end_date - timedelta(days=1)
            while tempdate >= archive_start_date:
                archive_partitions.append(tempdate.strftime("%Y") + "Q" + str((tempdate.month - 1) // 3 + 1) + tempdate.strftime("%m%d"))
                tempdate -= timedelta(days=1)
        elif refresh_granularity == 'month':
            tempdate = archive_end_date - relativedelta(months=1)
            while tempdate >= archive_start_date:
                archive_partitions.append(tempdate.strftime("%Y") + "Q" + str((tempdate.month - 1) // 3 + 1) + tempdate.strftime("%m"))
                tempdate -= relativedelta(months=1)
    elif archive_granularity == 'day':
        if refresh_granularity == 'day':
            tempdate = archive_end_date - timedelta(days=1)
            while tempdate >= archive_start_date:
                archive_partitions.append(tempdate.strftime("%Y") + "Q" + str((tempdate.month - 1) // 3 + 1) + tempdate.strftime("%m%d"))
                tempdate -= timedelta(days=1)
    return [archive_partitions, refresh_partitions]

print(generate_smart_powerbi_partitions(4, 'year', 10, 'quarter', datetime(2025, 10, 12)))