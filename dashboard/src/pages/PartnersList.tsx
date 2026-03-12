import { useParams, useSearchParams } from 'react-router-dom';
import { useFrappePostCall } from 'frappe-react-sdk';
import { useMemo, useState, useEffect } from 'react';
import { ChevronLeft, ChevronRight, ArrowUpDown, Sparkles, ListFilter, Check } from 'lucide-react';
import DashboardLayout from '@/components/DashboardLayout';
import { AppBreadcrumb } from '@/components/AppBreadcrumb';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from '@/components/ui/table';
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuCheckboxItem,
    DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';

const ITEMS_PER_PAGE = 10;

export default function PartnersList({ scope = 'grant' }: { scope?: 'grant' | 'project' }) {
    const { grantId, projectId } = useParams<{ grantId: string; projectId?: string }>();
    const [searchParams] = useSearchParams();
    const quarter = searchParams.get('quarter');

    const [currentPage, setCurrentPage] = useState(1);
    const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');
    const [projectFilter, setProjectFilter] = useState<string[]>([]);
    const [sortByType, setSortByType] = useState<'title' | null>(null);

    // Only use projectId if we are explicitly in project scope
    const activeProjectId = scope === 'project' ? projectId : undefined;



    // --- GRANT SCOPE DATA FETCHING (New API) ---
    const { call: fetchGrantPartners, result: grantPartnersResult } = useFrappePostCall('gms.api.projects.fetch_grant_partners');
    const { call: fetchProjectPartners, result: projectPartnersResult } = useFrappePostCall('gms.api.project.fetch_project_partners');

    useEffect(() => {
        if (activeProjectId && quarter) {
            // Project Scope
            fetchProjectPartners({
                grant_id: grantId,
                project_id: activeProjectId,
                quarter_value: quarter,
                page: currentPage,
                page_size: ITEMS_PER_PAGE,
                sort_by: sortByType === 'title' ? 'title' : undefined
            });
        } else if (grantId && quarter) {
            // Grant Scope
            fetchGrantPartners({
                grant_id: grantId,
                quarter_value: quarter,
                page: currentPage,
                page_size: ITEMS_PER_PAGE,
                project_ids: projectFilter.length > 0 ? projectFilter : undefined,
                sort_by: sortByType === 'title' ? 'title' : undefined
            });
        }
    }, [grantId, quarter, currentPage, activeProjectId, fetchGrantPartners, fetchProjectPartners, projectFilter, sortByType, sortOrder]);

    // Extract partners based on scope
    const partners = useMemo(() => {
        if (activeProjectId) {
            // Project context (New API Logic)
            if (!projectPartnersResult?.message?.partners_map) return [];
            return Object.values(projectPartnersResult.message.partners_map).flat().map((p: any) => ({
                id: p.id,
                title: p.title,
                projectName: p.project_name,
                responsibilities: p.responsibilities || [],
                budget: p.budget
            }));
        } else {
            // Grant context (New API Logic)
            if (!grantPartnersResult?.message?.partners_map) return [];

            // Flatten the map values into a single array
            return Object.values(grantPartnersResult.message.partners_map).flat().map((p: any) => ({
                id: p.id,
                title: p.title,
                projectName: p.project_name,
                responsibilities: p.responsibilities || [],
                budget: p.budget
            }));
        }
    }, [activeProjectId, grantPartnersResult, projectPartnersResult]);

    // Extract All Projects
    const allProjects: { id: string; name: string }[] = useMemo(() => {
        return grantPartnersResult?.message?.all_projects || [];
    }, [grantPartnersResult]);

    // Total Items logic
    const totalItems = useMemo(() => {
        if (activeProjectId) {
            return projectPartnersResult?.message?.total_count || 0;
        } else {
            return grantPartnersResult?.message?.total_count || 0;
        }
    }, [activeProjectId, grantPartnersResult, projectPartnersResult]);

    // Pagination Logic
    const totalPages = useMemo(() => {
        if (activeProjectId) {
            return projectPartnersResult?.message?.total_pages || 1;
        } else {
            return grantPartnersResult?.message?.total_pages || 1;
        }
    }, [activeProjectId, grantPartnersResult, projectPartnersResult]);

    // Derived list for render
    const visiblePartners = partners;

    // Pagination display variables
    const startIndex = (currentPage - 1) * ITEMS_PER_PAGE;
    const endIndex = Math.min(startIndex + ITEMS_PER_PAGE, totalItems);

    // Handlers
    const handleSort = () => {
        setSortByType('title');
        setSortOrder(prev => prev === 'asc' ? 'desc' : 'asc');
    };

    const handlePreviousPage = () => {
        setCurrentPage((prev) => Math.max(prev - 1, 1));
    };

    const handleNextPage = () => {
        setCurrentPage((prev) => Math.min(prev + 1, totalPages));
    };

    const handlePageClick = (page: number) => {
        setCurrentPage(page);
    };

    // Generate page numbers to display
    const getPageNumbers = () => {
        const pages: (number | string)[] = [];
        if (totalPages <= 5) {
            for (let i = 1; i <= totalPages; i++) {
                pages.push(i);
            }
        } else {
            if (currentPage <= 3) {
                pages.push(1, 2, 3, '...', totalPages);
            } else if (currentPage >= totalPages - 2) {
                pages.push(1, '...', totalPages - 2, totalPages - 1, totalPages);
            } else {
                pages.push(1, '...', currentPage, '...', totalPages);
            }
        }
        return pages;
    };



    return (
        <DashboardLayout showGrantSwitcher={true}>
            <AppBreadcrumb />

            <div className="bg-white rounded-lg border border-none p-6 mt-4">
                {/* Header */}
                <div className="flex items-center justify-between mb-6">
                    <h1 className="text-xl font-semibold text-foreground">Academic & Industry Partners</h1>
                </div>

                {/* Table */}
                <Table>
                    <TableHeader>
                        <TableRow className="border-b border-border">
                            <TableHead className="w-[352px]">
                                <button
                                    onClick={handleSort}
                                    className="flex items-center gap-2 text-muted-foreground font-medium hover:text-foreground"
                                >
                                    Organisation
                                    <ArrowUpDown className="w-4 h-4" />
                                </button>
                            </TableHead>
                            {!activeProjectId && (
                                <TableHead className="text-muted-foreground font-medium">
                                    <DropdownMenu>
                                        <DropdownMenuTrigger asChild>
                                            <button className="flex items-center gap-2 text-muted-foreground font-medium hover:text-foreground">
                                                Project
                                                <ListFilter className="w-4 h-4" />
                                            </button>
                                        </DropdownMenuTrigger>
                                        <DropdownMenuContent align="start" className='border-border rounded-sm max-w-[516px]'>
                                            {allProjects.map((project) => {
                                                const isChecked = projectFilter.includes(project.id);
                                                return (
                                                    <DropdownMenuCheckboxItem
                                                        key={project.id}
                                                        className="border-border pl-2 [&>span]:hidden cursor-pointer"
                                                        checked={isChecked}
                                                        onSelect={(e) => e.preventDefault()}
                                                        onCheckedChange={(checked) => {
                                                            setProjectFilter(prev => checked ? [...prev, project.id] : prev.filter(id => id !== project.id));
                                                            setCurrentPage(1);
                                                        }}
                                                    >
                                                        <div className="flex items-start gap-2 py-0.5">
                                                            <div className={`flex h-4 w-4 items-center justify-center rounded-[5px] border shrink-0 mt-0.5 ${isChecked ? 'bg-primary border-primary text-primary-foreground' : 'border-muted-foreground/30'}`}>
                                                                {isChecked && <Check className="h-3 w-3 bg-white rounded-[5px] border-[1px] border-border" />}
                                                            </div>
                                                            <span className="whitespace-normal break-words">{project.name}</span>
                                                        </div>
                                                    </DropdownMenuCheckboxItem>
                                                );
                                            })}
                                        </DropdownMenuContent>
                                    </DropdownMenu>
                                </TableHead>
                            )}
                            <TableHead className="text-muted-foreground font-medium max-w-[762px]">Responsibilities</TableHead>
                            {/* <TableHead className="text-right text-muted-foreground font-medium w-[120px]">Budget</TableHead> */}
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {visiblePartners.length > 0 ? (
                            visiblePartners.map((partner) => (
                                <TableRow key={partner.id} className="border-b border-border">
                                    <TableCell className="font-medium text-foreground py-4 w-[352px]">
                                        {partner.title}
                                    </TableCell>
                                    {!activeProjectId && (
                                        <TableCell className="py-4 text-muted-foreground">
                                            {/* @ts-expect-error: projectName is injected by API map but missing in type */}
                                            {partner.projectName || '-'}
                                        </TableCell>
                                    )}
                                    <TableCell className="py-4 max-w-[762px]">
                                        <div className="flex flex-wrap gap-2">
                                            {(partner.responsibilities || []).map((resp: string, index: number) => (
                                                <Badge
                                                    key={index}
                                                    variant="secondary"
                                                    className="font-normal border-border border bg-transparent text-[#525252] rounded-lg px-3 py-1 text-xs"
                                                >
                                                    {resp}
                                                </Badge>
                                            ))}
                                        </div>
                                    </TableCell>
                                    {/* <TableCell className="text-right text-foreground py-4">
                                        {formatBudget(partner.budget)}
                                    </TableCell> */}
                                </TableRow>
                            ))
                        ) : (
                            <TableRow>
                                <TableCell colSpan={!activeProjectId ? 3 : 2} className="text-center text-muted-foreground py-8">
                                    No partners found
                                </TableCell>
                            </TableRow>
                        )}
                    </TableBody>
                </Table>

                {/* Pagination */}
                {totalItems > 0 && (
                    <div className="flex items-center justify-between mt-6 pt-6 border-t border-border">
                        <div className="text-sm text-muted-foreground">
                            Showing {startIndex + 1}-{endIndex} of {totalItems} Members
                        </div>
                        <div className="flex items-center gap-2">
                            <Button
                                variant="ghost"
                                size="sm"
                                onClick={handlePreviousPage}
                                disabled={currentPage === 1}
                                className="text-muted-foreground hover:text-foreground"
                            >
                                <ChevronLeft className="w-4 h-4 mr-1" />
                                Previous
                            </Button>

                            <div className="flex items-center gap-1">
                                {getPageNumbers().map((page, index) => (
                                    typeof page === 'number' ? (
                                        <Button
                                            key={index}
                                            variant={currentPage === page ? 'outline' : 'ghost'}
                                            size="sm"
                                            onClick={() => handlePageClick(page)}
                                            className={`w-8 h-8 p-0 ${currentPage === page ? 'border-border' : ''}`}
                                        >
                                            {page}
                                        </Button>
                                    ) : (
                                        <span key={index} className="px-2 text-muted-foreground">...</span>
                                    )
                                ))}
                            </div>

                            <Button
                                variant="ghost"
                                size="sm"
                                onClick={handleNextPage}
                                disabled={currentPage === totalPages}
                                className="text-muted-foreground hover:text-foreground"
                            >
                                Next
                                <ChevronRight className="w-4 h-4 ml-1" />
                            </Button>
                        </div>
                    </div>
                )}
            </div>
        </DashboardLayout>
    );
}
