import React, { useState, useEffect } from 'react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { CssBaseline, Container, Tabs, Tab, Box, Typography, Alert } from '@mui/material';
import QueryTab from './components/QueryTab';
import SearchTab from './components/SearchTab';
import HealthIndicator from './components/HealthIndicator';
import axios from 'axios';

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
});

function App() {
  const [tabValue, setTabValue] = useState(0);
  const [healthStatus, setHealthStatus] = useState(null);
  const [healthError, setHealthError] = useState(null);

  useEffect(() => {
    checkHealth();
  }, []);

  const checkHealth = async () => {
    try {
      const response = await axios.get('/api/v1/health');
      setHealthStatus(response.data);
      setHealthError(null);
    } catch (error) {
      setHealthError(error.message);
      setHealthStatus(null);
    }
  };

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Discourse RAG Assistant
        </Typography>
        
        <HealthIndicator 
          status={healthStatus} 
          error={healthError} 
          onRefresh={checkHealth} 
        />

        {healthError && (
          <Alert severity="error" sx={{ mt: 2 }}>
            Backend connection failed: {healthError}
          </Alert>
        )}

        <Box sx={{ borderBottom: 1, borderColor: 'divider', mt: 3 }}>
          <Tabs value={tabValue} onChange={handleTabChange} aria-label="rag tabs">
            <Tab label="Ask Question" />
            <Tab label="Search Chunks" />
          </Tabs>
        </Box>

        <Box sx={{ mt: 3 }}>
          {tabValue === 0 && <QueryTab />}
          {tabValue === 1 && <SearchTab />}
        </Box>
      </Container>
    </ThemeProvider>
  );
}

export default App;
