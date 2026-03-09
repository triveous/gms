import React, { useState, useEffect } from 'react';
import { Outlet } from 'react-router-dom';
import ChatPanel from '@/components/chat/ChatPanel';
import { useChatContext } from '@/contexts/ChatContext';
import {
    ResizablePanel,
    ResizablePanelGroup,
} from '@/components/ui/resizable';


const MIN_CHAT_WIDTH_PX = 447;
const DEFAULT_CHAT_WIDTH_PX = 447;
const MAX_CHAT_WIDTH_PX = 1000;

const ResizableLayout: React.FC = () => {
    const { isChatOpen } = useChatContext();
    const [isLargeScreen, setIsLargeScreen] = useState(window.innerWidth >= 1280);
    const [windowWidth, setWindowWidth] = useState(window.innerWidth);

    useEffect(() => {
        const handleResize = () => {
            const width = window.innerWidth;
            setWindowWidth(width);
            setIsLargeScreen(width >= 1280);
        };

        window.addEventListener('resize', handleResize);
        return () => window.removeEventListener('resize', handleResize);
    }, []);


    // On large screen with chat open - use Shadcn Resizable
    // We always render the group so ChatPanel state is not destroyed on mobile resize
    return (
        <ResizablePanelGroup
            orientation="horizontal"
            className="h-screen w-screen"
        >
            {/* Main Dashboard Panel - Remaining Space */}
            <ResizablePanel
                defaultSize={windowWidth - DEFAULT_CHAT_WIDTH_PX}
                className="h-screen overflow-auto remove-scrollbar"
                minSize={30} // Prevent dashboard from becoming too small
            >
                <Outlet />
            </ResizablePanel>


            {/* Chat Panel - Fixed Pixel Width (converted to %) */}
            {/* Collapses to 0-width on mobile or when closed */}
            <ResizablePanel
                defaultSize={(isLargeScreen && isChatOpen) ? DEFAULT_CHAT_WIDTH_PX : 0}
                minSize={(isLargeScreen && isChatOpen) ? MIN_CHAT_WIDTH_PX : 0}
                maxSize={(isLargeScreen && isChatOpen) ? MAX_CHAT_WIDTH_PX : 0}
                className="h-screen relative"
            >
                <div className="h-full w-full">
                    <ChatPanel isDrawerMode={!isLargeScreen} />
                </div>
            </ResizablePanel>
        </ResizablePanelGroup>
    );
};

export default ResizableLayout;
