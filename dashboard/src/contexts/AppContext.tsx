import React, { createContext, useContext, useState, useEffect, type ReactNode } from 'react';

interface GrantInfo {
    id: string;
    alias: string;
}

interface AppContextType {
    lastVisitedGrant: GrantInfo | null;
    setLastVisitedGrant: (grant: GrantInfo) => void;
    grantsList: GrantInfo[];
    setGrantsList: (grants: GrantInfo[]) => void;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export const AppProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
    const [lastVisitedGrant, setLastVisitedGrant] = useState<GrantInfo | null>(() => {
        const savedGrant = localStorage.getItem('lastVisitedGrant');
        return savedGrant ? JSON.parse(savedGrant) : null;
    });

    const [grantsList, setGrantsList] = useState<GrantInfo[]>(() => {
         const savedGrants = localStorage.getItem('grantsList');
         return savedGrants ? JSON.parse(savedGrants) : [];
    });

    useEffect(() => {
        if (lastVisitedGrant) {
            localStorage.setItem('lastVisitedGrant', JSON.stringify(lastVisitedGrant));
        }

    }, [lastVisitedGrant]);

    useEffect(() => {
        if (grantsList.length > 0) {
            localStorage.setItem('grantsList', JSON.stringify(grantsList));
        }
    }, [grantsList]);

    return (
        <AppContext.Provider value={{ lastVisitedGrant, setLastVisitedGrant, grantsList, setGrantsList }}>
            {children}
        </AppContext.Provider>
    );
};

export const useAppContext = () => {
    const context = useContext(AppContext);
    if (!context) {
        throw new Error('useAppContext must be used within an AppProvider');
    }
    return context;
};
