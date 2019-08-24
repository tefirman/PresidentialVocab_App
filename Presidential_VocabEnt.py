#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jul 21 19:58:56 2019

@author: tefirman
"""

import pandas as pd
import numpy as np
import re
import pyphen
import datetime
import os
import time

dic = pyphen.Pyphen(lang='en')
""" http://www.gutenberg.org/files/3204/ """
syllables = pd.read_csv('mhyph.txt',names=['Hyphenated'],encoding='latin8').fillna(' ')
syllables = syllables.loc[~syllables.Hyphenated.str.contains(' ')]
syllables['Word'] = syllables['Hyphenated'].str.replace('ċ','')
syllables['Hyphenated'] = syllables['Hyphenated'].str.split('ċ')
syllables['Syllables'] = syllables.Hyphenated.apply(lambda x: len(x))
syllables = syllables.drop_duplicates(subset=['Word'])
funcWords = "a about  above  after  after  again  against  ago  ahead  all  almost " + \
" almost  along  already  also  although  always  am among  an and  any  are " + \
" aren't  around  as at  away backward  backwards   be  because  before  behind " + \
" below  beneath  beside  between  both  but  by can  cannot  can't  cause  'cos " + \
" could  couldn't 'd   despite  did  didn't  do  does  doesn't  don't  down " + \
" during each  either  even  ever  every  except for forward  from had hadn't " + \
" has  hasn't  have  haven't  he  her  here  hers  herself  him  himself  his " + \
" how  however  i if  in  inside  inspite  instead  into  is   isn't  it  its " + \
" itself just 'll   least  less  like 'm  many  may  mayn't  me  might  mightn't " + \
" mine  more  most  much  must  mustn't  my  myself near  need  needn't  needs " + \
" neither  never  no  none  nor  not  now of  off  often  on  once  only  onto " + \
" or  ought  oughtn't  our  ours  ourselves  out  outside  over past  perhaps " + \
"quite 're  rather 's  seldom  several  shall  shan't  she  should  shouldn't " + \
" since  so  some  sometimes  soon  than  that  the  their  theirs  them  " + \
"themselves  then  there  therefore  these  they  this  those  though  through " + \
" thus  till  to  together  too  towards  under  unless  until  up  upon  us " + \
" used  usedn't usen't  usually 've very was   wasn't  we  well  were  weren't " + \
" what  when  where  whether  which  while  who  whom  whose  why  will  with " + \
" without  won't  would  wouldn't yet  you  your  yours  yourself  yourselves"
funcWords = re.sub('[^\w\s]','',funcWords)
funcWords = funcWords.split()

indices = pd.read_csv('Presidential_Transcripts_Indices.csv')
byPresident = indices.groupby('President').size().to_frame('Total_Count').reset_index()
indices = indices.loc[indices.President.isin(byPresident.loc[byPresident.Total_Count > 1000,'President'].tolist())].reset_index(drop=True)

indices['Actual_Year'] = indices.Date.str.split(' ').str[-1].astype(int)
presidentYear = indices[['President','Actual_Year']].drop_duplicates().groupby('President').Actual_Year.mean().astype(int).reset_index()
presidentYear['Ngram_Year'] = presidentYear.Actual_Year.apply(lambda x: min(x,2000))

""" Analyze vocabularies in their entireties, not speech by speech... """

filesPerList = 1000
os.mkdir('Presidential_Transcripts/Vocab_Lists')
vocabs = pd.DataFrame(columns=['President','Word','Count'])
for ind in range(indices.shape[0]):
    if ind%filesPerList == 0:
        print('Index = ' + str(ind) + ' out of ' + str(indices.shape[0]) + ', ' + str(datetime.datetime.now()))
        if ind > 0:
            vocabs.to_csv('Presidential_Transcripts/Vocab_Lists/Vocab_List_' + str(ind//filesPerList) + '.csv',index=False)
            vocabs = pd.DataFrame(columns=['President','Word','Count'])
    tempData = open('Presidential_Transcripts/' + indices.loc[ind,'Doc_Type'] + \
    '/' + indices.loc[ind,'President'].replace(' ','_').replace('.','') + '_' + \
    str(indices.loc[ind,'Doc_Index']) + '.txt','r')
    transcript = tempData.read().lower()
    tempData.close()
    del tempData
    transcript = re.sub('[^\w\s]',' ',transcript).replace('_',' ').replace('ÿ',' ')
    transcript = re.sub('1|2|3|4|5|6|7|8|9|0',' ',transcript)
    transcript = transcript.split()
    vocabs = vocabs.append(pd.DataFrame({'President':len(transcript)*[indices.loc[ind,'President']],\
    'Word':transcript,'Count':len(transcript)*[1]}),ignore_index=True)
    vocabs = vocabs.groupby(['President','Word']).Count.sum().reset_index()
    del transcript
vocabs.to_csv('Presidential_Transcripts/Vocab_Lists/Vocab_List_' + str(ind//filesPerList + 1) + '.csv',index=False)
del ind

vocabs = pd.DataFrame(columns=['President','Word','Count'])
for ind in range(1,indices.shape[0]//filesPerList + 2):
    print('Merging List #' + str(ind))
    vocabs = vocabs.append(pd.read_csv('Presidential_Transcripts/Vocab_Lists/Vocab_List_' + str(ind) + '.csv'))
    vocabs = vocabs.groupby(['President','Word']).Count.sum().fillna(0.0).reset_index()
    os.remove('Presidential_Transcripts/Vocab_Lists/Vocab_List_' + str(ind) + '.csv')
del ind
os.rmdir('Presidential_Transcripts/Vocab_Lists')

vocabs = pd.merge(left=vocabs,right=syllables,how='left',on='Word')
vocabs.loc[vocabs.Hyphenated.isnull(),'Hyphenated'] = vocabs.loc[vocabs.Hyphenated.isnull(),'Word'].apply(dic.inserted).str.split('-')
vocabs.loc[vocabs.Syllables.isnull(),'Syllables'] = vocabs.loc[vocabs.Syllables.isnull(),'Hyphenated'].apply(len)
vocabs = vocabs.loc[~vocabs.Word.isin(funcWords) & ~vocabs.Word.isnull()]
vocabs = vocabs.loc[~vocabs.Word.isin(['applause','laughter','booing']) & (vocabs.Word.str.len() > 1)]
vocabs = pd.merge(left=vocabs,right=presidentYear,how='inner',on='President')
vocabs = vocabs.loc[vocabs.Word.str.len() >= 3]
vocabs['Probability'] = float('NaN')

ngrams = pd.DataFrame({'File':os.listdir('Google_Ngrams')})
if ngrams.shape[0] > 0:
    ngrams['Words'] = ngrams.File.str.split('-eng').str[0].str.split('_')
else:
    ngrams['Words'] = []

query = []
for word in vocabs.loc[~vocabs.Word.isnull(),'Word'].unique():
    """ Ngram query doesn't like the word "year" for some reason... """
    if word == 'year':
        continue
    
    if vocabs.Word.unique().tolist().index(word)%100 == 0:
        print(word + ', Index = ' + str(vocabs.Word.unique().tolist().index(word)) + \
        ' out of ' + str(vocabs.Word.unique().shape[0]) + ', ' + str(datetime.datetime.now()))
    
    if ngrams.Words.apply(lambda x: word in x).any():
        probs = pd.read_csv('Google_Ngrams/' + ngrams.loc[ngrams.Words.apply(lambda x: word in x),'File'].values[0])
        if word in probs.columns:
            probs = probs[['year',word]].rename(index=str,columns={'year':'Ngram_Year',word:'Word_Prob'})
            probs['Word'] = word
            vocabs = pd.merge(left=vocabs,right=probs,how='left',on=['Word','Ngram_Year'])
            vocabs.loc[vocabs.Probability.isnull() & ~vocabs.Word_Prob.isnull(),'Probability'] = \
            vocabs.loc[vocabs.Probability.isnull() & ~vocabs.Word_Prob.isnull(),'Word_Prob']
            del vocabs['Word_Prob']
        del probs
    else:
        query.append(word)
    
    if len(query) == 12:
        os.system('python getngrams.py ' + ', '.join(query) + ' --noprint')
        counter = 0
        while os.stat('_'.join(query) + '-eng_2012-1800-2000-3-caseSensitive.csv').st_size == 1 and counter < 20:
            time.sleep(300)
            os.system('python getngrams.py ' + ', '.join(query) + ' --noprint')
            counter += 1
        
        if os.stat('_'.join(query) + '-eng_2012-1800-2000-3-caseSensitive.csv').st_size == 1:
            print("Tried 20 times and still can't download the ngram... Weird stuff's happening... Check this out...")
            break
        
        os.rename('_'.join(query) + '-eng_2012-1800-2000-3-caseSensitive.csv',\
        'Google_Ngrams/' + '_'.join(query) + '-eng_2012-1800-2000-3-caseSensitive.csv')
        for val in query:
            probs = pd.read_csv('Google_Ngrams/' + '_'.join(query) + '-eng_2012-1800-2000-3-caseSensitive.csv')
            if val in probs.columns:
                probs = probs[['year',val]].rename(index=str,columns={'year':'Ngram_Year',val:'Word_Prob'})
                probs['Word'] = val
                vocabs = pd.merge(left=vocabs,right=probs,how='left',on=['Word','Ngram_Year'])
                vocabs.loc[vocabs.Probability.isnull() & ~vocabs.Word_Prob.isnull(),'Probability'] = \
                vocabs.loc[vocabs.Probability.isnull() & ~vocabs.Word_Prob.isnull(),'Word_Prob']
                del vocabs['Word_Prob']
            del probs
        del val
        query = []

""" Eliminating words that only occur once... """
byWord = vocabs.groupby('Word').Count.sum().reset_index()
vocabs = vocabs.loc[~vocabs.Word.isin(byWord.loc[byWord.Count == 1,'Word'].tolist())]
del byWord

byPres = vocabs.groupby('President').Count.sum().reset_index().rename(index=str,columns={'Count':'Tot_Count'})
vocabs = pd.merge(left=vocabs,right=byPres,how='inner',on='President')
vocabs['Frequency'] = vocabs['Count']/vocabs['Tot_Count']
del vocabs['Tot_Count']

vocabs['p_log_p'] = vocabs.Frequency*np.log(vocabs.Frequency)
vocabs['p_log_p_pn'] = vocabs.Frequency*np.log(vocabs.Frequency/vocabs.Probability)
vocabs.loc[np.isinf(vocabs.p_log_p_pn),'p_log_p_pn'] = 0

vocabs = pd.merge(left=vocabs,right=pd.read_csv('Presidential_Parties.csv'),how='inner',on='President')
vocabs.to_csv('Presidential_Vocabs.csv',index=False)

""" Grouping by president """
entropies = vocabs.groupby('President')[['p_log_p','p_log_p_pn']].sum()
syllables = vocabs.groupby(['President','Syllables']).Frequency.sum().reset_index()
syllables['Weighted_Mean'] = syllables['Syllables']*syllables['Frequency']
avgSyllable = syllables.groupby('President').Weighted_Mean.sum().reset_index()\
.rename(index=str,columns={'Weighted_Mean':'Avg_Syllables'})

byPres = pd.merge(left=entropies,right=avgSyllable,how='inner',on='President')
byPres.to_csv('VocabByPresident.csv',index=False)

#""" Grouping by party """
#party_vocabs = vocabs.groupby(['Party','Word']).Count.sum().reset_index()
#byParty = party_vocabs.groupby('Party').Count.sum().reset_index().rename(index=str,columns={'Count':'Tot_Count'})
#party_vocabs = pd.merge(left=party_vocabs,right=byParty,how='inner',on='Party')
#party_vocabs['Frequency'] = party_vocabs['Count']/party_vocabs['Tot_Count']
#del party_vocabs['Tot_Count'], byParty
#
#party_vocabs = pd.merge(left=party_vocabs,right=vocabs[['Word','Syllables']].drop_duplicates(),how='inner',on='Word')
#party_vocabs['p_log_p'] = party_vocabs.Frequency*np.log(party_vocabs.Frequency)
#
#entropies = party_vocabs.groupby('Party').p_log_p.sum()
#syllables = party_vocabs.groupby(['Party','Syllables']).Frequency.sum().reset_index()
#syllables['Weighted_Mean'] = syllables['Syllables']*syllables['Frequency']
#avgSyllable = syllables.groupby('Party').Weighted_Mean.sum().reset_index()\
#.rename(index=str,columns={'Weighted_Mean':'Avg_Syllables'})
#
#byParty = pd.merge(left=entropies,right=avgSyllable,how='inner',on='Party')
#byParty.to_csv('VocabByParty.csv',index=False)

""" Look at trends over time!!! That would definitely be interesting!!! """
""" Save the top words to note weird differences... """
""" Maybe look at the range of entropies??? """



