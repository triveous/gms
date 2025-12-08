import React, { type ReactNode } from 'react';
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

    return (
        <div 
            className={cn(
                "min-h-screen bg-[#f8fafc] transition-all duration-300 ease-in-out p-[44px] border-border border-[1px]",
                className
            )}
            style={{
                maxWidth: isChatOpen ? 'calc(100vw - 464px)' : '100%',
                transition: 'max-width 300ms ease-in-out',
                borderRadius: isChatOpen ? '12px' : '0'
            }}
        >
            <div 
                className={cn(
                    "max-w-[1200px] mx-auto transition-all duration-300",
                    containerClassName
                )}
            >
                {children}
            </div>
        </div>
    );
};

export default DashboardWrapper;
