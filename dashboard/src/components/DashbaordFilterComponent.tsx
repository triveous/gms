
import { useMemo, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { UploadedFilesDialog } from './UploadedFilesDialog';
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
  showUploadedFiles?: boolean;
}

const DashboardFilterComponent = ({ 
  quartersList, 
  selectedPeriod, 
  setSelectedPeriod, 
  comparisonQuarter, 
  setComparisonQuarter,
  showUploadedFiles = true
}: DashboardFilterProps) => {
  const { projectId } = useParams();


  // flatten for easier filtering
  const allQuarters = useMemo(() => {
    return quartersList
      .filter(g => g.label !== 'Yearly Wise')
      .flatMap(g => g.items);
  }, [quartersList]);

  const allYears = useMemo(() => {
    const yearly = quartersList.find(g => g.label === 'Yearly Wise');
    return yearly ? yearly.items : [];
  }, [quartersList]);

  const secondSelectOptions = useMemo(() => {
    if (!selectedPeriod) return [];

    let options = [];

    // if it starts with 'Q', it's quarter
    if (selectedPeriod.startsWith('Q')) {
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

  // useEffect(() => {
  //   if (quartersList && quartersList.length > 0 && quartersList[0].items && quartersList[0].items.length > 0) {
  //       setSelectedPeriod(quartersList[0].items[0].value);
  //   }
  // },[])

  return (
    <div className="sticky top-16 z-40 bg-[#f8fafc] pb-3 flex items-center justify-between pt-6 mb-3">

      {/* ---------------- FIRST SELECT ---------------- */}
      <div className="flex items-center gap-4">
        <Select onValueChange={setSelectedPeriod} defaultValue={quartersList[0]?.items[0]?.value}>
          <SelectTrigger className="bg-card h-10">
            <SelectValue placeholder="Select Period" />
          </SelectTrigger>

          <SelectContent>
            {quartersList
              .filter(group => group.label !== 'Yearly Wise')
              .map(group => (
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
        <Select disabled={!selectedPeriod || secondSelectOptions.length === 0} onValueChange={setComparisonQuarter} value={comparisonQuarter}>
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

      {/* ---------------- THIRD SELECT (Uploaded Files) ---------------- */}
      {!projectId && showUploadedFiles && <UploadedFilesDialog />}

    </div>
  );
};

export default DashboardFilterComponent;
