import React from 'react';
import {
    PromptInput,
    PromptInputBody,
    PromptInputSubmit,
    PromptInputTextarea,
    type PromptInputMessage,
} from '@/components/ai-elements/prompt-input';
import { Square, Loader2 } from 'lucide-react';

interface ChatInputAreaProps {
    input: string;
    setInput: (value: string) => void;
    onSend: (message: PromptInputMessage) => void;
    status: 'submitted' | 'streaming' | 'ready' | 'error';
    disabled: boolean;
    isAssistantResponding: boolean;
    hasTextPart: boolean | undefined;
    showBeforeThinking: boolean;
    showThinkingActive: boolean;
}

const ChatInputArea: React.FC<ChatInputAreaProps> = ({
    input,
    setInput,
    onSend,
    status,
    disabled,
    isAssistantResponding,
    hasTextPart,
    showBeforeThinking,
    showThinkingActive,
}) => {
    return (
        <div className="relative">
            <div className="relative rounded-lg p-[1px] bg-gradient-to-r from-orange-400 to-pink-400">
                <PromptInput
                    onSubmit={onSend}
                    className='relative outline-none focus:outline-none bg-white rounded-[9px] flex items-center gap-2 px-3 py-3 m-0 [&_[data-slot=input-group]]:!h-10 [&_[data-slot=input-group]]:gap-2 [&_[data-slot=input-group]]:border-none [&_[data-slot=input-group]]:shadow-none [&_[data-slot=input-group]]:focus-within:!ring-0 [&_[data-slot=input-group]]:focus-within:!border-none'
                >
                    <PromptInputBody>
                        <PromptInputTextarea
                            className='flex-1 text-[14px] font-normal tracking-[0.07px] text-foreground placeholder:text-muted-foreground bg-transparent border-none outline-none focus:outline-none disabled:opacity-50 !h-10 !min-h-10 !max-h-10 resize-none overflow-x-auto overflow-y-hidden whitespace-nowrap remove-scrollbar ![field-sizing:fixed] leading-5'
                            onChange={(event) => setInput(event.target.value)}
                            value={input}
                            wrap="off"
                            rows={1}
                            placeholder='Ask me about the project'
                            disabled={disabled}
                        />
                    </PromptInputBody>
                    <PromptInputSubmit
                        disabled={!(input.trim() || status) || (isAssistantResponding && !hasTextPart)}
                        status={status}
                        className='bg-[#FEF2F2]  text-orange-500 hover:!text-orange-700 cursor-pointer'
                    >
                        {(showBeforeThinking || showThinkingActive) ? (
                            <Loader2 className="w-5 h-5 text-orange-500 animate-spin shrink-0" />
                        ) : (
                            <svg className="w-5 h-5 text-orange-500 shrink-0" viewBox="0 0 20 20" fill="none">
                                <path d="M3 10L17 10M17 10L11 4M17 10L11 16" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                            </svg>
                        )}
                    </PromptInputSubmit>
                </PromptInput>
            </div>
        </div>
    );
};

export default ChatInputArea;
