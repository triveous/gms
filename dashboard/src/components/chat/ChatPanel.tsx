import React, { useState, useEffect, useRef } from 'react';
import { useChatContext } from '@/contexts/ChatContext';
import { cn } from '@/lib/utils';
import { useChat } from '@ai-sdk/react';
import { DefaultChatTransport } from 'ai';
import { useFrappeCreateDoc, useFrappeGetDocList, useFrappeGetCall, useFrappeDeleteDoc } from 'frappe-react-sdk';
import {
    Conversation,
    ConversationContent,
    ConversationScrollButton,
} from '@/components/ai-elements/conversation';
import { Message, MessageContent } from '@/components/ai-elements/message';
import { type PromptInputMessage } from '@/components/ai-elements/prompt-input';
import ChatMessageItem from './ChatMessageItem';
import type { SDKMessage, Conversation as ConversationType } from '@/types/chat';
import { useChatScroll } from './hooks/useChatScroll';
import { useChatHistory } from './hooks/useChatHistory';
import BeforeThinkingLoader from './BeforeThinkingLoader';
import type { QuickQuestion } from '@/types/chat';
import QuickQuestions from './QuickQuestions';
import ChatHeader from './ChatHeader';
import ChatInputArea from './ChatInputArea';
import ChainOfThoughtComponent from './ChainofThought';


const ChatPanel: React.FC = () => {
    const { isChatOpen, closeChat } = useChatContext();
    const { createDoc } = useFrappeCreateDoc();
    const { deleteDoc } = useFrappeDeleteDoc();
    const [input, setInput] = useState('');
    const [currentConversaionId, setCurrentConversaionId] = useState('');
    const [initialMessage, setInitialMessage] = useState<string | null>(null);
    const [isHistoryRequested, setIsHistoryRequested] = useState(false);
    const [activeToolUI, setActiveToolUI] = useState<{ tool: string; state: string; query?: string } | null>(null);
    const [forceShowThinking, setForceShowThinking] = useState(false);
    const chatContainerRef = useRef<HTMLDivElement>(null);

    const { data: conversationListData, mutate: refetchConversationList } = useFrappeGetDocList<ConversationType>('AI Thread', {
        fields: ['name', 'title'],
        orderBy: {
            field: 'creation',
            order: 'desc'
        }
    });

    const { data: quickQuestionsData } = useFrappeGetCall('gms.api.quick_questions.get_all_quick_questions');
    const quickQuestions: QuickQuestion[] = quickQuestionsData?.message?.questions || [];

    const { messages, sendMessage, status, setMessages, error } = useChat({
        id: currentConversaionId,
        transport: new DefaultChatTransport({
            api: '/api/method/gms.api.ai.ask',
            headers: {
                'X-Frappe-CSRF-Token': (window as any).csrf_token
            },
            prepareSendMessagesRequest({ messages, id }) {
                const textPart = messages[messages.length - 1].parts?.find(p => p.type === "text")
                return { body: { query: textPart?.text, thread_id: id } };
            },
        }) as any,
        async onFinish(options: any) {
            const { isError, messages } = options;

            if (isError && messages.length <= 2) {
                const docToDelete = currentConversaionId;
                setCurrentConversaionId('');
                setMessages([]);
                setInitialMessage(null);
                if (docToDelete) {
                    try {
                        await deleteDoc('AI Thread', docToDelete);
                        refetchConversationList();
                    } catch (e) {
                        console.error('Failed to delete failed conversation:', e);
                    }
                }
            }
        },
    });

    console.log(messages)

    // Centralized auto-scroll
    useChatScroll(chatContainerRef, [messages, activeToolUI]);

    useEffect(() => {
        if (status === 'ready') {
            setActiveToolUI(null);
            setForceShowThinking(false);
        }
    }, [status]);

    // Force show "Thinking" after 3 seconds if still in beforeThinking state
    useEffect(() => {
        if (status === 'submitted' || status === 'streaming') {
            const timer = setTimeout(() => {
                setForceShowThinking(true);
            }, 3000);

            return () => clearTimeout(timer);
        } else {
            setForceShowThinking(false);
        }
    }, [status]);

    const latestAssistantMessage = messages.length > 0 && messages[messages.length - 1].role === 'assistant'
        ? messages[messages.length - 1] as SDKMessage
        : null;

    const isAssistantResponding = status === 'submitted' || status === 'streaming' || initialMessage !== null;

    const hasDataBlockPart = latestAssistantMessage?.parts?.some(p => 
        p.type === 'data-block' || p.type === 'data-goal' || p.type === 'data-step'
    );
    const hasTextPart = latestAssistantMessage?.parts?.some(p => p.type === 'text');

    const showBeforeThinking = isAssistantResponding && !hasDataBlockPart && !hasTextPart && !forceShowThinking;
    const showThinkingActive = isAssistantResponding && (hasDataBlockPart || forceShowThinking) && !hasTextPart;


    useChatHistory({
        threadId: currentConversaionId,
        isHistoryRequested,
        setMessages,
        onHistoryLoaded: () => setIsHistoryRequested(false)
    });


    const initializeConversation = async () => {
        const doc = await createDoc('AI Thread', {
            title: 'New Chat',
        });
        setCurrentConversaionId(doc.name);
        setIsHistoryRequested(false);
        return doc.name;
    };

    const handleNewChat = async () => {
        if (messages.length === 0) return;
        await initializeConversation();
    };

    const handleConversationClick = (conversationId: string) => {
        // setRenderMessages([]); // Removed
        setCurrentConversaionId(conversationId);
        setIsHistoryRequested(true);
    };


    const handleSend = async (message: PromptInputMessage) => {
        const hasText = Boolean(message.text);
        if (!hasText) {
            return;
        }
        if (currentConversaionId) {
            sendMessage({ text: message.text });
            setInput('');
            return;
        }
        setInitialMessage(message.text);
        setInput('');
        await initializeConversation()
    };

    useEffect(() => {
        if (currentConversaionId && initialMessage) {
            sendMessage({ text: initialMessage });
            setTimeout(() => setInitialMessage(null), 0);
        }
    }, [currentConversaionId, initialMessage, sendMessage]);

    return (
        <>
            {isChatOpen && (
                <div
                    className="fixed inset-0 bg-black/50 backdrop-blur-sm transition-opacity duration-300 z-40 xl:hidden"
                    onClick={closeChat}
                />
            )}

            <div
                className={cn(
                    'fixed top-0 right-0 h-screen min-w-[447px] bg-background transition-transform duration-300 ease-in-out z-50',
                    isChatOpen ? 'translate-x-0' : 'translate-x-full'
                )}
            >
                <div className="flex flex-col h-full">
                    {/* Header */}
                    <ChatHeader
                        onNewChat={handleNewChat}
                        onClose={closeChat}
                        conversationList={conversationListData || []}
                        onSelectConversation={handleConversationClick}
                    />

                    {/* Main Content Container */}
                    <div className="flex flex-col gap-4 p-6 pt-0 flex-1 overflow-hidden">

                        {/* Conversation Area */}
                        <Conversation className="relative flex-1 w-[399px] min-h-0 remove-scrollbar">
                            <ConversationContent className='h-full max-w-[399px] flex flex-col-reverse overflow-y-auto bg-[#F8FAFC] rounded-md p-4 remove-scrollbar'>
                                {(status === 'error' || error) && (
                                    <div className="flex w-full justify-center py-2">
                                        <span className="text-sm text-red-500">Oops! Something went wrong. Please try again.</span>
                                    </div>
                                )}

                                {/* REMOVED DUPLICATE THINKING BLOCK HERE */}

                                {showBeforeThinking && (
                                    <Message from="assistant">
                                        <MessageContent className="rounded-tl-none p-1">
                                            <BeforeThinkingLoader />
                                        </MessageContent>
                                    </Message>
                                )}

                                {showThinkingActive && !hasDataBlockPart && (
                                    <Message from="assistant">
                                        <MessageContent className="rounded-tl-none p-1">
                                            <ChainOfThoughtComponent
                                                open={true}
                                                data={[]}
                                                status={status}
                                            />
                                        </MessageContent>
                                    </Message>
                                )}

                                {messages.length === 0 ? (
                                    <QuickQuestions
                                        questions={quickQuestions}
                                        onQuestionClick={(text) => handleSend({ text, files: [] })}
                                        disabled={status !== 'ready'}
                                    />
                                ) : (
                                    [...messages].reverse().map((message) => {
                                        const lastMessage = messages[messages.length - 1];
                                        const isLastMessage = message.id === lastMessage?.id;
                                        const isAssistant = message.role === 'assistant';
                                        const messageStatus = (isLastMessage && isAssistant) ? status : 'ready';

                                        return (
                                            <ChatMessageItem
                                                key={message.id}
                                                message={message as SDKMessage}
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

                        {/* Input Area */}
                        <ChatInputArea
                            input={input}
                            setInput={setInput}
                            onSend={handleSend}
                            status={status}
                            disabled={(status !== 'ready' && status !== 'error') || initialMessage !== null}
                            isAssistantResponding={!!isAssistantResponding}
                            hasTextPart={hasTextPart}
                            showBeforeThinking={!!showBeforeThinking}
                            showThinkingActive={!!showThinkingActive}
                        />
                    </div>
                </div>
            </div>
        </>
    );
};

export default ChatPanel;