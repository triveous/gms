import React, { useState, useEffect, useRef } from 'react';
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
import ChatConversation from './ChatConversation';
import VectorLogo from '../assets/Vector.png';

interface Conversation {
    name: string;
    title: string;
}

const ChatPanel: React.FC = () => {
    const { isChatOpen, closeChat } = useChatContext();
    const { createDoc } = useFrappeCreateDoc();
    const [input, setInput] = useState('');
    const [currentConversaionId, setCurrentConversaionId] = useState('');
    const [initialMessage, setInitialMessage] = useState<string | null>(null);
    const [isHistoryRequested, setIsHistoryRequested] = useState(false);
    const [activeToolUI, setActiveToolUI] = useState<{ tool: string; state: string; query?: string } | null>(null);
    const chatContainerRef = useRef<HTMLDivElement>(null);



    const { messages, sendMessage, status, setMessages, addToolOutput } = useChat({
        id: currentConversaionId,
        transport: new DefaultChatTransport({
            api: '/api/method/gms.api.conversation.run',
            headers:{
                'X-Frappe-CSRF-Token': window.csrf_token
            },
        }),
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
        }
    }, [status]);


    const { data: conversationHistoryData } = useFrappeGetCall(
        'gms.api.conversation.history',
        { conversation_id: currentConversaionId },
        (currentConversaionId && isHistoryRequested) ? undefined : null
    );


    useEffect(() => {
        if (conversationHistoryData?.message && !initialMessage) {
            const transformedMessages = conversationHistoryData.message.map((msg: any) => ({
                id: msg.id,
                role: msg.role,
                parts: msg.parts
            }));
            
            setMessages(transformedMessages);
            setTimeout(() => setIsHistoryRequested(false), 0);
        }
    }, [conversationHistoryData, setMessages, initialMessage, isHistoryRequested]);


    const { data: conversationListData } = useFrappeGetDocList<Conversation>('AI Conversation', {
        fields: ['name', 'title'],
        orderBy: {
            field: 'creation',
            order: 'desc'
        },
        limit: 50
    });

    

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
        await initializeConversation();
    };

    const handleConversationClick = (conversationId: string) => {
        setCurrentConversaionId(conversationId);
        setIsHistoryRequested(true);
    };


    const handleSend = async (text: string) => {
        if (!text.trim()) return;

        // Case 1: Conversation already exists → send immediately
        if (currentConversaionId) {
            sendMessage({ text });
            setInput('');
            return;
        }

        // First message: store it and wait
        setInitialMessage(text);
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
                <div className="flex flex-col gap-4 p-6 flex-1 overflow-hidden">
                    {/* Reference Section */}
                    {/* <div className="flex items-center gap-2">
                        <span className="text-sm">Ref:</span>
                            <Button
                                variant="outline"
                                className="px-[8px] py-[5.5px] gap-2 text-foreground border-border hover:bg-accent"
                            >
                                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 14 14" fill="none">
                                    <path d="M4.75 8.66699C5.5324 8.66699 6.16699 9.30158 6.16699 10.084V12.084C6.16664 12.8661 5.53219 13.5 4.75 13.5H1.41699C0.634806 13.5 0.000351737 12.8661 0 12.084V10.084C0 9.30158 0.634589 8.66699 1.41699 8.66699H4.75ZM12.083 6C12.8654 6 13.5 6.63459 13.5 7.41699V12.083C13.5 12.8654 12.8654 13.5 12.083 13.5H8.75C7.96775 13.4998 7.33301 12.8653 7.33301 12.083V7.41699C7.33301 6.6347 7.96775 6.00018 8.75 6H12.083ZM1.5 12H4.66699V10.167H1.5V12ZM8.83301 12H12V7.5H8.83301V12ZM4.75 0C5.5324 1.28852e-07 6.16699 0.634589 6.16699 1.41699V6.08301C6.16699 6.86541 5.5324 7.5 4.75 7.5H1.41699C0.634589 7.5 0 6.86541 0 6.08301V1.41699C0 0.634589 0.634589 0 1.41699 0H4.75ZM1.5 6H4.66699V1.5H1.5V6ZM12.083 0C12.8654 1.28852e-07 13.5 0.634589 13.5 1.41699V3.41699C13.4998 4.19925 12.8653 4.83301 12.083 4.83301H8.75C7.96785 4.83283 7.33318 4.19914 7.33301 3.41699V1.41699C7.33301 0.634697 7.96775 0.000175814 8.75 0H12.083ZM8.83301 3.33301H12V1.5H8.83301V3.33301Z" fill="#020617"/>
                                </svg>
                                AICoE Health & AI
                            </Button>
                    </div> */}

                    {/* Chat Content Area */}
                    {/* Chat Content Area */}
                    <div className="relative flex-1 w-[399px] min-h-0">
                        <div 
                            ref={chatContainerRef} 
                            className="h-full w-full flex flex-col-reverse overflow-y-auto bg-[#F8FAFC] rounded-md p-4 remove-scrollbar"
                        >
                            {messages.length === 0 ? (
                                <div className="flex flex-col items-end text-right mb-2">
                                    <h3 className="text-sm font-semibold text-foreground mb-2">Quick suggestion to ask.</h3>
                                    <p className="text-xs text-muted-foreground mb-4">You can pick can from below or ask anything in chat.</p>

                                    <div className="w-full space-y-2">
                                        <Button
                                            variant="outline"
                                            className="w-auto justify-start text-sm h-auto py-2.5 px-3 text-left font-normal shadow-none"
                                            onClick={() => handleSend('How much budget utilised by each project')}
                                            disabled={status !== 'ready'}
                                        >
                                            How much budget utilised by each project
                                        </Button>
                                        <Button
                                            variant='outline'
                                            className='w-auto justify-start text-sm h-auto py-2.5 px-3 text-left font-normal shadow-none'
                                            onClick={() => handleSend('Projects having more than 5 MRL Metric')}
                                            disabled={status !== 'ready'}
                                        >
                                            Projects having more than 5 MRL Metric
                                        </Button>
                                        <Button
                                            variant='outline'
                                            className='w-auto justify-start text-sm h-auto py-2.5 px-3 text-left font-normal shadow-none'
                                            onClick={() => handleSend('Summarise Goals and Impact of the CoE')}
                                            disabled={status !== 'ready'}
                                        >
                                            Summarise Goals and Impact of the CoE
                                        </Button>
                                    </div>
                                </div>
                            ) : (
                                <ChatConversation 
                                    messages={messages} 
                                    status={status} 
                                    activeToolUI={activeToolUI} 
                                />
                            )}
                        </div>
                        {/* Top Fade Overlay */}
                        <div className="absolute top-0 left-0 right-0 h-10 bg-gradient-to-b from-[#F8FAFC] to-transparent pointer-events-none rounded-t-md z-10" />
                    </div>

                    {/* Input Area */}
                    <form
                        onSubmit={(e) => {
                            e.preventDefault();
                            handleSend(input);
                        }}
                        className="relative"
                    >
                        <div className="relative rounded-lg p-[1px] bg-gradient-to-r from-orange-400 to-pink-400">
                            <div className="relative bg-white rounded-[9px] flex items-center gap-2 px-3 py-3">
                                {/* <Plus className="w-4 h-4 text-orange-500 shrink-0" /> */}
                                <input
                                    type="text"
                                    value={input}
                                    onChange={(e) => setInput(e.target.value)}
                                    disabled={(status !== 'ready' && status !== 'error') || initialMessage !== null}
                                    placeholder="Ask me about the project"
                                    className="flex-1 text-[14px] font-normal tracking-[0.07px] text-foreground placeholder:text-muted-foreground bg-transparent border-none outline-none focus:outline-none disabled:opacity-50"
                                />
                                <button
                                    type="submit"
                                    disabled={(status !== 'ready' && status !== 'error') || initialMessage !== null || !input.trim()}
                                    className="p-0 border-none bg-[#FEF2F2] cursor-pointer disabled:opacity-50 h-[36px] w-[36px] flex items-center justify-center rounded-md"
                                >
                                    {(status === 'submitted' || status === 'streaming' || initialMessage !== null) ? (
                                        <Loader2 className="w-5 h-5 text-orange-500 animate-spin shrink-0" />
                                    ) : (
                                        <svg className="w-5 h-5 text-orange-500 shrink-0" viewBox="0 0 20 20" fill="none">
                                            <path d="M3 10L17 10M17 10L11 4M17 10L11 16" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                                        </svg>
                                    )}
                                </button>
                            </div>
                        </div>
                    </form>
                </div>
            </div>
        </div>
        </>
    );
};

export default ChatPanel;


