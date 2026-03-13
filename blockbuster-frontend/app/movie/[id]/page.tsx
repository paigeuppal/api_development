import Link from "next/link";

// Fetch movie details from API
async function getMovieDetails(id: string) {
  const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/movies/adjusted/${id}`, {
    cache: "no-store"
  });
  
  if (!res.ok) {
    // Parse message from API, use generic error if that fails
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || "Failed to load movie data");
  }
  return res.json();
}

// The main page component for displaying movie details
export default async function MoviePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  let movie = null;
  let errorMessage = "";

  //Attempt to fetch movie details, catch any errors to display in the UI
  try {
    movie = await getMovieDetails(id);
  } catch (error: any) {
    errorMessage = error.message;
  }

  // If there was an error fetching the movie, show a user-friendly error message and a link back to the dashboard
  if (errorMessage) {
    return (
      <main className="min-h-screen p-8 bg-[#e57a5e] text-[#fbe0d9] flex flex-col items-center justify-center text-center">
        <h1 className="text-4xl font-bold text-[#012f3d] mb-4">Oops!</h1>
        <p className="text-xl text-[#fbe0d9] mb-8">{errorMessage}</p>
        <Link href="/" className="px-6 py-3 bg-[#012f3d] hover:bg-[#0a4557] text-[#fbe0d9] rounded-lg font-bold transition-colors">
          Return to Dashboard
        </Link>
      </main>
    );
  }

  // If no errors, display movie details in clean layout 
  return (
    <main className="min-h-screen p-8 bg-[#e57a5e] text-[#fbe0d9]">
      <div className="max-w-3xl mx-auto">
        
        <div className="mb-6">
          <Link href="/" className="text-[#012f3d] hover:text-[#fbe0d9] font-semibold transition-colors">
            &larr; Back to Dashboard
          </Link>
        </div>

        {/* Header */}
        <div className="bg-[#fbe0d9] text-[#012f3d] p-8 rounded-t-2xl shadow-2xl border border-[#fbe0d9]/60 border-b-0">
          <h1 className="text-4xl font-extrabold text-[#012f3d] mb-2">{movie.title}</h1>
          <p className="text-xl text-[#012f3d]/70">Released in {movie.release_year}</p>

          {/* Genre Badge */}
          {movie.genres && (
            <div className="mt-2 mb-6">
              <span className="inline-block bg-[#012f3d]/10 text-[#012f3d] border border-[#012f3d]/20 text-sm font-bold px-4 py-1.5 rounded-full shadow-sm">
                {movie.genres}
              </span>
            </div>
          )}
        </div>

        {/* Financial Data Grid */}
        <div className="bg-[#fbe0d9] text-[#012f3d] p-8 rounded-b-2xl shadow-2xl border border-[#fbe0d9]/60">
          <h2 className="text-xl font-bold text-[#012f3d] mb-6 border-b border-[#012f3d]/10 pb-2">Inflation-Adjusted Financials</h2>
          
          <div className="grid md:grid-cols-2 gap-8">
            {/* Box Office Stats */}
            <div className="space-y-6">
              <div className="bg-white/55 p-4 rounded-lg border border-[#012f3d]/10">
                <p className="text-sm font-semibold text-[#012f3d]/60 uppercase tracking-wider mb-1">Adjusted Budget</p>
                <p className="text-2xl font-bold text-[#012f3d]">
                  ${movie.adjusted_budget?.toLocaleString() || "N/A"}
                </p>
              </div>
              
              <div className="bg-white/55 p-4 rounded-lg border border-[#012f3d]/10">
                <p className="text-sm font-semibold text-[#012f3d]/60 uppercase tracking-wider mb-1">Adjusted Revenue</p>
                <p className="text-2xl font-bold text-emerald-700">
                  ${movie.adjusted_revenue?.toLocaleString() || "N/A"}
                </p>
              </div>
            </div>

            {/* ROI Highlight */}
            <div className="flex flex-col justify-center items-center bg-[#012f3d] p-6 rounded-xl border border-[#012f3d]/20">
              <p className="text-sm font-bold text-[#fbe0d9]/80 uppercase tracking-widest mb-2">Return on Investment</p>
              <p className="text-5xl font-extrabold text-[#e57a5e]">
                {movie.roi_percentage?.toLocaleString()}%
              </p>
              <p className="text-xs text-[#fbe0d9]/70 mt-4 text-center">
                Calculated based on modern economic value.
              </p>
            </div>
          </div>
        </div>
        
      </div>
    </main>
  );
}