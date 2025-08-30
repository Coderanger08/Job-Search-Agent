import React, { useState, useEffect } from 'react';
import { 
  Box, 
  CssBaseline, 
  ThemeProvider, 
  createTheme,
  AppBar,
  Toolbar,
  Typography,
  Container,
  Grid,
  Paper
} from '@mui/material';
import { motion, AnimatePresence } from 'framer-motion';
import ChatInterface from './components/ChatInterface';
import FilterSidebar from './components/FilterSidebar';
import JobResults from './components/JobResults';
import Header from './components/Header';
import './App.css';

// Create a beautiful theme
const theme = createTheme({
  palette: {
    primary: {
      main: '#667eea',
      light: '#8fa4f3',
      dark: '#4a5fd1',
    },
    secondary: {
      main: '#764ba2',
      light: '#9a6bb8',
      dark: '#5a3a7a',
    },
    background: {
      default: '#f8f9fa',
      paper: '#ffffff',
    },
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
    h1: {
      fontWeight: 700,
    },
    h2: {
      fontWeight: 600,
    },
    h3: {
      fontWeight: 600,
    },
  },
  shape: {
    borderRadius: 12,
  },
  components: {
    MuiPaper: {
      styleOverrides: {
        root: {
          boxShadow: '0 4px 20px rgba(0,0,0,0.08)',
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          borderRadius: 8,
          fontWeight: 600,
        },
      },
    },
  },
});

function App() {
  const [messages, setMessages] = useState([]);
  const [jobs, setJobs] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const [filters, setFilters] = useState({
    location: "All Locations",
    experience: "Any",
    job_type: "Any",
    salary_range: [0, 200000],
    sources: {
      "BDJobs": true,
      "LinkedIn": true,
      "Indeed": true,
      "Web Search": true
    },
    max_results: 20,
    timeout: 30
  });

  const [searchStats, setSearchStats] = useState({
    total_found: 0,
    search_time: 0,
    sources_used: []
  });

  // Add welcome message on component mount
  useEffect(() => {
    const welcomeMessage = {
      id: Date.now(),
      type: 'ai',
      content: "Hello! I'm your AI job search assistant. I can help you find jobs in Bangladesh from multiple sources including BDJobs, LinkedIn, Indeed, and web search. What kind of job are you looking for?",
      timestamp: new Date().toISOString()
    };
    setMessages([welcomeMessage]);
  }, []);

  const handleSearch = async (query) => {
    console.log('🔍 handleSearch called with query:', query);
    if (!query.trim()) return;

    // Add user message
    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: query,
      timestamp: new Date().toISOString()
    };
    setMessages(prev => [...prev, userMessage]);

    // Add typing indicator
    const typingMessage = {
      id: Date.now() + 1,
      type: 'typing',
      content: 'Searching for jobs...',
      timestamp: new Date().toISOString()
    };
    setMessages(prev => [...prev, typingMessage]);

    setIsSearching(true);

    try {
      console.log('🌐 Making API request to backend...');
      console.log('📤 Request body:', JSON.stringify({
        query: query,
        ...filters
      }));
      
      const response = await fetch('http://localhost:8000/api/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: query,
          ...filters
        }),
      });
      
      console.log('📥 Response status:', response.status);
      console.log('📥 Response headers:', response.headers);

      const data = await response.json();
      console.log('📥 Response data:', data);

      // Remove typing indicator
      setMessages(prev => prev.filter(msg => msg.type !== 'typing'));

      // Check if query was relevant
      if (!data.is_relevant) {
        // Handle irrelevant or inappropriate queries
        const aiMessage = {
          id: Date.now() + 2,
          type: 'ai',
          content: data.message,
          timestamp: new Date().toISOString(),
          suggestions: data.suggestions || [],
          isInappropriate: data.is_inappropriate || false
        };
        setMessages(prev => [...prev, aiMessage]);
        setJobs([]);
        setSearchStats({
          total_found: 0,
          search_time: data.search_time || 0,
          sources_used: []
        });
        return;
      }

      if (data.success) {
        // Add AI response with jobs
        const aiMessage = {
          id: Date.now() + 2,
          type: 'ai',
          content: data.message,
          timestamp: new Date().toISOString(),
          jobs: data.jobs
        };
        setMessages(prev => [...prev, aiMessage]);
        setJobs(data.jobs);
        setSearchStats({
          total_found: data.total_found,
          search_time: data.search_time,
          sources_used: data.sources_used,
          database_jobs: data.database_jobs || 0,
          web_search_jobs: data.web_search_jobs || 0
        });
      } else {
        // Add error message
        const errorMessage = {
          id: Date.now() + 2,
          type: 'ai',
          content: data.message || "Sorry, I couldn't find any jobs matching your criteria. Try adjusting your search terms or filters.",
          timestamp: new Date().toISOString()
        };
        setMessages(prev => [...prev, errorMessage]);
        setJobs([]);
      }
    } catch (error) {
      console.error('Search error:', error);
      
      // Remove typing indicator
      setMessages(prev => prev.filter(msg => msg.type !== 'typing'));
      
      // Add error message
      const errorMessage = {
        id: Date.now() + 2,
        type: 'ai',
        content: "Sorry, there was an error processing your search. Please try again.",
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsSearching(false);
    }
  };

  const handleFilterChange = (newFilters) => {
    setFilters(newFilters);
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
        <Header />
        
        <Container maxWidth="xl" sx={{ flex: 1, py: 3 }}>
          <Grid container spacing={3} sx={{ height: 'calc(100vh - 140px)' }}>
            {/* Filter Sidebar */}
            <Grid item xs={12} md={3}>
              <motion.div
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.5 }}
              >
                <FilterSidebar 
                  filters={filters}
                  onFilterChange={handleFilterChange}
                />
              </motion.div>
            </Grid>

            {/* Main Content */}
            <Grid item xs={12} md={9}>
              <Grid container spacing={3} sx={{ height: '100%' }}>
                {/* Chat Interface */}
                <Grid item xs={12} lg={6}>
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.5, delay: 0.1 }}
                  >
                    <Paper 
                      sx={{ 
                        height: '100%', 
                        display: 'flex', 
                        flexDirection: 'column',
                        overflow: 'hidden'
                      }}
                    >
                      <ChatInterface 
                        messages={messages}
                        onSendMessage={handleSearch}
                        isSearching={isSearching}
                      />
                    </Paper>
                  </motion.div>
                </Grid>

                {/* Job Results */}
                <Grid item xs={12} lg={6}>
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.5, delay: 0.2 }}
                  >
                    <Paper sx={{ height: '100%', overflow: 'hidden' }}>
                      <JobResults 
                        jobs={jobs}
                        searchStats={searchStats}
                        isSearching={isSearching}
                      />
                    </Paper>
                  </motion.div>
                </Grid>
              </Grid>
            </Grid>
          </Grid>
        </Container>
      </Box>
    </ThemeProvider>
  );
}

export default App;
