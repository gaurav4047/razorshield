import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { 
  Volume2, 
  VolumeX, 
  Play, 
  RotateCcw, 
  Sparkles, 
  AlertCircle,
  Headphones,
  CheckCircle2
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

interface VoiceNudgePlayerProps {
  module: "A" | "B" | "C";
  caseId: string;
}

interface VoiceNudgeResponse {
  status: "ready" | "synthesized" | "blocked" | "settled" | "closed";
  can_generate: boolean;
  reason?: string;
  module: string;
  case_id: string;
  script_text: string | null;
  audio_url: string | null;
  audio_base64: string | null;
  speaker: string;
  archived_call_metadata?: {
    channel?: string;
    duration_seconds?: number;
    call_status?: string;
    recorded_at?: string;
  };
}

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

export default function VoiceNudgePlayer({ module, caseId }: VoiceNudgePlayerProps) {
  const [speaker, setSpeaker] = useState<string>("priya");
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [scriptText, setScriptText] = useState<string | null>(null);

  // 1. Fetch initial script and policy status
  const { data: initialData, isLoading } = useQuery<VoiceNudgeResponse>({
    queryKey: ["voice-nudge", module, caseId, speaker],
    queryFn: async () => {
      const res = await fetch(`${API_BASE}/api/cases/${module}/${caseId}/voice-nudge?synthesize=false&speaker=${speaker}`);
      if (!res.ok) throw new Error("Failed to load voice nudge details");
      const json = await res.json();
      if (json.script_text) setScriptText(json.script_text);
      return json;
    },
  });

  const displayedScript = scriptText || initialData?.script_text;
  const currentAudioUrl = audioUrl || (initialData?.audio_url ? `${API_BASE}${initialData.audio_url}` : null);

  // 2. Synthesize audio mutation
  const synthesizeMutation = useMutation({
    mutationFn: async () => {
      const scriptParam = displayedScript ? `&custom_script=${encodeURIComponent(displayedScript)}` : "";
      const res = await fetch(
        `${API_BASE}/api/cases/${module}/${caseId}/voice-nudge?synthesize=true&speaker=${speaker}${scriptParam}`
      );
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Audio synthesis failed");
      }
      return res.json() as Promise<VoiceNudgeResponse>;
    },
    onSuccess: (data) => {
      if (data.script_text) {
        setScriptText(data.script_text);
      }
      if (data.audio_url) {
        setAudioUrl(`${API_BASE}${data.audio_url}`);
      } else if (data.audio_base64) {
        setAudioUrl(`data:audio/wav;base64,${data.audio_base64}`);
      }
    },
  });

  if (isLoading) {
    return (
      <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-4 text-xs sm:text-sm text-slate-400 animate-pulse">
        Loading Voice Recovery Module...
      </div>
    );
  }

  // If case is already settled — display archived historical outreach call
  if (initialData?.status === "settled") {
    const meta = initialData.archived_call_metadata;
    return (
      <div className="rounded-2xl border border-emerald-500/30 bg-emerald-950/20 p-5 text-xs sm:text-sm space-y-4 shadow-xl">
        {/* Header */}
        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-emerald-500/30 pb-3">
          <div className="flex items-center gap-2.5 text-emerald-300 font-bold">
            <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-emerald-600 text-white shadow-xs">
              <Headphones className="h-4 w-4" />
            </div>
            <div>
              <span className="block text-sm font-black text-white">
                Archived Autonomous Voice Call
              </span>
              <span className="block text-xs text-emerald-400 font-medium">
                Sarvam AI Bulbul Neural Engine &bull; Dispatched Prior to Settlement
              </span>
            </div>
          </div>
          <Badge className="border-emerald-500/30 bg-emerald-500/15 text-emerald-300 font-semibold px-3 py-1 text-xs rounded-full">
            Call Completed &bull; Settled
          </Badge>
        </div>

        {/* Telemetry Strip */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 font-mono text-[11px]">
          <div className="bg-slate-950/60 border border-emerald-500/20 p-2.5 rounded-xl">
            <span className="text-slate-400 font-sans block text-[10px] font-semibold">Channel</span>
            <span className="font-bold text-emerald-300">{meta?.channel || "Outbound AI Voice"}</span>
          </div>
          <div className="bg-slate-950/60 border border-emerald-500/20 p-2.5 rounded-xl">
            <span className="text-slate-400 font-sans block text-[10px] font-semibold">Duration</span>
            <span className="font-bold text-emerald-300">{meta?.duration_seconds || 32}s (Completed)</span>
          </div>
          <div className="bg-slate-950/60 border border-emerald-500/20 p-2.5 rounded-xl">
            <span className="text-slate-400 font-sans block text-[10px] font-semibold">Call Status</span>
            <span className="font-bold text-emerald-300">{meta?.call_status || "Answered & Converted"}</span>
          </div>
          <div className="bg-slate-950/60 border border-emerald-500/20 p-2.5 rounded-xl">
            <span className="text-slate-400 font-sans block text-[10px] font-semibold">Outcome</span>
            <span className="font-bold text-emerald-300">Payment Link Paid</span>
          </div>
        </div>

        {/* Script Content */}
        {initialData.script_text && (
          <div className="space-y-1.5">
            <span className="font-bold text-emerald-300 text-xs uppercase tracking-wider block">
              Dispatched Hinglish Call Script:
            </span>
            <div className="rounded-xl border border-emerald-500/30 bg-slate-950/70 p-3.5 text-xs sm:text-sm text-slate-200 font-medium italic leading-relaxed">
              "{initialData.script_text}"
            </div>
          </div>
        )}

        <div className="flex items-center gap-2 text-xs text-emerald-300 font-medium">
          <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0" />
          <span>Payment collected and settled into bank (T+2). Outbound collection calls are terminated.</span>
        </div>
      </div>
    );
  }

  // If case is closed / written off
  if (initialData?.status === "closed") {
    return (
      <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-4 text-xs sm:text-sm space-y-1.5">
        <div className="flex items-center gap-2 text-slate-300 font-bold">
          <VolumeX className="h-4 w-4 text-slate-500 shrink-0" />
          <span>Case Closed / Unrecovered</span>
          <Badge variant="outline" className="border-slate-700 bg-slate-800 text-slate-400 text-xs font-semibold ml-auto px-2.5 py-0.5 rounded-full">
            Outreach Closed
          </Badge>
        </div>
        <p className="text-slate-400 leading-relaxed font-medium">
          {initialData?.reason || "All automated recovery actions have been exhausted for this account. Outbound voice calls are terminated."}
        </p>
      </div>
    );
  }

  // If blocked by policy gate (Rule 6, Rule 1, Rule 12)
  if (initialData?.status === "blocked" || !initialData?.can_generate) {
    return (
      <div className="rounded-2xl border border-rose-500/30 bg-rose-950/30 p-4 text-xs sm:text-sm space-y-1.5">
        <div className="flex items-center gap-2 text-rose-300 font-bold">
          <VolumeX className="h-4 w-4 text-rose-400 shrink-0" />
          <span>Outbound Voice Outreach Suppressed</span>
          <Badge variant="outline" className="border-rose-500/30 bg-rose-500/10 text-rose-300 text-xs font-semibold ml-auto px-2.5 py-0.5 rounded-full">
            Policy Gate Halt
          </Badge>
        </div>
        <p className="text-slate-400 leading-relaxed font-medium">
          {initialData?.reason || "Automated customer voice notes are restricted under deterministic safety rules."}
        </p>
      </div>
    );
  }

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/90 p-5 shadow-xl space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-blue-600 text-white shadow-md shadow-blue-500/25 border border-blue-400/30">
            <Headphones className="h-4 w-4" />
          </div>
          <div>
            <span className="text-xs sm:text-sm font-black uppercase tracking-wider text-white block">
              AI Hinglish Voice Recovery Nudge
            </span>
            <span className="text-xs text-slate-400 font-medium">
              Sarvam AI Bulbul Neural Engine &bull; Code-Switching Outreach
            </span>
          </div>
        </div>
        <Badge className="border-blue-500/30 bg-blue-500/15 text-blue-300 text-xs font-semibold px-2.5 py-0.5 rounded-full">
          Voice Agent
        </Badge>
      </div>

      {/* Script Section */}
      <div className="space-y-2">
        <div className="flex items-center justify-between text-xs font-semibold text-slate-400">
          <span className="flex items-center gap-1.5 font-bold text-slate-300">
            <Sparkles className="h-3.5 w-3.5 text-blue-400" />
            Synthesized Hinglish Dialogue:
          </span>
          <div className="flex items-center gap-2">
            <span className="text-slate-400 font-medium">Voice:</span>
            <select
              value={speaker}
              onChange={(e) => {
                setSpeaker(e.target.value);
                setAudioUrl(null);
              }}
              className="rounded-lg border border-slate-700 bg-slate-800 px-2.5 py-1 text-xs text-slate-200 font-semibold focus:border-blue-500 focus:outline-none shadow-xs cursor-pointer"
            >
              <option value="priya">Priya (Female - Primary)</option>
              <option value="ritu">Ritu (Female)</option>
              <option value="shubh">Shubh (Male - Primary)</option>
              <option value="aditya">Aditya (Male)</option>
              <option value="rohan">Rohan (Male)</option>
            </select>
          </div>
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-950/70 p-3.5 font-mono text-xs sm:text-sm leading-relaxed text-slate-200 italic shadow-inner">
          "{displayedScript || initialData?.script_text}"
        </div>
      </div>

      {/* Audio Playback Controls */}
      <div className="pt-3 border-t border-slate-800 flex flex-wrap items-center justify-between gap-3">
        {currentAudioUrl ? (
          <div className="flex flex-1 items-center gap-3">
            <audio controls autoPlay src={currentAudioUrl} className="h-9 w-full max-w-md rounded-xl" />

            <Button
              variant="outline"
              size="sm"
              onClick={() => synthesizeMutation.mutate()}
              disabled={synthesizeMutation.isPending}
              className="h-9 text-xs font-semibold gap-1.5 text-slate-300 rounded-xl border-slate-700 bg-slate-800/80 hover:bg-slate-700 hover:text-white shrink-0"
              title="Re-synthesize"
            >
              <RotateCcw className="h-3.5 w-3.5" />
              <span>Re-generate</span>
            </Button>
          </div>
        ) : (
          <Button
            onClick={() => synthesizeMutation.mutate()}
            disabled={synthesizeMutation.isPending}
            className="bg-blue-600 hover:bg-blue-500 text-white text-xs sm:text-sm font-semibold gap-2 h-10 px-5 rounded-xl shadow-lg shadow-blue-500/25 active:scale-98"
          >
            {synthesizeMutation.isPending ? (
              <>
                <Volume2 className="h-4 w-4 animate-bounce" />
                <span>Synthesizing Sarvam Audio...</span>
              </>
            ) : (
              <>
                <Play className="h-4 w-4 fill-white" />
                <span>Generate &amp; Play Voice Nudge</span>
              </>
            )}
          </Button>
        )}

        {synthesizeMutation.isError && (
          <div className="w-full rounded-xl border border-rose-500/30 bg-rose-950/40 p-2.5 text-xs text-rose-300 flex items-center gap-2">
            <AlertCircle className="h-4 w-4 shrink-0 text-rose-400" />
            <span className="font-semibold">{(synthesizeMutation.error as Error).message}</span>
          </div>
        )}
      </div>
    </div>
  );
}