import React, { useState, useRef, useEffect } from "react";
import axios from "axios";
import { Link } from "react-router-dom";
import {
  Stethoscope, Upload, Activity, Sun, Moon, FileText, Settings,
  LogOut, Brain, CheckCircle2, Sparkles, User,
  ListChecks, AlignLeft, Info, GitBranch, AlertTriangle, Pill, ClipboardList, Thermometer,
  BookOpen, Eye, Edit3 // Added Eye/Edit icons
} from "lucide-react";
import { AnimatePresence, motion } from "framer-motion";

// --- TYPES ---

interface GraphPath {
  start_node: string;
  relationship: string;
  end_node: string;
  source_db: string;
}

interface DiagnosisResult {
  disease: string;
  matches: number;
  matched_symptoms: string[];
  confidence_score: number;
  trace_chain: GraphPath[];
}

interface Medication {
  name: string;
  dosage?: string;
  citations?: string; // e.g. "[3]"
}

interface MedicalSummary {
  patient_demographics?: {
    age?: string;
    sex?: string;
  };
  chief_complaint?: string;
  history_of_present_illness?: string;
  past_medical_history?: string[];
  medications?: Array<Medication | string>;
  procedures?: string[];
  diagnostic_findings?: string[];
  assessment?: string;
  plan?: string;
  clinical_course?: string;
  [key: string]: any;
}

// Helper Type for Citation Map
interface CitationSource {
  date: string;
  context: string;
  source_chunk_index: number;
  entities: Array<{
    text: string;
    label: string;
    confidence: number;
  }>;
}

export default function Dashboard({ toggleTheme, currentTheme }: { toggleTheme: () => void, currentTheme: string }) {
  const [inputText, setInputText] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);

  // Highlight State
  const [highlightContext, setHighlightContext] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  const [activeTab, setActiveTab] = useState<'summary' | 'diagnosis' | 'evidence'>('summary');
  const [expandedDiagnosis, setExpandedDiagnosis] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'edit' | 'view'>('edit'); // Track View Mode

  // Scroll to highlight when it changes
  useEffect(() => {
    if (highlightContext && viewMode === 'view') {
      // Short delay to allow render
      setTimeout(() => {
        const mark = document.getElementById('highlight-mark');
        if (mark) {
          mark.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
      }, 100);
    }
  }, [highlightContext, viewMode]);

  // --- API HANDLERS ---

  const handleAnalyze = async () => {
    if (!inputText) return;
    setLoading(true);
    setActiveTab('summary');
    setResult(null);

    try {
      const response = await axios.post("http://localhost:8000/analyze/text", {
        text: inputText,
      });
      setResult(response.data);
      setViewMode('view'); // Auto-switch to view mode
    } catch (error: any) {
      console.error("Backend Error:", error);
      alert(`Analysis Failed: ${error.response?.data?.detail || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setLoading(true);
    setActiveTab('summary');
    setResult(null);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await axios.post("http://localhost:8000/analyze/file", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      const data = response.data;
      setResult(data);

      // Reconstruct Text from Timeline for Display
      if (data.timeline && Array.isArray(data.timeline)) {
        const extractedText = data.timeline
          .map((t: any) => `Timeframe: ${t.date}\n${t.text || ''}`)
          .join("\n\n----------------------------------------\n\n");

        setInputText(extractedText);
        setViewMode('view'); // Switch to view mode to show text
      }

    } catch (error: any) {
      console.error("Backend Error:", error);
      alert(`File Upload Failed: ${error.response?.data?.detail || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleCitationClick = (citationRef: string) => {
    // Handle multiple citations: extract all IDs from formats like "1,2,3" or "1, 2, 3"
    const citationIds = citationRef
      .replace(/[\[\]\s]/g, '') // Remove brackets and spaces
      .split(',')
      .filter(id => id.length > 0);

    console.log(`[Citation Click] Raw: "${citationRef}" → IDs: [${citationIds.join(', ')}]`);
    console.log('[Citation Map Keys]:', Object.keys(result?.citation_map || {}));

    // Find all valid citations
    const validCitations = citationIds
      .map(id => ({
        id,
        data: result?.citation_map?.[id]
      }))
      .filter(item => item.data !== undefined);

    if (validCitations.length === 0) {
      console.warn(`[Citation NOT FOUND] None of the IDs found in map.`);
      return;
    }

    // Select the citation with the shortest context
    const shortestCitation = validCitations.reduce((shortest, current) => {
      return current.data.context.length < shortest.data.context.length
        ? current
        : shortest;
    });

    console.log(`[Citation Selected] ID ${shortestCitation.id} (length: ${shortestCitation.data.context.length})`);
    setHighlightContext(shortestCitation.data.context);
    setViewMode('view');
  };

  // --- RENDER HELPERS ---

  const renderSection = (title: string, content: any, icon?: any) => {
    if (!content) return null;
    if (Array.isArray(content) && content.length === 0) return null;

    return (
      <div className="mb-6 p-4 bg-slate-50 dark:bg-slate-800/50 rounded-xl border border-slate-100 dark:border-slate-800">
        <div className="flex items-center gap-2 mb-3">
          {icon && <div className="text-indigo-500">{icon}</div>}
          <h4 className="font-bold text-slate-900 dark:text-slate-200 uppercase text-xs tracking-wider">
            {title}
          </h4>
        </div>

        <div className="text-sm leading-relaxed text-slate-700 dark:text-slate-300">
          {Array.isArray(content) ? (
            <ul className="list-disc pl-4 space-y-1">
              {content.map((item, idx) => {
                if (typeof item === 'object' && item !== null) {
                  return (
                    <li key={idx}>
                      <span className="font-medium text-slate-800 dark:text-slate-200">{item.name}</span>
                      {item.dosage && <span className="text-slate-500 dark:text-slate-500 text-xs ml-2 rounded-full bg-slate-200 dark:bg-slate-800 px-2 py-0.5">{item.dosage}</span>}
                      {item.citations && (
                        <sup
                          className="text-indigo-500 font-bold text-[10px] ml-1 cursor-pointer hover:underline"
                          onClick={() => handleCitationClick(item.citations)}
                          title="Click to see source context"
                        >
                          {item.citations}
                        </sup>
                      )}
                    </li>
                  )
                }
                return (
                  <li key={idx}>
                    {typeof item === 'string' ? renderTextWithCitations(item) : item}
                  </li>
                );
              })}
            </ul>
          ) : (
            <p className="whitespace-pre-line">
              {renderTextWithCitations(content)}
            </p>
          )}
        </div>
      </div>
    );
  };

  const renderTextWithCitations = (text: string) => {
    // Regex to match [1] or [1, 2, 3] or [123, 124, 125, 126]
    const parts = text.split(/(\[\s*\d+(?:\s*,\s*\d+)*\s*\])/g);

    return parts.map((part, i) => {
      // Test if this part is a citation block
      if (/^\[\s*\d+(?:\s*,\s*\d+)*\s*\]$/.test(part)) {
        // Extract all numbers: "123, 124, 125" -> ["123", "124", "125"]
        const citationNumbers = part.match(/\d+/g) || [];

        return (
          <span key={i} className="inline-flex items-center">
            {citationNumbers.map((num, idx) => (
              <sup
                key={idx}
                onClick={() => handleCitationClick(num)}
                className="text-indigo-500 font-bold cursor-pointer hover:underline text-[10px] mx-0.5"
                title={`View Evidence [${num}]`}
              >
                [{num}]{idx < citationNumbers.length - 1 && ','}
              </sup>
            ))}
          </span>
        );
      }
      return <span key={i}>{part}</span>;
    });
  };

  return (
    <div className="flex h-screen bg-slate-50 dark:bg-[#0B0F19] font-sans text-slate-900 dark:text-slate-100 transition-colors duration-300 overflow-hidden">

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col relative overflow-hidden min-w-0">

        {/* Header */}
        <header className="h-16 flex items-center justify-between px-8 border-b border-slate-200 dark:border-slate-800 bg-white/80 dark:bg-slate-900/80 backdrop-blur-md z-10 shadow-sm">
          <div className="flex items-center gap-4">
            <div className="bg-indigo-600 p-1.5 rounded-lg shadow-[0_0_15px_rgba(79,70,229,0.4)]">
              <Stethoscope className="text-white w-5 h-5" />
            </div>
            <div className="w-px h-6 bg-slate-300 dark:bg-slate-700 mx-1"></div>
            <div className="flex flex-col">
              <span className="text-sm font-bold tracking-tight leading-none text-slate-900 dark:text-white">NeoMed</span>
              <span className="text-[10px] font-medium text-slate-500 uppercase tracking-wider">Clinical Intelligence</span>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <button onClick={toggleTheme} className="p-2 rounded-full border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 hover:text-indigo-500 transition shadow-sm">
              {currentTheme === 'dark' ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
            </button>
            <div className="h-6 w-px bg-slate-200 dark:bg-slate-700"></div>
            <Link to="/">
              <button className="flex items-center gap-2 text-sm font-medium text-slate-500 hover:text-red-500 transition px-3 py-1.5 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/10">
                <LogOut className="w-4 h-4" /> <span className="hidden sm:inline">Exit</span>
              </button>
            </Link>
          </div>
        </header>

        {/* Workspace Grid */}
        <div className="flex-1 p-4 md:p-8 grid grid-cols-1 lg:grid-cols-2 gap-8 overflow-hidden max-w-[1920px] mx-auto w-full">

          {/* LEFT: Editor/Viewer Pane */}
          <div className="flex flex-col h-full bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm overflow-hidden group focus-within:ring-2 ring-indigo-500/30 transition-all">

            {/* Editor Toolbar with Toggle */}
            <div className="h-14 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between px-4 bg-slate-50/50 dark:bg-slate-900/50">
              <div className="flex items-center gap-2 p-1 bg-slate-200 dark:bg-slate-800 rounded-lg">
                <button
                  onClick={() => setViewMode('edit')}
                  className={`flex items-center gap-2 px-3 py-1 text-xs font-bold rounded ${viewMode === 'edit' ? 'bg-white dark:bg-slate-700 shadow-sm' : 'text-slate-500'}`}
                >
                  <Edit3 className="w-3 h-3" /> INPUT
                </button>
                <button
                  onClick={() => setViewMode('view')}
                  disabled={!inputText}
                  className={`flex items-center gap-2 px-3 py-1 text-xs font-bold rounded ${viewMode === 'view' ? 'bg-white dark:bg-slate-700 shadow-sm' : 'text-slate-500'}`}
                >
                  <Eye className="w-3 h-3" /> PREVIEW
                </button>
              </div>

              <label className="flex items-center gap-2 px-3 py-1.5 bg-white dark:bg-slate-800 hover:bg-slate-50 dark:hover:bg-slate-700 border border-slate-200 dark:border-slate-700 rounded-lg text-xs font-medium text-slate-600 dark:text-slate-300 transition cursor-pointer shadow-sm group/btn">
                <Upload className="w-3.5 h-3.5 group-hover/btn:text-indigo-500 transition-colors" />
                Upload Scan
                <input type="file" className="hidden" onChange={handleFileUpload} accept=".pdf,.png,.jpg,.jpeg" />
              </label>
            </div>

            {/* Content Area - Toggle between Textarea and Div */}
            {viewMode === 'edit' ? (
              <textarea
                className="flex-1 p-6 bg-transparent outline-none resize-none text-slate-700 dark:text-slate-300 font-mono text-sm leading-8 placeholder:text-slate-300 dark:placeholder:text-slate-700"
                placeholder="// ENTER CLINICAL DATA...&#10;&#10;PATIENT:    58M&#10;CC:         Substernal Chest Pain (8/10)&#10;ONSET:      2 hours ago&#10;VITALS:     BP 160/95, HR 110, O2 94% RA&#10;HISTORY:    HTN (non-compliant), Hyperlipidemia"
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                spellCheck="false"
              />
            ) : (
              <div className="flex-1 p-6 overflow-y-auto font-mono text-sm leading-8 text-slate-700 dark:text-slate-300 bg-slate-50/50 dark:bg-black/20 whitespace-pre-wrap">
                {highlightContext ? (
                  // Fuzzy Highlight: Try to find context even if spacing differs
                  (() => {
                    // Normalize both strings (remove extra spaces, newlines for matching)
                    const normalizedInput = inputText.replace(/\s+/g, ' ');
                    const normalizedContext = highlightContext.replace(/\s+/g, ' ');

                    const index = normalizedInput.indexOf(normalizedContext);

                    if (index !== -1) {
                      // Calculate original position by counting characters
                      let charCount = 0;
                      let originalIndex = 0;
                      for (let i = 0; i < inputText.length; i++) {
                        if (inputText[i] !== '\n' && inputText[i] !== '\r') charCount++;
                        if (charCount === index) {
                          originalIndex = i;
                          break;
                        }
                      }

                      const before = inputText.substring(0, originalIndex);
                      const match = inputText.substring(originalIndex, originalIndex + highlightContext.length);
                      const after = inputText.substring(originalIndex + highlightContext.length);

                      return (
                        <>
                          <span>{before}</span>
                          <mark
                            id="highlight-mark"
                            className="bg-yellow-200 dark:bg-yellow-900/50 text-slate-900 dark:text-white px-1 py-0.5 rounded border border-yellow-300 dark:border-yellow-700 shadow-[0_0_15px_rgba(234,179,8,0.3)] animate-pulse"
                          >
                            {match}
                          </mark>
                          <span>{after}</span>
                        </>
                      );
                    } else {
                      // Fallback: Show the whole text with a warning
                      console.warn('[Highlight] Context not found in text. Showing full text.');
                      return <>{inputText}</>
                    }
                  })()
                ) : inputText}
              </div>
            )}


            {/* Action Bar */}
            <div className="p-4 border-t border-slate-100 dark:border-slate-800 bg-slate-50 dark:bg-[#0B0F19] flex justify-between items-center">
              <span className="text-[10px] text-slate-400 font-mono hidden sm:inline-block">
                READY • {(inputText.length).toLocaleString()} CHARS
              </span>
              <button
                onClick={handleAnalyze}
                disabled={loading || !inputText}
                className="bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-300 dark:disabled:bg-slate-800 disabled:cursor-not-allowed text-white px-6 py-2.5 rounded-xl font-bold text-sm shadow-xl shadow-indigo-600/20 flex items-center gap-2 transition-all hover:scale-105 active:scale-95"
              >
                {loading ? <Activity className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
                {loading ? 'ANALYZING GRAPH...' : 'GENERATE DIAGNOSIS'}
              </button>
            </div>
          </div>

          {/* RIGHT: Analysis Pane */}
          <div className="flex flex-col h-full bg-slate-100 dark:bg-[#0F1523] rounded-2xl border border-slate-200 dark:border-slate-800 relative overflow-hidden shadow-inner">

            {/* Result Tabs */}
            {/* Added 'Evidence' Tab */}
            <div className="h-14 border-b border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 flex px-2 items-end gap-2">
              <button
                onClick={() => setActiveTab('summary')}
                className={`
                        flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-all outline-none
                        ${activeTab === 'summary'
                    ? 'border-indigo-500 text-indigo-600 dark:text-indigo-400 bg-indigo-50/50 dark:bg-indigo-900/20'
                    : 'border-transparent text-slate-500 hover:text-slate-700 dark:hover:text-slate-200'}
                      `}
              >
                <AlignLeft className="w-4 h-4" /> Summary
              </button>
              <button
                onClick={() => setActiveTab('diagnosis')}
                disabled={!result}
                className={`
                        flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-all outline-none
                        ${activeTab === 'diagnosis'
                    ? 'border-indigo-500 text-indigo-600 dark:text-indigo-400 bg-indigo-50/50 dark:bg-indigo-900/20'
                    : 'border-transparent text-slate-500 hover:text-slate-700 dark:hover:text-slate-200'}
                        ${!result && 'opacity-50 cursor-not-allowed'}
                      `}
              >
                <ListChecks className="w-4 h-4" /> Differential <span className="text-[10px] bg-indigo-100 dark:bg-indigo-900 rounded-full px-1.5 py-0.5 ml-1 hidden lg:inline-block">AI</span>
              </button>

              <button
                onClick={() => setActiveTab('evidence')}
                disabled={!result?.citation_map}
                className={`
                        flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-all outline-none
                        ${activeTab === 'evidence'
                    ? 'border-indigo-500 text-indigo-600 dark:text-indigo-400 bg-indigo-50/50 dark:bg-indigo-900/20'
                    : 'border-transparent text-slate-500 hover:text-slate-700 dark:hover:text-slate-200'}
                        ${!result?.citation_map && 'opacity-50 cursor-not-allowed'}
                      `}
              >
                <BookOpen className="w-4 h-4" /> Evidence
              </button>
            </div>

            {/* Content Content - Scrollable */}
            <div className="flex-1 overflow-y-auto p-6 scrollbar-thin scrollbar-thumb-slate-300 dark:scrollbar-thumb-slate-700">

              {/* Empty State */}
              {!result && !loading && (
                <div className="h-full flex flex-col items-center justify-center text-slate-400 opacity-40 select-none">
                  <div className="w-24 h-24 bg-slate-200 dark:bg-slate-800/50 rounded-full flex items-center justify-center mb-6">
                    <Brain className="w-10 h-10 text-slate-400 dark:text-slate-600" />
                  </div>
                  <p className="font-mono text-sm tracking-widest uppercase">Awaiting Input Stream</p>
                </div>
              )}

              {/* Loading Phase */}
              {loading && (
                <div className="p-4 space-y-8">
                  <div className="flex items-center gap-4 mb-8">
                    <div className="relative">
                      <div className="w-6 h-6 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
                      <div className="absolute inset-0 border-2 border-indigo-500/20 rounded-full"></div>
                    </div>
                    <span className="text-xs font-mono text-indigo-500 animate-pulse tracking-widest uppercase">Processing clinical data...</span>
                  </div>
                  <div className="space-y-4 opacity-50">
                    <div className="h-4 bg-slate-300 dark:bg-slate-700 rounded w-3/4"></div>
                    <div className="h-4 bg-slate-300 dark:bg-slate-700 rounded w-1/2"></div>
                    <div className="h-32 bg-slate-300 dark:bg-slate-700 rounded-xl"></div>
                  </div>
                </div>
              )}

              {/* Results Display */}
              {result && !loading && (
                <div className="animate-in fade-in slide-in-from-bottom-2 duration-300">

                  {/* WARNINGS BLOCK */}
                  {result.warnings && result.warnings.length > 0 && (
                    <div className="mb-6 p-4 bg-amber-50 dark:bg-amber-900/10 border border-amber-200 dark:border-amber-800 rounded-lg flex gap-3 text-sm text-amber-800 dark:text-amber-200">
                      <AlertTriangle className="w-5 h-5 shrink-0" />
                      <div className="space-y-1">
                        <p className="font-bold">Analysis completed with warnings:</p>
                        <ul className="list-disc pl-4 space-y-1 text-xs opacity-90">
                          {result.warnings.map((w: string, i: number) => (
                            <li key={i}>{w}</li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  )}

                  {/* TAB 1: SUMMARY */}
                  {activeTab === 'summary' && (
                    <div className="bg-white dark:bg-slate-900 p-8 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm relative overflow-hidden">
                      <div className="absolute top-0 left-0 w-1.5 h-full bg-emerald-500"></div>

                      {/* Patient Header */}
                      {result.summary?.patient_demographics && (
                        <div className="flex gap-4 mb-8 pb-4 border-b border-slate-100 dark:border-slate-800">
                          <div className="w-12 h-12 rounded-full bg-emerald-100 dark:bg-emerald-900/30 flex items-center justify-center text-emerald-600 dark:text-emerald-400 font-bold">
                            PT
                          </div>
                          <div>
                            <h3 className="text-lg font-bold text-slate-900 dark:text-white">Clinical Summary</h3>
                            <p className="text-sm text-slate-500 font-mono mt-1">
                              {result.summary.patient_demographics.age} • {result.summary.patient_demographics.sex}
                            </p>
                          </div>
                          {/* Confidence Score for Validation */}
                          {result.validation && (
                            <div className="ml-auto text-right">
                              <div className={`text-xl font-bold ${result.validation.citation_coverage?.coverage_percent > 80 ? 'text-emerald-500' : 'text-amber-500'}`}>
                                {result.validation.citation_coverage?.coverage_percent || 0}%
                              </div>
                              <div className="text-[10px] uppercase text-slate-400 font-medium">Fact Coverage</div>
                            </div>
                          )}
                        </div>
                      )}

                      {/* Render ALL Sections with Icons */}
                      {renderSection("Chief Complaint", result.summary?.chief_complaint)}
                      {renderSection("History of Present Illness", result.summary?.history_of_present_illness)}

                      {renderSection("Past Medical History", result.summary?.past_medical_history, <ClipboardList className="w-4 h-4" />)}
                      {renderSection("Medications", result.summary?.medications, <Pill className="w-4 h-4" />)}
                      {renderSection("Diagnostic Findings", result.summary?.diagnostic_findings, <Activity className="w-4 h-4" />)}
                      {renderSection("Procedures", result.summary?.procedures, <Thermometer className="w-4 h-4" />)}

                      {renderSection("Assessment & Plan", result.summary?.assessment)}
                      {renderSection("Plan", result.summary?.plan)}
                      {renderSection("Clinical Course", result.summary?.clinical_course)}

                    </div>
                  )}

                  {/* TAB 2: DIAGNOSIS with Traceability */}
                  {activeTab === 'diagnosis' && (
                    <div className="space-y-4">
                      <div className="flex items-center justify-between mb-2">
                        <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest">
                          Knowledge Graph Matches
                        </h3>
                        <span className="text-[10px] font-mono text-emerald-500 bg-emerald-500/10 px-2 py-1 rounded border border-emerald-500/20">
                          {result.differential_diagnosis?.length || 0} POTENTIAL MATCHES
                        </span>
                      </div>

                      {(!result.differential_diagnosis || result.differential_diagnosis.length === 0) && (
                        <div className="text-center py-12 border-2 border-dashed border-slate-200 dark:border-slate-800 rounded-xl">
                          <AlertTriangle className="w-8 h-8 text-slate-300 mx-auto mb-2" />
                          <p className="text-slate-500 text-sm">No graph matches found.</p>
                          <p className="text-xs text-slate-400 mt-1">Try adding more specific symptoms like "fever" or "chest pain".</p>
                        </div>
                      )}

                      {result.differential_diagnosis?.map((diag: DiagnosisResult, idx: number) => {
                        const isExpanded = expandedDiagnosis === diag.disease;

                        return (
                          <div
                            key={idx}
                            onClick={() => setExpandedDiagnosis(isExpanded ? null : diag.disease)}
                            className={`
              group bg-white dark:bg-slate-900 border p-5 rounded-xl transition-all cursor-pointer relative overflow-hidden
              ${isExpanded
                                ? 'border-indigo-500 dark:border-indigo-500 ring-1 ring-indigo-500/30'
                                : 'border-slate-200 dark:border-slate-800 hover:border-indigo-500/50'}
          `}
                          >
                            {/* Top Row - Disease Header */}
                            <div className="flex justify-between items-start relative z-10">
                              <div className="flex gap-4">
                                <div className={`
                      w-10 h-10 rounded-lg border flex items-center justify-center font-bold text-sm transition-all
                      ${isExpanded
                                    ? 'bg-indigo-600 text-white border-indigo-600'
                                    : 'bg-slate-50 dark:bg-slate-800 border-slate-100 dark:border-slate-700 text-slate-400 group-hover:text-indigo-500'}
                  `}>
                                  {idx + 1}
                                </div>
                                <div>
                                  <h4 className="font-bold text-slate-800 dark:text-slate-100 group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors text-lg">
                                    {diag.disease}
                                  </h4>
                                  <div className="flex items-center gap-3 mt-2 text-xs">
                                    <span className="px-2 py-0.5 rounded bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400 font-medium">
                                      Matched: {diag.matches}/{diag.total_disease_symptoms || '?'}
                                    </span>
                                    <span className="text-slate-400 font-mono">
                                      {diag.matched_symptoms.slice(0, 3).join(", ")}
                                      {diag.matched_symptoms.length > 3 && "..."}
                                    </span>
                                  </div>
                                </div>
                              </div>

                              <div className="text-right">
                                <div className="text-2xl font-bold text-indigo-600 dark:text-indigo-400 slashed-zero">
                                  {diag.confidence_score}%
                                </div>
                                <div className="text-[9px] font-bold text-slate-400 uppercase tracking-wide">Confidence</div>
                              </div>
                            </div>

                            {/* Expanded Section - Graph Visualization */}
                            <AnimatePresence>
                              {isExpanded && (
                                <motion.div
                                  initial={{ height: 0, opacity: 0 }}
                                  animate={{ height: "auto", opacity: 1 }}
                                  exit={{ height: 0, opacity: 0 }}
                                  className="mt-6 pt-6 border-t border-slate-100 dark:border-slate-800"
                                >
                                  {/* Visual Graph Representation */}
                                  <div className="mb-6">
                                    <h5 className="text-xs font-bold text-slate-400 uppercase mb-4 tracking-widest flex items-center gap-2">
                                      <GitBranch className="w-4 h-4" /> Reasoning Graph
                                    </h5>

                                    {/* Central Disease Node */}
                                    <div className="flex flex-col items-center mb-4">
                                      <div className="bg-gradient-to-br from-indigo-500 to-indigo-600 text-white px-6 py-3 rounded-xl shadow-lg font-bold text-sm border-2 border-indigo-400">
                                        {diag.disease}
                                      </div>
                                      <div className="w-0.5 h-6 bg-gradient-to-b from-indigo-400 to-slate-300 dark:to-slate-700"></div>
                                    </div>

                                    {/* Symptom Connections Grid */}
                                    <div className="grid grid-cols-2 gap-3">
                                      {diag.matched_symptoms.map((symptom, sIdx) => (
                                        <div key={sIdx} className="flex flex-col items-center">
                                          {/* Connection Line */}
                                          <div className="w-0.5 h-4 bg-emerald-300 dark:bg-emerald-700"></div>

                                          {/* Symptom Node */}
                                          <div className="w-full bg-emerald-50 dark:bg-emerald-900/20 border-2 border-emerald-300 dark:border-emerald-700 rounded-lg p-3 text-center">
                                            <div className="text-xs font-bold text-emerald-700 dark:text-emerald-400 mb-1">
                                              {symptom}
                                            </div>
                                            <div className="flex items-center justify-center gap-1">
                                              <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></div>
                                              <span className="text-[10px] text-slate-500 dark:text-slate-400">Matched</span>
                                            </div>
                                          </div>
                                        </div>
                                      ))}
                                    </div>

                                    {/* Source Attribution */}
                                    <div className="mt-4 text-center">
                                      <span className="text-[10px] px-3 py-1 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-500 border border-slate-200 dark:border-slate-700">
                                        Source: {diag.trace_chain?.[0]?.source_db || 'Knowledge Graph'}
                                      </span>
                                    </div>
                                  </div>

                                  {/* Detailed Logic Trace (Technical View) */}
                                  <div className="pt-4 border-t border-slate-100 dark:border-slate-800">
                                    <details className="group/details">
                                      <summary className="text-xs font-bold text-slate-400 uppercase tracking-widest cursor-pointer hover:text-indigo-500 transition flex items-center gap-2">
                                        <Info className="w-3 h-3" />
                                        Technical Trace
                                        <span className="ml-auto text-[10px] opacity-50 group-open/details:rotate-180 transition-transform">▼</span>
                                      </summary>
                                      <div className="mt-3 space-y-2">
                                        {diag.trace_chain?.map((trace, tIdx) => (
                                          <div key={tIdx} className="flex items-center text-xs font-mono text-slate-500 bg-slate-50 dark:bg-slate-800/50 p-2 rounded border border-slate-200 dark:border-slate-800">
                                            <span className="text-indigo-500 font-bold mr-2">{trace.start_node}</span>
                                            <span className="text-slate-300 mx-2">--[{trace.relationship}]--&gt;</span>
                                            <span className="text-slate-700 dark:text-slate-300">{trace.end_node}</span>
                                            <span className="ml-auto text-[10px] text-slate-400 border border-slate-200 dark:border-slate-700 px-1 rounded">{trace.source_db}</span>
                                          </div>
                                        ))}
                                      </div>
                                    </details>
                                  </div>
                                </motion.div>
                              )}
                            </AnimatePresence>
                          </div>
                        );
                      })}
                    </div>
                  )}

                  {/* TAB 3: EVIDENCE / CITATION MAP */}
                  {activeTab === 'evidence' && result.citation_map && (
                    <div className="space-y-6">
                      <div className="border-l-4 border-indigo-500 pl-4 py-1">
                        <h3 className="font-bold text-lg dark:text-white">Evidence Source Map</h3>
                        <p className="text-sm text-slate-500">
                          Verify summary claims against original extracted text segments.
                        </p>
                      </div>

                      <div className="grid gap-4">
                        {Object.entries(result.citation_map).map(([key, value]: [string, any]) => (
                          <div
                            key={key}
                            id={`citation-${key}`}
                            className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm scroll-mt-20 cursor-pointer hover:border-indigo-400 transition-colors"
                            onClick={() => {
                              setHighlightContext(value.context);
                              setViewMode('view');
                            }}
                          >
                            <div className="flex items-start gap-4">
                              <div className="w-8 h-8 shrink-0 bg-indigo-100 dark:bg-indigo-900/50 text-indigo-700 dark:text-indigo-400 font-bold rounded-lg flex items-center justify-center text-sm border border-indigo-200 dark:border-indigo-800">
                                [{key}]
                              </div>
                              <div className="flex-1 space-y-2">
                                <div className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-1">
                                  {value.date} • Confidence: {(value.entities[0]?.confidence * 100).toFixed(0)}%
                                </div>
                                <p className="text-xs font-mono text-slate-600 dark:text-slate-400 bg-slate-50 dark:bg-slate-800 p-3 rounded border border-slate-100 dark:border-slate-700">
                                  "{value.context}"
                                </p>
                                <div className="flex gap-2 flex-wrap">
                                  {value.entities.map((e: any, i: number) => (
                                    <span key={i} className="text-[10px] px-2 py-1 rounded bg-indigo-50 dark:bg-indigo-900/20 text-indigo-600 dark:text-indigo-300 border border-indigo-100 dark:border-indigo-800">
                                      {e.label}: <b>{e.text}</b>
                                    </span>
                                  ))}
                                </div>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>

        </div>
      </main>
    </div>
  );
}