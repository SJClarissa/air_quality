import pandas as pd
import numpy as np
import pickle
from flask import Flask, request, render_template, jsonify, Response
import sys
from simulation.simulation import *
# from fbprophet import Prophet

app = Flask('myApp')

@app.route('/', methods=['GET', 'POST'])
@app.route('/form')
def form():
    air_type = 'ozone'
    if request.method == 'POST':
        air_type = request.form['option']
    
    if air_type == 'ozone':
        type_name = 'Ozone'
    else:
        type_name = 'PM 2.5'

    return render_template('form.html', air=air_type+'.html', air_name=type_name)

# Simulation
@app.route('/submit')
def form_submit():
    user_input = request.args
    state = user_input['state']
    
    # This will be removed later
    if user_input['air_type'] == 'ozone':
        state = 'Arizona'
    else:
        state = 'Indiana' 

    test_params = [
        user_input['air_type'],
        int(user_input['year']),
        int(user_input['month']),
        int(user_input['pp_num_0_50']),
        int(user_input['pp_num_50_100']),
        int(user_input['pp_num_100_150'])
    ]
    
    if test_params[0] == 'ozone':
        pred = round(simul_oz(test_params, state), 2)
    elif test_params[0] == 'pm2_5':
        pred = round(simul_pm(test_params, state), 2)

    links = ('./static/imgs/feature_importance_'+user_input['air_type']+'_'+state+'_allpp_dist.png',
            './static/imgs/simul_prophet_' + user_input['air_type'] + '_' + state + '.png',
            './static/imgs/'+user_input['air_type']+'_trend_'+state+'.png',
            './static/imgs/'+user_input['air_type']+'_seasonality_stack_'+state+'.png')  
    
    air_dict = {'ozone': 'Ozone', 'pm2_5': 'PM 2.5'}
    mon_dict = {1:'JAN', 2:'FEB', 3:'MAR', 4:'APR', 5:'MAY', 6:'JUN', 7:'JUL', 8:'AUG', 9:'SEP', 10:'OCT', 11:'NOV', 12:'DEC'}

    test_params[0] = air_dict[user_input['air_type']]
    test_params[2] = mon_dict[int(user_input['month'])]
    
    return render_template('results.html', prediction=pred, params=test_params, state=state, links=links)

# Display map
@app.route('/ozone.html')
def map_oz():
    return render_template('map_pp_oz_aqi_2016_allpp.html')

@app.route('/pm2_5.html')
def map_pm():
    return render_template('map_pp_pm2_5_aqi_2016_allpp.html')

# Display map
@app.route('/simul_map.html')
def map_simul():
    return render_template('map_simulation.html')

# # Display prophet graph
# @app.route('/simul_prophet_graph.html')
# def display_prophet_graph():
#     return render_template('prophet_graph.html')

if __name__ == '__main__':
    app.run(debug=True)
    # app.run(host='0.0.0.0')

# import sys
# sys.stdout.flush()