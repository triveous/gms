import { useNavigate } from 'react-router-dom';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { TrendingUp, ChevronRight, User } from 'lucide-react';

interface Grant {
    id: string;
    name: string;
    leadInstitute: string;
    timeline: string;
    totalBudget: string;
    budgetSpend: string;
    budgetSpendPercent: number;
    overallProgress: number;
    totalProjects: number;
    impactCreated: string;
    impactUnit: string;
    aiBreakthroughs: number;
}

const mockGrants: Grant[] = [
    {
        id: '1',
        name: 'Artificial Intelligence Centre of Excellence for Health and AI',
        leadInstitute: 'IISc Bangalore',
        timeline: '4 year (April 2020 - 31 March 2024)',
        totalBudget: '₹ 300 Cr.',
        budgetSpend: '₹ 120 Cr.',
        budgetSpendPercent: 40,
        overallProgress: 40,
        totalProjects: 4,
        impactCreated: '20 Cr.',
        impactUnit: 'citizens',
        aiBreakthroughs: 3
    },
    {
        id: '2',
        name: 'Artificial Intelligence Centre of Excellence for Agriculture',
        leadInstitute: 'IIT Ropar',
        timeline: '4 year (April 2020 - 31 March 2024)',
        totalBudget: '₹ 300 Cr.',
        budgetSpend: '₹ 100 Cr.',
        budgetSpendPercent: 33,
        overallProgress: 20,
        totalProjects: 9,
        impactCreated: '10 Cr.',
        impactUnit: 'citizens',
        aiBreakthroughs: 5
    },
    {
        id: '3',
        name: 'Artificial Intelligence Centre of Excellence for Sustainable Cities',
        leadInstitute: 'IIT Kanpur',
        timeline: '4 year (April 2020 - 31 March 2024)',
        totalBudget: '₹ 300 Cr.',
        budgetSpend: '₹ 80 Cr.',
        budgetSpendPercent: 40,
        overallProgress: 30,
        totalProjects: 2,
        impactCreated: '10 Lakh.',
        impactUnit: 'citizens',
        aiBreakthroughs: 1
    }
];

export default function Grants() {
    const navigate = useNavigate();

    const handleGrantClick = (grantId: string) => {
        navigate(`/grant/${grantId}`);
    };

    return (
        <div className="min-h-screen bg-background">
            {/* Top Navigation Bar */}
            <div className="bg-card">
                <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
                    {/* Logo */}
                    <div className="flex items-center gap-2">
                        <div className="flex items-center gap-1">
                            {/* Placeholder for the logo icon from design */}
                            <TrendingUp className="w-6 h-6 text-primary" />
                            <span className="text-xl font-bold text-foreground tracking-tight">AICOE</span>
                        </div>
                    </div>

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

            <div className="max-w-7xl mx-auto px-6 py-8">
                {/* Page Title */}
                <div className="mb-6">
                    <h1 className="text-2xl font-bold text-foreground">List of CoE's</h1>
                </div>

                {/* Grants List */}
                <div className="space-y-4">
                    {mockGrants.map((grant) => (
                        <Card
                            key={grant.id}
                            className="p-6 bg-card border-border shadow-sm"
                        >
                            {/* Header Row: Name and View Button */}
                            <div className="flex items-start justify-between mb-2">
                                <h2 className="text-lg font-bold text-foreground">
                                    {grant.name}
                                </h2>
                                <Button
                                    variant="outline"
                                    className="gap-1 text-foreground border-border hover:bg-accent"
                                    onClick={() => handleGrantClick(grant.id)}
                                >
                                    View CoE <ChevronRight className="w-4 h-4" />
                                </Button>
                            </div>

                            {/* Metadata Row */}
                            <div className="flex items-center gap-4 text-sm text-muted-foreground mb-6">
                                <span>Lead Institute: <span className="text-foreground">{grant.leadInstitute}</span></span>
                                <span className="text-border">|</span>
                                <span>Timeline: {grant.timeline}</span>
                            </div>

                            {/* Metrics Grid */}
                            <div className="grid grid-cols-6 gap-8">
                                {/* Total Budget */}
                                <div>
                                    <div className="text-xs text-muted-foreground mb-1">Total Budget</div>
                                    <div className="text-xl font-bold text-foreground">
                                        {grant.totalBudget}
                                    </div>
                                </div>

                                {/* Total Budget Spend */}
                                <div>
                                    <div className="text-xs text-muted-foreground mb-1">Total Budget Spend</div>
                                    <div className="flex items-center gap-2">
                                        <div className="text-xl font-bold text-foreground">
                                            {grant.budgetSpend}
                                        </div>
                                        <Badge
                                            variant="secondary"
                                            className="bg-green-100 text-green-700 hover:bg-green-100 border-0 text-[10px] px-1.5 py-0 h-5"
                                        >
                                            {grant.budgetSpendPercent}%
                                        </Badge>
                                    </div>
                                </div>

                                {/* Overall Progress */}
                                <div>
                                    <div className="text-xs text-muted-foreground mb-1">Overall Progress</div>
                                    <div className="text-xl font-bold text-foreground">
                                        {grant.overallProgress}%
                                    </div>
                                </div>

                                {/* Total Projects */}
                                <div>
                                    <div className="text-xs text-muted-foreground mb-1">Total Projects</div>
                                    <div className="text-xl font-bold text-foreground">
                                        {grant.totalProjects}
                                    </div>
                                </div>

                                {/* Impact Created */}
                                <div>
                                    <div className="text-xs text-muted-foreground mb-1">Impact created</div>
                                    <div className="flex items-baseline gap-1">
                                        <div className="text-xl font-bold text-foreground">
                                            {grant.impactCreated}
                                        </div>
                                        {grant.impactUnit && (
                                            <span className="text-xs text-muted-foreground">
                                                {grant.impactUnit}
                                            </span>
                                        )}
                                    </div>
                                </div>

                                {/* AI Breakthroughs */}
                                <div>
                                    <div className="text-xs text-muted-foreground mb-1">AI breakthroughs</div>
                                    <div className="text-xl font-bold text-foreground">
                                        {grant.aiBreakthroughs}
                                    </div>
                                </div>
                            </div>
                        </Card>
                    ))}
                </div>
            </div>
        </div>
    );
}
