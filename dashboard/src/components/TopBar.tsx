import { Button } from '@/components/ui/button';
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { useFrappeAuth } from 'frappe-react-sdk';
import React, { useEffect, useState } from 'react';
import { User, ChevronsUpDown, ChevronDown, LayoutDashboard } from 'lucide-react';
import ChatToggleButton from '@/components/ChatToggleButton';
import { useChatContext } from '@/contexts/ChatContext';
import { useAuth } from '@/contexts/AuthContext';
import { Logo } from '@/components/Logo';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAppContext } from '@/contexts/AppContext';

interface TopBarProps {
    showGrantSwitcher?: boolean;
}

const TopBar: React.FC<TopBarProps> = ({ showGrantSwitcher = false }) => {
    const { isChatOpen } = useChatContext();
    const { logout } = useFrappeAuth();
    const { userData } = useAuth();
    const [isLargeScreen, setIsLargeScreen] = useState(window.innerWidth >= 1280);
    
    // Grant Switcher Logic
    const location = useLocation();
    const navigate = useNavigate();
    const { grantsList, lastVisitedGrant } = useAppContext();
    
    const pathParts = location.pathname.split('/').filter(Boolean);
    const currentGrantId = pathParts[0] || lastVisitedGrant?.id || '';

    const currentGrantName = grantsList.find(g => g.id === currentGrantId)?.alias || 'Select CoE';

    useEffect(() => {
        const handleResize = () => {
            setIsLargeScreen(window.innerWidth >= 1280);
        };

        window.addEventListener('resize', handleResize);
        return () => window.removeEventListener('resize', handleResize);
    }, []);

    const handleLogout = async () => {
        try {
            await logout();
        } catch (error) {
            console.error('Logout failed:', error);
        }
    };

    return (
        <div className="bg-card sticky top-0 z-40 ">
            <div className="mx-auto px-[72px] h-16 flex items-center justify-between">
                {/* Logo */}
                <div className="flex items-center gap-4">
                    {/* Logo */}
                    <Logo />

                    {/* Grant Switcher */}
                    {showGrantSwitcher && (
                        <div>
                             <DropdownMenu>
                                <DropdownMenuTrigger asChild>
                                    <Button variant="ghost" className="gap-2 h-9 px-3 bg-[#E2E8F0] hover:bg-muted text-secondary-foreground font-medium">
                                        {currentGrantName}
                                        <ChevronsUpDown className="w-[13.5px] h-[13.5px] text-muted-foreground" />
                                    </Button>
                                </DropdownMenuTrigger>
                                <DropdownMenuContent align="start" className="w-[240px] p-2">
                                    <div className="px-2 py-2 text-sm text-muted-foreground mb-1">
                                        List of CoE's
                                    </div>
                                    {grantsList.map((grant) => (
                                        <DropdownMenuItem 
                                            key={grant.id} 
                                            onClick={() => navigate(`/${grant.id}`)}
                                            className={`gap-3 py-2.5 my-[8px] cursor-pointer ${location.pathname.includes(grant.id) ? 'bg-muted' : ''}`}
                                        >
                                            <LayoutDashboard className="w-4 h-4 text-muted-foreground" />
                                            <span className="font-medium">{grant.alias}</span>
                                        </DropdownMenuItem>
                                    ))}
                                </DropdownMenuContent>
                            </DropdownMenu>
                        </div>
                    )}
                </div>

                {/* Right side buttons */}
                <div className="flex items-center gap-6" style={{ marginRight: (isChatOpen && isLargeScreen) ? '380px' : '0', transition: 'margin-right 300ms ease-in-out' }}>
                    {/* User Dropdown Menu */}
                    <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                            <Button variant="outline" className="gap-2">
                                <User className="w-4 h-4" />
                                {userData?.username || 'Guest'}
                                <ChevronDown className="w-4 h-4" />
                            </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                            {/* <DropdownMenuItem>Profile</DropdownMenuItem>
                            <DropdownMenuItem>Settings</DropdownMenuItem> */}
                            <DropdownMenuItem onClick={handleLogout}>Logout</DropdownMenuItem>
                        </DropdownMenuContent>
                    </DropdownMenu>

                    {/* Separator */}
                    <div className="h-6 w-px bg-border" />

                    {!isChatOpen && <ChatToggleButton />}
                </div>
            </div>
        </div>
    );
};

export default TopBar;
