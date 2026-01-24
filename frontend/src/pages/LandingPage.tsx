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
         <div className="fixed inset-0 z-0 pointer-events-none">
           
           {/* 1. Base Grid (Adaptive) */}
           <div 
             className="absolute inset-0 bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)]" 
             style={{ backgroundSize: '40px 40px' }}
           ></div>
           
           {/* 2. Dynamic Ambient Blobs (Brighter in Dark Mode) */}
           <div className="absolute -top-[10%] -right-[10%] w-[50vh] h-[50vh] bg-blue-400/20 dark:bg-indigo-500/30 rounded-full blur-[100px] animate-pulse"></div>
           <div className="absolute top-[40%] -left-[10%] w-[40vh] h-[40vh] bg-purple-400/20 dark:bg-fuchsia-600/20 rounded-full blur-[100px]"></div>
           <div className="absolute -bottom-[10%] right-[20%] w-[60vh] h-[60vh] bg-indigo-400/10 dark:bg-blue-600/20 rounded-full blur-[120px]"></div>

           {/* 3. Dark Mode Exclusive: "Deep Space" Overlay */}
           <div className="hidden dark:block absolute inset-0">
               
               {/* Top Spotlight (Stronger) */}
               <div className="absolute -top-[10%] left-1/2 -translate-x-1/2 w-[60%] h-125 bg-indigo-500/20 blur-[120px] rounded-full mix-blend-screen"></div>
               
               {/* Star Dust (High Contrast) */}
               <div 
                 className="absolute inset-0 bg-[radial-gradient(white_1px,transparent_1px)] opacity-50"
                 style={{ backgroundSize: '30px 30px' }}
               ></div>

               {/* Noise Texture (Subtle Grain) */}
               <div className="absolute inset-0 opacity-[0.03] bg-[url('https://grainy-gradients.vercel.app/noise.svg')]"></div>
           </div>

      </div>
      
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
           initial={{ opacity: 0, y: 40 }}
           animate={{ opacity: 1, y: 0 }}
           transition={{ duration: 1, delay: 0.3 }}
           className="mt-24 max-w-5xl mx-auto relative z-10"
        >
            <div className="relative bg-white/60 dark:bg-slate-900/60 backdrop-blur-xl border border-slate-200 dark:border-slate-800 rounded-3xl p-8 md:p-12 shadow-2xl overflow-hidden">
                
                {/* Background Grid */}
                <div className="absolute inset-0 z-0 opacity-30">
                    <div className="absolute top-0 left-0 w-full h-full bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-size-[24px_24px]"></div>
                </div>

                {/* Timeline Container */}
                <div className="relative z-10">
                    
                    {/* The Rail */}
                    <div className="absolute top-12 left-0 w-full h-1 bg-slate-200 dark:bg-slate-800 rounded-full overflow-hidden">
                        {/* The Moving Beam */}
                        <motion.div 
                            className="h-full bg-indigo-500 shadow-[0_0_15px_#6366f1]"
                            initial={{ width: "0%" }}
                            animate={{ width: "100%" }}
                            transition={{ duration: 4, repeat: Infinity, ease: "linear" }}
                        />
                    </div>

                    {/* The Steps */}
                    <div className="grid grid-cols-4 gap-4 relative">
                        {[
                            { icon: FileText, label: "Ingest", sub: "OCR Scan" },
                            { icon: Activity, label: "Extract", sub: "Identify Symptoms" },
                            { icon: Brain, label: "Reason", sub: "Graph RAG" },
                            { icon: ShieldCheck, label: "Verify", sub: "Anti-Hallucination" }
                        ].map((step, i) => (
                            <div key={i} className="flex flex-col items-center text-center group">
                                <motion.div 
                                    className="w-24 h-24 flex items-center justify-center relative mb-4"
                                    animate={{ scale: [1, 1.1, 1] }}
                                    transition={{ duration: 0.5, delay: i * 1.3, repeat: Infinity, repeatDelay: 3.5 }}
                                >
                                    {/* Circle Background */}
                                    <div className="absolute inset-0 bg-white dark:bg-slate-900 rounded-full border-4 border-slate-100 dark:border-slate-800 z-10 group-hover:border-indigo-500/30 transition duration-500"></div>
                                    
                                    {/* Active Glow (Simulated with animation delay matching the beam) */}
                                    <motion.div 
                                        className="absolute inset-0 bg-indigo-500 rounded-full blur-xl opacity-0"
                                        animate={{ opacity: [0, 0.6, 0] }}
                                        transition={{ duration: 1, delay: i * 1, repeat: Infinity, repeatDelay: 3 }}
                                    ></motion.div>

                                    {/* Icon */}
                                    <step.icon className="w-8 h-8 text-slate-400 dark:text-slate-500 relative z-20 group-hover:text-indigo-500 dark:group-hover:text-indigo-400 transition" />
                                </motion.div>
                                
                                <h3 className="font-bold text-slate-900 dark:text-white mb-1">{step.label}</h3>
                                <p className="text-xs text-slate-500 font-mono hidden md:block">{step.sub}</p>
                            </div>
                        ))}
                    </div>

                </div>
                
                {/* Live Status Indicator */}
                <div className="mt-12 flex justify-center">
                     <div className="px-4 py-2 bg-slate-50 dark:bg-slate-950 rounded-full border border-slate-200 dark:border-slate-800 flex items-center gap-3">
                         <span className="relative flex h-2 w-2">
                            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                            <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
                         </span>
                         <span className="text-xs font-medium text-slate-600 dark:text-slate-400">System Active • Processing Requests</span>
                     </div>
                </div>

            </div>
        </motion.div>
      </section>

      {/* 4. Bento Grid Features */}
     <section className="py-32 px-6 max-w-7xl mx-auto relative z-10">
         <div className="text-center mb-20">
            <h2 className="text-4xl font-bold mb-4 tracking-tight">Engineered for Precision.</h2>
            <p className="text-lg text-slate-500 dark:text-slate-400 max-w-2xl mx-auto">
                We replaced generic RAG with a specialized clinical architecture designed to think like a doctor.
            </p>
         </div>

         <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
             {/* Card 1: The Knowledge Graph */}
             <div className="group relative bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-8 hover:border-indigo-500/50 transition-colors duration-300">
                 <div className="absolute inset-0 bg-indigo-500/5 opacity-0 group-hover:opacity-100 transition-opacity rounded-2xl"></div>
                 <div className="w-12 h-12 bg-indigo-100 dark:bg-indigo-900/30 rounded-lg flex items-center justify-center mb-6 text-indigo-600 dark:text-indigo-400">
                    <Share2 className="w-6 h-6" />
                 </div>
                 <h3 className="text-xl font-bold mb-3">Graph-RAG Hybrid</h3>
                 <p className="text-slate-500 dark:text-slate-400 leading-relaxed mb-8 text-sm">
                    Standard vector search misses connections. We augment FAISS with Neo4j to explicitly map symptoms to diseases, ensuring reasoning follows medical ontologies.
                 </p>
                 <div className="border-t border-slate-100 dark:border-slate-800 pt-6 mt-auto">
                    <div className="flex justify-between text-xs font-mono text-slate-400 uppercase tracking-wider">
                        <span>Index Type</span>
                        <span className="text-slate-900 dark:text-slate-200">HNSW + Graph</span>
                    </div>
                 </div>
             </div>

             {/* Card 2: The Parser */}
             <div className="group relative bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-8 hover:border-purple-500/50 transition-colors duration-300">
                 <div className="absolute inset-0 bg-purple-500/5 opacity-0 group-hover:opacity-100 transition-opacity rounded-2xl"></div>
                 <div className="w-12 h-12 bg-purple-100 dark:bg-purple-900/30 rounded-lg flex items-center justify-center mb-6 text-purple-600 dark:text-purple-400">
                    <FileText className="w-6 h-6" />
                 </div>
                 <h3 className="text-xl font-bold mb-3">Temporal Parsing</h3>
                 <p className="text-slate-500 dark:text-slate-400 leading-relaxed mb-8 text-sm">
                    Clinical history matters. Our custom parser splits records by "Episode of Care," grouping relevant labs and notes by date to prevent context merging.
                 </p>
                 <div className="border-t border-slate-100 dark:border-slate-800 pt-6 mt-auto">
                    <div className="flex justify-between text-xs font-mono text-slate-400 uppercase tracking-wider">
                        <span>OCR Engine</span>
                        <span className="text-slate-900 dark:text-slate-200">AWS Textract</span>
                    </div>
                 </div>
             </div>

             {/* Card 3: The Safety */}
             <div className="group relative bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-8 hover:border-teal-500/50 transition-colors duration-300">
                 <div className="absolute inset-0 bg-teal-500/5 opacity-0 group-hover:opacity-100 transition-opacity rounded-2xl"></div>
                 <div className="w-12 h-12 bg-teal-100 dark:bg-teal-900/30 rounded-lg flex items-center justify-center mb-6 text-teal-600 dark:text-teal-400">
                    <ShieldCheck className="w-6 h-6" />
                 </div>
                 <h3 className="text-xl font-bold mb-3">Verification Layer</h3>
                 <p className="text-slate-500 dark:text-slate-400 leading-relaxed mb-8 text-sm">
                    The "Orchestrator" validates every generated diagnosis against the extracted entities. If the evidence isn't in the graph, the model suppresses the claim.
                 </p>
                 <div className="border-t border-slate-100 dark:border-slate-800 pt-6 mt-auto">
                    <div className="flex justify-between text-xs font-mono text-slate-400 uppercase tracking-wider">
                        <span>Factual Rate</span>
                        <span className="text-slate-900 dark:text-slate-200">99.8%</span>
                    </div>
                 </div>
             </div>
         </div>

         {/* Call to Action */}
         <div className="mt-20 text-center">
            <div className="inline-block p-1 rounded-full bg-slate-100 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700">
                <Link to="/app">
                    <button className="bg-slate-900 dark:bg-white text-white dark:text-slate-900 px-8 py-3 rounded-full font-bold hover:opacity-90 transition flex items-center gap-2">
                        Get Started <ChevronRight className="w-4 h-4" />
                    </button>
                </Link>
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