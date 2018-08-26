import types
import pandas as pd
import numpy as np
import datetime
import DriverSchedule as ds
import os

PATH = r'/Users/eveyw/Desktop/SmartPark_DataExtract/extractData'

def create_dictionary():
    shuttle_dictionary = {}
    for i in range(ds.Driver.NUM_OF_SHUTTLE):
        shuttle_dictionary[ds.Driver.SHUTTLE_NUM[i]] = ds.Driver.PHONE_ID[i]
    return shuttle_dictionary
    # for key in shuttle_dictionary:
    #     print key, '=>', shuttle_dictionary[key]


def readgps(shuttle_num, start_time, end_time, file_name):
    """
    :param shuttle_num: '787'
    :param start_time: lower bound timestamp    (length = 13)
    :param end_time:    upper bound timestamp   (length = 13)
    :param file_name:  'Gps0706-0710.csv'
    :return: GPS data of this shuttle
    """
    # [start_time, end_time)
    my_matrix = pd.read_csv(file_name, header=None)
    # find the phone_id of corresponding shuttle
    shuttle_dict = create_dictionary()
    if shuttle_num in shuttle_dict.keys():
        phone_id = shuttle_dict[shuttle_num]
    else:
        print('No GPS data of this shuttle, please check it again!')
        return -1
    gps = my_matrix.loc[my_matrix.loc[:,1] == phone_id, :]
    gps = gps.loc[(start_time <= gps.loc[:,2]) & (gps.loc[:,2] < end_time), :]
    return gps


def driver_schedule(schedule):
    """
    :param schedule: schedule file, csv format, eg: 'Schedule0705-0709(comma).csv'
    :return: dictionary: key -> driver name     value -> list of schedule
    """
    my_matrix = pd.read_csv(schedule, header=None)
    df = pd.DataFrame(my_matrix.iloc[1:len(my_matrix),:])
    df.columns = my_matrix.loc[0]
    driver_dictionary = {}

    for date in df.columns:
        current_column = df[date]
        for info in current_column:
            if isinstance(info, types.StringType):
                info = info + ',' + date
                temp = info.split(',')
                driver_dictionary.setdefault(temp[2], []).append(temp)
    for key in driver_dictionary.keys():
        print(key, '=>', driver_dictionary.get(key))
        print(key, '====>',len(driver_dictionary.get(key)))
    return driver_dictionary


# driver who works most times, but may drive shuttles which are not we cared about
def get_max_driver(driver_dictionary):
    """
    :param driver_dictionary: return value of driver_schedule(schedule)
    :return: find the driver who works the most day
    """
    temp_key = ''
    length = -1
    for key in driver_dictionary.keys():
        if len(driver_dictionary.get(key)) > length:
            length = len(driver_dictionary.get(key))
            temp_key = key
    # print length
    # print temp_key
    return temp_key

####################################################


def get_driver_schedule(dictionary, driver):
    """
    :param dictionary:  return value of driver_schedule()
    :param driver: ds.Driver()
    :return: driver schedule who has worked most of days
    """
    array = driver.read_bus_assignments("virtualScheduleSEP.csv")

    # sort dictionary as list which is according to length of values
    sorted_list = sorted(dictionary.items(), key=lambda item: len(item[1]), reverse=True)

    driver_schedule_dict = {}

    for temp in sorted_list:
        # print temp
        for schedule in temp[1]:
            print('aaaaaaaaaaaaaaaaaaa')
            print(schedule)
            print('aaaaaaaaaaaaaaaaaaa')
            # Just consider date_start, we assume date_end is for next driver: [a, b)
            time = schedule[1].split('-')
            date = schedule[3]
            date_start = date + ' ' + driver.convert_ap_pm(date, time[0])
            print(time, '===>', date)
            print(date_start)
            timestamp_start = driver.date_to_timestamp(date_start)
            # print timestamp_start
            for i in range(driver.NUM_OF_SHUTTLE):
                # print i
                return_start = driver.read_bus_details(array, i, timestamp_start)
                if return_start != -1:
                    temp1 = driver.get_driver_info("Schedule0918-0924(csv).csv", return_start, timestamp_start)
                    if type(temp1) == list:
                        if temp1[2] == temp[0]:     # the same driver name
                            temp1.append(date)
                            temp1.append(i)
                            driver_schedule_dict.setdefault(temp[0],[]).append(temp1)

    # used to save correct schedule: correct means having corresponding GPS data
    driver_list = sorted(driver_schedule_dict.items(), key=lambda item: len(item[1]), reverse=True)
    print('*************************')
    print(len(driver_list))
    count = 0;
    for i in driver_list:
        print count;
        count += 1;
        print(i)
    print('*************************')
    # driver who has most number of correct schedule
    hardest_driver = driver_list[7]     ###choose ith driver
    return hardest_driver


def get_new_time_range(current_time):
    """
    :param current_time: 2017/7/5 15:0
    :return: [2017/7/5 14:55, 2017/7/5 15:5]
    """
    dt = datetime.datetime.strptime(current_time, "%Y/%m/%d %H:%M")
    time_range = []
    dt_s = dt + datetime.timedelta(seconds=-300)    # 5 minutes
    dt_e = dt + datetime.timedelta(seconds=300)     # 5 minutes
    time_range.append(dt_s.strftime("%Y/%-m/%-d %-H:%-M"))
    time_range.append(dt_e.strftime("%Y/%-m/%-d %-H:%-M"))
    # for i in time_range:
    #     print i
    return time_range


def find_index(timestamp, location, t_location):
    """
    :param index: index list of gps
    :param location:  location list
    :param t_location: duplicated value
    :return: first and last index
    """
    position = []
    temp = []
    for i in range(len(location)):
        if np.array_equal(location[i], t_location):
            temp.append(i)
    position.append(timestamp[temp[0]])
    position.append(timestamp[temp[-1]])
    return position


def check_gps_repeat(gps, times):
    """
    :param gps: gps list
    :param times: repeat count
    :return: if count >= times return index of start and end of repeat tuple
    """
    latitude = []
    longitude = []
    timestamp = []
    for i in gps.index:       # not begin from 0
        timestamp.append(gps.loc[i,2])
        latitude.append(gps.loc[i, 4])
        longitude.append(gps.loc[i, 3])

    temp_latitude = latitude[0]
    temp_longitude = longitude[0]
    count = 1
    for i in range(1, len(latitude)):
        if latitude[i] == temp_latitude and longitude[i] == temp_longitude:
            count += 1
        else:
            count = 1
            temp_longitude = longitude[i]
            temp_latitude = latitude[i]

    if count >= times:
        location = []
        t_location = []
        for i in range(len(latitude)):
            temp_l = [latitude[i], longitude[i]]
            location.append(temp_l)
        t_location.append(temp_latitude)
        t_location.append(temp_longitude)

        position1 = find_index(timestamp, location, t_location)
        return position1,position1
    else:
        position1 = [timestamp[0], timestamp[-1]]
        print(position1[0], '-->', position1[1])
        return -1,position1


def get_gps_data(schedule, file_name, driver):
    """
    :param schedule: driver's correct schedule list
    :param file_name: 'Gps0706-0710.csv'
    :param driver: driver = ds.Driver()
    :return: GPS data or -1
    """
    print(schedule)
    time_range = schedule[1].split('-')
    date_start = schedule[3] + ' ' + driver.convert_ap_pm(schedule[3], time_range[0])
    date_end = schedule[3] + ' ' + driver.convert_ap_pm(schedule[3], time_range[1])
    head_range = get_new_time_range(date_start)
    tail_range = get_new_time_range(date_end)
    ha = driver.date_to_timestamp(head_range[0])*1000
    he = driver.date_to_timestamp(head_range[1])*1000
    ta = driver.date_to_timestamp(tail_range[0])*1000
    te = driver.date_to_timestamp(tail_range[1])*1000
    # print ha/1000, '--->', he/1000
    # print ta/1000, '--->', te/1000
    head_gps = readgps(driver.SHUTTLE_NUM[schedule[4]], ha, he, file_name)
    # print head_gps
    tail_gps = readgps(driver.SHUTTLE_NUM[schedule[4]], ta, te, file_name)
    # print '-------------------------------->'
    # print tail_gps
    a,c = check_gps_repeat(head_gps, 300)
    b,d = check_gps_repeat(tail_gps, 300)
    if a != -1 and b != -1:
        print(a[0], '-->', b[0])
        t1 = a[0]
        t2 = b[0]
        gps = readgps(driver.SHUTTLE_NUM[schedule[4]], t1, t2, file_name)
        print('lalalala' + driver.SHUTTLE_NUM[schedule[4]])
        return gps
    elif a == -1 and b != -1:
        print('Shuttle Late!')
        # print c[0], '-->', c[1]
        gps = readgps(driver.SHUTTLE_NUM[schedule[4]], c[0], c[1], file_name)
        print('lalalala' + driver.SHUTTLE_NUM[schedule[4]])
        # return -1
        return gps
    elif b == -1:
        print('Driver Late!')
        # print d[0], '-->', d[1]
        gps = readgps(driver.SHUTTLE_NUM[schedule[4]], d[0], d[1], file_name)
        print('lalalala' + driver.SHUTTLE_NUM[schedule[4]])
        # return -1
        return gps

def download_gps_data(schedule, file_name, driver):
    """
   :param schedule: driver's correct schedule list
   :param file_name: 'Gps0706-0710.csv'
   :param driver: driver = ds.Driver()
   :return: gps
    """

    print(schedule)
    time_range = schedule[1].split('-')
    date_start = schedule[3] + ' ' + driver.convert_ap_pm(schedule[3], time_range[0])
    date_end = schedule[3] + ' ' + driver.convert_ap_pm(schedule[3], time_range[1])
    ha = driver.date_to_timestamp(date_start) * 1000
    he = driver.date_to_timestamp(date_end) * 1000

    return_gps = readgps(driver.SHUTTLE_NUM[schedule[4]], ha, he, file_name)
    return return_gps

def extractData(start_time, end_time, file_name):
    """
    :param start_time: lower bound timestamp    (length = 13)
    :param end_time:    upper bound timestamp   (length = 13)
    :param file_name:  'Gps0706-0710.csv'
    :return: data of this shuttle
    """
    # [start_time, end_time)
    my_matrix = pd.read_csv(file_name, header=None)
    # find the phone_id of corresponding shuttle
    data = my_matrix.loc[(start_time <= my_matrix.loc[:, 3]) & (my_matrix.loc[:, 3] < end_time), :]
    return data
# current_path = os.getcwd()
# path = current_path+'\\data'


dictionary = driver_schedule('Schedule0918-0924(csv).csv')
# driver1 = get_max_driver(dictionary)
driver = ds.Driver()
hardest_driver = get_driver_schedule(dictionary, driver)
print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
print(hardest_driver[1])
for i in hardest_driver[1]:
    print(i)
print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
schedule_list = hardest_driver[1]
print(type(schedule_list))
for i in range(len(schedule_list)):
    print('------------------------------------>')
    print(schedule_list[i])
    gps = download_gps_data(schedule_list[i], 'Gps.csv', driver)
    gps.to_csv(os.path.join(PATH,"gps" + str(i) + ".csv"))
    # acce = download_gps_data(schedule_list[i], 'E', driver)
    # acce.to_csv(os.path.join(PATH,"acce" + str(i) + ".csv"))
    # gyro = download_gps_data(schedule_list[i], 'Gyroscope.csv', driver)
    # gyro.to_csv(os.path.join(PATH,"gyro" + str(i) + ".csv"))
    # magne = download_gps_data(schedule_list[i], 'Magnetometer.csv', driver)
    # magne.to_csv(os.path.join(PATH,"magne" + str(i) + ".csv"))
    # motion = download_gps_data(schedule_list[i], 'MotionState.csv', driver)
    # motion.to_csv(os.path.join(PATH,"motion" + str(i) + ".csv"))


# driver = ds.Driver()
# PATH = r'/Users/youngq/Documents/Pycharm27/LearnPycharm/BusAssignments/extractData/right'
# list = [['up', '4:05 PM - 4:19 PM', 'Tianming','2017/9/29', 2],['rrt', '4:25 PM - 4:50 PM', 'Tianming','2017/9/29', 2],['cs', '5:07 PM - 5:20 PM', 'Tianming','2017/9/29', 2]]
# for i in range(len(list)):
#     print '------------------------------------>'
#     print list[i]
#     gps = download_gps_data(list[i], 'Gps.csv', driver)
#     gps.to_csv(os.path.join(PATH,list[i][0] + '_' + 'gps' + '.csv'))
#     # gps.to_csv("gps" + str(i) + ".csv")
#     acce = download_gps_data(list[i], 'Accelerometer.csv', driver)
#     acce.to_csv(os.path.join(PATH, list[i][0] + '_' + 'acce' + '.csv'))
#     # acce.to_csv("acce" + str(i) + ".csv")
#     gyro = download_gps_data(list[i], 'Gyroscope.csv', driver)
#     gyro.to_csv(os.path.join(PATH, list[i][0] + '_' + 'gyro' + '.csv'))
#     # gyro.to_csv("gyro" + str(i) + ".csv")

# driver = ds.Driver()
# list = ['21:30,21:55,RRT','22:45,23:00,GAS']
#
# for i in list:
#     t = i.split(',')
#     start = driver.date_to_timestamp("2017/8/23 " + t[0])*1000
#     end = driver.date_to_timestamp("2017/8/23 " + t[1])*1000
#     gps = extractData(start, end, 'gps1.csv')
#     gps.to_csv(t[2] + '_' + 'gps' + '.csv')
#     gyro = extractData(start, end, 'gyro1.csv')
#     gyro.to_csv(t[2] + '_' + 'gyro' + '.csv')
#     acce = extractData(start, end, 'acce1.csv')
#     acce.to_csv(t[2] + '_' + 'acce' + '.csv')



# start = driver.date_to_timestamp("2017/7/15 18:00")*1000
# end = driver.date_to_timestamp("2017/7/15 18:25")*1000
# gps = extractData(start, end, 'gps5.csv')
# gps.to_csv('OAK' + '_' + 'gps' + '.csv')
# gyro = extractData(start, end, 'gyro5.csv')
# gyro.to_csv('OAK' + '_' + 'gyro' + '.csv')
# acce = extractData(start, end, 'acce5.csv')
# acce.to_csv('OAK' + '_' + 'acce' + '.csv')

