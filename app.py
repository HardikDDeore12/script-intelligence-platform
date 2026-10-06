from flask import Flask, render_template, request, jsonify
from src.matcher_engine import MatcherEngine
from src.llm_analyzer import NarrativeAnalyzer  # <-- Import Analyzer

app = Flask(__name__)

matcher = MatcherEngine()
analyzer = NarrativeAnalyzer()  # <-- Initialize Analyzer

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/api/match", methods=["POST"])
def match_script():
    try:
        data = request.get_json()
        if not data or "plot_summary" not in data:
            return jsonify({"status": "error", "message": "Please provide a plot_summary."}), 400

        plot_summary = data["plot_summary"].strip()
        top_k = int(data.get("top_k", 5))

        if len(plot_summary) < 20:
            return jsonify({"status": "error", "message": "Plot summary too short."}), 400

        # Fetch matches
        analysis_report = matcher.analyze_script_concept(plot_summary=plot_summary, top_k=top_k)

        # Generate LLM Narrative Insights
        if analysis_report.get("status") == "success":
            qualitative_insights = analyzer.generate_executive_summary(
                plot_summary=plot_summary,
                top_matches=analysis_report.get("comparable_movies", [])
            )
            analysis_report["executive_insights"] = qualitative_insights  # <-- Added to response

        return jsonify(analysis_report), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)