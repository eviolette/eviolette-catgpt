import React, { useState, useRef, useEffect } from 'react';
import { Box, TextField, IconButton, MenuItem, Select, InputLabel, FormControl, Paper, Typography, useTheme } from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import axios from 'axios';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import { Dialog, DialogTitle, DialogContent, Button } from '@mui/material';
import { CloudOff, DataObject, Notes } from '@mui/icons-material';
import { ReactComponent as PythonIcon } from '../../assets/python.svg';


interface ChatMessage {
    role: 'user' | 'assistant';
    type: 'markdown' | 'markdown:multi' | 'python' | 'json' | 'readme';
    content: string;
    isLoading?: boolean;
}

const ChatWindow: React.FC = () => {
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [input, setInput] = useState('');
    const [expanded, setExpanded] = useState(false);
    const [format, setFormat] = useState<'markdown' | 'markdown:multi' | 'python' | 'readme' | 'json:BasicResponse' | 'json:BasicListResponse'>('markdown');
    const chatEndRef = useRef<HTMLDivElement | null>(null);
    const [pendingMultiPersona, setPendingMultiPersona] = useState<null | {
        prompt: string;
        responses: { persona: string; content: string }[];
    }>(null);
    const theme = useTheme();
    const isDark = theme.palette.mode === 'dark';

    const scrollToBottom = () => {
        chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };
    useEffect(() => {
        const fetchMessages = async () => {
            try {
                const res = await axios.get("http://localhost:8081/chat/history", {
                    params: { chat_id: "chat-0001" },
                });
                const history = res.data.messages as ChatMessage[];
                setMessages(history);
            } catch (error) {
                console.error("Failed to load chat history", error);
            }
        };

        fetchMessages();
    }, []);

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

        // Handle multi-persona separately
        if (baseType === 'markdown' && schemaName === 'multi') {
            setMessages((prev) => [...prev, userMessage, {
                role: 'assistant',
                type: 'markdown',
                content: '...',
                isLoading: true,
            }]);

            try {
                const res = await axios.post('http://localhost:8081/multi_markdown', {
                    prompt: userMessage.content,
                });
                setPendingMultiPersona({
                    prompt: userMessage.content,
                    responses: res.data.responses,
                });

                // remove loading placeholder once modal is ready
                setMessages((prev) => prev.slice(0, -1));
            } catch (error) {
                setMessages((prev) => [
                    ...prev.slice(0, -1),
                    {
                        role: 'assistant',
                        type: 'markdown',
                        content: '⚠️ Error generating multi-persona response. Check the backend.',
                    },
                ]);
            }

            setInput('');
            return;
        }

        // Default case
        setMessages((prev) => [...prev, userMessage, {
            role: 'assistant',
            type: baseType as any,
            content: '...',
            isLoading: true,
        }]);
        setInput('');

        try {

            const payload: any = {
                prompt: userMessage.content,
            };

            if (baseType === 'json' && schemaName) {
                payload.schema_name = schemaName;
            }

            const res = await axios.post("http://localhost:8081/chat", {
                chat_id: "chat-0001",        // fixed for now
                prompt: userMessage.content,
                type: baseType,
                schema_name: schemaName ?? undefined,
            });

            const botMessage: ChatMessage = {
                role: 'assistant',
                type: baseType as any,
                content: res.data.response,
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
                            <MenuItem value="markdown"><Notes />&nbsp; Markdown</MenuItem>
                            <MenuItem value="json:BasicResponse"><DataObject />&nbsp; JSON (Basic Dictionary)</MenuItem>
                            <MenuItem value="json:BasicListResponse"><DataObject />&nbsp; JSON (Basic List)</MenuItem>
                            <MenuItem value="python">
                                <PythonIcon style={{ width: 20, height: 20, marginRight: 8 }} />
                                Python
                            </MenuItem>
                            <MenuItem value="readme"><CloudOff />&nbsp; Markdown (README.md)</MenuItem>
                            <MenuItem value="markdown:multi"><CloudOff />&nbsp; Markdown (Multi-Persona)</MenuItem>
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
                        onKeyDown={(e) => {
                            if ((e.metaKey) && e.key === 'Enter') {
                                e.preventDefault();
                                handleSend();
                            }
                        }}
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
            {pendingMultiPersona && (
                <Dialog open onClose={() => setPendingMultiPersona(null)} fullWidth maxWidth="md">
                    <DialogTitle>Select a Persona Response</DialogTitle>
                    <DialogContent>
                        {pendingMultiPersona.responses.map(({ persona, content }, idx) => (
                            <Paper key={idx} sx={{ m: 2, p: 2 }}>
                                <Typography variant="subtitle1" sx={{ fontWeight: 'bold', mb: 1 }}>
                                    {persona}
                                </Typography>
                                <SyntaxHighlighter
                                    language="markdown"
                                    style={vscDarkPlus}
                                    wrapLines
                                    wrapLongLines
                                    customStyle={{ whiteSpace: 'pre-wrap' }}
                                >
                                    {content}
                                </SyntaxHighlighter>
                                <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 1 }}>
                                    <Button variant="contained" onClick={() => {
                                        setMessages((prev) => [...prev, {
                                            role: 'assistant',
                                            type: 'markdown',
                                            content
                                        }]);
                                        setPendingMultiPersona(null);
                                    }}>
                                        <Typography variant="caption" sx={{ fontWeight: 'regular', color: isDark ? theme.palette.grey[100] : theme.palette.common.white }}>
                                            Use this Response
                                        </Typography>
                                    </Button>
                                </Box>
                            </Paper>
                        ))}
                    </DialogContent>
                </Dialog>
            )}
        </Box>
    );
};

export default ChatWindow;