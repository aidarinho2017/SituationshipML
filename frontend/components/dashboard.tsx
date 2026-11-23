"use client";

import { Activity, ArrowLeft, Database, LoaderCircle, ShieldAlert } from "lucide-react";
import {
  Area, AreaChart, Bar, BarChart, CartesianGrid, Cell, Line, LineChart, ResponsiveContainer,
  Tooltip, XAxis, YAxis,
} from "recharts";
import { Analysis, Metric, TimeValue } from "@/lib/types";

const PINK = "#F472A8";
const WHITE = "#FAFAFA";
const MUTED = "#A3A3A3";
const GRID = "#292929";
const tooltip = { background: "#141414", border: `1px solid ${GRID}`, borderRadius: 0, color: WHITE, fontSize: 12 };

function Section({ label, title, children }: { label: string; title: string; children: React.ReactNode }) {
  return <section className="border-t rule py-14 md:py-20"><p className="eyebrow">{label}</p><h2 className="mt-4 max-w-2xl text-3xl font-medium tracking-[-.035em] md:text-5xl">{title}</h2><div className="mt-10">{children}</div></section>;
}

function MetricPair({ title, values, suffix = "" }: { title: string; values: Metric[]; suffix?: string }) {
  const maximum = Math.max(...values.map((item) => item.value));
  const hasWinner = values.some((item) => item.value !== maximum);
  return <div className="border-t rule pt-4"><p className="mb-5 text-xs uppercase tracking-[.13em] text-[#A3A3A3]">{title}</p>{values.map((item) => <div key={item.participant} className="mb-3 flex items-baseline justify-between gap-3"><span className="text-sm">{item.participant}</span><span className={`mono text-lg ${hasWinner && item.value === maximum ? "text-[#F472A8]" : ""}`}>{item.value.toLocaleString()}{suffix}</span></div>)}</div>;
}

function Timeline({ data, names, kind = "area" }: { data: TimeValue[]; names: string[]; kind?: "area" | "line" }) {
  const Chart = kind === "line" ? LineChart : AreaChart;
  return <div className="h-72 w-full"><ResponsiveContainer><Chart data={data} margin={{ top: 10, right: 6, left: -25, bottom: 0 }}><CartesianGrid stroke={GRID} vertical={false} /><XAxis dataKey="time" stroke={MUTED} tickLine={false} axisLine={false} fontSize={11} minTickGap={28} /><YAxis stroke={MUTED} tickLine={false} axisLine={false} fontSize={11} /><Tooltip contentStyle={tooltip} />{kind === "area" ? <><Area type="monotone" dataKey="participant_a" name={names[0]} stroke={WHITE} fill={WHITE} fillOpacity={0.08} /><Area type="monotone" dataKey="participant_b" name={names[1]} stroke={PINK} fill={PINK} fillOpacity={0.12} /></> : <><Line type="monotone" dataKey="participant_a" name={names[0]} stroke={WHITE} dot={false} strokeWidth={2} /><Line type="monotone" dataKey="participant_b" name={names[1]} stroke={PINK} dot={false} strokeWidth={2} /></>}</Chart></ResponsiveContainer></div>;
}

function Bars({ data, names }: { data: TimeValue[]; names: string[] }) {
  return <div className="h-64"><ResponsiveContainer><BarChart data={data} margin={{ top: 8, right: 5, left: -28, bottom: 0 }}><CartesianGrid stroke={GRID} vertical={false} /><XAxis dataKey="time" stroke={MUTED} tickLine={false} axisLine={false} fontSize={10} /><YAxis stroke={MUTED} tickLine={false} axisLine={false} fontSize={11} /><Tooltip contentStyle={tooltip} /><Bar dataKey="participant_a" name={names[0]} fill={WHITE} radius={0} /><Bar dataKey="participant_b" name={names[1]} fill={PINK} radius={0} /></BarChart></ResponsiveContainer></div>;
}

export function Dashboard({ analysis, onReset, onSave, saved, saving, error }: { analysis: Analysis; onReset: () => void; onSave: () => void; saved: boolean; saving: boolean; error: string }) {
  const { overview, dynamics, flirting, romantic_score: score, participants, model } = analysis;
  const formatDate = (value: string) => new Intl.DateTimeFormat("en", { month: "short", day: "numeric", year: "numeric" }).format(new Date(value));
  const participantBars = overview.messages.map((item, index) => ({ name: item.participant, value: item.value, fill: index ? PINK : WHITE }));
  const initiationBars = dynamics.initiations.map((item, index) => ({ name: item.participant, value: item.value, fill: index ? PINK : WHITE }));

  return <main>
    <header className="shell flex items-center justify-between border-b rule py-5"><button onClick={onReset} className="flex items-center gap-2 text-sm text-[#A3A3A3] hover:text-white"><ArrowLeft size={16} /> New analysis</button><button onClick={onSave} disabled={saved || saving} className="button-secondary">{saving ? <LoaderCircle className="animate-spin" size={15} /> : <Database size={15} />} {saved ? "Saved in MongoDB" : "Save analysis"}</button></header>
    <div className="shell">
      {error && <p role="alert" className="mt-5 border-l-2 border-[#F472A8] pl-4 text-sm">{error}</p>}
      <section className="grid min-h-[66vh] items-end gap-10 py-16 md:grid-cols-[1.35fr_.65fr] md:py-24">
        <div><p className="eyebrow">Experimental signal index</p><h1 className="mt-7 text-5xl font-medium leading-[.95] tracking-[-.06em] sm:text-7xl lg:text-8xl">Romantic<br />potential</h1><p className="mt-7 max-w-xl text-base leading-7 text-[#A3A3A3]">A transparent heuristic based on flirting signals, reciprocity, initiation, and engagement. It is not a probability of feelings or a prediction of what happens next.</p></div>
        <div className="border-l border-[#F472A8] pl-7 md:pb-2">{score.sufficient_evidence ? <><div className="mono text-[clamp(90px,14vw,180px)] leading-none tracking-[-.09em]">{score.score}<span className="ml-2 text-2xl text-[#F472A8]">/100</span></div><p className="mt-5 text-sm leading-6 text-[#A3A3A3]">{score.reason}</p></> : <><ShieldAlert className="text-[#F472A8]" /><h2 className="mt-5 text-3xl">Insufficient evidence</h2><p className="mt-3 text-sm leading-6 text-[#A3A3A3]">{score.reason}</p></>}</div>
      </section>

      <Section label="01 · Overview" title={`${analysis.chat_name}, by the numbers.`}>
        <div className="grid gap-px bg-[#292929] border border-[#292929] sm:grid-cols-2 lg:grid-cols-4">
          {[{label:"Messages",value:overview.total_messages.toLocaleString()},{label:"Active days",value:overview.active_days},{label:"Sessions",value:dynamics.sessions},{label:"Date range",value:`${formatDate(overview.date_start)} — ${formatDate(overview.date_end)}`}].map(item => <div className="bg-[#090909] p-6" key={item.label}><p className="text-xs uppercase tracking-[.14em] text-[#A3A3A3]">{item.label}</p><p className={`mt-5 ${item.label === "Date range" ? "mono text-sm leading-6" : "metric-value"}`}>{item.value}</p></div>)}
        </div>
        <div className="mt-12 grid gap-10 lg:grid-cols-[1.4fr_1fr]">
          <div><p className="mb-5 text-sm text-[#A3A3A3]">Message volume over time</p><Timeline data={dynamics.messages_per_day} names={participants} /></div>
          <div className="grid grid-cols-2 gap-8"><MetricPair title="Share" values={overview.percentages} suffix="%" /><MetricPair title="Average length" values={overview.average_length} suffix=" chars" /><MetricPair title="Total words" values={overview.total_words} /><MetricPair title="Response median" values={dynamics.median_response_minutes} suffix=" min" /></div>
        </div>
      </Section>

      <Section label="02 · Dynamics" title="The rhythm of the conversation.">
        <div className="grid gap-12 lg:grid-cols-2">
          <div><p className="mb-5 text-sm text-[#A3A3A3]">Messages per participant</p><div className="h-56"><ResponsiveContainer><BarChart data={participantBars} layout="vertical" margin={{ left: 5, right: 20 }}><XAxis type="number" hide /><YAxis type="category" dataKey="name" width={90} tick={{ fill: MUTED, fontSize: 12 }} axisLine={false} tickLine={false} /><Tooltip contentStyle={tooltip} /><Bar dataKey="value">{participantBars.map((item) => <Cell key={item.name} fill={item.fill} />)}</Bar></BarChart></ResponsiveContainer></div></div>
          <div><p className="mb-5 text-sm text-[#A3A3A3]">Conversation initiations</p><div className="h-56"><ResponsiveContainer><BarChart data={initiationBars} layout="vertical" margin={{ left: 5, right: 20 }}><XAxis type="number" hide /><YAxis type="category" dataKey="name" width={90} tick={{ fill: MUTED, fontSize: 12 }} axisLine={false} tickLine={false} /><Tooltip contentStyle={tooltip} /><Bar dataKey="value">{initiationBars.map((item) => <Cell key={item.name} fill={item.fill} />)}</Bar></BarChart></ResponsiveContainer></div></div>
          <div><p className="mb-5 text-sm text-[#A3A3A3]">Hourly activity</p><Bars data={dynamics.hourly_activity} names={participants} /></div>
          <div><p className="mb-5 text-sm text-[#A3A3A3]">Activity by weekday</p><Bars data={dynamics.weekday_activity} names={participants} /></div>
        </div>
      </Section>

      <Section label="03 · Flirting signals" title="What the classifier noticed.">
        {model.version.startsWith("legacy-") && <p className="mb-8 border-l-2 border-[#F472A8] pl-4 text-sm text-[#A3A3A3]">Legacy model result. Re-upload this chat after training a local model to recalculate it with the conservative policy.</p>}
        <div className="grid gap-10 lg:grid-cols-[.8fr_1.2fr]">
          <div className="grid grid-cols-2 gap-8"><MetricPair title="Messages evaluated" values={flirting.eligible_count} /><MetricPair title="Signals" values={flirting.signal_count} /><MetricPair title="Signal rate" values={flirting.signal_rate} suffix="%" /><MetricPair title="Average classifier score" values={flirting.average_score} suffix=" / 100" /><div className="border-t rule pt-4"><p className="text-xs uppercase tracking-[.13em] text-[#A3A3A3]">Mutual indicator</p><p className="mt-5 text-2xl">{flirting.mutual ? "Observed" : "Not enough signals"}</p></div><div className="border-t rule pt-4"><p className="text-xs uppercase tracking-[.13em] text-[#A3A3A3]">Model policy</p><p className="mt-5 text-sm leading-6">{model.version}<br /><span className="text-[#A3A3A3]">threshold {model.threshold.toFixed(2)} · {model.minimum_alphanumeric || "no"} character minimum</span></p></div></div>
          <div><p className="mb-5 text-sm text-[#A3A3A3]">Signals over time</p><Timeline data={flirting.over_time} names={participants} kind="line" /></div>
        </div>
        {flirting.examples.length > 0 && <div className="mt-14 grid border-t rule md:grid-cols-2">{flirting.examples.map((example, index) => <blockquote key={`${example.participant}-${index}`} className="border-b rule p-6 md:odd:border-r"><p className="text-lg leading-7">“{example.text}”</p><footer className="mt-5 flex justify-between text-xs text-[#A3A3A3]"><span>{example.participant}</span><span className="mono">classifier {Math.round(example.score * 100)}/100</span></footer></blockquote>)}</div>}
      </Section>

      <Section label="04 · Evidence-based notes" title="Observed, not imagined.">
        <div className="grid gap-px bg-[#292929] border border-[#292929] md:grid-cols-2">{analysis.insights.map((insight, index) => <div className="bg-[#141414] p-7 md:p-9" key={insight}><span className="mono text-xs text-[#F472A8]">0{index + 1}</span><p className="mt-8 text-xl leading-8">{insight}</p></div>)}</div>
      </Section>

      {score.components.length > 0 && <Section label="05 · Method" title="A score you can inspect."><div className="grid gap-8 md:grid-cols-2">{score.components.map(component => <div key={component.label} className="border-t rule pt-4"><div className="flex justify-between text-sm"><span>{component.label}</span><span className="mono text-[#F472A8]">{Math.round(component.value)} × {component.weight}</span></div><div className="mt-4 h-1 bg-[#292929]"><div className="h-full bg-[#F472A8]" style={{ width: `${component.value}%` }} /></div></div>)}</div><p className="mt-10 max-w-2xl text-sm leading-6 text-[#A3A3A3]">Classifier scores identify patterns similar to labeled training messages. Messages below the model’s minimum evidence rule are excluded, not classified as neutral. Scores are not calibrated probabilities of attraction, consent, or future relationship outcomes.</p></Section>}
    </div>
    <footer className="shell flex flex-wrap items-center justify-between gap-5 border-t rule py-8 text-xs text-[#A3A3A3]"><span>Situationship AI · self-hosted and open source</span><span className="flex gap-2"><Activity size={14} /> {saved ? "Metrics saved; message excerpts removed" : "Analysis stays in request memory"}</span></footer>
  </main>;
}

