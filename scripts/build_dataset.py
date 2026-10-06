import os
import re
import json
import pandas as pd
from datasets import load_dataset

def normalize_title(title):
    """Clean and normalize title for matching"""
    if pd.isna(title):
        return ""
    title = str(title).lower().strip()
    title = re.sub(r"[^\w\s]", "", title)  # Remove punctuation
    title = re.sub(r"\s+", " ", title)     # Remove extra spaces
    return title

def extract_director(crew_json_str):
    """Extract director name from crew JSON string"""
    try:
        crew_list = json.loads(crew_json_str)
        for member in crew_list:
            if member.get('job') == 'Director':
                return member.get('name', '')
    except Exception:
        pass
    return ""

def extract_top_cast(cast_json_str, top_n=3):
    """Extract top N cast members from cast JSON string"""
    try:
        cast_list = json.loads(cast_json_str)
        # Sort by order if available, get top_n names
        top_cast = [member.get('name', '') for member in cast_list[:top_n] if 'name' in member]
        return ", ".join(top_cast)
    except Exception:
        pass
    return ""

def prepare_master_dataset():
    print("🚀 Step 1: Loading Wikipedia Movie Plots Dataset...")
    try:
        wiki_dataset = load_dataset("wikipedia_movie_plots", split="train")
        wiki_df = pd.DataFrame(wiki_dataset)
        wiki_df['clean_title'] = wiki_df['Title'].apply(normalize_title)
        wiki_df['year'] = pd.to_numeric(wiki_df['Release Year'], errors='coerce')
        wiki_df = wiki_df.rename(columns={'Plot': 'plot_summary', 'Title': 'wiki_title'})
        print(f"✅ Loaded {len(wiki_df)} Wikipedia plot summaries.")
    except Exception as e:
        print(f"⚠️ Wikipedia Dataset load fail ho gaya: {e}")
        wiki_df = pd.DataFrame(columns=['clean_title', 'year', 'plot_summary', 'wiki_title'])

    print("\n🚀 Step 2: Fetching TMDb Movies & Credits Dataset...")
    tmdb_movies_file = "tmdb_5000_movies.csv"
    tmdb_credits_file = "tmdb_5000_credits.csv"

    if not os.path.exists(tmdb_movies_file) or not os.path.exists(tmdb_credits_file):
        print(f"⚠️ Error: Ensure both '{tmdb_movies_file}' and '{tmdb_credits_file}' are present in your project directory.")
        return

    tmdb_movies_df = pd.read_csv(tmdb_movies_file)
    tmdb_credits_df = pd.read_csv(tmdb_credits_file)

    # Credits dataset se Director aur Top Cast extract karo
    print("🎬 Extracting Director and Top Cast details from Credits...")
    tmdb_credits_df['director'] = tmdb_credits_df['crew'].apply(extract_director)
    tmdb_credits_df['main_cast'] = tmdb_credits_df['cast'].apply(lambda x: extract_top_cast(x, top_n=3))

    # Movies aur Credits ko movie_id / id par merge karo
    tmdb_merged = pd.merge(
        tmdb_movies_df,
        tmdb_credits_df[['movie_id', 'director', 'main_cast']],
        left_on='id',
        right_on='movie_id',
        how='left'
    )

    # Extract Release Year and Clean Title
    tmdb_merged['year'] = pd.to_datetime(tmdb_merged['release_date'], errors='coerce').dt.year
    tmdb_merged['clean_title'] = tmdb_merged['title'].apply(normalize_title)

    # Filter movies with valid budget and revenue
    tmdb_merged = tmdb_merged[(tmdb_merged['budget'] > 0) & (tmdb_merged['revenue'] > 0)]
    print(f"✅ Loaded {len(tmdb_merged)} TMDb movies with budget, revenue, and credits.")

    print("\n🚀 Step 3: Merging Wikipedia Plots with TMDb Data...")
    if not wiki_df.empty:
        master_df = pd.merge(
            tmdb_merged,
            wiki_df[['clean_title', 'year', 'plot_summary', 'wiki_title']],
            on=['clean_title', 'year'],
            how='left'
        )
    else:
        master_df = tmdb_merged
        master_df['plot_summary'] = None

    # Fallback to TMDb overview if Wikipedia plot is missing
    master_df['plot_summary'] = master_df['plot_summary'].fillna(master_df['overview'])
    master_df = master_df.drop_duplicates(subset=['clean_title', 'year'])

    print("\n🚀 Step 4: Computing Metrics & Master Dataset Schema...")
    master_df['roi'] = (master_df['revenue'] / master_df['budget']).round(2)

    final_df = pd.DataFrame({
        'movie_id': master_df['id'],
        'title': master_df['title'],
        'release_year': master_df['year'].fillna(0).astype(int),
        'director': master_df['director'].fillna("Unknown"),
        'main_cast': master_df['main_cast'].fillna("Unknown"),
        'budget': master_df['budget'],
        'revenue_worldwide': master_df['revenue'],
        'roi': master_df['roi'],
        'genres': master_df['genres'],
        'plot_summary': master_df['plot_summary'],
        'vote_average': master_df['vote_average'],
        'vote_count': master_df['vote_count']
    })

    # Drop rows without valid plot text
    final_df = final_df.dropna(subset=['plot_summary'])
    final_df = final_df[final_df['plot_summary'].str.len() > 50]

    output_csv = "master_movie_dataset.csv"
    output_json = "master_movie_dataset.json"

    final_df.to_csv(output_csv, index=False)
    final_df.to_json(output_json, orient="records", indent=2)

    print(f"\n🎉 SUCCESS: Enhanced Master Dataset Created!")
    print(f"📊 Total Movies Processed: {len(final_df)}")
    print(f"📁 Files saved: '{output_csv}' and '{output_json}'")

if __name__ == "__main__":
    prepare_master_dataset()