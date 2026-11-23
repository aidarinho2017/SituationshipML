"use client";

import { useCallback, useEffect, useState } from "react";
import { ArrowDown, Github, LockKeyhole, ScanText, Server, Sparkles } from "lucide-react";
import { Dashboard } from "@/components/dashboard";
import { ImportPanel } from "@/components/import-panel";
import { History } from "@/components/history";
import { analyzeChat, deleteAnalysis, getAnalysis, listAnalyses, parseChat, renameAnalysis, saveAnalysis } from "@/lib/api";
import { Analysis, Preview, SavedAnalysisSummary } from "@/lib/types";

const repository = process.env.NEXT_PUBLIC_REPOSITORY_URL || "https://github.com/aidarinho2017/SituationshipML";

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<Preview | null>(null);
  const [selected, setSelected] = useState<string[]>([]);
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [sessionGap, setSessionGap] = useState(8);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [history, setHistory] = useState<SavedAnalysisSummary[]>([]);
  const [historyError, setHistoryError] = useState("");
  const [savedId, setSavedId] = useState<string | null>(null);

  const refreshHistory = useCallback(async () => {
    try { setHistory(await listAnalyses()); setHistoryError(""); }
    catch (reason) { setHistoryError(reason instanceof Error ? reason.message : "Could not load saved analyses."); }
  }, []);

  useEffect(() => {
    listAnalyses()
      .then((items) => { setHistory(items); setHistoryError(""); })
      .catch((reason) => setHistoryError(reason instanceof Error ? reason.message : "Could not load saved analyses."));
  }, []);

  const loadFile = async (nextFile: File) => {
    setLoading(true); setError(""); setPreview(null); setSelected([]); setFile(nextFile);
    try {
      const nextPreview = await parseChat(nextFile);
      setPreview(nextPreview);
      setSelected(nextPreview.participants.slice(0, 2).map((person) => person.id));
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Could not read this file."); }
    finally { setLoading(false); }
  };

  const runAnalysis = async () => {
    if (!file || selected.length !== 2) return;
    setLoading(true); setError("");
    try { setAnalysis(await analyzeChat(file, selected, sessionGap)); setSavedId(null); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Analysis failed."); }
    finally { setLoading(false); }
  };

  const tryDemo = async () => {
    setLoading(true); setError("");
    try {
      const response = await fetch("/demo.json");
      if (!response.ok) throw new Error("Demo fixture is unavailable.");
      await loadFile(new File([await response.blob()], "situationship-demo.json", { type: "application/json" }));
      setTimeout(() => document.querySelector("#import")?.scrollIntoView({ behavior: "smooth" }), 50);
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Demo failed."); setLoading(false); }
  };

  const saveCurrent = async () => {
    if (!analysis || savedId) return;
    setLoading(true); setError("");
    try { const saved = await saveAnalysis(analysis); setSavedId(saved.id); await refreshHistory(); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Could not save this analysis."); }
    finally { setLoading(false); }
  };

  const openSaved = async (id: string) => {
    setLoading(true); setError("");
    try { const saved = await getAnalysis(id); setAnalysis(saved.analysis); setSavedId(saved.id); window.scrollTo(0, 0); }
    catch (reason) { setHistoryError(reason instanceof Error ? reason.message : "Could not open this analysis."); }
    finally { setLoading(false); }
  };

  const renameSaved = async (id: string, title: string) => {
    try { await renameAnalysis(id, title); await refreshHistory(); }
    catch (reason) { setHistoryError(reason instanceof Error ? reason.message : "Could not rename this analysis."); }
  };

  const deleteSaved = async (id: string) => {
    if (!window.confirm("Delete this saved analysis? This cannot be undone.")) return;
    try { await deleteAnalysis(id); await refreshHistory(); }
    catch (reason) { setHistoryError(reason instanceof Error ? reason.message : "Could not delete this analysis."); }
  };

  if (analysis) return <Dashboard analysis={analysis} saved={Boolean(savedId)} saving={loading} error={error} onSave={saveCurrent} onReset={() => { setAnalysis(null); setPreview(null); setFile(null); setSelected([]); setSavedId(null); setError(""); }} />;

  return <main>
    <nav className="shell flex items-center justify-between border-b rule py-5">
      <a href="#top" className="font-semibold tracking-[-.03em]">Situationship<span className="text-[#F472A8]">/AI</span></a>
      <div className="flex items-center gap-5 text-xs text-[#A3A3A3]"><a href="#history" className="hidden hover:text-white sm:block">History</a><a href="#method" className="hidden hover:text-white sm:block">Method</a><a href="#privacy" className="hidden hover:text-white sm:block">Privacy</a><a href={repository} target="_blank" rel="noreferrer" aria-label="View source on GitHub" className="hover:text-[#F472A8]"><Github size={18} /></a></div>
    </nav>

    <section id="top" className="shell grid min-h-[78vh] items-center gap-14 py-20 md:grid-cols-[1.35fr_.65fr] md:py-28">
      <div><p className="eyebrow">Telegram conversation analysis</p><h1 className="mt-7 max-w-5xl text-[clamp(62px,10vw,148px)] font-medium leading-[.82] tracking-[-.075em]">Are they<br /><span className="text-[#F472A8]">flirting</span> back?</h1></div>
      <div className="md:self-end md:pb-5"><p className="max-w-md text-lg leading-8 text-[#A3A3A3]">Your Telegram conversations, decoded. Discover flirting signals, communication patterns, and the dynamics behind your chats.</p><div className="mt-9 flex flex-wrap gap-3"><a href="#import" className="button-primary">Analyze a chat <ArrowDown size={17} /></a><button onClick={tryDemo} disabled={loading} className="button-secondary"><Sparkles size={16} /> Try demo</button></div></div>
    </section>

    <section id="import" className="border-y rule bg-[#0c0c0c]"><div className="shell grid gap-12 py-16 md:grid-cols-[.65fr_1.35fr] md:py-24"><div><p className="eyebrow">Private by design</p><h2 className="mt-5 text-3xl font-medium tracking-[-.04em] md:text-5xl">Bring the chat.<br />Keep the context.</h2><p className="mt-6 max-w-sm text-sm leading-6 text-[#A3A3A3]">Export a chat from Telegram Desktop as machine-readable JSON. Your local backend processes it in memory and does not save the upload.</p></div><ImportPanel preview={preview} selected={selected} loading={loading} error={error} sessionGap={sessionGap} onFile={loadFile} onSelected={setSelected} onSessionGap={setSessionGap} onAnalyze={runAnalysis} /></div></section>

    <History analyses={history} error={historyError} onOpen={openSaved} onRename={renameSaved} onDelete={deleteSaved} />

    <section id="method" className="shell py-20 md:py-28"><p className="eyebrow">How it works</p><div className="mt-10 grid border-t rule md:grid-cols-3">
      {[{icon:ScanText,title:"Parse",text:"Telegram entities, service events, media, and malformed records are handled before analysis."},{icon:Sparkles,title:"Classify",text:"A character TF–IDF model scores textual flirting patterns in English, Russian, Kazakh, and mixed messages."},{icon:Server,title:"Measure",text:"Deterministic statistics describe reciprocity, response rhythm, initiation, activity, and balance."}].map((item,index) => <article key={item.title} className="border-b rule py-8 md:border-r md:px-7 md:first:pl-0 md:last:border-r-0"><div className="flex items-center justify-between"><item.icon size={21} strokeWidth={1.5} className="text-[#F472A8]" /><span className="mono text-xs text-[#555]">0{index+1}</span></div><h3 className="mt-12 text-2xl">{item.title}</h3><p className="mt-4 text-sm leading-6 text-[#A3A3A3]">{item.text}</p></article>)}
    </div></section>

    <section id="privacy" className="bg-[#F472A8] text-[#090909]"><div className="shell grid gap-10 py-16 md:grid-cols-[.8fr_1.2fr] md:py-20"><div className="flex items-start gap-3"><LockKeyhole strokeWidth={1.5} /><p className="eyebrow !text-[#090909]">Privacy, precisely stated</p></div><div><h2 className="text-3xl font-medium tracking-[-.04em] md:text-5xl">Your backend sees the file.<br />Nobody else does.</h2><p className="mt-6 max-w-2xl text-sm leading-6 text-[#351522]">Analysis happens on the self-hosted FastAPI server you control. Chat files and message text are never persisted. When you explicitly save a result, MongoDB stores only computed metrics, participant names, dates, scores, and insights.</p></div></div></section>

    <footer className="shell flex flex-wrap items-center justify-between gap-5 py-8 text-xs text-[#A3A3A3]"><span>Situationship AI · open source</span><a href={repository} target="_blank" rel="noreferrer" className="flex items-center gap-2 hover:text-white"><Github size={14} /> View source</a></footer>
  </main>;
}

