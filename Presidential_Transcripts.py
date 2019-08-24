#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Jul 20 11:32:50 2019

@author: tefirman
"""

import wget
import os
import pandas as pd
import html2text
h = html2text.HTML2Text()
h.ignore_links = True

presidents = ['George Washington','John Adams','Thomas Jefferson','James Madison',\
'James Monroe','John Quincy Adams','Andrew Jackson','Martin van Buren','William Henry Harrison',\
'John Tyler','James K. Polk','Zachary Taylor','Millard Fillmore','Franklin Pierce',\
'James Buchanan','Abraham Lincoln','Andrew Johnson','Ulysses S. Grant',\
'Rutherford B. Hayes','James A. Garfield','Grover Cleveland','Benjamin Harrison',\
'William McKinley','Theodore Roosevelt','William Howard Taft','Woodrow Wilson',\
'Chester A. Arthur','Warren G. Harding','Calvin Coolidge','Herbert Hoover',\
'Franklin D. Roosevelt','Harry S. Truman','Dwight D. Eisenhower','John F. Kennedy',\
'Lyndon B. Johnson','Richard Nixon','Gerald R. Ford','Jimmy Carter','Ronald Reagan',\
'George Bush','William J. Clinton','George W. Bush','Barack Obama','Donald J. Trump']

docType = 'spoken-addresses-and-remarks'
numLists = 89
#docType = 'written-statements'
#numLists = 267
#docType = 'miscellaneous-remarks'
#numLists = 374
#docType = 'miscellaneous-written'
#numLists = 13
#docType = 'memoranda'
#numLists = 32
#docType = 'letters'
#numLists = 74
#docType = 'vetoes'
#numLists = 5
#docType = 'written-messages'
#numLists = 187
#docType = 'written-presidential-orders'
#numLists = 235
#docType = 'interviews'       # Might not want to include these... Interviewer's vocab too...
#numLists = 16                # Might not want to include these... Interviewer's vocab too...
#docType = 'news-conferences' # Might not want to include these... Interviewer's vocab too...
#numLists = 36                # Might not want to include these... Interviewer's vocab too...

if os.path.exists('Presidential_Transcripts_Indices.csv'):
    indices = pd.read_csv('Presidential_Transcripts_Indices.csv')
else:
    indices = pd.DataFrame(columns=['President','Doc_Type','Doc_Index','Date','Title'])

if not os.path.exists('Presidential_Transcripts/' + docType):
    os.mkdir('Presidential_Transcripts/' + docType)

weirdEntries = []
for listInd in range(159,numLists):
    print('List #' + str(listInd + 1))
    if listInd == 0:
        wget.download('https://www.presidency.ucsb.edu/documents/app-categories/' + \
        'presidential/' + docType + '?items_per_page=60','TempList.html')
    else:
        wget.download('https://www.presidency.ucsb.edu/documents/app-categories/' + \
        'presidential/' + docType + '?items_per_page=60&page=' + str(listInd),'TempList.html')
    tempData = open('TempList.html','r')
    tempList = tempData.read().split('<div  about="')[1:]
    tempData.close()
    del tempData
    filenames = [val.split('" typeof="')[0] for val in tempList]
    dates = [val.split('<span class="date-display-single"')[1].split('>')[1].split('<')[0] for val in tempList]
    titles = [h.handle(val.split('<div class="field-title">\n    <p><a href')[1].split('>')[1].split('<')[0]).replace('\n',' ') for val in tempList]
    speakers = ['' if '<div class="label-above">Related</div><p><a href="' not in val \
    else val.split('<div class="label-above">Related</div><p><a href="')[1].split('>')[1].split('<')[0] for val in tempList]
    os.remove('TempList.html')
    
    for docInd in range(len(filenames)):
        if speakers[docInd] not in presidents:
            weirdEntries.append(speakers[docInd])
            continue
        wget.download('https://www.presidency.ucsb.edu/' + filenames[docInd],'TempDoc.html')
        
        tempData = open('TempDoc.html','r')
        tempContent = tempData.read().split('<div class="field-docs-content">')[1].split('</div')[0]
        tempData.close()
        del tempData
        tempContent = tempContent.replace(' (Applause.)','').replace(' [<i>applause</i>]','').replace(' [<i>booing</i>]','')
        
        if indices.loc[(indices.President == speakers[docInd]) & (indices.Doc_Type == docType) & \
        (indices.Date == dates[docInd]) & (indices.Title == titles[docInd])].shape[0] == 0:
            if speakers[docInd] not in indices.President.tolist():
                indices = indices.append({'President':speakers[docInd],'Doc_Type':docType,\
                'Doc_Index':0,'Date':dates[docInd],'Title':titles[docInd]},ignore_index=True)
            else:
                indices = indices.append({'President':speakers[docInd],'Doc_Type':docType,\
                'Doc_Index':indices.loc[indices.President == speakers[docInd],'Doc_Index'].max() + 1,\
                'Date':dates[docInd],'Title':titles[docInd]},ignore_index=True)
            
            tempData = open('Presidential_Transcripts/' + docType + '/' + \
            indices.loc[indices.shape[0] - 1,'President'].replace(' ','_').replace('.','') + \
            '_' + str(indices.loc[indices.shape[0] - 1,'Doc_Index']) + '.txt','w')
            tempData.write(h.handle(tempContent).replace('\n',' '))
            tempData.close()
            del tempData
        
        os.remove('TempDoc.html')
    del docInd
    
    indices.to_csv('Presidential_Transcripts_Indices.csv',index=False)
    
del listInd




