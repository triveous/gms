import { useParams, useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { ChartContainer, ChartTooltip, ChartTooltipContent } from '@/components/ui/chart';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid } from 'recharts';
import { ArrowLeft, AlertCircle, TrendingUp, TrendingDown, CheckCircle2, ChevronDown, CircleCheckBig, BadgeInfo } from 'lucide-react';
import DashboardLayout from '@/components/DashboardLayout';
import { ProjectCard } from '@/components/ProjectCard';
import { BudgetUtilizationChart } from '@/components/BudgetUtilizationChart';
import { SectionWrapper } from '@/components/SectionWrapper';

const budgetData = [
    { date: 'Q1 2024', sanctioned: 40, released: 30, actual: 25 },
    { date: 'Q2 2024', sanctioned: 60, released: 50, actual: 42 },
    { date: 'Q3 2024', sanctioned: 80, released: 65, actual: 58 },
    { date: 'Q4 2024', sanctioned: 100, released: 82, actual: 75 },
    { date: 'Q1 2025', sanctioned: 110, released: 95, actual: 85 },
];

const chartConfig = {
    sanctioned: { label: 'Sanctioned', color: '#60A5FA' },
    released: { label: 'Released', color: '#34D399' },
    actual: { label: 'Actual', color: '#F59E0B' },
};

export default function Grant() {
    const { id } = useParams();
    const navigate = useNavigate();
    

    const projectData = {
        name: 'A point of care artificial intelligence (AI) based screening tools for oral cancer',
        department: 'Computer Science',
        leadInstitute: 'IIT Bangalore',
        dateOfSanction: '01 Apr 2025',
        endDate: '31 March 2030',
        lastModified: 'Last modified on: 21 Apr 2025',
    };

    const metrics = {
        screeningReadiness: { current: 4, status: 'on-track' },
        projectBenchmarks: { current: 6, status: 'at-risk' },
        overallProgress: { current: 4, status: 'on-track' },
        securityCompliance: { current: 4, status: 'on-track' },
    };

    const highlights = [
        'Medical updates and advancements: Digital pathology services are increasing pathology capacity by early detection of the Oral Lesion',
        'Developed a handheld device (VeloScope) which is the World leading device to produce rapid, real-time results for DM-PCR in under 30 mins.',
    ];

    const lowlights = [
        'Hardware and Software compatibility: We were facing the issue of Low Oral Lesion images Data Transfer in some of the district hospital.',
        'Discussed about the product development regarding lack of data: From COVID Screening to India\'s Health Ecosystem.',
    ];

    const projects = [
        {
            id: '1',
            title: 'A point of care artificial intelligence (AI) based screening tools for oral cancer',
            projectLead: 'IISc Bangalore',
            activeSince: '12 years',
            lastUpdated: '12/10/2025',
            metrics: {
                tbl: { value: 4, change: '+2', isPositive: true },
                mrl: { value: 6, change: '-1', isPositive: false },
                crl: { value: 4, change: '+2', isPositive: true },
                sirl: { value: 4, change: '+2', isPositive: true },
            },
            budgetSpent: '₹ 92 Cr.',
            progress: '40%',
        },
        {
            id: '2',
            title: 'Consortium for AI and Remote Digital Interventions Against Cardiovascular disease in India',
            projectLead: 'JIPMER Puducherry',
            activeSince: '6 months',
            lastUpdated: '12/10/2025',
            metrics: {
                tbl: { value: 4, change: '+2', isPositive: true },
                mrl: { value: 6, change: '-1', isPositive: false },
                crl: { value: 4, change: '+2', isPositive: true },
                sirl: { value: 4, change: '+2', isPositive: true },
            },
            budgetSpent: '₹ 92 Cr.',
            progress: '40%',
        },
    ];

    return (
        <DashboardLayout>
            {/* Breadcrumb */}
            <div className="mb-6">
                <button 
                    onClick={() => navigate('/grants')}
                    className="text-sm text-muted-foreground hover:text-foreground flex items-center gap-1"
                >
                    Home <span>›</span>
                </button>
            </div>

            {/* Page Header */}
            <div className="mb-6">
                <h1 className="text-foreground font-semibold text-[30px] leading-[125%] tracking-[-0.3px] mb-4">
                    {projectData.name}
                </h1>
                
                {/* Metadata Row */}
                <div className="flex flex-wrap items-center gap-2">
                    <Badge variant="secondary" className="text-muted-foreground text-center font-medium text-sm leading-[150%] tracking-[0.07px] rounded-lg border border-[#E2E8F0]">
                        Alias: AICOE Health & AI
                    </Badge>
                    <Badge variant="secondary" className="text-muted-foreground text-center font-medium text-sm leading-[150%] tracking-[0.07px] rounded-lg border border-[#E2E8F0]">
                        Lead Institute: {projectData.leadInstitute}
                    </Badge>
                    <Badge variant="secondary" className="text-muted-foreground text-center font-medium text-sm leading-[150%] tracking-[0.07px] rounded-lg border border-[#E2E8F0]">
                        Timeline: 4 year (April 2020 - 31 March 2024)
                    </Badge>
                    <Badge variant="secondary" className="text-muted-foreground text-center font-medium text-sm leading-[150%] tracking-[0.07px] rounded-lg border border-[#E2E8F0]">
                        Approval Number: AICOE/2020/Health011
                    </Badge>
                </div>
            </div>

            {/* Metrics Cards */}
            <div className="flex gap-4 mb-6">
                {/* Total Budget */}
                <div className="flex flex-col gap-3">
                    <div className="text-muted-foreground font-medium text-base leading-[150%]">Total Budget</div>
                    <div className="text-foreground font-semibold text-xl leading-[120%] tracking-[-0.4px]">₹ 300 Cr.</div>
                </div>

                <div className="w-px bg-border self-stretch" />

                {/* Total Budget Spend */}
                <div className="flex flex-col gap-3">
                    <div className="text-muted-foreground font-medium text-base leading-[150%]">Total Budget Spend</div>
                    <div className="flex items-center gap-2">
                        <div className="text-foreground font-semibold text-xl leading-[120%] tracking-[-0.4px]">₹ 120 Cr.</div>
                        <Badge className="bg-green-100 text-foreground font-mono text-xs font-normal leading-[150%]">
                            40%
                        </Badge>
                    </div>
                </div>

                <div className="w-px bg-border self-stretch" />

                {/* Overall Progress */}
                <div className="flex flex-col gap-3">
                    <div className="text-muted-foreground font-medium text-base leading-[150%]">Overall Progress</div>
                    <div className="text-foreground font-semibold text-xl leading-[120%] tracking-[-0.4px]">40%</div>
                </div>
            </div>

            {/* Separator */}
            <div className="h-px bg-border mb-6" />

            {/* Controls Row */}
            <div className="sticky top-17 z-40 bg-background pb-3 flex items-center justify-between mb-3">
                <div className="flex items-center gap-4">
                    <Select defaultValue="q2">
                        <SelectTrigger className="bg-card h-10">
                            <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                            <SelectItem value="q2">
                                <span className="text-foreground">Q2 Jul-Sep 2025</span>
                                {" "}
                                <span className="text-muted-foreground/60 font-sans text-sm font-normal leading-[21px] tracking-[0.07px]">(Recent Quarter)</span>
                            </SelectItem>
                        </SelectContent>
                    </Select>
                    
                    <Select defaultValue="q1">
                        <SelectTrigger className="h-10 bg-card">
                            <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                            <SelectItem value="q1">
                                <span className="text-foreground"><span className="text-muted-foreground/60 font-sans text-sm font-normal leading-[21px] tracking-[0.07px]">Compare to</span> Q1 | Apr-Jun 2025</span>
                            </SelectItem>
                        </SelectContent>
                    </Select>
                </div>
                <Select>
                    <SelectTrigger className="h-10 bg-card text-foreground">
                        <div className="flex items-center gap-2">
                            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                                <path d="M14 10v2.667A1.333 1.333 0 0112.667 14H3.333A1.333 1.333 0 012 12.667V10m2.667-4L8 9.333m0 0L11.333 6M8 9.333V2" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                            </svg>
                            <SelectValue placeholder="Download Reports" />
                        </div>
                    </SelectTrigger>
                    <SelectContent>
                        <SelectItem value="pdf">Download as PDF</SelectItem>
                        <SelectItem value="excel">Download as Excel</SelectItem>
                        <SelectItem value="csv">Download as CSV</SelectItem>
                    </SelectContent>
                </Select>
            </div>

            {/* Projects Section */}
            <SectionWrapper 
                title="Projects"
                className="mt-8"
                contentClassName="space-y-4"
            >
                {projects.map((project) => (
                    <ProjectCard
                        key={project.id}
                        title={project.title}
                        projectLead={project.projectLead}
                        activeSince={project.activeSince}
                        lastUpdated={project.lastUpdated}
                        metrics={project.metrics}
                        budgetSpent={project.budgetSpent}
                        progress={project.progress}
                    />
                ))}
            </SectionWrapper>

            {/* Key Highlights & Lowlights */}
            <SectionWrapper 
                title="Key Highlights & Lowlights"
                contentClassName="grid grid-cols-3 gap-6"
            >
                {/* Highlights */}
                <div className="p-6 bg-card flex flex-col gap-4 border border-border rounded text-muted-foreground font-inter text-base font-medium leading-6">
                    <h3>Highlights</h3>
                    <div className="flex flex-col gap-4 text-card-foreground">
                        <div className="flex gap-2 items-start">
                            <CircleCheckBig className="w-5 h-5 shrink-0 mt-0.5" />
                            <p>
                                Received positive and encouraging reviews from Technology Advisors on the System Design
                            </p>
                        </div>
                        <div className="flex gap-2 items-start">
                            <CircleCheckBig className="w-5 h-5 shrink-0 mt-0.5" />
                            <p>
                                Submitting a blue print for doing a user research / review studies at scale in India
                            </p>
                        </div>
                    </div>
                </div>

                {/* Lowlights */}
                <div className="p-6 bg-card flex flex-col gap-4 border border-border rounded text-muted-foreground font-inter text-base font-medium leading-6">
                    <h3>Lowlights</h3>
                    <div className="flex flex-col gap-4 text-card-foreground">
                        <div className="flex gap-2 items-start">
                            <BadgeInfo className="w-5 h-5 shrink-0 mt-0.5" />
                            <p>
                                Hardware and Software compatibility has been tuning out to be the major design revision factor than we anticipated. We are going ahead with the largest API/SDK distribution as per Android Developer's distribution page
                            </p>
                        </div>
                    </div>
                </div>

                {/* Outcome Indicator */}
                <div className="flex flex-col gap-4">
                    {/* Outcome Indicator */}
                    <div className='h-[117px] p-6 bg-card border border-border rounded'>
                        <div className="text-sm text-muted-foreground mb-3">Outcome Indicator</div>
                        <div className="flex items-center gap-2">
                            <span className="text-2xl font-semibold text-foreground">Good</span>
                            <div className="w-6 h-6 rounded-md bg-green-500 flex items-center justify-center">
                                <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                                    <path d="M11.667 3.5L5.25 9.917L2.333 7" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                                </svg>
                            </div>
                        </div>
                    </div>

                    {/* Impact Indicator */}
                    <div className='h-[117px] p-6 bg-card border border-border rounded'>
                        <div className="text-sm text-muted-foreground mb-3">Impact Indicator</div>
                        <div className="flex items-center gap-2">
                            <span className="text-2xl font-semibold text-foreground">Good</span>
                            <div className="w-6 h-6 rounded-md bg-green-500 flex items-center justify-center">
                                <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                                    <path d="M11.667 3.5L5.25 9.917L2.333 7" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                                </svg>
                            </div>
                        </div>
                    </div>
                </div>
            </SectionWrapper>

            {/* Budget Utilisation */}
            <SectionWrapper 
                title="Budget Utilisation"
                contentClassName="flex flex-col gap-6"
            >
                <div className="p-6 bg-card border border-border rounded">
                    <BudgetUtilizationChart />
                </div>
                {/* Metrics Grid */}
                <div className="grid grid-cols-4 gap-4">
                    {/* Q3 Forecasted */}
                    <div className="p-6 bg-card border border-border rounded flex flex-col gap-3">
                        <div className="text-sm text-muted-foreground">Q3 Forecasted</div>
                        <div className="flex items-center gap-2">
                            <span className="text-2xl font-semibold leading-[120%]  text-foreground">₹ 80 Cr.</span>
                            <span className="flex items-center gap-1 px-2 py-1 rounded-xl bg-input ">
                                <TrendingDown className="w-3 h-3" />
                                <span className="text-xs font-medium">12%</span>
                            </span>
                        </div>
                    </div>

                    {/* Q3 Actual Spend */}
                    <div className="p-6 bg-card border border-border rounded flex flex-col gap-3">
                        <div className="text-sm text-muted-foreground">Q3 Actual Spend</div>
                        <div className="flex items-center gap-2">
                            <span className="text-2xl font-semibold leading-[120%]  text-foreground">₹ 92 Cr.</span>
                            <span className="flex items-center gap-1 px-2 py-1 rounded-full bg-input ">
                                <TrendingUp className="w-3 h-3" />
                                <span className="text-xs font-medium">12%</span>
                            </span>
                        </div>
                    </div>

                    {/* Q3 Utilisation % */}
                    <div className="p-6 bg-card border border-border rounded flex flex-col gap-3">
                        <div className="text-sm text-muted-foreground">Q3 Utilisation %</div>
                        <div className="flex items-center gap-2">
                            <span className="text-2xl font-semibold leading-[120%]  text-foreground">120%</span>
                            <span className="flex items-center gap-1 px-2 py-1 rounded-full bg-orange-100 text-orange-700">
                                <TrendingUp className="w-3 h-3" />
                                <span className="text-xs font-medium">2%</span>
                            </span>
                        </div>
                    </div>

                    {/* Current year Utilised */}
                    <div className="p-6 bg-card border border-border rounded flex flex-col gap-3">
                        <div className="text-sm text-muted-foreground">Current year Utilised</div>
                        <div className="flex items-center gap-2">
                            <span className="text-2xl font-semibold leading-[120%]  text-foreground">78 %</span>
                            <span className="flex items-center gap-1 px-2 py-1 rounded-full bg-green-100 text-green-700">
                                <TrendingUp className="w-3 h-3" />
                                <span className="text-xs font-medium">+18%</span>
                            </span>
                        </div>
                    </div>
                </div>
            </SectionWrapper>
        </DashboardLayout>
    );
}
