import React, { createContext, useContext, useState, type ReactNode } from 'react';

// ─── Types ──────────────────────────────────────────────────────────────────

export type PageContextData =
    | { page: 'grants_list'; grants: { title: string }[] }
    | {
        page: 'grant_details';
        grantTitle: string;
        selectedQuarter: string;
        projects: { title: string }[];
    }
    | {
        page: 'project_details';
        projectTitle: string;
        selectedQuarter: string;
    }
    | null;

interface PageContextType {
    pageContext: PageContextData;
    setPageContext: (data: PageContextData) => void;
}

// ─── Context ─────────────────────────────────────────────────────────────────

const PageContext = createContext<PageContextType | undefined>(undefined);

export const PageContextProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
    const [pageContext, setPageContext] = useState<PageContextData>(null);

    return (
        <PageContext.Provider value={{ pageContext, setPageContext }}>
            {children}
        </PageContext.Provider>
    );
};

/* eslint-disable react-refresh/only-export-components */
export const usePageContext = () => {
    const context = useContext(PageContext);
    if (!context) {
        throw new Error('usePageContext must be used within a PageContextProvider');
    }
    return context;
};

// ─── Helper: Build context string for sending to AI ─────────────────────────

export const buildPageContextString = (ctx: PageContextData): string => {
    if (!ctx) return '';

    switch (ctx.page) {
        case 'grants_list': {
            const grantList = ctx.grants.map((g) => `- ${g.title}`).join('\n');
            return `User is on the Grants List page. Available grants:\n${grantList}`;
        }

        case 'grant_details': {
            const projectList = ctx.projects.map((p) => `- ${p.title}`).join('\n');
            return `User is on the Grant Details page.\nGrant: ${ctx.grantTitle}\nSelected Quarter: ${ctx.selectedQuarter || 'None'}\nProjects:\n${projectList}`;
        }

        case 'project_details': {
            return `User is on the Project Details page.\nProject: ${ctx.projectTitle}\nSelected Quarter: ${ctx.selectedQuarter || 'None'}`;
        }

        default:
            return '';
    }
};
