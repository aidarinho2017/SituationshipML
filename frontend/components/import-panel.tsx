"use client";

import { ChangeEvent, DragEvent, useRef } from "react";
import { ArrowRight, FileJson, LoaderCircle, ShieldCheck, Upload } from "lucide-react";
import { Preview } from "@/lib/types";

type Props = {
  preview: Preview | null;
  selected: string[];
  loading: boolean;
  error: string;
  sessionGap: number;
  onFile: (file: File) => void;
  onSelected: (ids: string[]) => void;
  onSessionGap: (hours: number) => void;
  onAnalyze: () => void;
};

export function ImportPanel({ preview, selected, loading, error, sessionGap, onFile, onSelected, onSessionGap, onAnalyze }: Props) {
  const input = useRef<HTMLInputElement>(null);
  const choose = (event: ChangeEvent<HTMLInputElement>) => event.target.files?.[0] && onFile(event.target.files[0]);
  const drop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    if (event.dataTransfer.files[0]) onFile(event.dataTransfer.files[0]);
  };
  const toggle = (id: string) => {
    if (selected.includes(id)) onSelected(selected.filter((item) => item !== id));
    else if (selected.length < 2) onSelected([...selected, id]);
  };

  if (!preview) {
    return (
      <div>
        <div
          onDragOver={(event) => event.preventDefault()}
          onDrop={drop}
          className="group min-h-72 border border-dashed border-[#3a3a3a] bg-[#0d0d0d] p-8 flex flex-col items-center justify-center text-center transition-colors hover:border-[#F472A8]"
        >
          {loading ? <LoaderCircle className="mb-5 animate-spin text-[#F472A8]" size={30} /> : <Upload className="mb-5 text-[#F472A8]" size={30} strokeWidth={1.5} />}
          <h2 className="text-xl font-medium">Drop your Telegram export here</h2>
          <p className="mt-2 max-w-sm text-sm leading-6 text-[#A3A3A3]">JSON from Telegram Desktop · up to 20 MB · never stored</p>
          <button className="button-secondary mt-6" onClick={() => input.current?.click()} disabled={loading}>Choose JSON file</button>
          <input ref={input} className="sr-only" type="file" accept=".json,application/json" onChange={choose} />
        </div>
        {error && <p role="alert" className="mt-4 border-l-2 border-[#F472A8] pl-4 text-sm text-[#FAFAFA]">{error}</p>}
      </div>
    );
  }

  return (
    <div className="panel p-6 md:p-8">
      <div className="flex flex-wrap items-start justify-between gap-6 border-b rule pb-7">
        <div>
          <span className="eyebrow">Export validated</span>
          <h2 className="mt-3 text-2xl font-medium">{preview.chat_name}</h2>
          <p className="mt-2 text-sm text-[#A3A3A3]">{preview.text_messages.toLocaleString()} text messages · {preview.skipped_messages} non-text or service items skipped</p>
        </div>
        <FileJson className="text-[#F472A8]" strokeWidth={1.4} />
      </div>
      <div className="py-7">
        <div className="mb-4 flex items-center justify-between gap-4">
          <p className="text-sm font-medium">Select exactly two participants</p>
          <span className="mono text-xs text-[#A3A3A3]">{selected.length}/2</span>
        </div>
        <div className="grid gap-2 sm:grid-cols-2">
          {preview.participants.map((person) => {
            const active = selected.includes(person.id);
            return (
              <button
                key={person.id}
                onClick={() => toggle(person.id)}
                aria-pressed={active}
                className={`flex items-center justify-between border p-4 text-left transition-colors ${active ? "border-[#F472A8] bg-[#1b1216]" : "border-[#292929] hover:border-[#555]"}`}
              >
                <span>{person.name}</span><span className="mono text-xs text-[#A3A3A3]">{person.messages}</span>
              </button>
            );
          })}
        </div>
      </div>
      <div className="flex flex-wrap items-center justify-between gap-4 border-t rule pt-6">
        <div className="flex flex-wrap items-center gap-5"><span className="flex items-center gap-2 text-xs text-[#A3A3A3]"><ShieldCheck size={15} /> Processed by your local FastAPI server</span><label className="text-xs text-[#A3A3A3]">New session after <select value={sessionGap} onChange={(event) => onSessionGap(Number(event.target.value))} className="ml-2 border border-[#292929] bg-[#090909] px-2 py-1 text-white"><option value={4}>4h</option><option value={8}>8h</option><option value={12}>12h</option></select></label></div>
        <button className="button-primary" disabled={selected.length !== 2 || loading} onClick={onAnalyze}>
          {loading ? <LoaderCircle className="animate-spin" size={17} /> : <>Analyze conversation <ArrowRight size={17} /></>}
        </button>
      </div>
      {error && <p role="alert" className="mt-5 text-sm text-[#F472A8]">{error}</p>}
    </div>
  );
}

