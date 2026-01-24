// filepath: 
import { Link } from "react-router-dom";
import { 
  Activity, Brain, FileText, Share2, ShieldCheck, ArrowRight, 
  Stethoscope, Moon, Sun, ChevronRight 
} from "lucide-react";
import { motion } from "framer-motion";

export default function LandingPage({ toggleTheme, currentTheme }: { toggleTheme: () => void, currentTheme: string }) {
  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 font-sans text-slate-900 dark:text-slate-100 transition-colors duration-300">
      
      {/* 1. Navbar (Floating & Centered content) */}
      <nav className="fixed w-full z-50 px-6 py-4">
        <div className="max-w-5xl mx-auto bg-white/70 dark:bg-slate-900/70 backdrop-blur-lg border border-slate-200 dark:border-slate-800 rounded-2xl px-6 py-3 flex justify-between items-center shadow-sm">
          <div className="flex items-center gap-2">
            <div className="bg-indigo-600 p-1.5 rounded-lg">
              <Stethoscope className="text-white w-5 h-5" />
            </div>
            <span className="text-lg font-bold tracking-tight">NeoMed</span>
          </div>
          
          <div className="flex items-center gap-4">
             <button onClick={toggleTheme} className="p-2 rounded-full hover:bg-slate-100 dark:hover:bg-slate-800 transition">
                {currentTheme === 'dark' ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
             </button>
             <Link to="/app">
                <button className="bg-slate-900 dark:bg-white text-white dark:text-slate-900 px-5 py-2 rounded-xl text-sm font-semibold hover:opacity-90 transition">
                  Launch App
                </button>
             </Link>
          </div>
        </div>
      </nav>

      {/* 2. Hero Section (Centered) */}
      <section className="relative pt-40 pb-20 px-6 text-center overflow-hidden">
        
        {/* Background Glows */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 -z-10 w-200 h-125 bg-indigo-500/20 dark:bg-indigo-500/10 blur-[120px] rounded-full pointer-events-none"></div>

        <motion.div 
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          className="max-w-4xl mx-auto"
        >
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-50 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300 font-medium text-xs mb-8 border border-indigo-100 dark:border-indigo-800">
             <span className="w-2 h-2 rounded-full bg-indigo-500 animate-pulse"></span>
             v2.0 Now Live
          </div>

          <h1 className="text-6xl md:text-8xl font-bold tracking-tight mb-8 bg-clip-text text-transparent bg-linear-to-b from-slate-900 to-slate-600 dark:from-white dark:to-slate-400">
            Diagnosis backed by <br/> intelligence.
          </h1>
          
          <p className="text-xl md:text-2xl text-slate-500 dark:text-slate-400 mb-12 max-w-2xl mx-auto leading-relaxed">
            The first clinical AI that combines 
            <span className="text-indigo-600 dark:text-indigo-400 font-semibold"> Vector Recall</span> with 
            <span className="text-indigo-600 dark:text-indigo-400 font-semibold"> Knowledge Graphs</span> 
            to eliminate hallucinations.
          </p>
          
          <div className="flex justify-center gap-4">
            <Link to="/app">
              <button className="flex items-center gap-2 bg-indigo-600 text-white px-8 py-4 rounded-2xl font-bold text-lg hover:bg-indigo-700 transition shadow-xl shadow-indigo-600/20 hover:scale-105 active:scale-95">
                Start Analysis <ArrowRight className="w-5 h-5" />
              </button>
            </Link>
          </div>
        </motion.div>

        {/* 3. Hero Visual (The "App Shell" Look) */}
        <motion.div 
           initial={{ opacity: 0, scale: 0.95 }}
           animate={{ opacity: 1, scale: 1 }}
           transition={{ duration: 1, delay: 0.3 }}
           className="mt-20 max-w-6xl mx-auto"
        >
           <div className="relative rounded-2xl border border-slate-200 dark:border-slate-800 bg-white/50 dark:bg-slate-900/50 backdrop-blur-xl shadow-2xl overflow-hidden p-2">
              <div className="bg-slate-50 dark:bg-slate-950 rounded-xl border border-slate-200 dark:border-slate-800 overflow-hidden h-125 md:h-175 relative">
                  
                  {/* Mock Interface Content */}
                  <div className="absolute top-0 left-0 w-full h-12 border-b border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 flex items-center px-4 gap-2">
                      <div className="flex gap-1.5">
                        <div className="w-3 h-3 rounded-full bg-red-400/80"></div>
                        <div className="w-3 h-3 rounded-full bg-amber-400/80"></div>
                        <div className="w-3 h-3 rounded-full bg-green-400/80"></div>
                      </div>
                      <div className="mx-auto text-xs font-mono text-slate-400">NeoMed_Analysis_Engine.tsx</div>
                  </div>

                  <div className="p-8 grid grid-cols-3 gap-8 h-full pt-20">
                      {/* Left Sidebar Mock */}
                      <div className="col-span-1 hidden md:block space-y-4">
                          <div className="h-4 bg-slate-200 dark:bg-slate-800 rounded w-1/3"></div>
                          <div className="h-32 bg-slate-100 dark:bg-slate-800/50 rounded-xl border border-dashed border-slate-300 dark:border-slate-700"></div>
                          <div className="h-4 bg-slate-200 dark:bg-slate-800 rounded w-2/3"></div>
                      </div>
                      
                      {/* Center Content Mock */}
                      <div className="col-span-3 md:col-span-2 space-y-6">
                           <div className="flex items-center gap-4 p-4 bg-indigo-50/50 dark:bg-indigo-900/20 rounded-xl border border-indigo-100 dark:border-indigo-800">
                                <Activity className="text-indigo-600 dark:text-indigo-400" />
                                <div>
                                    <div className="h-4 bg-indigo-200 dark:bg-indigo-800 rounded w-32 mb-2"></div>
                                    <div className="h-3 bg-indigo-100 dark:bg-indigo-900 rounded w-48"></div>
                                </div>
                           </div>
                           <div className="space-y-3">
                                {[1,2,3].map(i => (
                                    <div key={i} className="h-16 bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm"></div>
                                ))}
                           </div>
                      </div>
                  </div>

                  {/* Overlay Gradient for "Coming to Life" effect */}
                  <div className="absolute bottom-0 left-0 w-full h-64 bg-linear-to-t from-slate-50 dark:from-slate-950 to-transparent"></div>
              </div>
           </div>
        </motion.div>
      </section>

      {/* 4. Bento Grid Features */}
      <section className="py-32 px-6 max-w-7xl mx-auto">
         <div className="text-center mb-16">
            <h2 className="text-3xl font-bold mb-4">Under the Hood</h2>
            <p className="text-slate-500 dark:text-slate-400">Built for speed, accuracy, and scalability.</p>
         </div>

         <div className="grid grid-cols-1 md:grid-cols-3 gap-6 auto-rows-[300px]">
             {/* Feature 1 (Large) */}
             <div className="md:col-span-2 bg-slate-100 dark:bg-slate-900 rounded-3xl p-8 relative overflow-hidden group">
                 <div className="absolute top-8 right-8 bg-white dark:bg-slate-800 p-3 rounded-2xl shadow-sm">
                    <Brain className="w-8 h-8 text-purple-500" />
                 </div>
                 <div className="mt-auto h-full flex flex-col justify-end relative z-10">
                    <h3 className="text-2xl font-bold mb-2">Dual-Engine Retrieval</h3>
                    <p className="text-slate-500 dark:text-slate-400 max-w-md">combines dense vector embeddings (FAISS) with structured knowledge graphs (Neo4j) to ground every answer.</p>
                 </div>
                 <div className="absolute inset-0 bg-linear-to-br from-purple-500/5 to-transparent opacity-0 group-hover:opacity-100 transition duration-500"></div>
             </div>

             {/* Feature 2 */}
             <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-8 flex flex-col justify-between hover:border-indigo-500 transition duration-300">
                  <div className="w-12 h-12 bg-blue-100 dark:bg-blue-900/30 rounded-full flex items-center justify-center text-blue-600 dark:text-blue-400">
                     <FileText className="w-6 h-6" />
                  </div>
                  <div>
                    <h3 className="text-xl font-bold mb-2">Hybrid OCR</h3>
                    <p className="text-slate-500 text-sm">Handles digital PDFs and messy handwritten scans effortlessly.</p>
                  </div>
             </div>

             {/* Feature 3 */}
             <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-8 flex flex-col justify-between hover:border-green-500 transition duration-300">
                  <div className="w-12 h-12 bg-green-100 dark:bg-green-900/30 rounded-full flex items-center justify-center text-green-600 dark:text-green-400">
                     <ShieldCheck className="w-6 h-6" />
                  </div>
                  <div>
                    <h3 className="text-xl font-bold mb-2">Zero Hallucinations</h3>
                    <p className="text-slate-500 text-sm">Every diagnosis cites specific evidence from the Knowledge Graph.</p>
                  </div>
             </div>

              {/* Feature 4 (Large) */}
             <div className="md:col-span-2 bg-slate-900 dark:bg-slate-800 text-white rounded-3xl p-8 flex flex-col justify-center items-center text-center relative overflow-hidden">
                 <div className="relative z-10">
                    <h3 className="text-3xl font-bold mb-4">Ready to try?</h3>
                    <Link to="/app">
                        <button className="bg-white text-slate-900 px-8 py-3 rounded-full font-bold hover:bg-slate-200 transition">
                            Open Dashboard
                        </button>
                    </Link>
                 </div>
                 <div className="absolute inset-0 bg-linear-to-r from-indigo-600 to-blue-600 opacity-20"></div>
             </div>
         </div>
      </section>

      {/* Footer */}
      <footer className="py-8 text-center text-slate-400 text-sm border-t border-slate-200 dark:border-slate-800">
        <p>© 2026 NeoMed AI. Hackathon Edition.</p>
      </footer>

    </div>
  );
}