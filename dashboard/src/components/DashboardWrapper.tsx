import React, { type ReactNode, useEffect, useState } from 'react';
import { useChatContext } from '@/contexts/ChatContext';
import { cn } from '@/lib/utils';

interface DashboardWrapperProps {
    children: ReactNode;
    className?: string;
    containerClassName?: string;
}

const DashboardWrapper: React.FC<DashboardWrapperProps> = ({ 
    children, 
    className,
    containerClassName 
}) => {
    const { isChatOpen } = useChatContext();
    const [isLargeScreen, setIsLargeScreen] = useState(window.innerWidth >= 1280);

    useEffect(() => {
        const handleResize = () => {
            setIsLargeScreen(window.innerWidth >= 1280);
        };

        window.addEventListener('resize', handleResize);
        return () => window.removeEventListener('resize', handleResize);
    }, []);

    return (
        <div 
            className={cn(
                'min-h-screen bg-[#f8fafc] transition-all duration-300 ease-in-out p-[44px] border-border border-[1px]',
                className
            )}
            style={{
                maxWidth: (isChatOpen && isLargeScreen) ? 'calc(100vw - 464px)' : '100%',
                transition: 'max-width 300ms ease-in-out',
                borderRadius: (isChatOpen && isLargeScreen) ? '12px' : '0'
            }}
        >
            <div 
                className={cn(
                    'max-w-[1200px] mx-auto transition-all duration-300',
                    containerClassName
                )}
            >
                {children}
            </div>
        </div>
    );
};

export default DashboardWrapper;
