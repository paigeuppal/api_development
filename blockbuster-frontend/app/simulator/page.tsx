"use client";

import { useState } from "react";
import Link from "next/link";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

// Define TypeScript interfaces for the expected API response structure
interface CompMovie {
  title: string;
  release_year: number;
  budget: number;
  revenue: number;
  roi_percentage: number;
}

interface SimulationResult {
  risk_assessment: {
    colour_code: "green" | "yellow" | "red";
    rating: string;
    analysis: string;
    cohort_size: number;
    success_rate_percentage: number;
  };
  genre_insights: {
    average_historical_roi_percentage: number;
    total_movies_analysed: number;
    closest_budget_comps: CompMovie[];
  };
}

// Fetch data from API 
export default function SimulatorPage() {
  const [budget, setBudget] = useState<number>(100000000);
  const [genre, setGenre] = useState<string>("Action");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<SimulationResult | null>(null);
  const [error, setError] = useState("");

  const genres = [
    "Action", "Adventure", "Animation", "Comedy", "Crime", "Documentary", 
    "Drama", "Family", "Fantasy", "History", "Horror", "Music", "Mystery", 
    "Romance", "Science Fiction", "Thriller", "War", "Western"
  ];

  const runSimulation = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    setResult(null);

    try {
      // Call the FastAPI endpoint with the proposed budget and genre as query parameters
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/analytics/success-predictor/?proposed_budget=${budget}&genre=${genre}`
      );
      
      const data = await res.json();

      if (!res.ok || data.error) {
        throw new Error(data.detail || data.error || "Failed to run simulation.");
      }

      setResult(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen p-8 bg-[#e57a5e] text-[#fbe0d9]">
      <div className="max-w-6xl mx-auto">
        
        {/* HEADER */}
        <div className="flex justify-between items-end mb-8 border-b border-[#fbe0d9]/40 pb-4">
          <div>
            <h1 className="text-4xl font-extrabold text-[#fbe0d9] mb-2">Success Predictor</h1>
            <p className="text-[#fbe0d9]/90">Predictive financial analytics based on historical comparable budgets.</p>
          </div>
          <Link href="/" className="text-[#012f3d] hover:text-[#fbe0d9] transition-colors font-semibold">
            &larr; Back to Dashboard
          </Link>
        </div>

        {/* INPUT FORM */}
        <div className="bg-[#fbe0d9] text-[#012f3d] p-6 rounded-2xl shadow-2xl border border-[#fbe0d9]/60 mb-8">
          <form onSubmit={runSimulation} className="flex flex-col md:flex-row gap-4 items-end">
            <div className="flex-1 w-full">
              <label className="block text-sm font-bold text-[#012f3d] mb-2">Proposed Budget ($)</label>
              <input 
                type="number" 
                min="100"
                value={budget} 
                onChange={(e) => setBudget(Number(e.target.value))}
                className="w-full p-3 border border-[#012f3d]/20 rounded-lg text-[#012f3d] bg-white/80 focus:ring-2 focus:ring-[#e57a5e] outline-none"
              />
            </div>
            <div className="flex-1 w-full">
              <label className="block text-sm font-bold text-[#012f3d] mb-2">Target Genre</label>
              <select 
                value={genre} 
                onChange={(e) => setGenre(e.target.value)}
                className="w-full p-3 border border-[#012f3d]/20 rounded-lg text-[#012f3d] focus:ring-2 focus:ring-[#e57a5e] bg-white/80 outline-none"
              >
                {genres.map(g => <option key={g} value={g}>{g}</option>)}
              </select>
            </div>
            <button 
              type="submit" 
              disabled={loading}
              className="w-full md:w-auto px-8 py-3 bg-[#012f3d] text-[#fbe0d9] font-bold rounded-lg hover:bg-[#0a4557] transition disabled:bg-[#012f3d]/50"
            >
              {loading ? "Simulating..." : "Run Analysis"}
            </button>
          </form>
          {error && <p className="text-red-600 mt-4 font-medium">{error}</p>}
        </div>

        {/* DYNAMIC RESULTS DASHBOARD */}
        {result && (
          <div className="space-y-8 animate-in fade-in duration-500">
            
            {/* TOP ROW: Risk Rating & Genre Averages */}
            <div className="grid md:grid-cols-3 gap-6">
              
              {/* Risk Assessment Box */}
              <div className={`col-span-1 md:col-span-2 p-6 rounded-xl border-2 flex flex-col justify-center ${
                result.risk_assessment.colour_code === "green" ? "bg-emerald-50 border-emerald-400 text-[#012f3d]" :
                result.risk_assessment.colour_code === "yellow" ? "bg-amber-50 border-amber-400 text-[#012f3d]" :
                "bg-rose-50 border-rose-400 text-[#012f3d]"
              }`}>
                <h2 className={`text-sm font-bold uppercase tracking-widest mb-2 ${
                  result.risk_assessment.colour_code === "green" ? "text-green-700" :
                  result.risk_assessment.colour_code === "yellow" ? "text-yellow-700" :
                  "text-red-700"
                }`}>Risk Assessment</h2>
                <h3 className={`text-4xl font-extrabold mb-4 ${
                  result.risk_assessment.colour_code === "green" ? "text-green-600" :
                  result.risk_assessment.colour_code === "yellow" ? "text-yellow-600" :
                  "text-red-600"
                }`}>{result.risk_assessment.rating}</h3>
                <p className="text-[#012f3d]/90 font-medium">{result.risk_assessment.analysis}</p>
                <div className="mt-4 inline-flex items-center gap-2 bg-white/60 w-fit px-3 py-1 rounded-full text-sm font-semibold border border-[#012f3d]/10">
                  <span className="text-[#012f3d]/90">Based on {result.risk_assessment.cohort_size} comparable comps</span>
                  <span className="text-[#012f3d]/40">•</span>
                  <span className="text-[#012f3d]/90">{result.risk_assessment.success_rate_percentage}% Success Rate</span>
                </div>
              </div>

              {/* Genre Insights Box */}
              <div className="col-span-1 bg-[#fbe0d9] text-[#012f3d] p-6 rounded-xl shadow-sm border border-[#012f3d]/10 flex flex-col justify-center">
                <h2 className="text-sm font-bold uppercase tracking-widest text-[#012f3d]/60 mb-4">Genre Baseline ({genre})</h2>
                <p className="text-4xl font-extrabold text-[#012f3d] mb-1">
                  {result.genre_insights.average_historical_roi_percentage}%
                </p>
                <p className="text-sm text-[#012f3d]/70 mb-4">Average Historical ROI</p>
                <p className="text-xs text-[#012f3d]/60 border-t border-[#012f3d]/10 pt-4">
                  Analysed {result.genre_insights.total_movies_analysed} movies in this genre globally.
                </p>
              </div>

            </div>

            {/* BOTTOM ROW: Data Visualization (Comps) */}
            <div className="bg-[#fbe0d9] text-[#012f3d] p-6 rounded-2xl shadow-2xl border border-[#fbe0d9]/60">
              <h2 className="text-xl font-bold text-[#012f3d] mb-6">Financial Comparables (Budget vs Revenue)</h2>
              
              <div className="h-96 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={result.genre_insights.closest_budget_comps} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#D8BBB2" />
                    <XAxis dataKey="title" tick={{fontSize: 12}} tickFormatter={(val) => val.length > 15 ? val.substring(0,15) + '...' : val} />
                    <YAxis tickFormatter={(val) => `$${(val / 1000000).toFixed(0)}M`} />
                    <Tooltip formatter={(value: any) => `$${Number(value).toLocaleString()}`} />
                    <Legend />
                    <Bar name="Budget" dataKey="budget" fill="#B58A7D" radius={[4, 4, 0, 0]} />
                    <Bar name="Revenue" dataKey="revenue" fill="#012F3D" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>

              {/* Data Table for exact numbers */}
              <div className="mt-8 overflow-x-auto">
                <table className="w-full text-left text-sm border-collapse">
                  <thead>
                    <tr className="bg-[#012f3d]/5 border-b border-[#012f3d]/10">
                      <th className="p-3">Title</th>
                      <th className="p-3">Year</th>
                      <th className="p-3">Budget</th>
                      <th className="p-3">Revenue</th>
                      <th className="p-3 text-right">ROI</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.genre_insights.closest_budget_comps.map((comp: CompMovie) => (
                      <tr key={comp.title} className="border-b border-[#012f3d]/10 hover:bg-white/50 transition-colors">
                        <td className="p-3 font-medium">{comp.title}</td>
                        <td className="p-3 text-[#012f3d]/70">{comp.release_year}</td>
                        <td className="p-3">${comp.budget.toLocaleString()}</td>
                        <td className="p-3">${comp.revenue.toLocaleString()}</td>
                        <td className={`p-3 text-right font-bold ${comp.roi_percentage >= 0 ? 'text-emerald-600' : 'text-rose-600'}`}>
                          {comp.roi_percentage}%
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

            </div>

          </div>
        )}

      </div>
    </main>
  );
}