import { Box } from "@mui/system";

function Logo() {
    return (
        <Box sx={{ display: "flex", alignItems: "center" }}>
            <img
                src="/obi.png"
                alt="Company Logo"
                style={{ height: 40 }}
            />
        </Box>
    );
}

export default Logo;
