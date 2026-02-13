import React from 'react';
import logo from '../assets/AIKAM Logo.svg';
import { Link } from 'react-router-dom';

export const Logo: React.FC = () => {
    return (
        <Link to="/" className="flex items-center gap-2 hover:opacity-80 transition-opacity">
            <img src={logo} alt="AIKAM Logo" className="h-6 w-auto" />
        </Link>
    );
};
