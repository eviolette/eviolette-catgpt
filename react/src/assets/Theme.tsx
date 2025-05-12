import { createTheme, lighten, getContrastRatio, darken } from '@mui/material/styles';

// 👇 Function that returns a theme based on system preference
const getAppTheme = (mode: 'light' | 'dark') => {
    return createTheme({
        palette: {
            mode,
            primary: {
                main: '#00A3E0',
                light: lighten('#00A3E0', 0.2),
                dark: darken('#00A3E0', 0.2),
                contrastText: getContrastRatio('#00A3E0', '#000') >= 3 ? '#004f6b' : '#fff',
            },
            secondary: {
                main: '#7f00e0',
                light: lighten('#7f00e0', 0.2),
                dark: darken('#7f00e0', 0.2),
                contrastText: getContrastRatio('#7f00e0', '#000') >= 3 ? '#000' : '#fff',
            },
            error: {
                main: '#EF2D56',
                light: lighten('#EF2D56', 0.2),
                dark: darken('#EF2D56', 0.2),
                contrastText: getContrastRatio('#EF2D56', '#000') >= 3 ? '#000' : '#fff',
            },
            warning: {
                main: '#FFB400',
                light: lighten('#FFB400', 0.2),
                dark: darken('#FFB400', 0.2),
                contrastText: getContrastRatio('#FFB400', '#000') >= 3 ? '#000' : '#fff',
            },
        },
        typography: {
            fontFamily: 'Open Sans, sans-serif',
        },
        breakpoints: {
            values: {
                xs: 0,
                sm: 600,
                md: 960,
                lg: 1280,
                xl: 2000,
            },
        },
        components: {
            MuiMenuItem: {
                styleOverrides: {
                    root: {
                        '&.Mui-selected': {
                            backgroundColor: lighten('#00A3E0', 0.9),
                        },
                        '&.Mui-selected:hover': {
                            backgroundColor: lighten('#00A3E0', 0.8),
                        },
                    },
                },
            },
        },
    });
};

export default getAppTheme;