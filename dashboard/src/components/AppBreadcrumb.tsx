import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAppContext } from '@/contexts/AppContext';

export interface BreadcrumbItem {
    label: string;
    path?: string;
    action?: () => void;
}

interface AppBreadcrumbProps {
    items?: BreadcrumbItem[];
}

export const AppBreadcrumb: React.FC<AppBreadcrumbProps> = ({ items = [] }) => {
    const navigate = useNavigate();
    const location = useLocation();
    const { lastVisitedGrant } = useAppContext();

    const isProjectPage = location.pathname.includes('/project/');
    
    let calculatedItems: BreadcrumbItem[] = [{ label: 'AIKAM', path: '/' }];
    
    if (isProjectPage) {
        calculatedItems = [
            { label: 'AIKAM', path: '/' },
            { label: lastVisitedGrant?.alias || 'Projects', action: () => navigate(-1) }
        ];
    } else {
        calculatedItems = [{ label: 'AIKAM', path: '/' }];
    }

    const displayItems = items.length > 0 ? items : calculatedItems;

    return (
        <div className="mb-6 flex items-center gap-2">
            {displayItems.map((item, index) => {
                const isLast = index === displayItems.length - 1;
                const handleClick = () => {
                    if (item.action) {
                        item.action();
                    } else if (item.path) {
                        navigate(item.path);
                    }
                };
                
                // If it's the last item and there's more than one item, it's usually current page (active)
                // However, user's design shows "Projects" (which is current in the list but clickable to go back? No, the code said navigate(-1)).
                // In Grant.tsx: Home > [No label for current page?]
                // In Project.tsx: Home > Projects (clickable, goes back)
                // Actually in Project.tsx code: Home > (Projects clickable, goes back)
                // It doesn't show the current page title in breadcrumb in Project.tsx.
                
                return (
                    <React.Fragment key={index}>
                        <button
                            onClick={handleClick}
                            className={`text-sm flex items-center gap-1 ${
                                isLast && displayItems.length > 1
                                    ? 'text-foreground' 
                                    : 'text-muted-foreground hover:text-foreground'
                            }`}
                        >
                            {item.label}
                        </button>
                        {(index < displayItems.length - 1 || displayItems.length === 1) && (
                            <span className="text-sm text-muted-foreground">›</span>
                        )}
                    </React.Fragment>
                );
            })}
        </div>
    );
};
