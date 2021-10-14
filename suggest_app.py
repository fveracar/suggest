import streamlit as st
import pandas as pd 
import requests
from bs4 import BeautifulSoup
from string import ascii_lowercase
import json 

@st.cache
def convert_df(df):
  return df.to_csv().encode('utf-8')


#Get input from users
with st.form('my_form'):
  seed_kw = st.text_input('seed_kw') 
  seed_kw2 = st.text_input('seed_kw2')
  consultas = st.text_area('Introduce una consulta por línea')
  country = st.text_input('Country', value='es')

  submitted = st.form_submit_button("Obtener suggests")

if submitted:
  kw_list = consultas.split("\n") #almacenamos en una lista cada consulta ingresada por línea en el text area
  #convert seed keyword to list
  keywords = [[seed_kw],[seed_kw2]]
  #create aditionnal seeed by appending a-z & 0-9 to it
  sugg_all_lists = []
  for k in range(len(keywords)):
    for c in ascii_lowercase:
      for c2 in ascii_lowercase:
        keywords[k].append(keywords[k][0]+' '+c+c2)
    for i in range(0,10):
      keywords[k].append(keywords[k][0]+' '+str(i))

    st.write(keywords[k])

    
    #gett all suggestions from Google
    sugg_all = []
    i=1

    for kw in keywords[k]:
      r = requests.get('http://suggestqueries.google.com/complete/search?output=toolbar&hl={}&q={}'.format(country,kw))
      soup = BeautifulSoup(r.content, 'html.parser')
      sugg = [sugg['data'] for sugg in soup.find_all('suggestion')]
      sugg_all.extend(sugg)
    
    sugg_all_lists.append(sugg_all)

  st.write(len(sugg_all_lists))
  st.write(sugg_all_lists)

  for sugg_list in range(len(sugg_all_lists)):
    #remove duplicated
    sugg_all_lists[sugg_list] = pd.Series(sugg_all_lists[sugg_list]).drop_duplicates(keep='first')
    if len(sugg_all_lists[sugg_list])==0:
      st.write('There are no suggestion. The script can\'t work :(')
      
    #get search volume data 
    #prepare keywords for encoding
    data = sugg_all_lists[sugg_list].str.replace(' ','%20').unique()
    #divide kws into chunks of kws
    chunks = [data[x:x+25] for x in range(0, len(data), 25)]

    #create dataframe to receive data from API
    results = pd.DataFrame(columns=['keyword','volume'])

    #get data 
    for chunk in chunks:
      url = (
          'https://db2.keywordsur.fr/keyword_surfer_keywords?country={}&keywords=[%22'.format(country)+
          '%22,%22'.join(chunk)+
          '%22]'
      )

      r = requests.get(url)
      try:
        data = json.loads(r.text)
      except:
        continue

      for key in data.keys():
        results.loc[len(results)] = [key,data[key]['search_volume']]

    results = (
        sugg_all_lists[sugg_list]
        .to_frame()
        .rename({0:'keyword'},axis=1)
        .merge(results,on='keyword',how='left')
        .fillna(0)
    )

    results.sort_values(by='volume',ascending=False).to_csv('data_' + keywords[sugg_list][0] +'.csv',index=False)
    results

    csv = convert_df(results)

    st.download_button(
        label="Descargar",
        data=csv,
        file_name='data_' + keywords[sugg_list][0] +'.csv',
        mime='text/csv',
    )
