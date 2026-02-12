import React, { useState, useEffect, useRef } from 'react';
import { useChatContext } from '@/contexts/ChatContext';
import { cn } from '@/lib/utils';
import { useChat } from '@ai-sdk/react';
import { DefaultChatTransport } from 'ai';
import { useFrappeCreateDoc, useFrappeGetDocList, useFrappeGetCall, useFrappeDeleteDoc } from 'frappe-react-sdk';
import { type PromptInputMessage } from '@/components/ai-elements/prompt-input';
import type { SDKMessage, Conversation as ConversationType } from '@/types/chat';
import { useChatScroll } from './hooks/useChatScroll';
import { useChatHistory } from './hooks/useChatHistory';
import type { QuickQuestion } from '@/types/chat';
import ChatLayout from './ChatLayout';

interface ChatPanelProps {
    isDrawerMode?: boolean;
}

const ChatPanel: React.FC<ChatPanelProps> = ({ isDrawerMode = true }) => {
    const { isChatOpen, closeChat } = useChatContext();
    const { createDoc } = useFrappeCreateDoc();
    const { deleteDoc } = useFrappeDeleteDoc();
    const [input, setInput] = useState('');
    const [currentConversaionId, setCurrentConversaionId] = useState('');
    const [initialMessage, setInitialMessage] = useState<string | null>(null);
    const [isHistoryRequested, setIsHistoryRequested] = useState(false);
    const [activeToolUI, setActiveToolUI] = useState<{ tool: string; state: string; query?: string } | null>(null);
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
                // 'X-Frappe-CSRF-Token': (window as any).csrf_token
                'X-Frappe-CSRF-Token': 'fd49c1ef66c75ed8b7414a272671e63545488a18dc30735c31400122'
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
        }
    }, [status]);

    const latestAssistantMessage = messages.length > 0 && messages[messages.length - 1].role === 'assistant'
        ? messages[messages.length - 1] as SDKMessage
        : null;

    const isAssistantResponding = status === 'submitted' || status === 'streaming' || initialMessage !== null;

    const hasDataBlockPart = latestAssistantMessage?.parts?.some(p => p.type === 'data-block');
    const hasTextPart = latestAssistantMessage?.parts?.some(p => p.type === 'text');

    const showBeforeThinking = isAssistantResponding && !hasDataBlockPart && !hasTextPart;
    const showThinkingActive = isAssistantResponding && hasDataBlockPart && !hasTextPart;


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

    // Drawer mode (traditional fixed overlay)
    if (isDrawerMode) {
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
                    <ChatLayout
                    isDrawerMode
                    onNewChat={handleNewChat}
                    onClose={closeChat}
                    conversationList={conversationListData || []}
                    onSelectConversation={handleConversationClick}
                    messages={messages}
                    status={status}
                    error={error}
                    quickQuestions={quickQuestions}
                    handleSend={handleSend}
                    input={input}
                    setInput={setInput}
                    isAssistantResponding={!!isAssistantResponding}
                    hasTextPart={!!hasTextPart}
                    showBeforeThinking={!!showBeforeThinking}
                    showThinkingActive={!!showThinkingActive}
                />
                </div>
            </>
        );
    }

    // Panel mode (resizable panel)
    return (
        <div className="h-full w-full bg-background border-l border-border">
            <ChatLayout
            onNewChat={handleNewChat}
            onClose={closeChat}
            conversationList={conversationListData || []}
            onSelectConversation={handleConversationClick}
            messages={messages}
            status={status}
            error={error}
            quickQuestions={quickQuestions}
            handleSend={handleSend}
            input={input}
            setInput={setInput}
            isAssistantResponding={!!isAssistantResponding}
            hasTextPart={!!hasTextPart}
            showBeforeThinking={!!showBeforeThinking}
            showThinkingActive={!!showThinkingActive}
        />
        </div>
    );
};

export default ChatPanel;