import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { 
  Volume2, 
  VolumeX, 
  Play, 
  RotateCcw, 
  Sparkles, 
  AlertCircle,
  Radio
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

interface VoiceNudgePlayerProps {
  module: "A" | "B" | "C";
  caseId: string;
}

interface VoiceNudgeResponse {
  status: "ready" | "synthesized" | "blocked";
  can_generate: boolean;
  reason?: string;
  module: string;
  case_id: string;
  script_text: string | null;
  audio_base64: string | null;
  speaker: string;
}

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

export default function VoiceNudgePlayer({ module, caseId }: VoiceNudgePlayerProps) {
  const [speaker, setSpeaker] = useState<string>("priya");
  const [audioUrl, setAudioUrl] = useState<string | null>(null);



  // 1. Fetch initial script and policy status
  const { data: initialData, isLoading } = useQuery<VoiceNudgeResponse>({
    queryKey: ["voice-nudge", module, caseId],
    queryFn: async () => {
      const res = await fetch(`${API_BASE}/api/cases/${module}/${caseId}/voice-nudge?synthesize=false`);
      if (!res.ok) throw new Error("Failed to load voice nudge details");
      return res.json();
    },
  });

  // 2. Synthesize audio mutation
  const synthesizeMutation = useMutation({
    mutationFn: async () => {
      const res = await fetch(
        `${API_BASE}/api/cases/${module}/${caseId}/voice-nudge?synthesize=true&speaker=${speaker}`
      );
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Audio synthesis failed");
      }
      return res.json() as Promise<VoiceNudgeResponse>;
    },
    onSuccess: (data) => {
      if (data.audio_base64) {
        setAudioUrl(`data:audio/wav;base64,${data.audio_base64}`);
      }
    },
  });

  if (isLoading) {
    return (
      <div className="rounded-lg border border-slate-200 bg-slate-50/50 p-3 text-xs text-slate-500 animate-pulse">
        Loading Voice Recovery Module...
      </div>
    );
  }

  // If blocked by policy gate (Rule 6, Rule 1, Rule 12)
  if (initialData?.status === "blocked" || !initialData?.can_generate) {
    return (
      <div className="rounded-lg border border-rose-200 bg-rose-50/70 p-3.5 text-xs">
        <div className="flex items-center gap-2 text-rose-800 font-bold mb-1">
          <VolumeX className="h-4 w-4 text-rose-600 shrink-0" />
          <span>Outbound Voice Outreach Suppressed</span>
          <Badge variant="outline" className="border-rose-300 bg-rose-100 text-rose-800 text-[10px] ml-auto">
            Policy Gate Halt
          </Badge>
        </div>
        <p className="text-slate-600 text-[11px] leading-relaxed">
          {initialData?.reason || "Automated customer voice notes are restricted under deterministic safety rules."}
        </p>
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-indigo-200 bg-gradient-to-br from-indigo-50/50 via-white to-blue-50/40 p-4 shadow-xs">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-indigo-100 pb-2.5">
        <div className="flex items-center gap-2">
          <div className="flex h-6 w-6 items-center justify-center rounded-md bg-indigo-600 text-white">
            <Radio className="h-3.5 w-3.5" />
          </div>
          <div>
            <span className="text-xs font-bold uppercase tracking-wider text-slate-800 block">
              AI Hinglish Voice Recovery Nudge
            </span>
            <span className="text-[10px] text-slate-500">
              Sarvam AI Bulbul Neural Engine &bull; Hindi-English Code-Switching
            </span>
          </div>
        </div>
        <Badge className="border-indigo-300 bg-indigo-100 text-indigo-800 text-[10px] font-semibold">
          Voice Agent
        </Badge>
      </div>

      {/* Script Section */}
      <div className="mt-3">
        <div className="flex items-center justify-between text-[11px] font-semibold text-slate-600 mb-1">
          <span className="flex items-center gap-1">
            <Sparkles className="h-3 w-3 text-indigo-600" />
            Synthesized Hinglish Dialogue:
          </span>
          <div className="flex items-center gap-1.5">
            <span className="text-slate-400">Voice:</span>
            <select
              value={speaker}
              onChange={(e) => {
                setSpeaker(e.target.value);
                setAudioUrl(null);
              }}
              className="rounded border border-slate-200 bg-white px-1.5 py-0.5 text-[11px] text-slate-700 font-medium"
            >
              <option value="priya">Priya (Female - Primary)</option>
              <option value="ritu">Ritu (Female)</option>
              <option value="shubh">Shubh (Male - Primary)</option>
              <option value="aditya">Aditya (Male)</option>
              <option value="rohan">Rohan (Male)</option>
            </select>


          </div>
        </div>

        <div className="rounded-md border border-slate-200 bg-white p-2.5 font-mono text-[11.5px] leading-relaxed text-slate-800 italic">
          "{initialData?.script_text}"
        </div>
      </div>

      {/* Audio Playback Controls */}
      <div className="mt-3 pt-2.5 border-t border-indigo-100/70 flex flex-wrap items-center justify-between gap-2">
        {audioUrl ? (
          <div className="flex flex-1 items-center gap-3">
            <audio controls autoPlay src={audioUrl} className="h-8 w-full max-w-md rounded-md" />
            <Button
              variant="outline"
              size="sm"
              onClick={() => synthesizeMutation.mutate()}
              disabled={synthesizeMutation.isPending}
              className="h-8 text-xs gap-1 text-slate-600 shrink-0"
              title="Re-synthesize"
            >
              <RotateCcw className="h-3 w-3" />
              Re-generate
            </Button>
          </div>
        ) : (
          <Button
            onClick={() => synthesizeMutation.mutate()}
            disabled={synthesizeMutation.isPending}
            className="bg-indigo-600 text-white hover:bg-indigo-700 text-xs font-semibold gap-1.5 h-8 px-3.5 shadow-sm"
          >
            {synthesizeMutation.isPending ? (
              <>
                <Volume2 className="h-3.5 w-3.5 animate-bounce" />
                Synthesizing Sarvam Audio...
              </>
            ) : (
              <>
                <Play className="h-3.5 w-3.5 fill-white" />
                Generate &amp; Play Voice Nudge
              </>
            )}
          </Button>
        )}

        {synthesizeMutation.isError && (
          <div className="w-full rounded border border-rose-200 bg-rose-50 p-2 text-[11px] text-rose-700 flex items-center gap-1.5 mt-1">
            <AlertCircle className="h-3.5 w-3.5 shrink-0 text-rose-600" />
            <span>{(synthesizeMutation.error as Error).message}</span>
          </div>
        )}
      </div>
    </div>
  );
}
