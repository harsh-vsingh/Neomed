import { useState } from "react";
import { Stethoscope, Upload, Mic, Search, ChevronRight, Activity, Sun, Moon } from "lucide-react";
import axios from "axios";

export default function Dashboard({ toggleTheme, currentTheme }: { toggleTheme: () => void, currentTheme: string }) {
  const [inputText, setInputText] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);

  const handleAnalyze = async () => {
    if (!inputText) return;
    setLoading(true);
    try {
      const response = await axios.post("http://localhost:8000/analyze/text", {
        text: inputText,
      });
      setResult(response.data);
    } catch (error) {
      console.error("Backend Error:", error);
      alert("Failed to connect to backend. Check console.");
    } finally{
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 text-slate-900 font-sans selection:bg-blue-100">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 px-6 py-4 flex items-center gap-3 sticky top-0 z-10 shadow-md">
        <div className="bg-blue-600 p-2 rounded-lg shadow-lg shadow-blue-600/20">
          <Stethoscope className="text-white w-6 h-6" />
        </div>
        <h1 className="text-xl font-bold bg-clip-text text-transparent bg-linear-to-r from-blue-700 to-cyan-600">
          NeoMed AI
        </h1>
        <button onClick={toggleTheme}>
             {currentTheme === 'dark' ? <Sun /> : <Moon />}
          </button>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-8 grid grid-cols-1 lg:grid-cols-2 gap-8">
        
        {/* LEFT COLUMN: Input */}
        <div className="space-y-6">
          <div>
            <h2 className="text-2xl font-bold text-slate-800">Patient Intake</h2>
            <p className="text-slate-500">Enter clinical notes to generate a differential diagnosis.</p>
          </div>

          <div className="bg-white p-1 rounded-2xl shadow-sm border border-slate-200 focus-within:ring-4 ring-blue-500/10 transition-all">
            {/* Toolbar */}
            <div className="flex gap-2 p-2 border-b border-slate-100 mb-1">
              <button className="flex items-center gap-2 px-3 py-2 bg-blue-50 hover:bg-blue-100 text-blue-700 rounded-lg text-sm font-medium transition-colors">
                <Mic className="w-4 h-4" /> Dictate
              </button>
              <button className="flex items-center gap-2 px-3 py-2 hover:bg-slate-100 text-slate-600 rounded-lg text-sm font-medium transition-colors">
                
                <Upload className="w-4 h-4" /> Upload PDF
              </button>
            </div>

            <textarea 
              className="w-full h-80 p-4 bg-transparent outline-none resize-none text-slate-700 text-lg leading-relaxed placeholder:text-slate-300"
              placeholder="e.g. 58yo male presents with crushing substernal chest pain..."
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
            />
          </div>

          <div className="flex justify-end">
            <button 
              onClick={handleAnalyze}
              disabled={loading || !inputText}
              className={`
                flex items-center gap-2 px-8 py-4 bg-linear-to-r from-blue-600 to-blue-700 
                text-white rounded-xl font-bold text-lg shadow-xl shadow-blue-600/20 
                hover:-translate-y-0.5 transition-all
                ${loading ? 'opacity-70 cursor-wait' : 'hover:shadow-blue-600/40'}
              `}
            >
              {loading ? (
                <>
                  <Activity className="w-6 h-6 animate-spin" /> Analyzing...
                </>
              ) : (
                <>
                  <Search className="w-6 h-6" /> Generate Diagnosis
                </>
              )}
            </button>
          </div>
        </div>

        {/* RIGHT COLUMN: Output */}
        <div className="space-y-6">
          <div>
            <h2 className="text-2xl font-bold text-slate-800">Analysis Results</h2>
            <p className="text-slate-500">AI-generated summary & evidence-based diagnosis.</p>
          </div>

          {result ? (
            <div className="space-y-6 animate-in fade-in slide-in-from-bottom-8 duration-700">
              
              {/* Summary Card */}
              <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200 relative overflow-hidden">
                <div className="absolute top-0 left-0 w-1 h-full bg-green-500"></div>
                <h3 className="text-sm font-bold text-slate-400 uppercase tracking-wider mb-3 flex items-center gap-2">
                  <Activity className="w-4 h-4 text-green-500" /> Clinical Summary
                </h3>
                <p className="text-slate-800 text-lg leading-relaxed">
                  {result.summary}
                </p>
              </div>

              {/* Diagnosis List Placeholder */}
              <div>
                <h3 className="tex-sm font-bold text-slate-400 uppercase tracking-wider mb-4">Differential Diagnosis</h3>
                <div className="space-y-3">
                  {[1, 2, 3].map((i) => (
                    <div key={i} className="bg-white p-4 rounded-xl shadow-sm border border-slate-200 hover:border-blue-400 transition-colors cursor-pointer group">
                      <div className="flex justify-between items-start">
                        <div className="flex gap-4">
                          <div className={`
                            w-10 h-10 rounded-full flex items-center justify-center font-bold text-lg
                            ${i === 1 ? 'bg-blue-100 text-blue-600' : 'bg-slate-100 text-slate-500'}
                          `}>
                            {i}
                          </div>
                          <div>
                            <h4 className="font-bold text-lg text-slate-800 group-hover:text-blue-600 transition-colors">
                              Diagnosis Placeholder {i}
                            </h4>
                            <div className="flex gap-2 mt-2">
                              <span className="bg-slate-100 text-slate-600 text-xs px-2 py-1 rounded-md font-medium">
                                Confidence: {(90 - i * 10)}%
                              </span>
                              <span className="bg-blue-50 text-blue-600 text-xs px-2 py-1 rounded-md font-medium border border-blue-100">
                                Evidence: Case #{400+i}
                              </span>
                            </div>
                          </div>
                        </div>
                        <ChevronRight className="text-slate-300 group-hover:text-blue-500 group-hover:translate-x-1 transition-all" />
                      </div>
                    </div>
                  ))}
                </div>
              </div>

            </div>
          ) : (
            // Empty State
            <div className="h-125 flex flex-col items-center justify-center border-2 border-dashed border-slate-200 rounded-3xl bg-slate-50/50 text-slate-400">
              <div className="bg-white p-6 rounded-full shadow-sm mb-6">
                <Activity className="w-12 h-12 text-slate-300" />
              </div>
              <p className="font-medium text-lg text-slate-500">Ready to analyze clinical data</p>
              <p className="text-sm">Patient history + Knowledge Graph = Diagnosis</p>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

