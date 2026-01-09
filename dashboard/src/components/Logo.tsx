import React from 'react';
import { ChartNoAxesCombined } from 'lucide-react';

export const Logo: React.FC = () => {
    return (
        <div className="flex items-center gap-2">
            <div className="flex items-center gap-1">
                {/* Placeholder for the logo icon from design */}
                <ChartNoAxesCombined className="w-6 h-6 text-sidebar-accent-foreground" />
                <span className="text-xl font-bold text-foreground tracking-tight">AIKAM</span>
            </div>
        </div>
    );
};
