class NarrativeAnalyzer:
    """
    Qualitative narrative & risk analysis generator for script concepts.
    """
    
    def generate_executive_summary(self, plot_summary: str, top_matches: list) -> dict:
        """
        Generates qualitative narrative insights based on comparable historical comps.
        """
        if not top_matches:
            return {"summary": "Insufficient data to generate qualitative analysis."}

        top_comp = top_matches[0]
        avg_roi = round(sum(m.get("roi", 1.0) for m in top_matches) / len(top_matches), 2)

        # Risk level determination based on ROI distribution
        if avg_roi >= 2.5:
            risk_level = "Low Risk / High Commercial Potential"
            recommendation = "STRONG GREENLIGHT: Concept aligns with high-margin historical benchmarks."
        elif avg_roi >= 1.2:
            risk_level = "Moderate Risk / Moderate Yield"
            recommendation = "PROCEED WITH CAUTION: Optimize production budget to ensure profitability."
        else:
            risk_level = "High Commercial Risk"
            recommendation = "REVISE SCRIPT/BUDGET: Historical comps indicate potential box-office underperformance."

        return {
            "primary_comp": top_comp.get("title", "N/A"),
            "risk_assessment": risk_level,
            "executive_recommendation": recommendation,
            "key_takeaway": f"This concept shares strong narrative elements with '{top_comp.get('title')}', which earned ${top_comp.get('revenue_worldwide', 0)/1000000:.1f}M worldwide."
        }