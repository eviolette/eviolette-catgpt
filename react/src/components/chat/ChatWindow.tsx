import React, { useState, useRef, useEffect } from 'react';
import { Box, TextField, IconButton, MenuItem, Select, InputLabel, FormControl, Paper, Typography } from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import axios from 'axios';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';

interface ChatMessage {
    role: 'user' | 'assistant';
    type: 'markdown' | 'python' | 'json' | 'readme';
    content: string;
    isLoading?: boolean;
}

const ChatWindow: React.FC = () => {
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [input, setInput] = useState('');
    const [expanded, setExpanded] = useState(false);
    const [format, setFormat] = useState<'markdown' | 'python' | 'readme' | 'json:BasicResponse' | 'json:BasicListResponse'>('markdown');
    const chatEndRef = useRef<HTMLDivElement | null>(null);

    const scrollToBottom = () => {
        chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const handleSend = async () => {
        if (!input.trim()) return;

        const [baseType, schemaName] = format.includes(':') ? format.split(':') : [format, null];

        const userMessage: ChatMessage = {
            role: 'user',
            type: baseType as any,
            content: input,
        };
        setMessages((prev) => [...prev, userMessage, {
            role: 'assistant',
            type: baseType as any,
            content: '...',
            isLoading: true,
        }]);
        setInput('');

        try {
            const endpointMap: Record<string, string> = {
                markdown: '/markdown',
                python: '/python',
                readme: '/readme',
                json: '/json',
            };

            const payload: any = {
                prompt: userMessage.content,
            };

            if (baseType === 'json' && schemaName) {
                payload.schema_name = schemaName;
            }

            const res = await axios.post(`http://localhost:8081${endpointMap[baseType]}`, payload);

            const botMessage: ChatMessage = {
                role: 'assistant',
                type: baseType as any,
                content: res.data.content,
            };
            setMessages((prev) => {
                const copy = [...prev];
                copy[copy.length - 1] = botMessage; // replace loading
                return copy;
            });
        } catch (error) {
            const errMsg: ChatMessage = {
                role: 'assistant',
                type: 'markdown',
                content: '⚠️ Error generating response. Check the backend.',
            };
            setMessages((prev) => [...prev, errMsg]);
        }
    };

    const renderMessage = (msg: ChatMessage, idx: number) => {
        const languageMap: Record<string, string> = {
            markdown: 'markdown',
            python: 'python',
            json: 'json',
            readme: 'markdown',
        };

        return (
            <Paper
                key={idx}
                sx={{
                    position: 'relative',
                    p: 2,
                    my: 1,
                    backgroundColor: msg.role === 'user' ? '#e3f2fd' : '#f3e5f5',
                    wordBreak: 'break-word',
                    overflowWrap: 'anywhere', // aggressively wrap long words/URLs
                    whiteSpace: 'pre-wrap'   // wrap at spaces too
                }}>
                <Typography variant="caption" sx={{ fontWeight: 'bold' }}>
                    {msg.role === 'user' ? 'You' : 'CatGPT'}
                </Typography>
                {!msg.isLoading && (
                    <IconButton
                        size="small"
                        sx={{ position: 'absolute', top: 8, right: 8 }}
                        onClick={() => navigator.clipboard.writeText(msg.content)}
                    >
                        <ContentCopyIcon fontSize="small" />
                    </IconButton>
                )}
                <SyntaxHighlighter
                    language={languageMap[msg.type]}
                    style={vscDarkPlus}
                    wrapLongLines
                    wrapLines
                    customStyle={{
                        whiteSpace: 'pre-wrap',
                        wordBreak: 'break-word',
                    }}
                >
                    {msg.content}
                </SyntaxHighlighter>
            </Paper>
        );
    };

    return (
        <Box
            sx={{
                display: 'flex',
                flexDirection: 'column',
                height: 'calc(100vh - 64px)', // TopBar height
                width: '100%',
                overflow: 'hidden',
                px: 0, // <-- REMOVE horizontal padding
                minWidth: '40vw',
                maxWidth: '70vw'
            }}
        >
            {/* Chat History Area */}
            <Box
                sx={{
                    flexGrow: 1,
                    overflowY: 'auto',
                    py: 2,
                    pr: 1, // optional: avoid scroll overlap
                }}
            >
                {messages.map((msg, idx) => renderMessage(msg, idx))}
                <div ref={chatEndRef} />
            </Box>

            {/* Prompt Input Area */}
            <Box
                sx={{
                    flex: `0 0 ${expanded ? '50%' : '25%'}`,
                    transition: 'flex-basis 0.3s ease',
                    display: 'flex',
                    flexDirection: 'column',
                    borderTop: '1px solid #ccc',
                    pt: 1,
                    backgroundColor: 'background.paper',
                    overflow: 'hidden', // prevents content from leaking
                }}
            >
                {/* Dropdown */}
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                    <FormControl size="small" sx={{ minWidth: 120 }}>
                        <InputLabel>Type</InputLabel>
                        <Select
                            value={format}
                            label="Type"
                            onChange={(e) => setFormat(e.target.value as any)}
                        >
                            <MenuItem value="markdown">.md</MenuItem>
                            <MenuItem value="python">Python</MenuItem>
                            <MenuItem value="readme">README.md</MenuItem>
                            <MenuItem value="json:BasicResponse">JSON - BasicResponse</MenuItem>
                            <MenuItem value="json:BasicListResponse">JSON - BasicListResponse</MenuItem>
                        </Select>
                    </FormControl>
                </Box>

                {/* Text Area */}
                <Box sx={{ flexGrow: 1, overflowY: 'auto', mb: 1 }}>
                    <TextField
                        multiline
                        fullWidth
                        placeholder="Enter your prompt..."
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onFocus={() => setExpanded(true)}
                        onBlur={() => input.trim() === '' && setExpanded(false)}
                        sx={{
                            height: '100%',
                            '& .MuiInputBase-input': {
                                overflow: 'auto',
                            },
                        }}
                    />
                </Box>

                {/* Send Button */}
                <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
                    <IconButton color="primary" onClick={handleSend}>
                        <SendIcon />
                    </IconButton>
                </Box>
            </Box>
        </Box>
    );
};

export default ChatWindow;