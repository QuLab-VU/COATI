import numpy as np
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from utils import *
from statistics import mean
import datetime as dt
import webbrowser

col1, col3 = st.columns(2)
with col1:
    st.header('C.O.A.T.I.')
    st.write('Calcium Oscillation Analysis Tool -- interactive')

with col3:
    st.image('images/coati3.png')

st.markdown('#')

st.info(
    'This program accepts calcium binding data with pre-defined regions of interest (ROIs). User defined criteria are'
    'used to identify and quantify oscillations in the calcium binding data.')

st.subheader('1. Upload calcium oscillation data')
csv_in = st.file_uploader("Choose a CSV file", type='csv', accept_multiple_files=False)

with st.expander('Upload file requirements'):
    st.write("""
    Upload file must meet the following requirements:
    1. CSV format
    2. File should contain region of interest data generated using NIS AR software.    
    """)

df = pd.DataFrame()

if csv_in is not None:

    st.write('Formatting data...')

    df_in = pd.read_csv(csv_in)
    df_out = df_in[['ROI ID', 'Time [h:m:s]', 'Ratio 340/380']].copy()

    cols = df_out.columns
    ids = df_out[cols[0]].unique()
    time_cols = ['ID'] + list(df_out[cols[1]].unique())

    vals_by_cell = list()

    progress_bar_0 = st.progress(0)

    for i in range(len(ids)):
        id_n = [ids[i]] + list(df_out[df_out[cols[0]] == ids[i]][cols[2]])
        vals_by_cell.append(id_n)
        progress = i / len(ids)
        progress_bar_0.progress(progress)

    df = pd.DataFrame(vals_by_cell, columns=time_cols)

    st.write('Data successfully formatted.')
    st.text('Dataset contains : ' + str(len(df)) + ' samples')
st.markdown('#')
st.markdown('#')
st.markdown('#')

# Select features of interest
st.subheader('2. Select features')
feature_options = ['ROI mean', 'Number of oscillations',
                   'Oscillation integral', 'Oscillation duration', 'Oscillation height',
                   'Oscillation mean']

selected_options = st.multiselect(
    'Features of interest',
    feature_options,
    default=feature_options)

with st.expander('Additional feature information'):
    st.caption("""
    ROI mean: mean calcium binding ratio across the entire ROI\n
    Number of oscillations: The number of oscillations detected in an ROI\n
    Oscillation integral: mean integral of area underneath oscillations in an ROI\n
    Oscillation duration: mean duration of oscillations in an ROI\n
    Oscillation height: mean height of oscillations in an ROI\n
    Oscillation height: mean of mean values of oscillations in an ROI
    """)

# st.write('You selected:', str(selected_options))
st.markdown('#')
st.markdown('#')
st.markdown('#')

# Define oscillation criteria
st.subheader('3. Define oscillation criteria')
if df is not None and len(df) > 0:
    # st.subheader('Define oscillation criteria')

    example_roi = st.selectbox(
        'Select an example region of interest (ROI) to visualize oscillation criteria',
        list(df[df.columns[0]]), index=8)

# Select a moving average period
ma_size = st.slider('Select a moving average period (default=20)', 0, 100, 20)
st.write("Selected moving average ", ma_size)

stdev = st.slider('Select a standard deviation threshold (default=0.50)', 0.1, 2.0, .5)
st.write("Threshold", stdev)

if df is not None and len(df) > 0:
    fig = plt.figure(figsize=(10, 5))
    roi = list(df.iloc[example_roi])[2:]
    roi_ma = calc_ma(roi, size=ma_size)
    starts, ends, threshold = find_ma_spikes(roi, roi_ma, std_threshold=stdev)
    roi_cum_ma = calc_cum_ma(roi)
    plt.plot(roi)
    plt.plot(roi_ma, color='k')
    plt.plot(threshold, color='y')
    for i in range(len(starts)):
        plt.axvline(x=starts[i], color='goldenrod', linestyle='dashdot')
        plt.axvline(x=ends[i], color='goldenrod', linestyle='dashdot')

    plt.xticks(np.arange(0, len(roi), 50))
    plt.legend(['Bound calcium ratio', 'Moving average', 'Oscillation threshold'])
    st.pyplot(fig)
    st.info('Vertical golden bars denote oscillations defined by your criteria')

    # Display meta stats for example ROI
    durations = [ends[i] - starts[i] for i in range(len(ends))]
    heights = list()
    means = list()
    integrals = list()

    if len(starts) > 0:
        for i in range(len(starts)):
            spike = roi[starts[i] - 1:ends[i] + 1]

            height = max(spike)
            heights.append(height)

            mean_ = round(mean(spike), 3)
            means.append(mean_)

            floor = roi_cum_ma[i]
            norm_spike = [round(point - floor, 3) for point in spike]
            integral = np.trapz(norm_spike)
            integrals.append(integral)

    parameters = list()
    if feature_options[0] in selected_options:
        parameters.append(mean(roi))
    if feature_options[1] in selected_options:
        parameters.append(len(starts))
    if feature_options[2] in selected_options:
        try:
            parameters.append(mean(integrals))
        except:
            parameters.append(0)
    if feature_options[3] in selected_options:
        try:
            parameters.append(mean(durations))
        except:
            parameters.append(0)
    if feature_options[4] in selected_options:
        try:
            parameters.append(mean(heights))
        except:
            parameters.append(0)
    if feature_options[5] in selected_options:
        try:
            parameters.append(mean(means))
        except:
            parameters.append(0)

    # parameters = [example_roi] + parameters
    param_columns = selected_options
    example_param_df = pd.DataFrame([parameters], columns=param_columns, index=[example_roi])
    st.dataframe(example_param_df.style.hide_index())

# if df is not None and len(df) > 0:
#     fig = plt.figure(figsize=(10, 5))
#     plt.plot(df.iloc[example_roi][2:])
#     plt.xticks([])
#     st.pyplot(fig)

st.subheader('4. Run analysis on full dataset')

progress_bar = st.progress(0)
analysis = False

if st.button('Run analysis'):
    st.write('Analysis running...')

    parameter_list_2 = list()

    for j in range(len(df)):
        progress = j / len(df)
        progress_bar.progress(progress)
        roi = list(list(df.iloc[j].values)[2:])
        roi_ma = calc_ma(roi, size=20)

        # use the new ma
        starts, ends, threshold = find_ma_spikes(roi, roi_ma, std_threshold=0.5)
        roi_cum_ma = calc_cum_ma(roi)

        durations = [ends[i] - starts[i] for i in range(len(ends))]
        heights = []
        means = []
        integrals = []

        if len(starts) > 0:
            for i in range(len(starts)):
                spike = roi[starts[i] - 1:ends[i] + 1]

                height = max(spike)
                heights.append(height)

                mean_ = round(mean(spike), 3)
                means.append(mean_)

                floor = roi_cum_ma[i]
                norm_spike = [round(point - floor, 3) for point in spike]
                integral = np.trapz(norm_spike)
                integrals.append(integral)

            parameters = list()
            if feature_options[0] in selected_options:
                parameters.append(mean(roi))
            if feature_options[1] in selected_options:
                parameters.append(len(starts))
            if feature_options[2] in selected_options:
                parameters.append(mean(integrals))
            if feature_options[3] in selected_options:
                parameters.append(mean(durations))
            if feature_options[4] in selected_options:
                parameters.append(mean(heights))
            if feature_options[5] in selected_options:
                parameters.append(mean(means))
            parameter_list_2.append(parameters)

        elif len(starts) == 0:
            parameters = list()
            if feature_options[0] in selected_options:
                parameters.append(mean(roi))
            if feature_options[1] in selected_options:
                parameters.append(0)
            if feature_options[2] in selected_options:
                parameters.append(0)
            if feature_options[3] in selected_options:
                parameters.append(0)
            if feature_options[4] in selected_options:
                parameters.append(0)
            if feature_options[5] in selected_options:
                parameters.append(0)
            parameter_list_2.append(parameters)

    parameter_columns_2 = selected_options
    parameter_df_2 = pd.DataFrame(parameter_list_2, columns=parameter_columns_2)

    st.text('View Results')
    st.dataframe(parameter_df_2)
    analysis = True

st.markdown('#')
st.markdown('#')
st.markdown('#')

st.subheader('5. Download results')

if analysis:
    st.download_button(
        label="Download results as CSV",
        data=parameter_df_2.to_csv().encode('utf-8'),
        file_name='coati-results-{}.csv'.format(dt.date.today())
    )

st.markdown('#')
st.markdown('#')
st.markdown('#')
st.write('Created by Jonathan Lifferth in the lab of Dr. Vito Quaranta')
src_url = 'https://github.com/QuLab-VU/COATI'
if st.button('View source code on GitHub'):
    webbrowser.open_new_tab(src_url)
