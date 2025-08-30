import React from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  CardActions,
  Button,
  Chip,
  Avatar,
  Divider,
  LinearProgress,
  Alert,
  IconButton,
  Tooltip
} from '@mui/material';
import {
  Work as WorkIcon,
  LocationOn as LocationIcon,
  Business as BusinessIcon,
  Link as LinkIcon,
  BookmarkBorder as BookmarkIcon,
  Share as ShareIcon,
  AccessTime as TimeIcon
} from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';

const JobResults = ({ jobs, searchStats, isSearching }) => {
  const formatSalary = (salary) => {
    if (!salary) return 'Not specified';
    return `৳${salary.toLocaleString()}`;
  };

  const formatTime = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleDateString();
  };

  const getSourceColor = (source) => {
    const colors = {
      'BDJobs': 'primary',
      'LinkedIn': 'info',
      'Indeed': 'success',
      'Web Search': 'warning'
    };
    return colors[source] || 'default';
  };

  const handleApply = (job) => {
    window.open(job.url, '_blank');
  };

  const handleShare = (job) => {
    if (navigator.share) {
      navigator.share({
        title: job.title,
        text: `${job.title} at ${job.company}`,
        url: job.url
      });
    } else {
      navigator.clipboard.writeText(job.url);
    }
  };

  if (isSearching) {
    return (
      <Box sx={{ p: 3, height: '100%', display: 'flex', flexDirection: 'column' }}>
        <Typography variant="h6" sx={{ mb: 2, fontWeight: 600, color: 'primary.main' }}>
          🔍 Searching for jobs...
        </Typography>
        <LinearProgress sx={{ mb: 2 }} />
        <Typography variant="body2" color="text.secondary">
          Searching across multiple job sites...
        </Typography>
      </Box>
    );
  }

  if (!jobs || jobs.length === 0) {
    return (
      <Box sx={{ p: 3, height: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
        <WorkIcon sx={{ fontSize: 64, color: 'grey.400', mb: 2 }} />
        <Typography variant="h6" color="text.secondary" sx={{ mb: 1 }}>
          No jobs found
        </Typography>
        <Typography variant="body2" color="text.secondary" align="center">
          Try adjusting your search criteria or filters to find more opportunities.
        </Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3, height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="h6" sx={{ fontWeight: 600, color: 'primary.main', mb: 1 }}>
          💼 Job Results ({jobs.length})
        </Typography>
        
        {/* Search Stats */}
        {searchStats.total_found > 0 && (
          <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', mb: 2 }}>
            <Chip
              icon={<TimeIcon />}
              label={`${searchStats.search_time.toFixed(1)}s`}
              size="small"
              color="info"
              variant="outlined"
            />
            <Chip
              icon={<WorkIcon />}
              label={`${searchStats.total_found} found`}
              size="small"
              color="success"
              variant="outlined"
            />
            {searchStats.database_jobs > 0 && (
              <Chip
                label={`${searchStats.database_jobs} from DB`}
                size="small"
                color="success"
                variant="outlined"
              />
            )}
            {searchStats.web_search_jobs > 0 && (
              <Chip
                label={`${searchStats.web_search_jobs} from Web`}
                size="small"
                color="warning"
                variant="outlined"
              />
            )}
            {searchStats.sources_used.length > 0 && (
              <Chip
                label={`${searchStats.sources_used.length} sources`}
                size="small"
                color="primary"
                variant="outlined"
              />
            )}
          </Box>
        )}

        {/* Sources Used */}
        {searchStats.sources_used.length > 0 && (
          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 2 }}>
            {searchStats.sources_used.map((source) => (
              <Chip
                key={source}
                label={source}
                size="small"
                color={getSourceColor(source)}
                variant="outlined"
              />
            ))}
          </Box>
        )}
      </Box>

      <Divider sx={{ mb: 3 }} />

      {/* Job Cards */}
      <Box sx={{ flex: 1, overflow: 'auto' }}>
        <AnimatePresence>
          {jobs.map((job, index) => (
            <motion.div
              key={job.id || index}
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
              <Card
                sx={{
                  mb: 2,
                  '&:hover': {
                    boxShadow: 4,
                    transform: 'translateY(-2px)',
                    transition: 'all 0.3s ease'
                  }
                }}
              >
                <CardContent>
                  {/* Job Header */}
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                    <Box sx={{ flex: 1 }}>
                      <Typography variant="h6" sx={{ fontWeight: 600, mb: 1, lineHeight: 1.3 }}>
                        {job.title}
                      </Typography>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                        <BusinessIcon sx={{ fontSize: 16, color: 'text.secondary' }} />
                        <Typography variant="body2" color="text.secondary">
                          {job.company || 'Company not specified'}
                        </Typography>
                      </Box>
                      {job.location && (
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <LocationIcon sx={{ fontSize: 16, color: 'text.secondary' }} />
                          <Typography variant="body2" color="text.secondary">
                            {job.location}
                          </Typography>
                        </Box>
                      )}
                    </Box>
                    
                    {/* Source Badge */}
                    <Chip
                      label={job.source || 'Unknown'}
                      size="small"
                      color={getSourceColor(job.source)}
                      variant="outlined"
                    />
                  </Box>

                  {/* Job Details */}
                  <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 2 }}>
                    {job.salary && (
                      <Chip
                        label={formatSalary(job.salary)}
                        size="small"
                        color="success"
                        variant="outlined"
                      />
                    )}
                    {job.job_type && (
                      <Chip
                        label={job.job_type}
                        size="small"
                        color="info"
                        variant="outlined"
                      />
                    )}
                    {job.experience && (
                      <Chip
                        label={job.experience}
                        size="small"
                        color="warning"
                        variant="outlined"
                      />
                    )}
                  </Box>

                  {/* Job Description */}
                  {job.description && (
                    <Typography
                      variant="body2"
                      color="text.secondary"
                      sx={{
                        mb: 2,
                        display: '-webkit-box',
                        WebkitLineClamp: 3,
                        WebkitBoxOrient: 'vertical',
                        overflow: 'hidden',
                        lineHeight: 1.5
                      }}
                    >
                      {job.description}
                    </Typography>
                  )}

                  {/* Posted Date */}
                  {job.posted_date && (
                    <Typography variant="caption" color="text.secondary">
                      Posted: {formatTime(job.posted_date)}
                    </Typography>
                  )}
                </CardContent>

                <CardActions sx={{ justifyContent: 'space-between', px: 2, pb: 2 }}>
                  <Box sx={{ display: 'flex', gap: 1 }}>
                    <Button
                      variant="contained"
                      size="small"
                      startIcon={<LinkIcon />}
                      onClick={() => handleApply(job)}
                      sx={{ textTransform: 'none' }}
                    >
                      Apply Now
                    </Button>
                  </Box>
                  
                  <Box sx={{ display: 'flex', gap: 0.5 }}>
                    <Tooltip title="Save job">
                      <IconButton size="small" color="primary">
                        <BookmarkIcon />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Share job">
                      <IconButton size="small" color="primary" onClick={() => handleShare(job)}>
                        <ShareIcon />
                      </IconButton>
                    </Tooltip>
                  </Box>
                </CardActions>
              </Card>
            </motion.div>
          ))}
        </AnimatePresence>
      </Box>
    </Box>
  );
};

export default JobResults;
