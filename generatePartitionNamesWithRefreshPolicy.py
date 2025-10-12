from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

_gr_order = ["day", "month", "quarter", "year"]  # increasing coarseness


def _norm(g):
    return g.strip().lower()


def _align_start(dt, gran):
    if gran == "year":
        return dt.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    if gran == "quarter":
        qmonth = ((dt.month - 1) // 3) * 3 + 1
        return dt.replace(month=qmonth, day=1, hour=0, minute=0, second=0, microsecond=0)
    if gran == "month":
        return dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if gran == "day":
        return dt.replace(hour=0, minute=0, second=0, microsecond=0)
    raise ValueError("Invalid granularity")


def _next_boundary(dt, gran):
    if gran == "year":
        return _align_start(dt, "year") + relativedelta(years=1)
    if gran == "quarter":
        return _align_start(dt, "quarter") + relativedelta(months=3)
    if gran == "month":
        return _align_start(dt, "month") + relativedelta(months=1)
    if gran == "day":
        return _align_start(dt, "day") + timedelta(days=1)
    raise ValueError("Invalid granularity")


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
    raise ValueError("Invalid granularity")


def generate_smart_powerbi_partitions(
    archive_number,
    archive_granularity,
    refresh_number,
    refresh_granularity,
    effective_date
):
    archive_granularity = _norm(archive_granularity)
    refresh_granularity = _norm(refresh_granularity)
    if archive_granularity not in _gr_order or refresh_granularity not in _gr_order:
        raise ValueError("Granularity must be one of Year, Quarter, Month, Day")
    if not (isinstance(archive_number, int) and archive_number > 0 and isinstance(refresh_number, int) and refresh_number > 0):
        raise ValueError("Periods must be positive whole numbers")

    if not isinstance(effective_date, datetime):
        effective_date = datetime(effective_date.year, effective_date.month, effective_date.day)

    eff = effective_date.replace(hour=0, minute=0, second=0, microsecond=0)

    # inclusive stored window start .. eff
    if archive_granularity == "quarter":
        stored_start = eff - relativedelta(months=archive_number * 3) + timedelta(days=1)
    else:
        kw = {f"{archive_granularity}s": archive_number}
        stored_start = eff - relativedelta(**kw) + timedelta(days=1)

    # inclusive refresh window start .. eff
    if refresh_granularity == "quarter":
        refresh_start = eff - relativedelta(months=refresh_number * 3) + timedelta(days=1)
    else:
        kw = {f"{refresh_granularity}s": refresh_number}
        refresh_start = eff - relativedelta(**kw) + timedelta(days=1)

    stored_start = stored_start.replace(hour=0, minute=0, second=0, microsecond=0)
    refresh_start = refresh_start.replace(hour=0, minute=0, second=0, microsecond=0)

    # permitted granularities (coarsest first) up to archive_granularity
    max_rank = _gr_order.index(archive_granularity)
    permitted = _gr_order[: max_rank + 1][::-1]  # e.g. ['year','quarter','month','day']

    parts = []
    cur = stored_start

    # cover older part before refresh_start using largest aligned buckets that fit entirely before refresh_start
    while cur < refresh_start:
        placed = False
        for gran in permitted:
            if _align_start(cur, gran) != cur:
                continue
            nxt = _next_boundary(cur, gran)
            if nxt <= refresh_start:
                parts.append(_name_for(cur, gran))
                cur = nxt
                placed = True
                break
        if not placed:
            # no larger bucket fits; fallback to day
            parts.append(_name_for(cur, "day"))
            cur += timedelta(days=1)

    # cover refresh window with exact refresh_granularity partitions
    cur = refresh_start
    while cur <= eff:
        parts.append(_name_for(cur, refresh_granularity))
        if refresh_granularity == "day":
            cur += timedelta(days=1)
        elif refresh_granularity == "month":
            cur += relativedelta(months=1)
        elif refresh_granularity == "quarter":
            cur += relativedelta(months=3)
        elif refresh_granularity == "year":
            cur += relativedelta(years=1)

    return parts

# Example usage:
partitions = generate_smart_powerbi_partitions(4, "Year", 10, "Quarter", datetime(2025,10,12))
print(partitions)