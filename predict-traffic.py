import os
import time

# checks files in the history folder
files = os.listdir("history")
files = [file for file in files if file.endswith(".json")]
files.sort()

hour_now = time.strftime("%H", time.localtime())
day_now = time.strftime("%d", time.localtime())
month_now = time.strftime("%m", time.localtime())
print(hour_now, day_now, month_now)

time_now = int(time.time())
time_7_days_ago = time_now - 7 * 24 * 60 * 60
print(time_now)
print(time_7_days_ago)

data = {}

for filename in files:
    # get timestamp from filename
    timestamp = time.mktime(time.strptime(filename, "%d.%m.%Y-%H:%M.json"))

    # discard files older than 7 days
    if timestamp < time_7_days_ago:
        continue

    # convert timestamp to day month year
    date = time.strftime("%d.%m.%Y-%H:%M", time.localtime(timestamp))
    print(date)