import { useParams } from 'react-router-dom';
import { useFrappeGetCall, useFrappePostCall } from 'frappe-react-sdk';
import { useEffect, useMemo, useState } from 'react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { CircleCheckBig, BadgeInfo, Link } from 'lucide-react';
import DashboardLayout from '@/components/DashboardLayout';
import { AppBreadcrumb } from '@/components/AppBreadcrumb';
import { BudgetUtilizationChart } from '@/components/BudgetUtilizationChart';
import { SectionWrapper } from '@/components/SectionWrapper';
import DashbaordFilterComponent from '@/components/DashbaordFilterComponent';
import OrgMembers, { type Partner, type Contributor } from '@/components/OrgMembers';
import DialogButton from '@/components/DialogButton';
import NotFound from '@/pages/NotFound';
import { formatIndianAmount } from '@/utils/formatters';
import { TrendingBadge } from '@/components/TrendingBadge';
import { formatTextWithNumber } from '@/utils/textFormatters';

interface BudgetUtilizationItem {
    quarter: string;
    title: string;
    quarterStartDate: string;
    budgetSpent: number;
    forecastedAmount: number;
}

interface MilestoneMetrics {
    'Social Impact Readiness Level'?: number;
    'Market Readiness Level'?: number;
    'Key activities performed'?: string;
    'Grantee Comment'?: string;
    'Milestones achieved'?: string;
    'Impact Created'?: string;
    'Low lights'?: string[];
    'Overall Progress'?: number;
    'Nodal Agency Comment'?: string;
    'Commercial Readiness Level'?: number;
    'Technology Readiness Level'?: number;
    'High lights'?: string[];
    'Budget Spent'?: string | number;
    'AI Breakthroughs': number;
}

interface Artifact {
    parent: string;
    title: string;
    link: string;
}

interface Milestone {
    name: string;
    milestone_title: string;
    period_start: string;
    last_updated: string;
    forecasted_amount: string;
    metrics: MilestoneMetrics;
    partners_and_team_members?: { partner?: Partner; contributor?: Contributor }[];
    artifacts?: Artifact[];
}

interface ProjectMilestoneData {
    name: string;
    title: string;
    alias: string;
    start_date: string;
    end_date: string | null;
    lead_organization: string;
    milestone: Milestone;
}

interface QuarterItem {
    value: string;
    title: string;
    description: string | null;
}

interface QuarterGroup {
    label: string;
    items: QuarterItem[];
}

interface QuarterWiseProgress {
    quarter: string;
    overall_progress: number;
}

interface ProjectDetails {
    name: string;
    title: string;
    alias: string;
    start_date: string;
    end_date: string | null;
    lead_organization: string;
    last_updated: string;
    quartersList: QuarterGroup[];
    budget_utilization: BudgetUtilizationItem[];
    quarterWiseOverallProgress: QuarterWiseProgress[];
}


export default function Project() {
    const { grantId, projectId } = useParams<{ grantId: string; projectId: string }>();
    const [projectData, setProjectData] = useState<ProjectDetails | null>(null);
    const [projectMilestoneData, setProjectMilestoneData] = useState<ProjectMilestoneData | null>(null);
    const [selectedPeriod, setSelectedPeriod] = useState<string>('');
    const [comparisonQuarter, setComparisonQuarter] = useState<string>('');
    const [overallYearUtilization, setOverallUtilization] = useState(0);
    const { data: projectResponse, error: projectError, isLoading: isLoadingProject } = useFrappeGetCall<{ message: { project: ProjectDetails } }>('gms.api.project.get_project_details', {
        project_id: projectId
    });

    // Helper to find latest quarter for year
    const findLatestQuarter = (period: string) => {
        if (!period || period.startsWith('Q')) return period;

        // It's a year value, find the corresponding group
        if (projectData?.quartersList) {
            const yearlyGroup = projectData.quartersList.find((g: any) => g.label === "Yearly Wise");
            const yearItem = yearlyGroup?.items.find((i: any) => i.value === period);

            if (yearItem) {
                // Find group matching year title
                const quarterGroup = projectData.quartersList.find((g: any) =>
                    g.label !== "Yearly Wise" && g.label.includes(yearItem.title)
                );
                if (quarterGroup && quarterGroup.items && quarterGroup.items.length > 0) {
                    return quarterGroup.items[0].value;
                }
            }
        }
        return period;
    }

    const effectiveSelectedPeriod = useMemo(() => findLatestQuarter(selectedPeriod), [selectedPeriod, projectData]);
    const effectiveComparisonQuarter = useMemo(() => findLatestQuarter(comparisonQuarter), [comparisonQuarter, projectData]);

    const { data: projectsRes, mutate } = useFrappeGetCall<{ message: { project: ProjectMilestoneData } }>(
        'gms.api.project.get_grant_projects_by_quarter',
        { project_id: projectId, quarter_value: effectiveSelectedPeriod },
        effectiveSelectedPeriod ? undefined : null
    );

    const { data: comparisonRes } = useFrappeGetCall(
        'gms.api.project.compare_quarter_metrics_grant',
        {
            project_id: projectId,
            quarter_value: effectiveSelectedPeriod,
            compare_with: effectiveComparisonQuarter
        },
        comparisonQuarter ? undefined : null
    );

    useEffect(() => {
        console.log('selectedPeriod ----> ', selectedPeriod)
        mutate()
    }, [selectedPeriod, effectiveSelectedPeriod]);

    useEffect(() => {
        if (projectsRes?.message?.project) {
            console.log('Milestone Data ----> ', projectsRes.message.project);
            setProjectMilestoneData(projectsRes.message.project);
            setOverallUtilization(projectsRes.message.overall_utilization_percent)
        }
    }, [projectsRes]);

    useEffect(() => {
        if (projectResponse?.message?.project && JSON.stringify(projectResponse.message.project) !== JSON.stringify(projectData)) {
            setProjectData(projectResponse.message.project);
        }
        if (projectError) {
            console.error('Project Details Fetch Error:', projectError);
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [projectResponse, projectError]);

    useEffect(() => {
        if (projectData && projectData.quartersList && projectData.quartersList.length > 0 && projectData.quartersList[0].items && projectData.quartersList[0].items.length > 0) {
            setSelectedPeriod(projectData.quartersList[0].items[0].value);
        }
    }, [projectData])

    // Scroll to top when component mounts
    useEffect(() => {
        window.scrollTo(0, 0);
    }, []);



    const budgetMetrics = useMemo(() => {
        if (!projectMilestoneData?.milestone) {
            return {
                forecasted: 0,
                actual: 0,
                utilization: '0',
                overallUtilized: 0
            };
        }

        const totalActual = Number(projectMilestoneData.milestone.metrics['Budget Spent'] || 0);
        const totalForecasted = Number(projectMilestoneData.milestone.forecasted_amount || 0);
        const utilization = totalForecasted > 0 ? ((totalActual / totalForecasted) * 100).toFixed(0) : '0';
        const overallUtilized = overallYearUtilization
        return {
            forecasted: totalForecasted,
            actual: totalActual,
            utilization: utilization,
            overallUtilized
        };
    }, [projectMilestoneData]);

    const getMetricTrend = (key: string) => {
        if (comparisonRes?.message?.metrics?.[key]) {
            const metric = comparisonRes.message.metrics[key];
            if (metric.growth === 0) return { change: 'No Change', isPositive: true };
            return {
                change: `${metric.growth > 0 ? '+' : ''}${metric.growth_percent}%`,
                isPositive: metric.growth >= 0
            };
        }
        return null;
    };

    const trlTrend = getMetricTrend('Technology Readiness Level');
    const mrlTrend = getMetricTrend('Market Readiness Level');
    const crlTrend = getMetricTrend('Commercial Readiness Level');
    const sirlTrend = getMetricTrend('Social Impact Readiness Level');
    const budgetTrend = getMetricTrend('Budget Spent');
    const forecastTrend = getMetricTrend('Forecasted Amount');
    const utilizationTrend = getMetricTrend('Fund Utilization');
    const impactTrend = getMetricTrend('Impact Created');
    const aiTrend = getMetricTrend('AI Breakthroughs');

    // Data Fetching for Partners and Contributors
    const { call: fetchPartners, result: partnersResult } = useFrappePostCall('gms.api.project.fetch_project_partners');
    const { call: fetchContributors, result: contributorsResult } = useFrappePostCall('gms.api.project.fetch_project_contributors');

    useEffect(() => {
        if (grantId && projectId && effectiveSelectedPeriod) {
            fetchPartners({
                grant_id: grantId,
                quarter_value: effectiveSelectedPeriod,
                project_id: projectId,
                sort_by: 'title',
                page: 1,
                page_size: 10
            });
            fetchContributors({
                grant_id: grantId,
                quarter_value: effectiveSelectedPeriod,
                project_id: projectId,
                sort_by: 'title',
                page: 1,
                page_size: 10
            });
        }
    }, [grantId, projectId, effectiveSelectedPeriod, fetchPartners, fetchContributors]);

    const partners = useMemo(() => {
        if (!partnersResult?.message?.partners_map) return [];
        return Object.values(partnersResult.message.partners_map).flat().map((p: any) => ({
            id: p.id,
            title: p.title,
            responsibilities: p.responsibilities || [],
            budget: p.budget
        }));
    }, [partnersResult]);

    const contributors = useMemo(() => {
        if (!contributorsResult?.message?.contributors_map) return [];
        return Object.values(contributorsResult.message.contributors_map).flat().map((c: any) => ({
            id: c.id,
            title: c.title,
            role: c.role,
            designation: c.designation,
            position: c.position,
            institution: c.institution,
            email: c.email
        }));
    }, [contributorsResult]);

    // Show loading state while data is being fetched
    if (isLoadingProject || (!projectData && !projectError)) {
        return (
            <DashboardLayout>
                <div className="flex items-center justify-center h-full">
                    <p className="text-muted-foreground">Loading project details...</p>
                </div>
            </DashboardLayout>
        );
    }

    // Show 404 page if project not found or error occurred (after loading completes)
    if (projectError || !projectResponse) {
        return <NotFound />;
    }






    return (
        <DashboardLayout showGrantSwitcher={true}>
            {/* Breadcrumb */}
            <AppBreadcrumb />

            {/* Page Header */}
            <div className="mb-6">
                <h1 className="text-foreground font-semibold text-[30px] leading-[125%] tracking-[-0.3px] mb-4">
                    {projectData.title}
                </h1>
                {/* Metadata Row */}
                <div className="flex flex-wrap items-center gap-2">
                    <Badge variant="secondary" className="text-muted-foreground text-center font-medium text-sm leading-[150%] tracking-[0.07px] rounded-lg border border-[#E2E8F0]">
                        Lead Institute: {projectData.lead_organization}
                    </Badge>
                    <Badge variant="secondary" className="text-muted-foreground text-center font-medium text-sm leading-[150%] tracking-[0.07px] rounded-lg border border-[#E2E8F0]">
                        Active Since: {projectData.start_date}
                    </Badge>
                    <Badge variant="secondary" className="text-muted-foreground text-center font-medium text-sm leading-[150%] tracking-[0.07px] rounded-lg border border-[#E2E8F0]">
                        Last Updated: {projectData.last_updated ? new Date(projectData.last_updated).toLocaleDateString('en-IN') : '--'}
                    </Badge>
                </div>
            </div>



            {/* Separator */}
            <div className="h-px bg-border mb-6" />

            {/* Controls Row */}
            <DashbaordFilterComponent
                quartersList={projectData?.quartersList}
                selectedPeriod={selectedPeriod}
                setSelectedPeriod={setSelectedPeriod}
                comparisonQuarter={comparisonQuarter}
                setComparisonQuarter={setComparisonQuarter}
            />

            <SectionWrapper
                title="TCRM's Metrics"
                contentClassName="grid grid-cols-4 gap-4"
            >
                {/* Q3 Forecasted */}
                <div className="p-6 bg-card border border-border rounded flex flex-col gap-4">
                    <div className="text-muted-foreground font-medium text-base leading-6">Technology Readiness Level</div>
                    <div className="flex items-center gap-2">
                        <span className="text-2xl font-semibold leading-[120%]  text-foreground">{projectMilestoneData?.milestone?.metrics?.['Technology Readiness Level']}</span>
                        {trlTrend && (
                            <TrendingBadge change={trlTrend.change} isPositive={trlTrend.isPositive} />
                        )}
                    </div>
                </div>

                {/* Q3 Actual Spend */}
                <div className="p-6 bg-card border border-border rounded flex flex-col gap-4">
                    <div className="text-muted-foreground font-medium text-base leading-6">Market Readiness Level</div>
                    <div className="flex items-center gap-2">
                        <span className="text-2xl font-semibold leading-[120%]  text-foreground">{projectMilestoneData?.milestone?.metrics?.['Market Readiness Level']}</span>
                        {mrlTrend && (
                            <TrendingBadge change={mrlTrend.change} isPositive={mrlTrend.isPositive} />
                        )}
                    </div>
                </div>

                {/* Q3 Utilisation % */}
                <div className="p-6 bg-card border border-border rounded flex flex-col gap-4">
                    <div className="text-muted-foreground font-medium text-base leading-6">Commercial Readiness Level</div>
                    <div className="flex items-center gap-2">
                        <span className="text-2xl font-semibold leading-[120%]  text-foreground">{projectMilestoneData?.milestone?.metrics?.['Commercial Readiness Level']}</span>
                        {crlTrend && (
                            <TrendingBadge change={crlTrend.change} isPositive={crlTrend.isPositive} />
                        )}
                    </div>
                </div>

                {/* Current year Utilised */}
                <div className="p-6 bg-card border border-border rounded flex flex-col gap-4">
                    <div className="text-muted-foreground font-medium text-base leading-6">Social Impact Readiness Level</div>
                    <div className="flex items-center gap-2">
                        <span className="text-2xl font-semibold leading-[120%]  text-foreground">{projectMilestoneData?.milestone?.metrics?.['Social Impact Readiness Level']}</span>
                        {sirlTrend && (
                            <TrendingBadge change={sirlTrend.change} isPositive={sirlTrend.isPositive} />
                        )}
                    </div>
                </div>
            </SectionWrapper>

            {/* Key Highlights & Lowlights */}
            <SectionWrapper
                title="Key Highlights & Lowlights"
                contentClassName="grid flex gap-6 flex-col"
            >
                <div className="grid grid-cols-2 gap-6">
                    {/* Highlights */}
                    <div className="p-6 bg-card flex flex-col gap-4 border border-border rounded text-muted-foreground font-inter text-base font-medium leading-6">
                        <h3>Highlights</h3>
                        <div className="flex flex-col gap-4 text-muted-foreground">
                            {projectMilestoneData?.milestone?.metrics?.['High lights']?.map((highlight, index) => (
                                <div key={index} className="flex gap-2 items-start">
                                    <CircleCheckBig className="w-5 h-5 shrink-0 mt-0.5" />
                                    <p>{highlight}</p>
                                </div>
                            ))}
                            {(!projectMilestoneData?.milestone?.metrics?.['High lights'] || projectMilestoneData.milestone.metrics['High lights'].length === 0) && (
                                <p className="text-sm italic">No highlights recorded.</p>
                            )}
                        </div>
                    </div>

                    {/* Lowlights */}
                    <div className="p-6 bg-card flex flex-col gap-4 border border-border rounded text-muted-foreground font-inter text-base font-medium leading-6">
                        <h3>Lowlights</h3>
                        <div className="flex flex-col gap-4 text-muted-foreground">
                            {projectMilestoneData?.milestone?.metrics?.['Low lights']?.map((lowlight, index) => (
                                <div key={index} className="flex gap-2 items-start">
                                    <BadgeInfo className="w-5 h-5 shrink-0 mt-0.5" />
                                    <p>{lowlight}</p>
                                </div>
                            ))}
                            {(!projectMilestoneData?.milestone?.metrics?.['Low lights'] || projectMilestoneData.milestone.metrics['Low lights'].length === 0) && (
                                <p className="text-sm italic">No lowlights recorded.</p>
                            )}
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
                            {projectData?.quarterWiseOverallProgress?.slice(0, 4).map((item, index) => (
                                <div key={index}>
                                    <div className="flex items-center justify-between mb-2">
                                        <span className="text-sm font-medium">{item.quarter}</span>
                                        <span className="text-sm font-semibold">{item.overall_progress}%</span>
                                    </div>
                                    <div className="w-full bg-gray-200 rounded-full h-2">
                                        <div
                                            className="bg-black h-2 rounded-full"
                                            style={{ width: `${item.overall_progress}%` }}
                                        />
                                    </div>
                                </div>
                            ))}
                        </div>
                        {projectData?.quarterWiseOverallProgress && projectData.quarterWiseOverallProgress.length > 4 && (
                            <DialogButton
                                title="Progress"
                                description="Overall progress for each quarter."
                                content={
                                    <div className="space-y-6 mt-4">
                                        {projectData.quarterWiseOverallProgress.map((item, index) => (
                                            <div key={index}>
                                                <div className="flex items-center justify-between mb-2">
                                                    <span className="text-sm font-medium">{item.quarter}</span>
                                                    <span className="text-sm font-semibold">{item.overall_progress}%</span>
                                                </div>
                                                <div className="w-full bg-gray-200 rounded-full h-2">
                                                    <div
                                                        className="bg-black h-2 rounded-full"
                                                        style={{ width: `${item.overall_progress}%` }}
                                                    />
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                }
                            >
                                <Button variant="outline" className="w-full mt-6">
                                    View all
                                    <svg className="ml-2 w-4 h-4" viewBox="0 0 16 16" fill="none">
                                        <path
                                            d="M6 12L10 8L6 4"
                                            stroke="currentColor"
                                            strokeWidth="2"
                                            strokeLinecap="round"
                                            strokeLinejoin="round"
                                        />
                                    </svg>
                                </Button>
                            </DialogButton>
                        )}
                    </div>

                    {/* Artifacts Card */}
                    <div className="p-6 bg-card border border-border rounded">
                        <h3 className="text-base font-semibold mb-1">Artifacts</h3>
                        <p className="text-sm text-muted-foreground mb-6">Quick links to access the projects related doc</p>

                        <div className="space-y-6">
                            {projectMilestoneData?.milestone?.artifacts?.slice(0, 6).map((artifact, index) => (
                                <a key={index} href={artifact.link} target="_blank" rel="noopener noreferrer" className="flex items-center gap-2 text-sm hover:underline">
                                    <Link className='h-4 w-4' />
                                    {artifact.title}
                                </a>
                            ))}
                            {(!projectMilestoneData?.milestone?.artifacts || projectMilestoneData.milestone.artifacts.length === 0) && (
                                <p className="text-sm italic">No artifacts found.</p>
                            )}
                        </div>

                        {projectMilestoneData?.milestone?.artifacts && projectMilestoneData.milestone.artifacts.length > 6 && (
                            <DialogButton
                                title="Artifacts"
                                description="Quick links to access the projects related doc"
                                content={
                                    <div className="space-y-6 mt-4">
                                        {projectMilestoneData?.milestone?.artifacts?.map((artifact, index) => (
                                            <div key={index}>
                                                <a href={artifact.link} target="_blank" rel="noopener noreferrer" className="flex items-center gap-2 text-sm hover:underline">
                                                    <Link className='h-4 w-4' />
                                                    {artifact.title}
                                                </a>
                                            </div>
                                        ))}
                                    </div>
                                }
                            >
                                <Button variant="outline" className="w-full mt-6">
                                    View all
                                    <svg className="ml-2 w-4 h-4" viewBox="0 0 16 16" fill="none">
                                        <path
                                            d="M6 12L10 8L6 4"
                                            stroke="currentColor"
                                            strokeWidth="2"
                                            strokeLinecap="round"
                                            strokeLinejoin="round"
                                        />
                                    </svg>
                                </Button>
                            </DialogButton>
                        )}
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
                                    <span className="text-3xl font-bold text-foreground">{formatTextWithNumber(projectMilestoneData?.milestone?.metrics?.['Impact Created'] || '')}</span>
                                    {/* <span className="text-sm text-muted-foreground">citizens</span> */}
                                </div>
                                {impactTrend && (
                                    <div className="flex items-center w-3 gap-2">
                                        <TrendingBadge change={impactTrend.change} isPositive={impactTrend.isPositive} />
                                    </div>  
                                )}
                            </div>

                            {/* AI breakthroughs */}
                            <div className="p-4 border border-orange-200 rounded-lg bg-orange-50/30">
                                <div className="text-sm text-muted-foreground mb-2">AI breakthroughs</div>
                                <div className="flex items-baseline gap-2 mb-2">
                                    <span className="text-3xl font-bold text-foreground">{projectMilestoneData?.milestone?.metrics?.['AI Breakthroughs']}</span>
                                </div>
                                {aiTrend && (
                                    <div className="flex items-center w-3 gap-2">
                                        <TrendingBadge change={aiTrend.change} isPositive={aiTrend.isPositive} />
                                    </div>
                                )}
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
                <div className="p-6 pl-0 bg-card border border-border rounded">
                    <BudgetUtilizationChart budgetUtilization={projectData.budget_utilization}/>
                </div>
                {/* Metrics Grid */}
                <div className="grid grid-cols-4 gap-4">
                    {/* Q3 Forecasted */}
                    <div className="p-6 bg-card border border-border rounded flex flex-col gap-3">
                        <div className="text-sm text-muted-foreground">{selectedPeriod.slice(0, 2) || 'Quarterly'}  Forecasted</div>
                        <div className="flex items-center gap-2">
                            <span className="text-2xl font-semibold leading-[120%]  text-foreground">{formatIndianAmount(budgetMetrics?.forecasted)}</span>
                            {forecastTrend && (
                                <TrendingBadge change={forecastTrend.change} isPositive={forecastTrend.isPositive} />
                            )}
                        </div>
                    </div>

                    {/* Q3 Actual Spend */}
                    <div className="p-6 bg-card border border-border rounded flex flex-col gap-3">
                        <div className="text-sm text-muted-foreground">{selectedPeriod.slice(0, 2) || 'Quarterly'}  Actual Spend</div>
                        <div className="flex items-center gap-2">
                            <span className="text-2xl font-semibold leading-[120%]  text-foreground">{formatIndianAmount(budgetMetrics?.actual)}</span>
                            {budgetTrend && (
                                <TrendingBadge change={budgetTrend.change} isPositive={budgetTrend.isPositive} />
                            )}
                        </div>
                    </div>

                    {/* Q3 Utilisation % */}
                    <div className="p-6 bg-card border border-border rounded flex flex-col gap-3">
                        <div className="text-sm text-muted-foreground">{selectedPeriod.slice(0, 2) || 'Quarterly'} Utilisation %</div>
                        <div className="flex items-center gap-2">
                            <span className="text-2xl font-semibold leading-[120%]  text-foreground">
                                {budgetMetrics.utilization}%
                            </span>
                            {utilizationTrend && (
                                <TrendingBadge change={utilizationTrend.change} isPositive={utilizationTrend.isPositive} />
                            )}
                        </div>
                    </div>

                    {/* Current year Utilised */}
                    <div className="p-6 bg-card border border-border rounded flex flex-col gap-3">
                        <div className="text-sm text-muted-foreground">Overall year Utilised</div>
                        <div className="flex items-center gap-2">
                            <span className="text-2xl font-semibold leading-[120%]  text-foreground">{budgetMetrics?.overallUtilized || 0}%</span>
                            {/* <span className="flex items-center gap-1 px-2 py-1 rounded-full bg-green-100 text-green-700">
                                <TrendingUp className="w-3 h-3" />
                                <span className="text-xs font-medium">+18%</span>
                            </span> */}
                        </div>
                    </div>
                </div>
            </SectionWrapper>

            <OrgMembers partners={partners} contributors={contributors} quarter={selectedPeriod} />
        </DashboardLayout>
    );
}
