import React from 'react';
import {
  Box,
  Typography,
  Avatar,
  Chip,
  Paper
} from '@mui/material';
import {
  Person as PersonIcon,
  SmartToy as AIIcon,
  Work as WorkIcon
} from '@mui/icons-material';
import { motion } from 'framer-motion';

const MessageBubble = ({ message }) => {
  const isUser = message.type === 'user';
  const isAI = message.type === 'ai';
  const isTyping = message.type === 'typing';

  const getMessageStyle = () => {
    if (isUser) {
      return {
        alignSelf: 'flex-end',
        backgroundColor: 'primary.main',
        color: 'white',
        borderRadius: '18px 18px 4px 18px',
        maxWidth: '80%',
        marginLeft: 'auto'
      };
    } else if (isAI) {
      return {
        alignSelf: 'flex-start',
        backgroundColor: 'background.paper',
        color: 'text.primary',
        borderRadius: '18px 18px 18px 4px',
        maxWidth: '80%',
        marginRight: 'auto',
        border: '1px solid',
        borderColor: 'divider'
      };
    } else {
      return {
        alignSelf: 'flex-start',
        backgroundColor: 'grey.100',
        color: 'text.secondary',
        borderRadius: '18px 18px 18px 4px',
        maxWidth: '80%',
        marginRight: 'auto'
      };
    }
  };

  const getAvatar = () => {
    if (isUser) {
      return (
        <Avatar
          sx={{
            bgcolor: 'primary.main',
            width: 32,
            height: 32,
            marginLeft: 1
          }}
        >
          <PersonIcon />
        </Avatar>
      );
    } else {
      return (
        <Avatar
          sx={{
            bgcolor: 'secondary.main',
            width: 32,
            height: 32,
            marginRight: 1
          }}
        >
          <AIIcon />
        </Avatar>
      );
    }
  };

  const formatTime = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{
        duration: 0.3,
        type: 'spring',
        stiffness: 260,
        damping: 20
      }}
    >
      <Box
        sx={{
          display: 'flex',
          alignItems: 'flex-start',
          gap: 1,
          mb: 2,
          flexDirection: isUser ? 'row-reverse' : 'row'
        }}
      >
        {!isUser && getAvatar()}
        
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
          <Paper
            elevation={isUser ? 2 : 1}
            sx={{
              p: 2,
              ...getMessageStyle(),
              wordBreak: 'break-word'
            }}
          >
            <Typography variant="body1" sx={{ lineHeight: 1.5 }}>
              {message.content}
            </Typography>
            
            {/* Show suggestions for irrelevant queries */}
            {isAI && message.suggestions && message.suggestions.length > 0 && (
              <Box sx={{ mt: 2 }}>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 1, fontWeight: 600 }}>
                  💡 Suggestions:
                </Typography>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
                  {message.suggestions.map((suggestion, index) => (
                    <Typography
                      key={index}
                      variant="body2"
                      sx={{
                        color: 'primary.main',
                        cursor: 'pointer',
                        '&:hover': { textDecoration: 'underline' }
                      }}
                    >
                      • {suggestion}
                    </Typography>
                  ))}
                </Box>
              </Box>
            )}
            
            {/* Show inappropriate content warning */}
            {isAI && message.isInappropriate && (
              <Box sx={{ mt: 1 }}>
                <Chip
                  label="Professional Response"
                  size="small"
                  color="warning"
                  variant="outlined"
                  sx={{ fontSize: '0.7rem' }}
                />
              </Box>
            )}
            
            {/* Show job count if AI message has jobs */}
            {isAI && message.jobs && message.jobs.length > 0 && (
              <Box sx={{ mt: 1 }}>
                <Chip
                  icon={<WorkIcon />}
                  label={`${message.jobs.length} job${message.jobs.length > 1 ? 's' : ''} found`}
                  size="small"
                  color="success"
                  variant="outlined"
                />
              </Box>
            )}
          </Paper>
          
          <Typography
            variant="caption"
            color="text.secondary"
            sx={{
              fontSize: '0.75rem',
              alignSelf: isUser ? 'flex-end' : 'flex-start',
              ml: isUser ? 0 : 1,
              mr: isUser ? 1 : 0
            }}
          >
            {formatTime(message.timestamp)}
          </Typography>
        </Box>
        
        {isUser && getAvatar()}
      </Box>
    </motion.div>
  );
};

export default MessageBubble;
