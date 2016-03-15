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
base_url_string =  "http://api.builtwith.com/v7/api.json?KEY={0}&LOOKUP={1}"
credits_available_string = "x-api-credits-available"
credits_used_string = "x-api-credits-used"
url_file='input.txt' # text file containing urls
key="1e3fb00c-a1a3-419a-b2cd-50688a33cdc2"

# add in ability to use parameter to indicate if files are already there or need to be pulled
# separating download and processing and putting into one batch file is probably ideal
def main():
  # download files and return list of names
  files=getfiles()
  print files
  # Create database
  db=sqlite3.connect(':memory:')
  create_table(db)
  # Loop through file list
  for f in files: 
    # Load JSON data
    file=open(f,'r')
    data=file.read()
    dj=json.loads(json.loads(data))
    # check for errors
    # Pull out relevant information
    companyName=dj["Results"][0]["Meta"]["CompanyName"]
    paths=dj["Results"][0]["Result"]["Paths"]
    #check company name value
    if companyName is None:
      companyName=''
    #initialize array
    rows=[]
    # loop through paths creating rows for technologies
    for p in paths:
      url=p["Url"]
      domain=p["Domain"]
      subdomain=p["SubDomain"]
      techs=p["Technologies"]
      for t in techs:
        if int(t["FirstDetected"] > 0):
          first_detected=datetime.datetime.fromtimestamp(t["FirstDetected"]/1000.0).isoformat()
        else:
          first_detected=None
        if int(t["LastDetected"] > 0):
          last_detected=datetime.datetime.fromtimestamp(t["LastDetected"]/1000.0).isoformat()
        else:
          last_detected=None
        rows.append((companyName,domain,subdomain,t["Name"],t["Description"],t["Tag"],first_detected,last_detected))
    # insert data into table
    # deal with blanks for bank name
    insert_techs(db,rows)
  # get output
  output=get_output(db)
  # write output to csv
  write_csv(output, 'output.csv')

  # historic information Experimental code
  historic = get_historic(db)
  write_csv(historic, 'historic.csv')
  
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
                files.append(filename)
    # sends back names of files
    return files

def create_table(db):
  cursor=db.cursor()
  cursor.execute('''
    CREATE TABLE techs (id INTEGER Primary Key, company TEXT, domain TEXT, subdomain TEXT,
    name TEXT, description text, tag TEXT, first_detected TEXT, last_detected TEXT)
  ''')
  db.commit()

def insert_techs(db,rows):
  cursor=db.cursor()
  cursor.executemany('''INSERT INTO techs(company,domain,subdomain,name,description, tag,first_detected,last_detected) VALUES(?,?,?,?,?,?,?,?)''',rows)
  cursor.execute('''Update techs Set subdomain='home' Where subdomain="" ''')
  db.commit()
  
def get_output(db):
  cursor=db.cursor()
  cursor.execute('''Select domain, subdomain, name from techs
  where tag in ("analytics","ads","widgets","cms")
  and substr(last_detected,1,7) in (substr(date('now','start of month'),1,7),substr(date('now','start of month','-1 day'),1,7))''') #
  dbrows=cursor.fetchall()
  #print dbrows
  return dbrows

def get_historic(db):
  cursor=db.cursor()
  cursor.execute('''Select domain, subdomain, name, first_detected, last_detected from techs''')
  dbrows=cursor.fetchall()
  return dbrows

def write_csv(output, filename):
  with open(filename, 'wb') as f:
    wr = UnicodeWriter(f)
    wr.writerows(output)

class UnicodeWriter:
    """
    A CSV writer which will write rows to CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        # Redirect output to a queue
        self.queue = cStringIO.StringIO()
        self.writer = csv.writer(self.queue, dialect=dialect, **kwds)
        self.stream = f
        self.encoder = codecs.getincrementalencoder(encoding)()

    def writerow(self, row):
        self.writer.writerow([s.encode("utf-8") for s in row])
        # Fetch UTF-8 output from the queue ...
        data = self.queue.getvalue()
        data = data.decode("utf-8")
        # ... and reencode it into the target encoding
        data = self.encoder.encode(data)
        # write to the target stream
        self.stream.write(data)
        # empty queue
        self.queue.truncate(0)

    def writerows(self, rows):
      for row in rows:
        print row
        self.writerow(row)
  
if __name__ == "__main__":
   main()
   
   
   
   
# Notes about Builtwith JSON
