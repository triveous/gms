
import { Select, SelectContent, SelectGroup, SelectItem, SelectLabel, SelectTrigger, SelectValue } from './ui/select'

const DashbaordFilterComponent = () => {
  return (
                <div className="sticky top-16 z-40 bg-[#f8fafc] pb-3 flex items-center justify-between  pt-6 mb-3">
                <div className="flex items-center gap-4">
                    <Select defaultValue="v1">
                        <SelectTrigger className="bg-card h-10">
                            <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                            <SelectGroup>
                                <SelectLabel>Current year (2025 - 2026)</SelectLabel>
                                <SelectItem value="v1">
                                    <span className="text-foreground">Q2 Jul-Sep 2025</span>
                                    <span className="text-muted-foreground/60 font-sans text-sm font-normal leading-[21px] tracking-[0.07px]">(Recent Quarter)</span>
                                </SelectItem>
                                <SelectItem value="v2">
                                    <span className="text-foreground">Q1 Apr-Jun 2025</span>
                                </SelectItem>
                            </SelectGroup>
                            <SelectGroup>
                                <SelectLabel>2024 - 2025</SelectLabel>
                                <SelectItem value="v3">
                                    <span className="text-foreground">Q4 Jan-Apr 2025</span>
                                </SelectItem>
                                <SelectItem value="v4">
                                    <span className="text-foreground">Q3 Oct-Dec 2024</span>
                                </SelectItem>
                                <SelectItem value="v5">
                                    <span className="text-foreground">Q2 Jul-Sep 2024</span>
                                </SelectItem>
                                <SelectItem value="v6">
                                    <span className="text-foreground">Q1 Apr-Jun 2024</span>
                                </SelectItem>
                            </SelectGroup>
                            <SelectGroup>
                                <SelectLabel>Yearly Wise</SelectLabel>
                                <SelectItem value="v7">
                                    <span className="text-foreground">2025 - 2026</span>
                                    {" "}
                                    <span className="text-muted-foreground/60 font-sans text-sm font-normal leading-[21px] tracking-[0.07px]">(This Year)</span>
                                </SelectItem>
                                <SelectItem value="v8">
                                    <span className="text-foreground">2024 - 2025</span>
                                </SelectItem>
                            </SelectGroup>
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
  )
}

export default DashbaordFilterComponent