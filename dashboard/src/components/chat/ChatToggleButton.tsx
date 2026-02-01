import React from 'react';
import { useChatContext } from '@/contexts/ChatContext';
import { Button } from '@/components/ui/button';
import VectorLogo from '../../assets/Vector.png';
const ChatToggleButton: React.FC = () => {
    const { toggleChat, isChatOpen } = useChatContext();

    return (
        <Button
            onClick={toggleChat}
            className="flex items-center gap-2 px-4 py-2 rounded-md bg-yellow-50 border-2 border-orange-400 hover:bg-yellow-100 transition-colors"
            title={isChatOpen ? 'Close Chat' : 'Open Chat'}
        >
            <img src={VectorLogo} alt="Logo" className="w-4 h-4 object-contain" />
            <span className="text-[#DB8500] text-[16px] font-medium">AIKAM</span>
        </Button>
    );
};

export default ChatToggleButton;
