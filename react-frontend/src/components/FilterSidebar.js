import React from 'react';
import {
  Box,
  Typography,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Slider,
  FormControlLabel,
  Checkbox,
  Paper,
  Divider,
  Chip
} from '@mui/material';
import { motion } from 'framer-motion';

const FilterSidebar = ({ filters, onFilterChange }) => {
  const handleLocationChange = (event) => {
    onFilterChange({ ...filters, location: event.target.value });
  };

  const handleExperienceChange = (event) => {
    onFilterChange({ ...filters, experience: event.target.value });
  };

  const handleJobTypeChange = (event) => {
    onFilterChange({ ...filters, job_type: event.target.value });
  };

  const handleSalaryChange = (event, newValue) => {
    onFilterChange({ ...filters, salary_range: newValue });
  };

  const handleSourceChange = (source) => (event) => {
    const newSources = { ...filters.sources };
    newSources[source] = event.target.checked;
    onFilterChange({ ...filters, sources: newSources });
  };

  const handleMaxResultsChange = (event) => {
    onFilterChange({ ...filters, max_results: event.target.value });
  };

  const handleTimeoutChange = (event) => {
    onFilterChange({ ...filters, timeout: event.target.value });
  };

  const formatSalary = (value) => {
    return `৳${value.toLocaleString()}`;
  };

  return (
    <Paper sx={{ p: 3, height: '100%', overflow: 'auto' }}>
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <Typography variant="h6" sx={{ mb: 3, fontWeight: 600, color: 'primary.main' }}>
          🔍 Search Filters
        </Typography>

        {/* Location Filter */}
        <Box sx={{ mb: 3 }}>
          <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>
            📍 Location
          </Typography>
          <FormControl fullWidth size="small">
            <InputLabel>Location</InputLabel>
            <Select
              value={filters.location}
              label="Location"
              onChange={handleLocationChange}
            >
              <MenuItem value="All Locations">All Locations</MenuItem>
              <MenuItem value="Dhaka">Dhaka</MenuItem>
              <MenuItem value="Chittagong">Chittagong</MenuItem>
              <MenuItem value="Sylhet">Sylhet</MenuItem>
              <MenuItem value="Rajshahi">Rajshahi</MenuItem>
              <MenuItem value="Khulna">Khulna</MenuItem>
              <MenuItem value="Barisal">Barisal</MenuItem>
              <MenuItem value="Rangpur">Rangpur</MenuItem>
              <MenuItem value="Mymensingh">Mymensingh</MenuItem>
            </Select>
          </FormControl>
        </Box>

        <Divider sx={{ my: 2 }} />

        {/* Experience Level */}
        <Box sx={{ mb: 3 }}>
          <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>
            👨‍💼 Experience Level
          </Typography>
          <FormControl fullWidth size="small">
            <InputLabel>Experience</InputLabel>
            <Select
              value={filters.experience}
              label="Experience"
              onChange={handleExperienceChange}
            >
              <MenuItem value="Any">Any</MenuItem>
              <MenuItem value="Entry Level">Entry Level</MenuItem>
              <MenuItem value="Mid Level">Mid Level</MenuItem>
              <MenuItem value="Senior Level">Senior Level</MenuItem>
              <MenuItem value="Executive">Executive</MenuItem>
            </Select>
          </FormControl>
        </Box>

        <Divider sx={{ my: 2 }} />

        {/* Job Type */}
        <Box sx={{ mb: 3 }}>
          <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>
            💼 Job Type
          </Typography>
          <FormControl fullWidth size="small">
            <InputLabel>Job Type</InputLabel>
            <Select
              value={filters.job_type}
              label="Job Type"
              onChange={handleJobTypeChange}
            >
              <MenuItem value="Any">Any</MenuItem>
              <MenuItem value="Full-time">Full-time</MenuItem>
              <MenuItem value="Part-time">Part-time</MenuItem>
              <MenuItem value="Contract">Contract</MenuItem>
              <MenuItem value="Remote">Remote</MenuItem>
              <MenuItem value="Hybrid">Hybrid</MenuItem>
            </Select>
          </FormControl>
        </Box>

        <Divider sx={{ my: 2 }} />

        {/* Salary Range */}
        <Box sx={{ mb: 3 }}>
          <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>
            💰 Salary Range
          </Typography>
          <Box sx={{ px: 1 }}>
            <Slider
              value={filters.salary_range}
              onChange={handleSalaryChange}
              valueLabelDisplay="auto"
              valueLabelFormat={formatSalary}
              min={0}
              max={200000}
              step={5000}
              marks={[
                { value: 0, label: '৳0' },
                { value: 50000, label: '৳50K' },
                { value: 100000, label: '৳100K' },
                { value: 150000, label: '৳150K' },
                { value: 200000, label: '৳200K' }
              ]}
            />
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 1 }}>
              <Typography variant="caption" color="text.secondary">
                {formatSalary(filters.salary_range[0])}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {formatSalary(filters.salary_range[1])}
              </Typography>
            </Box>
          </Box>
        </Box>

        <Divider sx={{ my: 2 }} />

        {/* Data Sources */}
        <Box sx={{ mb: 3 }}>
          <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>
            🔗 Data Sources
          </Typography>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
            {Object.entries(filters.sources).map(([source, enabled]) => (
              <FormControlLabel
                key={source}
                control={
                  <Checkbox
                    checked={enabled}
                    onChange={handleSourceChange(source)}
                    size="small"
                  />
                }
                label={
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Chip
                      label={source}
                      size="small"
                      color={enabled ? "primary" : "default"}
                      variant={enabled ? "filled" : "outlined"}
                    />
                  </Box>
                }
              />
            ))}
          </Box>
        </Box>

        <Divider sx={{ my: 2 }} />

        {/* Max Results */}
        <Box sx={{ mb: 3 }}>
          <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>
            📊 Max Results
          </Typography>
          <FormControl fullWidth size="small">
            <InputLabel>Max Results</InputLabel>
            <Select
              value={filters.max_results}
              label="Max Results"
              onChange={handleMaxResultsChange}
            >
              <MenuItem value={5}>5 jobs</MenuItem>
              <MenuItem value={10}>10 jobs</MenuItem>
              <MenuItem value={15}>15 jobs</MenuItem>
              <MenuItem value={20}>20 jobs</MenuItem>
              <MenuItem value={30}>30 jobs</MenuItem>
            </Select>
          </FormControl>
        </Box>

        <Divider sx={{ my: 2 }} />

        {/* Timeout */}
        <Box sx={{ mb: 3 }}>
          <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>
            ⏱️ Search Timeout
          </Typography>
          <FormControl fullWidth size="small">
            <InputLabel>Timeout</InputLabel>
            <Select
              value={filters.timeout}
              label="Timeout"
              onChange={handleTimeoutChange}
            >
              <MenuItem value={15}>15 seconds</MenuItem>
              <MenuItem value={30}>30 seconds</MenuItem>
              <MenuItem value={45}>45 seconds</MenuItem>
              <MenuItem value={60}>60 seconds</MenuItem>
            </Select>
          </FormControl>
        </Box>

        {/* Active Filters Summary */}
        <Box sx={{ mt: 3, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
          <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>
            ✅ Active Filters
          </Typography>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
            {filters.location !== "All Locations" && (
              <Chip label={filters.location} size="small" color="primary" />
            )}
            {filters.experience !== "Any" && (
              <Chip label={filters.experience} size="small" color="secondary" />
            )}
            {filters.job_type !== "Any" && (
              <Chip label={filters.job_type} size="small" color="info" />
            )}
            {Object.entries(filters.sources).filter(([_, enabled]) => enabled).length > 0 && (
              <Chip 
                label={`${Object.entries(filters.sources).filter(([_, enabled]) => enabled).length} sources`} 
                size="small" 
                color="success" 
              />
            )}
          </Box>
        </Box>
      </motion.div>
    </Paper>
  );
};

export default FilterSidebar;
