from flask import Flask, render_template, request
import os
from datetime import datetime
import shutil

from utils.gsheet import GoogleSheet
from data_analysis import *
from constant import *

# in deploy_branch

app = Flask(__name__)


@app.route('/')
def main_page():

    # rm the folder to avoid multiple rendering data explode
    bar_chart_folder = os.path.dirname(PATH_TO_BARCHART)
    if os.path.exists(bar_chart_folder):
        shutil.rmtree(bar_chart_folder)
    os.makedirs(os.path.dirname(PATH_TO_BARCHART))

    gs = GoogleSheet.read_from(STUDY_TIME_TABLE_NAME)
    df_dur = gs.sheet(sheet_name=SHEET1, least_col_name=START_TIME)
    df_eve = gs.sheet(sheet_name=SHEET2, least_col_name=NAME)
    df = merge_dur_eve(df_dur, df_eve)

    # process the data table
    df_all = preprocess_data(df)

    # transfer it to plot-ready data table
    df_min_all = to_minutes_leaderboard(df_all)
    df_min_last_week = to_minutes_leaderboard(to_this_week_table(df_all))

    # add datetime time to avoid read from cache
    chart_name, img_format = os.path.split(PATH_TO_BARCHART)[1].split(".")
    new_chart_name = "{}_{}.{}".format(chart_name, datetime.now().strftime('%H_%M_%S'), img_format)

    # component 1: the last week bar chart
    path_to_chart_last_week = os.path.join(os.path.dirname(PATH_TO_BARCHART), "last_week_" + new_chart_name)
    plot_the_bar_chart(df_min_last_week, output_path=path_to_chart_last_week)

    # component 2: the bar chart
    path_to_chart_all = os.path.join(os.path.dirname(PATH_TO_BARCHART), "all_" + new_chart_name)
    plot_the_bar_chart(df_min_all, output_path=path_to_chart_all)

    # component 3: name_winner and duration_str
    name_winner = list(df_min_all[NAME])[0]
    duration_str = min2duration_str(list(df_min_all[MINUTES])[0])

    return render_template('index.html',
                           path_to_chart_last_week=path_to_chart_last_week,
                           path_to_chart_all=path_to_chart_all,
                           name_winner=name_winner,
                           duration_str=duration_str)


@app.route('/about')
def about_page():
    return render_template('about.html')

@app.route('/personal_analysis', methods=['GET', 'POST'])
def personal_analysis_page():

    # rm the folder to avoid multiple rendering data explode
    bar_chart_folder = os.path.dirname(PATH_TO_BARCHART)
    if os.path.exists(bar_chart_folder):
        shutil.rmtree(bar_chart_folder)
    os.makedirs(os.path.dirname(PATH_TO_BARCHART))

    no_such_user=False

    if request.method == 'POST':  # this block is only entered when the form is submitted
        username = request.form.get('username')

        gs = GoogleSheet.read_from(STUDY_TIME_TABLE_NAME)
        df_dur = gs.sheet(sheet_name=SHEET1, least_col_name=START_TIME)
        df_eve = gs.sheet(sheet_name=SHEET2, least_col_name=NAME)
        df = merge_dur_eve(df_dur, df_eve)

        # process the data table
        df_all = preprocess_data(df)

        if username in df[NAME].unique():
            df_user = to_personal_analysis_table(df_all, username)

            chart_name, img_format = os.path.split(PATH_TO_BARCHART)[1].split(".")
            new_chart_name = "{}_{}.{}".format(chart_name, datetime.now().strftime('%H_%M_%S'), img_format)
            path_to_chart_user = os.path.join(os.path.dirname(PATH_TO_BARCHART), username + "_" + new_chart_name)

            plot_hours_per_day(df_user, output_path=path_to_chart_user)

            return render_template('personal_analysis.html',
                                   username=username,
                                   path_to_chart_user=path_to_chart_user)
        else:
            no_such_user = True

    if no_such_user:
        name_warning = ""
    else:  # has such user
        name_warning = "visibility: hidden"

    return render_template('personal_analysis_login.html', name_warning=name_warning)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5555, debug=True)
