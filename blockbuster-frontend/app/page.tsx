import SearchBar from "../components/SearchBar";
import Image from "next/image";

async function getLeaderboard() {
  const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/analytics/leaderboard`, {
    cache: "no-store"
  });
  
  if (!res.ok) {
    throw new Error('Failed to fetch leaderboard from Python API');
  }
  
  return res.json();
}

// Define TypeScript interface for the expected API response structure
interface LeaderboardMovie {
  movie_id: number;
  title: string;
  release_year: number;
  roi_percentage: number;
}

// The main page component for the dashboard, which fetches and displays the adjusted leaderboard and includes the search bar
export default async function Home() {
  const data = await getLeaderboard();
  const topMovies = data.top_movies;

  return (
    <main className="min-h-screen bg-[#e57a5e] text-[#fbe0d9] font-sans pb-12">
      
      {/* Hero Section */}
      <div className="max-w-5xl mx-auto px-6 pt-16 pb-8">
        <div className="flex flex-col items-center text-center mb-10">
          {/* Logo */}
          <Image 
            src="/ReelReturnsAPI-rec.png" 
            alt="Reel Returns Logo" 
            width={300} 
            height={200} 
            className="rounded-2xl mb-6 shadow-xl shadow-[#012f3d]/50 border-2 border-[#e57a5e]/20" 
          />
          <h1 className="text-5xl font-extrabold mb-4 tracking-tight">
            REEL RETURNS
          </h1>
          <p className="text-xl opacity-90 max-w-2xl">
            The most profitable movies of all time, adjusted for modern inflation.
          </p>
        </div>

        {/* Search Bar*/}
        <div className="w-full max-w-2xl mx-auto mb-16">
          <SearchBar />
        </div>

        {/* Leaderboard Section*/}
        <div className="bg-[#fbe0d9] text-[#012f3d] rounded-2xl shadow-2xl overflow-hidden border border-[#fbe0d9]/50">
          
          {/* Table Header */}
          <div className="p-6 border-b border-[#012f3d]/10 bg-white/40">
            <h2 className="text-2xl font-extrabold tracking-tight">Adjusted Leaderboard</h2>
          </div>

          {/* Table */}
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-[#012f3d]/5 text-[#012f3d] text-sm uppercase tracking-wider">
                  <th className="p-4 font-bold">Rank</th>
                  <th className="p-4 font-bold">Title</th>
                  <th className="p-4 font-bold">Year</th>
                  <th className="p-4 font-bold text-right">Adjusted ROI</th>
                </tr>
              </thead>
              <tbody>
                {topMovies.map((movie: LeaderboardMovie, index: number) => (
                  <tr key={movie.movie_id} className="border-b border-[#012f3d]/10 hover:bg-white/50 transition-colors">
                    <td className="p-4 font-extrabold text-[#e57a5e]">#{index + 1}</td>
                    <td className="p-4 font-bold">{movie.title}</td>
                    <td className="p-4 opacity-75 font-medium">{movie.release_year}</td>
                    <td className="p-4 font-black text-right text-[#012f3d]">
                      {movie.roi_percentage.toLocaleString()}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          
        </div>
      </div>
    </main>
  );
}