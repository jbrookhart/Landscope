from flask import render_template
from flask import request, redirect, url_for
from flaskexample import app
from flask_paginate import Pagination, get_page_parameter
from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database
from a_Model import ModelIt
import pandas as pd
import psycopg2
import googlemaps
from datetime import datetime
import numpy as np 
import urllib, json
from math import ceil

user = 'jlbrookhart' #add your username here (same as previous postgreSQL)                      
host = 'localhost'
dbname = 'plants'
db = create_engine('postgres://%s%s/%s'%(user,host,dbname))
con = None
con = psycopg2.connect(database = dbname, user = user)
gmaps = googlemaps.Client(key='AIzaSyDsgfg5hbIAhxEPs25s0ksjwcCs3QphLE4')

hardiness_grid = np.load("phm_us.npy")
hg_latitudes = np.linspace(49.9375, 24.0625, 3105)
hg_longitudes = np.linspace(-125.020833, -66.479167, 7025)
 

def get_zone(tmp):
  temps = [
        ['0b',-65],
        ['1a',-60],
        ['1b',-55],
        ['2a',-50],
        ['2b',-45],
        ['3a',-40],
        ['3b',-35],
        ['4a',-30],
        ['4b',-25],
        ['5a',-20],
        ['5b',-15],
        ['6a',-10],
        ['6b',-5],
        ['7a',0],
        ['7b',5],
        ['8a',10],
        ['8b',15],
        ['9a',20],
        ['9b',25],
        ['10a',30],
        ['10b',35],
        ['11a',40],
        ['11b',45],
        ['12a',50],
        ['12b',55],
      ]
  tmpF = tmp/ 100 *9./5+32
  if tmpF<-65:
    return '0a'
  if tmpF>55:
    return '12b'
  for i,temp in enumerate(temps[0:-1]):
    if (tmpF>= temp[1]) and (tmpF<temps[i+1][1]):
      return temp[0]

def find_nearest(array,value):
    return (np.abs(array-value)).argmin()

def get_ph_range(pH):
  if pH <= 4.5:
    return '4.5 or below (very acidic)'
  if pH <= 5.0:
    return '4.6 to 5.0 (highly acidic)'
  if pH <= 5.5:
    return '5.1 to 5.5 (strongly acidic)'
  if pH <= 6.0:
    return '5.6 to 6.0 (acidic)'
  if pH <= 6.5:
    return '6.1 to 6.5 (mildly acidic)'
  if pH <= 7.5:
    return '6.6 to 7.5 (neutral)'
  if pH <= 7.8:
    return '7.6 to 7.8 (mildly alkaline)'
  if pH <= 8.5:
    return '7.9 to 8.5 (alkaline)'
  if pH <= 9.0:
    return '8.6 to 9.0 (strongly alkaline)'
  return 'over 9.1 (very alkaline)' 

def fix_danger(danger):
  if (danger is None) or danger in [np.nan,"None", "N/A"]:
    return "Safe"
  danger = danger.strip("{").strip("}").replace('","',', ').replace('"','')
  return danger

@app.route('/slides')
def address_slides():
  return render_template("slides.html")

@app.route('/' )
@app.route('/index')
def address_input():
    return render_template("input.html")

PAGENUM = 10

@app.route('/output/')
def address_output():
  address = request.args.get('address')
  geocode_result = gmaps.geocode(address)

  latitude = geocode_result[0]["geometry"]["location"]["lat"]
  longitude = geocode_result[0]["geometry"]["location"]["lng"]

  latpos = find_nearest(hg_latitudes, latitude)
  lngpos = find_nearest(hg_longitudes, longitude)

  zone = get_zone(hardiness_grid[latpos,lngpos])

  soilurl = "https://rest.soilgrids.org/query?lon="+ str(longitude) + "&lat=" + str(latitude) + "&attributes=PHIHOX"
  response = urllib.urlopen(soilurl)
  data = json.loads(response.read())
  ph_dict = data["properties"]["PHIHOX"]["M"]
  pH = get_ph_range(sum([ph_dict[key] for key in ph_dict])/10./len(ph_dict))

  query = "SELECT plantname, url, picture, danger, family FROM plants_data_table WHERE hardiness LIKE '%"+zone +"%' AND ph LIKE '%"+ pH +"%'"
  def construct_query(cat, val):
    if (val is not None) and (val!="All"):
      return " AND " + cat + " LIKE '%" + val +"%'"
    return ""

  sun = request.args.get("sun")
  query += construct_query("sun", sun)
  category = request.args.get("category")
  query += construct_query("category", category)


  query_results=pd.read_sql_query(query,con)
  query_results = query_results.sort_values(["family","plantname"])
  query_results.loc[query_results['picture'].isnull(),'picture']="//:0"
  query_results['danger'] = query_results['danger'].apply(fix_danger)
  plants = []
  for i in range(0,query_results.shape[0]):
      plants.append(dict(plant_name=query_results.iloc[i]['plantname'],   
                         url=query_results.iloc[i]['url'], 
                         image=query_results.iloc[i]['picture'], 
                         danger=query_results.iloc[i]['danger']))
  result = query_results.shape[0]

  page = request.args.get(get_page_parameter(), type=int, default=1)
  
  if not result and page != 1:
    abort(404)
  def plants_this_page(plants,page):
    return plants[(page-1)*PAGENUM:page*PAGENUM]

  plants = plants_this_page(plants, page)
  pagination = Pagination(page=page, 
    total=result, record_name=plants, per_page=PAGENUM,
    css_framework='bootstrap3')
  return render_template("output.html", 
      pagination = pagination,
      plants = plants, 
      num_plants = result, 
      address = address,
      sun = sun,
      category = category,
      latitude = latitude,
      longitude = longitude
      )