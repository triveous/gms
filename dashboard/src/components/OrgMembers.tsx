import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ChevronRight, Building2, UserSearch } from 'lucide-react';
import { useNavigate, useParams } from 'react-router-dom';

export interface Partner {
    id: string;
    title: string;
    responsibilities?: string[];
    budget?: number | string;
}

export interface Contributor {
    id: string;
    title: string;
    designation: string;
    role: string;
    position?: string;
    institution?: string;
    email?: string;
}

interface OrgMembersProps {
    partners?: Partner[];
    contributors?: Contributor[];
    quarter?: string;
}

const MAX_VISIBLE_RESPONSIBILITIES = 4;
const MAX_VISIBLE_PARTNERS = 6;
const MAX_VISIBLE_CONTRIBUTORS = 6;

const OrgMembers = ({ partners = [], contributors = [], quarter }: OrgMembersProps) => {
    const navigate = useNavigate();
    const { grantId, projectId } = useParams<{ grantId: string; projectId?: string }>();

    const getNavigationUrl = (type: 'partners' | 'contributors') => {
        const baseUrl = projectId 
            ? `/${grantId}/${projectId}/${type}`
            : `/${grantId}/${type}`;
        
        return quarter ? `${baseUrl}?quarter=${quarter}` : baseUrl;
    };

    const handleViewAllPartners = () => {
        navigate(getNavigationUrl('partners'));
    };

    const handleViewAllContributors = () => {
        navigate(getNavigationUrl('contributors'));
    };

    const visiblePartners = partners.slice(0, MAX_VISIBLE_PARTNERS);
    const visibleContributors = contributors.slice(0, MAX_VISIBLE_CONTRIBUTORS);

    return (
        <div className="flex flex-col gap-8 mt-8">
            {/* Academic & Industry Partners Section */}
            <div className="flex flex-col gap-4">
                <div className="flex items-center justify-between">
                    <h2 className="text-xl font-bold text-foreground">Academic & Industry Partners</h2>
                    {partners.length > MAX_VISIBLE_PARTNERS && (
                        <Button 
                            variant="outline" 
                            className="shadow-none rounded-md p-[7.5px] bg-white border-[#E2E8F0] hover:bg-gray-50 gap-3 w-[156px] h-[36px] text-[#020617] text-sm font-medium leading-[21px] tracking-[0.07px] text-center"
                            onClick={handleViewAllPartners}
                        >
                            View all
                            <ChevronRight className="w-5 h-5" />
                        </Button>
                    )}
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                    {visiblePartners.length > 0 ? (
                        visiblePartners.map((partner, index) => {
                            const responsibilities = partner.responsibilities || [];
                            const visibleResponsibilities = responsibilities.slice(0, MAX_VISIBLE_RESPONSIBILITIES);
                            const hiddenCount = responsibilities.length - MAX_VISIBLE_RESPONSIBILITIES;

                            return (
                                <Card key={partner.id || index} className="p-5 gap-0 rounded shadow-none">
                                    <div className="font-semibold text-foreground text-base mb-3">
                                        {partner.title}
                                    </div>
                                    <div className="flex flex-wrap gap-2">
                                        {visibleResponsibilities.map((resp, respIndex) => (
                                            <Badge 
                                                key={respIndex}
                                                variant="secondary" 
                                                className="font-normal border-border border bg-transparent text-[#525252] hover:bg-secondary/80 rounded-lg px-3 py-1 text-xs"
                                            >
                                                {resp}
                                            </Badge>
                                        ))}
                                        {hiddenCount > 0 && (
                                            <Badge 
                                                variant="secondary" 
                                                className="font-medium border-border border bg-transparent text-[#525252] hover:bg-secondary/80 rounded-lg px-3 py-1 text-xs"
                                            >
                                                +{hiddenCount} More
                                            </Badge>
                                        )}
                                    </div>
                                </Card>
                            );
                        })
                    ) : (
                        <div className="col-span-2 flex flex-col items-center justify-center py-[16px] w-[292px] gap-[16px] text-center m-auto">
                            <Building2 className="w-[44px] h-[44px] text-[#475569]" strokeWidth={1.5} />
                            <div className='flex flex-col gap-[4px]'>
                                <h3 className="text-base font-semibold text-[#0F172A] mb-1">No information available</h3>
                                <p className="text-sm text-[#0F172A]">
                                    No partner information is currently available for the projects.
                                </p>
                            </div>
                        </div>
                    )}
                </div>
            </div>

            {/* People & teams Section */}
            <div className="flex flex-col gap-4">
                <div className="flex items-center justify-between">
                    <h2 className="text-xl font-bold text-foreground">People & teams</h2>
                    {contributors.length > MAX_VISIBLE_CONTRIBUTORS && (
                        <Button 
                            variant="outline" 
                            className="shadow-none rounded-lg p-[7.5px] bg-white border-[#E2E8F0] hover:bg-gray-50 gap-3 w-[156px] h-[36px] text-[#020617] text-sm font-medium leading-[21px] tracking-[0.07px] text-center"
                            onClick={handleViewAllContributors}
                        >
                            View all
                            <ChevronRight className="w-5 h-5" />
                        </Button>
                    )}
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                    {visibleContributors.length > 0 ? (
                        visibleContributors.map((person, index) => {
                            // Build the details string
                            const details = [
                                person.designation,
                                person.institution,
                                person.email
                            ].filter(Boolean).join(' • ');

                            return (
                                <Card key={person.id || index} className="p-5 gap-0 rounded shadow-none">
                                    <div className="flex flex-wrap items-center gap-2 mb-2">
                                        <span className="font-semibold text-foreground text-base">
                                            {person.title}
                                        </span>
                                        {person.role && (
                                            <Badge 
                                                variant="secondary" 
                                                className="font-normal border-border border bg-transparent text-muted-foreground rounded-full px-3 py-0.5 text-xs"
                                            >
                                                {person.role}
                                            </Badge>
                                        )}
                                    </div>
                                    {details && (
                                        <div className="text-sm text-muted-foreground leading-relaxed">
                                            {details}
                                        </div>
                                    )}
                                </Card>
                            );
                        })
                    ) : (
                        <div className="col-span-2 flex flex-col items-center justify-center py-[16px] w-[292px] gap-[16px] text-center m-auto">
                            <UserSearch className="w-[44px] h-[44px] text-[#475569]" strokeWidth={1.5} />
                            <div className='flex flex-col gap-[4px]'>
                                <h3 className="text-base font-semibold text-[#0F172A] mb-1">No information available</h3>
                                <p className="text-sm text-[#0F172A]">
                                    No people or team details are currently available for the projects.
                                </p>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

export default OrgMembers