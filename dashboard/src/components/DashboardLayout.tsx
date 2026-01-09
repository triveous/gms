import React, { type ReactNode } from 'react';
import TopBar from '@/components/TopBar';
import DashboardWrapper from '@/components/DashboardWrapper';

interface DashboardLayoutProps {
    children: ReactNode;
    className?: string;
    containerClassName?: string;
    showGrantSwitcher?: boolean;
}

const DashboardLayout: React.FC<DashboardLayoutProps> = ({ 
    children, 
    className,
    containerClassName,
    showGrantSwitcher = false,
}) => {
    return (
        <>
            <TopBar showGrantSwitcher={showGrantSwitcher} />
            <DashboardWrapper className={className} containerClassName={containerClassName}>
                {children}
            </DashboardWrapper>
        </>
    );
};

export default DashboardLayout;
