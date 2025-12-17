import React, { type ReactNode } from 'react';
import TopBar from '@/components/TopBar';
import DashboardWrapper from '@/components/DashboardWrapper';

interface DashboardLayoutProps {
    children: ReactNode;
    className?: string;
    containerClassName?: string;
}

const DashboardLayout: React.FC<DashboardLayoutProps> = ({ 
    children, 
    className,
    containerClassName 
}) => {
    return (
        <>
            <TopBar />
            <DashboardWrapper className={className} containerClassName={containerClassName}>
                {children}
            </DashboardWrapper>
        </>
    );
};

export default DashboardLayout;
