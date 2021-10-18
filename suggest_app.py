import streamlit as st
import pandas as pd 
import requests
from bs4 import BeautifulSoup
from string import ascii_lowercase
import json 

st.set_page_config(
    page_title='Suggest | Vocento',
)

#Get input from users
with st.form('my_form'):
  consultas = st.text_area('Introduce una consulta por línea')
  country = st.text_input('Country', value='es')

  submitted = st.form_submit_button("Obtener suggests")

if submitted:
  kw_list = consultas.split("\n") #almacenamos en una lista cada consulta ingresada por línea en el text area
  #convert seed keyword to list
  kw_lists = []

  #bucle para crear las lista de cada consulta e incluirla en la kw_lists
  for i in range(len(kw_list)):
    kw_lists.append([])
    for j in range(1):
      kw_lists[i].append(kw_list[i])

  #create aditionnal seeed by appending a-z & 0-9 to it
  sugg_all_lists = []
  for k in range(len(kw_lists)):
    for c in ascii_lowercase:
      for c2 in ascii_lowercase:
        kw_lists[k].append(kw_lists[k][0]+' '+c+c2)
    for i in range(0,10):
      kw_lists[k].append(kw_lists[k][0]+' '+str(i))

    
    #gett all suggestions from Google
    sugg_all = []
    i=1

    for kw in kw_lists[k]:
      r = requests.get('http://suggestqueries.google.com/complete/search?output=toolbar&hl={}&q={}'.format(country,kw))
      soup = BeautifulSoup(r.content, 'html.parser')
      sugg = [sugg['data'] for sugg in soup.find_all('suggestion')]
      sugg_all.extend(sugg)
    
    sugg_all_lists.append(sugg_all)

  for sugg_list in range(len(sugg_all_lists)):
    #remove duplicated
    sugg_all_lists[sugg_list] = pd.Series(sugg_all_lists[sugg_list]).drop_duplicates(keep='first')
    if len(sugg_all_lists[sugg_list])==0:
      st.write('There are no suggestion. The script can\'t work :(')
      
    #get search volume data 
    #prepare kw_lists for encoding
    data = sugg_all_lists[sugg_list].str.replace(' ','%20').unique()
    #divide kws into chunks of kws
    chunks = [data[x:x+25] for x in range(0, len(data), 25)]

    #create dataframe to receive data from API
    results = pd.DataFrame(columns=['keyword','volume'])

    #get data 
    for chunk in chunks:
      url = (
          'https://db2.kw_listsur.fr/keyword_surfer_kw_lists?country={}&kw_lists=[%22'.format(country)+
          '%22,%22'.join(chunk)+
          '%22]'
      )
      error=False
      try:
        r = requests.get(url)
        data = json.loads(r.text)
      except:
        error = True
        continue

    #  for key in data.keys():
        results.loc[len(results)] = [key,data[key]['search_volume']]

    results = (
        sugg_all_lists[sugg_list]
        .to_frame()
        .rename({0:'keyword'},axis=1)
        .merge(results,on='keyword',how='left')
        .fillna(0)
    )

    if error==True:
      st.write('No se pudo obtener el volumen de búsquedas')

    results.to_csv('data_' + kw_lists[sugg_list][0] +'.csv',index=False)
    results
