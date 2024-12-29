import os
import json
import sqlite3
from pathlib import Path

import pandas as pd

app_dir = Path(__file__).parent
data = pd.read_csv(app_dir / "tips.csv")

# Ścieżka do bazy danych
DB_PATH = os.path.join(app_dir, 'data', 'chinook.db')
COUNTRIES_GEO = os.path.join(app_dir, 'data', 'countries.geo.json')
# Zapytania SQL
ARTISTS_QUERY = """
    SELECT artists.Name AS ArtistName, COUNT(tracks.TrackId) AS SongCount, 
           SUM(invoice_items.Quantity) AS TotalPurchases
    FROM artists
    JOIN albums ON artists.ArtistId = albums.ArtistId
    JOIN tracks ON albums.AlbumId = tracks.AlbumId
    LEFT JOIN invoice_items ON tracks.TrackId = invoice_items.TrackId
    GROUP BY artists.ArtistId
    ORDER BY TotalPurchases DESC;
"""

INVOICES_QUERY = """
    SELECT BillingCountry AS Country, COUNT(*) AS PurchaseCount
    FROM invoices
    GROUP BY BillingCountry
    ORDER BY PurchaseCount DESC;
"""

INVOICES_FULL_QUERY = """
    SELECT invoices.InvoiceId, invoices.InvoiceDate, invoices.Total, invoice_items.UnitPrice as UnitPrice , invoices.BillingCountry, customers.FirstName, customers.LastName, customers.Email, tracks.Name as TrackName
    FROM invoices
    LEFT JOIN invoice_items ON invoice_items.InvoiceId = invoices.InvoiceId
    LEFT JOIN tracks ON tracks.TrackId = invoice_items.TrackId
    LEFT JOIN customers ON invoices.CustomerId = Customers.CustomerId
    ORDER BY invoices.InvoiceId DESC;
"""

GENRES_QUERY = """
    SELECT genres.Name AS GenreName, COUNT(invoice_items.TrackId) AS PurchaseCount
    FROM genres
    JOIN tracks ON genres.GenreId = tracks.GenreId
    JOIN invoice_items ON tracks.TrackId = invoice_items.TrackId
    JOIN invoices ON invoice_items.InvoiceId = invoices.InvoiceId
    GROUP BY genres.GenreId
    ORDER BY PurchaseCount DESC;
"""

SALES_BY_GENRE_QUERY = """
    SELECT genres.Name AS GenreName, COUNT(invoice_items.TrackId) AS PurchaseCount, invoices.BillingCountry as Country
    FROM genres
    JOIN tracks ON genres.GenreId = tracks.GenreId
    JOIN invoice_items ON tracks.TrackId = invoice_items.TrackId
    JOIN invoices ON invoice_items.InvoiceId = invoices.InvoiceId
    GROUP BY BillingCountry, GenreName
    ORDER BY PurchaseCount DESC;
"""

GENRE_NAMES_QUERY = """
    SELECT genres.Name AS GenreName
    FROM genres
"""

COUNTRY_TOP10_QUERY = """
    SELECT BillingCountry AS Country, COUNT(*) AS PurchaseCount
    FROM invoices
    GROUP BY BillingCountry
    ORDER BY PurchaseCount DESC
    LIMIT 5;
"""

# Funkcja do pobierania danych z bazy danych
def fetch_data(query):
    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql_query(query, conn)

with open(COUNTRIES_GEO, "r") as f:
    country_boundaries = json.load(f)


# Pobranie danych
artists_data = fetch_data(ARTISTS_QUERY)
invoices_data = fetch_data(INVOICES_QUERY)
invoices_full_data = fetch_data(INVOICES_FULL_QUERY)
def genres_data():
    return fetch_data(GENRES_QUERY)
def sales_genres_data():
    return fetch_data(SALES_BY_GENRE_QUERY)
def genre_names_data():
    return fetch_data(GENRE_NAMES_QUERY)
country_top10_data = fetch_data(COUNTRY_TOP10_QUERY)
