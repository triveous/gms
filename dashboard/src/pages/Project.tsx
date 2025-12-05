import { useParams, useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { ChartContainer, ChartTooltip, ChartTooltipContent } from '@/components/ui/chart';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid } from 'recharts';
import { ArrowLeft, CheckCircle2, AlertCircle, Calendar, CircleCheckBig, BadgeInfo, TrendingUp, TrendingDown, Link } from 'lucide-react';
import DashboardLayout from '@/components/DashboardLayout';
import { ProjectCard } from '@/components/ProjectCard';
import { BudgetUtilizationChart } from '@/components/BudgetUtilizationChart';
import { SectionWrapper } from '@/components/SectionWrapper';

const budgetData = [
    { date: 'Q1 2024', sanctioned: 30, released: 25, actual: 20 },
    { date: 'Q2 2024', sanctioned: 50, released: 42, actual: 35 },
    { date: 'Q3 2024', sanctioned: 70, released: 58, actual: 50 },
    { date: 'Q4 2024', sanctioned: 85, released: 72, actual: 65 },
    { date: 'Q1 2025', sanctioned: 95, released: 85, actual: 78 },
];

const chartConfig = {
    sanctioned: { label: 'Sanctioned', color: '#60A5FA' },
    released: { label: 'Released', color: '#34D399' },
    actual: { label: 'Actual', color: '#F59E0B' },
};

export default function Project() {
    const { id } = useParams();
    const navigate = useNavigate();

    const projectData = {
        name: 'A point of care artificial intelligence (AI) based screening tools for oral cancer',
        department: 'Computer Science',
        leadInstitute: 'IIT Bangalore',
        startDate: '01 Apr 2025',
        endDate: 'Last updated: 10/10/2023',
    };

    const metrics = {
        screeningReadiness: { current: 4, status: 'on-track' },
        projectBenchmarks: { current: 6, status: 'at-risk' },
        commercialization: { current: 4, status: 'on-track' },
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

    const milestones = [
        { quarter: 'Q1 2020-2026', progress: 40, description: 'SG: Make product M Validation Summary' },
        { quarter: 'Q2 2021-2022', progress: 30, description: 'Pilot Study & Clinical Documents' },
        { quarter: 'Q3 2022-2024', progress: 25, description: 'Technology Architecture Degree' },
        { quarter: 'Q4 2024-2025', progress: 10, description: 'Rapid Assay & Testing' },
    ];

    const artifacts = [
        'Study plans to screen lung cong-specific',
        'SG: Make a product M Validation Summary',
        'Technology Scorecard',
        'Rapid Assay & Testing',
        'Strong Evidence-Authored Impact',
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
            <div className="mb-6 flex items-center gap-2">
                <div 
                    
                    className="text-sm text-muted-foreground  flex items-center gap-1"
                >
                    Home <span>›</span>
                </div>
                <div onClick={() => navigate('/grant/1')} className=" cursor-pointer text-sm text-foreground flex items-center gap-1">
                    Projects
                </div>
            </div>

            {/* Page Header */}
            <div className="mb-6">
                <h1 className="text-foreground font-semibold text-[30px] leading-[125%] tracking-[-0.3px] mb-4">
                    {projectData.name}
                </h1>
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

            <SectionWrapper 
                title="TCRM's Metrics" 
                contentClassName="grid grid-cols-4 gap-4"
            >
                {/* Q3 Forecasted */}
                <div className="p-6 bg-card border border-border rounded flex flex-col gap-4">
                    <div className="text-muted-foreground font-medium text-base leading-6">Technology Readiness Level</div>
                    <div className="flex items-center gap-2">
                        <span className="text-2xl font-semibold leading-[120%]  text-foreground">4</span>
                        <span className="flex items-center gap-1 px-2 py-1 rounded-full bg-blue-100 text-blue-700">
                            <TrendingDown className="w-3 h-3" />
                            <span className="text-xs font-medium">+2</span>
                        </span>
                    </div>
                </div>

                {/* Q3 Actual Spend */}
                <div className="p-6 bg-card border border-border rounded flex flex-col gap-4">
                    <div className="text-muted-foreground font-medium text-base leading-6">Market Readiness Level</div>
                    <div className="flex items-center gap-2">
                        <span className="text-2xl font-semibold leading-[120%]  text-foreground">6</span>
                        <span className="flex items-center gap-1 px-2 py-1 rounded-full bg-blue-100 text-blue-700">
                            <TrendingUp className="w-3 h-3" />
                            <span className="text-xs font-medium">-1</span>
                        </span>
                    </div>
                </div>

                {/* Q3 Utilisation % */}
                <div className="p-6 bg-card border border-border rounded flex flex-col gap-4">
                    <div className="text-muted-foreground font-medium text-base leading-6">Commercial Readiness Level</div>
                    <div className="flex items-center gap-2">
                        <span className="text-2xl font-semibold leading-[120%]  text-foreground">4</span>
                        <span className="flex items-center gap-1 px-2 py-1 rounded-full bg-orange-100 text-orange-700">
                            <TrendingUp className="w-3 h-3" />
                            <span className="text-xs font-medium">2%</span>
                        </span>
                    </div>
                </div>

                {/* Current year Utilised */}
                <div className="p-6 bg-card border border-border rounded flex flex-col gap-4">
                    <div className="text-muted-foreground font-medium text-base leading-6">Social Impact Readiness Level</div>
                    <div className="flex items-center gap-2">
                        <span className="text-2xl font-semibold leading-[120%]  text-foreground">4</span>
                        <span className="flex items-center gap-1 px-2 py-1 rounded-full bg-green-100 text-green-700">
                            <TrendingUp className="w-3 h-3" />
                            <span className="text-xs font-medium">+2</span>
                        </span>
                    </div>
                </div>
            </SectionWrapper>

            {/* Key Highlights & Lowlights */}
            <SectionWrapper 
                title="Key Highlights & Lowlights"
                contentClassName="grid flex gap-6 flex-col"
            >
                <div className="grid grid-cols-3 gap-6">
                    {/* Highlights */}
                    <div className="p-6 bg-card flex flex-col gap-4 border border-border rounded text-muted-foreground font-inter text-base font-medium leading-6">
                        <h3>Highlights</h3>
                        <div className="flex flex-col gap-4 text-muted-foreground">
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
                        <div className="flex flex-col gap-4 text-muted-foreground">
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
                </div>
                {/* Progress Artifacts Ask DiyaAI  */}
                <div className="grid grid-cols-3 gap-6">
                    {/* Progress Card */}
                    <div className="p-6 bg-card border border-border rounded">
                        <h3 className="text-base font-semibold mb-1">Progress</h3>
                        <p className="text-sm text-muted-foreground mb-6">Overall Progress achieved quarter-wise</p>
                        
                        <div className="space-y-6">
                            {/* Q2 2025-2026 */}
                            <div>
                                <div className="flex items-center justify-between mb-2">
                                    <span className="text-sm font-medium">Q2- 2025-2026</span>
                                    <span className="text-sm font-semibold">40%</span>
                                </div>
                                <div className="w-full bg-gray-200 rounded-full h-2">
                                    <div className="bg-black h-2 rounded-full" style={{ width: '40%' }} />
                                </div>
                            </div>

                            {/* Q1 2025-2026 */}
                            <div>
                                <div className="flex items-center justify-between mb-2">
                                    <span className="text-sm font-medium">Q1- 2025-2026</span>
                                    <span className="text-sm font-semibold">30%</span>
                                </div>
                                <div className="w-full bg-gray-200 rounded-full h-2">
                                    <div className="bg-black h-2 rounded-full" style={{ width: '30%' }} />
                                </div>
                            </div>

                            {/* Q4 2024-2025 */}
                            <div>
                                <div className="flex items-center justify-between mb-2">
                                    <span className="text-sm font-medium">Q4- 2024-2025</span>
                                    <span className="text-sm font-semibold">20%</span>
                                </div>
                                <div className="w-full bg-gray-200 rounded-full h-2">
                                    <div className="bg-black h-2 rounded-full" style={{ width: '20%' }} />
                                </div>
                            </div>

                            {/* Q3 2024-2025 */}
                            <div>
                                <div className="flex items-center justify-between mb-2">
                                    <span className="text-sm font-medium">Q3- 2024-2025</span>
                                    <span className="text-sm font-semibold">10%</span>
                                </div>
                                <div className="w-full bg-gray-200 rounded-full h-2">
                                    <div className="bg-black h-2 rounded-full" style={{ width: '10%' }} />
                                </div>
                            </div>
                        </div>

                        <Button variant="outline" className="w-full mt-6">
                            View all
                            <svg className="ml-2 w-4 h-4" viewBox="0 0 16 16" fill="none">
                                <path d="M6 12L10 8L6 4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                            </svg>
                        </Button>
                    </div>

                    {/* Artifacts Card */}
                    <div className="p-6 bg-card border border-border rounded">
                        <h3 className="text-base font-semibold mb-1">Artifacts</h3>
                        <p className="text-sm text-muted-foreground mb-6">Quick links to access the projects related doc</p>
                        
                        <div className="space-y-6">
                            <a href="#" className="flex items-center gap-2 text-sm hover:underline">
                                <Link className='h-4 w-4'/>
                                ML Model Accuracy & Validation Summary
                            </a>
                            <a href="#" className="flex items-center gap-2 text-sm hover:underline">
                                <Link className='h-4 w-4'/>
                                User Research Blueprint / Protocol Document
                            </a>
                            <a href="#" className="flex items-center gap-2 text-sm hover:underline">
                                <Link className='h-4 w-4'/>
                                Technology Architecture Diagram
                            </a>
                            <a href="#" className="flex items-center gap-2 text-sm hover:underline">
                                <Link className='h-4 w-4'/>
                                App Usability Testing Results
                            </a>
                            <a href="#" className="flex items-center gap-2 text-sm hover:underline">
                                <Link className='h-4 w-4'/>
                                Pilot Study Report 
                            </a>
                            <a href="#" className="flex items-center gap-2 text-sm hover:underline">
                                <Link className='h-4 w-4'/>
                                Training & Capacity Building Report
                            </a>
                        </div>

                        <Button variant="outline" className="w-full mt-6">
                            View all
                            <svg className="ml-2 w-4 h-4" viewBox="0 0 16 16" fill="none">
                                <path d="M6 12L10 8L6 4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                            </svg>
                        </Button>
                    </div>

                    {/* Ask DiyaAI Card */}
                    <div className="p-6 bg-card border border-border rounded">
                        <h3 className="text-base font-semibold mb-1">Impact & Innovation Outcomes</h3>
                        <p className="text-sm text-muted-foreground mb-6">Real-world beneficiaries and breakthroughs achieved</p>
                        
                        <div className="space-y-4">
                            {/* Impact created */}
                            <div className="p-4 border border-orange-200 rounded-lg bg-orange-50/30">
                                <div className="text-sm text-muted-foreground mb-2">Impact created</div>
                                <div className="flex items-baseline gap-2 mb-2">
                                    <span className="text-3xl font-bold text-foreground">20 Cr.</span>
                                    <span className="text-sm text-muted-foreground">citizens</span>
                                </div>
                                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-green-100 text-green-700">
                                    <TrendingUp className="w-3 h-3" />
                                    <span className="text-xs font-medium">10%</span>
                                </span>
                            </div>

                            {/* AI breakthroughs */}
                            <div className="p-4 border border-orange-200 rounded-lg bg-orange-50/30">
                                <div className="text-sm text-muted-foreground mb-2">AI breakthroughs</div>
                                <div className="flex items-baseline gap-2 mb-2">
                                    <span className="text-3xl font-bold text-foreground">3</span>
                                </div>
                                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-green-100 text-green-700">
                                    <TrendingUp className="w-3 h-3" />
                                    <span className="text-xs font-medium">+1</span>
                                </span>
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
