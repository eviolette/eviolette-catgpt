import React from 'react';
import { Box } from '@mui/material';
import { Outlet } from 'react-router-dom';
import TopBar from '../menus/TopBar';
import Sidebar from '../menus/Sidebar';

const Layout: React.FC = () => {
    return (
        <Box sx={{ display: 'flex', width: '100%', overflowX: 'hidden' }}>
            <TopBar />
            <Sidebar />
            <Box component="main"
                sx={{ 
                    flexGrow: 1, 
                    paddingTop: 8, 
                }}
            >
                <Outlet />
            </Box>
        </Box>
    );
};

export default Layout;