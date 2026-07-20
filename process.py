import glob
import pandas as pd
from unidecode import unidecode
import dash
from dash import html
from dash import dcc
from dash import dash_table, html, dcc, Input, Output
import dash_bootstrap_components as dbc
import plotly.express as px
import re
from datetime import datetime
import json
from urllib.request import urlopen
import plotly.graph_objects as go
from data.types import QuestionClassificationResult
import utils.classify_question, utils.extract_vote_value

# --- Configuration ---
INPUT_FILE = './data/referendums/held_referendums_with_coords.csv'  # Input file with referendums data with coords

# Load your dataframe here (replace with your actual data loading logic)
df_geo = pd.read_csv(INPUT_FILE)

# Print lines with missing coordinates (= 0)
# print(df_geo[df_geo['city_latitude'].isna() | df_geo['city_longitude'].isna()][['lokalita', 'geo_city']])

df_geo['vitr_fin'] = pd.Series(df_geo['otazka']).apply(unidecode).str.contains('vitr|vetrn').map(lambda x: True if x == True else False)
df_geo['result'] = df_geo.apply(lambda x: "Platné (vítr)" if x['vitr_fin'] == True and x['platnost_fin'] == "ANO"
                      else "Platné (jiné)" if x['vitr_fin'] == False and x['platnost_fin'] == "ANO"
                      else "Neplatné (vítr)" if x['vitr_fin'] == True and x['platnost_fin'] == "NE"
                      else "Neplatné (jiné)", axis=1)

df_grouped = df_geo
df_grouped = df_grouped.astype({"rok_fin": "category", "platnost_fin": "category", "result": "category"})

# Get all unique category combinations
rok_categories = df_grouped['rok_fin'].cat.categories
platnost_categories = df_grouped['platnost_fin'].cat.categories
result_categories = df_grouped['result'].cat.categories

# Create a MultiIndex for all possible combinations
multi_index = pd.MultiIndex.from_product(
    [rok_categories, platnost_categories],
    names=['rok_fin', 'platnost_fin']
)

# Group, count, and reindex to include all combinations
pocet_series = (
    df_grouped.groupby(['rok_fin', 'platnost_fin'])
    .size()
    .reindex(multi_index, fill_value=0)
    .reset_index(name='pocet')
)

# Repeat for 'result' and merge
result_multi_index = pd.MultiIndex.from_product(
    [rok_categories, result_categories],
    names=['rok_fin', 'result']
)
pocet_result_series = (
    df_grouped.groupby(['rok_fin', 'result'])
    .size()
    .reindex(result_multi_index, fill_value=0)
    .reset_index(name='pocet_result')
)

# Merge back into the original DataFrame
df_grouped = df_grouped.merge(
    pocet_series,
    on=['rok_fin', 'platnost_fin'],
    how='right'
).merge(
    pocet_result_series,
    on=['rok_fin', 'result'],
    how='right'
)

# Fill NaN (from missing counts) with 0
df_grouped[['pocet', 'pocet_result']] = df_grouped[['pocet', 'pocet_result']].fillna(0)
print(df_grouped[['rok_fin', 'platnost_fin', 'vitr_fin', 'result', 'pocet_result']].head(50))

# Create a copy of the filtered DataFrame (vitr_fin=True)
df_filtered = df_grouped[df_grouped['vitr_fin'] == True].copy()

# --- Column Renaming and Reordering ---
df_filtered = df_filtered.rename(columns={
    "rok_fin": "rok",
    "otazka": "otázka",
    "opravnene_osoby": "opr. osob (#)",
    "ucast": "účast (%)",
    "pro": "pro",
    "proti": "proti",
    "result": "platnost",
    "obec_fin": "obec",
    "kraj_fin": "kraj"
})
    
# Classify each question
df_filtered["question_type"]: pd.Series[QuestionClassificationResult] = df_filtered["otázka"].apply(utils.classify_question) # type: ignore


# Determine traffic light color
def get_semafor(row):
    # Extract numeric values for "pro" and "proti"
    pro = utils.extract_vote_value(row["pro"], extract_type="count")
    proti = utils.extract_vote_value(row["proti"], extract_type="count")

    if row["question_type"] == QuestionClassificationResult["pro_turbines"]:
        if row["platnost"] == "Platné (vítr)":
            return "💚" if pro > proti else "💔"
        else:
            return "💛"  # Valid question but invalid referendum
    elif row["question_type"] == QuestionClassificationResult["anti_turbines"]:
        if row["platnost"] == "Platné (vítr)":
            return "💔" if pro > proti else "💛"  # Oppose question: "pro" = support opposition
        else:
            return "💛"  # Oppose question but invalid referendum
    else:
        return "⚪"  # Edge case (unclear)

df_filtered["semafor"] = df_filtered.apply(get_semafor, axis=1)

# --- Load and convert GeoJSON files ---
def convert_geometry_collection_to_feature(collection_data, properties=None):
    """Convert a GeometryCollection to a FeatureCollection"""
    if properties is None:
        properties = {}

    features = []
    for geometry in collection_data.get("geometries", []):
        features.append({
            "type": "Feature",
            "geometry": geometry,
            "properties": properties.copy()
        })

    return {
        "type": "FeatureCollection",
        "features": features
    }


# --- Load and convert GeoJSON files ---
# Czech Republic outline
try:
    with open("./data/polygons/czechia.geojson", 'r', encoding='utf-8') as f:
        czechia_geojson = json.load(f)
        # If it's a GeometryCollection, convert it to FeatureCollection
        if czechia_geojson.get("type") == "GeometryCollection":
            czechia_geojson = {
                "type": "FeatureCollection",
                "features": [{
                    "type": "Feature",
                    "geometry": czechia_geojson,
                    "properties": {}
                }]
            }
except Exception as e:
    print(f"Error loading Czechia outline: {e}")
    czechia_geojson = {"type": "FeatureCollection", "features": []}

# District outlines
districts_geojson = {"type": "FeatureCollection", "features": []}
district_files = glob.glob("./data/polygons/districts/*.geojson")

if not district_files:
    print("Warning: No district GeoJSON files found")
else:
    for district_file in district_files:
        try:
            with open(district_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

                # Handle GeometryCollection
                if data.get("type") == "GeometryCollection":
                    district_name = district_file.split('/')[-1].replace('.geojson', '')
                    districts_geojson["features"].append({
                        "type": "Feature",
                        "geometry": data,
                        "properties": {"name": district_name}
                    })
                elif data.get("type") == "FeatureCollection":
                    for feature in data.get("features", []):
                        if "properties" not in feature:
                            feature["properties"] = {}
                        feature["properties"]["name"] = district_file.split('/')[-1].replace('.geojson', '')
                    districts_geojson["features"].extend(data.get("features", []))
                elif data.get("type") == "Feature":
                    if "properties" not in data:
                        data["properties"] = {}
                    data["properties"]["name"] = district_file.split('/')[-1].replace('.geojson', '')
                    districts_geojson["features"].append(data)
        except Exception as e:
            print(f"Error loading {district_file}: {e}")

print(f"Loaded {len(districts_geojson['features'])} district features")

# --- Prepare data ---
df = df_filtered.copy()
df = df.dropna(subset=["city_latitude", "city_longitude"])

# Create color mapping for semafor
color_map = {
    "💚": "green",
    "💔": "red",
    "💛": "orange",
    "⚪": "gray"
}

# --- Create the map using go.Figure ---
fig = go.Figure()

# Add scatter plot for points
fig.add_trace(go.Scattermapbox(
    lat=df["city_latitude"],
    lon=df["city_longitude"],
    mode="markers",
    marker=go.scattermapbox.Marker(
        size=10,
        color=[color_map.get(s, "gray") for s in df["semafor"]],
        opacity=0.8
    ),
    hovertext=df["obec"],
    hoverinfo="text",
    customdata=df[["rok", "otázka", "platnost", "pro", "proti", "účast (%)"]],
    hovertemplate="<b>%{hovertext}</b><br><br>" +
                  "Rok: %{customdata[0]}<br>" +
                  "Otázka: %{customdata[1]}<br>" +
                  "Platnost: %{customdata[2]}<br>" +
                  "Pro: %{customdata[3]} | Proti: %{customdata[4]}<br>" +
                  "Účast: %{customdata[5]}<br>" +
                  "Výsledek: %{marker.color}<extra></extra>"
))

# Add Czechia outline if available
if czechia_geojson.get("features"):
    fig.add_trace(go.Choroplethmapbox(
        geojson=czechia_geojson,
        locations=[0],  # Dummy location
        z=[1],  # Dummy value
        colorscale=[[0, '#666666'], [1, '#666666']],
        showscale=False,
        marker_opacity=1,
        marker_line_width=2,
        hoverinfo="skip"
    ))

# Add district boundaries if available
if districts_geojson.get("features"):
    fig.add_trace(go.Choroplethmapbox(
        geojson=districts_geojson,
        locations=[0],  # Dummy location
        z=[1],  # Dummy value
        colorscale=[[0, '#999999'], [1, '#999999']],
        showscale=False,
        marker_opacity=1,
        marker_line_width=1,
        hoverinfo="skip"
    ))

# Update layout
fig.update_layout(
    mapbox_style="carto-positron",
    mapbox_center={"lat": 49.8175, "lon": 15.4730},
    mapbox_zoom=7,
    margin={"r":0,"t":0,"l":0,"b":0},
    height=600
)


# --- Calculate Stats ---
current_year = datetime.now().year
total_referendums = len(df_geo)
wind_referendums = len(df_filtered)

# Proportion of wind referendums (easier to interpret)
wind_proportion = wind_referendums / total_referendums if total_referendums > 0 else 0
recent_years = df_geo[df_geo["rok_fin"] >= (current_year - 5)]
recent_wind_referendums = df_filtered[df_filtered["rok"] >= (current_year - 5)]
recent_proportion = len(recent_wind_referendums) / len(recent_years) if len(recent_years) > 0 else 0

# Percentage change in proportion
pct_change = ((recent_proportion - wind_proportion) / wind_proportion) * 100 if wind_proportion > 0 else 0
trend_word = "rose" if pct_change > 0 else "fell"
trend_emoji = "↗️" if pct_change > 0 else "↘️"

# For display: "X in 10" format
wind_per_10 = wind_proportion * 10
recent_per_10 = recent_proportion * 10

# --- Summary Card ---
summary_card = dbc.Card(
    dbc.CardBody([
        html.Div([
            html.H4("Wind Referendums in Czechia", className="card-title"),
            html.P([
                f"About ",
                html.Span(f"{wind_per_10:.1f} in 10", style={"fontWeight": "bold", "fontSize": "1.2em", "color": "#28a745"}),
                " local referendums so far were about wind energy. ",
                f"This share {trend_word} by ",
                html.Span(f"{abs(pct_change):.1f}%", style={"fontWeight": "bold", "color": "#28a745" if pct_change > 0 else "#dc3545"}),
                f" {trend_emoji} in the last 5 years (now ",
                html.Span(f"{recent_per_10:.1f} in 10", style={"fontWeight": "bold"}),
                ")."
            ]),
            html.Hr(),
            html.H5("How to Read the Traffic Light (Semafor):", className="mt-3"),
            html.Ul([
                html.Li([
                    html.Span("💚 ", style={"fontSize": "1.2em"}),
                    "Green light: The referendum supports wind turbines, is valid, and majority voted 'yes'."
                ]),
                html.Li([
                    html.Span("💔 ", style={"fontSize": "1.2em"}),
                    "Red light: The referendum opposes turbines or a valid vote rejected them."
                ]),
                html.Li([
                    html.Span("💛 ", style={"fontSize": "1.2em"}),
                    "Yellow light: Unclear outcome (e.g., invalid referendum or mixed signals)."
                ]),
            ], className="mb-0"),
            html.P([
                "We classify each referendum by its ",
                html.I("question phrasing"),
                ", ",
                html.I("validity"),
                ", and ",
                html.I("vote result"),
                ". ",
                html.A("Learn more", id="learn-more-link", href="#", style={"textDecoration": "none", "color": "#007bff"}),
                " about the methodology."
            ], className="small text-muted"),
        ], className="p-3")
    ]),
    className="mb-4 shadow-sm",
    style={"borderLeft": "4px solid #28a745"}
)

# Sort by "rok" descending (2025 → 2024 → ...)
df_filtered = df_filtered.sort_values(['platnost', 'nr'], ascending=[False, False])

# Add index column "ind" (1-based)
df_filtered.insert(0, "ind", range(1, len(df_filtered) + 1))

# Multiply "účast (%)" by 100 and add "%"
# Convert to numeric first (in case it's a string or object)
df_filtered["účast (%)"] = pd.to_numeric(df_filtered["účast (%)"], errors='coerce')

# Multiply by 100, round to 2 decimal places, and add "%"
df_filtered["účast (%)"] = (df_filtered["účast (%)"] * 100).round(2).astype(str) + " %"

# Select and reorder columns (excluding "_T" columns and including specified ones)
cols_order = [
    "ind", "rok", "semafor", "otázka", "opr. osob (#)", "účast (%)",
    "pro", "proti", "platnost", "obec", "kraj"
]
df_filtered = df_filtered[cols_order]

print(dash.__version__)
print(x)
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.ZEPHYR])
app.title = "...2"

# --- Define Filters (Dropdowns for "kraj" and "platnost") ---
rok_options = [{"label": rok, "value": rok} for rok in df_filtered["rok"].unique()]
kraj_options = [{"label": kraj, "value": kraj} for kraj in df_filtered["kraj"].unique()]
result_options = [{"label": res, "value": res} for res in df_filtered["platnost"].unique()]

app.layout = html.Div(
    id="app-container",
    children=[
        html.H1("Wind Turbine Referendums in Czechia"),
        dbc.Row(summary_card),
        dcc.Graph(
            id="map",
            figure=fig,
            style={"height": "600px"}
        ),
        # Legend
        html.Div([
            html.Div([
                html.Span("💚", style={"color": "green", "fontSize": "20px"}),
                " Podporuje (platné)"
            ]),
            html.Div([
                html.Span("💔", style={"color": "red", "fontSize": "20px"}),
                " Odmítá (platné)"
            ]),
            html.Div([
                html.Span("💛", style={"color": "orange", "fontSize": "20px"}),
                " Neplatné/nejasné"
            ])
        ], style={
            "position": "absolute",
            "bottom": "20px",
            "right": "20px",
            "zIndex": 1000,
            "backgroundColor": "white",
            "padding": "10px",
            "borderRadius": "5px",
            "boxShadow": "0 0 10px rgba(0,0,0,0.2)"
        }),
        dcc.Graph(figure=px.line(df_grouped.sort_values(['rok_fin', 'platnost_fin']), x="rok_fin", y="pocet", color="platnost_fin", title="...")),
        dcc.Graph(figure=px.line(df_grouped.sort_values(['rok_fin', 'result']), x="rok_fin", y='pocet_result', color="result", title="...",
             color_discrete_map={
                 "Average": "#456987",
                 "Raw": "#147852"
             })),
        dbc.Row([
            dbc.Col([
                html.Label("Filter by Rok:"),
                dcc.Dropdown(
                    id="rok-filter",
                    options=rok_options,
                    multi=True,
                    placeholder="Select roky..."
                )
            ], width=4),
            dbc.Col([
                html.Label("Filter by Kraj:"),
                dcc.Dropdown(
                    id="kraj-filter",
                    options=kraj_options,
                    multi=True,
                    placeholder="Select kraje..."
                )
            ], width=4),
            dbc.Col([
                html.Label("Filter by Platnost:"),
                dcc.Dropdown(
                    id="result-filter",
                    options=result_options,
                    multi=True,
                    placeholder="Select platnost..."
                )
            ], width=4),
        ], className="mb-4"),

        dash_table.DataTable(
            id="table",
            columns=[
                {"name": " ", "id": "ind"},  # Index column
                {"name": "ROK", "id": "rok"},
                {"name": "SEMAFOR", "id": "semafor"},
                {"name": "OTÁZKA", "id": "otázka"},
                {"name": "OPR. OSOB (#)", "id": "opr. osob (#)"},
                {"name": "ÚČAST (%)", "id": "účast (%)"},
                {"name": "PRO", "id": "pro"},
                {"name": "PROTI", "id": "proti"},
                {"name": "PLATNOST", "id": "platnost"},
                {"name": "OBEC", "id": "obec"},
                {"name": "KRAJ", "id": "kraj"}
            ],
            data=df_filtered.to_dict("records"),
            page_size=100,  # Paging after 100 records (hidden if <100 rows)

            # --- Styling ---
            style_data_conditional=[
                # Light gray for "Neplatné (vítr)" rows
                {
                    "if": {"filter_query": '{platnost} = "Neplatné (vítr)"'},
                    "backgroundColor": "#F8F9FA",  # Very light gray
                },
                # Light green/red for platnost (True/False)
                {
                    "if": {"filter_query": '{platnost} = "Platné (vítr)"', "column_id": "platnost"},
                    "backgroundColor": "#D4EDDA",
                },
                {
                    "if": {"filter_query": '{platnost} = "Neplatné (vítr)"', "column_id": "platnost"},
                    "backgroundColor": "#F8D7DA",
                },
            ],
            style_cell_conditional=[
                # Style for "otázka" (bold, 12px, etc.)
                {
                    "if": {"column_id": "otázka"},
                    "fontWeight": "bold",
                    "fontSize": "12px",
                    "textAlign": "left",
                    "width": "500px",
                    "minWidth": "500px",
                    "maxWidth": "500px",
                    "whiteSpace": "normal",
                    "height": "auto"
                },
                # Default style for ALL OTHER COLUMNS (11px, left-aligned)
                *[
                    {
                        "if": {"column_id": col},
                        "fontSize": "11px",
                        "textAlign": "center",
                        "verticalAlign": "middle"
                    }
                    for col in df_filtered.columns
                    if col != "otázka"  # Exclude "otázka"
                ],
                # Fixed widths for specific columns
                {"if": {"column_id": "ind"}, "width": "50px", "minWidth": "50px", "maxWidth": "50px"}
            ],
            style_header={
                "backgroundColor": "rgb(230, 230, 230)",
                "fontWeight": "bold",
                "textAlign": "center",
            },
            style_table={"overflowX": "auto"},
            style_data={"whiteSpace": "normal", "height": "auto"},

            # --- Features ---
            sort_action="none",  # Disable sorting
            filter_action="none",  # Disable column filtering
        )
    ]
)


# --- Callback for Filtering ---
@app.callback(
    Output("table", "data"),
    [Input("rok-filter", "value"), Input("kraj-filter", "value"), Input("result-filter", "value")]
)
def update_table(rok_selected, kraj_selected, result_selected):
    filtered_df = df_filtered
    if rok_selected:
        filtered_df = filtered_df[filtered_df["rok"].isin(rok_selected)]
    if kraj_selected:
        filtered_df = filtered_df[filtered_df["kraj"].isin(kraj_selected)]
    if result_selected:
        filtered_df = filtered_df[filtered_df["platnost"].isin(result_selected)]
    return filtered_df.to_dict("records")

if __name__ == "__main__":
    app.run(debug=True)

