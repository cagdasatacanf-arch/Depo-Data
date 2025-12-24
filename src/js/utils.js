/**
 * DEPO Utilities Module
 * Standardized formatting and calculation helpers
 */

export const Utils = {
    /**
     * Formats a number as currency
     * @param {number} value - The price value
     * @param {string} currency - Currency code (default: USD)
     * @returns {string} Formatted currency string
     */
    formatCurrency: (value, currency = 'USD') => {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: currency,
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        }).format(value);
    },

    /**
     * Formats volume and large numbers (e.g., 1.2M, 500K)
     * @param {number} value - The number to format
     * @returns {string} Formatted number
     */
    formatNumber: (value) => {
        if (value === null || value === undefined) return 'N/A';
        return new Intl.NumberFormat('en-US', {
            notation: 'compact',
            compactDisplay: 'short'
        }).format(value);
    },

    /**
     * Formats an ISO date string (YYYY-MM-DD) for UI display
     * @param {string} dateString - ISO date string
     * @returns {string} Formatted date (e.g., Dec 24, 2025)
     */
    formatDate: (dateString) => {
        const options = { year: 'numeric', month: 'short', day: 'numeric' };
        return new Date(dateString).toLocaleDateString('en-US', options);
    },

    /**
     * Calculates percentage change between two values
     * @param {number} initial - Starting value
     * @param {number} current - Ending value
     * @returns {object} { value: number, string: string, isPositive: boolean }
     */
    calculateChange: (initial, current) => {
        const change = ((current - initial) / initial) * 100;
        const isPositive = change >= 0;
        return {
            value: change.toFixed(2),
            string: `${isPositive ? '+' : ''}${change.toFixed(2)}%`,
            isPositive
        };
    },

    /**
     * Persists a key-value pair to localStorage
     */
    saveToStorage: (key, value) => {
        localStorage.setItem(`depo_${key}`, JSON.stringify(value));
    },

    /**
     * Retrieves a value from localStorage
     */
    getFromStorage: (key) => {
        const item = localStorage.getItem(`depo_${key}`);
        return item ? JSON.parse(item) : null;
    }
};
