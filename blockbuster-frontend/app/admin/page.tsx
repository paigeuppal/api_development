// Admin page for managing movies and inflation data, protected by API key authentication.
"use client";

import { useState } from "react";

export default function AdminPage() {
  // State for the security vault
  const [apiKey, setApiKey] = useState("");
  const [isUnlocked, setIsUnlocked] = useState(false);
  const [feedback, setFeedback] = useState({ type: "", message: "" });

  // State for the Add Movie form
  const [newMovie, setNewMovie] = useState({
    title: "",
    release_year: 2024,
    budget: 0,
    revenue: 0,
    genres: "",
  });

  // State for the Delete Movie form
  const [deleteId, setDeleteId] = useState("");

  // State for the Update Inflation form
  const [newInflation, setNewInflation] = useState({
    year: 2024,
    cpi: 315.0, // Example starting CPI
  });

  const handleVerify = async () => {
    setFeedback({ type: "info", message: "Verifying API Key..." });
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/auth/verify`, {
        headers: { "X-API-Key": apiKey }
      });
      
      if (res.ok) {
        setIsUnlocked(true);
        setFeedback({ type: "success", message: "Key verified successfully!" });
      } else {
        setIsUnlocked(false);
        setFeedback({ type: "error", message: "Incorrect API Key!" });
      }
    } catch (err) {
      setFeedback({ type: "error", message: "Failed to connect to the server." });
    }
  };

  // Handler for adding a movie (POST)
  const handleAddMovie = async (e: React.FormEvent) => {
    e.preventDefault();
    setFeedback({ type: "info", message: "Adding movie..." });

    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/movies/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-API-Key": apiKey,
        },
        body: JSON.stringify(newMovie),
      });

      const data = await res.json();

      if (!res.ok) {
        if (Array.isArray(data.detail)) {
          throw new Error(data.detail[0].msg);
        }
        throw new Error(data.detail || "Failed to add movie");
      }

      setFeedback({ 
        type: "success", 
        message: `${data.message} (ID: ${data.movie_id})` 
      });
      setNewMovie({ title: "", release_year: 2024, budget: 0, revenue: 0, genres: "" });
    } catch (err: any) {
      setFeedback({ type: "error", message: err.message });
    }
  };

  // Handler for deleting a movie (DELETE)
  const handleDeleteMovie = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!deleteId) return;
    
    setFeedback({ type: "info", message: "Deleting movie..." });

    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/movies/${deleteId}`, {
        method: "DELETE",
        headers: {
          "X-API-Key": apiKey,
        },
      });

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || "Failed to delete movie");
      }

      setFeedback({ type: "success", message: `Success! Movie ID ${deleteId} has been deleted.` });
      setDeleteId(""); 
    } catch (err: any) {
      setFeedback({ type: "error", message: err.message });
    }
  };

  // Handler for adding/updating inflation data (SMART POST/PUT)
  const handleAddInflation = async (e: React.FormEvent) => {
    e.preventDefault();
    setFeedback({ type: "info", message: "Processing inflation data..." });

    try {
      // Attempt to CREATE the record (POST)
      const postRes = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/inflation/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-API-Key": apiKey,
        },
        body: JSON.stringify(newInflation),
      });

      const postData = await postRes.json();

      // If POST is successful (brand new year):
      if (postRes.ok) {
        setFeedback({ type: "success", message: `Success! ${postData.message}` });
        setNewInflation({ year: newInflation.year + 1, cpi: newInflation.cpi });
        return; // Stop execution
      }

      // If POST failed, check if it's because the year exists (400)
      const errorMsg = Array.isArray(postData.detail) ? postData.detail[0].msg : postData.detail;

      if (postRes.status === 400 && errorMsg.includes("already exists")) {
        setFeedback({ type: "info", message: `Year ${newInflation.year} exists. Updating instead...` });

        // Do UPDATE (PUT) since the year already exists
        const putRes = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/inflation/${newInflation.year}?cpi=${newInflation.cpi}`, {
          method: "PUT",
          headers: {
            "X-API-Key": apiKey,
          }
        });

        const putData = await putRes.json();

        if (!putRes.ok) {
            const putError = Array.isArray(putData.detail) ? putData.detail[0].msg : putData.detail;
            throw new Error(putError || "Failed to update inflation.");
        }

        setFeedback({ type: "success", message: `Success! ${putData.message}` });
        setNewInflation({ year: newInflation.year + 1, cpi: newInflation.cpi });

      } else {
          // Failed for another reason 
          throw new Error(errorMsg || "Failed to process inflation data.");
      }
    } catch (err: any) {
      setFeedback({ type: "error", message: err.message });
    }
  };

  return (
    <main className="min-h-screen bg-[#012f3d] text-[#fbe0d9] pb-12">
      <div className="max-w-5xl mx-auto px-6 pt-16 pb-8">
        
        <div className="mb-10 border-b border-[#fbe0d9]/20 pb-4 flex justify-between items-end gap-4">
          <div>
            <h1 className="text-4xl font-extrabold text-[#fbe0d9] mb-2 tracking-tight">Admin Control Panel</h1>
            <p className="text-[#fbe0d9]/80">Restricted access. API Key required for all destructive actions.</p>
          </div>
          <a href="/" className="text-sm font-semibold text-[#e57a5e] hover:text-[#fbe0d9] transition-colors">
            &larr; Back to Dashboard
          </a>
        </div>

        {/* SECURITY VAULT */}
        <div className="bg-[#0a4557] p-6 rounded-2xl border border-[#fbe0d9]/15 mb-8 shadow-2xl">
          <h2 className="text-xl font-semibold mb-4 text-[#fbe0d9] flex items-center gap-2">
            🔐 Authentication
          </h2>
          <div className="flex gap-4">
            <input
              type="password"
              value={apiKey}
              onChange={(e) => {
                  setApiKey(e.target.value);
                  if (isUnlocked) setIsUnlocked(false);
              }}
              className={`flex-1 p-3 bg-[#012f3d] border rounded-lg outline-none transition-all placeholder-[#fbe0d9]/50 ${
                  isUnlocked 
                  ? "border-emerald-500 ring-2 ring-emerald-500/20 text-emerald-300" 
                  : "border-[#fbe0d9]/20 focus:ring-2 focus:ring-[#e57a5e] text-[#fbe0d9]"
              }`}
              placeholder="Enter your secret API Key..."
            />
            <button 
              onClick={handleVerify}
              className={`px-6 py-3 rounded-lg font-semibold transition-colors text-white ${
                  isUnlocked 
                  ? "bg-emerald-600 hover:bg-emerald-700" 
                  : "bg-[#e57a5e] hover:bg-[#d0694e]"
              }`}
            >
              {isUnlocked ? "Key Set" : "Unlock Panel"}
            </button>
          </div>
        </div>

        {/* FEEDBACK BANNER */}
        {feedback.message && (
          <div className={`p-4 rounded-xl mb-8 font-medium ${
            feedback.type === "error" ? "bg-rose-950/50 text-rose-200 border border-rose-800/80" :
            feedback.type === "success" ? "bg-emerald-950/40 text-emerald-200 border border-emerald-800/70" :
            "bg-[#fbe0d9]/10 text-[#fbe0d9] border border-[#fbe0d9]/20"
          }`}>
            {feedback.message}
          </div>
        )}

        {/* CONTROL PANEL GRID */}
        <div className="grid md:grid-cols-2 gap-8">
          
          {/* LEFT COLUMN: ADD MOVIE FORM */}
          <div className="bg-[#0a4557] p-6 rounded-2xl border border-[#fbe0d9]/15 shadow-2xl">
            <h3 className="text-lg font-bold text-[#fbe0d9] mb-4">Add New Movie</h3>
            <form onSubmit={handleAddMovie} className="space-y-4">
              <div>
                <label className="block text-sm text-[#fbe0d9]/80 mb-1">Title</label>
                <input required type="text" value={newMovie.title} onChange={e => setNewMovie({...newMovie, title: e.target.value})} className="w-full p-2.5 bg-[#012f3d] border border-[#fbe0d9]/20 rounded-lg text-[#fbe0d9] focus:ring-2 focus:ring-[#e57a5e] outline-none" />
              </div>
              <div>
                <label className="block text-sm text-[#fbe0d9]/80 mb-1">Genres (comma separated)</label>
                <input 
                  type="text" 
                  placeholder="e.g. Action, Adventure, Sci-Fi"
                  value={newMovie.genres} 
                  onChange={e => setNewMovie({...newMovie, genres: e.target.value})} 
                  className="w-full p-2.5 bg-[#012f3d] border border-[#fbe0d9]/20 rounded-lg text-[#fbe0d9] placeholder-[#fbe0d9]/50 focus:ring-2 focus:ring-[#e57a5e] outline-none" 
                />
             </div>
              <div>
                <label className="block text-sm text-[#fbe0d9]/80 mb-1">Release Year</label>
                <input required type="number" value={newMovie.release_year} onChange={e => setNewMovie({...newMovie, release_year: parseInt(e.target.value)})} className="w-full p-2.5 bg-[#012f3d] border border-[#fbe0d9]/20 rounded-lg text-[#fbe0d9] focus:ring-2 focus:ring-[#e57a5e] outline-none" />
              </div>
              <div>
                <label className="block text-sm text-[#fbe0d9]/80 mb-1">Budget ($)</label>
                <input 
                  required 
                  type="number" 
                  value={Number.isNaN(newMovie.budget) ? "" : newMovie.budget} 
                  onChange={e => setNewMovie({...newMovie, budget: parseFloat(e.target.value)})} 
                  className="w-full p-2.5 bg-[#012f3d] border border-[#fbe0d9]/20 rounded-lg text-[#fbe0d9] focus:ring-2 focus:ring-[#e57a5e] outline-none" 
                />
              </div>
              <div>
                <label className="block text-sm text-[#fbe0d9]/80 mb-1">Revenue ($)</label>
                <input 
                  required 
                  type="number" 
                  value={Number.isNaN(newMovie.revenue) ? "" : newMovie.revenue} 
                  onChange={e => setNewMovie({...newMovie, revenue: parseFloat(e.target.value)})} 
                  className="w-full p-2.5 bg-[#012f3d] border border-[#fbe0d9]/20 rounded-lg text-[#fbe0d9] focus:ring-2 focus:ring-[#e57a5e] outline-none" 
                />              
              </div>
              <button 
                type="submit" 
                disabled={!isUnlocked}
                className="w-full bg-[#e57a5e] hover:bg-[#d0694e] disabled:bg-[#fbe0d9]/20 disabled:text-[#fbe0d9]/50 disabled:cursor-not-allowed text-white p-2.5 rounded-lg font-bold transition-colors"
                >
                POST /movies/
              </button>
            </form>
          </div>

          {/* RIGHT COLUMN: STACKED FORMS (DELETE & INFLATION) */}
          <div className="flex flex-col gap-8 h-fit">
            
            {/* DELETE MOVIE FORM */}
            <div className="bg-[#0a4557] p-6 rounded-2xl border border-[#fbe0d9]/15 shadow-2xl">
              <h3 className="text-lg font-bold text-[#fbe0d9] mb-4">Delete Movie</h3>
              <form onSubmit={handleDeleteMovie} className="space-y-4">
                <div>
                  <label className="block text-sm text-[#fbe0d9]/80 mb-1">Movie ID to Delete</label>
                  <input 
                    required 
                    type="number" 
                    value={deleteId} 
                    onChange={e => setDeleteId(e.target.value)} 
                    placeholder="e.g., 42"
                    className="w-full p-2.5 bg-[#012f3d] border border-[#fbe0d9]/20 rounded-lg text-[#fbe0d9] placeholder-[#fbe0d9]/50 focus:ring-2 focus:ring-[#e57a5e] outline-none" 
                  />
                </div>
                <button 
                  type="submit" 
                  disabled={!isUnlocked}
                  className="w-full bg-[#e57a5e] hover:bg-[#d0694e] disabled:bg-[#fbe0d9]/20 disabled:text-[#fbe0d9]/50 disabled:cursor-not-allowed text-white p-2.5 rounded-lg font-bold transition-colors"
                >
                  DELETE /movies/{"{id}"}
                </button>
              </form>
            </div>

            {/* UPDATE INFLATION FORM */}
            <div className="bg-[#0a4557] p-6 rounded-2xl border border-[#fbe0d9]/15 shadow-2xl">
              <h3 className="text-lg font-bold text-[#fbe0d9] mb-4">Create/Update CPI value</h3>
              <form onSubmit={handleAddInflation} className="space-y-4">
                <div>
                  <label className="block text-sm text-[#fbe0d9]/80 mb-1">Year</label>
                  <input 
                    required 
                    type="number" 
                    value={Number.isNaN(newInflation.year) ? "" : newInflation.year} 
                    onChange={e => setNewInflation({...newInflation, year: parseInt(e.target.value)})} 
                    className="w-full p-2.5 bg-[#012f3d] border border-[#fbe0d9]/20 rounded-lg text-[#fbe0d9] focus:ring-2 focus:ring-[#e57a5e] outline-none" 
                  />
                </div>
                
                <div>
                  <label className="block text-sm text-[#fbe0d9]/80 mb-1">CPI Value</label>
                  <input 
                    required 
                    type="number" 
                    step="0.01" 
                    value={Number.isNaN(newInflation.cpi) ? "" : newInflation.cpi} 
                    onChange={e => setNewInflation({...newInflation, cpi: parseFloat(e.target.value)})} 
                    className="w-full p-2.5 bg-[#012f3d] border border-[#fbe0d9]/20 rounded-lg text-[#fbe0d9] focus:ring-2 focus:ring-[#e57a5e] outline-none" 
                  />
                </div>
                
                <button 
                  type="submit" 
                  disabled={!isUnlocked}
                  className="w-full bg-[#e57a5e] hover:bg-[#d0694e] disabled:bg-[#fbe0d9]/20 disabled:text-[#fbe0d9]/50 disabled:cursor-not-allowed text-white p-2.5 rounded-lg font-bold transition-colors"
                >
                  POST / PUT /inflation/
                </button>
              </form>
            </div>

          </div>
        </div>
      </div>
    </main>
  );
}