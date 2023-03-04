#Importing necessary libraries
import requests
import pandas as pd
import numpy as np
from datetime import date, timedelta
import plotly_express as px
import streamlit as st

#Setting Streamlit page config

st.set_page_config(page_title='Portfel walutowy',page_icon=':chart_with_upwards_trend:',layout='wide')

#Setting the start and end date to the current date
start_date = date.today().strftime("%Y-%m-%d")
end_date = date.today().strftime("%Y-%m-%d")


#Defining a function to get data from the API
def get_data(start):
    url = f"https://api.nbp.pl/api/exchangerates/tables/a/{start_date}/{end_date}/?format=json"
    response = requests.get(url)
    if response.status_code == 200:
        data_raw = response.json()


        list_data = []
        list_date = []
        for date in data_raw:
            for data in date['rates']:
                list_data.append(list(data.values()))
                list_date.append(date['effectiveDate'])


        df_raw = pd.DataFrame(list_data)
        df_raw['Data'] = list_date
        df_raw = df_raw.rename(columns={0:'currency',1:'code',2:'mid'})


        df = df_raw.copy()
        return df
    else:
        st.write("Wystąpił błąd:", response.status_code)
        
        
#Defining a function to check the end date
def end_date_check(start):
    if start + timedelta(days=30) > date.today():
        return date.today().strftime("%Y-%m-%d")
    else:
        d = start + timedelta(days=30)
        return 
        
    

# SIDEBEAR
#Setting up the sidebar with input widgets
st.sidebar.header('Dane:')
start_date = st.sidebar.date_input("Wprowadź datę:",min_value=date.today() - timedelta(days=90),max_value=date.today())
end_date = end_date_check(start_date)

#Getting the data from the API
df = get_data(start_date)

if df is not None:
    #Creating selection boxes for currency codes
    sw1 = st.sidebar.selectbox('Wprowadź kod waluty:', df['code'].unique(), key='sw1')
    sw2 = st.sidebar.selectbox('Wprowadź kod waluty:', df['code'].unique(), key='sw2')
    sw3 = st.sidebar.selectbox('Wprowadź kod waluty:', df['code'].unique(), key='sw3')


    #Getting the amount from the user
    amount = st.sidebar.number_input('Wprwoadź kwotę:', min_value=0, value=1000, step=50)


    st.sidebar.text("")
    st.sidebar.text("")

    #Creating an empty error message to display in case of incorrect user input
    error_info = st.sidebar.empty()


    #Creating sliders to allow the user to set the percentage of each currency in the portfolio
    wp1 = st.sidebar.slider(f'Procentowy udział waluty {st.session_state.sw1}:', 0, 100, 40, key='wp1') /100
    wp2 = st.sidebar.slider(f'Procentowy udział waluty {st.session_state.sw2}:', 0, 100, 30, key='wp2') /100
    wp3 = st.sidebar.slider(f'Procentowy udział waluty {st.session_state.sw3}:', 0, 100, 30, key='wp3') /100

    #Checking if the sum of percentages is greater than 100%
    if sum([st.session_state.wp1,st.session_state.wp2,st.session_state.wp3]) > 100:
        error_info.error('Suma ustalonych procentów więszka od 100%')
        
    #Define a dictionary that maps currency codes to their respective names
    currency_dict = {sw1:wp1,sw2:wp2,sw3:wp3}

    #Filter the DataFrame to include only the specified currency codes and rename some of the columns
    df_selector = df.query('code in [@sw1,@sw2,@sw3]')
    df_selector = df_selector.rename(columns=
                    {'currency': 'Nazwa waluty',
                        'code': 'Kod',
                        'mid': 'Kurs',
                        })


    # BODY
    #Convert the start date to a string and filter the DataFrame to include only data from that date
    s = str(start_date)
    df_start = df_selector.query('Data == @s').reset_index(drop=True)

    #Calculate the percentage value and the invested amount for each currency and add them as new columns to df_start
    df_start['Wartość %'] = df_start['Kod'].map(currency_dict)
    df_start['Inwestowana kwota'] = amount * df_start['Wartość %']

    #Calculate the purchased value for each currency and add it as a new column to df_start
    df_start['Zakupiona wartość'] = df_start['Inwestowana kwota'] / df_start['Kurs']

    #Merge df_selector with df_start on the 'Kod' column and add the resulting columns as new columns to df_selector
    df_selector = df_selector.merge(df_start,left_on='Kod',right_on='Kod',how='left',suffixes=('_new','_start'))

    #Calculate the return amount and profit/loss for each currency and add them as new columns to df_selector
    df_selector['Kwota zwrotu'] = df_selector['Zakupiona wartość'] * df_selector['Kurs_new']
    df_selector['Zysk/Strata'] = df_selector['Kwota zwrotu'] - df_selector['Inwestowana kwota']

    #Filter the DataFrame to include only data from the end date
    df_end = df_selector[df_selector["Data_new"] == df_selector["Data_new"].max()]


    #HEADER

    #Define the headers for the left and right columns of the main section
    left_header,space, right_header = st.columns([3,1,2])

    #Write the header for the right column
    right_header.write('Aktualne kursy walut')
    metric1,metric2,metric3 = right_header.columns([1,1,1])

    #Define the three metrics for displaying the currency codes, current values, and percentage changes
    value_mid_m1 = df_end.query('Kod == @sw1')
    value_mid_p1 = ((value_mid_m1['Kurs_new'] / value_mid_m1['Kurs_start'])-1)
    value_mid_m1 = value_mid_m1['Kurs_new']

    #Retrieve the current value and percentage change for the second currency and display them using the second metric
    value_mid_m2 = df_end.query('Kod == @sw2')
    value_mid_p2 = (value_mid_m2['Kurs_new'] / value_mid_m2['Kurs_start'])-1
    value_mid_m2 = value_mid_m2['Kurs_new']

    #Retrieve the current value and percentage change for the third currency and display them using the third metric
    value_mid_m3 = df_end.query('Kod == @sw3')
    value_mid_p3 = (value_mid_m3['Kurs_new'] / value_mid_m3['Kurs_start'])-1
    value_mid_m3 = value_mid_m3['Kurs_new']

    #Display currency code, current value, and percentage change using the metric
    metric1.metric(f"{sw1}", value_mid_m1,f'{np.round(value_mid_p1.item(),4)} %')
    metric2.metric(f"{sw2}", value_mid_m2,f'{np.round(value_mid_p2.item(),4)} %')
    metric3.metric(f"{sw3}", value_mid_m3,f'{np.round(value_mid_p3.item(),4)} %')
    left_header.dataframe(df_start,use_container_width=True)




    # MAIN
    sum_currency = df_selector[['Data_new','Kwota zwrotu']].groupby('Data_new').sum()
    fig = px.line(sum_currency)
    section_sum = st.container()
    section_sum.plotly_chart(fig,use_container_width=True)
    df_main = df_selector[['Data_new','Nazwa waluty_new','Kod','Kurs_new','Data_start','Kurs_start','Inwestowana kwota','Zakupiona wartość','Kwota zwrotu','Zysk/Strata']].rename(columns=
        {
            'Nazwa waluty_new' : 'Nazwa waluty',
            'Kod': 'Kod',
            'Kurs_new': 'Kurs Akt.',
            'Data_new': 'Data notowania',
            'Data_start': 'Data zakupu',
            'Kurs_start': 'Kurs Zakupu',
        }
    )

    st.dataframe(df_main,use_container_width=True)