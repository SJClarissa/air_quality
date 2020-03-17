import pandas as pd
import numpy as np
import folium
import geopandas as gpd
from branca.colormap import linear
from shapely.geometry.polygon import Polygon
from sklearn.utils import resample
# from fbprophet import Prophet
from matplotlib import pyplot as plt
import pickle
import sys

# Input air type, empty df with columns of pickle, year, month and num of power plants within certain miles
# Return dataset for simulation
def make_dataset(df_test, data_50, data_100, data_150, i_year=2020, i_month=3, num_0_50=0, num_50_100=0, num_100_150=0):
    
    # Resample
    df_test = pd.concat([df_test, resample(data_50, n_samples=num_0_50, replace=True)], axis=0, sort=False)
    df_test = pd.concat([df_test, resample(data_100, n_samples=num_50_100, replace=True)], axis=0, sort=False)
    df_test = pd.concat([df_test, resample(data_150, n_samples=num_100_150, replace=True)], axis=0, sort=False)
            
    df_test['year'] = i_year
        
    # Take care of dummied months
    for i in range(2, 13, 1):
        if i == i_month:
            df_test['month_'+str(i)] = 1
        else:
            df_test['month_'+str(i)] = 0
    
    return df_test

# Functino to simulate with a picked model
def get_pred(model_path, sample):
    
    with open(model_path, 'rb') as f:
        mdl = pickle.load(f)
    
    return mdl.predict(sample).mean()
        
def simul_oz(params, state):
    columns = pd.read_csv('./data/simul/rf_oz_Arizona_allpp_columns.csv')
    smpl = make_dataset(columns,
                        pd.read_csv('./data/simul/rf_oz_Arizona_allpp_50.csv'),
                        pd.read_csv('./data/simul/rf_oz_Arizona_allpp_100.csv'),
                        pd.read_csv('./data/simul/rf_oz_Arizona_allpp_150.csv'),
                        params[1], params[2], params[3], params[4], params[5])
    pp_data = smpl[['lat', 'long', 'fuel', 'pp_boiler', 'state']]
    states_Arizona = ['Arizona', 'California', 'Nevada', 'Utah', 'Colorado', 'New Mexico']
    ctr_ll = (36.229759, -111.431221)

    # make sample dataset as the same shape as the modeling data 
    smpl.drop(columns=['lat', 'long', 'fuel', 'state'], axis=1, inplace=True)

    pred = get_pred('./code/pickles/rf_ozone_Arizona_dsi.pickle', smpl)

    save_map(states_Arizona, 'pm2_5_aqi', ctr_ll, pred, pp_data)
    # save_prophet_plot(state, params[0], params[1], params[2], pred)

    return pred

def simul_pm(params, state):
    columns = pd.read_csv('./data/simul/rf_pm_Indiana_allpp_columns.csv')
    smpl = make_dataset(columns,
                        pd.read_csv('./data/simul/rf_pm_Indiana_allpp_50.csv'),
                        pd.read_csv('./data/simul/rf_pm_Indiana_allpp_100.csv'),
                        pd.read_csv('./data/simul/rf_pm_Indiana_allpp_150.csv'),
                        params[1], params[2], params[3], params[4], params[5])
    pp_data = smpl[['lat', 'long', 'fuel', 'pp_boiler', 'state']]
    states_Indiana = ['Indiana', 'Illinois', 'Kentucky', 'Ohio', 'Michigan', 'Wisconsin']
    ctr_ll = (40.849426, -86.258278)

    # make sample dataset as the same shape as the modeling data 
    smpl.drop(columns=['lat', 'long', 'fuel', 'state'], axis=1, inplace=True)

    pred = get_pred('./code/pickles/rf_pm2_5_Indiana_dsi.pickle', smpl)

    save_map(states_Indiana, 'oz_aqi', ctr_ll, pred, pp_data)
    # save_prophet_plot(state, params[0], params[1], params[2], pred)

    return pred

def save_map(states, air, ctr_ll, pred, pp_data):
    shape_load = gpd.read_file('./data/shape_states')
    map = make_simul_map(shape_load, air, 'Average AQI', pp_data, 'fuel', 'pp_boiler', ctr_ll, states, pred)
    map.save('./templates/map_simulation.html')


def make_simul_map(shape, shape_column, shape_caption, data, data_cat, data_val, ctr_ll, states, pred):
    color_map = linear.Blues_09.scale(min(shape[shape_column]), max(shape[shape_column]))
    color_map = color_map.to_step(index=np.linspace(shape[shape_column].min(), shape[shape_column].max(), 10, endpoint=True).round(0))

    pred_color = color_map(pred)
    fuel_color = {'Fossil_fuel':'red', 'Oil':'purple', 'Biomass':'brown', 'Gas':'pink',
              'Hydro': 'yellow', 'Nuclear': 'green', 'Sun':'orange', 'Wind': 'gray'}

    shape = shape[shape['state'].isin(states)]
    
    m = folium.Map([ctr_ll[0], ctr_ll[1]], zoom_start=6)

    style_function = lambda x: {
        'fillColor': pred_color,
        'color': 'black',
        'weight': 1.5,
        'fillOpacity': 0.7
    }

    folium.GeoJson(
        shape,
        style_function=style_function
    ).add_to(m)

    for idx, row in data.iterrows():
        folium.CircleMarker(location=(row['lat'], row['long']),
                            radius= row[data_val]+2,
                            color=fuel_color[row[data_cat]],
                            fill=True,
                            fillColor=fuel_color[row[data_cat]],
                            fill_opacity = 0.4,
                            stroke=False,
                            tooltip=row[data_cat]).add_to(m)
    
    color_map.caption = shape_caption
    color_map.add_to(m)
    return m

# def save_prophet_plot(state, air_type, pred_year, pred_month, pred_value):
#     if int(pred_month) < 10:
#         pred_date = pd.to_datetime(str(pred_year)+'-0'+str(pred_month)+'-15')
#     else:        
#         pred_date = pd.to_datetime(str(pred_year)+'-'+str(pred_month)+'-15')
 
#     model = pickle.load(open('./code/pickles/prophet_'+air_type+'_'+state+'.pickle', 'rb'))
    
#     dt_future = model.make_future_dataframe(periods=365)
#     model_forecast = model.predict(dt_future)  
#     fig = model.plot(model_forecast)
#     plt.scatter(pred_date, pred_value, color = 'red', alpha=0.8)
    
#     fig.savefig('./static/imgs/simul_prophet_' + air_type + '_' + state + '.png')
#     fig.savefig('./img/simulated_prophet_graph.png')

