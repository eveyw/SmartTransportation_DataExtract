import pandas as pd
import time
import datetime
import os
from math import radians, cos, sin, asin, sqrt, fabs

class ExtractMan:
    # SHUTTLE_NUM = ["787", "788", "528", "526"]
    # PHONE_ID = ["023d6dfce95b3997", "01ef64e4dec54025", "024a0c2d305eb3cc", "025391f6de955621"]
    # NUM_OF_SHUTTLE = 4
    # 762 024a09d94ab01756 025c411f85bad2ac
    SHUTTLE_NUM = ["763", "747", "762", "748", "787", "788", "528", "526"]
    PHONE_ID = ["02597a5b9e75cf6c", "02596c2b9e85bf69", "025c411f85bad2ac", "0249cc55455bc6ad",
                "023d6dfce95b3997", "01ef64e4dec54025", "024a0c2d305eb3cc", "025391f6de955621"]
    NUM_OF_SHUTTLE = 8
    BuUnionLat = 42.086942806500474
    BuUnionLon = -75.96704414865724
    PATH = r'/Users/eveyw/Desktop/SmartPark_DataExtract/extractData'

    def __init__(self):
        print('Begin to get Driver information')

    @staticmethod
    def date_to_timestamp(date):  # convert Y/M/D H:M to x xxx xxx xxx . xxx
        time_array = time.strptime(date, "%Y/%m/%d %H:%M")
        timestamp = time.mktime(time_array)
        return timestamp

    @staticmethod
    def get_new_time_range(current_time, seconds):
        """
        :param current_time: 2017/7/5 15:0
        :param seconds:     -120s      or   120s
        :return:     2017/7/5 14:58    or   2017/7/5 15:2
        """
        dt = datetime.datetime.strptime(current_time, "%Y/%m/%d %H:%M")
        dt_s = dt + datetime.timedelta(seconds = seconds)
        return dt_s.strftime("%Y/%-m/%-d %-H:%-M")


    @staticmethod
    def hav(theta):
        s = sin(theta / 2)
        return s * s

    def get_distance_hav(self, lat0, lng0, lat1, lng1):
        r = 6371
        lat0 = radians(lat0)
        lat1 = radians(lat1)
        lng0 = radians(lng0)
        lng1 = radians(lng1)

        dlng = fabs(lng0 - lng1)
        dlat = fabs(lat0 - lat1)
        h = self.hav(dlat) + cos(lat0) * cos(lat1) * self.hav(dlng)
        distance = 2 * r * asin(sqrt(h)) * 1000
        return distance     # return meter

    def data_extract(self, filename, schedule, shuttle_num, date, file_type):
        """
        :param filename:    Gps.csv / Accelerometer.csv / Gyroscope.csv
        :param schedule:    list of list: [[start_time, end_time, route_name], ...]
        :param shuttle_num: index of shuttle: 0 -> 788
        :param date:        eg:2017/7/8
        :param file_type:   gps / acce /gyro    (used for name extracted data file)
        # :param driver:      instance of DriverSchedule: driver = ds.Driver()
        :return:            data with accurate scope
        """
        # create a shuttle info dictionary
        shuttle_dictionary = {}
        for i in range(len(ExtractMan.SHUTTLE_NUM)):  # len(ExtractMan.SHUTTLE_NUM) == NUM_OF_SHUTTLE
            shuttle_dictionary[ExtractMan.SHUTTLE_NUM[i]] = ExtractMan.PHONE_ID[i]

        # get data of corresponding shuttle according to shuttle_num
        my_matrix = pd.read_csv(filename, header=None)
        my_matrix_acce = pd.read_csv('Accelerometer.csv', header=None)
        my_matrix_gyro = pd.read_csv('Gyroscope.csv', header=None)
        my_matrix_motion = pd.read_csv('MotionState.csv', header=None)
        my_matrix_magne = pd.read_csv('Magnetometer.csv', header=None, low_memory=False)
        if shuttle_num in shuttle_dictionary.keys():
            phone_id = shuttle_dictionary[shuttle_num]
        else:
            print('No corresponding data of this shuttle, please check it again!')
            return -1
        data = my_matrix.loc[my_matrix.loc[:, 1] == phone_id, :]
        data_acce = my_matrix_acce.loc[my_matrix_acce.loc[:, 1] == phone_id, :]
        data_gyro = my_matrix_gyro.loc[my_matrix_gyro.loc[:, 1] == phone_id, :]
        data_motion = my_matrix_motion.loc[my_matrix_motion.loc[:, 1] == phone_id, :]
        data_magne = my_matrix_magne.loc[my_matrix_magne.loc[:, 1] == phone_id, :]

        for temp_schedule in schedule:
            list_schedule = temp_schedule.split(',')
            start_time = date + ' ' + list_schedule[0]
            end_time = date + ' ' + list_schedule[1]
            count = 0       # record count of scope change, if bigger than 10 (20minutes), check this schedule, it must has
            flag = False
            while 1:        # something happen
                print(count)
                count += 1
                if count > 20:
                    print('!!!!!!!!!!!!!!!!')
                    flag = True
                    print('check route of this driver, some accidents may happens')
                    print(temp_schedule)
                    print('!!!!!!!!!!!!!!!!')
                    break
                start = self.date_to_timestamp(start_time)*1000
                end = self.date_to_timestamp(end_time)*1000
                result = data.loc[(start <= data.loc[:, 2]) & (data.loc[:, 2] < end), :]
                result_acce = data_acce.loc[(start <= data_acce.loc[:, 2]) & (data_acce.loc[:, 2] < end), :]
                result_gyro = data_gyro.loc[(start <= data_gyro.loc[:, 2]) & (data_gyro.loc[:, 2] < end), :]
                result_motion = data_motion.loc[(start <= data_motion.loc[:, 2]) & (data_motion.loc[:, 2] < end), :]
                result_magne = data_magne.loc[(start <= data_magne.loc[:, 2]) & (data_magne.loc[:, 2] < end), :]
                # result.to_csv(list_schedule[2] + '_' + file_type + '.csv')
                print(start_time + ' ' + end_time)
                if start >= end:
                    print('start time >= end time')
                    flag = True
                    break

                start_lat = result.iloc[0,3]
                start_lon = result.iloc[0,4]
                end_lat = result.iloc[-1,3]
                end_lon = result.iloc[-1,4]
                distance1 = self.get_distance_hav(self.BuUnionLat, self.BuUnionLon, start_lat, start_lon)
                distance2 = self.get_distance_hav(self.BuUnionLat, self.BuUnionLon, end_lat, end_lon)
                # print distance1
                # print distance2
                if distance1 <= 400 and distance2 <= 300:
                    print 'In right scope'
                    break
                if distance1 > 400:
                    print 'last driver late or this driver go early'
                    start_time = self.get_new_time_range(start_time, 120)
                if distance2 > 300:
                    print 'not arrive'
                    end_time = self.get_new_time_range(end_time, 120)
            if not flag:
                result.to_csv(os.path.join(self.PATH,list_schedule[2] + '_' + file_type + '.csv'))
                result_acce.to_csv(os.path.join(self.PATH,list_schedule[2] + '_' + 'acce' + '.csv'))
                result_gyro.to_csv(os.path.join(self.PATH, list_schedule[2] + '_' + 'gyro' + '.csv'))
                result_motion.to_csv(os.path.join(self.PATH, list_schedule[2] + '_' + 'motion' + '.csv'))
                result_magne.to_csv(os.path.join(self.PATH, list_schedule[2] + '_' + 'magne' + '.csv'))

Zh = ExtractMan()
# try_schedule = ['13:00,13:15,CS1','13:15,13:30,CS2','13:30,13:45,CS3','13:45,14:00,CS4','14:00,14:15,CS5','14:15,14:30,CS6','14:30,14:45,CS7','14:45,15:00,CS8']

# try_schedule = ['14:30,15:15,WS_OUT_DCL_IN','15:15,16:00,DCL_OUT_WS_IN','16:00,16:30,UDC']

try_schedule = ['0:00,0:45,WS_OUT_DCL_IN1','0:45,1:00,CS1','1:00,1:30,DE1','1:30,2:00,DE2','2:00,2:45,WS_OUT_DCL_IN2','2:45,3:00,CS2','3:00,3:30,DE3']

# try_schedule = ['9:00,9:15,CS1','9:15,9:30,CS2','9:30,9:45,CS3','9:45,10:00,CS4','10:00,10:15,CS5','10:15,10:30,CS6','10:30,10:45,CS7','10:45,11:00,CS8']

# try_schedule = ['7:30,7:45,CS1','7:45,8:00,CS2','8:00,8:15,CS3','8:15,8:30,CS4','8:30,8:45,CS5','8:45,9:00,CS6','9:00,9:15,CS7','9:15,9:30,CS8']

# try_schedule = ['9:30,10:10,UDC_WS_IN','10:10,10:45,DCL_IN','10:45,11:30,WS_OUT_DCL_IN']

# try_schedule = ['9:30,9:45,CS1','9:45,10:00,CS2','10:00,10:15,CS3','10:15,10:30,CS4','10:30,10:45,CS5','10:45,11:00,CS6','11:00,11:15,CS7','11:15,11:30,CS8','11:30,11:45,CS9','11:45,12:00,CS10','12:00,12:15,CS11','12:15,12:30,CS12','12:30,12:45,CS13']

Zh.data_extract('Gps.csv', try_schedule, Zh.SHUTTLE_NUM[5], '2017/9/22', 'gps')


