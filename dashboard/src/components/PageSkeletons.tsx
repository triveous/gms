import { Skeleton } from '@/components/ui/skeleton';

export const GrantsSkeleton = () => (
  <div className="space-y-4">
    {[1, 2, 3].map((i) => (
      <div
        key={i}
        className="p-6 bg-card border-border rounded border flex flex-col gap-6"
      >
        <div className="flex gap-4">
          <div className="flex flex-col gap-4 flex-1">
            <Skeleton className="h-7 w-3/4" />
            <div className="flex gap-4">
              <Skeleton className="h-4 w-32" />
              <Skeleton className="h-4 w-32" />
            </div>
          </div>
          <Skeleton className="h-[45px] w-[155px]" />
        </div>
        <div className="flex gap-8">
          {[1, 2, 3, 4].map((j) => (
            <div key={j} className="flex flex-col gap-2">
              <Skeleton className="h-3 w-20" />
              <Skeleton className="h-6 w-24" />
            </div>
          ))}
        </div>
      </div>
    ))}
  </div>
);

export const GrantSkeleton = () => (
  <div className="space-y-6">
    {/* Breadcrumb Skeleton */}
    <Skeleton className="h-4 w-48" />

    {/* Header Skeleton */}
    <div className="space-y-4">
      <Skeleton className="h-10 w-2/3" />
      <div className="flex gap-2">
        <Skeleton className="h-8 w-24 rounded-lg" />
        <Skeleton className="h-8 w-32 rounded-lg" />
        <Skeleton className="h-8 w-28 rounded-lg" />
        <Skeleton className="h-8 w-36 rounded-lg" />
      </div>
    </div>

    {/* Metrics Skeleton */}
    <div className="flex gap-4">
      {[1, 2, 3].map((i) => (
        <div key={i} className="flex flex-col gap-3 min-w-[150px]">
          <Skeleton className="h-4 w-24" />
          <Skeleton className="h-8 w-32" />
        </div>
      ))}
    </div>

    <div className="h-px bg-border" />

    {/* Projects Section Skeleton */}
    <div className="space-y-4">
      <Skeleton className="h-8 w-32" />
      {[1, 2].map((i) => (
        <Skeleton key={i} className="h-48 w-full rounded-lg" />
      ))}
    </div>
  </div>
);

export const ProjectSkeleton = () => (
  <div className="space-y-6">
    {/* Breadcrumb Skeleton */}
    <Skeleton className="h-4 w-48" />

    {/* Header Skeleton */}
    <div className="space-y-4">
      <Skeleton className="h-10 w-2/3" />
      <div className="flex gap-2">
        <Skeleton className="h-8 w-30 rounded-lg" />
        <Skeleton className="h-8 w-32 rounded-lg" />
        <Skeleton className="h-8 w-36 rounded-lg" />
      </div>
    </div>

    <div className="h-px bg-border" />

    {/* Filter Skeleton */}
    <div className="flex gap-4">
      <Skeleton className="h-10 w-48 rounded-lg" />
      <Skeleton className="h-10 w-48 rounded-lg" />
    </div>

    {/* TCRM Metrics Skeleton */}
    <div className="grid grid-cols-4 gap-4">
      {[1, 2, 3, 4].map((i) => (
        <div
          key={i}
          className="p-6 bg-card border border-border rounded flex flex-col gap-4"
        >
          <Skeleton className="h-4 w-3/4" />
          <Skeleton className="h-8 w-1/4" />
        </div>
      ))}
    </div>

    {/* Content Section Skeleton */}
    <div className="grid grid-cols-2 gap-6">
      <Skeleton className="h-64 w-full rounded-lg" />
      <Skeleton className="h-64 w-full rounded-lg" />
    </div>
  </div>
);
