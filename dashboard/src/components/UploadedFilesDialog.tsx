
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Dialog,
  DialogContent,
  DialogTitle,
  DialogTrigger,
  DialogClose
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Download, ArrowUpDown, ListFilter, X, Check } from 'lucide-react';
import { useParams } from 'react-router-dom';
import { useFrappeGetCall } from 'frappe-react-sdk';
import React, { useState } from 'react';

interface DPRFile {
    file_id: string;
    file_name: string;
    uploaded_on: string;
    download_link: string;
    file_type: string;
    start_date?: string;
    end_date?: string;
}

const formatDate = (dateStr?: string) => {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    if (isNaN(date.getTime())) return dateStr;
    const day = String(date.getDate()).padStart(2, '0');
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const year = date.getFullYear();
    return `${day}-${month}-${year}`;
};

export function UploadedFilesDialog() {
  const { grantId } = useParams<{ grantId: string }>();
  const [selectedTypes, setSelectedTypes] = useState<string[]>([]);
  const [sortBy, setSortBy] = useState<string | null>(null);
  
  const { data, isLoading } = useFrappeGetCall(
    'gms.api.grant.fetch_grant_dpr_files',
    { 
        grant_id: grantId,
        file_types: selectedTypes.length > 0 ? selectedTypes.join(',') : undefined,
        sort_by: sortBy || undefined
    },
    grantId ? undefined : null
  );

  const dprFiles = data?.message?.files || [];
  const filterOptions = data?.message?.file_types || [];

  const toggleType = (type: string) => {
    setSelectedTypes(prev => 
      prev.includes(type) 
        ? prev.filter(t => t !== type) 
        : [...prev, type]
    );
  };

  const toggleSort = (key: string) => {
    setSortBy(prev => prev === key ? null : key);
  };

  const handleDownload = (link: string) => {
    if (!link) return;
    window.open(link, '_blank');
  };

  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button variant="outline" className="h-10 bg-card text-foreground font-normal min-w-[140px] justify-between">
            <Download className="h-3.5 w-3.5" />
           Uploaded files
           <span className="sr-only">Open uploaded files</span>
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[1000px] p-0 gap-0 overflow-hidden rounded-xl" showCloseButton={false}>
        <div className="flex items-center justify-between p-6 pb-2">
            <DialogTitle className="text-xl font-semibold">Uploaded files</DialogTitle>
            <DialogClose className="h-9 rounded-md px-3 bg-secondary/50 hover:bg-secondary/70 text-secondary-foreground text-sm font-medium transition-colors flex items-center gap-2">
                <X className="h-4 w-4" />
                Close
            </DialogClose>
        </div>

        <div className="p-6 pt-4">
            <div className="rounded-md">
                <Table>
                    <TableHeader>
                        <TableRow className='text-[#020617]'>
                            <TableHead className="w-[150px] p-2">
                                <button 
                                    className={`flex items-center gap-2 hover:text-foreground text-[#020617] ${sortBy === 'file_name' ? 'font-semibold' : ''}`}
                                    onClick={() => toggleSort('file_name')}
                                >
                                    File name
                                    <ArrowUpDown className="h-3 w-3" />
                                </button>
                            </TableHead>
                            <TableHead className="w-[140px] p-2">
                                <DropdownMenu>
                                    <DropdownMenuTrigger asChild>
                                        <button className="flex items-center gap-2 hover:text-foreground text-[#020617] outline-none">
                                            Document type
                                            <ListFilter className="h-3 w-3" />
                                        </button>
                                    </DropdownMenuTrigger>
                                    <DropdownMenuContent align="start" className="w-[300px] p-1 bg-white rounded-lg shadow-xl border border-slate-200">
                                        {filterOptions.map((option) => (
                                            <DropdownMenuItem
                                                key={option}
                                                onSelect={(e) => {
                                                    e.preventDefault();
                                                    toggleType(option);
                                                }}
                                                className="flex items-center gap-3 px-3 py-2 text-[15px] font-medium text-slate-800 hover:bg-slate-50 rounded-md cursor-pointer focus:bg-slate-50 focus:text-slate-900"
                                            >
                                                <div className={`w-[18px] h-[18px] rounded border flex items-center justify-center transition-colors ${
                                                    selectedTypes.includes(option) 
                                                        ? 'border-slate-300 text-primary-foreground' 
                                                        : 'border-slate-300 bg-white'
                                                }`}>
                                                    {selectedTypes.includes(option) && <Check className="w-3.5 h-3.5 stroke-[3]" />}
                                                </div>
                                                {option}
                                            </DropdownMenuItem>
                                        ))}
                                    </DropdownMenuContent>
                                </DropdownMenu>
                            </TableHead>
                            <TableHead className="w-[196px] p-2 text-[#020617]">
                                Assigned Timeline
                            </TableHead>
                            <TableHead className="w-[200px] p-2 text-[#020617]">
                                Uploaded on
                            </TableHead>
                            <TableHead className="w-[120px] p-2 text-[#020617]">
                                Actions
                            </TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {isLoading ? (
                            <TableRow>
                                <TableCell colSpan={5} className="h-24 text-center">
                                    Loading files...
                                </TableCell>
                            </TableRow>
                        ) : dprFiles.length === 0 ? (
                            <TableRow>
                                <TableCell colSpan={5} className="h-24 text-center">
                                    No files found.
                                </TableCell>
                            </TableRow>
                        ) : (
                            dprFiles.map((file: DPRFile) => (
                                <TableRow key={file.file_id}>
                                    <TableCell className="font-medium text-foreground p-2">
                                        {file.file_name}
                                    </TableCell>
                                    <TableCell className='p-2'>
                                        <Badge variant="secondary" className="font-normal border-border bg-secondary/50 text-[#334155] hover:bg-secondary/60 rounded-md">
                                            {file.file_type}
                                        </Badge>
                                    </TableCell>
                                    <TableCell className="text-[#020617] font-[14px] p-2">
                                        {file.start_date && file.end_date 
                                            ? `${formatDate(file.start_date)} → ${formatDate(file.end_date)}`
                                            : '-'}
                                    </TableCell>
                                    <TableCell className="text-[#020617] font-[14px]  p-2">
                                        {formatDate(file.uploaded_on)}
                                    </TableCell>
                                    <TableCell className='p-2'>
                                        <Button 
                                            size="sm" 
                                            className="h-8 gap-2 ml-0 shadow-none border-border bg-gray-100 hover:bg-gray-200 text-gray-900"
                                            onClick={() => handleDownload(file.download_link)}
                                        >
                                            <Download className="h-3.5 w-3.5" />
                                            Download
                                        </Button>
                                    </TableCell>
                                </TableRow>
                            ))
                        )}
                    </TableBody>
                </Table>
            </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
