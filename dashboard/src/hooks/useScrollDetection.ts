import { useState, useEffect, useCallback } from 'react';

export interface ScrollInfo {
    isScrollable: boolean;
    isAtTop: boolean;
    isAtBottom: boolean;
}

/**
 * A reusable hook to detect if a container is scrollable and its current scroll position.
 * Scalable approach: logic is extracted, reusable, and handles lifecycle cleanup.
 */
export function useScrollDetection(
    node: HTMLElement | null, 
    triggerDeps: React.DependencyList = []
): ScrollInfo {
    const [scrollInfo, setScrollInfo] = useState<ScrollInfo>({
        isScrollable: false,
        isAtTop: true,
        isAtBottom: true,
    });

    const checkScroll = useCallback(() => {
        if (!node) return;

        const { scrollTop, scrollHeight, clientHeight } = node;
        
        // Using a 1px buffer for rounding errors
        const isScrollable = scrollHeight > clientHeight + 1.5;
        const isAtTop = scrollTop <= 0;
        const isAtBottom = Math.abs(scrollHeight - clientHeight - scrollTop) < 1.5;

        setScrollInfo(prev => {
            // Only update if values actually changed to avoid unnecessary re-renders
            if (
                prev.isScrollable === isScrollable &&
                prev.isAtTop === isAtTop &&
                prev.isAtBottom === isAtBottom
            ) {
                return prev;
            }
            return { isScrollable, isAtTop, isAtBottom };
        });
    }, [node]);

    useEffect(() => {
        if (!node) return;

        const observer = new ResizeObserver(checkScroll);
        observer.observe(node);
        window.addEventListener('resize', checkScroll);
        node.addEventListener('scroll', checkScroll);

        return () => {
            observer.disconnect();
            window.removeEventListener('resize', checkScroll);
            node.removeEventListener('scroll', checkScroll);
        };
    }, [node, checkScroll, ...triggerDeps]); // Ignoring the spread warning as it's intended for dynamic dependencies

    return scrollInfo;
}
