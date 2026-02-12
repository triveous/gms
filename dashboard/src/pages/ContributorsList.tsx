import { useParams, useSearchParams } from 'react-router-dom';
import { useFrappePostCall } from 'frappe-react-sdk';
import { useMemo, useState, useEffect } from 'react';
import { ChevronLeft, ChevronRight, ArrowUpDown, Sparkles, Filter, ListFilter, Check } from 'lucide-react';
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

export default function ContributorsList({ scope = 'grant' }: { scope?: 'grant' | 'project' }) {
    const { grantId, projectId } = useParams<{ grantId: string; projectId?: string }>();
    const [searchParams] = useSearchParams();
    const quarter = searchParams.get('quarter');
    
    const [currentPage, setCurrentPage] = useState(1);
    const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');
    const [roleFilter, setRoleFilter] = useState<string | null>(null);
    const [projectFilter, setProjectFilter] = useState<string | null>(null);
    const [sortByType, setSortByType] = useState<'name' | null>(null);

    // Only use projectId if we are explicitly in project scope
    const activeProjectId = scope === 'project' ? projectId : undefined;



    // --- GRANT SCOPE DATA FETCHING (New API) ---
    const { call: fetchGrantContributors, result: grantContributorsResult } = useFrappePostCall('gms.api.projects.fetch_grant_contributors');
    const { call: fetchProjectContributors, result: projectContributorsResult } = useFrappePostCall('gms.api.project.fetch_project_contributors');

    useEffect(() => {
        if (activeProjectId && quarter) {
            // Project Scope
            fetchProjectContributors({
                grant_id: grantId,
                project_id: activeProjectId,
                quarter_value: quarter,
                page: currentPage,
                page_size: ITEMS_PER_PAGE,
                role_filter: roleFilter || undefined,
                sort_by: sortByType === 'name' ? 'name' : undefined
            });
        } else if (grantId && quarter) {
            // Grant Scope
            fetchGrantContributors({
                grant_id: grantId,
                quarter_value: quarter,
                page: currentPage,
                page_size: ITEMS_PER_PAGE,
                role_filter: roleFilter || undefined,
                project_id: projectFilter || undefined,
                sort_by: sortByType === 'name' ? 'name' : undefined
            });
        }
    }, [grantId, quarter, currentPage, activeProjectId, fetchGrantContributors, fetchProjectContributors, roleFilter, projectFilter, sortByType, sortOrder]);

    // Extract contributors from the response
    const contributors = useMemo(() => {
        if (activeProjectId) {
            // Project context (New API Logic)
            if (!projectContributorsResult?.message?.contributors_map) return [];
            return Object.values(projectContributorsResult.message.contributors_map).flat().map((c: any) => ({
                id: c.id,
                title: c.title,
                projectName: c.project_name,
                role: c.role,
                designation: c.designation,
                position: c.position,
                institution: c.institution,
                email: c.email
            }));
        } else {
            // Grant context (New API Logic)
            if (!grantContributorsResult?.message?.contributors_map) return [];
            
            // Flatten the map values into a single array
            return Object.values(grantContributorsResult.message.contributors_map).flat().map((c: any) => ({
                id: c.id,
                title: c.title,
                projectName: c.project_name,
                role: c.role,
                designation: c.designation,
                position: c.position,
                institution: c.institution,
                email: c.email
            }));
        }
    }, [activeProjectId, grantContributorsResult, projectContributorsResult]);

    // Extract All Roles
    const allRoles: string[] = useMemo(() => {
        if (activeProjectId) {
            return projectContributorsResult?.message?.all_roles || [];
        } else {
            return grantContributorsResult?.message?.all_roles || [];
        }
    }, [activeProjectId, grantContributorsResult, projectContributorsResult]);

    // Extract All Projects
    const allProjects: { id: string; name: string }[] = useMemo(() => {
        return grantContributorsResult?.message?.all_projects || [];
    }, [grantContributorsResult]);

    // Total Items logic
    const totalItems = useMemo(() => {
        if (activeProjectId) {
             return projectContributorsResult?.message?.total_count || 0;
        } else {
             return grantContributorsResult?.message?.total_count || 0;
        }
    }, [activeProjectId, grantContributorsResult, projectContributorsResult]);

    // Pagination Logic
    const totalPages = useMemo(() => {
        if (activeProjectId) {
             return projectContributorsResult?.message?.total_pages || 1;
        } else {
             return grantContributorsResult?.message?.total_pages || 1;
        }
    }, [activeProjectId, grantContributorsResult, projectContributorsResult]);

    // Derived list for render
    const visibleContributors = contributors;

    // Pagination display variables
    const startIndex = (currentPage - 1) * ITEMS_PER_PAGE;
    const endIndex = Math.min(startIndex + ITEMS_PER_PAGE, totalItems);

    // Handlers
    const handleSort = () => {
        setSortByType('name');
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

    // Generate page numbers to display logic (reused)
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
                    <h1 className="text-xl font-semibold text-foreground">People & teams</h1>
                </div>

                {/* Table */}
                <Table>
                    <TableHeader>
                        <TableRow className="border-b border-border">
                            <TableHead className="w-[300px]">
                                <button 
                                    onClick={handleSort}
                                    className="flex items-center gap-2 text-muted-foreground font-medium hover:text-foreground"
                                >
                                    Name
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
                                        <DropdownMenuContent align="start" className='border-border rounded-sm'>
                                            {allProjects.map((project) => {
                                                const isChecked = projectFilter === project.id;
                                                return (
                                                    <DropdownMenuCheckboxItem
                                                        key={project.id}
                                                        className="border-border pl-2 [&>span]:hidden cursor-pointer"
                                                        checked={isChecked}
                                                        onCheckedChange={(checked) => {
                                                            setProjectFilter(checked ? project.id : null);
                                                            setCurrentPage(1);
                                                        }}
                                                    >
                                                        <div className="flex items-center gap-2">
                                                            <div className={`flex h-4 w-4 items-center justify-center rounded-[5px] border ${isChecked ? 'bg-primary border-primary text-primary-foreground' : 'border-muted-foreground/30'}`}>
                                                                {isChecked && <Check className="h-3 w-3 bg-white rounded-[5px] border-[1px] border-border" />}
                                                            </div>
                                                            <span>{project.name}</span>
                                                        </div>
                                                    </DropdownMenuCheckboxItem>
                                                );
                                            })}
                                        </DropdownMenuContent>
                                    </DropdownMenu>
                                </TableHead>
                            )}
                            <TableHead className="text-muted-foreground font-medium">
                                <DropdownMenu>
                                    <DropdownMenuTrigger asChild>
                                        <button className="flex items-center gap-2 text-muted-foreground font-medium hover:text-foreground">
                                            Role
                                            <ListFilter className="w-4 h-4" />
                                        </button>
                                    </DropdownMenuTrigger>
                                    <DropdownMenuContent align="start" className='border-border rounded-sm'>
                                        {allRoles.map((role) => {
                                            const isChecked = roleFilter === role;
                                            return (
                                                <DropdownMenuCheckboxItem
                                                    key={role}
                                                    className="border-border pl-2 [&>span]:hidden cursor-pointer"
                                                    checked={isChecked}
                                                    onCheckedChange={(checked) => {
                                                        setRoleFilter(checked ? role : null);
                                                        setCurrentPage(1); // Reset page on filter
                                                    }}
                                                >
                                                    <div className="flex items-center gap-2">
                                                        <div className={`flex h-4 w-4 items-center justify-center rounded-[5px] border ${isChecked ? 'bg-primary border-primary text-primary-foreground' : 'border-muted-foreground/30'}`}>
                                                            {isChecked && <Check className="h-3 w-3 bg-white rounded-[5px] border-[1px] border-border" />}
                                                        </div>
                                                        <span>{role}</span>
                                                    </div>
                                                </DropdownMenuCheckboxItem>
                                            );
                                        })}
                                    </DropdownMenuContent>
                                </DropdownMenu>
                            </TableHead>
                            <TableHead className="text-muted-foreground font-medium">Designation</TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {visibleContributors.length > 0 ? (
                            visibleContributors.map((person) => {
                                return (
                                    <TableRow key={person.id} className="border-b border-border">
                                        <TableCell className="font-medium text-foreground py-4">
                                            {person.title}
                                        </TableCell>
                                        {!activeProjectId && (
                                            <TableCell className="py-4 text-muted-foreground">
                                            {/* @ts-expect-error: projectName is injected by API map but missing in type */}
                                            {person.projectName || '-'}
                                            </TableCell>
                                        )}
                                        <TableCell className="py-4 text-muted-foreground">
                                            {person.role && (
                                                <Badge 
                                                    variant="secondary" 
                                                    className="font-normal border-border border bg-transparent text-muted-foreground rounded-full px-3 py-0.5 text-xs"
                                                >
                                                    {person.role}
                                                </Badge>
                                            )}
                    
                                        </TableCell>
                                        <TableCell className="py-4">
                                            {person.designation}
                                        </TableCell>
                                        
                                    </TableRow>
                                );
                            })
                        ) : (
                            <TableRow>
                                <TableCell colSpan={!activeProjectId ? 4 : 3} className="text-center text-muted-foreground py-8">
                                    No contributors found
                                </TableCell>
                            </TableRow>
                        )}
                    </TableBody>
                </Table>

                {/* Pagination */}
                {totalItems > 0 && (
                    <div className="flex items-center justify-between mt-6 pt-6 border-t border-border">
                        <div className="text-sm text-muted-foreground">
                            Showing {startIndex + 1}-{endIndex} of {totalItems} People
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
