import tkinter as tk
from tkinter import messagebox
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pymongo import MongoClient
import threading
db = None
collection = None
df = None
def init_resources():
    global db, collection, df
    try:
        client = MongoClient(
            "mongodb://localhost:27017/",
            serverSelectionTimeoutMS=2000
        )
        db = client["movie_recommender"]
        collection = db["history"]
    except Exception as e:
        print("MongoDB not connected:", e)
    try:
        df = pd.read_csv("movies.csv")
        df["genre"] = df["genres"].apply(
            lambda x: x.split("|")[0] if pd.notna(x) else "Unknown"
        )
        df["rating"] = 8.0
        df = df[["title", "genre", "rating"]]
    except Exception as e:
        print("Dataset loading error:", e)
def recommend_movies():
    genre = genre_entry.get()
    fav_movie = fav_entry.get()
    rating_val = rating_entry.get()
    threading.Thread(
        target=process_recommendation,
        args=(genre, fav_movie, rating_val)
    ).start()
def process_recommendation(genre, fav_movie, rating_val):
    global df, collection
    if df is None:
        root.after(
            0,
            lambda: messagebox.showerror(
                "Error",
                "movies.csv file not found!"
            )
        )
        return
    try:
        min_rating = float(rating_val)
    except ValueError:
        root.after(
            0,
            lambda: messagebox.showerror(
                "Error",
                "Enter valid rating"
            )
        )
        return
    filtered = df[
        (df["genre"].str.lower() == genre.lower()) &
        (df["rating"] >= min_rating)
    ]
    if filtered.empty:
        root.after(0, update_result_box, "No movies found!")
        return
    if fav_movie:
        fav_row = df[df["title"].str.lower() == fav_movie.lower()]
        if not fav_row.empty:
            fav_rating = fav_row.iloc[0]["rating"]
            ratings = filtered["rating"].values
            similarity = 1 / (1 + np.abs(ratings - fav_rating))
            filtered = filtered.copy()
            filtered["similarity"] = similarity
            filtered = filtered.sort_values(
                by="similarity",
                ascending=False
            )
    recommendations = filtered["title"].head(10).tolist()
    root.after(0, update_result_box, "\n".join(recommendations))
    if collection is not None:
        try:
            collection.insert_one({
                "genre": genre,
                "min_rating": min_rating,
                "favorite_movie": fav_movie,
                "recommendations": recommendations
            })
        except Exception as e:
            print("MongoDB insertion error:", e)
    root.after(0, show_plot, filtered)
def update_result_box(text):
    result_box.config(state="normal")
    result_box.delete("1.0", tk.END)
    result_box.insert(tk.END, text)
    result_box.config(state="disabled")
def show_plot(filtered):
    plt.figure(figsize=(6, 4))
    plt.hist(filtered["rating"], bins=5)
    plt.title("Movie Rating Distribution")
    plt.xlabel("Rating")
    plt.ylabel("Count")
    plt.show()
root = tk.Tk()
root.title("Movie Recommendation System")
root.geometry("500x550")
threading.Thread(target=init_resources).start()
# Title
tk.Label(
    root,
    text="Movie Recommendation System",
    font=("Arial", 16, "bold")
).pack(pady=10)
# Genre
tk.Label(root, text="Preferred Genre").pack()
genre_entry = tk.Entry(root, width=30)
genre_entry.pack(pady=5)
# Rating
tk.Label(root, text="Minimum Rating").pack()
rating_entry = tk.Entry(root, width=30)
rating_entry.pack(pady=5)
# Favorite Movie
tk.Label(root, text="Favorite Movie").pack()
fav_entry = tk.Entry(root, width=30)
fav_entry.pack(pady=5)
# Button
tk.Button(
    root,
    text="Recommend Movies",
    command=recommend_movies
).pack(pady=15)
# Result box
tk.Label(
    root,
    text="Recommended Movies"
).pack()
result_box = tk.Text(
    root,
    width=40,
    height=15
)
result_box.pack(pady=10)
result_box.insert(
    tk.END,
    "Your movie recommendations\nwill appear here"
)
result_box.config(state="disabled")
root.mainloop()