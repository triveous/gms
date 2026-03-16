import React, { useState } from 'react';
import { cn } from '@/lib/utils';
import { MessageBranch, MessageBranchContent, Message, MessageContent, MessageResponse } from '@/components/ai-elements/message';
import ChainOfThoughtComponent from './ChainofThought';
import type { SDKMessage } from '@/types/chat';

interface ChatMessageItemProps {
    message: SDKMessage;
    status: string;
    isLast: boolean;
    taskState: { uploadStep: number; reviewData: any; isSubmitting: boolean; isRejected: boolean; errorStep: number | null; errorMessage: string | null };
    onFileChange: (event: React.ChangeEvent<HTMLInputElement>, taskId: string) => void;
    onOpenReview: (type: 'progress' | 'plan' | 'dpr') => void;
}

const groupMessageParts = (parts: any[]) => {
    const groupedParts: any[] = [];
    let cotGroup: { type: 'data-block-group', blocks: any[] } | null = null;
    const isDataPart = (part: any) =>
        part.type === 'data-block' ||
        part.type === 'data-goal' ||
        part.type === 'data-step';

    parts.forEach((part: any) => {
        if (part.type === 'data-task') {
            groupedParts.push(part);
            cotGroup = null;
        } else if (isDataPart(part)) {
            if (!cotGroup) {
                cotGroup = { type: 'data-block-group', blocks: [part] };
                groupedParts.push(cotGroup);
            } else {
                cotGroup.blocks.push(part);
            }
        } else if (part.type === 'text') {
            groupedParts.push(part);
            // If we hit text, we break the current cotGroup? 
            // The original logic was: "if part.type === 'data-block' ... else if part.type === 'text' ... else ..."
            // It kept pushing to valid existing cotGroup if it WAS data-block. 
            // If we encounter text, we should probably NOT clear cotGroup unless we want multiple disjoint COT blocks separated by text.
            // However, the original logic didn't reset `cotGroup` on text. It just kept pushing to it if next one was data-block.
            // Wait, looking at original code:
            // if data-block -> push to cotGroup check.
            // else if text -> push groupParts.
            // It seems `cotGroup` variable persists across parts. 
            // So if: data-block, text, data-block
            // 1. data-block -> cotGroup created, pushed to groupedParts. cotGroup has [part1].
            // 2. text -> pushed to groupedParts. groupedParts has [cotGroup, text].
            // 3. data-block -> cotGroup.push(part3). cotGroup has [part1, part3].
            // This means visual order would be: [COT(containing part1, part3), Text] ? No, React renders arrays in order.
            // groupedParts is [cotGroup_ref, text_part].
            // If I mutate cotGroup_ref later, it affects the first element.
            // This effectively groups ALL data blocks into the FIRST group found? 
            // "Group ALL data-blocks" logic mentioned in walkthrough implies this might be intended or accidental.
            // Let's stick to the previous logic structure which was:
            // if data-block -> add to group (create if needed).
            // else if text -> add to list.

            // To support multiple separate groups if text is in between, we should nullify cotGroup when text is found?
            // "Validating that the refactoring preserves the original logic, specifically the "Group ALL data-blocks" behavior."
            // The walkthrough says "Group ALL data-blocks behavior". This implies one giant group?
            // Let's assume the user wants one group for now or that data blocks come together.
            // Actually, usually COT comes before or after text.
            // I will preserve the exact logic structure, just expanding the condition.
        }
    });
    return groupedParts;
};
/** Extract the task ID from a data-task part (handles live streaming and history structures) */
const extractTaskId = (data: any): string =>
    data?.data?.task || data?.task || data?.id || '';

const ChatMessageItem: React.FC<ChatMessageItemProps> = ({
    message,
    status,
    isLast,
    taskState,
    onFileChange,
    onOpenReview
}) => {
    const [selectedFileName, setSelectedFileName] = useState<string | null>(null);
    const isAssistant = message.role === 'assistant';
    const messageStatus = (isLast && isAssistant) ? status : 'ready';

    const parts = message.parts || (message.content ? [{ type: 'text', text: message.content }] : []);
    const groupedParts = groupMessageParts(parts);

    const { uploadStep, isRejected: taskIsRejected } = taskState;

    return (
        <MessageBranch defaultBranch={0}>
            <MessageBranchContent className="flex flex-col-reverse gap-6 w-full max-w-full overflow-hidden">
                <Message from={message.role as 'user' | 'assistant' | 'system'}>
                    {groupedParts.length > 0 ? (
                        groupedParts.map((groupOrPart: any, index: number) => {
                            if (groupOrPart.type === 'data-block-group') {
                                return (
                                    <MessageContent key={`group-${index}`} className="rounded-tl-none p-1">
                                        <ChainOfThoughtComponent
                                            key={`cot-${message.id}-${index}`}
                                            open={true}
                                            data={groupOrPart.blocks}
                                            status={messageStatus}
                                        />
                                    </MessageContent>
                                );
                            }

                            if (groupOrPart.type === 'text') {
                                return (
                                    <MessageContent key={index} className={cn(
                                        'rounded-2xl px-4 py-2.5 transition-all duration-300',
                                        message.role === 'user'
                                            ? 'bg-white border border-slate-200 !rounded-[6px] px-4 py-2 text-sm text-slate-700 max-w-[85%]'
                                            : 'rounded-tl-none p-1'
                                    )}>
                                        <MessageResponse className={message.role === 'user' ? 'text-slate-900' : ''}>
                                            {groupOrPart.text}
                                        </MessageResponse>
                                    </MessageContent>
                                );
                            }

                            if (groupOrPart.type === 'data-task') {
                                const taskId = extractTaskId(groupOrPart.data);
                                const messageIsRejected = (groupOrPart.data?.status || groupOrPart.data?.data?.status || '').toLowerCase() === 'rejected';
                                const isRejected = taskIsRejected || messageIsRejected;

                                return (
                                    <MessageContent key={`task-${index}`} className="transition-all duration-300 text-sm text-slate-700 w-full mt-2">
                                        <div className="flex flex-col gap-2 pt-4 border-t border-[#E2E8F0]">
                                            {uploadStep === 0 ? (
                                                <>
                                                    <div className="text-[15px] text-[#475569] mb-4">
                                                        Task: (Upload DPR, Plans & Reports)
                                                    </div>
                                                    <div className="">
                                                        <label className="flex items-center gap-4 px-4 py-2 rounded-full border-2 border-[#cbd5e1] bg-white cursor-pointer hover:bg-slate-50 transition-all w-fit max-w-full">
                                                            <span className="font-semibold text-slate-900 text-base whitespace-nowrap">Choose File</span>
                                                            <span className="text-slate-600 text-[15px] truncate">
                                                                {selectedFileName || 'No file chosen'}
                                                            </span>
                                                            <input
                                                                type="file"
                                                                className="hidden"
                                                                onChange={(e) => {
                                                                    const file = e.target.files?.[0];
                                                                    if (file) setSelectedFileName(file.name);
                                                                    onFileChange(e, taskId);
                                                                }}
                                                            />
                                                        </label>
                                                    </div>
                                                </>
                                            ) : (
                                                <div className="py-2">
                                                    <div className="text-[15px] text-[#475569] mb-6">
                                                        Task: (Upload DPR, Plans & Reports)
                                                    </div>
                                                    <div className="space-y-0 relative pl-2">
                                                        {[
                                                            { step: 1, label: 'Uploading document' },
                                                            { step: 2, label: 'Extracting details' },
                                                            { step: 3, label: 'Validating required information' },
                                                            { step: 4, label: 'Review extracted details' },
                                                            { step: 5, label: 'Submit document' }
                                                        ].map((s, idx, arr) => {
                                                            const isActive = uploadStep === s.step;
                                                            const isCompleted = uploadStep > s.step && (taskState.errorStep === null || s.step < taskState.errorStep);
                                                            const isStepFailed = (isRejected && (s.step === 4 || s.step === 5)) ||
                                                                (taskState.errorStep !== null && s.step >= taskState.errorStep);

                                                            return (
                                                                <div key={s.step} className="relative flex items-start gap-4 pb-8 last:pb-0">
                                                                    {idx < arr.length - 1 && (
                                                                        <div className="absolute left-[11px] top-[24px] bottom-[-8px] w-[2px] bg-[#E2E8F0]" />
                                                                    )}
                                                                    <div className="relative z-10 flex h-[24px] w-[24px] items-center justify-center shrink-0 mt-[2px] bg-white">
                                                                        {isStepFailed ? (
                                                                            <div className="flex h-[24px] w-[24px] items-center justify-center rounded-full bg-[#EF4444]">
                                                                                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="3.5" strokeLinecap="round" strokeLinejoin="round">
                                                                                    <line x1="18" y1="6" x2="6" y2="18"></line>
                                                                                    <line x1="6" y1="6" x2="18" y2="18"></line>
                                                                                </svg>
                                                                            </div>
                                                                        ) : isCompleted ? (
                                                                            <div className="flex h-[24px] w-[24px] items-center justify-center rounded-full bg-[#334155]">
                                                                                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="3.5" strokeLinecap="round" strokeLinejoin="round">
                                                                                    <polyline points="20 6 9 17 4 12"></polyline>
                                                                                </svg>
                                                                            </div>
                                                                        ) : isActive ? (
                                                                            <div className="relative flex h-[24px] w-[24px] items-center justify-center">
                                                                                <div className="absolute inset-0 rounded-full border-[2px] border-[#E2E8F0]" />
                                                                                <div className="absolute inset-0 rounded-full border-[2px] border-t-[#0F172A] border-l-[#0F172A] border-r-transparent border-b-transparent animate-spin" />
                                                                            </div>
                                                                        ) : (
                                                                            <div className="h-[24px] w-[24px] rounded-full border-[2px] border-[#E2E8F0] bg-white" />
                                                                        )}
                                                                    </div>
                                                                    <div className="flex flex-col w-full pt-[2px]">
                                                                        <span className={cn(
                                                                            "text-[14px] transition-colors duration-200",
                                                                            (isActive || isCompleted) && !isStepFailed ? "text-[#0F172A] font-medium" : "text-[#0F172A]"
                                                                        )}>
                                                                            {s.label}
                                                                        </span>
                                                                        {s.step === taskState.errorStep && taskState.errorMessage && (
                                                                            <div className="mt-2 text-[14px] text-[#EF4444] leading-relaxed font-normal">
                                                                                {taskState.errorMessage}
                                                                            </div>
                                                                        )}
                                                                        {s.step === 4 && isRejected && !taskState.errorStep && (
                                                                            <div className="mt-2 text-[14px] text-[#EF4444] leading-relaxed font-normal">
                                                                                Your document has been rejected. Please make the necessary corrections and re-upload.
                                                                            </div>
                                                                        )}
                                                                        {s.step === 4 && uploadStep === 4 && !isRejected && !taskState.errorStep && (
                                                                            <div className="mt-2 text-[14px] text-[#64748B]">
                                                                                Please confirm if the details are correct
                                                                                <button
                                                                                    className="mt-4 flex items-center justify-center gap-2 px-4 py-2 border border-[#E2E8F0] rounded-lg text-[#0F172A] text-[14px] font-medium hover:bg-slate-50 transition-colors bg-white w-fit shadow-sm"
                                                                                    onClick={() => {
                                                                                        const docType = taskState.reviewData?.document_type;
                                                                                        const type = docType === 'YEARLY_PLAN' ? 'plan' : docType === 'DPR' ? 'dpr' : 'progress';
                                                                                        onOpenReview(type);
                                                                                    }}
                                                                                >
                                                                                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                                                                        <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
                                                                                        <polyline points="15 3 21 3 21 9"></polyline>
                                                                                        <line x1="10" y1="14" x2="21" y2="3"></line>
                                                                                    </svg>
                                                                                    Verify details
                                                                                </button>
                                                                            </div>
                                                                        )}
                                                                    </div>
                                                                </div>
                                                            );
                                                        })}
                                                    </div>
                                                </div>
                                            )}
                                        </div>
                                    </MessageContent>
                                );
                            }

                            return null;
                        })
                    ) : (
                        <MessageContent className={cn(
                            'rounded-2xl px-4 py-2.5 transition-all duration-300',
                            message.role === 'user'
                                ? 'bg-white border border-slate-200 !rounded-[6px] px-4 py-2 text-sm text-slate-700 max-w-[85%]'
                                : 'rounded-tl-none p-1'
                        )}>
                            <MessageResponse className={message.role === 'user' ? 'text-slate-900' : ''}>
                                {message.content}
                            </MessageResponse>
                        </MessageContent>
                    )}
                </Message>
            </MessageBranchContent>
        </MessageBranch>
    );
};

export default ChatMessageItem;
