import os, requests, argparse, json, re
from pprint import pprint

parser = argparse.ArgumentParser()
parser.add_argument('-debug', action='store_true')
args = parser.parse_args()

# Assumes the directory is named with the correct show name

showname = os.getcwd().split('/')[-1]

# Scrape show metadata from tvdb

url='https://api.thetvdb.com/'
apikey = 'F386OP1GPBNFMYMN'

showData = list()

def getToken():
	path = 'login'
	r = requests.post(url+path, json={'apikey': apikey})
	return json.loads(r.content)['token']

def getShowID(token):
	path = 'search/series'
	r = requests.get(url+path, params={'name':showname}, headers={'Authorization': f'Bearer {token}'})
	return json.loads(r.content)['data'][0]['id']

# Get the deets and store it into a dictonary element and append it into a list for traversal later

def storeListLocally(sno, epno, name):
	element = {'Season':sno, 'Episode':epno, 'Name':name}
	# Omit Specials
	if(sno!=0):
		showData.append(element)

def getEpisodeList(token, showID):
	path = f'series/{showID}/episodes'

	# Load a single page of response
	
	r = requests.get(url+path, params={'page':1}, headers={'Authorization': f'Bearer {token}'})
	jsonr = json.loads(r.content)
	epdata = jsonr['data']
	if args.debug:
		print('Data obtained from api is : ')
	for episode in epdata:
		if args.debug:
			print('S' + str(episode['airedSeason']) + 'E' + str(episode['airedEpisodeNumber']), episode['episodeName'])
		storeListLocally(episode['airedSeason'], episode['airedEpisodeNumber'], episode['episodeName'])
	
	# Keep reading until there are no more pages to load
	
	while(jsonr['links']['next']!=None):
		r = requests.get(url+path, params={'page':jsonr['links']['next']}, headers={'Authorization': f'Bearer {token}'})
		jsonr = json.loads(r.content)
		epdata = jsonr['data']
		for episode in epdata:
			if args.debug:
				print('S' + str(episode['airedSeason']) + 'E' + str(episode['airedEpisodeNumber']), episode['episodeName'])
			storeListLocally(episode['airedSeason'], episode['airedEpisodeNumber'], episode['episodeName'])

def episodenumber(filename):
	match = re.search(r'(?ix)(?:e|x|episode|^)\s*(\d{2})', filename)
	if match:
		return match.group(1)

def search(sno, eno):
	return next((item for item in showData if item["Episode"] == eno and item['Season'] == sno), None)

def renameFiles():
	for root, dirs, files in os.walk('.', topdown=True):
		files = [f for f in files if not f[0] == '.' ]
		dirs[:] = [d for d in dirs if not d[0] == '.']
		if(root!= '.'):
			# This is true for all sub-directories
			# root has the parent directory for the file.
			# f in files iterates over the files in the directory
			seasonnumber = re.search(r'([0-9]+)', root)
			snum = seasonnumber.group(0)
			for f in files:
				enum = episodenumber(f)
				try:
					newepisodename = search(int(snum), int(enum))['Name']
					# print(snum, enum, newname['Name'])
					newfilename = f'Episode {int(enum)} - {newepisodename}.' + f.split('.')[-1]
					newfilename = newfilename.replace('/', ':')
					if args.debug:
						print('Old : ' + f, '\nNew : ' + newfilename)
						print()

					# File is renamed here
					# print(os.path.join(root,f), os.path.join(root, newfilename))
					os.rename(os.path.join(root, f), os.path.join(root, newfilename))
				except:
					# This is a non-parsable filename
					if args.debug:
						print('Cannot parse this file : ' + f)

if __name__ == '__main__':
	token = getToken()
	showID = getShowID(token)
	getEpisodeList(token, showID)
	if args.debug:
		print("Stored data is : ")
		pprint(showData)
	renameFiles()
