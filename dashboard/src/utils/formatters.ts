// Helper: Replace null/undefined/"" with "--"
export const safe = (value: string) =>
    value === null || value === undefined || value === '' ? '--' : value;

export const formatIndianAmount = (value: any) => {
    if (value === null || value === undefined || value === '' || isNaN(value)) {
        return '--';
    }

    const amount = Number(value);

    if (amount >= 1_00_000) {
        // Display in Crores for amounts >= 1 Lakh
        return `₹ ${(amount / 1_00_00_000).toLocaleString('en-IN', {
            maximumFractionDigits: 2
        })} Cr`;
    }

    // Default fallback (just number)
    return amount.toLocaleString('en-IN');
};

export const formatIndianNumber = (value: any) => {
    if (value === null || value === undefined || value === '' || isNaN(value)) {
        return '--';
    }

    const amount = Number(value);

    if (amount >= 1_00_000) {
        // Display in Crores for amounts >= 1 Lakh
        return `${(amount / 1_00_00_000).toLocaleString('en-IN', {
            maximumFractionDigits: 2
        })} Cr`;
    }

    // Default fallback (just number)
    return amount.toLocaleString('en-IN');
};

export const formatTimeline = (start: string, end: string) => {
    if (!start || !end) return '--';

    const s = new Date(start);
    const e = new Date(end);

    if (isNaN(s.getTime()) || isNaN(e.getTime())) return '--';

    // Calculate difference in years
    const years = e.getFullYear() - s.getFullYear();

    // Convert to readable date formats
    const months = [
        'January','February','March','April','May','June',
        'July','August','September','October','November','December'
    ];

    const startFormatted = `${months[s.getMonth()]} ${s.getFullYear()}`;
    const endFormatted = `${e.getDate()} ${months[e.getMonth()]} ${e.getFullYear()}`;

    // return `${years} year (${startFormatted} - ${endFormatted})`;
    return `${years} year`;
};

export const calculateBudgetSpendPercent = (total: any, spent: any) => {
    const totalAmount = Number(total);
    const spentAmount = Number(spent);

    if (
        total === null ||
        total === undefined ||
        total === '' ||
        spent === null ||
        spent === undefined ||
        spent === '' ||
        isNaN(totalAmount) ||
        isNaN(spentAmount) ||
        totalAmount === 0
    ) {
        return '--';
    }

    return ((spentAmount / totalAmount) * 100).toFixed(0);
};
