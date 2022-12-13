import datetime
from dateutil.relativedelta import relativedelta

print(datetime.datetime(year=2022, month=3, day=31) + relativedelta(months=-11))
print(datetime.datetime(year=2022, month=2, day = 1).month)