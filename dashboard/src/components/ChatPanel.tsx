import React from 'react';
import { useChatContext } from '@/contexts/ChatContext';
import { Button } from '@/components/ui/button';
import { X, MessageSquare } from 'lucide-react';
import { cn } from '@/lib/utils';

const ChatPanel: React.FC = () => {
    const { isChatOpen, closeChat } = useChatContext();

    return (
        <div
            className={cn(
                "fixed top-0 right-0 h-screen w-[400px] bg-card border-l border-border shadow-lg transition-transform duration-300 ease-in-out z-50",
                isChatOpen ? "translate-x-0" : "translate-x-full"
            )}
        >
            <div className="flex flex-col h-full">
                {/* Header */}
                <div className="flex items-center justify-between p-4 border-b border-border">
                    <div className="flex items-center gap-2">
                        <MessageSquare className="w-5 h-5 text-primary" />
                        <h2 className="text-lg font-semibold text-foreground">AI Assistant</h2>
                    </div>
                    <Button
                        variant="ghost"
                        size="icon"
                        onClick={closeChat}
                        className="h-8 w-8"
                    >
                        <X className="w-4 h-4" />
                    </Button>
                </div>

                {/* Chat Content */}
                <div className="flex-1 p-4 overflow-y-auto">
                    <p className="text-sm text-muted-foreground">
                        Chat interface will be implemented here...
                    </p>
                </div>

                {/* Input Area */}
                <div className="p-4 border-t border-border">
                    <input
                        type="text"
                        placeholder="Type a message..."
                        className="w-full px-3 py-2 text-sm border border-border rounded-md bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary"
                    />
                </div>
            </div>
        </div>
    );
};

export default ChatPanel;
