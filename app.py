# Import data from shared.py
import random

import plotly.express as px
from IPython.core.display import GeoJSON
from faicons import icon_svg
from ipyleaflet import GeoJSON, Map, Popup
from ipywidgets import HTML
from shapely import MultiPolygon
from shapely.geometry import shape
from shiny import reactive
from shiny.express import input, render, ui
from shinywidgets import render_plotly, render_widget

ui.page_opts(title="Chinook overview", fillable=True)

from shared import app_dir, artists_data, invoices_data, invoices_full_data, country_top10_data, genre_names_data, \
    genres_data, sales_genres_data, country_boundaries, top_albums_data


def random_color(feature):
    return {
        "color": "black",
        "fillColor": random.choice(["red", "yellow", "green", "orange"]),
    }


def calculate_centroid(polygon_coordinates):
    polygon = shape({
        "type": "Polygon",
        "coordinates": polygon_coordinates
    })
    centroid = polygon.centroid
    return centroid.y, centroid.x


def calculate_multi_centroid(multi_polygon_coordinates):
    polygons = [shape({"type": "Polygon", "coordinates": coords}) for coords in multi_polygon_coordinates]
    multi_polygon = MultiPolygon(polygons)
    centroid = multi_polygon.centroid
    return centroid.y, centroid.x


with ui.sidebar(title="Filters"):
    ui.input_select("genres", "Select Genre", genre_names_data()['GenreName'].tolist(), multiple=True,
                    remove_button=True)
    ui.input_select("country", "Select Country", invoices_data['Country'].unique().tolist(), multiple=True,
                    remove_button=True)
    ui.input_action_button("reset", "Reset filters")

with ui.navset_card_pill(id="tab"):
    with ui.nav_panel("Overview"):
        with ui.layout_column_wrap(fill=False, gap="10px"):
            with ui.value_box(showcase=icon_svg("people-arrows")):
                "Total artists count"


                @render.text
                def count():
                    return artists_data.shape[0]

            with ui.value_box(showcase=icon_svg("flag")):
                "Total countries count"


                @render.text
                def count2():
                    return conutries_count().shape[0]

            with ui.value_box(showcase=icon_svg("music")):
                "Total genres count"


                @render.text
                def count3():
                    return genre_names_data().shape[0]

        with ui.layout_columns():
            with ui.card():
                ui.card_header("Sales by Genree")


                @render_plotly
                def plot_genre():
                    fig = px.histogram(
                        top_invoices_by_country(),
                        x="GenreName",
                        y="PurchaseCount",
                        labels={"GenreName": "Genre", "PurchaseCount": "purchase"},
                        text_auto=False,

                    )
                    return fig
            with ui.card():
                ui.card_header("Sales by Country")


                @render_plotly
                def plot_country():
                    fig = px.histogram(
                        country_top10_data,
                        x="Country",
                        y="PurchaseCount",
                        labels={"Country": "Country", "PurchaseCount": "purchase"},
                        text_auto=False,

                    )
                    return fig

    with ui.nav_panel("Map"):
        with ui.card():
            @render_widget
            def map():
                map = Map(center=(50.2660531, 19.0224004), zoom=3, close_popup_on_click=True)

                geo_json = GeoJSON(
                    data=country_boundaries,
                    style={
                        "opacity": 1,
                        "dashArray": "9",
                        "fillOpacity": 0.1,
                        "weight": 1,
                    },
                    hover_style={"color": "white", "dashArray": "0", "fillOpacity": 0.5},
                    style_callback=random_color,
                )
                popup_content = HTML()
                popup = Popup(
                    child=popup_content,
                    close_button=True,
                    auto_close=False,
                    auto_pan=False,
                    close_on_escape_key=False
                )

                def on_click_handler(event, feature, **kwargs):
                    print(kwargs)
                    country = feature['properties']['name']
                    if country=="United States of America":
                        country="USA"

                    top_albums = top_albums_data(country)

                    album_list = "<br>".join(
                        [f"{row['AlbumTitle']} ({row['PurchaseCount']} sales)" for _, row in top_albums.iterrows()]
                    ) if not top_albums.empty else "No data available"

                    coordinates = feature['geometry']['coordinates']
                    if feature['geometry']['type'] == 'Polygon':
                        centroid_lat, centroid_lon = calculate_centroid(coordinates)
                    elif feature['geometry']['type'] == 'MultiPolygon':
                        centroid_lat, centroid_lon = calculate_multi_centroid(coordinates)

                    popup.location = (centroid_lat, centroid_lon)
                    popup_content.value = f"<h3>{country}</h3><p>{album_list}</p>"
                    popup.open_popup()

                geo_json.on_click(on_click_handler)

                map.add(popup)
                map.add(geo_json)

                return map

    with ui.nav_panel("Data source"):
        with ui.card(full_screen=True):
            ui.card_header("Invoices")


            @render.data_frame
            def summary_statistics():
                return render.DataGrid(filtered_invoices_full_data(), filters=True)


@reactive.calc
def filtered_artists_data():
    return artists_data


@reactive.calc
def filtered_invoices_data():
    filt_df = invoices_data[invoices_data["Country"].isin(input.country())]
    return filt_df


@reactive.calc
def top_invoices_by_country():
    if len(input.genres()) > 0 or len(input.country()) > 0:
        data = sales_genres_data()
        if len(input.genres()) > 0:
            data = data[data["GenreName"].isin(input.genres())]
        if len(input.country()) > 0:
            data = data[data["Country"].isin(input.country())]
        return data.head(6)
    data = genres_data()
    return data.head(6)


def conutries_count():
    return invoices_data['Country'].value_counts()


@reactive.calc
def filtered_invoices_full_data():
    if len(input.country()) > 0:
        filt_df = invoices_full_data[invoices_full_data["BillingCountry"].isin(input.country())]
    else:
        filt_df = invoices_full_data
    return filt_df


ui.include_css(app_dir / "styles.css")


@reactive.effect
@reactive.event(input.reset)
def _():
    ui.update_select("genres", selected=[])
    ui.update_select("country", selected=[])
