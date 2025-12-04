import React, { useState } from 'react';
import {
  Box,
  TextField,
  Button,
  Typography,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Alert,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  List,
  ListItem,
  ListItemText,
  Link,
  IconButton,
  Tooltip,
  Divider,
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import OpenInNewIcon from '@mui/icons-material/OpenInNew';
import axios from 'axios';

function QueryTab() {
  const [query, setQuery] = useState('');
  const [topK, setTopK] = useState(5);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [copied, setCopied] = useState(false);

  const handleCopyAnswer = async () => {
    if (result?.answer) {
      try {
        await navigator.clipboard.writeText(result.answer);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
      } catch (err) {
        console.error('Failed to copy:', err);
      }
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await axios.post('/api/v1/ask', {
        query: query.trim(),
        top_k: topK,
      });
      setResult(response.data);
    } catch (err) {
      setError(err.response?.data?.error || err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Ask a Question
      </Typography>
      <Typography variant="body2" color="text.secondary" gutterBottom>
        Get AI-powered answers based on the indexed Discourse content
      </Typography>
      
      <form onSubmit={handleSubmit}>
        <TextField
          fullWidth
          label="Your question"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          margin="normal"
          required
          multiline
          rows={3}
          disabled={loading}
          placeholder="e.g., What is the reading club about?"
        />
        
        <TextField
          label="Number of sources"
          type="number"
          value={topK}
          onChange={(e) => setTopK(Math.max(1, Math.min(20, parseInt(e.target.value) || 5)))}
          margin="normal"
          sx={{ width: 200 }}
          inputProps={{ min: 1, max: 20 }}
          disabled={loading}
        />
        
        <Button
          type="submit"
          variant="contained"
          disabled={loading || !query.trim()}
          sx={{ mt: 2, ml: 2 }}
        >
          {loading ? <CircularProgress size={24} /> : 'Ask Question'}
        </Button>
      </form>

      {error && (
        <Alert severity="error" sx={{ mt: 2 }}>
          <Typography variant="body2" fontWeight="bold">Error:</Typography>
          <Typography variant="body2">{error}</Typography>
          <Typography variant="caption" sx={{ mt: 1, display: 'block' }}>
            Please check your connection and try again. If the problem persists, ensure the backend server is running.
          </Typography>
        </Alert>
      )}

      {result && (
        <Card sx={{ mt: 3 }}>
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6">
                Answer
              </Typography>
              <Tooltip title={copied ? "Copied!" : "Copy answer"}>
                <IconButton size="small" onClick={handleCopyAnswer} color="primary">
                  <ContentCopyIcon fontSize="small" />
                </IconButton>
              </Tooltip>
            </Box>
            
            <Typography 
              variant="body1" 
              sx={{ 
                mb: 2, 
                whiteSpace: 'pre-wrap',
                wordBreak: 'break-word',
                lineHeight: 1.7
              }}
            >
              {result.answer}
            </Typography>
            
            <Divider sx={{ my: 2 }} />
            
            <Box sx={{ mb: 2, display: 'flex', flexWrap: 'wrap', gap: 1 }}>
              <Chip 
                label={`Latency: ${result.latency_ms?.toFixed(0)}ms`} 
                color="primary" 
                size="small" 
              />
              <Chip 
                label={`Sources: ${result.sources?.length || 0}`} 
                color="secondary" 
                size="small" 
              />
              <Chip 
                label={`Chunks: ${result.chunks_retrieved || 0}`} 
                color="default" 
                size="small" 
                variant="outlined"
              />
              {result.model_used && (
                <Chip 
                  label={`Model: ${result.model_used}`} 
                  color="info" 
                  size="small" 
                  variant="outlined"
                />
              )}
            </Box>

            {result.sources && result.sources.length > 0 && (
              <Accordion>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Typography variant="subtitle1">
                    View Sources ({result.sources.length})
                  </Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <List>
                    {result.sources.map((source, index) => (
                      <ListItem 
                        key={index} 
                        divider
                        sx={{ 
                          flexDirection: 'column', 
                          alignItems: 'stretch',
                          py: 2
                        }}
                      >
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                          <Typography variant="subtitle2" fontWeight="bold">
                            Source {index + 1}
                          </Typography>
                          {source.similarity !== undefined && (
                            <Chip 
                              label={`${(source.similarity * 100).toFixed(1)}% match`} 
                              size="small" 
                              color="info" 
                              variant="outlined"
                            />
                          )}
                        </Box>
                        
                        {source.title && (
                          <Typography variant="h6" sx={{ mb: 1, fontSize: '1rem' }}>
                            {source.title}
                          </Typography>
                        )}
                        
                        {source.chunk_text && (
                          <Typography 
                            variant="body2" 
                            color="text.secondary" 
                            sx={{ 
                              mb: 1.5,
                              p: 1.5,
                              bgcolor: 'grey.50',
                              borderRadius: 1,
                              borderLeft: '3px solid',
                              borderColor: 'primary.main'
                            }}
                          >
                            {source.chunk_text}
                          </Typography>
                        )}
                        
                        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mt: 1 }}>
                          {source.url && (
                            <Link
                              href={source.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              sx={{ 
                                display: 'flex', 
                                alignItems: 'center', 
                                gap: 0.5,
                                textDecoration: 'none'
                              }}
                            >
                              <OpenInNewIcon fontSize="small" />
                              <Typography variant="caption" color="primary">
                                View Original Post
                              </Typography>
                            </Link>
                          )}
                          {source.post_id && (
                            <Chip 
                              label={`Post #${source.post_id}`} 
                              size="small" 
                              variant="outlined"
                            />
                          )}
                          {source.topic_id && (
                            <Chip 
                              label={`Topic #${source.topic_id}`} 
                              size="small" 
                              variant="outlined"
                            />
                          )}
                        </Box>
                      </ListItem>
                    ))}
                  </List>
                </AccordionDetails>
              </Accordion>
            )}
            
            {result.sources && result.sources.length === 0 && (
              <Alert severity="info" sx={{ mt: 2 }}>
                No sources were retrieved for this query.
              </Alert>
            )}
          </CardContent>
        </Card>
      )}
    </Box>
  );
}

export default QueryTab;
