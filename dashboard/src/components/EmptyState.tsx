import { Sparkles } from 'lucide-react';
import DefaultImage from '../assets/defalut-coe.png'


export default function EmptyState() {
    return (
        <div className="flex flex-col items-center justify-center py-16 px-4 bg-white mt-6 rounded-lg">
            {/* Illustration */}
            <div className="mb-8">
                <img src={DefaultImage} alt="" className='w-[400px]'/>
            </div>

            {/* Text */}
            <h2 className="text-foreground font-semibold text-xl mb-8">
                Please setup your platform:
            </h2>

            {/* Upload Button */}
            <div 
                className="flex items-center gap-2 px-6 py-2.5 border border-border rounded-lg hover:bg-accent transition-colors"
            >
                <Sparkles className="w-5 h-5" />
                Upload your DPR
            </div>
        </div>
    );
}
