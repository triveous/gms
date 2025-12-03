import { useParams, useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ChartContainer, ChartTooltip, ChartTooltipContent } from '@/components/ui/chart';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid } from 'recharts';
import { ArrowLeft, AlertCircle, TrendingUp, CheckCircle2 } from 'lucide-react';

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

    return (
        <div className="min-h-screen bg-linear-to-br from-blue-50 via-white to-blue-50">
            <div className="max-w-7xl mx-auto p-6 md:p-8">
                {/* Back Button */}
                <Button
                    variant="ghost"
                    className="mb-4 text-blue-600 hover:text-blue-700"
                    onClick={() => navigate('/grants')}
                >
                    <ArrowLeft className="h-4 w-4 mr-2" />
                    Back to Grants
                </Button>

                {/* Header */}
                <div className="mb-8">
                    <div className="flex items-start justify-between mb-4">
                        <div className="flex-1">
                            <Badge className="mb-3 bg-blue-100 text-blue-700 border-0">
                                ❖ AI-CoE
                            </Badge>
                            <h1 className="text-3xl font-bold text-gray-900 mb-3">
                                CPMU Dashboard
                            </h1>
                            <h2 className="text-xl text-gray-700 mb-2">
                                {projectData.name}
                            </h2>
                            <div className="flex flex-wrap gap-4 text-sm text-gray-600">
                                <span><span className="font-medium">Department:</span> {projectData.department}</span>
                                <span>•</span>
                                <span><span className="font-medium">Lead Institute:</span> {projectData.leadInstitute}</span>
                                <span>•</span>
                                <span><span className="font-medium">Date of sanction:</span> {projectData.dateOfSanction}</span>
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
                    <p className="text-sm text-gray-500">{projectData.lastModified}</p>
                </div>

                {/* TODAY'S METRICS */}
                <div className="mb-8">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">TODAY'S Metrics</h3>
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
                                <p className="text-sm text-gray-600 mb-1">Commercialization Readiness level</p>
                                <div className="flex items-baseline gap-2">
                                    <p className="text-3xl font-bold">{metrics.overallProgress.current}</p>
                                    <Badge variant="secondary" className="bg-green-100 text-green-700 border-0">
                                        on track
                                    </Badge>
                                </div>
                            </CardContent>
                        </Card>

                        <Card className="border-l-4 border-l-green-500">
                            <CardContent className="pt-6">
                                <p className="text-sm text-gray-600 mb-1">Security/Compliance Readiness Level</p>
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
                    {/* Highlights */}
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

                    {/* Lowlights */}
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

                {/* BUDGET UTILIZATION */}
                <Card className="mb-8">
                    <CardHeader>
                        <CardTitle className="flex items-center justify-between">
                            <span>Budget Utilization</span>
                            <div className="flex gap-6 text-sm font-normal">
                                <div className="flex items-center gap-2">
                                    <div className="h-3 w-3 bg-blue-400 rounded"></div>
                                    <span>Sanctioned</span>
                                    <span className="font-semibold">₹ 212 Cr</span>
                                </div>
                                <div className="flex items-center gap-2">
                                    <div className="h-3 w-3 bg-green-400 rounded"></div>
                                    <span>Released</span>
                                    <span className="font-semibold">₹ 160 Cr</span>
                                </div>
                                <div className="flex items-center gap-2">
                                    <div className="h-3 w-3 bg-orange-400 rounded"></div>
                                    <span>Actual</span>
                                    <span className="font-semibold">₹ 140 Cr</span>
                                </div>
                            </div>
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <ChartContainer config={chartConfig} className="h-[300px]">
                            <AreaChart data={budgetData}>
                                <defs>
                                    <linearGradient id="sanctioned" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#60A5FA" stopOpacity={0.3} />
                                        <stop offset="95%" stopColor="#60A5FA" stopOpacity={0} />
                                    </linearGradient>
                                    <linearGradient id="released" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#34D399" stopOpacity={0.3} />
                                        <stop offset="95%" stopColor="#34D399" stopOpacity={0} />
                                    </linearGradient>
                                    <linearGradient id="actual" x1="0" y1="0" x2="0" y2="1">
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
                                    fill="url(#sanctioned)"
                                    strokeWidth={2}
                                />
                                <Area
                                    type="monotone"
                                    dataKey="released"
                                    stroke="#34D399"
                                    fill="url(#released)"
                                    strokeWidth={2}
                                />
                                <Area
                                    type="monotone"
                                    dataKey="actual"
                                    stroke="#F59E0B"
                                    fill="url(#actual)"
                                    strokeWidth={2}
                                />
                            </AreaChart>
                        </ChartContainer>

                        {/* Summary Stats */}
                        <div className="grid grid-cols-3 gap-6 mt-6 pt-6 border-t">
                            <div>
                                <p className="text-sm text-gray-500 mb-1">O3 Fund Utilization</p>
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

                        {/* Additional Stats */}
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
                                <Button variant="link" className="text-blue-600">
                                    See all →
                                </Button>
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="space-y-4">
                                <div>
                                    <p className="text-sm font-semibold mb-2">Academic & Industry Partners</p>
                                    <div className="space-y-2">
                                        <div className="text-sm">
                                            <p className="font-medium">Indian Institute of Science (IISc)</p>
                                            <p className="text-gray-600">Lead institution in AI research</p>
                                        </div>
                                        <div className="text-sm">
                                            <p className="font-medium">Manipal Hospital</p>
                                            <p className="text-gray-600">Partner institution for clinical trials</p>
                                        </div>
                                    </div>
                                </div>
                                <div className="border-t pt-4">
                                    <p className="text-sm font-semibold mb-2">MeitY/AI / TSC</p>
                                    <div className="text-sm">
                                        <p className="font-medium">NITI Aayog</p>
                                        <p className="text-gray-600">Policy and technical support</p>
                                    </div>
                                </div>
                            </div>
                        </CardContent>
                    </Card>

                    <Card>
                        <CardHeader>
                            <CardTitle className="text-lg flex items-center justify-between">
                                Lead Investigators and Partners
                                <span className="text-sm font-normal text-gray-500">See 12</span>
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="space-y-3">
                                <div>
                                    <p className="text-sm font-semibold mb-2">Principal Investigator</p>
                                    <div className="text-sm space-y-1">
                                        <p className="font-medium">Dr. Ram Krishna Singh</p>
                                        <p className="text-gray-600">Professor, Dept. of Computer Science and Engg</p>
                                    </div>
                                </div>
                                <div>
                                    <p className="text-sm font-semibold mb-2">Publication list</p>
                                    <div className="text-sm space-y-1">
                                        <p className="text-blue-600 cursor-pointer hover:underline">
                                            Dr Krishna and 3 others reviewed results related to latest test results
                                        </p>
                                    </div>
                                </div>
                                <div>
                                    <p className="text-sm font-semibold mb-2">Deliverables list</p>
                                    <div className="text-sm space-y-1">
                                        <p className="text-gray-600">Next milestones: Q4 project delivery milestone tracking</p>
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
