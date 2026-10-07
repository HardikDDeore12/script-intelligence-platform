let compsChartInstance = null;

document.getElementById('matchForm').addEventListener('submit', async function (e) {
    e.preventDefault();

    const plotSummary = document.getElementById('plot_summary').value;
    const topK = document.getElementById('top_k').value;
    const submitBtn = document.getElementById('submitBtn');

    // UI Loading state
    submitBtn.disabled = true;
    submitBtn.innerHTML = `<span>Matching Concepts...</span>`;

    try {
        const response = await fetch('/api/match', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                plot_summary: plotSummary,
                top_k: parseInt(topK)
            })
        });

        const data = await response.json();

        if (data.status === 'success') {
            renderDashboard(data);
        } else {
            alert(data.message || 'Error executing match query.');
        }

    } catch (err) {
        console.error(err);
        alert('Failed to connect to server.');
    } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = `<span>Run Concept Matcher</span>`;
    }
});

function renderDashboard(data) {
    document.getElementById('placeholderState').classList.add('hidden');
    document.getElementById('resultsDashboard').classList.remove('hidden');

    const metrics = data.summary_metrics;

    // Helper formatter for money
    const formatMoney = (val) => `$${(val / 1000000).toFixed(1)}M`;

    // Populate Metrics Cards
    document.getElementById('metricAvgBudget').innerText = formatMoney(metrics.avg_budget);
    document.getElementById('metricAvgRevenue').innerText = formatMoney(metrics.avg_revenue_worldwide);
    document.getElementById('metricAvgRoi').innerText = `${metrics.avg_roi}x`;
    document.getElementById('metricTopMatch').innerText = metrics.top_benchmark_movie;
    // Metric Cards Update
    document.getElementById('metricProfitabilityRate').innerText = `${metrics.profitability_rate}%`;
    document.getElementById('metricProfitabilityRatio').innerText = `(${metrics.profitable_count_25}/25 Comps Profitable)`;
    // Render Bar Chart
    renderChart(data.comparable_movies);

    if (data.executive_insights) {
    const insights = data.executive_insights;
    document.getElementById('execRecommendation').innerText = insights.executive_recommendation;
    document.getElementById('execTakeaway').innerText = insights.key_takeaway;
    document.getElementById('riskBadge').innerText = insights.risk_assessment;
}

    // Render Comparable Movies List
    const listContainer = document.getElementById('moviesList');
    listContainer.innerHTML = '';

    data.comparable_movies.forEach(movie => {
        let posterUrl;
        if (movie.poster_path && movie.poster_path !== 'nan' && movie.poster_path.trim() !== '') {
            const path = movie.poster_path.startsWith('/') ? movie.poster_path : `/${movie.poster_path}`;
            posterUrl = `https://image.tmdb.org/t/p/w500${path}`;
        } else {
            const titleText = encodeURIComponent(movie.title);
            posterUrl = `https://ui-avatars.com/api/?name=${titleText}&background=1e293b&color=818cf8&size=150&font-size=0.25&bold=true`;
        }

        const card = document.createElement('div');
        card.className = 'bg-slate-800/80 border border-slate-700/80 rounded-xl p-4 hover:border-slate-600 transition flex gap-4 items-center';
        
        card.innerHTML = `
            <div class="w-20 h-28 rounded-lg shadow-md border border-slate-700 flex-shrink-0 bg-slate-950 overflow-hidden relative flex items-center justify-center">
                <img src="${posterUrl}" 
                    alt="${movie.title}" 
                    class="w-full h-full object-cover" 
                    onerror="this.onerror=null; this.src='https://ui-avatars.com/api/?name=${encodeURIComponent(movie.title)}&background=0f172a&color=a5b4fc&size=150&bold=true';">
            </div>

            <div class="flex-1 space-y-1.5">
                <div class="flex justify-between items-start">
                    <div>
                        <h4 class="text-base font-bold text-white">${movie.title} <span class="text-xs font-normal text-slate-400">(${movie.release_year})</span></h4>
                        <p class="text-xs text-indigo-300">Director: ${movie.director} | Cast: ${movie.main_cast}</p>
                    </div>
                    <span class="bg-indigo-500/10 text-indigo-400 border border-indigo-500/30 text-xs font-semibold px-2.5 py-1 rounded-full">
                        ${movie.similarity_score}% Match
                    </span>
                </div>
                <p class="text-xs text-slate-300 line-clamp-2">${movie.plot_summary}</p>
                <div class="flex space-x-4 pt-2 text-xs text-slate-400 border-t border-slate-700/50">
                    <span>Budget: <strong class="text-slate-200">${formatMoney(movie.budget)}</strong></span>
                    <span>Box Office: <strong class="text-emerald-400">${formatMoney(movie.revenue_worldwide)}</strong></span>
                    <span>ROI: <strong class="text-indigo-400">${movie.roi}x</strong></span>
                </div>
            </div>
        `;
        listContainer.appendChild(card);
    });
}

function renderChart(movies) {
    const ctx = document.getElementById('compsChart').getContext('2d');

    const labels = movies.map(m => m.title);
    const budgets = movies.map(m => (m.budget / 1000000).toFixed(1));
    const revenues = movies.map(m => (m.revenue_worldwide / 1000000).toFixed(1));

    if (compsChartInstance) {
        compsChartInstance.destroy();
    }

    compsChartInstance = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Budget ($M)',
                    data: budgets,
                    backgroundColor: '#6366f1',
                    borderRadius: 4
                },
                {
                    label: 'Worldwide Gross ($M)',
                    data: revenues,
                    backgroundColor: '#10b981',
                    borderRadius: 4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { labels: { color: '#94a3b8' } }
            },
            scales: {
                x: { ticks: { color: '#94a3b8' }, grid: { display: false } },
                y: { ticks: { color: '#94a3b8' }, grid: { color: '#334155' } }
            }
        }
    });
}