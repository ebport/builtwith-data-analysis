__author__ = 'eporter'

import json
import os
import sys
import codecs
import sqlite3
import csv
import cStringIO
import urllib2
import datetime

# Preset variables
directory_string = "Files" #directory to save JSON files
base_url_string =  "http://api.builtwith.com/v8/api.json?KEY={0}&LOOKUP={1}"
credits_available_string = "x-api-credits-available"
credits_used_string = "x-api-credits-used"
url_file='input.txt' # text file containing urls
key="1e3fb00c-a1a3-419a-b2cd-50688a33cdc2"

# add in ability to use parameter to indicate if files are already there or need to be pulled
# separating download and processing and putting into one batch file is probably ideal
# need to propagate noneType error fix over here
def main():
  # download files and return list of names
  files=getfiles()
  print files

def getfiles():
  #Opens file as readonly, iterates through lines. Makes an api call for each line after the first and saves file
    with open(url_file) as f:
        #Iterate over lines containing urls, send request and save file
        lines = f.readlines()
        files=[]
        for line in lines:
            if line:
                #Get rid of newline chars
                line = line.strip()
                filename=os.path.join(directory_string,line+'.txt')
                if not os.path.isfile(filename):
                  send_request(line)
                files.append(filename)
    # sends back names of files
    return files
    
def send_request(url):
    #String for api call:
    bw_request_url = base_url_string.format(key, url)

    #http response
    response = urllib2.urlopen(bw_request_url)
    code = response.getcode()
    data = response.read()

    #Check to see if success - http responses in the 200s
    if code > 199 and code < 300:

        #Builtwith swallows some errors and returns the details in an Errors JSON tag
        #Right now any time there is anything in the Error tag nothing will be saved and the error will be printed
        data_json=json.loads(data)
        error_element = data_json["Errors"]

        #If errors exist print errors
        if(len(error_element) > 0):
            print "Error for "+ bw_request_url + " on " + url
            for e in error_element:
                print e

        #If no errors save JSON file
        else:
          #Creates file if it doesn't exist, overwrite if it does
          fileName=url+".txt"
          filePath = os.path.join(directory_string, fileName)
          with open(filePath, 'w') as outfile:
            json.dump(data, outfile)
    #Print error code
    else:
        print ("Error for " +url + ": " + url + "yielded " + str(code))


    #if no more credits end the program
    try:
        info = dict(response.info())
        credits_available = int(info[credits_available_string])
        credits_used = int(info[credits_used_string])
        if(credits_available - credits_used <= 0):
            print ("Out of credits")
            sys.exit()
    except KeyError:
        print ("API headers for credits may have changed. Check and update the script variables")

	
if __name__ == "__main__":
   main()
   
   
   
   
# Notes about Builtwith JSON
