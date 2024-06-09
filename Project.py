#################### Requirements
"""Requirements:
1. Require Python 3.6 or higher
2. Install python libraries - pandas, geopandas, dash, dash-bootstrap-components, openpyxl,dash-auth - using pip:
    pip install pandas
    pip install geopandas
    pip install dash
    pip install dash-bootstrap-components
    pip install openpyxl #To enable loading of excel spreadsheet file i.e. .xls/.xlsx file.
    pip install dash-auth
"""



################### import the libraries
import dash_auth.basic_auth
import plotly.io as pio
import plotly.express as px
from dash import Dash, html, dcc, Input, Output, State
import dash_bootstrap_components as dbc
import geopandas as gpd
import pandas as pd
import json
from datetime import date
import dash_auth


####### Adding authorization
userPasswordPairs = [['Project', 'Password@123'], ['Sameer', 'Sameer@123'], ['User', 'zxcvbnm']]

#To define rows and columns, here premade CSS stylsheet ('VAPOR') has been used which is available within dash.
app = Dash(__name__, external_stylesheets=[dbc.themes.VAPOR])
server = app.server
login = dash_auth.BasicAuth(app, userPasswordPairs)

###################### Prepare the data

##### Load the shapefile (from SOI) and convert it to geodataframe using geopandas. Projection used for this shapefile EPSG:32643 (UTM43N, WGS84)
# Locate the path of shapefile in your computer.
shapefile_path = "Shapefile/UTTARAKHAND_SUBDISTRICT_BDY.shp"
gdf = gpd.read_file(shapefile_path)

#IMPORTANT: Ensure projection of shapefile to "WGS84" so that everything goes fine while plotting map.
gdf = gdf.to_crs("WGS84")
#This geodataframe was converted to geojson file and saved in local folder. The below code has been commented because the file has been already saved.
#gdf.to_file("Shapefile/UTTARAKHAND_SUBDISTRICT_BDY.geojson")

#load the above geojson file. Locate the path of geojson file in your computer.
gjson = json.load(open("Shapefile/UTTARAKHAND_SUBDISTRICT_BDY.geojson"))

# Locate the path of excel spreadsheet in your computer.
#load the excel spreadsheet using pandas to make it a dataframe. The data was downloaded from Agmarket portal, Govt. of India.
df = pd.read_excel("Data/Compiled Data.xlsx")

#format the date in dataframe to process further.
df["Reported Date"]=pd.to_datetime(df["Reported Date"], format="mixed")

########### Manage the layout and styling of dashboard (web interface as seen by user)
#Dash handles layout as components be it heading, dropdown menus, radio buttons, graphs, maps etc.
#The whole webpage is like a container in which there are many rows, and within rows there are column(s).
app.layout = dbc.Container(
    [
        dbc.Row(    #### The first row is heading. The next row has four column - two for dropdown menus and another two for date selector.
            dbc.Col(
                [
                    html.H1(
                        "Market Price of Agricultural Commodity in Mandis of Uttarakhand",
                        style={"textAlign": "center", "fontSize":30, "marginBottom": "50px"},
                    ),
                ],
                width=12,
            ) 
        ),  
        dbc.Row(
            [
                dbc.Col([dbc.Label(     ### This column has dropdown menu for selecting Market Name. 
                            "Select Market Name",
                            className="fw-bold",
                            style={"textAlign":"center","fontSize": 15, "display":"block"},
                            ),
                dcc.Dropdown(
                        id="Market-dropdown",
                        multi=True, ##To enable selection of multiple options multi=True is added.
                        options= [{"label": "Select All", "value": "all"}]+
                        [{"label":x, "value": x} for x in sorted(df["Market Name"].unique())],
                        value=["all"], ## This is the default selected which appears first on opening webpage.
                        style={"color":"blue"},
                        searchable=True, ## The user can select items from dropmenu by typing.
                        placeholder='Select a Market Name', ## This is what displays in dropdown menu when no item is selected.
                    ),
                ],
                width=3
            ), 
            dbc.Col([dbc.Label( ### This column has dropdown menu for selecting Commodity. 
                            "Select Commodity",
                            className="fw-bold",
                            style={"textAlign":"center","fontSize": 15, "display":"block"},
                            ),
                dcc.Dropdown(
                        id="Commodity",
                        multi=False, ### As in choropleth map, colour is displayed as per one item only.
                        options=[
                        {"label":x, "value": x} for x in sorted(df["Commodity"].unique())
                        ],
                        value="Apple",
                        style={"color":"blue"},
                        searchable=True,
                        placeholder='Select a Commodity'
                    ),
            ],
            width=3
            ),
            dbc.Col([dbc.Label( ### This column has start date selector. The user may wish to visualize data for one date or a range of date.
                            "Select Start Date:",
                            className="fw-bold",
                            style={"textAlign":"center","fontSize": 15, "display":"block"},
            ),
                dcc.DatePickerSingle(
                    id="start-date",
                    month_format='Do MMM, YYYY',
                    placeholder='Start Date',
                    date=df['Reported Date'].min().date(), #changing Timestamp (date with time) to date only
                    min_date_allowed = df['Reported Date'].min().date(),
                    max_date_allowed = df['Reported Date'].max().date(),
                    clearable=True,
                    stay_open_on_select=True,
                    style={"marginLeft":"50px"}
                    ),
                    ],
                    width=3
            ),
            dbc.Col([dbc.Label( ### This column has end date selector.
                            "Select End Date:",
                            className="fw-bold",
                            style={"textAlign":"justified","fontSize": 15, "display":"block"},
            ),
                dcc.DatePickerSingle(
                    id="end-date",
                    month_format='Do MMM, YYYY',
                    placeholder='End Date',
                    date=df['Reported Date'].max().date(), #changing Timestamp (date with time) to date only
                    min_date_allowed = df['Reported Date'].min().date(),
                    max_date_allowed = df['Reported Date'].max().date(),
                    clearable=True,
                    stay_open_on_select=True,
                    style={"marginLeft":"10px"}
                    ),
                    ],
                    width=3
            )
            ]

        ),
        dbc.Row( ##### In this row, map will be displayed.
            dbc.Col(
                dcc.Graph(id="choropleth-map", figure={})
            ),
        ),
        dbc.Row(
            dbc.Col(## This row is for radio buttons to choose one out of min, max, or modal price, or commodity arrival
                dbc.RadioItems(
                    id="output-indicator",
                    options=[{"label":"Minimum Price (Rs./Quintal)", "value": df.columns[-4]},
                           {"label":"Maximum Price (Rs./Quintal)", "value": df.columns[-3]},
                           {"label":"Modal Price (Rs./Quintal)", "value": df.columns[-2]},
                           {"label":"Arrivals (Tonnes)", "value": df.columns[-5]}],
                    value=df.columns[-2],
                    inline=True,
                    inputClassName="me-2",
                    style={"marginTop":"10px", "marginBottom":"10px"},
                    ),
            ),
        ),
        dbc.Row( ## This row is for radio buttons
            [dbc.Col(
                dbc.RadioItems( ## This column is for radio buttons to choose either line chart or bar chart
                    id="chart-indicator",
                    options=[{"label":"Line Chart", "value": "Line Chart"},
                           {"label":"Bar Chart", "value": "Bar Chart"},
                           ],
                    value="Bar Chart",
                    inline=True,
                    inputClassName="me-2",
                    style={"marginTop":"10px", "marginBottom":"10px"},
                    ),
            ),
            dbc.Col(
                dbc.RadioItems(## This column is for radio buttons to choose either line chart or bar chart
                    id="order-indicator",
                    options=[{"label":"Ascending order", "value":"total ascending"},
                           {"label":"Descending order", "value":"total descending"},
                           {"label":"Default order", "value":"trace"}
                           ],
                    value="trace",
                    inline=True,
                    inputClassName="me-2",
                    style={"marginTop":"10px", "marginBottom":"10px"},
                    ),
            ),
            ]
        ),
        dbc.Row( #### This row is for displaying graph in form of line chart or bar chart
            dbc.Col(
                dcc.Graph(id="graph", figure={}, style={'width': '100%', 'height': '95vh'})
            ),
        ),
        dbc.Row( ### In last row a url link to Agmarknet portal has been given
            dbc.Col(
                dcc.Link(id="Agmarknet",
                         children="Source of Data: Agmarknet portal, Govt. of India",
                         href="https://agmarknet.gov.in/",
                         target="_blank"
                         )
            )
        )
    ]  
)  

##### The Callback is where all magic happens. It is the Dash callback which enables user interactivity within the dashboard app.
#### The Dashback has two parts: the callback decorator and the callback function.

#### The "callback decorator" identifies the relevant components as prepared above in layout.
#### The "callback function" defines how those Dash components should interact.

# In callback decorator, there are two arguments: Output and Input. As many Output and as many Inputs are required accordingly they are placed in list.
#Output is the component that should change in reponse to the users's action on a different component (Input).
#Both Output and Input will include two arguments: One is the component id (which refers to "id" in dash components in app layout above) and second one referes to "value" chosen as default in layout.

# Below is the callback decorator "@app.callback()". It is mandatory that just below callback decorator, the callback function should be placed.
@app.callback( 
    [Output("chart-indicator", "options"),
    Output("order-indicator", "options"),
    Output("choropleth-map", "figure"),
    Output("graph", "figure"),
    ],
    [Input("Market-dropdown", "value"),
    Input("Commodity", "value"),
    Input("start-date", "date"),
    Input("end-date", "date"),
    Input("output-indicator", "value"),
    Input("chart-indicator", "value"),
    Input("order-indicator", "value")]
) ###### IMPORTANT: There must be no space between the decorator and the callback function. So, don't press enter key here please!!!
def update_graph(market, commodity, startDate, endDate, choice, chart, orderValue): ### Here, the callback function is being defined
    if market==["all"]: 
        market=sorted(df["Market Name"].unique()) #This is to select all market. Else, one or multiple market may be selected by user in dropdown menu.
    selected_dates = pd.date_range(start=startDate, end=endDate, freq='D') # date range has been selected by user
    filtered_df = df[df['Reported Date'].isin(selected_dates)] #filtering data as per user's selected date range
    filtered_df2 = filtered_df.loc[filtered_df['Market Name'].isin(market)] #filtering data as per user's se;ected market
    filtered_df3 = filtered_df2.loc[(df['Commodity'].isin([commodity]))] #filtering data as per user's selected commodity
    dff = filtered_df3.groupby(["Market Name", "Commodity"])[choice].mean().reset_index() #Finalised data. Grouping the data and taking mean value of price/arrival weight for representing on choropleth map and bar chart.
    dff_lineChart = filtered_df3.groupby(["Market Name", "Commodity", "Reported Date"])[choice].mean().reset_index()  #Grouping the data and taking mean value of price/arrival weight for representing on line chart.

    # Defining the choropleth map
    map = px.choropleth_mapbox(
        dff, #dataframe as finalised after filter based on user's selction
        geojson=gdf, #geodata frame or geojson file
        color=choice, #color as per the selected option: min, max, or modal price, or arrival weight of commodity
        mapbox_style="open-street-map", #acts as basemap. Need internet connection to download. It appears below shapefile.
        center = {"lat": 29.6, "lon": 78.9}, #This is the coordinates which will be centered for representation of map. The coordinate value has been so selected that whole Mandis of Uttarkhand appears.
        zoom=7,
        locations='Market Name', #That column name in dataframe which refers to location (same spelling as in shapefile attribute). So, it will depend on market(s) selected by user.
        hover_data={"Commodity":True}, #The data that will appear on hovering cursor over map.
        featureidkey="properties.TEHSIL") #### IMPORTANT: Boundaries of map to be shown. So, it will depend on shapefile. "TEHSIL" is one of the attribute in shapefile.
    map.update_layout(margin=dict(l=0.5, r=0.5, t=0.5, b=0.5))

    # The display of chart option changes with whether start and end date are same or different
    if startDate == endDate:
        chartOption = [{"label":"Bar Chart", "value": "Bar Chart"}]
    elif startDate!=endDate:
        chartOption = [{"label":"Line Chart", "value": "Line Chart"},
                           {"label":"Bar Chart", "value": "Bar Chart"},
                           ]
    
    #The display of sorting/ordering option (ascending, descending, or default) for bar chart
    if chart=="Bar Chart" or startDate==endDate:
        orderOption = [{"label":"Ascending order", "value":"total ascending"},
                           {"label":"Descending order", "value":"total descending"},
                           {"label":"Default order", "value":"trace"}
                           ]
    else:
        orderOption = []

    #Defining the Bar chart
    if chart=="Bar Chart" or startDate==endDate:
        chart = px.bar(
            data_frame=dff,
            x="Market Name",
            y=choice,
            hover_data=["Commodity"],
            text=choice
        )
        chart.update_traces(marker_color="purple",
                            texttemplate='%{text:.0f}', #Here {text:.0f} means text to be displayed as 0 digits after decimal and the number is in fullform not like 2k for 2000.
                            textposition='outside') #To place text above bar chart
        chart.update_layout(margin=dict(l=0.5, r=0.5, t=0.5, b=0.5), xaxis={'categoryorder':orderValue})
    elif chart=="Line Chart": #Defining the Line chart
        chart = px.line(
            data_frame=dff_lineChart,
            x="Reported Date",
            y=choice,
            color="Market Name",
            hover_data={"Commodity":True},
            log_y=False,
            labels={
                choice:choice,
                "Reported Date":"Date",
                "Market Name":"Market",
            },
        )
        chart.update_layout(hovermode='x unified',
                            margin=dict(l=0.5, r=0.5, t=0.5, b=0.5),
                            hoverlabel=dict(bgcolor="white",font_size=10))
    
    return chartOption, orderOption, map, chart # Four outputs as desired in the callback decorator.


if __name__ == "__main__":
    app.run_server(debug=False)
    
