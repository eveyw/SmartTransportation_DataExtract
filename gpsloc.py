from math import radians, cos, sin, asin, sqrt, fabs
import pandas as pd

def hav(theta):
    s = sin(theta / 2)
    return s * s

def get_distance_hav(lat0, lng0, lat1, lng1):
    r = 6371
    lat0 = radians(lat0)
    lat1 = radians(lat1)
    lng0 = radians(lng0)
    lng1 = radians(lng1)

    dlng = fabs(lng0 - lng1)
    dlat = fabs(lat0 - lat1)
    h = hav(dlat) + cos(lat0) * cos(lat1) * hav(dlng)
    distance = 2 * r * asin(sqrt(h)) * 1000
    return distance  # return meter


f1 = pd.read_csv('/Users/eveyw/PycharmProjects/SmartParkGPS/Gpswen.csv', names=['lng','lat'])
f2 = pd.read_csv('/Users/eveyw/PycharmProjects/SmartParkGPS/Gpsfate.csv', names=['1','2','3','4','5','lng','lat'])

for i in range(len(f1)):
    print('--------')
    print (i)
    for j in range(len(f2)):
        distance = get_distance_hav(f1.loc[i,'lat'], f1.loc[i,'lng'], f2.loc[j,'lat'], f2.loc[j,'lng'])
        if distance <= 10:
            print (distance)
            print (f2.loc[j])
    print ('--------')
