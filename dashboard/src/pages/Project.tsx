import { useParams, useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ChartContainer, ChartTooltip, ChartTooltipContent } from '@/components/ui/chart';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid } from 'recharts';
import { ArrowLeft, CheckCircle2, AlertCircle, Calendar } from 'lucide-react';

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

    return (
        <div className="min-h-screen bg-linear-to-br from-blue-50 via-white to-blue-50">
            <div className="max-w-7xl mx-auto p-6 md:p-8">
                {/* Back Button */}
                <Button
                    variant="ghost"
                    className="mb-4 text-blue-600 hover:text-blue-700"
                    onClick={() => navigate(`/grant/${id}`)}
                >
                    <ArrowLeft className="h-4 w-4 mr-2" />
                    Back to Grant
                </Button>

                {/* Header */}
                <div className="mb-8">
                    <div className="flex items-start justify-between mb-4">
                        <div className="flex-1">
                            <Badge className="mb-3 bg-blue-100 text-blue-700 border-0">
                                ❖ AI-CoE
                            </Badge>
                            <h1 className="text-3xl font-bold text-gray-900 mb-3">
                                CPMU Project dashboard
                            </h1>
                            <h2 className="text-xl text-gray-700 mb-2">
                                {projectData.name}
                            </h2>
                            <div className="flex flex-wrap gap-4 text-sm text-gray-600">
                                <span><span className="font-medium">Department:</span> {projectData.department}</span>
                                <span>•</span>
                                <span><span className="font-medium">Lead Institute:</span> {projectData.leadInstitute}</span>
                                <span>•</span>
                                <span><span className="font-medium">Start Date:</span> {projectData.startDate}</span>
                            </div>
                        </div>
                        <div className="flex gap-2">
                            <Button variant="outline">
                                ⚙ Filter
                            </Button>
                            <Button className="bg-blue-600 hover:bg-blue-700 text-white">
                                ↗ Export
                            </Button>
                        </div>
                    </div>
                    <p className="text-sm text-gray-500">{projectData.endDate}</p>
                </div>

                {/* TODAY'S METRICS */}
                <div className="mb-8">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">TODAY'S Metrics (Q3 2025)</h3>
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                        <Card className="border-l-4 border-l-green-500">
                            <CardContent className="pt-6">
                                <p className="text-sm text-gray-600 mb-1">Screening Readiness Level</p>
                                <div className="flex items-baseline gap-2">
                                    <p className="text-3xl font-bold">{metrics.screeningReadiness.current}</p>
                                    <Badge variant="secondary" className="bg-green-100 text-green-700 border-0">
                                        on track
                                    </Badge>
                                </div>
                            </CardContent>
                        </Card>

                        <Card className="border-l-4 border-l-orange-500">
                            <CardContent className="pt-6">
                                <p className="text-sm text-gray-600 mb-1">Project Benchmarks Level</p>
                                <div className="flex items-baseline gap-2">
                                    <p className="text-3xl font-bold">{metrics.projectBenchmarks.current}</p>
                                    <Badge variant="secondary" className="bg-orange-100 text-orange-700 border-0">
                                        at risk
                                    </Badge>
                                </div>
                            </CardContent>
                        </Card>

                        <Card className="border-l-4 border-l-green-500">
                            <CardContent className="pt-6">
                                <p className="text-sm text-gray-600 mb-1">Commercialization Readiness</p>
                                <div className="flex items-baseline gap-2">
                                    <p className="text-3xl font-bold">{metrics.commercialization.current}</p>
                                    <Badge variant="secondary" className="bg-green-100 text-green-700 border-0">
                                        on track
                                    </Badge>
                                </div>
                            </CardContent>
                        </Card>

                        <Card className="border-l-4 border-l-green-500">
                            <CardContent className="pt-6">
                                <p className="text-sm text-gray-600 mb-1">Security/Compliance Readiness</p>
                                <div className="flex items-baseline gap-2">
                                    <p className="text-3xl font-bold">{metrics.securityCompliance.current}</p>
                                    <Badge variant="secondary" className="bg-green-100 text-green-700 border-0">
                                        on track
                                    </Badge>
                                </div>
                            </CardContent>
                        </Card>
                    </div>
                </div>

                {/* KEY HIGHLIGHTS & LOWLIGHTS */}
                <div className="grid md:grid-cols-2 gap-6 mb-8">
                    <Card>
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2 text-lg">
                                <CheckCircle2 className="h-5 w-5 text-green-600" />
                                Key Highlights & Lowlights (Q3 2025)
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="space-y-4">
                                <div>
                                    <p className="text-sm font-semibold text-gray-700 mb-2">Highlights</p>
                                    {highlights.map((highlight, index) => (
                                        <div key={index} className="flex gap-2 mb-3">
                                            <Badge variant="secondary" className="bg-green-100 text-green-700 border-0 shrink-0">
                                                Good
                                            </Badge>
                                            <p className="text-sm text-gray-600">{highlight}</p>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </CardContent>
                    </Card>

                    <Card>
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2 text-lg">
                                <AlertCircle className="h-5 w-5 text-orange-600" />
                                Observed Behavior
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="space-y-4">
                                <div>
                                    <p className="text-sm font-semibold text-gray-700 mb-2">Lowlights</p>
                                    {lowlights.map((lowlight, index) => (
                                        <div key={index} className="flex gap-2 mb-3">
                                            <Badge variant="secondary" className="bg-green-100 text-green-700 border-0 shrink-0">
                                                Good
                                            </Badge>
                                            <p className="text-sm text-gray-600">{lowlight}</p>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                </div>

                {/* PROGRESS SECTION */}
                <div className="grid md:grid-cols-2 gap-6 mb-8">
                    {/* Progress & Milestones */}
                    <Card>
                        <CardHeader>
                            <CardTitle className="text-lg flex items-center justify-between">
                                <span>Progress</span>
                                <Button variant="link" className="text-blue-600 text-sm">
                                    View all →
                                </Button>
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="space-y-4">
                                {milestones.map((milestone, index) => (
                                    <div key={index} className="space-y-2">
                                        <div className="flex items-center justify-between text-sm">
                                            <div className="flex items-center gap-2">
                                                <Calendar className="h-4 w-4 text-gray-400" />
                                                <span className="font-medium">{milestone.quarter}</span>
                                            </div>
                                            <span className="text-gray-600">{milestone.progress}%</span>
                                        </div>
                                        <div className="w-full bg-gray-200 rounded-full h-2">
                                            <div
                                                className="bg-blue-600 h-2 rounded-full"
                                                style={{ width: `${milestone.progress}%` }}
                                            />
                                        </div>
                                        <p className="text-xs text-gray-600">{milestone.description}</p>
                                    </div>
                                ))}
                            </div>
                        </CardContent>
                    </Card>

                    {/* Artifacts */}
                    <Card>
                        <CardHeader>
                            <CardTitle className="text-lg flex items-center justify-between">
                                <span>Artifacts</span>
                                <Button variant="link" className="text-blue-600 text-sm">
                                    View all →
                                </Button>
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="space-y-2">
                                {artifacts.map((artifact, index) => (
                                    <div key={index} className="flex items-center gap-2 p-2 hover:bg-gray-50 rounded">
                                        <div className="h-8 w-8 bg-blue-100 rounded flex items-center justify-center text-blue-600">
                                            📄
                                        </div>
                                        <p className="text-sm text-gray-700">{artifact}</p>
                                    </div>
                                ))}
                            </div>
                        </CardContent>
                    </Card>
                </div>

                {/* BUDGET UTILIZATION */}
                <Card className="mb-8">
                    <CardHeader>
                        <CardTitle className="flex items-center justify-between">
                            <span>Budget Utilization</span>
                            <div className="flex gap-6 text-sm font-normal">
                                <div className="flex items-center gap-2">
                                    <div className="h-3 w-3 bg-blue-400 rounded"></div>
                                    <span>Sanctioned</span>
                                    <span className="font-semibold">₹ 40 Cr</span>
                                </div>
                                <div className="flex items-center gap-2">
                                    <div className="h-3 w-3 bg-green-400 rounded"></div>
                                    <span>Released</span>
                                    <span className="font-semibold">₹ 32 Cr</span>
                                </div>
                                <div className="flex items-center gap-2">
                                    <div className="h-3 w-3 bg-orange-400 rounded"></div>
                                    <span>Actual</span>
                                    <span className="font-semibold">₹ 28 Cr</span>
                                </div>
                            </div>
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <ChartContainer config={chartConfig} className="h-[300px]">
                            <AreaChart data={budgetData}>
                                <defs>
                                    <linearGradient id="sanctioned-project" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#60A5FA" stopOpacity={0.3} />
                                        <stop offset="95%" stopColor="#60A5FA" stopOpacity={0} />
                                    </linearGradient>
                                    <linearGradient id="released-project" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#34D399" stopOpacity={0.3} />
                                        <stop offset="95%" stopColor="#34D399" stopOpacity={0} />
                                    </linearGradient>
                                    <linearGradient id="actual-project" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#F59E0B" stopOpacity={0.3} />
                                        <stop offset="95%" stopColor="#F59E0B" stopOpacity={0} />
                                    </linearGradient>
                                </defs>
                                <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                                <XAxis dataKey="date" />
                                <YAxis />
                                <ChartTooltip content={<ChartTooltipContent />} />
                                <Area
                                    type="monotone"
                                    dataKey="sanctioned"
                                    stroke="#60A5FA"
                                    fill="url(#sanctioned-project)"
                                    strokeWidth={2}
                                />
                                <Area
                                    type="monotone"
                                    dataKey="released"
                                    stroke="#34D399"
                                    fill="url(#released-project)"
                                    strokeWidth={2}
                                />
                                <Area
                                    type="monotone"
                                    dataKey="actual"
                                    stroke="#F59E0B"
                                    fill="url(#actual-project)"
                                    strokeWidth={2}
                                />
                            </AreaChart>
                        </ChartContainer>

                        {/* Summary Stats */}
                        <div className="grid grid-cols-3 gap-6 mt-6 pt-6 border-t">
                            <div>
                                <p className="text-sm text-gray-500 mb-1">Q3 Fund Utilization</p>
                                <div className="flex items-baseline gap-2">
                                    <p className="text-2xl font-bold">₹ 40 Cr</p>
                                    <Badge variant="secondary" className="bg-green-100 text-green-700 border-0">
                                        24% up
                                    </Badge>
                                </div>
                            </div>
                            <div>
                                <p className="text-sm text-gray-500 mb-1">Q4 EC Fund Utilization</p>
                                <div className="flex items-baseline gap-2">
                                    <p className="text-2xl font-bold">₹ 44 Cr</p>
                                    <Badge variant="secondary" className="bg-green-100 text-green-700 border-0">
                                        24% up
                                    </Badge>
                                </div>
                            </div>
                            <div>
                                <p className="text-sm text-gray-500 mb-1">Q1 Fund Utilization</p>
                                <div className="flex items-baseline gap-2">
                                    <p className="text-2xl font-bold">120%</p>
                                    <Badge variant="secondary" className="bg-orange-100 text-orange-700 border-0">
                                        23% up
                                    </Badge>
                                </div>
                            </div>
                        </div>

                        <div className="grid grid-cols-3 gap-6 mt-4">
                            <div>
                                <p className="text-sm text-gray-500 mb-1">Current year Utilized</p>
                                <div className="flex items-baseline gap-2">
                                    <p className="text-2xl font-bold">78%</p>
                                    <Badge variant="secondary" className="bg-green-100 text-green-700 border-0">
                                        9% up
                                    </Badge>
                                </div>
                            </div>
                        </div>
                    </CardContent>
                </Card>

                {/* PEOPLE & PARTNERS */}
                <div className="grid md:grid-cols-2 gap-6">
                    <Card>
                        <CardHeader>
                            <CardTitle className="text-lg flex items-center justify-between">
                                People & Partners
                                <Button variant="link" className="text-blue-600 text-sm">
                                    See all →
                                </Button>
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="space-y-4">
                                <div>
                                    <p className="text-sm font-semibold mb-2">Academic & Industry Partners</p>
                                    <div className="space-y-2 text-sm">
                                        <div>
                                            <p className="font-medium">Indian Institute of Science (IISc)</p>
                                            <p className="text-gray-600">Lead institution in AI research</p>
                                        </div>
                                        <div>
                                            <p className="font-medium">Tata Memorial Hospital</p>
                                            <p className="text-gray-600">Partner institution</p>
                                        </div>
                                    </div>
                                </div>
                                <div className="border-t pt-4">
                                    <p className="text-sm font-semibold mb-2">Stakeholders</p>
                                    <div className="text-sm">
                                        <p className="font-medium">Ministry of Health</p>
                                        <p className="text-gray-600">Regulatory support and guidelines</p>
                                    </div>
                                </div>
                            </div>
                        </CardContent>
                    </Card>

                    <Card>
                        <CardHeader>
                            <CardTitle className="text-lg flex items-center justify-between">
                                Lead Investigators and Partners
                                <span className="text-sm font-normal text-gray-500">See 8</span>
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="space-y-3">
                                <div>
                                    <p className="text-sm font-semibold mb-2">Principal Investigator</p>
                                    <div className="text-sm space-y-1">
                                        <p className="font-medium">Dr. Rajesh Kumar</p>
                                        <p className="text-gray-600">Associate Professor, Medical Informatics</p>
                                    </div>
                                </div>
                                <div>
                                    <p className="text-sm font-semibold mb-2">Publication list</p>
                                    <div className="text-sm">
                                        <p className="text-blue-600 cursor-pointer hover:underline">
                                            Dr Kumar and 2 others published new findings on AI-based detection
                                        </p>
                                    </div>
                                </div>
                                <div>
                                    <p className="text-sm font-semibold mb-2">Deliverables list</p>
                                    <div className="text-sm">
                                        <p className="text-gray-600">
                                            Next deliverables: Prototype testing and clinical validation (Q4 2025)
                                        </p>
                                    </div>
                                </div>
                                <div>
                                    <p className="text-sm font-semibold mb-2">Research Brief</p>
                                    <div className="text-sm">
                                        <p className="text-gray-600">
                                            Current research focuses on machine learning algorithms for improved detection accuracy
                                        </p>
                                    </div>
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                </div>
            </div>
        </div>
    );
}
