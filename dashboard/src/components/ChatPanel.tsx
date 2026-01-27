import React, { useState, useEffect, useRef } from 'react';
import { useChatContext } from '@/contexts/ChatContext';
import { Button } from '@/components/ui/button';
import { X, Clock, MessageSquare, Square, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useChat } from '@ai-sdk/react';
import { DefaultChatTransport } from 'ai';
import { useFrappeCreateDoc, useFrappeGetDocList, useFrappeGetCall, useFrappeDeleteDoc } from 'frappe-react-sdk';
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuLabel,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import VectorLogo from '../assets/Vector.png';
import {
  MessageBranch,
  MessageBranchContent,
} from '@/components/ai-elements/message';
import {
  Conversation,
  ConversationContent,
  ConversationScrollButton,
} from '@/components/ai-elements/conversation';
import { Message, MessageContent, MessageResponse } from '@/components/ai-elements/message';
import {
  PromptInput,
  PromptInputBody,
  type PromptInputMessage,
  PromptInputSubmit,
  PromptInputTextarea,
} from '@/components/ai-elements/prompt-input';
import ChainOfThoughtComponent from './ChainofThought';

interface Conversation {
    name: string;
    title: string;
}

interface SDKMessage {
    id: string;
    role: 'user' | 'assistant' | 'system' | 'data';
    content?: string;
    parts?: { type: string; data?: unknown; text?: string }[];
}

const ThreeDotsLoader = () => (
    <div className="flex space-x-1 items-center h-5">
        <div className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce [animation-delay:-0.3s]"></div>
        <div className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce [animation-delay:-0.15s]"></div>
        <div className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce"></div>
    </div>
);

const commonQuestions = [
    'PI & Co-PI for Oral lesions project',
    'Summarise goals & impact of TANUH projects',
    'Projects having more than 5 TRL'
];

const ChatPanel: React.FC = () => {
    const { isChatOpen, closeChat } = useChatContext();
    const { createDoc } = useFrappeCreateDoc();
    const { deleteDoc } = useFrappeDeleteDoc();
    const [input, setInput] = useState('');
    const [currentConversaionId, setCurrentConversaionId] = useState('');
    const [initialMessage, setInitialMessage] = useState<string | null>(null);
    const [isHistoryRequested, setIsHistoryRequested] = useState(false);
    const [activeToolUI, setActiveToolUI] = useState<{ tool: string; state: string; query?: string } | null>(null);
    const chatContainerRef = useRef<HTMLDivElement>(null);
    
    // Synced directly with SDK messages
    const [renderMessages, setRenderMessages] = useState<SDKMessage[]>([]);

    const { data: conversationListData, mutate: refetchConversationList } = useFrappeGetDocList<Conversation>('AI Conversation', {
        fields: ['name', 'title'],
        orderBy: {
            field: 'creation',
            order: 'desc'
        }
    });

    const { messages, sendMessage, status, setMessages, addToolOutput, error } = useChat({
        id: currentConversaionId,
        transport: new DefaultChatTransport({
            api: '/api/method/gms.api.conversation.run',
            headers:{
                'X-Frappe-CSRF-Token': window.csrf_token
            },
        }),
        onData: (dataPart) => {
            if (dataPart.type === 'data-conversation-title') {
                refetchConversationList();
            }
            // Removed 'data-thinking' handling here because it's handled in the message loop
        },

        async onToolCall({ toolCall }) {
            if (toolCall.toolName === 'research-tool') {
                const query = toolCall?.input?.query;
                setActiveToolUI({ 
                    tool: 'research-tool', 
                    state: status,
                    query: query
                });
            }

            addToolOutput({
                tool: toolCall.toolName,
                toolCallId: toolCall.toolCallId,
                output: {},
            });
        },
        async onFinish(options: any) {
            const { isError, messages } = options;

            if (isError && messages.length <= 2) {
                const docToDelete = currentConversaionId;
                setCurrentConversaionId('');
                setMessages([]);
                setInitialMessage(null);
                if (docToDelete) {
                    try {
                        await deleteDoc('AI Conversation', docToDelete);
                        refetchConversationList();
                    } catch (e) {
                        console.error('Failed to delete failed conversation:', e);
                    }
                }
            }
        },
    });

    // Centralized auto-scroll
    useEffect(() => {
        if (chatContainerRef.current) {
            chatContainerRef.current.scrollTop = 0; 
        }
    }, [messages, activeToolUI]);

    useEffect(() => {
        if (status === 'ready') {
            setActiveToolUI(null);
        }
    }, [status]);

    useEffect(() => {
        setRenderMessages(messages);
    }, [messages]);

    const latestAssistantMessage = renderMessages.length > 0 && renderMessages[renderMessages.length - 1].role === 'assistant' 
        ? renderMessages[renderMessages.length - 1] 
        : null;
    
    const isAssistantResponding = status === 'submitted' || status === 'streaming' || initialMessage !== null;
    
    const hasThinkingPart = latestAssistantMessage?.parts?.some(p => p.type === 'data-thinking');
    const hasTextPart = latestAssistantMessage?.parts?.some(p => p.type === 'text');

    const showBeforeThinking = isAssistantResponding && !hasThinkingPart && !hasTextPart;
    const showThinkingActive = isAssistantResponding && hasThinkingPart && !hasTextPart;


    const { data: conversationHistoryData } = useFrappeGetCall(
        'gms.api.conversation.history',
        { conversation_id: currentConversaionId },
        (currentConversaionId && isHistoryRequested) ? undefined : null
    );

    // Handle History Loading
    useEffect(() => {
        if (conversationHistoryData?.message && !initialMessage) {
            const transformedMessages = conversationHistoryData.message
                .map((msg: { id: string; role: 'user' | 'assistant'; parts: Record<string, unknown>[] }) => ({
                    id: msg.id,
                    role: msg.role,
                    parts: msg.parts
                }))
                .filter((msg: { id: string; role: string; parts: Record<string, unknown>[] }) => {
                    if (msg.role === 'user') return true;
                    // Keep text or thinking parts
                    return msg.parts?.some((p) => p['type'] === 'text' || p['type'] === 'data-thinking');
                });
  
            setMessages(transformedMessages);
            setIsHistoryRequested(false);
        }
    }, [conversationHistoryData, setMessages, initialMessage, isHistoryRequested]);


    const initializeConversation = async () => {
        const doc = await createDoc('AI Conversation', {
            title: 'New Conversation',
        });
        setCurrentConversaionId(doc.name);
        setIsHistoryRequested(false);
        return doc.name;
    };

    const handleNewChat = async () => {
        if (messages.length === 0) return;
        setRenderMessages([]); 
        await initializeConversation();
    };

    const handleConversationClick = (conversationId: string) => {
        setRenderMessages([]); 
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
                <div className="flex items-center justify-between px-4 py-3  h-16">
                    <div className="flex items-center gap-2">
                        <img src={VectorLogo} alt="Logo" className="w-4 h-4 object-contain" />
                        <span className="text-[#DB8500] text-[16px] font-medium">AIKAM</span>
                    </div>
                    <div className="flex items-center gap-3">
                        <Button variant="outline" size="sm" className="h-8 gap-2 text-sm" onClick={() => handleNewChat()}>
                            <svg className="w-4 h-4" viewBox="0 0 16 16" fill="none" stroke="currentColor">
                                <path d="M8 4v8M4 8h8" strokeWidth="2" strokeLinecap="round"/>
                            </svg>
                            New Chat
                        </Button>
                        <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                                <Button variant="outline" size="icon" className="h-8 w-8">
                                    <Clock className="w-4 h-4" />
                                </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end" className="w-[400px]">
                                <DropdownMenuLabel className="text-muted-foreground text-sm font-normal">
                                    Chat History
                                </DropdownMenuLabel>
                                <DropdownMenuSeparator />
                                {conversationListData && conversationListData.length > 0 ? (
                                    conversationListData.map((conversation) => (
                                        <DropdownMenuItem 
                                            key={conversation.name}
                                            className="flex items-center gap-3 py-3 px-3 cursor-pointer"
                                            onClick={() => handleConversationClick(conversation.name)}
                                        >
                                            <MessageSquare className="w-5 h-5 shrink-0" />
                                            <span className="flex-1 truncate">{conversation.title}</span>
                                        </DropdownMenuItem>
                                    ))
                                ) : (
                                    <div className="px-3 py-2 text-sm text-muted-foreground">
                                        No conversations yet
                                    </div>
                                )}
                            </DropdownMenuContent>
                        </DropdownMenu>
                        <Button
                            variant="outline"
                            size="icon"
                            onClick={closeChat}
                            className="h-8 w-8 "
                        >
                            <X className="w-4 h-4" />
                        </Button>
                    </div>
                </div>

                {/* Main Content Container */}
                <div className="flex flex-col gap-4 p-6 pt-0 flex-1 overflow-hidden">
                    
                    {/* Conversation Area */}
                    <Conversation className="relative flex-1 w-[399px] min-h-0 remove-scrollbar">
                        <ConversationContent className='h-full max-w-[399px] flex flex-col-reverse overflow-y-auto bg-[#F8FAFC] rounded-md p-4 remove-scrollbar'>
                            {(status === 'error'||error) && (
                                <div className="flex w-full justify-center py-2">
                                    <span className="text-sm text-red-500">Oops! Something went wrong. Please try again.</span>
                                </div>
                            )}

                            {/* REMOVED DUPLICATE THINKING BLOCK HERE */}

                            {showBeforeThinking && (
                                <Message from="assistant">
                                    <MessageContent className="rounded-tl-none p-1">
                                        <ThreeDotsLoader />
                                    </MessageContent>
                                </Message>
                            )}

                            {renderMessages.length === 0 ? (
                                <div className="flex flex-col items-end text-right mb-2">
                                    <h3 className="text-sm font-semibold text-foreground mb-2">Quick suggestion to ask.</h3>
                                    <p className="text-xs text-muted-foreground mb-4">You can pick can from below or ask anything in chat.</p>

                                    <div className="w-full space-y-2">
                                        {commonQuestions.map((q) => (
                                            <Button
                                                key={q}
                                                variant="outline"
                                                className="w-auto justify-start text-sm h-auto py-2.5 px-3 text-left font-normal shadow-none"
                                                onClick={() => handleSend({ text: q, files: [] })}
                                                disabled={status !== 'ready'}
                                            >
                                                {q}
                                            </Button>
                                        ))}
                                    </div>
                                </div>
                            ) : (
                                (() => {
                                    const lastMessage = renderMessages[renderMessages.length - 1];
                                    return [...renderMessages].reverse().map((message) => {
                                        const isLastMessage = message.id === lastMessage?.id;
                                        const isAssistant = message.role === 'assistant';
                                        const messageStatus = (isLastMessage && isAssistant) ? status : 'ready';

                                        return (
                                            <MessageBranch defaultBranch={0} key={message.id}>
                                                <MessageBranchContent className="flex flex-col-reverse gap-6 w-full max-w-full overflow-hidden">
                                                    <Message from={message.role} key={message.id}>
                                                        {message.parts ? (
                                                            message.parts.map((part: any, index: number) => {
                                                                if (part.type === 'text' || part.type === 'data-thinking') {
                                                                    return (
                                                                        <MessageContent key={index} className={cn(
                                                                            'rounded-2xl px-4 py-2.5 transition-all duration-300',
                                                                            message.role === 'user' 
                                                                                ? 'bg-white border border-slate-200 !rounded-[6px] px-4 py-2 text-sm text-slate-700 max-w-[85%]' 
                                                                                : 'rounded-tl-none p-1'
                                                                        )}>
                                                                            {part.type === 'data-thinking' && (
                                                                                <ChainOfThoughtComponent 
                                                                                    key={`cot-${message.id}-${index}`}
                                                                                    open={true} 
                                                                                    data={part.data} 
                                                                                    status={messageStatus} 
                                                                                />
                                                                            )}
                                                                            {part.type === 'text' && (
                                                                                <MessageResponse className={message.role === 'user' ? 'text-slate-900' : ''}>
                                                                                    {part.text}
                                                                                </MessageResponse>
                                                                            )}
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
                                    });
                                })()
                            )}
                            </ConversationContent>
                            <ConversationScrollButton />
                            <div className="absolute top-0 left-0 right-0 h-10 bg-gradient-to-b from-[#F8FAFC] to-transparent pointer-events-none rounded-t-md z-10" />
                        </Conversation>
                    
                    {/* Input Area */}
                    <div className="relative">
                        <div className="relative rounded-lg p-[1px] bg-gradient-to-r from-orange-400 to-pink-400">
                            <PromptInput 
                                onSubmit={handleSend} 
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
                                        disabled={(status !== 'ready' && status !== 'error') || initialMessage !== null}
                                    />
                                </PromptInputBody>
                                <PromptInputSubmit
                                    disabled={!(input.trim() || status) || (isAssistantResponding && !hasTextPart)}
                                    status={status}
                                    className='bg-[#FEF2F2]  text-orange-500 hover:!text-orange-700 cursor-pointer'
                                    children={<>
                                        {showBeforeThinking ? (
                                            <Square className="w-4 h-4 text-orange-500 fill-orange-500 shrink-0" />
                                        ) : showThinkingActive ? (
                                            <Loader2 className="w-5 h-5 text-orange-500 animate-spin shrink-0" />
                                        ) : (
                                            <svg className="w-5 h-5 text-orange-500 shrink-0" viewBox="0 0 20 20" fill="none">
                                                <path d="M3 10L17 10M17 10L11 4M17 10L11 16" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                                            </svg>
                                        )}
                                    </>}
                                />
                            </PromptInput>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        </>
    );
};

export default ChatPanel;