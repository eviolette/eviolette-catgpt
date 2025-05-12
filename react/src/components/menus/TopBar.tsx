import React from 'react';
import { AppBar, Toolbar, Typography, Button, Box, useTheme } from '@mui/material';
import { Link, useLocation } from 'react-router-dom';
import Logo from './Logo';

const TopBar: React.FC = () => {
    const location = useLocation().pathname;
    const theme = useTheme();
    const isDark = theme.palette.mode === 'dark';

    const buttonStyle = (path: string) => ({
        textTransform: 'none',
        color: location.includes(path)
            ? theme.palette.secondary.light
            : isDark
                ? theme.palette.grey[100]
                : theme.palette.grey[900],
        '&:hover': {
            color: theme.palette.primary.light,
        },
    });

    return (
        <AppBar
            position="fixed"
            sx={{
                backgroundColor: isDark
                    ? theme.palette.grey[900]
                    : theme.palette.primary.dark,
                zIndex: theme.zIndex.drawer + 1,
            }}
        >
            <Toolbar>
                <Logo />
                <Typography
                    variant="h6"
                    sx={{
                        marginLeft: 2,
                        marginRight: 8,
                        color: isDark ? theme.palette.grey[100] : theme.palette.common.white,
                    }}
                >
                    CatGPT
                </Typography>
                <Box sx={{ display: 'flex', gap: 2 }}>
                    <Button
                        color="inherit"
                        sx={buttonStyle('projects')}
                        component={Link}
                        to="/"
                    >
                        <Typography variant="h6" sx={{ fontWeight: 'regular', color: isDark ? theme.palette.grey[100] : theme.palette.common.white }}>
                            Projects
                        </Typography>
                    </Button>
                    <Button
                        color="inherit"
                        sx={buttonStyle('chats')}
                        component={Link}
                        to="/chat"
                    >
                        <Typography variant="h6" sx={{ fontWeight: 'regular', color: isDark ? theme.palette.grey[100] : theme.palette.common.white, }}>
                            Chats
                        </Typography>
                    </Button>
                </Box>
            </Toolbar>
        </AppBar>
    );
};

export default TopBar;