export type Participant = { id: string; name: string; messages: number };
export type Preview = {
  chat_name: string; chat_type: string; participants: Participant[]; text_messages: number;
  skipped_messages: number; date_start: string | null; date_end: string | null;
};
export type Metric = { participant: string; value: number };
export type TimeValue = { time: string; total: number; participant_a: number; participant_b: number };
export type Analysis = {
  chat_name: string;
  participants: string[];
  overview: {
    total_messages: number; active_days: number; date_start: string; date_end: string;
    messages: Metric[]; percentages: Metric[]; average_length: Metric[]; total_words: Metric[];
  };
  dynamics: {
    sessions: number; initiations: Metric[]; median_response_minutes: Metric[]; conversation_balance: number;
    messages_per_day: TimeValue[]; activity_over_time: TimeValue[]; hourly_activity: TimeValue[]; weekday_activity: TimeValue[];
  };
  flirting: {
    eligible_count: Metric[]; signal_count: Metric[]; signal_rate: Metric[]; average_score: Metric[]; over_time: TimeValue[]; mutual: boolean;
    examples: { participant: string; text: string; score: number }[];
  };
  romantic_score: {
    score: number | null; sufficient_evidence: boolean; reason: string;
    components: { label: string; value: number; weight: number }[];
  };
  insights: string[];
  model: { version: string; threshold: number; minimum_alphanumeric: number };
};

export type SavedAnalysisSummary = {
  id: string; title: string; chat_name: string; participants: string[];
  score: number | null; model_version: string; created_at: string;
};

export type SavedAnalysis = {
  id: string; title: string; created_at: string; analysis: Analysis;
};

