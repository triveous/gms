import React, { useState, useEffect } from 'react';
import { Outlet } from 'react-router-dom';
import ChatPanel from '@/components/chat/ChatPanel';
import { useChatContext } from '@/contexts/ChatContext';
import {
    ResizableHandle,
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


    
    // If on small screen or chat is closed, show traditional layout
    if (!isLargeScreen || !isChatOpen) {
        return (
            <>
                <div className="min-h-screen w-full">
                    <Outlet />
                </div>
                <ChatPanel isDrawerMode={true} />
            </>
        );
    }

    // On large screen with chat open - use Shadcn Resizable
    return (
        <ResizablePanelGroup 
            orientation="horizontal" 
            className="h-screen w-screen"
        >
            {/* Main Dashboard Panel - Remaining Space */}
            <ResizablePanel 
                defaultSize={windowWidth-DEFAULT_CHAT_WIDTH_PX} 
                className="h-screen overflow-auto remove-scrollbar"
                minSize={30} // Prevent dashboard from becoming too small
            >
                <Outlet />
            </ResizablePanel>


            <ResizableHandle withHandle className='w-0' />

            {/* Chat Panel - Fixed Pixel Width (converted to %) */}
            <ResizablePanel 
                defaultSize={isChatOpen? DEFAULT_CHAT_WIDTH_PX: 0}
                minSize={isChatOpen? MIN_CHAT_WIDTH_PX: 0}
                maxSize={isChatOpen? MAX_CHAT_WIDTH_PX: 0}
                className="h-screen relative"
            >
                <div className="h-screen absolute sticky top-0">
                    <ChatPanel isDrawerMode={false} />
                </div>
            </ResizablePanel>
        </ResizablePanelGroup>
    );
};

export default ResizableLayout;
