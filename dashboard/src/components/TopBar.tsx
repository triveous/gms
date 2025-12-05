import React from 'react';
import { Button } from '@/components/ui/button';
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { TrendingUp, User } from 'lucide-react';
import ChatToggleButton from '@/components/ChatToggleButton';

const TopBar: React.FC = () => {
    return (
        <div className="bg-card sticky top-0 z-40 border-b border-border">
            <div className="mx-auto px-6 h-16 flex items-center justify-between">
                {/* Logo */}
                <div className="flex items-center gap-2">
                    <div className="flex items-center gap-1">
                        {/* Placeholder for the logo icon from design */}
                        <TrendingUp className="w-6 h-6 text-primary" />
                        <span className="text-xl font-bold text-foreground tracking-tight">AICOE</span>
                    </div>
                </div>

                {/* Right side buttons */}
                <div className="flex items-center gap-2">
                    <ChatToggleButton />
                    
                    {/* User Dropdown Menu */}
                    <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                            <Button variant="outline" className="gap-2">
                                <User className="w-4 h-4" />
                                CPMU
                            </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                            <DropdownMenuItem>Profile</DropdownMenuItem>
                            <DropdownMenuItem>Settings</DropdownMenuItem>
                            <DropdownMenuItem>Logout</DropdownMenuItem>
                        </DropdownMenuContent>
                    </DropdownMenu>
                </div>
            </div>
        </div>
    );
};

export default TopBar;
