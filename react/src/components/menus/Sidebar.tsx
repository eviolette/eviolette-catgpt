import {
    Box,
    Divider,
    Drawer,
    List,
    ListItem,
    ListItemText,
    Toolbar,
    useTheme
} from "@mui/material";
import { Input, AutoGraph} from "@mui/icons-material";
import { useLocation, Link } from "react-router-dom";

const SideBar = () => {
    const theme = useTheme();
    const location = useLocation().pathname;
    const drawerWidth = 240;
    const isDark = theme.palette.mode === 'dark';

    const ListItemStyle = (path: string) => ({
        gap: 2,
        color: location.includes(path)
            ? theme.palette.primary.light
            : isDark
                ? theme.palette.grey[100]
                : theme.palette.grey[900],
        '&:hover': {
            color: theme.palette.primary.light,
        },
    });

    return (
        <Drawer
            variant="permanent"
            sx={{
                width: drawerWidth,
                flexShrink: 0,
                [`& .MuiDrawer-paper`]: {
                    width: drawerWidth,
                    boxSizing: 'border-box',
                    backgroundColor: theme.palette.background.default,
                    color: theme.palette.text.primary,
                },
            }}
        >
            <Toolbar />
            <Box sx={{ overflow: 'auto' }}>
                <List>
                    <ListItem
                        component={Link}
                        to="/chat"
                        sx={ListItemStyle('/')}
                    >
                        <Input />
                        <ListItemText primary="Get Started" />
                    </ListItem>
                    <Divider
                        sx={{
                            backgroundColor: theme.palette.divider,
                            opacity: 0.5,
                            my: 1,
                        }}
                    />
                    <ListItem
                        component={Link}
                        to="/chat"
                        sx={ListItemStyle('/')}
                    >
                        <AutoGraph />
                        <ListItemText primary="Chat 1" />
                    </ListItem>
                </List>
            </Box>
        </Drawer>
    );
};

export default SideBar;