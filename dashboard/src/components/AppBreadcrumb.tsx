import React from 'react';
import { useNavigate, useLocation, useParams } from 'react-router-dom';
import { useAppContext } from '@/contexts/AppContext';
import { useFrappeGetCall } from 'frappe-react-sdk';

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
    const { grantId, projectId } = useParams<{ grantId: string; projectId: string }>();

    const { data: projectData } = useFrappeGetCall<{ message: { project: { title: string } } }>(
        'gms.api.project.get_project_details',
        { project_id: projectId },
        projectId ? undefined : null
    );
    
    let calculatedItems: BreadcrumbItem[] = [{ label: 'AIKAM', path: '/' }];
    
    if (grantId) {
        const grantLabel = lastVisitedGrant?.alias || 'Grant';
        if (projectId) {
            const projectLabel = projectData?.message?.project?.title || 'Project';
            const isProjectRoot = location.pathname.replace(/\/$/, '').endsWith(projectId);
            
            if (isProjectRoot) {
                 calculatedItems = [
                    { label: 'AIKAM', path: '/' },
                    { label: grantLabel, path: `/${grantId}` }
                    // Project Label omitted on Project Dashboard as requested
                ];
            } else {
                calculatedItems = [
                    { label: 'AIKAM', path: '/' },
                    { label: grantLabel, path: `/${grantId}` },
                    { label: projectLabel, path: `/${grantId}/${projectId}` }
                ];
            }
        } else {
            calculatedItems = [
                { label: 'AIKAM', path: '/' },
                { label: grantLabel } // Current page (Grant Dashboard)
            ];
        }
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
