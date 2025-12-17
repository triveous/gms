import type { ReactNode } from 'react';
import { cn } from '@/lib/utils';

interface SectionWrapperProps {
    /** The section title */
    title: string;
    /** Additional classes for the outer wrapper */
    className?: string;
    /** Additional classes for the title */
    titleClassName?: string;
    /** Additional classes for the content wrapper */
    contentClassName?: string;
    /** The content to render inside the section */
    children: ReactNode;
}

export function SectionWrapper({
    title,
    className,
    titleClassName,
    contentClassName,
    children,
}: SectionWrapperProps) {
    return (
        <div className={cn('mb-8 flex flex-col gap-6', className)}>
            <h2 className={cn(
                'text-foreground text-xl font-semibold leading-[120%] tracking-[-0.4px]',
                titleClassName
            )}>
                {title}
            </h2>
            <div className={cn(contentClassName)}>
                {children}
            </div>
        </div>
    );
}
