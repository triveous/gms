import React from 'react';
import { Button } from '@/components/ui/button';
import { Clock, X, MessageSquare } from 'lucide-react';
import VectorLogo from '../../assets/Vector.png';
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuLabel,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import type { Conversation } from '@/types/chat';

interface ChatHeaderProps {
    onNewChat: () => void;
    onClose: () => void;
    conversationList: Conversation[];
    onSelectConversation: (id: string) => void;
}

const ChatHeader: React.FC<ChatHeaderProps> = ({
    onNewChat,
    onClose,
    conversationList,
    onSelectConversation,
}) => {
    return (
        <div className="flex items-center justify-between px-4 py-3 h-16">
            <div className="flex items-center gap-2">
                <img src={VectorLogo} alt="Logo" className="w-4 h-4 object-contain" />
                <span className="text-[#DB8500] text-[16px] font-medium">AIKAM</span>
            </div>
            <div className="flex items-center gap-3">
                <Button variant="outline" size="sm" className="h-8 gap-2 text-sm" onClick={onNewChat}>
                    <svg className="w-4 h-4" viewBox="0 0 16 16" fill="none" stroke="currentColor">
                        <path d="M8 4v8M4 8h8" strokeWidth="2" strokeLinecap="round" />
                    </svg>
                    New Chat
                </Button>
                <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                        <Button variant="outline" size="icon" className="h-8 w-8">
                            <Clock className="w-4 h-4" />
                        </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end" className="w-[400px] max-h-[662px] overflow-y-auto">
                        <DropdownMenuLabel className="text-muted-foreground text-sm font-normal">
                            Chat History
                        </DropdownMenuLabel>
                        <DropdownMenuSeparator />
                        {conversationList && conversationList.length > 0 ? (
                            conversationList.map((conversation) => (
                                <DropdownMenuItem
                                    key={conversation.name}
                                    className="flex items-center gap-3 py-3 px-3 cursor-pointer"
                                    onClick={() => onSelectConversation(conversation.name)}
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
                <Button variant="outline" size="icon" onClick={onClose} className="h-8 w-8">
                    <X className="w-4 h-4" />
                </Button>
            </div>
        </div>
    );
};

export default ChatHeader;
