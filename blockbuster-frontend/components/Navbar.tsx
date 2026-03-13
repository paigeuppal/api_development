import Link from "next/link";
import Image from "next/image";

export default function Navbar() {
  return (
    <nav className="bg-[#fbe0d9] text-[#012f3d] shadow-lg sticky top-0 z-50 border-b border-[#012f3d]/10">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-20">
          
          {/* LEFT SIDE: Reel Returns Logo */}
          <div className="flex-shrink-0 flex items-center">
            <Link href="/" className="inline-flex items-center hover:opacity-90 transition-opacity">
              <Image
                src="/ReelReturnsAPI-rec.png"
                alt="Reel Returns"
                width={160}
                height={160}
                className="h-20 w-auto"
                priority
              />
            </Link>
          </div>
          
          {/* RIGHT SIDE: Navigation Links */}
          <div className="flex items-center space-x-4 sm:space-x-8">
            <Link href="/" className="text-sm sm:text-base font-medium hover:text-[#e57a5e] transition-colors">
              Dashboard
            </Link>
            <div className="border-l border-[#012f3d]/20 h-6 hidden sm:block"></div>
            <Link 
              href="/simulator" 
              className="text-sm sm:text-base font-medium hover:text-[#e57a5e] transition-colors"
            >
              Success Predictor
            </Link>
            <div className="border-l border-[#012f3d]/20 h-6 hidden sm:block"></div>
            <Link href="/admin" className="text-sm sm:text-base font-medium hover:text-[#e57a5e] transition-colors">
               Admin
            </Link>

            
          </div>

        </div>
      </div>
    </nav>
  );
}