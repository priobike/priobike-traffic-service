import os
import time
import json

time_now = int(time.time())
time_7_days_ago = time_now - 60 * 60 * 24 * 7


def build_average(hour_now, files):
    """
    Build average for a given hour over max. last 7 days
    Returns the average score for the given hour or None if no data is available
    """

    global time_now, time_7_days_ago

    # print(time_now)
    # print(time_7_days_ago)

    scores = []

    for filename in files:
        # get timestamp from filename
        timestamp = time.mktime(time.strptime(filename, "%d.%m.%Y-%H:%M.json"))

        # discard files older than 7 days. Files are sorted by date, therefore break at first file older than 7 days
        if timestamp < time_7_days_ago:
            break

        # extract hour from timestamp
        data_hour = int(time.strftime("%H", time.localtime(timestamp)))

        if data_hour == hour_now:
            # open json file and get score
            with open(f"history/{filename}", "r") as file:
                data = json.load(file)
                score = data["trafficflow"]
                scores.append(score)
                print(scores)

    # calculate average score
    if len(scores) != 0:
        return sum(scores) / len(scores)
    else:
        return None


def main():

    # checks files in the history folder
    files = os.listdir("history")
    files = [file for file in files if file.endswith(".json")]
    files.sort(reverse=True)

    hour_now = int(time.strftime("%H", time.localtime()))
    day_now = int(time.strftime("%d", time.localtime()))
    month_now = int(time.strftime("%m", time.localtime()))
    year_now = int(time.strftime("%Y", time.localtime()))
    print(hour_now, day_now, month_now, year_now)

    # get the average scores from hour -1 to hour +3
    hour_score = build_average(hour_now, files)
    next_hour_score = build_average(hour_now + 1, files)
    next2_hour_score = build_average(hour_now + 2, files)
    next3_hour_score = build_average(hour_now + 3, files)
    prev_hour_score = build_average(hour_now - 1, files)


if __name__ == "__main__":
    main()