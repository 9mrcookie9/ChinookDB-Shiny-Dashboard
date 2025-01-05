import os

import seaborn as sns
from IPython.core.display import GeoJSON
from faicons import icon_svg

# Import data from shared.py
import pathlib
import random

from ipyleaflet import GeoJSON, Map, Marker
from shiny import reactive
from shiny.express import input, render, ui
from shinywidgets import render_plotly, render_widget
import plotly.express as px

ui.page_opts(title="Chinook overview", fillable=True)

from shared import app_dir, artists_data, invoices_data, invoices_full_data, country_top10_data, genre_names_data, \
    genres_data, sales_genres_data, country_boundaries, orders_by_month_data, years_data


def random_color(feature):
    return {
        "color": "black",
        "fillColor": random.choice(["red", "yellow", "green", "orange"]),
    }


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
        with ui.card():
            @render_widget
            def map():
                map = Map(center=(50.2660531, 19.0224004), zoom=3)

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
                map.add_layer(geo_json)

                point = Marker(location=(50.2660531, 19.0224004), draggable=False)
                map.add_layer(point)

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
