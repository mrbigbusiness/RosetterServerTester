#!/usr/bin/python3

import json
import requests
import random
import time
import argparse
import textwrap
from datetime import datetime
random.seed()

parser = argparse.ArgumentParser(description='Test record similarity API',formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument('-e','--explain', required=False, action='store_true', default=False, \
                    help='Include explanation data (very verbose!)')
parser.add_argument('-s','--start', required=False, type=int, default=-1, \
                    help='Record number to start with, to repeat data queries.')
parser.add_argument('-c','--recordcount', required=True, type=int, default=1, \
                    help='How many records to submit and compare at once')
parser.add_argument('-f','--fields',required=True,nargs='*', \
help=textwrap.dedent('''\
Which data field(s) to compare.  Otions include:
	name, company, address, dob
	include mulitples by using "-f name company dob" for example.'''))
	
parser.add_argument('-n','--namemangle', choices=['none','drop-middle','init-first','init-firstmiddle','typo','random'], \
                    default='none', required=False, help=textwrap.dedent('''\
How to mangle the name.  Choices are:
	none - self explanatory, and the default
	drop-middle - Use only first and last name
	init-first - Use firstname inital and lastname
	init-firstmiddle - Use initials for first and middle plus full lastname
	typo = Remove a random letter from the lastname
	random - a random choice of the others'''))

parser.add_argument('-a','--addressmangle', choices=['none','drop-street','drop-city','null','typo','random'], \
                    default='none', required=False, help=textwrap.dedent('''\
How to mangle the address.  Choices are:
	none - self explanatory, and the default
	drop-street - Remove the street line from the address
	drop-city - Remove city name from the address
	null - return nothing - a blank address
	typo = Remove a random letter from the city name
	random - a random choice of the others'''))
	
parser.add_argument('-x','--companymangle', choices=['none','null','typo'], \
                    default='none', required=False, help=textwrap.dedent('''\
How to mangle the company name.  Choices are:
	none - self explanatory, and the default
	null - return nothing - a blank company name
	typo - Remove a random letter from the city name'''))

parser.add_argument('-d','--DOBmangle', choices=['none','usa','eu','year','human','wrong'], \
                    default='none', required=False, help=textwrap.dedent('''\
How to mangle the date of birth.  Choices are:
	none - self explanatory, and the default
	usa - month/day/year format like real americans
	eu - day/month/year like all fancy
	year - return only the year
	human - format like "Jan 17, 2012"
	wrong = just some other random date, same YYYY-MM-DD format'''))	
	
args = parser.parse_args()
random.seed()

# Opening JSON file
file = open('addressdata.json')
 
# returns JSON object as 
# a dictionary
data = json.load(file)
file.close()
 
# Iterating through the json
# list
#for i in data:
#    print(i)
 
url = 'http://localhost:8181/rest/v1/record-similarity'
headers = {'Content-Type':'application/json','Accept':'application/json','Cache-Control':'no-cache'}

### For reference, this is the given data structure/json
  # {
    # "eyeColor": "blue",
    # "firstname": "Hodges",
    # "middlename": "Susan",
    # "lastname": "Chen",
    # "gender": "female",
    # "company": "GLOBOIL",
    # "street": "975 Sandford Street",
    # "city": "Disautel",
    # "state": "South Dakota",
    # "zip": 93474,
    # "birthdate": "1977-06-08"
  # },

def mangleDOB(cakeday):
	dt = datetime.strptime(cakeday, '%Y-%m-%d')
	# foo = string.split('=')
	# month = foo[1]
	# day = foo[2]
	# year = foo[0]   ####### yeah, there is a better way to do it, but I refuse to google it right now
	choice = args.DOBmangle
	if choice == 'wrong':
		return str(random.randint(1924,2020))+'-'+str(random.randint(0,12)).zfill(2)+'-'+str(random.randint(1,28)).zfill(2)
	elif choice == 'usa':
		return datetime.strftime(dt,'%m/%d/%Y')
	elif choice == 'eu':
		return datetime.strftime(dt,'%d/%m/%Y')
	elif choice == 'year':
		return datetime.strftime(dt,'%Y')
	elif choice == 'human':
		return datetime.strftime(dt,'%b %d %Y')
	else:
		return cakeday
	
def mangleName(givenName):
	choices=['none','drop-middle','init-first','init-firstmiddle','typo']
	if args.namemangle == 'random':
		choice = random.choice(choices)
	else:		
		choice = args.namemangle
	print (choice)
	if choice == 'drop-middle':  		## drop the middle name
		return givenName['firstname']+' '+givenName['lastname']
	elif choice == 'init-first':  		## only give first initial and lastname
		return givenName['firstname'][0]+' '+givenName['lastname']
	elif choice == 'init-firstmiddle':		## first and middle initials only, plus lastname
		return givenName['firstname'][0]+' '+givenName['middlename'][0]+' '+givenName['lastname']
	elif choice == 'typo': 		## remove a random letter from the last name
		lastname = givenName['lastname']
		remove = random.randint(1,len(lastname))
		lastname = lastname[0:remove]+lastname[remove+1:]
		return givenName['firstname']+' '+givenName['middlename']+' '+lastname
	else:					## do nothing, return the name unmolested
		return givenName['firstname']+' '+givenName['middlename']+' '+givenName['lastname']

def mangleCompany(givenName):
	choice = args.companymangle
	print (choice)
	if choice == 'null':  		## return a blank entry
		return ''
	elif choice == 'typo': 		## remove a random letter from the last name
		remove = random.randint(1,len(givenName))
		companyname = givenName[0:remove]+givenName[remove+1:]
		return companyname
	else:					## do nothing, return the name unmolested
		return givenName

def mangleAddress(address):
	choices=['none','drop-street','drop-city','null','typo']
	if args.addressmangle == 'random':
		choice = random.choice(choices)
	else:		
		choice = args.addressmangle
	if choice == 'drop-street':  		## drop the street
		return address['city']+', '+address['state']+', '+address['zip']
	elif choice == 'drop-city':  		## drop the city
		return address['street']+', '+address['state']+', '+address['zip']
	elif choice == 'null':		## return null
		return ''
	elif choice == 'typo': 		## remove a random letter from the city
		city = address['city']
		remove = random.randint(1,len(city))
		city = city[0:remove]+city[remove+1:]
		return address['street']+', '+city+', '+address['state']+', '+address['zip']
	else:					## do nothing, return the address unmolested
		return address['street']+', '+address['city']+', '+address['state']+', '+address['zip']


#explainTF = args.explain
payload = {"fields": {"fullname": {"type": "rni_name", "weight": 0.5}, \
		"address": {"type": "rni_address", "weight": 0.5}, \
		"dob": {"type": "rni_date", "weight": 0.4}, \
		"company": {'type':'rni_name', 'weight':0.1}},\
		"properties": {"threshold": 0.7, "includeExplainInfo": args.explain}, "records": {}}

left = []
right = []
counter = 0
itemCount = len(data)
if args.start < 0:
	itemNumber = random.randint(0,itemCount-2)
else:
	itemNumber = args.start
itemStart = itemNumber
while counter < args.recordcount:
	item = data[itemNumber]
	itemNumber = itemNumber+1
	if itemNumber == itemCount:
		itemNumber = 0
	counter=counter+1
	if (counter > args.recordcount):  ### only pull the first N records
		break
	fullname1 = item['firstname']+' '+item['middlename']+' '+item['lastname']
	address1 = item['street']+', '+item['city']+', '+item['state']+', '+str(item['zip'])
	company1 = item['company']
	birthdate1 = item['birthdate']
	#print(fullname1, address1)	
	left.append({'fullname':{'text':fullname1,'entityType':'PERSON','language':'eng'}, \
				 'address':address1, 'company':{'text':company1, 'entityType':'ORGANIZATION'},\
				 'dob':{'date':birthdate1}})
	#left.append(thisData)
	
	thisData = {}
	if 'name' in args.fields:
		fullname2 = mangleName({'firstname':item['firstname'],'middlename':item['middlename'],'lastname':item['lastname']})
		thisData['fullname'] = {'text':fullname2,'entityType':'PERSON','language':'eng'}
	if 'company' in args.fields:
		company2 = mangleCompany(item['company'])
		thisData['company'] = {'text':company2,'entityType':'ORGANIZATION'}
	if 'address' in args.fields:	
		address2 = mangleAddress({'street':item['street'],'city':item['city'],'state':item['state'],'zip':str(item['zip'])})
		thisData['address'] = address2
	if 'dob' in args.fields:
		birthdate2 = mangleDOB(item['birthdate'])
		thisData['dob'] = {'date':birthdate2}	
	
	# right.append({'fullname':{'text':fullname2,'entityType':'PERSON','language':'eng'}, \
				# 'address':address2, 'company':{'text':company2, 'entityType':'ORGANIZATION'},\
				# 'dob':{'date':birthdate2}})
	right.append(thisData)				
		

payload['records'] = {'left':left,'right':right}
print(json.dumps(payload, indent=2))
print()
print('Performing Query')
print()
startTime=time.time()
response = requests.post(url, headers=headers, json=payload)
elapsed = time.time()-startTime
print(json.dumps(json.loads(response.text), indent=2))
print('This query took '+str(elapsed)+' seconds.')
print('Started at record '+str(itemStart))
	else:					## do nothing, return the name unmolested
		return givenName['firstname']+' '+givenName['middlename']+' '+givenName['lastname']

def mangleCompany(givenName):
	choice = args.companymangle
	print (choice)
	if choice == 'null':  		## return a blank entry
		return ''
	elif choice == 'typo': 		## remove a random letter from the last name
		remove = random.randint(1,len(givenName))
		companyname = givenName[0:remove]+givenName[remove+1:]
		return companyname
	else:					## do nothing, return the name unmolested
		return givenName

def mangleAddress(address):
	choices=['none','drop-street','drop-city','null','typo']
	if args.addressmangle == 'random':
		choice = random.choice(choices)
	else:		
		choice = args.addressmangle
	if choice == 'drop-street':  		## drop the street
		return address['city']+', '+address['state']+', '+address['zip']
	elif choice == 'drop-city':  		## drop the city
		return address['street']+', '+address['state']+', '+address['zip']
	elif choice == 'null':		## return null
		return ''
	elif choice == 'typo': 		## remove a random letter from the city
		city = address['city']
		remove = random.randint(1,len(city))
		city = city[0:remove]+city[remove+1:]
		return address['street']+', '+city+', '+address['state']+', '+address['zip']
	else:					## do nothing, return the address unmolested
		return address['street']+', '+address['city']+', '+address['state']+', '+address['zip']


#explainTF = args.explain
payload = {"fields": {"fullname": {"type": "rni_name", "weight": 0.5}, \
		"address": {"type": "rni_address", "weight": 0.5}, \
		"dob": {"type": "rni_date", "weight": 0.4}, \
		"company": {'type':'rni_name', 'weight':0.1}},\
		"properties": {"threshold": 0.7, "includeExplainInfo": args.explain}, "records": {}}

left = []
right = []
counter = 0
itemCount = len(data)
itemNumber = random.randint(0,itemCount-2)
while counter < args.recordcount:
	itemNumber = itemNumber+1
	if itemNumber == itemCount:
		itemNumber = 0
	item = data[itemNumber]
	counter=counter+1
	if (counter > args.recordcount):  ### only pull the first N records
		break
	fullname1 = item['firstname']+' '+item['middlename']+' '+item['lastname']
	address1 = item['street']+', '+item['city']+', '+item['state']+', '+str(item['zip'])
	company1 = item['company']
	birthdate1 = item['birthdate']
	#print(fullname1, address1)	
	left.append({'fullname':{'text':fullname1,'entityType':'PERSON','language':'eng'}, \
				 'address':address1, 'company':{'text':company1, 'entityType':'ORGANIZATION'},\
				 'dob':{'date':birthdate1}})
	#left.append(thisData)
	
	thisData = {}
	if 'name' in args.fields:
		fullname2 = mangleName({'firstname':item['firstname'],'middlename':item['middlename'],'lastname':item['lastname']})
		thisData['fullname'] = {'text':fullname2,'entityType':'PERSON','language':'eng'}
	if 'company' in args.fields:
		company2 = mangleCompany(item['company'])
		thisData['company'] = {'text':company2,'entityType':'ORGANIZATION'}
	if 'address' in args.fields:	
		address2 = mangleAddress({'street':item['street'],'city':item['city'],'state':item['state'],'zip':str(item['zip'])})
		thisData['address'] = address2
	if 'dob' in args.fields:
		birthdate2 = mangleDOB(item['birthdate'])
		thisData['dob'] = {'date':birthdate2}	
	
	# right.append({'fullname':{'text':fullname2,'entityType':'PERSON','language':'eng'}, \
				# 'address':address2, 'company':{'text':company2, 'entityType':'ORGANIZATION'},\
				# 'dob':{'date':birthdate2}})
	right.append(thisData)				
		

payload['records'] = {'left':left,'right':right}
print(json.dumps(payload, indent=2))
print()
print('Performing Query')
print()
startTime=time.time()
response = requests.post(url, headers=headers, json=payload)
elapsed = time.time()-startTime
print(json.dumps(json.loads(response.text), indent=2))
print('This query took '+str(elapsed)+' seconds.')	
