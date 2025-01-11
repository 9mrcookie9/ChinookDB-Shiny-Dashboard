# Import data from shared.py
import random

import numpy as np
import plotly.express as px
from IPython.core.display import GeoJSON
from branca.colormap import LinearColormap
from faicons import icon_svg
from ipyleaflet import GeoJSON, Map, Popup, WidgetControl
from ipywidgets import HTML
from shapely import MultiPolygon
from shapely.geometry import shape
from shiny import reactive
from shiny.express import input, render, ui
from shinywidgets import render_plotly, render_widget

ui.page_opts(title="Chinook overview", fillable=True)

from shared import genre_names_data, invoices_data, years_data, artists_data, country_top10_data, orders_by_month_data, \
    sales_by_country, sales_revenue_genres_data, top_albums_data, sales_genres_data, genres_data, invoices_full_data, \
    app_dir


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

def calculate_centroid_or_multi_centroid(coordinates, geometry_type):
    if geometry_type == 'Polygon':
        return calculate_centroid(coordinates)
    elif geometry_type == 'MultiPolygon':
        return calculate_multi_centroid(coordinates)
    else:
        raise ValueError("Unsupported geometry type: {}".format(geometry_type))


with ui.sidebar(title="Filters"):
    ui.input_select("genres", "Select Genre", genre_names_data()['GenreName'].tolist(), multiple=True,
                    remove_button=True)
    ui.input_select("country", "Select Country", invoices_data['Country'].unique().tolist(), multiple=True,
                    remove_button=True)
    ui.input_select("year", "Select Year", years_data()['Year'].tolist(), multiple=False)
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

        with ui.layout_columns():
            with ui.card():
                ui.card_header("Sales by Month")


                @render_plotly
                def plot_time():
                    selected_year = input.year()
                    filtered_data = orders_by_month_data[orders_by_month_data['MonthYear'].str.endswith(selected_year)]
                    fig = px.line(
                        filtered_data,
                        x="MonthYear",
                        y="PurchaseCount",
                        labels={"MonthYear": "Month-Year", "PurchaseCount": "Sum of purchases"},
                        markers=False,

                    )
                    return fig

    with ui.nav_panel("Map"):
        def get_filtered_sales_data(selected_genres, selected_countries):
            filtered_sales_data = sales_by_country()

            if selected_genres:
                genre_sales_data = sales_revenue_genres_data()
                filtered_sales_data = genre_sales_data[genre_sales_data['GenreName'].isin(selected_genres)]
                if selected_countries:
                    filtered_sales_data = filtered_sales_data[filtered_sales_data['Country'].isin(selected_countries)]
                else:
                    selected_countries = filtered_sales_data['Country'].unique().tolist()
            elif selected_countries:
                filtered_sales_data = filtered_sales_data[filtered_sales_data['Country'].isin(selected_countries)]
            return filtered_sales_data, selected_countries


        def get_sales_range(filtered_sales_data):
            if filtered_sales_data.empty:
                return 0, 0
            print(filtered_sales_data['Revenue'])
            return filtered_sales_data['Revenue'].max(), filtered_sales_data['Revenue'].min()


        def create_colormap(min_sales, max_sales):
            return LinearColormap(
                colors=['darkblue', 'blue', 'cyan', 'yellow', 'orange', 'red'],
                index=np.round(np.linspace(min_sales, max_sales, num=5)).astype(int),
                vmin=round(min_sales),
                vmax=round(max_sales),
                caption='Total Sales Count'
            )


        def get_country_color(country, filtered_sales_data, colormap):
            sales_count = filtered_sales_data[filtered_sales_data['Country'] == country]['Revenue'].values
            return colormap(sales_count[0]) if len(sales_count) > 0 else '#d3d3d3'


        def create_map(filtered_sales_data, colormap, country_boundaries, selected_genres):
            map = Map(center=(50.2660531, 19.0224004), zoom=3, close_popup_on_click=True)
            popup_content = HTML()
            popup = Popup(child=popup_content, close_button=True, auto_close=True, auto_pan=False,
                          close_on_escape_key=False)

            def style_function(feature):
                country = feature['properties']['name']
                country = "USA" if country == "United States of America" else country
                is_highlighted = not filtered_sales_data[filtered_sales_data['Country'] == country].empty
                return {
                    'fillColor': get_country_color(country, filtered_sales_data, colormap),
                    'color': 'black',
                    'weight': 1,
                    'fillOpacity': 0.7,
                    'clickable': is_highlighted
                }

            geo_json = GeoJSON(
                data=country_boundaries,
                style_callback=style_function,
                hover_style={'fillColor': 'white', 'fillOpacity': 0.5},
            )

            def on_click_handler(event, feature, **kwargs):
                country = feature['properties']['name']
                country = "USA" if country == "United States of America" else country
                if filtered_sales_data[filtered_sales_data['Country'] == country].empty:
                    return
                top_albums = top_albums_data(country, selected_genres)
                country_revenue = filtered_sales_data[filtered_sales_data['Country'] == country]['Revenue'].sum()
                album_list = "<br>".join(
                    [f"<b>{row['AlbumTitle']}</b> (${row['Revenue']:.2f} revenue)" for _, row in top_albums.iterrows()]
                ) if not top_albums.empty else "No data available"

                coordinates = feature['geometry']['coordinates']
                centroid_lat, centroid_lon = calculate_centroid_or_multi_centroid(coordinates,
                                                                                  feature['geometry']['type'])

                popup.location = (centroid_lat, centroid_lon)
                popup_content.value = f"""<h3>{country} <br> Total Revenue - ${country_revenue:.2f}</h3>
                                          <p>Top 3 Albums:<br> {album_list}</p>"""
                popup.open_popup()

            geo_json.on_click(on_click_handler)

            map.add(popup)
            map.add(geo_json)

            colorbar_html = HTML()
            colorbar_html.value = colormap._repr_html_()
            colorbar_control = WidgetControl(widget=colorbar_html, position="bottomright")
            map.add_control(colorbar_control)

            return map

        @render_widget
        def map():
            selected_genres = input.genres()
            selected_countries = input.country()

            filtered_sales_data, selected_countries = get_filtered_sales_data(selected_genres, selected_countries)
            max_sales, min_sales = get_sales_range(filtered_sales_data)
            colormap = create_colormap(min_sales, max_sales)

            return create_map(filtered_sales_data, colormap, country_boundaries, selected_genres)
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
