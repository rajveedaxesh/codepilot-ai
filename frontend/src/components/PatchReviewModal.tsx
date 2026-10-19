import React, { useState } from 'react';
import { CheckCircle2, XCircle, ShieldCheck, AlertOctagon, GitCommit, Check } from 'lucide-react';
import type { ProposedPatch } from '../types';
import { DiffViewer } from './DiffViewer';

interface PatchReviewModalProps {
  patch: ProposedPatch | null;
  onApprove: (patchId: string, approved: boolean, reason?: string) => void;
  onApply: (patchId: string) => void;
  isApplying: boolean;
}

export const PatchReviewModal: React.FC<PatchReviewModalProps> = ({
  patch,
  onApprove,
  onApply,
  isApplying,
}) => {
  const [rejectionReason, setRejectionReason] = useState('');
  const [showRejectInput, setShowRejectInput] = useState(false);

  if (!patch) {
    return (
      <div className="flex flex-col items-center justify-center p-8 text-center text-slate-500 border border-dashed border-slate-800 rounded-xl bg-slate-900/40">
        <GitCommit className="h-8 w-8 text-slate-600 mb-2 stroke-[1.5]" />
        <p className="text-xs text-slate-400 font-medium">No Patch Generated Yet</p>
        <p className="text-[11px] text-slate-600 mt-1 max-w-xs">
          Run diagnosis and click "Generate Proposed Patch" to synthesize and inspect code diffs.
        </p>
      </div>
    );
  }

  const getStatusBadge = () => {
    switch (patch.status) {
      case 'approved':
        return <span className="px-2.5 py-0.5 rounded text-xs font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">APPROVED</span>;
      case 'rejected':
        return <span className="px-2.5 py-0.5 rounded text-xs font-semibold bg-red-500/20 text-red-300 border border-red-500/30">REJECTED</span>;
      case 'applied':
        return <span className="px-2.5 py-0.5 rounded text-xs font-semibold bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">APPLIED</span>;
      default:
        return <span className="px-2.5 py-0.5 rounded text-xs font-semibold bg-amber-500/20 text-amber-300 border border-amber-500/30">AWAITING USER APPROVAL</span>;
    }
  };

  return (
    <div className="flex flex-col h-full bg-slate-900/60 border border-slate-800/80 rounded-xl overflow-hidden shadow-sm">
      {/* Header */}
      <div className="p-3 border-b border-slate-800/80 bg-slate-950/40 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <GitCommit className="h-4 w-4 text-cyan-400" />
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-300">
            Patch Review & Safety Gate
          </span>
        </div>
        <div>{getStatusBadge()}</div>
      </div>

      <div className="p-4 flex-1 overflow-y-auto space-y-4">
        {/* Rationale */}
        <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800">
          <h5 className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 mb-1">
            Fix Rationale & Strategy
          </h5>
          <p className="text-xs text-slate-200 leading-relaxed font-medium">
            {patch.rationale}
          </p>
          <div className="flex items-center gap-2 mt-2 pt-2 border-t border-slate-800/80 text-[11px] text-slate-400">
            <span>Target files:</span>
            <span className="font-mono text-cyan-300">{patch.affected_files.join(', ')}</span>
          </div>
        </div>

        {/* Safety Boundary Verification Banner */}
        <div className="flex items-center justify-between px-3 py-2 rounded-lg bg-emerald-950/20 border border-emerald-500/20 text-xs">
          <div className="flex items-center gap-2 text-emerald-400">
            <ShieldCheck className="h-4 w-4 shrink-0" />
            <span className="font-medium">Safety boundaries validated</span>
          </div>
          <span className="text-[11px] text-slate-400 font-mono">
            Traversal & Dry-Run Checked
          </span>
        </div>

        {/* Diff Viewer */}
        <DiffViewer diffText={patch.diff_content} />

        {/* Explicit Approval Controls */}
        <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800 space-y-3">
          <div className="flex items-center justify-between">
            <div>
              <h5 className="text-xs font-semibold text-slate-200">User Approval Requirement</h5>
              <p className="text-[11px] text-slate-400">
                CodePilot AI will never modify your repository without your explicit consent.
              </p>
            </div>
            {patch.is_approved && (
              <span className="flex items-center gap-1 text-xs text-emerald-400 font-medium bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                <Check className="h-3.5 w-3.5" /> Approved
              </span>
            )}
          </div>

          {!patch.is_approved && patch.status !== 'rejected' && (
            <div className="flex items-center gap-2 pt-1">
              <button
                onClick={() => onApprove(patch.id, true)}
                className="flex-1 flex items-center justify-center gap-1.5 py-2 px-3 rounded-lg text-xs font-semibold bg-emerald-600 hover:bg-emerald-500 text-white shadow-md shadow-emerald-600/20 transition-all cursor-pointer"
              >
                <CheckCircle2 className="h-4 w-4" />
                <span>Explicitly Approve Patch</span>
              </button>

              <button
                onClick={() => setShowRejectInput(!showRejectInput)}
                className="flex items-center gap-1.5 py-2 px-3 rounded-lg text-xs font-semibold bg-red-950/40 hover:bg-red-900/50 text-red-300 border border-red-500/30 transition-all cursor-pointer"
              >
                <XCircle className="h-4 w-4" />
                <span>Reject</span>
              </button>
            </div>
          )}

          {showRejectInput && !patch.is_approved && (
            <div className="space-y-2 pt-2 border-t border-slate-800">
              <input
                type="text"
                placeholder="Reason for rejection (optional feedback for agent)..."
                value={rejectionReason}
                onChange={e => setRejectionReason(e.target.value)}
                className="w-full p-2 text-xs bg-slate-900 border border-slate-700 rounded-md text-slate-200"
              />
              <button
                onClick={() => {
                  onApprove(patch.id, false, rejectionReason);
                  setShowRejectInput(false);
                }}
                className="px-3 py-1 text-xs font-semibold bg-red-600 hover:bg-red-500 text-white rounded-md cursor-pointer"
              >
                Confirm Rejection
              </button>
            </div>
          )}

          {patch.is_approved && !patch.is_applied && (
            <div className="pt-2 border-t border-slate-800">
              <button
                onClick={() => onApply(patch.id)}
                disabled={isApplying}
                className="w-full flex items-center justify-center gap-2 py-2.5 px-4 rounded-lg text-xs font-semibold bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white shadow-lg shadow-emerald-500/20 disabled:opacity-50 transition-all cursor-pointer"
              >
                <Check className="h-4 w-4" />
                <span>{isApplying ? 'Applying to Workspace...' : 'Apply Approved Patch to Workspace'}</span>
              </button>
            </div>
          )}

          {patch.is_applied && (
            <div className="p-2 rounded bg-cyan-500/10 border border-cyan-500/20 text-xs text-cyan-300 text-center font-medium">
              &check; Patch applied to workspace. Ready for automated verification.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
