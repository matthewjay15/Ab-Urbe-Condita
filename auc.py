# this script requires python 3.7+

import datetime, math        # calculating dates
import json, urllib.request  # getting and parsing sunrise/set data
import sys                   # commandline arguments
import os                    # get start dir
import logging               # debugging

logger = logging.getLogger()
handler = logging.StreamHandler(sys.stdout)

# to debug - add debug argument
if "--debug" in sys.argv:
    logger.setLevel(logging.DEBUG)

formatter = logging.Formatter("%(levelname)s: %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

start_dir = os.path.dirname(os.path.realpath(__file__))

help_text = "Converts dates into a Roman format\n\t--help\t\tshows this help text\n\t--now\t\tconvert current date and time\n\t--custom\t\tconvert a custom date (ISO 8601)\n\t--simple\t\tonly print the Roman format"

roman_months = ["Januarius", "Februarius", "Martius", "Aprilis", "Maius", "Junius", "Quintilius", "Sextilis", "September", "October", "November", "December"]
months_genitive = ["Januarii", "Februarii", "Martii", "Aprilis", "Maii", "Junii", "Quintilii", "Sextilis", "Septembris", "Octobris", "Novembris", "Decembris"]
weekdays = ["Lunae", "Martis", "Mercurii", "Iovis", "Veneris", "Saturni", "Solis"]

def int_to_roman(num):
    # https://stackoverflow.com/a/50012689
    _values = [
        1000000, 900000, 500000, 400000, 100000, 90000, 50000, 40000, 10000, 9000, 5000, 4000, 1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1]

    _strings = [
        'M', 'C', 'D', 'CD', 'C', 'XC', 'L', 'XL', 'X', 'IX', 'V', 'IV', "M", "CM", "D", "CD", "C", "XC", "L", "XL", "X", "IX", "V", "IV", "I"]

    result = ""
    decimal = num

    while decimal > 0:
        for i in range(len(_values)):
            if decimal >= _values[i]:
                if _values[i] > 1000:
                    result += u'\u0304'.join(list(_strings[i])) + u'\u0304'
                else:
                    result += _strings[i]
                decimal -= _values[i]
                break
    logging.debug(f"{num} --> {result}")
    return result

def get_year(input_date):
    # AUC = 21 April 752 BC

    if input_date.month == 4 and input_date.day < 21:
        auc = input_date.year + 752
    elif input_date.month == 4 and input_date.day >= 21:
        auc = input_date.year + 753
    elif input_date.month < 4:
        auc = input_date.year + 752
    elif input_date.month > 4:
        auc = input_date.year + 753
    
    return int_to_roman(auc)

def get_day(input_date):
    result = "dies " + weekdays[input_date.weekday()]
    return result

def get_date(input_date):
    kalends = input_date.replace(day=1)

    if input_date.month in [3, 5, 7, 10]:
        nones = kalends + datetime.timedelta(days = 6)
    else:
        nones = kalends + datetime.timedelta(days = 4)

    ides = nones + datetime.timedelta(days = 8)

    if input_date.day > 13:
        kalends2 = input_date + datetime.timedelta(days = 20)
        kalends2 = kalends2.replace(day = 1)
        kalends2_delta = input_date - kalends2
        logger.debug(f"\n Next month's Kalends:        {str(kalends2)}\n Next month's Kalends' delta: {kalends2_delta}")

    nones_delta = input_date - nones
    ides_delta = input_date - ides

    # for debugging:
    logger.debug(f"\n Kalends: {kalends}\n Nones:   {nones}\n Ides:    {ides}")
    logger.debug(f"\n Nones' delta: {str(nones_delta)}\n Ides' delta:  {str(ides_delta)}")

    # roman date goes to the closest marker in the future not the past, also need to check delta of the kalends of the next month!
    # plus one because Romans counted inclusively...


    if input_date.day == 1:
        day = "kalends " + months_genitive[input_date.month - 1]
    elif input_date.day < nones.day:
        day = "diem " + int_to_roman(abs(nones_delta.days) + 1) + " ante Nonas " + months_genitive[input_date.month - 1]
    elif input_date.day == nones.day:
        day = "Nones " + months_genitive[input_date.month - 1]
    elif input_date.day < ides.day:
        day = "diem " + int_to_roman(abs(ides_delta.days) + 1) + " ante Idus " + months_genitive[input_date.month - 1]
    elif input_date.day == ides.day:
        day = "Idus " + months_genitive[input_date.month - 1]
    else:
        # loop back to January if counting days until next month in December
        if input_date.month == 12:
            day = "diem " + int_to_roman(abs(kalends2_delta.days) + 1) + " ante Kalendas " + months_genitive[0]
        else:
            day = "diem " + int_to_roman(abs(kalends2_delta.days) + 1) + " ante Kalendas " + months_genitive[input_date.month]
    
    return day

def get_time(input_date):
    # get sunrise/sunset from internet, then work out length of hour

    # cache data for a whole day, then get new data when day changes
    if not os.path.exists(os.path.join(start_dir, "cache")):
        os.mkdir(os.path.join(start_dir, "cache"))
    try:
        logger.debug("Checking if today's data is cached")
        with open(os.path.join(start_dir, "cache", "sunrisesunset-" + input_date.strftime("%Y%m%d") + ".json"), "r", encoding="utf-8") as response:
            data = response.read()
            jsondata = json.loads(data)
    except:
        try:
            # requests the data for the current day of timezone - ISO 8601 format
            # TODO do not hardcode location - currently London
            logger.debug("Getting data from internet")
            response = urllib.request.urlopen("https://api.sunrise-sunset.org/json?lat=51.509865&lng=-0.118092&formatted=0&date=" + input_date.strftime("%Y-%m-%d"))
            logger.debug("Writing data to file")
            with open(os.path.join(start_dir, "cache", "sunrisesunset-" + input_date.strftime("%Y%m%d") + ".json"), "w", encoding="utf-8") as outfile:
                data = response.read().decode("utf-8")
                jsondata = json.loads(data)
                json.dump(jsondata, outfile)
        except:
            try:
                logger.debug("Trying to open yesterday's sunrise/set data since network probably down")
                yesterday = input_date - datetime.timedelta(days=1)
                with open(os.path.join(start_dir, "cache", "sunrisesunset-" + yesterday.strftime("%Y%m%d") + ".json"), "r", encoding="utf-8") as response:
                    data = response.read()
                    jsondata = json.loads(data)
            except:
                logger.debug("No internet access and no fallback data files")
                print("No internet access and no fallback data files, program exiting...")
                exit()

    sunrise = datetime.datetime.fromisoformat(jsondata["results"]["sunrise"])
    local_timezone = datetime.datetime.now().astimezone().tzinfo
    sunrise = sunrise.astimezone(local_timezone)

    sunset = datetime.datetime.fromisoformat(jsondata["results"]["sunset"])
    local_timezone = datetime.datetime.now().astimezone().tzinfo
    sunset = sunset.astimezone(local_timezone)

    input_date = input_date.replace(tzinfo=local_timezone)
    logger.debug(f"\n Input date: {input_date}\n Sunrise:    {sunrise}\n Sunset:     {sunset}")

    day_duration = sunset - sunrise
    hour_length = day_duration/12
    midday = sunrise + (day_duration/2)
    morning_portion = input_date - sunrise
    afternoon_portion = sunset - input_date
    logger.debug(f"\n Hour length:      {hour_length}\n Midday:           {midday}\n Morning length:   {morning_portion}\n Afternoon length: {afternoon_portion}")

    if input_date < sunrise:
        hour = int_to_roman(math.floor(abs(morning_portion/hour_length)) + 1)
        time = "hora " + hour + " ante solis ortum"
    elif input_date == sunrise:
        time = "solis ortus"
    elif input_date < midday:
        hour = int_to_roman(math.floor(morning_portion/hour_length) + 1)
        time = "hora " + hour + " post solis ortum"
    elif input_date == midday:
        time = "meridies"
    elif input_date < sunset:
        hour = int_to_roman(math.floor(afternoon_portion/hour_length) + 1)
        time = "hora " + hour + " ante solis occasum"
    elif input_date == sunset:
        time = "solis occasus"
    elif input_date > sunset:
        hour = int_to_roman(math.floor(abs(afternoon_portion/hour_length)) + 1)
        time = "hora " + hour + " post solis occasum"
    
    return time

output = {}

if len(sys.argv) < 2:
    print(help_text)
else:
    if "--help" in sys.argv:
        output["help"] = help_text
    elif "--now" in sys.argv:
        input_date = datetime.datetime.now()
        if "--json" not in sys.argv:
            output["normal"] = input_date.strftime("%H:%M, %A, %-d %B %Y AD")
            output["roman"] = get_time(input_date) + "\n" + get_day(input_date) + "\n" + get_date(input_date) + "\n" + get_year(input_date) + " AUC"
        else:
            output["data"] = json.dumps({
                "normal": {
                    "time": input_date.strftime("%H:%M"),
                    "day": input_date.strftime("%A"),
                    "date": input_date.strftime("%-d %B %Y AD")
                },
                "roman": {
                    "time": get_time(input_date),
                    "day": get_day(input_date),
                    "date": get_date(input_date),
                    "year": get_year(input_date) + " AUC"
                }
            })
    if "--custom" in sys.argv:
        try:
            test = output["normal"]
            print("Please use either --now or --custom date")
            sys.exit()
        except KeyError:
            # TODO custom time not supported
            try:
                input_date = datetime.datetime.fromisoformat(sys.argv[sys.argv.index("--custom") + 1])
            except:
                print("Date not in ISO 8601 format")
                sys.exit()
            output["normal"] = input_date.strftime("%A %-d %B %Y AD")
            output["roman"] = get_day(input_date) + "\n" + get_date(input_date) + "\n" + get_year(input_date) + " AUC"
    
    if "--simple" in sys.argv:
        try:
            output.pop("normal")
        except:
            print("Please select either a normal or custom date")
            sys.exit()
    if output == {}:
        output["help"] = help_text

    for x in output:
        print(output[x])