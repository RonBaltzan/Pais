# -*- coding: utf-8 -*-
"""
Created on Sat Jul 22 15:18:31 2023

@author: Ron
"""
import requests
from bs4 import BeautifulSoup
import pandas as pd

#function to scrape data for given ballot number
#input: ballot no. (int)
#output dataframe of al the data
def Ballot_scrape(url):
	r = requests.get(url) #create connection
	#%
	#get parse tree
	soup = BeautifulSoup(r.text, 'html.parser')
	#%
	#get ballot info
	table1 = soup.find('div', class_ = 'archive_open_info w-clearfix') #ballot info
	#get ballot no.
	name = table1.find('h3') #finding type 
	name = name.text #change to text
	name = int(name.split(' ')[-1]) #get name
	#get ballot date
	date = table1.find('div') #finding type 
	date = date.text #change to text
	date = date.split('\n')[2] #get date
	#%
	#get ballot results
	table2 = soup.find('div', class_ = 'current_lottery_numgroup w-clearfix') #ballot info
	#get ballot results
	#finding extra no.
	extra = table2.find('div') #finding type 
	extra = extra.text #change to text
	extra = int(extra.split('\n')[-5]) #get extra no.
	#get ballot regular numbers
	tmp = table2.find_all('li') #finding all type
	num_list = [] #list for numbers 
	#fetching numbers
	for num in tmp:
		num_list.append(int(num.text.split('\n')[1])) #get extra no.
	#%
	#get ballot first prize
	table3 = soup.find('div', class_ = 'archive_open_dates current_info w-clearfix') #ballot info
	tmp = table3.find('div').text.split(' ')[7] #get raw first prize
	#change to int
	tmp = tmp.split(',')
	f_prz = int(tmp[0] +tmp[1] + tmp[2]) 
	#%
	#get ballot total prize amount divided
	table4 = soup.find_all('div', class_ = 'cat_archive_txt open',tabindex="0") #ballot info
	tmp = table4[-1].text.split(' ')[-2] #get raw first prize
	#change to int
	tmp = tmp.split(',')
	tot_prz = int(tmp[0] +tmp[1] + tmp[2]) 
	#%
	#get prize data
	#get all raw_data 
	table5 = soup.find('ol', id = 'regularLottoList') #ballot winners results
	#get relevant raw_data
	raw_data = []
	for i in table5.find_all("li"): #data is in <li> element
	 title = i.text
	 raw_data.append(title)
	#%
	#aranging data in df
	data = pd.DataFrame(columns = ['Prize No.', 'Guess type', 'Amount of winners', 'Prize sum [NIS]']) #Creating empty df for results
	#fetching data
	for i, res in enumerate(raw_data):
		res = res.split('\n')
		#change prize amount to int if greater than 1000
		if len(res[-3][:-2])>3:
			prz = res[-3][:-2].split(',')
			#7 figures case
			if len(prz)>2:
				prz = int(prz[0]+prz[1]+prz[2])
			else:
				prz = int(prz[0]+prz[1])
		else:
			prz = int(res[-3][:-2])
		#change amount of winners to int if greater than 1000
		if len(res[8])>3:
			win = res[8].split(',')
			win = int(win[0]+win[1])
		else:
			win = int(res[8])
		#adding data for table
		tmp = [i+1, res[3], win, prz] #getting all data for row
		data.loc[len(data)] = tmp #addding to dataframe
	#%
	#calculating sum of prizes
	data['Total prize sum [NIS]'] = [0]*len(data) #create column for prize
	data['Theoretical precentage [%]'] = [0]*len(data) #create column for calculated actual precentage
	data['Actual precentage [%]'] = [0]*len(data) #create column for Actual actual precentage
	#creating data
	for i in range(len(data)-1, -1,-1): #reverse loop in (to avoid error if no winners)
		#adding first & second prizes (known numbers)
		if i==0 or i==1 or i==7:
			data.loc[i, 'Theoretical precentage [%]'] = 'N\A'
			data.loc[i, 'Actual precentage [%]'] = 'N\A'
			#adding first prize (known numbers)
			if i==0:
				data.loc[i, 'Total prize sum [NIS]'] = f_prz
			#adding second prize (known number, not constant)
			elif i==1:
				#if there is a winner
				if data.loc[i,'Prize sum [NIS]']>0:
					data.loc[i,'Total prize sum [NIS]'] = data.loc[i,'Prize sum [NIS]']*data.loc[i,'Amount of winners']
				else:
					data.loc[i, 'Total prize sum [NIS]'] = 750000
			#adding eighth prize (known number)
			elif i==7:
				data.loc[i, 'Total prize sum [NIS]'] = 10
		#calculting un constant figures
		else:
			#if data exsist (there is winners)
			if data.loc[i,'Prize sum [NIS]']>0:
				data.loc[i,'Total prize sum [NIS]'] = data.loc[i,'Prize sum [NIS]']*data.loc[i,'Amount of winners']
			else:
				data.loc[i,'Total prize sum [NIS]'] = 0
			#calculting precentage from total prizes
			data.loc[i, 'Actual precentage [%]'] = (data.loc[i,'Total prize sum [NIS]']/tot_prz)*100
			#calculating theoretical precentage
			#third prize
			if i==2:
				data.loc[i, 'Theoretical precentage [%]'] = 1.8
			#fourth prize
			elif i==3:
				data.loc[i, 'Theoretical precentage [%]'] = 1.6
			#fifth prize
			elif i==4:
				data.loc[i, 'Theoretical precentage [%]'] = 2.14
			#sixth prize
			elif i==5:
				data.loc[i, 'Theoretical precentage [%]'] = 4.3
			#seventh prize
			elif i==6:
				data.loc[i, 'Theoretical precentage [%]'] = 7.0
	#%
	#gather all data
	gat_data = [name, date, f_prz, tot_prz, [num_list, extra], data]
	return gat_data
#%%
#scraping data from all ballot available
import numpy as np
from tqdm import tqdm

b_list = np.arange(1035, 3605,1) #range of ballots
b_url = r'https://www.pais.co.il/lotto/currentlotto.aspx?lotteryId='
#creating df for data
data_tot = pd.DataFrame(columns = ['Ballot no.', 'Date', 'First prize [NIS]', 'Total prize\n divided [NIS]', 'Winning numbers', 'Prizes data'])
#running on all ballot range
for n in tqdm(b_list):
	url_ad = b_url+str(n) #crearing current url address
	data_tot.loc[len(data_tot)] = Ballot_scrape(url_ad) #get data
#%%
from PIL import Image
myImage = Image.open(r"C:\Users\Livnat\Desktop\ron\temp\capture.jpg");
myImage.show()
#%%
data_tot.to_pickle('data.pkl')