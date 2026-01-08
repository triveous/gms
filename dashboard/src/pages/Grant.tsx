import { useNavigate, useParams } from 'react-router-dom';
import { Badge } from '@/components/ui/badge';

import { TrendingUp, TrendingDown, CircleCheckBig, BadgeInfo } from 'lucide-react';
import DashboardLayout from '@/components/DashboardLayout';
import { ProjectCard } from '@/components/ProjectCard';
import { BudgetUtilizationChart } from '@/components/BudgetUtilizationChart';
import { SectionWrapper } from '@/components/SectionWrapper';
import DashbaordFilterComponent from '@/components/DashbaordFilterComponent';
import OrgMembers, { type Partner, type Contributor } from '@/components/OrgMembers';
import EmptyState from '@/components/EmptyState';
import { useFrappeGetCall } from 'frappe-react-sdk';
import { useEffect, useMemo, useState } from 'react';
import { safe, formatIndianAmount, formatTimeline, calculateBudgetSpendPercent } from '@/utils/formatters';
import { TrendingBadge } from '@/components/TrendingBadge';

interface GrantUI {
    id: string;
    title: string;
    leadInstitute: string;
    timeline: string;
    totalBudget: string | number;
    budgetSpend: string | number;
    budgetSpendPercent: string | number;
    overallProgress: string | number;
    alias: string;
    approvalNumber: string;
    quartersList: any[];
    budget_utilization: any[];
    totalProjects: string;
}

interface Project {
    title: string;
    id: string;
    projectLead: string;
    activeSince: string;
    lastUpdated: string;
    metrics: {
        tbl: { value: number; change: string; isPositive: boolean };
        mrl: { value: number; change: string; isPositive: boolean };
        crl: { value: number; change: string; isPositive: boolean };
        sirl: { value: number; change: string; isPositive: boolean };
    };
    budgetSpent: string;
    progress: string;
}

export default function Grant() {
    const navigate = useNavigate();
    const { grantId } = useParams<{ grantId: string }>();
    const [grantData, setGrantData] = useState<GrantUI>({} as GrantUI);
    const [selectedPeriod, setSelectedPeriod] = useState('');
    const [comparisonQuarter, setComparisonQuarter] = useState('');
    const [projectsData, setProjectData] = useState<Project[]>([]);

    const { data, error, isLoading } = useFrappeGetCall(
        'gms.api.grant.get_single_grant_info',
        { grant_id: grantId }
    );

    // Helper to find latest quarter for year
    const findLatestQuarter = (period: string) => {
        if (!period || period.startsWith('Q')) return period;
        
        // It's a year value, find the corresponding group
        if (grantData.quartersList) {
            const yearlyGroup = grantData.quartersList.find((g: any) => g.label === "Yearly Wise");
            const yearItem = yearlyGroup?.items.find((i: any) => i.value === period);
            
            if (yearItem) {
                // Find group matching year title
                const quarterGroup = grantData.quartersList.find((g: any) => 
                     g.label !== "Yearly Wise" && g.label.includes(yearItem.title)
                );
                if (quarterGroup?.items?.length > 0) {
                    return quarterGroup.items[0].value;
                }
            }
        }
        return period;
    }

    const effectiveSelectedPeriod = useMemo(() => findLatestQuarter(selectedPeriod), [selectedPeriod, grantData]);
    const effectiveComparisonQuarter = useMemo(() => findLatestQuarter(comparisonQuarter), [comparisonQuarter, grantData]);

    const { data: projectsRes, isLoading: projectsLoading, mutate } = useFrappeGetCall(
        'gms.api.projects.get_grant_projects_by_quarter',
        { grant_id: grantId, quarter_value: effectiveSelectedPeriod },
        effectiveSelectedPeriod ? undefined : null
    );
    console.log('DATA ---> ',projectsRes)

    // API → UI formatted grants
    const formattedGrant = useMemo<GrantUI>(() => {
        if (!data) return {} as GrantUI;

        return {
            id: safe(data.message.name),
            alias: safe(data.message.alias),
            title: safe(data.message.title),
            leadInstitute: safe(data.message.organization.title),
            timeline:formatTimeline(data.message.start_date, data.message.end_date),
            approvalNumber: safe(data.message.approval_number),
            totalBudget: formatIndianAmount(data.message.approved_amount),
            budgetSpend: formatIndianAmount(data.message.budget_spent),
            budgetSpendPercent: calculateBudgetSpendPercent(data.message.approved_amount, data.message.budget_spent),
            overallProgress: '--',
            quartersList: data.message.quartersList,
            totalProjects: safe(data.message.total_projects),
            budget_utilization: data.message.budget_utilization || [],
        };
    }, [data]);

    useEffect(() => {
        setGrantData(formattedGrant);
    }, [formattedGrant]);

    useEffect(() => {
    if (grantData.quartersList && grantData.quartersList.length > 0 && grantData.quartersList[0].items && grantData.quartersList[0].items.length > 0) {
        setSelectedPeriod(grantData.quartersList[0].items[0].value);
    }
    },[grantData])


    useEffect(() => {
        console.log('selectedPeriod ----> ',selectedPeriod)
        mutate()
    }, [selectedPeriod, effectiveSelectedPeriod]);




    const { data: comparisonRes } = useFrappeGetCall(
        'gms.api.projects.compare_quarter_metrics_grant_project_spesific',
        {
            grant_id: grantId,
            quarter_value: effectiveSelectedPeriod,
            compare_with: effectiveComparisonQuarter
        },
        comparisonQuarter ? undefined : null
    );

    const { data: forecastComparisonRes } = useFrappeGetCall(
        'gms.api.projects.compare_quarter_metrics_grant_forcast',
        {
            grant_id: grantId,
            quarter_value: effectiveSelectedPeriod,
            compare_with: effectiveComparisonQuarter
        },
        comparisonQuarter ? undefined : null
    );

    const getForecastMetric = (key: 'Forecasted Amount' | 'Budget Spent' | 'Fund Utilization') => {
        if (forecastComparisonRes?.message?.metrics?.[key]) {
            const metric = forecastComparisonRes.message.metrics[key];
            if (metric.growth === 0) return { change: 'No Change', isPositive: true };
            return {
                change: `${metric.growth > 0 ? '+' : ''}${metric.growth_percent}%`,
                isPositive: metric.growth >= 0
            };
        }
        return null;
    };

    const forecastedTrend = getForecastMetric('Forecasted Amount');
    const spentTrend = getForecastMetric('Budget Spent');
    const utilizationTrend = getForecastMetric('Fund Utilization');
    
    // Process Projects Data
    const formattedProjects = useMemo<Project[]>(() => {
        if (!projectsRes?.message?.projects) return [];

        return projectsRes.message.projects.map((project: { 
            name: string; 
            title: string; 
            lead_organization: string; 
            start_date: string; 
            milestones?: { metrics?: Record<string, string | number>; last_updated?: string }[] 
        }) => {
            // Get first milestone (assuming filtered by quarter or latest)
            const milestone = project.milestones?.[0] || {};
            const metrics = milestone.metrics || {};

            return {
                id: project.name,
                title: project.title,
                projectLead: project.lead_organization || '--', // Using ID as organization name is not available
                activeSince: project.start_date ? new Date(project.start_date).toLocaleDateString('en-IN', { month: 'short', year: 'numeric' }) : '--', 
                lastUpdated: milestone.last_updated ? new Date(milestone.last_updated).toLocaleDateString('en-IN') : '--',
                metrics: {
                    tbl: { 
                        value: Number(metrics['Technology Readiness Level'] || 0), 
                        change: '', 
                        isPositive: true 
                    },
                    mrl: { 
                        value: Number(metrics['Market Readiness Level'] || 0), 
                        change: '', 
                        isPositive: true 
                    },
                    crl: { 
                        value: Number(metrics['Commercial Readiness Level'] || 0), 
                        change: '', 
                        isPositive: true 
                    },
                    sirl: { 
                        value: Number(metrics['Social Impact Readiness Level'] || 0), 
                        change: '', 
                        isPositive: true 
                    },
                },
                budgetSpent: formatIndianAmount(metrics['Budget Spent']),
                progress: metrics['Overall Progress'] ? `${metrics['Overall Progress']}%` : '0%',
            };
        });
    }, [projectsRes]);

    useEffect(() => {
        setProjectData(formattedProjects);
    }, [formattedProjects]);

    const budgetMetrics = useMemo(() => {
        if (!projectsRes?.message?.projects) {
            return {
                forecasted: 0,
                actual: 0,
                utilization: '0',
                overallUtilization: 0
            };
        }

        const projects = projectsRes.message.projects;
        let totalForecasted = 0;

        projects.forEach((p: { milestones?: { forecasted_amount?: string | number }[] }) => {
            // Get first milestone (assuming filtered by quarter or latest)
            const milestone = p.milestones?.[0];
            if (milestone?.forecasted_amount) {
                totalForecasted += Number(milestone.forecasted_amount);
            }
        });

        const totalActual = Number(projectsRes.message.total_budget_spent || 0);
        
        const utilization = totalForecasted > 0 ? ((totalActual / totalForecasted) * 100).toFixed(0) : '0';

        return {
            forecasted: totalForecasted,
            actual: totalActual,
            utilization: utilization,
            overallUtilization: projectsRes.message.overall_utilization_percent || 0
        };
    }, [projectsRes]);


    const { partners, contributors } = useMemo(() => {
        if (!projectsRes?.message?.projects) return { partners: [], contributors: [] };

        const partnersMap = new Map<string, Partner>();
        const contributorsMap = new Map<string, Contributor>();

        projectsRes.message.projects.forEach((project: any) => {
            project.milestones?.forEach((milestone: any) => {
                milestone.partners_and_team_members?.forEach((member: any) => {
                    if (member.partner) {
                        partnersMap.set(member.partner.id, {
                            id: member.partner.id,
                            title: member.partner.title,
                            responsibility: member.partner.responsibility
                        });
                    }
                    if (member.contributor) {
                        contributorsMap.set(member.contributor.id, {
                            id: member.contributor.id,
                            title: member.contributor.title,
                            role: member.contributor.role
                        });
                    }
                });
            });
        });

        return {
            partners: Array.from(partnersMap.values()),
            contributors: Array.from(contributorsMap.values())
        };
    }, [projectsRes]);

    return (
        <DashboardLayout>
            {isLoading && (
                <div className="text-center text-muted-foreground py-6">
                    Loading grant details...
                </div>
            )}

            {error && (
                <div className="text-center text-red-600 py-6">
                    Failed to load grant details.
                </div>
            )}

            {!isLoading && !grantData.id && (
                 <div className="text-center text-muted-foreground py-6">
                    No grant details found.
                </div>
            )}

            {!isLoading && grantData.id && (
                <>
            {/* Breadcrumb */}
            <div className="mb-6">
                <button 
                    onClick={() => navigate('/')}
                    className="text-sm text-muted-foreground hover:text-foreground flex items-center gap-1"
                >
                    Home <span>›</span>
                </button>
            </div>

            {/* Page Header */}
            <div className="mb-6">
                <h1 className="text-foreground font-semibold text-[30px] leading-[125%] tracking-[-0.3px] mb-4">
                    {grantData.title}
                </h1>
                
                {/* Metadata Row */}
                <div className="flex flex-wrap items-center gap-2">
                    <Badge variant="secondary" className="text-muted-foreground text-center font-medium text-sm leading-[150%] tracking-[0.07px] rounded-lg border border-[#E2E8F0]">
                        Alias: {grantData.alias}
                    </Badge>
                    <Badge variant="secondary" className="text-muted-foreground text-center font-medium text-sm leading-[150%] tracking-[0.07px] rounded-lg border border-[#E2E8F0]">
                        Lead Institute: {grantData.leadInstitute}
                    </Badge>
                    <Badge variant="secondary" className="text-muted-foreground text-center font-medium text-sm leading-[150%] tracking-[0.07px] rounded-lg border border-[#E2E8F0]">
                        Timeline: {grantData.timeline}
                    </Badge>
                    <Badge variant="secondary" className="text-muted-foreground text-center font-medium text-sm leading-[150%] tracking-[0.07px] rounded-lg border border-[#E2E8F0]">
                        Approval Number: {grantData.approvalNumber}
                    </Badge>
                </div>
            </div>

            {/* Metrics Cards */}
            <div className="flex gap-4 mb-6">
                {/* Total Budget */}
                <div className="flex flex-col gap-3">
                    <div className="text-muted-foreground font-medium text-base leading-[150%]">Total Budget</div>
                    <div className="text-foreground font-semibold text-xl leading-[120%] tracking-[-0.4px]">
                        {grantData.totalBudget}
                    </div>
                </div>

                <div className="w-px bg-border self-stretch" />

                {/* Total Budget Spend */}
                <div className="flex flex-col gap-3">
                    <div className="text-muted-foreground font-medium text-base leading-[150%]">Total Budget Spend</div>
                    <div className="flex items-center gap-2">
                        <div className="text-foreground font-semibold text-xl leading-[120%] tracking-[-0.4px]">
                            {grantData.budgetSpend}
                        </div>
                        {grantData.budgetSpendPercent !== '--' && (
                            <Badge className="bg-green-100 text-foreground font-mono text-xs font-normal leading-[150%]">
                                {grantData.budgetSpendPercent}%
                            </Badge>
                        )}
                    </div>
                </div>

                <div className="w-px bg-border self-stretch" />

                {/* Overall Progress */}
                <div className="flex flex-col gap-3">
                    <div className="text-muted-foreground font-medium text-base leading-[150%]">Overall Progress</div>
                    <div className="text-foreground font-semibold text-xl leading-[120%] tracking-[-0.4px]">
                        {grantData.overallProgress}
                        {grantData.overallProgress !== '--' && '%'}
                    </div>
                </div>
            </div>

            {/* Separator */}
            <div className="h-px bg-border" />



            {/* Conditional rendering based on projects data */}
            {Number(grantData.totalProjects) === 0 ? (
                <EmptyState />
            ) : (
                <>
                    {/* Controls Row */}
                    <DashbaordFilterComponent 
                        quartersList={grantData.quartersList} 
                        selectedPeriod={selectedPeriod} 
                        setSelectedPeriod={setSelectedPeriod}
                        comparisonQuarter={comparisonQuarter}
                        setComparisonQuarter={setComparisonQuarter}
                    />
                    {/* Projects Section */}
                    <SectionWrapper 
                        title="Projects"
                        className="mt-8"
                        contentClassName="space-y-4"
                    >
                        {projectsData.map((project) => (
                            <ProjectCard
                                key={project.id}
                                grantId={grantId as string}
                                title={project.title}
                                id={project.id}
                                projectLead={project.projectLead}
                                activeSince={project.activeSince}
                                lastUpdated={project.lastUpdated}
                                metrics={project.metrics}
                                budgetSpent={project.budgetSpent}
                                progress={project.progress}
                                comparisonData={comparisonRes?.message?.find((item: any) => item.project === project.id)}
                            />
                        ))}
                    </SectionWrapper>

                    {/* Key Highlights & Lowlights */}
                    <SectionWrapper 
                        title="Key Highlights & Lowlights"
                        contentClassName="grid grid-cols-2 gap-6"
                    >
                        {/* Highlights */}
                        <div className="p-6 bg-card flex flex-col gap-4 border border-border rounded text-muted-foreground font-inter text-base font-medium leading-6">
                            <h3>Highlights</h3>
                            <div className="flex flex-col gap-4">
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
                            <div className="flex flex-col gap-4 ">
                                <div className="flex gap-2 items-start">
                                    <BadgeInfo className="w-5 h-5 shrink-0 mt-0.5" />
                                    <p>
                                        Hardware and Software compatibility has been tuning out to be the major design revision factor than we anticipated. We are going ahead with the largest API/SDK distribution as per Android Developer's distribution page
                                    </p>
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
                            <BudgetUtilizationChart budgetUtilization={grantData.budget_utilization}/>
                        </div>
                        {/* Metrics Grid */}
                        <div className="grid grid-cols-4 gap-4">
                            {/* Forecasted */}
                            <div className="p-6 bg-card border border-border rounded flex flex-col gap-3">
                                <div className="text-sm text-muted-foreground">{selectedPeriod.slice(0, 2) || 'Quarterly'} Forecasted</div>
                                <div className="flex flex-wrap items-center gap-2">
                                    <span className="text-2xl font-semibold leading-[120%]  text-foreground">
                                        {formatIndianAmount(budgetMetrics.forecasted)}
                                    </span>
                                    {forecastedTrend && (
                                        <TrendingBadge change={forecastedTrend.change} isPositive={forecastedTrend.isPositive} />
                                    ) }
                                </div>
                            </div>

                            {/* Actual Spend */}
                            <div className="p-6 bg-card border border-border rounded flex flex-col gap-3">
                                <div className="text-sm text-muted-foreground">{selectedPeriod.slice(0, 2) || 'Quarterly'} Actual Spend</div>
                                <div className="flex flex-wrap items-center gap-2">
                                    <span className="text-2xl font-semibold leading-[120%]  text-foreground">
                                        {formatIndianAmount(budgetMetrics.actual)}
                                    </span>
                                     {spentTrend && (
                                        <TrendingBadge change={spentTrend.change} isPositive={spentTrend.isPositive} />
                                    )}
                                </div>
                            </div>

                            {/* Utilisation % */}
                            <div className="p-6 bg-card border border-border rounded flex flex-col gap-3">
                                <div className="text-sm text-muted-foreground">{selectedPeriod.slice(0, 2) || 'Quarterly'} Utilisation %</div>
                                <div className="flex flex-wrap items-center gap-2">
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
                                    <span className="text-2xl font-semibold leading-[120%]  text-foreground">
                                        {budgetMetrics.overallUtilization}%
                                    </span>
                                    {/* <span className="flex items-center gap-1 px-2 py-1 rounded-full bg-green-100 text-green-700">
                                        <TrendingUp className="w-3 h-3" />
                                        <span className="text-xs font-medium">--</span>
                                    </span> */}
                                </div>
                            </div>
                        </div>
                    </SectionWrapper>

                    <OrgMembers partners={partners} contributors={contributors} />
                </>
            )}
            </>
            )}
        </DashboardLayout>
    );
}
