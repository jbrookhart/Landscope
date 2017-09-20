from flask import render_template
from flask import request
from flaskexample import app
from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database
from a_Model import ModelIt
import pandas as pd
import psycopg2

user = 'jlbrookhart' #add your username here (same as previous postgreSQL)                      
host = 'localhost'
dbname = 'plants'
db = create_engine('postgres://%s%s/%s'%(user,host,dbname))
con = None
con = psycopg2.connect(database = dbname, user = user)

@app.route('/')
@app.route('/index')
def index():
    return render_template("index.html",
       title = 'Home', user = { 'nickname': 'Jennifer' },
       )

# @app.route('/db')
# def plant_page():
#     sql_query = """
#                 SELECT sun FROM plants_data_table WHERE sun='Full Sun';
#                 """
#     query_results = pd.read_sql_query(sql_query,con)
#     plants = ""
#     for i in range(0,10):
#         plants += query_results.iloc[i]['Hardiness']
#         plants += "<br>"
#     return plants

# @app.route('/db_fancy')
# def plants_page_fancy():
#     sql_query = """
#                 SELECT index, name, category FROM plants_data_table WHERE Hardiness LIKE '%10%';
#                 """
#     query_results=pd.read_sql_query(sql_query,con)
#     plants = []
#     for i in range(0,query_results.shape[0]):
#         plants.append(dict(index=query_results.iloc[i]['index'], name=query_results.iloc[i]['name'], category=query_results.iloc[i]['category']))
#     return render_template('hardiness.html',plants=plants)

@app.route('/input')
def zipcode_input():
    return render_template("input.html")

@app.route('/output')
def zipcode_output():
  #pull 'birth_month' from input field and store it
  landscape = request.args.get('zipcode')
  sun = request.args.get('sun')
  print(landscape)
    #just select the Cesareans  from the birth dtabase for the month that the user inputs
  query = "SELECT zone FROM zipcode_data_table WHERE zipcode='%s'" %landscape
  zone = pd.read_sql_query(query,con).iloc[0,0]
  print(zone)
  query = "SELECT index, plant_name FROM plants_data_table WHERE sun LIKE '%"+sun +"%' AND hardiness LIKE '%"+zone +"%'"
  print(query)
  query_results=pd.read_sql_query(query,con)
  print query_results
  plants = []
  for i in range(0,query_results.shape[0]):
      plants.append(dict(index=query_results.iloc[i]['index'], 
                         plant_name=query_results.iloc[i]['plant_name']))
  result = len(plants)
  return render_template("output.html", plants = plants, num_plants = result)