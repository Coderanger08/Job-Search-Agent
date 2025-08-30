import React, { useState, useRef, useEffect } from 'react';
import {
  Box,
  TextField,
  IconButton,
  Typography,
  Avatar,
  Chip,
  Fade,
  CircularProgress
} from '@mui/material';
import {
  Send as SendIcon,
  Work as WorkIcon,
  Person as PersonIcon,
  SmartToy as AIIcon
} from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';
import MessageBubble from './MessageBubble';
import TypingIndicator from './TypingIndicator';

const ChatInterface = ({ messages, onSendMessage, isSearching }) => {
  const [input, setInput] = useState('');
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Focus input on mount
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const handleSend = () => {
    if (input.trim() && !isSearching) {
      onSendMessage(input.trim());
      setInput('');
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Chat Header */}
      <Box
        sx={{
          p: 2,
          borderBottom: '1px solid',
          borderColor: 'divider',
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          color: 'white',
          borderRadius: '12px 12px 0 0'
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Avatar
            sx={{
              bgcolor: 'rgba(255,255,255,0.2)',
              width: 40,
              height: 40
            }}
          >
            <AIIcon />
          </Avatar>
          <Box>
            <Typography variant="h6" sx={{ fontWeight: 600 }}>
              AI Job Assistant
            </Typography>
            <Typography variant="body2" sx={{ opacity: 0.8 }}>
              {isSearching ? 'Searching for jobs...' : 'Ready to help you find jobs'}
            </Typography>
          </Box>
        </Box>
      </Box>

      {/* Messages Container */}
      <Box
        sx={{
          flex: 1,
          overflow: 'auto',
          p: 2,
          display: 'flex',
          flexDirection: 'column',
          gap: 2
        }}
      >
        <AnimatePresence>
          {messages.map((message, index) => (
            <motion.div
              key={message.id}
              initial={{ opacity: 0, y: 20, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -20, scale: 0.95 }}
              transition={{
                duration: 0.3,
                delay: index * 0.1,
                type: 'spring',
                stiffness: 260,
                damping: 20
              }}
            >
              <MessageBubble message={message} />
            </motion.div>
          ))}
        </AnimatePresence>

        {/* Typing indicator */}
        {isSearching && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.3 }}
          >
            <TypingIndicator />
          </motion.div>
        )}

        {/* Auto-scroll anchor */}
        <div ref={messagesEndRef} />
      </Box>

      {/* Input Area */}
      <Box
        sx={{
          p: 2,
          borderTop: '1px solid',
          borderColor: 'divider',
          background: 'background.paper'
        }}
      >
        <Box sx={{ display: 'flex', gap: 1, alignItems: 'flex-end' }}>
          <TextField
            ref={inputRef}
            fullWidth
            multiline
            maxRows={4}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask me about jobs in Bangladesh..."
            variant="outlined"
            size="small"
            disabled={isSearching}
            sx={{
              '& .MuiOutlinedInput-root': {
                borderRadius: 2,
                backgroundColor: 'background.default',
                '&:hover': {
                  backgroundColor: 'action.hover',
                },
                '&.Mui-focused': {
                  backgroundColor: 'background.paper',
                },
              },
            }}
          />
          <IconButton
            onClick={handleSend}
            disabled={!input.trim() || isSearching}
            sx={{
              bgcolor: 'primary.main',
              color: 'white',
              width: 40,
              height: 40,
              '&:hover': {
                bgcolor: 'primary.dark',
              },
              '&:disabled': {
                bgcolor: 'action.disabledBackground',
                color: 'action.disabled',
              },
            }}
          >
            {isSearching ? (
              <CircularProgress size={20} color="inherit" />
            ) : (
              <SendIcon />
            )}
          </IconButton>
        </Box>

        {/* Quick Suggestions */}
        {!isSearching && messages.length <= 2 && (
          <Fade in={true} timeout={1000}>
            <Box sx={{ mt: 2 }}>
              <Typography variant="caption" color="text.secondary" sx={{ mb: 1, display: 'block' }}>
                Try asking:
              </Typography>
              <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                {[
                  'Software Engineer jobs',
                  'Marketing positions in Dhaka',
                  'Remote developer opportunities',
                  'Entry level jobs'
                ].map((suggestion, index) => (
                  <Chip
                    key={index}
                    label={suggestion}
                    size="small"
                    variant="outlined"
                    onClick={() => setInput(suggestion)}
                    sx={{
                      cursor: 'pointer',
                      '&:hover': {
                        bgcolor: 'primary.light',
                        color: 'white',
                      },
                    }}
                  />
                ))}
              </Box>
            </Box>
          </Fade>
        )}
      </Box>
    </Box>
  );
};

export default ChatInterface;
