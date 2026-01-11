import { Card, CardHeader, CardTitle, CardContent, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { SectionWrapper } from '@/components/SectionWrapper';
import { Badge } from '@/components/ui/badge';
import { ChevronRight, FileText } from 'lucide-react';
import { useChatContext } from '@/contexts/ChatContext';

export interface Partner {
    id: string;
    title: string;
    responsibility?: string | null;
}

export interface Contributor {
    id: string;
    title: string;
    role: string;
}

interface OrgMembersProps {
    partners?: Partner[];
    contributors?: Contributor[];
}

const OrgMembers = ({ partners = [], contributors = [] }: OrgMembersProps) => {
    
    const { toggleChat } = useChatContext();

  return (
                <SectionWrapper 
                title="People & Partners"
                contentClassName="grid grid-cols-2 gap-4"
            >
                <Card className="p-0 gap-0">
                    <CardHeader className="flex flex-row items-center justify-between p-6">
                        <CardTitle className="text-base font-bold text-muted-foreground">Academic & Industry Partners</CardTitle>
                        <Button onClick={toggleChat} variant="outline" size="sm" className="h-8 gap-2 text-muted-foreground font-normal">
                            Ask AI <FileText className="h-4 w-4" />
                        </Button>
                    </CardHeader>
                    <div className="mx-6 h-px bg-border" />
                    <CardContent className="p-0">
                        {partners.length > 0 ? (
                            partners.slice(0, 5).map((partner, index) => (
                                <div key={partner.id || index}>
                                    {index > 0 && <div className="mx-6 h-px bg-border" />}
                                    <div className="p-6 flex flex-col gap-3">
                                        <div className="font-semibold text-foreground text-lg">{partner.title}</div>
                                        <div className="flex flex-wrap gap-2">
                                            {partner.responsibility && (
                                                <Badge variant="secondary" className="font-normal border-border border bg-transparent text-muted-foreground hover:bg-secondary/80 rounded-lg px-3 py-1">
                                                    {partner.responsibility}
                                                </Badge>
                                            )}
                                        </div>
                                    </div>
                                </div>
                            ))
                        ) : (
                            <div className="p-6 text-center text-muted-foreground">No partners found</div>
                        )}
                    </CardContent>
                    {/* <CardFooter className="p-6">
                        <Button variant="outline" className="w-full justify-between group h-12 text-base font-medium">
                            <span />
                            <span>View all</span>
                            <ChevronRight className="h-5 w-5 text-muted-foreground group-hover:text-foreground" />
                        </Button>
                    </CardFooter> */}
                </Card>

                <Card className="p-0 gap-0">
                    <CardHeader className="flex flex-row items-center justify-between p-6">
                        <CardTitle className="text-base font-bold text-muted-foreground">Lead Investigators and Partners</CardTitle>
                        <Button onClick={toggleChat} variant="outline" size="sm" className="h-8 gap-2 text-muted-foreground font-normal">
                            Ask AI <FileText className="h-4 w-4" />
                        </Button>
                    </CardHeader>
                    <div className="mx-6 h-px bg-border" />
                    <CardContent className="p-0">
                        {contributors.length > 0 ? (
                            contributors.slice(0, 5).map((person, index) => (
                                <div key={person.id || index}>
                                    {index > 0 && <div className="mx-6 h-px bg-border" />}
                                    <div className="p-6 flex flex-col gap-2">
                                        <div className="flex flex-wrap items-center gap-2 mb-1">
                                            <span className="font-semibold text-foreground text-lg">{person.title}</span>
                                            {person.role && (
                                                <Badge variant="secondary" className="font-normal border-border border bg-transparent text-muted-foreground rounded-lg px-2 py-0.5">
                                                    {person.role}
                                                </Badge>
                                            )}
                                        </div>
                                        {/* <div className="text-sm text-muted-foreground leading-relaxed">
                                        professor</div> */}
                                        {/* Details are not currently provided in the API response */}
                                    </div>
                                </div>
                            ))
                        ) : (
                             <div className="p-6 text-center text-muted-foreground">No contributors found</div>
                        )}
                    </CardContent>
                    {/* <CardFooter className="p-6">
                        <Button variant="outline" className="w-full justify-between group h-12 text-base font-medium">
                            <span />
                            <span>View all</span>
                            <ChevronRight className="h-5 w-5 text-muted-foreground group-hover:text-foreground" />
                        </Button>
                    </CardFooter> */}
                </Card>
            </SectionWrapper>
  )
}

export default OrgMembers