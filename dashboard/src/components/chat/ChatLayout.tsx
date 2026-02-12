import React from 'react';
import {
    Conversation,
    ConversationContent,
    ConversationScrollButton,
} from '@/components/ai-elements/conversation';
import { Message, MessageContent } from '@/components/ai-elements/message';
import { type PromptInputMessage } from '@/components/ai-elements/prompt-input';
import ChatMessageItem from './ChatMessageItem';
import type { SDKMessage, Conversation as ConversationType } from '@/types/chat';
import ThinkingLoader from './ThinkingLoader';
import type { QuickQuestion } from '@/types/chat';
import QuickQuestions from './QuickQuestions';
import ChatHeader from './ChatHeader';
import ChatInputArea from './ChatInputArea';



interface ChatLayoutProps {
    onNewChat: () => void;
    onClose: () => void;
    conversationList: ConversationType[];
    onSelectConversation: (id: string) => void;

    messages: SDKMessage[];
    status: 'error' | 'submitted' | 'streaming' | 'ready';
    error: any;

    quickQuestions: QuickQuestion[];
    handleSend: (message: PromptInputMessage) => void;

    input: string;
    setInput: React.Dispatch<React.SetStateAction<string>>;

    isAssistantResponding: boolean;
    hasTextPart: boolean;
    showBeforeThinking: boolean;
    showThinkingActive: boolean;

    isDrawerMode?: boolean;
}

const ChatLayout: React.FC<ChatLayoutProps> = ({
    onNewChat,
    onClose,
    conversationList,
    onSelectConversation,
    messages,
    status,
    error,
    quickQuestions,
    handleSend,
    input,
    setInput,
    isAssistantResponding,
    hasTextPart,
    showBeforeThinking,
    showThinkingActive,
    isDrawerMode = false,
}) => {
    const containerWidthClass = isDrawerMode
        ? 'w-[399px] max-w-[399px]'
        : 'w-full';

    return (
        <div className="flex flex-col h-full">
            <ChatHeader
                onNewChat={onNewChat}
                onClose={onClose}
                conversationList={conversationList}
                onSelectConversation={onSelectConversation}
            />

            <div className="flex flex-col gap-4 p-6 pt-0 flex-1 overflow-hidden">

                <Conversation className={`relative flex-1 min-h-0 ${containerWidthClass}`}>
                    <ConversationContent
                        className={`h-full ${containerWidthClass} flex flex-col-reverse overflow-y-auto bg-[#F8FAFC] rounded-md p-4 remove-scrollbar`}
                    >
                        {(status === 'error' || error) && (
                            <div className="flex w-full justify-center py-2">
                                <span className="text-sm text-red-500">
                                    Oops! Something went wrong. Please try again.
                                </span>
                            </div>
                        )}

                        {showBeforeThinking && (
                            <Message from="assistant">
                                <MessageContent className="rounded-tl-none p-1">
                                    <ThinkingLoader />
                                </MessageContent>
                            </Message>
                        )}

                        {messages.length === 0 ? (
                            <QuickQuestions
                                questions={quickQuestions}
                                onQuestionClick={(text) =>
                                    handleSend({ text, files: [] })
                                }
                                disabled={status !== 'ready'}
                            />
                        ) : (
                            [...messages].reverse().map((message) => {
                                const lastMessage = messages[messages.length - 1];
                                const isLastMessage = message.id === lastMessage?.id;
                                const isAssistant = message.role === 'assistant';
                                const messageStatus =
                                    isLastMessage && isAssistant ? status : 'ready';

                                return (
                                    <ChatMessageItem
                                        key={message.id}
                                        message={message}
                                        status={messageStatus}
                                        isLast={isLastMessage && isAssistant}
                                    />
                                );
                            })
                        )}
                    </ConversationContent>

                    <ConversationScrollButton />

                    <div className="absolute top-0 left-0 right-0 h-10 bg-gradient-to-b from-[#F8FAFC] to-transparent pointer-events-none rounded-t-md z-10" />
                </Conversation>

                <ChatInputArea
                    input={input}
                    setInput={setInput}
                    onSend={handleSend}
                    status={status}
                    disabled={
                        (status !== 'ready' && status !== 'error')
                    }
                    isAssistantResponding={isAssistantResponding}
                    hasTextPart={hasTextPart}
                    showBeforeThinking={showBeforeThinking}
                    showThinkingActive={showThinkingActive}
                />
            </div>
        </div>
    );
};

export default ChatLayout;


