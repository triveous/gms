import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useChatContext } from '@/contexts/ChatContext';
import { Button } from '@/components/ui/button';
import { X, Clock, MessageSquare, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useChat } from '@ai-sdk/react';
import { DefaultChatTransport } from 'ai';
import { useFrappeCreateDoc, useFrappeGetDocList, useFrappeGetCall } from 'frappe-react-sdk';
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

const commonQuestions = [
    'PI & Co-PI for Oral lesions project',
    'Summarise goals & impact of TANUH projects',
    'Projects having more than 5 TRL'
];

const ChatPanel: React.FC = () => {
    const { isChatOpen, closeChat } = useChatContext();
    const { createDoc } = useFrappeCreateDoc();
    const [input, setInput] = useState('');
    const [currentConversaionId, setCurrentConversaionId] = useState('');
    const [initialMessage, setInitialMessage] = useState<string | null>(null);
    const [isHistoryRequested, setIsHistoryRequested] = useState(false);
    const [activeToolUI, setActiveToolUI] = useState<{ tool: string; state: string; query?: string } | null>(null);
    const chatContainerRef = useRef<HTMLDivElement>(null);
    const [renderMessages, setRenderMessages] = useState<any[]>([]);
    const renderedAssistantIds = useRef<Set<string>>(new Set());
    const [streamingMessageId, setStreamingMessageId] = useState<string | null>(null);
    const activeStreamRef = useRef<string | null>(null);
    const [currentThinkingData, setCurrentThinkingData] = useState<any>(null);


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
            if (dataPart.type === 'data-thinking') {
                setCurrentThinkingData(dataPart.data);
            }
        },

        async onToolCall({ toolCall }) {
            if (toolCall.toolName === 'research-tool') {
                // Type casting args as any to access query safely, assuming it matches the structure
                const query = toolCall?.input?.query;
                setActiveToolUI({ 
                    tool: 'research-tool', 
                    state: status,
                    query: query
                });
            }

            // Tool output can be empty – backend logic continues
            addToolOutput({
                tool: toolCall.toolName,
                toolCallId: toolCall.toolCallId,
                output: {},
            });
        } 
    });
    // Centralized auto-scroll - scrolls to bottom whenever content changes
    useEffect(() => {
        if (chatContainerRef.current) {
            chatContainerRef.current.scrollTop = 0; // 0 = top in flex-col-reverse = bottom visually
        }
    }, [messages, activeToolUI]);

    useEffect(() => {
        if (status === 'ready') {
            setActiveToolUI(null);
            setCurrentThinkingData(null);
        }
    }, [status]);

    useEffect(() => {
        setTimeout(() => {
            setRenderMessages(prev => {
                const newUserMessages = messages.filter(m => 
                    m.role === 'user' && !prev.some(pm => pm.id === m.id)
                );
                if (newUserMessages.length === 0) return prev;
                return [...prev, ...newUserMessages];
            });
        }, 0);
    }, [messages]);


    const { data: conversationHistoryData } = useFrappeGetCall(
        'gms.api.conversation.history',
        { conversation_id: currentConversaionId },
        (currentConversaionId && isHistoryRequested) ? undefined : null
    );



    useEffect(() => {
        if (conversationHistoryData?.message && !initialMessage) {
            const transformedMessages = conversationHistoryData.message
                .map((msg: { id: string; role: 'user' | 'assistant'; parts: Record<string, unknown>[] }) => ({
                    id: msg.id,
                    role: msg.role,
                    parts: msg.parts
                }))
                .filter((msg: { id: string; role: string; parts: Record<string, unknown>[] }) => {
                    // Always keep user messages
                    if (msg.role === 'user') return true;
                    // For assistant messages, only keep if they contain actual text content
                    return msg.parts?.some((p) => p['type'] === 'text');
                });
            
            setTimeout(() => {
                // Mark all assistant messages from history as already rendered
                transformedMessages.forEach((msg: { id: string; role: string }) => {
                    if (msg.role === 'assistant') {
                        renderedAssistantIds.current.add(msg.id);
                    }
                });
                
                setMessages(transformedMessages);
                setRenderMessages(transformedMessages);
                setIsHistoryRequested(false);
            }, 0);
        }
    }, [conversationHistoryData, setMessages, initialMessage, isHistoryRequested]);


    const streamResponse = useCallback(
        async (messageId: string, parts: any[]) => {
            if (activeStreamRef.current === messageId) return;
            activeStreamRef.current = messageId;
            
            const textPart = parts.find(p => p.type === 'text');
            const otherParts = parts.filter(p => !['text', 'ui'].includes(p.type));
            
            const content = textPart?.text || '';
            const words = content.split(' ');
            let currentContent = '';
            setStreamingMessageId(messageId);
            
            // Insert assistant message into renderMessages with other parts and empty text part
            setRenderMessages(prev => [
                ...prev,
                {
                    id: messageId,
                    role: 'assistant',
                    parts: [...otherParts, { type: 'text', text: '' }],
                },
            ]);

            for (const word of words) {
                // 🚫 cancel if another stream started
                if (activeStreamRef.current !== messageId) return;
                currentContent += (currentContent ? ' ' : '') + word;

                setRenderMessages(prev =>
                    prev.map(msg =>
                    msg.id === messageId
                        ? {
                            ...msg,
                            parts: [...otherParts, { type: 'text', text: currentContent }],
                        }
                        : msg
                    )
                );

                await new Promise(res => setTimeout(res, Math.random() * 100 + 50));
            }
            activeStreamRef.current = null;
            setStreamingMessageId(null);
        },
        []
    );


    useEffect(() => {
        const last = messages.at(-1);
        if (!last) return;

        // Only act on assistant messages
        if (last.role !== 'assistant') return;

        // Only after model is done generating
        if (status !== 'ready') return;

        // Prevent re-streaming the same message
        if (renderedAssistantIds.current.has(last.id)) return;

        renderedAssistantIds.current.add(last.id);

        const hasText = last.parts?.some(p => p.type === 'text');
        
        if (!hasText) {
             // If no text, just set it in renderMessages directly (e.g. only thinking)
             setTimeout(() => {
                 setRenderMessages(prev => [...prev, last]);
             }, 0);
             return;
        }

        setTimeout(() => {
             streamResponse(last.id, last.parts);
        }, 0);
    }, [messages, status, streamResponse]);

    

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
        setRenderMessages([]); // Clear for new chat
        renderedAssistantIds.current.clear();
        await initializeConversation();
    };

    const handleConversationClick = (conversationId: string) => {
        setRenderMessages([]); // Clear before switching
        renderedAssistantIds.current.clear();
        setCurrentConversaionId(conversationId);
        setIsHistoryRequested(true);
    };


    const handleSend = async (message: PromptInputMessage) => {
        const hasText = Boolean(message.text);
        if (!hasText) {
            return;
        }
        // Case 1: Conversation already exists → send immediately
        if (currentConversaionId) {
            sendMessage({ text: message.text });
            setInput('');
            return;
        }
                // First message: store it and wait
        setInitialMessage(message.text);
        setInput('');

        // Case 2: No conversation → create it first
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
            {/* Backdrop - only visible on screens below 1280px */}
            {isChatOpen && (
                <div
                    className="fixed inset-0 bg-black/50 backdrop-blur-sm transition-opacity duration-300 z-40 xl:hidden"
                    onClick={closeChat}
                />
            )}
            
            {/* Chat Panel */}
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

                            {/* Real-time thinking display during streaming */}
                            {(status === 'streaming' || status === 'submitted') && currentThinkingData && (
                                <MessageBranch defaultBranch={0} key="current-thinking">
                                    <MessageBranchContent className="flex flex-col-reverse gap-6">
                                        <Message from="assistant" key="thinking-message">
                                            <MessageContent className="rounded-2xl px-4 py-2.5 transition-all duration-300 rounded-tl-none p-1">
                                                <ChainOfThoughtComponent open={true} data={currentThinkingData} status={status} />
                                            </MessageContent>
                                        </Message>
                                    </MessageBranchContent>
                                </MessageBranch>
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
                            ([...renderMessages].reverse().map((message) => (
                                <MessageBranch defaultBranch={0} key={message.id}>
                                    <MessageBranchContent  className="flex flex-col-reverse gap-6 w-full max-w-full overflow-hidden">
                                        <Message
                                            from={message.role}
                                            key={message.id}
                                        >
                                            {message.parts.map((part, index) => {
                                                if (part.type === 'text' || part.type === 'data-thinking') {
                                                    console.log('Part in loop:', part);
                                                    return (
                                                        <MessageContent key={index} className={cn(
                                                            'rounded-2xl px-4 py-2.5 transition-all duration-300',
                                                            message.role === 'user' 
                                                                ? 'bg-white border border-slate-200 !rounded-[6px] px-4 py-2 text-sm text-slate-700 max-w-[85%]' 
                                                                : 'rounded-tl-none p-1 w-full max-w-full overflow-hidden'
                                                        )}>
                                                            {part.type === 'data-thinking' && (
                                                                <ChainOfThoughtComponent open={true} data={part.data} status={status} />
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
                                            })}
                                        </Message>
                                    </MessageBranchContent>
                                </MessageBranch>
                            )))
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
                                    disabled={!(input.trim() || status) || status === 'streaming' || status === 'submitted' }
                                    status={status}
                                    className='bg-[#FEF2F2]  text-orange-500 hover:!text-orange-700 cursor-pointer'
                                    children={<>
                                        {(status === 'submitted' || status === 'streaming' || initialMessage !== null) ? (
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


