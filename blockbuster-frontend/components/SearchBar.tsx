"use client"; // This tells Next.js this component runs in the user's browser!

import { useState } from "react";
import Link from "next/link";

export default function SearchBar() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const [error, setError] = useState("");

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault(); // Stop the page from refreshing
    if (!query) return;

    setIsSearching(true);
    setError("");
    setResults([]);

    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/movies/search/?title=${query}&limit=5`);
      
      if (!res.ok) {
        if (res.status === 404) throw new Error("No movies found.");
        throw new Error("Failed to search.");
      }

      const data = await res.json();
      setResults(data.results);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsSearching(false);
    }
  };

  return (
    <div className="mb-12 bg-white p-6 rounded-xl shadow-md border border-gray-100">
      <h2 className="text-2xl font-bold mb-4 text-gray-800">Search the Vault</h2>
      
      {/* Search Form*/}
      <form onSubmit={handleSearch} className="flex gap-2 mb-4">
        <input
          type="text"
          autoComplete="off"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Type a movie title (e.g., Avatar)..."
          className="flex-1 p-3 border border-gray-300 rounded-lg text-[#012f3d] placeholder-[#012f3d] focus:ring-2 focus:ring-blue-500 outline-none"
        />
        <button 
          type="submit" 
          disabled={isSearching}
          className="bg-blue-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-blue-700 transition-colors disabled:bg-blue-400"
        >
          {isSearching ? "Searching..." : "Search"}
        </button>
      </form>

      {/* Error Message */}
      {error && <p className="text-red-500 font-medium">{error}</p>}

      {/* Search Results */}
      {results.length > 0 && (
        <div className="mt-4 border-t pt-4">
          <h3 className="text-sm text-gray-500 font-semibold mb-2 uppercase tracking-wider">Top Results</h3>
        <ul className="space-y-2">
           {results.map((movie: any) => (
              <li key={movie.movie_id} className="bg-gray-50 rounded-lg border border-gray-100 hover:border-blue-300 hover:shadow-sm transition-all">
                <Link href={`/movie/${movie.movie_id}`} className="p-3 flex justify-between items-center w-full">
                  
                  {/* Title, ID, and Genre Badge on left */}
                  <div className="flex flex-col gap-1">
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-gray-800">{movie.title}</span>
                      <span className="text-xs font-mono text-blue-600 bg-blue-100 px-2 py-0.5 rounded-full">
                        ID: {movie.movie_id}
                      </span>
                    </div>
                    {movie.genres && (
                      <span className="text-xs font-semibold text-indigo-700 bg-indigo-50 border border-indigo-100 px-2 py-0.5 rounded-full w-fit">
                        {movie.genres}
                      </span>
                    )}
                  </div>

                  {/*Year and Arrow on right */}
                  <span className="text-sm text-gray-500 flex items-center gap-2">
                    {movie.release_year}
                    <span className="text-blue-500">&rarr;</span>
                  </span>
                  
                </Link>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}