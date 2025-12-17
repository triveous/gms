
// import { Select, SelectContent, SelectGroup, SelectItem, SelectLabel, SelectTrigger, SelectValue } from './ui/select'

// const DashbaordFilterComponent = () => {
//   return (
//                 <div className="sticky top-16 z-40 bg-[#f8fafc] pb-3 flex items-center justify-between  pt-6 mb-3">
//                 <div className="flex items-center gap-4">
//                     <Select defaultValue="v1">
//                         <SelectTrigger className="bg-card h-10">
//                             <SelectValue />
//                         </SelectTrigger>
//                         <SelectContent>
//                             <SelectGroup>
//                                 <SelectLabel>Current year (2025 - 2026)</SelectLabel>
//                                 <SelectItem value="v1">
//                                     <span className="text-foreground">Q2 Jul-Sep 2025</span>
//                                     <span className="text-muted-foreground/60 font-sans text-sm font-normal leading-[21px] tracking-[0.07px]">(Recent Quarter)</span>
//                                 </SelectItem>
//                                 <SelectItem value="v2">
//                                     <span className="text-foreground">Q1 Apr-Jun 2025</span>
//                                 </SelectItem>
//                             </SelectGroup>
//                             <SelectGroup>
//                                 <SelectLabel>2024 - 2025</SelectLabel>
//                                 <SelectItem value="v3">
//                                     <span className="text-foreground">Q4 Jan-Apr 2025</span>
//                                 </SelectItem>
//                                 <SelectItem value="v4">
//                                     <span className="text-foreground">Q3 Oct-Dec 2024</span>
//                                 </SelectItem>
//                                 <SelectItem value="v5">
//                                     <span className="text-foreground">Q2 Jul-Sep 2024</span>
//                                 </SelectItem>
//                                 <SelectItem value="v6">
//                                     <span className="text-foreground">Q1 Apr-Jun 2024</span>
//                                 </SelectItem>
//                             </SelectGroup>
//                             <SelectGroup>
//                                 <SelectLabel>Yearly Wise</SelectLabel>
//                                 <SelectItem value="v7">
//                                     <span className="text-foreground">2025 - 2026</span>
//                                     {' '}
//                                     <span className="text-muted-foreground/60 font-sans text-sm font-normal leading-[21px] tracking-[0.07px]">(This Year)</span>
//                                 </SelectItem>
//                                 <SelectItem value="v8">
//                                     <span className="text-foreground">2024 - 2025</span>
//                                 </SelectItem>
//                             </SelectGroup>
//                         </SelectContent>
//                     </Select>
                    
//                     <Select defaultValue="q1">
//                         <SelectTrigger className="h-10 bg-card">
//                             <SelectValue />
//                         </SelectTrigger>
//                         <SelectContent>
//                             <SelectItem value="q1">
//                                 <span className="text-foreground"><span className="text-muted-foreground/60 font-sans text-sm font-normal leading-[21px] tracking-[0.07px]">Compare to</span> Q1 | Apr-Jun 2025</span>
//                             </SelectItem>
//                         </SelectContent>
//                     </Select>
//                 </div>
//                 <Select>
//                     <SelectTrigger className="h-10 bg-card text-foreground">
//                         <div className="flex items-center gap-2">
//                             <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
//                                 <path d="M14 10v2.667A1.333 1.333 0 0112.667 14H3.333A1.333 1.333 0 012 12.667V10m2.667-4L8 9.333m0 0L11.333 6M8 9.333V2" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
//                             </svg>
//                             <SelectValue placeholder="Download Reports" />
//                         </div>
//                     </SelectTrigger>
//                     <SelectContent>
//                         <SelectItem value="pdf">Download as PDF</SelectItem>
//                         <SelectItem value="excel">Download as Excel</SelectItem>
//                         <SelectItem value="csv">Download as CSV</SelectItem>
//                     </SelectContent>
//                 </Select>
//             </div>
//   )
// }

// export default DashbaordFilterComponent





import { FileText, Download } from 'lucide-react';
import { useMemo, useEffect } from 'react';
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
  SelectValue
} from './ui/select';

interface DashboardFilterProps {
  quartersList: any[];
  selectedPeriod: string;
  setSelectedPeriod: (value: string) => void;
  comparisonQuarter: string;
  setComparisonQuarter: (value: string) => void;
}

const DashboardFilterComponent = ({ quartersList, selectedPeriod, setSelectedPeriod, comparisonQuarter, setComparisonQuarter }: DashboardFilterProps) => {


  // flatten for easier filtering
  const allQuarters = useMemo(() => {
    return quartersList
      .filter(g => g.label !== "Yearly Wise")
      .flatMap(g => g.items);
  }, [quartersList]);

  const allYears = useMemo(() => {
    const yearly = quartersList.find(g => g.label === "Yearly Wise");
    return yearly ? yearly.items : [];
  }, [quartersList]);

  const secondSelectOptions = useMemo(() => {
    if (!selectedPeriod) return [];

    let options = [];

    // if it starts with "Q", it's quarter
    if (selectedPeriod.startsWith("Q")) {
      options = allQuarters;
    } else {
      // else it's year
      options = allYears;
    }

    // Logic 1: Filter out the option selected in 1st select
    return options.filter((opt: { value: string; title: string }) => opt.value !== selectedPeriod);

  }, [selectedPeriod, allQuarters, allYears]);

  // Logic 2: Discard comparison selection if it's no longer valid (e.g. mode change or same value)
  useEffect(() => {
    if (comparisonQuarter) {
        const isValid = secondSelectOptions.some((opt: { value: string; title: string }) => opt.value === comparisonQuarter);
        if (!isValid) {
            setComparisonQuarter('');
        }
    }
  }, [secondSelectOptions, comparisonQuarter, setComparisonQuarter]);

  useEffect(() => {
    if (quartersList && quartersList.length > 0 && quartersList[0].items && quartersList[0].items.length > 0) {
        setSelectedPeriod(quartersList[0].items[0].value);
    }
  },[])

  return (
    <div className="sticky top-16 z-40 bg-[#f8fafc] pb-3 flex items-center justify-between pt-6 mb-3">

      {/* ---------------- FIRST SELECT ---------------- */}
      <div className="flex items-center gap-4">
        <Select onValueChange={setSelectedPeriod} defaultValue={quartersList[0]?.items[0]?.value}>
          <SelectTrigger className="bg-card h-10">
            <SelectValue placeholder="Select Period" />
          </SelectTrigger>

          <SelectContent>
            {quartersList.map(group => (
              <SelectGroup key={group.label}>
                <SelectLabel>{group.label}</SelectLabel>

                {group.items.map(item => (
                  <SelectItem key={item.title} value={item.value}>
                    <div className="flex">
                      <span className="text-foreground">{item.title}</span>
                      {item.description && (
                        <span className="text-muted-foreground/60 font-sans text-sm">
                          ({item.description})
                        </span>
                      )}
                    </div>
                  </SelectItem>
                ))}
              </SelectGroup>
            ))}
          </SelectContent>
        </Select>

        {/* ---------------- SECOND SELECT ---------------- */}
        <Select disabled={!selectedPeriod} onValueChange={setComparisonQuarter} value={comparisonQuarter}>
          <SelectTrigger className="h-10 bg-card">
            <SelectValue placeholder="Compare to" />
          </SelectTrigger>

          <SelectContent>
            {secondSelectOptions.map(item => (
              <SelectItem key={item.value} value={item.value}>
                {item.title}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* ---------------- THIRD SELECT (Download) ---------------- */}
      <Select>
        <SelectTrigger className="h-10 bg-card text-foreground">
          <div className="flex items-center gap-2">
            <SelectValue placeholder="Download Reports" />
          </div>
        </SelectTrigger>

        <SelectContent align="end" className="w-[280px]">
          <SelectGroup>
            <SelectLabel className="font-normal text-xs text-muted-foreground py-2 px-3">Quarterly progress reports</SelectLabel>
            {[
              'Q2 Jul-Sep 2025',
              'Q1 Apr-Jun 2025',
              'Q4 Jan-Mar 2024',
              'Q3 Oct-Dec 2024',
              'Q2 Jul-Sep 2024',
              'Q1 Apr-Jun 2024'
            ].map((report) => (
              <SelectItem key={report} value={report} className="cursor-pointer focus:bg-accent py-2 px-3">
                <div className="flex items-center justify-between w-full gap-4">
                  <div className="flex items-center gap-3 text-foreground font-medium text-sm">
                    <FileText className="w-4 h-4 stroke-[1.5px]" />
                    <span>{report}</span>
                  </div>
                  <Download className="w-4 h-4 text-muted-foreground stroke-[1.5px]" />
                </div>
              </SelectItem>
            ))}
          </SelectGroup>
          <div className="h-[1px] bg-border mx-1 my-1" />
          <SelectGroup>
            <SelectLabel className="font-normal text-xs text-muted-foreground py-2 px-3">Yearly Plans</SelectLabel>
            {[
              '2025 2026',
              '2024 2025'
            ].map((plan) => (
              <SelectItem key={plan} value={plan} className="cursor-pointer focus:bg-accent py-2 px-3">
                <div className="flex items-center justify-between w-full gap-4">
                  <div className="flex items-center gap-3 text-foreground font-medium text-sm">
                    <FileText className="w-4 h-4 stroke-[1.5px]" />
                    <span>{plan}</span>
                  </div>
                  <Download className="w-4 h-4 text-muted-foreground stroke-[1.5px]" />
                </div>
              </SelectItem>
            ))}
          </SelectGroup>
          <div className="h-[1px] bg-border mx-1 my-1" />
          <SelectGroup>
            <SelectLabel className="font-normal text-xs text-muted-foreground py-2 px-3">Dashboard (Current view)</SelectLabel>
            <SelectItem value="pdf" className="cursor-pointer focus:bg-accent py-2 px-3">
              <div className="flex items-center justify-between w-full gap-4">
                <div className="flex items-center gap-3 text-foreground font-medium text-sm">
                  <FileText className="w-4 h-4 stroke-[1.5px]" />
                  <span>Download as PDF</span>
                </div>
                <Download className="w-4 h-4 text-muted-foreground stroke-[1.5px]" />
              </div>
            </SelectItem>
          </SelectGroup>
        </SelectContent>
      </Select>

    </div>
  );
};

export default DashboardFilterComponent;
