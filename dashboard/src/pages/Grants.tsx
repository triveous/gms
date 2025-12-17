import { useNavigate } from 'react-router-dom';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ChevronRight } from 'lucide-react';
import DashboardLayout from '@/components/DashboardLayout';
import { SectionWrapper } from '@/components/SectionWrapper';

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
    },
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
        <DashboardLayout>
            {/* Page Title */}
            <SectionWrapper 
                title="List of CoE's"
                contentClassName="space-y-4"
            >
                {mockGrants.map((grant) => (
                    <div
                        key={grant.id}
                        className="p-6 bg-card border-border rounded border flex flex-col gap-4"
                    >
                        {/* Header Section */}
                        <div className="flex gap-4">
                            {/* Left Container */}
                            <div className="flex flex-col gap-4 flex-1">
                                {/* Header Row */}
                                <h2 className="text-foreground text-xl font-semibold leading-[120%] tracking-[-0.4px]">
                                    {grant.name}
                                </h2>
                                
                                {/* Metadata Row */}
                                <div className="flex items-center gap-4 text-sm text-muted-foreground font-normal leading-[150%]">
                                    <span>Lead Institute: {grant.leadInstitute}</span>
                                    <span className="text-border">|</span>
                                    <span>Timeline: {grant.timeline}</span>
                                </div>
                            </div>

                            {/* Right Container */}
                            <div>
                                <Button
                                    variant="outline"
                                    className="w-[155.5px] h-[45px] px-6 gap-2 text-foreground border-border hover:bg-accent"
                                    onClick={() => handleGrantClick(grant.id)}
                                >
                                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 14 14" fill="none">
                                        <path d="M4.75 8.66699C5.5324 8.66699 6.16699 9.30158 6.16699 10.084V12.084C6.16664 12.8661 5.53219 13.5 4.75 13.5H1.41699C0.634806 13.5 0.000351737 12.8661 0 12.084V10.084C0 9.30158 0.634589 8.66699 1.41699 8.66699H4.75ZM12.083 6C12.8654 6 13.5 6.63459 13.5 7.41699V12.083C13.5 12.8654 12.8654 13.5 12.083 13.5H8.75C7.96775 13.4998 7.33301 12.8653 7.33301 12.083V7.41699C7.33301 6.6347 7.96775 6.00018 8.75 6H12.083ZM1.5 12H4.66699V10.167H1.5V12ZM8.83301 12H12V7.5H8.83301V12ZM4.75 0C5.5324 1.28852e-07 6.16699 0.634589 6.16699 1.41699V6.08301C6.16699 6.86541 5.5324 7.5 4.75 7.5H1.41699C0.634589 7.5 0 6.86541 0 6.08301V1.41699C0 0.634589 0.634589 0 1.41699 0H4.75ZM1.5 6H4.66699V1.5H1.5V6ZM12.083 0C12.8654 1.28852e-07 13.5 0.634589 13.5 1.41699V3.41699C13.4998 4.19925 12.8653 4.83301 12.083 4.83301H8.75C7.96785 4.83283 7.33318 4.19914 7.33301 3.41699V1.41699C7.33301 0.634697 7.96775 0.000175814 8.75 0H12.083ZM8.83301 3.33301H12V1.5H8.83301V3.33301Z" fill="#020617"/>
                                    </svg>
                                    View CoE <ChevronRight className="w-4 h-4" />
                                </Button>
                            </div>
                        </div>

                        {/* Metrics Grid */}
                        <div className="flex gap-4">
                            {/* Total Budget */}
                            <div>
                                <div className="text-muted-foreground font-body font-medium text-sm leading-5 tracking-[0.5%]">Total Budget</div>
                                <div className="text-xl font-bold text-foreground">
                                    {grant.totalBudget}
                                </div>
                            </div>

                            <div className="w-px bg-border self-stretch" />

                            {/* Total Budget Spend */}
                            <div>
                                <div className="text-muted-foreground font-body font-medium text-sm leading-5 tracking-[0.5%]">Total Budget Spend</div>
                                <div className="flex items-center gap-2">
                                    <div className="text-xl font-bold text-foreground">
                                        {grant.budgetSpend}
                                    </div>
                                    <Badge
                                        variant="secondary"
                                        className="bg-green-100 hover:bg-green-100 border-0 text-[10px] px-1.5 py-0 h-5"
                                    >
                                        {grant.budgetSpendPercent}%
                                    </Badge>
                                </div>
                            </div>

                            <div className="w-px bg-border self-stretch" />

                            {/* Overall Progress */}
                            <div>
                                <div className="text-muted-foreground font-body font-medium text-sm leading-5 tracking-[0.5%]">Overall Progress</div>
                                <div className="text-xl font-bold text-foreground">
                                    {grant.overallProgress}%
                                </div>
                            </div>

                            <div className="w-px bg-border self-stretch" />

                            {/* Total Projects */}
                            <div>
                                <div className="text-muted-foreground font-body font-medium text-sm leading-5 tracking-[0.5%]">Total Projects</div>
                                <div className="text-xl font-bold text-foreground">
                                    {grant.totalProjects}
                                </div>
                            </div>
                        </div>
                    </div>
                ))}
            </SectionWrapper>
        </DashboardLayout>
    );
}
