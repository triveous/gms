import { useNavigate } from 'react-router';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ChevronRight } from 'lucide-react';
import DashboardLayout from '@/components/DashboardLayout';
import { SectionWrapper } from '@/components/SectionWrapper';
import { useFrappeGetCall } from 'frappe-react-sdk';
import { useEffect, useMemo, useState } from 'react';

interface GrantUI {
    id: string;
    name: string;
    leadInstitute: string;
    timeline: string;
    totalBudget: string | number;
    budgetSpend: string | number;
    budgetSpendPercent: string | number;
    overallProgress: string | number;
    totalProjects: string | number;
}

export default function Grants() {
    const navigate = useNavigate();

    const { data, error, isLoading } = useFrappeGetCall(
        'gms.api.grants.get_grants_with_related',
        { limit: 50 }
    );



    const [grants, setGrants] = useState<GrantUI[]>([]);

    // Helper: Replace null/undefined/"" with "--"
    const safe = (value: string) =>
        value === null || value === undefined || value === '' ? '--' : value;

    const formatIndianAmount = (value: any) => {
        if (value === null || value === undefined || value === '' || isNaN(value)) {
            return '--';
        }

        const amount = Number(value);

        if (amount >= 1_00_00_000) {
            // Crores (>= 1 Cr)
            return `₹ ${(amount / 1_00_00_000).toLocaleString('en-IN', {
                maximumFractionDigits: 2
            })} Cr`;
        }

        if (amount >= 1_00_000) {
            // Lakhs
            return `₹${(amount / 1_00_000).toLocaleString('en-IN', {
                maximumFractionDigits: 2
            })} Lakhs`;
        }

        // Default fallback (just number)
        return amount.toLocaleString('en-IN');
    };

    const formatTimeline = (start: string, end: string) => {
        if (!start || !end) return '--';

        const s = new Date(start);
        const e = new Date(end);

        if (isNaN(s.getTime()) || isNaN(e.getTime())) return '--';

        // Calculate difference in years
        const years = e.getFullYear() - s.getFullYear();

        // Convert to readable date formats
        const months = [
            'January','February','March','April','May','June',
            'July','August','September','October','November','December'
        ];

        const startFormatted = `${months[s.getMonth()]} ${s.getFullYear()}`;
        const endFormatted = `${e.getDate()} ${months[e.getMonth()]} ${e.getFullYear()}`;

        return `${years} year (${startFormatted} - ${endFormatted})`;
    };


    const calculateBudgetSpendPercent = (total: any, spent: any) => {
        const totalAmount = Number(total);
        const spentAmount = Number(spent);

        if (
            total === null ||
            total === undefined ||
            total === '' ||
            spent === null ||
            spent === undefined ||
            spent === '' ||
            isNaN(totalAmount) ||
            isNaN(spentAmount) ||
            totalAmount === 0
        ) {
            return '--';
        }

        return ((spentAmount / totalAmount) * 100).toFixed(0);
    };

    // API → UI formatted grants
    const formattedGrants = useMemo<GrantUI[]>(() => {
        if (!data) return [];
        return data.message.map((g: any) => ({
            id: safe(g.name),
            name: safe(g.title),
            leadInstitute: safe(g.organization.title),
            timeline:formatTimeline(g.start_date, g.end_date),
            totalBudget: formatIndianAmount(g.approved_amount),

            // Fields we DON'T have yet → default "--"
            budgetSpend: formatIndianAmount(g.budget_spent),
            budgetSpendPercent: calculateBudgetSpendPercent(g.approved_amount, g.budget_spent),
            overallProgress: '--',
            totalProjects: safe(g.total_projects),
        }));
    }, [data]);

    useEffect(() => {
        setGrants(formattedGrants);
    }, [formattedGrants]);

    const handleGrantClick = (grantId: string) => {
        navigate(`/grant/${grantId}`);
    };

    return (
        <DashboardLayout>
            <SectionWrapper title="List of CoE's" contentClassName="space-y-4">
                {isLoading && (
                    <div className="text-center text-muted-foreground py-6">
                        Loading grants...
                    </div>
                )}

                {error && (
                    <div className="text-center text-red-600 py-6">
                        Failed to load grants.
                    </div>
                )}

                {!isLoading && grants.length === 0 && (
                    <div className="text-center text-muted-foreground py-6">
                        No grants found.
                    </div>
                )}

                {grants.map((grant) => (
                    <div
                        key={grant.id}
                        className="p-6 bg-card border-border rounded border flex flex-col gap-4"
                    >
                        {/* Header */}
                        <div className="flex gap-4">
                            <div className="flex flex-col gap-4 flex-1">
                                <h2 className="text-xl font-semibold text-foreground">
                                    {grant.name}
                                </h2>

                                <div className="flex flex-wrap items-center gap-4 text-sm text-muted-foreground">
                                    <span>Lead Institute: {grant.leadInstitute}</span>
                                    <span className="text-border">|</span>
                                    <span>Timeline: {grant.timeline}</span>
                                </div>
                            </div>

                            <div>
                                <Button
                                    variant="outline"
                                    className="w-[155px] h-[45px] px-6 gap-2"
                                    onClick={() => handleGrantClick(grant.id)}
                                >
                                    View CoE <ChevronRight className="w-4 h-4" />
                                </Button>
                            </div>
                        </div>

                        {/* Metrics */}
                        <div className="flex gap-4">
                            {/* Total Budget */}
                            <div>
                                <div className="text-sm text-muted-foreground">
                                    Total Budget
                                </div>
                                <div className="text-xl font-bold">
                                    {grant.totalBudget}
                                </div>
                            </div>

                            <div className="w-px bg-border" />

                            {/* Budget Spend */}
                            <div>
                                <div className="text-sm text-muted-foreground">
                                    Total Budget Spend
                                </div>
                                <div className="flex items-center gap-2">
                                    <div className="text-xl font-bold">
                                        {grant.budgetSpend}
                                    </div>
                                    {grant.budgetSpendPercent !== '--' && (
                                        <Badge className="bg-green-100 border-0 h-5 px-1.5 text-[10px]">
                                            {grant.budgetSpendPercent}%
                                        </Badge>
                                    )}
                                </div>
                            </div>

                            <div className="w-px bg-border" />

                            {/* Overall Progress */}
                            <div>
                                <div className="text-sm text-muted-foreground">
                                    Overall Progress
                                </div>
                                <div className="text-xl font-bold">
                                    {grant.overallProgress}
                                    {grant.overallProgress !== '--' && '%'}
                                </div>
                            </div>

                            <div className="w-px bg-border" />

                            {/* Total Projects */}
                            <div>
                                <div className="text-sm text-muted-foreground">
                                    Total Projects
                                </div>
                                <div className="text-xl font-bold">
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
