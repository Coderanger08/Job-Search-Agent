import React from 'react';
import {
  Box,
  Typography,
  Avatar,
  Paper
} from '@mui/material';
import {
  SmartToy as AIIcon
} from '@mui/icons-material';
import { motion } from 'framer-motion';

const TypingIndicator = () => {
  return (
    <Box
      sx={{
        display: 'flex',
        alignItems: 'flex-start',
        gap: 1,
        mb: 2
      }}
    >
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
      
      <Paper
        elevation={1}
        sx={{
          p: 2,
          backgroundColor: 'background.paper',
          color: 'text.primary',
          borderRadius: '18px 18px 18px 4px',
          maxWidth: '80%',
          marginRight: 'auto',
          border: '1px solid',
          borderColor: 'divider'
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Typography variant="body2" color="text.secondary">
            Searching for jobs
          </Typography>
          
          {/* Animated dots */}
          <Box sx={{ display: 'flex', gap: 0.5 }}>
            {[0, 1, 2].map((index) => (
              <motion.div
                key={index}
                animate={{
                  y: [0, -8, 0]
                }}
                transition={{
                  duration: 0.6,
                  repeat: Infinity,
                  delay: index * 0.2,
                  ease: "easeInOut"
                }}
              >
                <Box
                  sx={{
                    width: 6,
                    height: 6,
                    borderRadius: '50%',
                    backgroundColor: 'primary.main'
                  }}
                />
              </motion.div>
            ))}
          </Box>
        </Box>
      </Paper>
    </Box>
  );
};

export default TypingIndicator;
