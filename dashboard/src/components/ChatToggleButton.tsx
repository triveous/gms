import React from 'react';
import { useChatContext } from '@/contexts/ChatContext';
import { Button } from '@/components/ui/button';
import { MessageSquare } from 'lucide-react';

const ChatToggleButton: React.FC = () => {
    const { toggleChat, isChatOpen } = useChatContext();

    return (
        <Button
            onClick={toggleChat}
            variant="outline"
            size="icon"
            className="gap-2"
            title={isChatOpen ? "Close Chat" : "Open Chat"}
        >
            <MessageSquare className="w-4 h-4" />
        </Button>
    );
};

export default ChatToggleButton;
