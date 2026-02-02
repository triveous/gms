import React from 'react';
import { cn } from '@/lib/utils';
import { MessageBranch, MessageBranchContent, Message, MessageContent, MessageResponse } from '@/components/ai-elements/message';
import ChainOfThoughtComponent from './ChainofThought';
import type { SDKMessage } from '@/types/chat';

interface ChatMessageItemProps {
    message: SDKMessage;
    status: string;
    isLast: boolean;
}

const groupMessageParts = (parts: any[]) => {
    const groupedParts: any[] = [];
    let cotGroup: { type: 'data-block-group', blocks: any[] } | null = null;
    const isDataPart = (part: any) =>
        part.type === 'data-block' ||
        part.type === 'data-goal' ||
        part.type === 'data-step' ||
        part.type === 'data-state';

    parts.forEach((part: any) => {
        if (isDataPart(part)) {
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

const ChatMessageItem: React.FC<ChatMessageItemProps> = ({ message, status, isLast }) => {
    const isAssistant = message.role === 'assistant';
    const messageStatus = (isLast && isAssistant) ? status : 'ready';

    const parts = message.parts || (message.content ? [{ type: 'text', text: message.content }] : []);
    const groupedParts = groupMessageParts(parts);

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
