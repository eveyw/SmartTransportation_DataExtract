import types
import pandas as pd
import time


class Driver:
    # SHUTTLE_NUM = ["787", "788", "528", "526"]
    # PHONE_ID = ["023d6dfce95b3997", "01ef64e4dec54025", "024a0c2d305eb3cc", "025391f6de955621"]
    # NUM_OF_SHUTTLE = 4
    # 762 024a09d94ab01756 025c411f85bad2ac
    SHUTTLE_NUM = ["763","747","762","748","787","788","528","526"]
    PHONE_ID = ["02597a5b9e75cf6c", "02596c2b9e85bf69", "025c411f85bad2ac","0249cc55455bc6ad",
                "023d6dfce95b3997","01ef64e4dec54025","024a0c2d305eb3cc","025391f6de955621"]
    NUM_OF_SHUTTLE = 8

    def __init__(self):
        print('Begin to get Driver information')

    def read_bus_assignments(self, driversheet):  # get Time , Bus and Details
        """
        :param driversheet: "DriverSheetJuly.csv"
        :return: list about Time, Bus and Details
        """
        # print my_matrix.head(3)         #return first three rows
        # print my_matrix.loc[1]          #return 1th row
        # print len(my_matrix)            #return rows of file: 204 (contain title line)
        # print len(my_matrix.columns)    #return columns of file: 5

        # the timestamp of data should from high to low
        # eg: 7/30 7/29 ... 7/6
        # we use list.reverse() in read_bus_details()

        my_matrix = pd.read_csv(driversheet, header=None)
        shuttle_list = []
        for i in range(len(my_matrix)):
            if my_matrix.loc[i][2] in Driver.SHUTTLE_NUM:
                shuttle_list.append(i)

        # shuttle assignments that we need
        temp_array = [([0] * 3) for i in range(len(shuttle_list))]
        index = 0
        for i in shuttle_list:
            temp_array[index][0] = my_matrix.loc[i][0]
            temp_array[index][1] = my_matrix.loc[i][2]
            temp_array[index][2] = my_matrix.loc[i][4]
            index += 1
        return temp_array

    def date_to_timestamp(self, date):  # convert Y/M/D H:M to x xxx xxx xxx . xxx
        time_array = time.strptime(date, "%Y/%m/%d %H:%M")
        timestamp = time.mktime(time_array)
        return timestamp

    def timestamp_to_date(self, timestamp):  # convert x xxx xxx xxx . xxx to Y/M/D H:M
        time_local = time.localtime(timestamp)
        dt = time.strftime("%Y/%-m/%-d %-H:%-M", time_local)  # %-m %-d if it's 07/06, will return 7/6
        return dt

    def read_bus_details(self, bus_array, bus_num, timestamp):
        """
        :param bus_array:get from read_bus_assignments()
        :param bus_num: 0 -> 787 1 -> 788 2 ->528 3 -> 526
        :param timestamp: x xxx xxx xxx . xxx (float)
        :return:shuttle details
        """
        bus_list = []
        for bus in bus_array:
            if bus[1] == Driver.SHUTTLE_NUM[bus_num]:
                bus_list.append([bus[0], bus[2]])
        bus_list.reverse()
        # for bus in bus_list:
        #     print bus

        # res is index of details we need
        res = -1
        low_bound = self.date_to_timestamp(bus_list[0][0])
        high_bound = self.date_to_timestamp(bus_list[len(bus_list) - 1][0])
        if timestamp < low_bound:  # if timestamp < lowest date, we think we can't get bus detail
            print("The timestamp is not in range of date, please check it again!")
            return -1
        elif timestamp > high_bound:
            res = len(bus_list) - 1

        if res == -1:
            low = 0
            high = len(bus_list) - 1

            while low <= high:
                mid = int(low + (high - low) / 2)
                if self.date_to_timestamp(bus_list[mid][0]) == timestamp:
                    res = mid
                    break
                elif self.date_to_timestamp(bus_list[mid][0]) < timestamp:
                    low = mid + 1
                else:
                    high = mid - 1
            if res == -1:
                if low != 0:
                    # if abs(date_to_timestamp(bus_list[low][0]) - timestamp) >= abs(
                    #                 date_to_timestamp(bus_list[low - 1][0]) - timestamp):
                    #     res = low - 1
                    # else:
                    #     res = low
                    res = low - 1
                else:
                    res = low
        print("the index is: " + str(res))

        # Sometimes same date will assignment a bus schedule twice, we should make sure choose the second one
        # Don't compare seconds of date, otherwise we may get the wrong details
        # If we input timestamp of 8:57:22am, we use return empty, no assignment, but just after 8s, it changed to Delta
        # eg: 2017/7/17  8:57:30AM 54 Details: Delta
        #     2017/7/17  8:57:20AM 54 Details:
        if res != -1 and res + 1 < len(bus_list):
            if self.date_to_timestamp(bus_list[res + 1][0]) == timestamp:
                res += 1
        # print (bus_list[res][1])

        # res = 11     # used to test return details
        if bus_list[res][1].find("Status: OUT") != -1:
            print("The shuttle's status is OUT!!!!!!!")
            return -1
        elif bus_list[res][1] == "Status: OK" or bus_list[res][1].endswith("Details:"):
            print("The shuttle has been assigned no route")
            return -1

        a = bus_list[res][1].split("Details: ")
        # print(a[1])
        # return a[1]
        return a[1].lower()     #ignore uppercase or lowercase between schedule

    def convert_ap_pm(self, date, time):
        """
        :param date: eg: 2017/7/7
        :param time: eg: 1pm
        :return:     eg: 13:00
        """
        temp = date + ' ' + time
        print(temp)
        res = pd.to_datetime(temp).strftime('%-H:%-M')
        return res

    def time_num_minute(self, date, time):
        """
        :param date: 2017/7/7
        :param time: 1pm
        :return:     13 * 60 + 0 = 780
        """
        t1 = self.convert_ap_pm(date, time)
        rt1 = t1.split(':')
        res = int(rt1[0]) * 60 + int(rt1[1])
        return res

    # get driver info: name
    def get_driver_info(self, schedule, detail, timestamp):
        """
        :param schedule:    "Schedule0705-0709(comma).csv"
        :param detail:      get from read_bus_details() method
        :param timestamp:   x xxx xxx xxx . xxx (float)
        :return:            driver schedule info
        """
        my_matrix = pd.read_csv(schedule, header=None)
        date = self.timestamp_to_date(timestamp)
        timestamp_time = date.split(' ')  # eg: ['2017-07-07', '06:34']

        df = pd.DataFrame(my_matrix.iloc[1:len(my_matrix), :])
        df.columns = my_matrix.loc[0]

        if timestamp_time[0] in df.columns:
            current_column = df[timestamp_time[0]]
            detail_list = []
            for tuple in current_column:
                # if type(tuple) is types.StringType:  # NaN is float type, avoid it
                if isinstance(tuple, types.StringType):
                    temp = tuple.split(',')
                    if temp[0].lower().find(detail) >= 0:       #temp[0].find(detail) >= 0
                        detail_list.append(temp)
            print(detail_list)
            if not detail_list:
                print('No information in schedule')
                return -1
            flag = 0
            for d in detail_list:
                s_t = d[1].split('-')
                l = self.time_num_minute(timestamp_time[0], s_t[0])
                h = self.time_num_minute(timestamp_time[0], s_t[1])
                cur = self.time_num_minute(timestamp_time[0], timestamp_time[1])
                if l <= cur < h:
                    # print(d)
                    flag = 1
                    break
                    # print '----'
            if flag == 0:
                print('No drive information')  # at this timestamp, no drive works
                return -1
            else:
                return d
        else:
            print('timestamp is out of range!!!')
            return -1


# d = Driver()
# # print(d.Daniel AsanteMava Jones)
# print(d.date_to_timestamp("2017/8/24 6:32"))
# print(d.date_to_timestamp("2017/8/23 07:10"))
# print(d.date_to_timestamp("2017/8/23 07:12"))
# print(d.date_to_timestamp("2017/8/23 07:15"))
# return_list = d.read_bus_assignments("ShuttleVirtualRoute.csv")
# print return_list
# return_detail = d.read_bus_details(return_list, 7, 1503570720.0)
# print(return_detail)
# return_detail = d.read_bus_details(return_list, 3, 1503486600.0)
# print(return_detail)
# return_detail = d.read_bus_details(return_list, 3, 1503486720.0)
# print(return_detail)
# return_detail = d.read_bus_details(return_list, 3, 1503486900.0)
# print(return_detail)
# if type(return_detail) is not int:
#     print('shuttle route is: ' + return_detail)
#
# result = d.get_driver_info("Schedule0705-0709(comma).csv", return_detail, 1499350500.0)
# if type(result) is not int:
#     print result
