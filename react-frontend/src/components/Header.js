import React from 'react';
import {
  AppBar,
  Toolbar,
  Typography,
  Box,
  Chip,
  IconButton,
  Tooltip
} from '@mui/material';
import {
  Work as WorkIcon,
  SmartToy as AIIcon,
  GitHub as GitHubIcon,
  Info as InfoIcon
} from '@mui/icons-material';
import { motion } from 'framer-motion';

const Header = () => {
  return (
    <AppBar 
      position="static" 
      sx={{ 
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        boxShadow: '0 4px 20px rgba(0,0,0,0.1)'
      }}
    >
      <Toolbar>
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5 }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <WorkIcon sx={{ fontSize: 28 }} />
              <Typography 
                variant="h6" 
                sx={{ 
                  fontWeight: 700,
                  fontSize: '1.5rem'
                }}
              >
                JobSearch AI
              </Typography>
            </Box>
            
            <Chip
              icon={<AIIcon />}
              label="Powered by AI"
              size="small"
              sx={{
                bgcolor: 'rgba(255,255,255,0.2)',
                color: 'white',
                border: '1px solid rgba(255,255,255,0.3)',
                '& .MuiChip-icon': {
                  color: 'white'
                }
              }}
            />
          </Box>
        </motion.div>

        <Box sx={{ flexGrow: 1 }} />

        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Chip
              label="Bangladesh"
              size="small"
              sx={{
                bgcolor: 'rgba(255,255,255,0.2)',
                color: 'white',
                border: '1px solid rgba(255,255,255,0.3)'
              }}
            />
            
            <Tooltip title="About">
              <IconButton 
                color="inherit"
                sx={{ 
                  bgcolor: 'rgba(255,255,255,0.1)',
                  '&:hover': {
                    bgcolor: 'rgba(255,255,255,0.2)'
                  }
                }}
              >
                <InfoIcon />
              </IconButton>
            </Tooltip>
            
            <Tooltip title="GitHub">
              <IconButton 
                color="inherit"
                sx={{ 
                  bgcolor: 'rgba(255,255,255,0.1)',
                  '&:hover': {
                    bgcolor: 'rgba(255,255,255,0.2)'
                  }
                }}
              >
                <GitHubIcon />
              </IconButton>
            </Tooltip>
          </Box>
        </motion.div>
      </Toolbar>
    </AppBar>
  );
};

export default Header;

