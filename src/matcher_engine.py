import requests
from src import config
from src.vector_store import VectorStoreManager

class MatcherEngine:
    def __init__(self):
        self.vector_store = VectorStoreManager()

    def _fetch_poster_path(self, movie_title: str) -> str:
        """TMDb Search API se movie ka actual poster_path fetch karta hai"""
        if not config.TMDB_API_KEY:
            return ""
        
        try:
            url = f"https://api.themoviedb.org/3/search/movie"
            params = {
                "api_key": config.TMDB_API_KEY,
                "query": movie_title
            }
            response = requests.get(url, params=params, timeout=3)
            if response.status_code == 200:
                results = response.json().get("results", [])
                if results and results[0].get("poster_path"):
                    return results[0]["poster_path"]
        except Exception as e:
            print(f"Poster fetch error for {movie_title}: {e}")
            
        return ""

    def analyze_script_concept(self, plot_summary: str, top_k: int = 5) -> dict:
        matches_25 = self.vector_store.search_similar(query_plot=plot_summary, top_k=25)

        if not matches_25:
            return {"status": "error", "message": "No comparable movies found."}

        # Calculate profitable movies count out of top 25
        profitable_movies_25 = [
            m for m in matches_25 
            if m.get("revenue_worldwide", 0) > m.get("budget", 0) and m.get("budget", 0) > 0
        ]
        profitability_rate = round((len(profitable_movies_25) / 25) * 100, 1)

        display_matches = matches_25[:top_k]

        # Fetch real-time poster paths from TMDb API for display matches
        for m in display_matches:
            poster_path = self._fetch_poster_path(m["title"])
            m["poster_path"] = poster_path

        budgets = [m["budget"] for m in display_matches if m.get("budget", 0) > 0]
        revenues = [m["revenue_worldwide"] for m in display_matches if m.get("revenue_worldwide", 0) > 0]
        rois = [m["roi"] for m in display_matches if "roi" in m]

        avg_budget = sum(budgets) / len(budgets) if budgets else 0.0
        avg_revenue = sum(revenues) / len(revenues) if revenues else 0.0
        avg_roi = round(sum(rois) / len(rois), 2) if rois else 0.0

        sorted_by_roi = sorted(display_matches, key=lambda x: x.get("roi", 0), reverse=True)
        top_performer = sorted_by_roi[0] if sorted_by_roi else None

        return {
            "status": "success",
            "summary_metrics": {
                "avg_budget": round(avg_budget, 2),
                "avg_revenue_worldwide": round(avg_revenue, 2),
                "avg_roi": avg_roi,
                "profitability_rate": profitability_rate,
                "profitable_count_25": len(profitable_movies_25),
                "top_benchmark_movie": top_performer["title"] if top_performer else "N/A",
                "max_roi_achieved": top_performer["roi"] if top_performer else 0.0
            },
            "comparable_movies": display_matches
        }