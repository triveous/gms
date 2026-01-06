import { LaptopMinimalCheck, Check } from 'lucide-react';

export default function DesktopOnly() {
  return (
    <div className="fixed inset-0 bg-[#F8FAFC] z-[9999] flex flex-col items-center justify-between p-8 text-center lg:hidden font-sans">
      {/* Spacer to push content to center */}
      <div className="flex-1" />

      {/* Main Content */}
      <div className="max-w-md flex flex-col items-center">
        {/* Icon with Checkmark Inside */}
        <div className="relative mb-6 text-[#475569]">
          <LaptopMinimalCheck size={60} strokeWidth={1.5} />
        </div>

        {/* Text Content */}
        <h2 className="text-[#334155] text-[22px] font-bold mb-4 leading-tight">
          Best viewed on a larger screen
        </h2>
        
        <p className="text-[#64748B] text-[15px] leading-[1.6] px-2 font-medium">
          AIKAM dashboards are built for detailed analysis and wide-screen layouts. 
          Please open this site on a laptop or desktop to continue.
        </p>
      </div>

      {/* Footer Content */}
      <div className="flex-1 flex flex-col justify-end pb-4">
        <p className="text-[#94A3B8] text-[13px] font-medium">
          Mobile and tablet support is currently unavailable.
        </p>
      </div>
    </div>
  );
}
