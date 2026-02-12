import { Button } from '@/components/ui/button';
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import React from 'react';
import { User, ChevronsUpDown, ChevronDown, LayoutDashboard, Building } from 'lucide-react';
import ChatToggleButton from './chat/ChatToggleButton';
import { useChatContext } from '@/contexts/ChatContext';
import { useAuth } from '@/contexts/AuthContext';
import { Logo } from '@/components/Logo';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAppContext } from '@/contexts/AppContext';
import { useFrappeGetCall } from 'frappe-react-sdk';

interface TopBarProps {
    showGrantSwitcher?: boolean;
}

const TopBar: React.FC<TopBarProps> = ({ showGrantSwitcher = false }) => {
    const { isChatOpen } = useChatContext();
    const { logout, userData, user } = useAuth();

    const { data: orgResponse } = useFrappeGetCall(
        'gms.api.organization.get_user_organization',
        user ? undefined : null as any
    );



    // Grant Switcher Logic
    const location = useLocation();
    const navigate = useNavigate();
    const { grantsList, lastVisitedGrant } = useAppContext();

    const pathParts = location.pathname.split('/').filter(Boolean);
    const currentGrantId = pathParts[0] || lastVisitedGrant?.id || '';

    const currentGrantName = grantsList.find(g => g.id === currentGrantId)?.alias || 'Select CoE';



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
                {/* Left: Logo and Grant Switcher */}
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

                {/* Right: Org, User, Chat Toggle */}
                <div className="flex items-center gap-6">
                    {/* Organization Name */}
                    {orgResponse?.message?.organization_name && (
                        <div className="flex items-center gap-2 text-[#475569] font-medium text-sm">
                            <Building className="w-5 h-5" />
                            <span>{orgResponse.message.organization_name}</span>
                        </div>
                    )}

                    {/* User Dropdown Menu */}
                    <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                            <Button variant="outline" className="gap-2">
                                <User className="w-4 h-4" />
                                {userData?.full_name || userData?.username || 'Guest'}
                                <ChevronDown className="w-4 h-4" />
                            </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                            <DropdownMenuItem onClick={handleLogout}>Logout</DropdownMenuItem>
                        </DropdownMenuContent>
                    </DropdownMenu>

                    {/* Separator */}
                    {!isChatOpen && (
                        <>
                            <div className="h-6 w-px bg-border" />
                            <ChatToggleButton />
                        </>
                    )}
                </div>
            </div>
        </div>
    );
};

export default TopBar;
