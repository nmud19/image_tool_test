import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
import base64
import json
import dash_table
import csv
# import cv2
from datetime import datetime as ds
import pandas as pd
from flask import Flask
from PIL import Image, ImageDraw
import urllib
import traceback
import dash_reusable_components as drc
import os
import flask
server = Flask(__name__)

app = dash.Dash(server=server)
app.config['suppress_callback_exceptions']=True
app.css.config.serve_locally = True
# app.script.config.serve_locally = True
# app.css.append_css({'external_url': 'bWLwgP.css'})
# # Loading screen CSS
# app.css.append_css({"external_url": "brPBPO.css"})




stylesheets = ['bWLwgP.css', 'brPBPO.css']
static_css_route = '/'
css_directory = os.getcwd()

@app.server.route('{}<stylesheet>'.format(static_css_route))
def serve_stylesheet(stylesheet):
    if stylesheet not in stylesheets:
        raise Exception(
            '"{}" is excluded from the allowed static files'.format(
                stylesheet
            )
        )
    return flask.send_from_directory(css_directory, stylesheet)


for stylesheet in stylesheets:
    app.css.append_css({"external_url": "/static/{}".format(stylesheet)})


def generate_thumbnail(image_filename):
    print(image_filename)
    encoded_image = base64.b64encode(open(image_filename, 'rb').read())
    encoded_image = encoded_image.decode()
    return html.Div([
        html.Img(
            id= image_filename.replace(".", "--"),
            title=image_filename,
            src='data:image/png;base64,{}'.format(encoded_image),
            style = {
                'height': '10%',
                'width': '10%',
                'float': 'left',
                'position': 'relative',
                'padding-top': 10,
                'padding-right': 10
            })
    ])


# @server.route('/t2/<path:filename>')
# def index(filename):
#     return 'Hello Flask app, is this your file? {}'.format(filename)



RANGE = [0, 1]
data = "" # Sample data string to initialize
# New file name
TABLE_PRESENCE_FILE_NAME = "tab_pres.csv"
# Create /append the file
RESULTS_FILE_NAME = "test.csv"
file = open(RESULTS_FILE_NAME, 'w+')
writer = csv.writer(file)
fields=['filename','ts','x1','x2', 'y1', 'y2', 'h', 'w']
writer.writerow(fields)
file.close()

# For table presence parameters
tab_presence = open(TABLE_PRESENCE_FILE_NAME, 'w+')
tab_presence_writer = csv.writer(tab_presence)
tab_presence_fields = ['filename', 'ts', 'is table present?']
tab_presence_writer.writerow(tab_presence_fields)
tab_presence.close()
#
UPLOAD_DIRECTORY = "app_uploaded_files"
DEFAULT_FOLDER = "trailfolder"
IMAGES_FOLDER = "test"
global IMAGE_NUM
IMAGE_NUM = 0
CURRENT_IMAGE_PATH = "{}/{}.jpg".format(IMAGES_FOLDER, IMAGE_NUM)
IS_MASK_IMAGE = False
TEMP_FILE = "tmp.jpg"
IMAGE_CLICKED_FLAG = 0

#
images_list = ['test/{}.jpg'.format(x) for x in range(10)]
img_div = []
for i in images_list:
    img_div.append(generate_thumbnail(i))

def check_entries() :
    """
    This function will check if any entries exist in the table plot csv.
    If yes
        Then a new image path will be created by drawing a
    :param entries_file_path:
    :return: new_image_file_path
    """
    global CURRENT_IMAGE_PATH
    # Read the file
    fn = pd.read_csv(RESULTS_FILE_NAME)
    # Filter for the current image
    fn = fn[fn.filename == CURRENT_IMAGE_PATH]
    # Check if there are bounfing boxes on the image
    if fn.empty :
        return False, fn
    else:
        # This is the branch if there are bounding boxes on the image
        img = Image.open(CURRENT_IMAGE_PATH)
        width, height = img.size
        draw = ImageDraw.Draw(img)
        fn = fn.reset_index(drop = True)
        for i in range(fn.shape[0]) :

            draw = ImageDraw.Draw(img)
            draw.rectangle(xy=[((fn.loc[i, 'x1'] * width), (1-fn.loc[i, 'y2']) * height),
                               ((fn.loc[i, 'x2'] * width), (1-fn.loc[i, 'y1']) * height),
                               ],
                           outline='red', width=3)

        img.save(TEMP_FILE)
        return True, fn


# Function to return an interactive image
def InteractiveImage(image_path):
    """
    This function updates the image prt of the page with  saved copy of the page
    :param image_path:
    :return:
    """
    # check_entries()
    global IS_MASK_IMAGE, TEMP_FILE
    # print("Status of ismask ---> {}".format(IS_MASK_IMAGE))
    flag, datasource = check_entries()

    print(flag, datasource, datasource.columns)
    if flag:
        encoded_image = base64.b64encode(open(TEMP_FILE, 'rb').read())
        print("Reading this ---> {}".format(TEMP_FILE))
    else:
        encoded_image = base64.b64encode(open(image_path, 'rb').read())
        print("Reading this ---> {}".format(image_path))

    encoded_image = encoded_image.decode()

    graph_layout = dcc.Graph(
        id='interactive-image',
        figure={
            'data': [],
            'layout': {
                'xaxis': {
                    'range': RANGE
                },
                'yaxis': {
                    'range': RANGE,
                    'scaleanchor': 'x',
                    'scaleratio': 1
                },
                'height': 550,
                'width' : 450,
                'images': [{
                    'xref': 'x',
                    'yref': 'y',
                    'x': RANGE[0],
                    'y': RANGE[1],
                    'sizex': RANGE[1] - RANGE[0],
                    'sizey': RANGE[1] - RANGE[0],
                    'sizing': 'stretch',
                    'layer': 'above',
                    'source': 'data:image/png;base64,{}'.format(encoded_image)
                }],
                'dragmode': 'select'  # or 'lasso'
            }
        }
    )
    table_layout = dash_table.DataTable(
                id='table',
                columns=[{"name": i, "id": i} for i in datasource],
                data=datasource.to_dict('records'),
                row_deletable=True,
                style_table={'overflowX': 'scroll'},
                style_cell={
                    'minWidth': '0px', 'maxWidth': '60px',
                    'whiteSpace': 'no-wrap',
                    'overflow': 'hidden',
                    'textOverflow': 'ellipsis',
                },
                css=[{
                    'selector': '.dash-cell div.dash-cell-value',
                    'rule': 'display: inline; white-space: inherit; overflow: inherit; text-overflow: inherit;'
                }],
            )
    return html.Div([
        graph_layout, table_layout,
        html.Div(id='dummy-for-tableremovevalues'),
    ])






@app.callback(Output('selected-image', 'children'),
              [
                  Input(id.replace(".", "--"), 'n_clicks_timestamp') for id in images_list
              ])
def tt(*args) :
    args = [-1 if x is None else x for x in args]
    # global IMAGE_CLICKED_FLAG

    most_recent = max(args)
    if most_recent == -1 :
        return html.H1("No image has been selected yet")
    else:
        global IMAGE_CLICKED_FLAG
        IMAGE_CLICKED_FLAG = 1
        i = args.index(most_recent)
        global CURRENT_IMAGE_PATH
        CURRENT_IMAGE_PATH = images_list[i]
        print("Reset the image filename = " , CURRENT_IMAGE_PATH)
        layout =new_layout()
        IMAGE_CLICKED_FLAG=0
        return layout




def append_to_file(filename, data) :
    """
    This function will take in input of the file and filenme to write in.
    We will append the existing data to the file and then close the file.
    This is always done so that we can use the most updated copy of the file to render image.
    :param filename:
    :param data:
    :return:
    """
    ff = open(filename, 'a+')
    writer = csv.writer(ff)
    writer.writerow(data)
    ff.close()
    return


# Pres any button and the image should be refreshed along with the table
@app.callback(Output('img', 'children'),
              [
                  # Input('next-page', 'n_clicks_timestamp'), Input('prev-page', 'n_clicks_timestamp'),
                  Input('button-table-presence', 'n_clicks_timestamp'),  # for the save table presence button.
                  Input('btn-1', 'n_clicks_timestamp'), # for the save coordinates button
                  Input('table', 'data_previous'), #  if there is table input
              ],
              state=[State('is-table-present', 'value'),
                     State('table', 'data')
                     ]
              )
def button_click_update_image(
        # next, prev,
                              table_button, coordinates_button, co_inpt_table_data,
                              radio_button_value, co_inpt_table_state):
    """
    Logic to save the bounding box from here
    Logic to identify the button that was clicked the most recent
    :param btn1:
    :return:
    """
    global IMAGE_NUM, CURRENT_IMAGE_PATH
    print("-------The input state------")
    print(co_inpt_table_data)
    print("---------The changed state--")
    print(co_inpt_table_state)
    print("-----------------------------")

    if co_inpt_table_data is not None:
        # Remove the row from the csv and save it
        rows_to_remove = [row for row in co_inpt_table_data if row not in co_inpt_table_state]
        print("These are the rows to remove ")
        mm = pd.DataFrame(rows_to_remove)
        m2 = list(mm['ts'])
        global RESULTS_FILE_NAME
        df = pd.read_csv(RESULTS_FILE_NAME)
        print(df)

        print("------>", m2)
        df = df[ ~df.ts.isin(m2)]
        df = df.sort_values(by=['ts'], ascending=False)
        print(df)

        df.to_csv(RESULTS_FILE_NAME, index= False)

    else:
        dash.exceptions.PreventUpdate()
        # Find the largest timestamp/most recent clicked button
        arr = [
            # next, prev,
            table_button, coordinates_button]
        arr = [0 if x is None else float(x) for x in arr]
        if max(arr) == 0 :
            print("No button pressed yet")
        else:
            largest_ts = max(arr)

            # If else logic to check which was clicked the most recent
            # if largest_ts ==  arr[0] :
            #     print(arr, "<---------")
            #     # next button was clicked
            #     print("nextr button clicked", IMAGE_NUM)
            #     if IMAGE_NUM >= 10 :
            #         IMAGE_NUM = 10
            #     else:
            #         IMAGE_NUM += 1
            # elif largest_ts == arr[1] :
            #     # prev button was clicked
            #     print("Prev clicked--", IMAGE_NUM)
            #     if IMAGE_NUM <= 0:
            #         IMAGE_NUM = 0
            #     else:
            #         IMAGE_NUM -= 1
            if largest_ts == arr[0] :
                print("Save table presence button clicked")
                ff = ['{}'.format(CURRENT_IMAGE_PATH), ds.now().timestamp(), radio_button_value]
                append_to_file(TABLE_PRESENCE_FILE_NAME, ff)
            elif largest_ts == arr[1] :
                print("Save coordinates button clicked")
                # The try catch block was to just identify the start boot error
                try:
                    print(data, type(data))
                    # global file, writer
                    ff = ['{}'.format(CURRENT_IMAGE_PATH), ds.now().timestamp(), data['range']['x'][0],
                          data['range']['x'][1], data['range']['y'][0], data['range']['y'][1],
                          abs(data['range']['y'][0] - data['range']['y'][1]),  # height = abs siff y values,
                          abs(data['range']['x'][0] - data['range']['x'][1]),  # width = abs diff x values
                          ]
                    append_to_file(RESULTS_FILE_NAME, ff)
                except:
                    pass
            else :
                pass
    global IMAGE_CLICKED_FLAG
    if IMAGE_CLICKED_FLAG == 0 :
        pass
    else:
        CURRENT_IMAGE_PATH = "{}/{}.jpg".format(IMAGES_FOLDER, IMAGE_NUM)

    print("After the logic this is the filename = {}//{}".format(CURRENT_IMAGE_PATH, IMAGE_CLICKED_FLAG))

    # Read the new image here
    return InteractiveImage(CURRENT_IMAGE_PATH)


# display the event data for debugging

@app.callback(Output('console', 'children'), [Input('interactive-image', 'selectedData')])
def display_selected_data(selectedData):
    global data
    data = selectedData
    return json.dumps(selectedData, indent=2)


@app.callback(
    dash.dependencies.Output('download-link', 'href'),
    [dash.dependencies.Input('download-link', 'download')])
def downloaddata(download):
    csv_string = pd.read_csv(RESULTS_FILE_NAME).to_csv(index=False, encoding='utf-8')
    csv_string = "data:text/csv;charset=utf-8,%EF%BB%BF" + urllib.parse.quote(csv_string)
    return csv_string

def new_layout():
    return html.Div([

        # Banner display
        # html.Div([
        #     html.H2(
        #         'More details',
        #         id='title',
        #     ),
        #     # html.Img(
        #     #     src="https://s3-us-west-1.amazonaws.com/plotly-tutorials/logo/new-branding/dash-logo-by-plotly-stripe-inverted.png"
        #     # )
        #
        # ],
        #     className="banner", style={'textAlign': 'center'}
        # ),

        # Body
        html.Div(className="container", children=[
            html.Div(className='row', children=[

                html.Div(
                    # className='three columns',
                         children=[
                    html.Div(
                        [
                            drc.Card([
                                # Next and previous buttons
                                html.Div([
                                    # html.Button('<--', id='prev-page', n_clicks_timestamp=0),
                                    # html.Button('-->', id='next-page', n_clicks_timestamp=0),
                                    html.A(
                                        'Download Data',
                                        id='download-link',
                                        download="test.csv",
                                        href="",
                                        target="_blank"
                                    )

                                ],
                                    # className='two columns', style={"border": "2px black solid"}
                                )

                                # Is there a table on the page
                                ,
                                html.Div(
                                    [
                                        html.Div(
                                            html.H6("Is there a table on this page?")
                                        ),  # Text for asking question
                                        html.Div(
                                            dcc.RadioItems(
                                                id="is-table-present",
                                                options=[
                                                    {'label': 'Yes', 'value': 'Y'},
                                                    {'label': 'No', 'value': 'N'},
                                                ],
                                                value='N',
                                                # labelStyle={'display': 'inline-block'}
                                            )
                                        ),  # The radio button
                                        html.Div(
                                            html.Button("Save table presence input!",
                                                        id="button-table-presence",
                                                        # style=dict(
                                                        #     width='50%',
                                                        #     display='table-cell',)
                                                        )
                                        ),  # button to save the input
                                    ],
                                    # className='three columns', style={"border": "2px black solid"}
                                ),
                            ]),

                            drc.Card([
                                html.Div(id='dummy-for-istablepresent-save'),
                                #
                                html.Div([
                                    html.Div([
                                        html.Button('Save this snapshot', id='btn-1', n_clicks_timestamp=0
                                                    # style=dict(
                                                    #     width='50%',
                                                    #     display='table-cell', )
                                                    ),
                                        html.Div(id='container-button-timestamp')
                                    ],
                                        # className='six columns'
                                    ),
                                    html.Div([
                                        html.Br(),
                                        html.Br(),
                                        html.Br(),
                                        html.Br(),

                                    ]),

                                    html.Pre(id='console'),
                                ]),

                            ]),
                        ], style={
                    'width': '50%', 'display': 'inline-block'
                            # 'width': '300%'
                }
                    ),
                             html.Div(
                                 # className='three columns',
                                 style={'width': '50%', 'display': 'inline-block'
                                        # 'width' : '600%'
                                        },
                                 children=[
                                     html.Div(id='img', children=InteractiveImage('test/0.jpg'),
                                              # className='six columns'
                                              )
                                 ]),

                    ]
                )
            ])
        ])
    ], style={'display': 'inline-block'} )



app.layout = html.Div([
    html.Div(
        [html.H1("Image Label Tool ".format(CURRENT_IMAGE_PATH))],
        style={'textAlign': 'center'}
    ),
    drc.Card([html.Div(children=img_div, style={'overflowY': 'scroll', 'height': 100, 'border': '3px', 'display': 'inline-block'})]),
    html.Div(id="selected-image"),
    # html.Div(id="analysis-chart" , children=[new_layout()])
], style={'width': '100%', 'display': 'inline-block'})


#
if __name__ == '__main__':
    app.run_server(debug=True)