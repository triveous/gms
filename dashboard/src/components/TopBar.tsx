import React, { useEffect, useState } from 'react';
import { Button } from '@/components/ui/button';
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { User, ChevronDown, ChartNoAxesCombined } from 'lucide-react';
import ChatToggleButton from '@/components/ChatToggleButton';
import { useChatContext } from '@/contexts/ChatContext';
import { useAuth } from '@/contexts/AuthContext';

const TopBar: React.FC = () => {
    const { isChatOpen } = useChatContext();
    const { logout } = useAuth();
    const [isLargeScreen, setIsLargeScreen] = useState(window.innerWidth >= 1280);

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
                <div className="flex items-center gap-2">
                    <div className="flex items-center gap-1">
                        {/* Placeholder for the logo icon from design */}
                        <ChartNoAxesCombined className="w-6 h-6 text-sidebar-accent-foreground" />
                        <span className="text-xl font-bold text-foreground tracking-tight">AICOE</span>
                    </div>
                </div>

                {/* Right side buttons */}
                <div className="flex items-center gap-6" style={{ marginRight: (isChatOpen && isLargeScreen) ? '380px' : '0', transition: 'margin-right 300ms ease-in-out' }}>
                    {/* User Dropdown Menu */}
                    <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                            <Button variant="outline" className="gap-2">
                                <User className="w-4 h-4" />
                                CPMU
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
