"use client";

import { FormEvent, useState } from "react";
import { ArrowRight, Pencil, Trash2 } from "lucide-react";
import { SavedAnalysisSummary } from "@/lib/types";

type Props = {
  analyses: SavedAnalysisSummary[];
  error: string;
  onOpen: (id: string) => void;
  onRename: (id: string, title: string) => Promise<void>;
  onDelete: (id: string) => void;
};

export function History({ analyses, error, onOpen, onRename, onDelete }: Props) {
  const [editing, setEditing] = useState<string | null>(null);
  const [title, setTitle] = useState("");
  const submit = async (event: FormEvent, id: string) => {
    event.preventDefault();
    if (!title.trim()) return;
    await onRename(id, title);
    setEditing(null);
  };

  return <section id="history" className="shell py-20 md:py-28">
    <p className="eyebrow">Saved in MongoDB</p>
    <div className="mt-5 flex items-end justify-between gap-5"><h2 className="text-3xl font-medium tracking-[-.04em] md:text-5xl">Analysis history.</h2><span className="mono text-xs text-[#A3A3A3]">{analyses.length} saved</span></div>
    {error && <p role="alert" className="mt-6 border-l-2 border-[#F472A8] pl-4 text-sm">{error}</p>}
    {!error && analyses.length === 0 && <p className="mt-8 text-sm text-[#A3A3A3]">Saved analyses will appear here. Raw messages and quoted examples are never stored.</p>}
    <div className="mt-10 border-t rule">
      {analyses.map((item) => <article key={item.id} className="grid gap-5 border-b rule py-6 md:grid-cols-[1fr_auto] md:items-center">
        <div>
          {editing === item.id ? <form onSubmit={(event) => submit(event, item.id)} className="flex max-w-xl gap-2"><label className="sr-only" htmlFor={`title-${item.id}`}>Analysis title</label><input id={`title-${item.id}`} autoFocus maxLength={120} value={title} onChange={(event) => setTitle(event.target.value)} className="min-w-0 flex-1 border border-[#555] bg-[#090909] px-3 py-2" /><button className="button-secondary" type="submit">Save</button><button type="button" className="px-2 text-sm text-[#A3A3A3]" onClick={() => setEditing(null)}>Cancel</button></form> : <h3 className="text-xl">{item.title}</h3>}
          <p className="mt-2 text-xs text-[#A3A3A3]">{new Date(item.created_at).toLocaleString()} · score {item.score ?? "withheld"}/100 · {item.model_version}</p>
        </div>
        <div className="flex items-center gap-2">
          <button aria-label={`Rename ${item.title}`} className="p-2 text-[#A3A3A3] hover:text-white" onClick={() => { setEditing(item.id); setTitle(item.title); }}><Pencil size={16} /></button>
          <button aria-label={`Delete ${item.title}`} className="p-2 text-[#A3A3A3] hover:text-[#F472A8]" onClick={() => onDelete(item.id)}><Trash2 size={16} /></button>
          <button className="button-secondary" onClick={() => onOpen(item.id)}>Open <ArrowRight size={15} /></button>
        </div>
      </article>)}
    </div>
  </section>;
}
