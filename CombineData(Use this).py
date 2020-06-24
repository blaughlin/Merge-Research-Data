import pandas as pd
import datetime
import matplotlib.pyplot as plt

def downsample_notocord(file_name):
	rat = pd.read_csv(file_name, skiprows=8)
	header = pd.read_csv(file_name, skiprows=2 , nrows=5, header = None)
	rat.columns = ['Time','Tb']
	time = header.iloc[1,0]
	offset = header.iloc[3,0]
	offset = int(offset)/1000000 # convert to seconds from microseconds
	time = pd.to_datetime(time)
	offset = datetime.timedelta(seconds = offset)
	CorrectTime = time + offset
	rat['Time'] = pd.to_datetime(rat.Time, origin=CorrectTime, unit='ms')
	rat.set_index('Time', inplace = True) 
	return(rat.resample('T').mean())

#offset time is in seconds relative to the notocord time
def create_respirometry_file(file_name, offset=120):
	resp = pd.read_csv(file_name, skiprows=2)
	respStartTime = pd.read_csv(file_name, header=0, encoding = 'unicode_escape')
	z = respStartTime.columns[0] + respStartTime.columns[1]
	z = datetime.datetime.strptime(z, ' %y/%m/%d %H:%M:%S')
	resp = resp.rename(columns=lambda x: x.strip())
	resp['Time'] = resp['Time']* 60 + offset
	resp['Time'] = pd.to_datetime(resp.Time, origin = z, unit ='s')
	resp.set_index('Time', inplace = True) 
	resp.rename(columns = {'Tb':'Tbrain'}, inplace = True) 
	return(resp)

def downsample_controller(file_name):
	controller = pd.read_csv(file_name, delimiter ='\t', skiprows = 1)
	dropCols = [1,3] # select columns to delete
	controller.drop(controller.columns[dropCols], axis = 1, inplace= True)
	controller.columns = ['Date', 'Time', 'CageTemp', 'AmbientTemp', 'SetPoint', 'PercentOut','PCB'] # rename columns
	pd.DateTime = controller['Date'] + ' ' + controller['Time'] # combine date and time
	cols = [0,1] #select date and time to delete
	controller.drop(controller.columns[cols], axis = 1, inplace= True) # reomve date and time
	controller = pd.concat([pd.DateTime, controller], axis =1) # combine DateTime with temperature 
	controller.columns = ['Time', 'CageTemp', 'AmbientTemp', 'SetPoint', 'PercentOut','PCB']
	controller['Time'] = pd.to_datetime(controller.Time) # convert to time format
	controller.set_index('Time', inplace = True) 
	controller = controller.resample('T').mean() # Take the mean value of every min 
	return(controller)

resp = create_respirometry_file('CombinedRespirometry.csv')
Tb = downsample_notocord('Rat19141_Tb.txt')
#Tb.index = Tb.index - pd.Timedelta(1, unit = 'h') #adust for daylight savings time 
controller = downsample_controller('Rat 19-141 Controller 112519.txt') 
#controller.index = controller.index - pd.Timedelta(1, unit='h') #adust for daylight savings time 

drugStartTime = datetime.datetime(2019, 11, 25, 13,29,00,00) # Time continous drug treatment started


df1 = Tb.join(controller, how='outer').join(resp, how ='outer')
df1['CHA'] = (df1.index - drugStartTime)
df1['days'] = df1['CHA'].dt.components.days
df1['hrs'] = df1['CHA'].dt.components.hours *60
df1['min'] = df1['CHA'].dt.components.minutes  + df1['hrs']
negativeTime = (df1.loc[df1['days'] == -1]).index
dayOne = (df1.loc[df1['days'] == 1]).index
df1.loc[negativeTime, 'min'] = df1.loc[negativeTime, 'min'] - 1440
df1.loc[dayOne, 'min'] = df1.loc[dayOne, 'min'] + 1440
df1.drop(df1.columns[[-2,-3,-4]], axis = 1, inplace= True) 

df1['Treatment'] = 'A'
df1['ID'] = '19-141'

df1.to_csv('Rat19-141.csv', index= 'Time', header = True)