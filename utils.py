from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import requests
import time
import math
import config
from termcolor import cprint

_gr_order = ["day", "month", "quarter", "year"]  


def _norm(g):
    return g.strip().lower()


def _start_of(dt, gran):
    if gran == "year":
        return dt.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    if gran == "quarter":
        qm = ((dt.month - 1) // 3) * 3 + 1
        return dt.replace(month=qm, day=1, hour=0, minute=0, second=0, microsecond=0)
    if gran == "month":
        return dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if gran == "day":
        return dt.replace(hour=0, minute=0, second=0, microsecond=0)
    raise ValueError("invalid granularity")


def _end_of(dt, gran):
    s = _start_of(dt, gran)
    if gran == "day":
        return s + timedelta(days=1) - timedelta(seconds=1)
    if gran == "month":
        return (s + relativedelta(months=1)) - timedelta(seconds=1)
    if gran == "quarter":
        return (s + relativedelta(months=3)) - timedelta(seconds=1)
    if gran == "year":
        return (s + relativedelta(years=1)) - timedelta(seconds=1)
    raise ValueError("invalid granularity")


def _next_boundary(dt, gran):
    s = _start_of(dt, gran)
    if gran == "day":
        return s + timedelta(days=1)
    if gran == "month":
        return s + relativedelta(months=1)
    if gran == "quarter":
        return s + relativedelta(months=3)
    if gran == "year":
        return s + relativedelta(years=1)
    raise ValueError("invalid granularity")


def _name_for(dt, gran):
    y = dt.year
    q = (dt.month - 1) // 3 + 1
    if gran == "year":
        return f"{y}"
    if gran == "quarter":
        return f"{y}Q{q}"
    if gran == "month":
        return f"{y}Q{q}{dt.strftime('%m')}"
    if gran == "day":
        return f"{y}Q{q}{dt.strftime('%m%d')}"
    raise ValueError("invalid granularity")


def generate_smart_powerbi_partitions(
    archive_number,
    archive_granularity,
    refresh_number,
    refresh_granularity,
    effective_date = datetime.today(),
    refresh_completed_periods=False
):
    archive_granularity = _norm(archive_granularity)
    refresh_granularity = _norm(refresh_granularity)
    if archive_granularity not in _gr_order or refresh_granularity not in _gr_order:
        raise ValueError("granularity must be one of Year, Quarter, Month, Day")
    if not (isinstance(archive_number, int) and archive_number > 0 and isinstance(refresh_number, int) and refresh_number > 0):
        raise ValueError("periods must be positive whole numbers")
    if not isinstance(effective_date, datetime):
        effective_date = datetime(effective_date.year, effective_date.month, effective_date.day)
    eff = effective_date.replace(hour=0, minute=0, second=0, microsecond=0)

    # if we operate on completed periods, move eff to end of previous period for refresh granularity
    if refresh_completed_periods:
        if refresh_granularity == "day":
            eff = eff - timedelta(days=1)
        else:
            eff = _start_of(eff, refresh_granularity) - timedelta(days=1)

    # refresh window (inclusive)
    if refresh_granularity == "day":
        refresh_start = eff - timedelta(days=refresh_number - 1)
    elif refresh_granularity == "month":
        refresh_start = _start_of(eff - relativedelta(months=refresh_number - 1), "month")
    elif refresh_granularity == "quarter":
        refresh_start = _start_of(eff - relativedelta(months=3 * (refresh_number - 1)), "quarter")
    elif refresh_granularity == "year":
        refresh_start = _start_of(eff - relativedelta(years=refresh_number - 1), "year")
    else:
        raise ValueError("invalid refresh granularity")
    refresh_end = eff

    # archive window: ends the day before refresh_start (inclusive archive_end)
    archive_end = refresh_start - timedelta(days=1)

    # compute archive_start based on the original effective_date (not eff which may be shifted
    # for refresh_completed_periods). align to period start for month/quarter/year.
    orig_eff = effective_date.replace(hour=0, minute=0, second=0, microsecond=0)

    # compute archive_start: last archive_number archive-granularity periods ending at archive_end (inclusive)
    if archive_granularity == "day":
        archive_start = orig_eff - timedelta(days=archive_number) + timedelta(days=1)
    elif archive_granularity == "month":
        archive_start = _start_of(orig_eff - relativedelta(months=archive_number) + timedelta(days=1), "month")
    elif archive_granularity == "quarter":
        archive_start = _start_of(orig_eff - relativedelta(months=archive_number * 3) + timedelta(days=1), "quarter")
    elif archive_granularity == "year":
        archive_start = _start_of(orig_eff - relativedelta(years=archive_number) + timedelta(days=1), "year")
    else:
        raise ValueError("invalid archive granularity")

    # if the computed archive_start is after archive_end, there are no archive partitions
    if archive_start > archive_end:
        archive_start = archive_end + timedelta(days=1)

    refresh_parts = []
    archive_parts = []

    # permitted granularities up to archive_granularity (coarsest first)
    max_idx = _gr_order.index(archive_granularity)
    permitted = _gr_order[: max_idx + 1][::-1]  # e.g. ['year','quarter','month','day']

    cur = archive_start
    # fill archive using largest aligned buckets that fit entirely within [archive_start, archive_end]
    while cur <= archive_end:
        placed = False
        for gran in permitted:
            if _start_of(cur, gran) != cur:
                continue
            nxt = _next_boundary(cur, gran)
            # nxt - 1s must be <= archive_end to fit entirely
            if nxt - timedelta(seconds=1) <= datetime(archive_end.year, archive_end.month, archive_end.day, 23, 59, 59):
                archive_parts.append(_name_for(cur, gran))
                cur = nxt
                placed = True
                break
        if not placed:
            # fallback to day
            archive_parts.append(_name_for(cur, "day"))
            cur = _next_boundary(cur, "day")

    # fill refresh window with exact refresh granularity
    cur = refresh_start
    while cur <= refresh_end:
        refresh_parts.append(_name_for(cur, refresh_granularity))
        cur = _next_boundary(cur, refresh_granularity)

    return {
        "Refresh": refresh_parts,
        "Archive": archive_parts,
        "All": archive_parts + refresh_parts,
    }
#generate_smart_powerbi_partitions(15, "Quarter", 10, "Quarter",effective_date=datetime(2025,12,30),refresh_completed_periods=True )



def refresh_partitions_in_batches(tableName:str ,partitions:list):

    def get_token():
        url = f"https://login.microsoftonline.com/{config.tenantId}/oauth2/v2.0/token"
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {
            "grant_type": "client_credentials",
            "client_id": config.servicePrincipalId,
            "client_secret": config.servicePrincipalSecret,
            "scope": "https://analysis.windows.net/powerbi/api/.default"
        }
        
        response = requests.post(url, headers=headers, data=data)
        
        if response.status_code == 200:
            return response.json().get("access_token")
        else:
            raise Exception(f"Failed to get token: {response.status_code} {response.text}")
    fullEndPoint = f"{config.rootEndPoint }groups/{config.workspaceId}/datasets/{config.datasetId}/refreshes"    
    token = get_token()
    batchCount = math.ceil(len(partitions) / config.batchCount) if len(partitions) > 0 else 0


    def getrefreshStatus():
        response = requests.get(url=f"{fullEndPoint}?$top=1",headers={"Authorization" : f"Bearer {token}","Content-type" : "application/json"})
        if response.status_code != 200:
            response = requests.get(url=f"{fullEndPoint}?$top=1",headers={"Authorization" : f"Bearer {get_token()}","Content-type" : "application/json"})
        return response.json().get("value",{})[0].get("status","")

    def postRefresh(payload):
        response = requests.post(url=fullEndPoint,headers={"Authorization" : f"Bearer {token}","Content-type" : "application/json"},json=payload)
        if response.status_code != 202:
            response = requests.post(url=fullEndPoint,headers={"Authorization" : f"Bearer {get_token()}","Content-type" : "application/json"},json=payload)
        return response.status_code


    cprint(f"Total Batches to process: {batchCount}",'blue')
    for batch_num in range(batchCount):
        objects = []
        temp = partitions[batch_num * config.batchCount : (batch_num + 1) * config.batchCount]
        for i in temp:
            objects.append({"table":tableName, "partition": i})
        config.payload["objects"] = objects

        try:
            # wait until service is idle before triggering this batch
            while True:
                status = getrefreshStatus()
                cur_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cprint(f"Current Status at {cur_time}: {status}",'green' if status=="Completed" else 'red' if status=="Failed" else 'yellow')
                if status in ["Completed", "Failed", "None"]:
                    break
                cprint("Waiting while the refresh is running",'yellow')
                time.sleep(config.delay)

            # trigger the refresh for this batch
            cprint(f"Triggering for batch {batch_num + 1} with partitions: {temp}",'yellow')
            resp = postRefresh(payload=config.payload)
            if resp != 202:
                cprint(f"Failed to trigger batch {batch_num + 1 }, response: {resp}",'red')
                # decide whether to retry or continue to next batch
                continue
            else:
                cprint(f"Batch {batch_num + 1} triggered successfully.",'blue')

            # poll until this triggered refresh finishes
            while True:
                cprint(f"Waiting for {config.delay} seconds before checking status...",'yellow')
                time.sleep(config.delay)
                status = getrefreshStatus()
                cur_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cprint(f"Current Status {cur_time}: {status}",'green' if status=="Completed" else 'red' if status=="Failed" else 'yellow')
                if status in ["Completed", "Failed", "None"]:
                    cprint(f"Batch {batch_num + 1} finished with status: {status}",'green' if status=="Completed" else 'red')
                    if batch_num + 1 == batchCount:
                        cprint("All batches processed.",'blue')
                    break

        except Exception as e:
            cprint(f"Error while running the API: {e}",'red')