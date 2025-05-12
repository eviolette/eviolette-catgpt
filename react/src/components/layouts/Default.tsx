import React from 'react';
import { Box } from '@mui/material';
import { Outlet } from 'react-router-dom';
import TopBar from '../menus/TopBar';
import Sidebar from '../menus/Sidebar';

const Layout: React.FC = () => {
    return (
        <Box sx={{ height: '100vh', width: '100%', display: 'flex', flexDirection: 'column' }}>
            {/* TopBar spans full width */}
            <TopBar />

            {/* Below TopBar: Sidebar + Main horizontally */}
            <Box sx={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
                {/* Sidebar (give it a fixed width) */}
                <Box sx={{ width: 240, flexShrink: 0, marginRight: 1 }}>
                    <Sidebar />
                </Box>

                {/* Main content (takes remaining width) */}
                <Box
                    component="main"
                    sx={{
                        flexGrow: 1,
                        overflow: 'auto',
                        marginTop: 8
                    }}
                >
                    <Outlet />
                </Box>
            </Box>
        </Box>
    );
};

export default Layout;