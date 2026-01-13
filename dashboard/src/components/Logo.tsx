import React from 'react';
import { ChartNoAxesCombined } from 'lucide-react';
import { Link } from 'react-router-dom';

export const Logo: React.FC = () => {
    return (
        <Link to="/" className="flex items-center gap-2 hover:opacity-80 transition-opacity">
            <div className="flex items-center gap-1">
                {/* Placeholder for the logo icon from design */}
                <ChartNoAxesCombined className="w-6 h-6 text-sidebar-accent-foreground" />
                <span className="text-xl font-bold text-foreground tracking-tight">AIKAM</span>
            </div>
        </Link>
    );
};
